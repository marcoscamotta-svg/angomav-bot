import asyncio

HISTORICO_PRECOS = []

def calcular_velas_memoria(precos, tamanho_vela):
    velas = []
    for i in range(0, len(precos), tamanho_vela):
        bloco = precos[i:i+tamanho_vela]
        if bloco:
            velas.append({
                'open': bloco[0],
                'high': max(bloco),
                'low': min(bloco),
                'close': bloco[-1]
            })
    return velas

def analisar_bias_h1(velas_h1):
    if not velas_h1:
        return "NEUTRO", 0.0, 0.0

    highs = [v['high'] for v in velas_h1]
    lows = [v['low'] for v in velas_h1]

    resistencia = max(highs) if highs else 0.0
    suporte = min(lows) if lows else 0.0

    ultimo_fecho = velas_h1[-1]['close']
    primeiro_fecho = velas_h1[0]['close']

    if ultimo_fecho > primeiro_fecho:
        bias = "BULLISH"
    elif ultimo_fecho < primeiro_fecho:
        bias = "BEARISH"
    else:
        bias = "NEUTRO"

    return bias, suporte, resistencia

def detectar_elliott_waves(velas_m15):
    """
    Mapeia a estrutura de Ondas de Elliott no M15 (Contagem simplificada de pivôs 1-2-3-4-5 / ABC).
    """
    if len(velas_m15) < 5:
        return "NEUTRO", "AGUARDANDO_ONDA"

    fechos = [v['close'] for v in velas_m15[-5:]]

    # Estrutura Impulsiva de Alta (Onda 3 ou 5)
    if fechos[-1] > fechos[-2] and fechos[-3] < fechos[-4] and fechos[-1] > fechos[-3]:
        return "BULLISH", "ONDA_3_IMPULSO"

    # Estrutura Correutiva ABC (Final de Onda C para Compra)
    elif fechos[-1] < fechos[-2] and fechos[-2] > fechos[-3] and fechos[-1] < fechos[-4]:
        return "BEARISH", "ONDA_C_CORRECAO"

    return "NEUTRO", "ONDA_CONSOLIDADA"

def detectar_wyckoff_e_sms(velas, suporte, resistencia):
    if len(velas) < 4:
        return None, None

    v_anterior = velas[-2]
    v_atual = velas[-1]

    wyckoff_evento = None
    sms_choch = None

    if v_atual['low'] < suporte and v_atual['close'] > suporte:
        wyckoff_evento = "SPRING_SWEEP"
    elif v_atual['high'] > resistencia and v_atual['close'] < resistencia:
        wyckoff_evento = "UTAD_SWEEP"

    if v_atual['close'] > v_anterior['high']:
        sms_choch = "BULLISH_CHOCH"
    elif v_atual['close'] < v_anterior['low']:
        sms_choch = "BEARISH_CHOCH"

    return wyckoff_evento, sms_choch

def detectar_fvg(velas):
    if len(velas) < 3:
        return None, 0.0

    v1, v2, v3 = velas[-3], velas[-2], velas[-1]

    if v3['low'] > v1['high']:
        return "BULLISH", (v3['low'] - v1['high'])
    elif v3['high'] < v1['low']:
        return "BEARISH", (v1['low'] - v3['high'])

    return None, 0.0

async def analisar_estrategia(connection, bot_status):
    global HISTORICO_PRECOS

    try:
        price_data = await connection.get_symbol_price("XAUUSD")
        preco_atual = price_data.get("bid", 0.0)
    except Exception as e:
        print(f"⚠️ Erro ao obter preço: {e}")
        return

    if preco_atual == 0.0:
        return

    HISTORICO_PRECOS.append(preco_atual)
    
    if len(HISTORICO_PRECOS) > 400:
        HISTORICO_PRECOS.pop(0)

    # Reagrupamento dos timeframes: M1 (5 ticks), M15 (30 ticks), H1 (60 ticks)
    velas_m1 = calcular_velas_memoria(HISTORICO_PRECOS, 5)
    velas_m15 = calcular_velas_memoria(HISTORICO_PRECOS, 30)
    velas_h1 = calcular_velas_memoria(HISTORICO_PRECOS, 60)

    if len(velas_m1) < 4:
        print(f"⏳ A acumular dados para H1 + M15 (Elliott) + M1... Ticks: {len(HISTORICO_PRECOS)}/20")
        return

    # 1. Análise H1 (Bias Maior + Suporte/Resistência)
    bias_h1, suporte_h1, resistencia_h1 = analisar_bias_h1(velas_h1)

    # 2. Análise M15 (Ondas de Elliott + FVG M15)
    bias_elliott_m15, onda_status = detectar_elliott_waves(velas_m15)
    fvg_m15, gap_m15 = detectar_fvg(velas_m15)

    # 3. Análise M1 (Gatilho Wyckoff / CHoCH + FVG M1)
    wyckoff_evt, sms_choch = detectar_wyckoff_e_sms(velas_m1, suporte_h1, resistencia_h1)
    fvg_m1, gap_m1 = detectar_fvg(velas_m1)

    print(f"📊 [H1] Bias: {bias_h1} | Sup: {suporte_h1:.2f} | Res: {resistencia_h1:.2f} | Preço: {preco_atual:.2f}")
    print(f"🌊 [M15 ELLIOTT] Estrutura: {bias_elliott_m15} ({onda_status}) | FVG M15: {fvg_m15}")
    print(f"⚡ [M1 GATILHO] Evento: {wyckoff_evt} | CHoCH: {sms_choch} | FVG M1: {fvg_m1}")

    # ---------------------------------------------------------
    # CONFLUÊNCIA DE COMPRA (BUY): H1 Bullish + M15 Elliott + M1 Gatilho
    # ---------------------------------------------------------
    if bias_h1 == "BULLISH" and bias_elliott_m15 == "BULLISH":
        if fvg_m15 == "BULLISH" or fvg_m1 == "BULLISH":
            if sms_choch == "BULLISH_CHOCH" or wyckoff_evt == "SPRING_SWEEP":
                print("🚀 [SINAL PERFEITO] Compra Confluente: H1 + M15 (Elliott) + M1 (CHoCH)!")
                bot_status["last_signals"].append("BUY XAUUSD - Elliott Wave M15 + CHoCH M1")
                from bot_engine import executar_ordem
                await executar_ordem(connection, "XAUUSD", "BUY", 0.01, sl=preco_atual - 15.0, tp=preco_atual + 45.0)
                HISTORICO_PRECOS.clear()

    # ---------------------------------------------------------
    # CONFLUÊNCIA DE VENDA (SELL): H1 Bearish + M15 Elliott + M1 Gatilho
    # ---------------------------------------------------------
    elif bias_h1 == "BEARISH" and bias_elliott_m15 == "BEARISH":
        if fvg_m15 == "BEARISH" or fvg_m1 == "BEARISH":
            if sms_choch == "BEARISH_CHOCH" or wyckoff_evt == "UTAD_SWEEP":
                print("🚀 [SINAL PERFEITO] Venda Confluente: H1 + M15 (Elliott) + M1 (CHoCH)!")
                bot_status["last_signals"].append("SELL XAUUSD - Elliott Wave M15 + CHoCH M1")
                from bot_engine import executar_ordem
                await executar_ordem(connection, "XAUUSD", "SELL", 0.01, sl=preco_atual + 15.0, tp=preco_atual - 45.0)
                HISTORICO_PRECOS.clear()
