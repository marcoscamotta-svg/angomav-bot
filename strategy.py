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

def detectar_wyckoff_e_sms(velas, suporte, resistencia):
    """
    Identifica Captura de Liquidez (Wyckoff Spring/UTAD) e Mudança de Caráter (CHoCH).
    """
    if len(velas) < 4:
        return None, None

    v_anterior = velas[-2]
    v_atual = velas[-1]

    wyckoff_evento = None
    sms_choch = None

    # Wyckoff Spring: Preço fura o suporte mas fecha acima dele (Varredura de Liquidez de Venda)
    if v_atual['low'] < suporte and v_atual['close'] > suporte:
        wyckoff_evento = "SPRING (SPRING_LIQUIDITY_SWEEP)"

    # Wyckoff UTAD: Preço fura a resistência mas fecha abaixo dela (Varredura de Liquidez de Compra)
    elif v_atual['high'] > resistencia and v_atual['close'] < resistencia:
        wyckoff_evento = "UTAD (UTAD_LIQUIDITY_SWEEP)"

    # SMS - CHoCH Bullish (Quebra o topo anterior)
    if v_atual['close'] > v_anterior['high']:
        sms_choch = "BULLISH_CHOCH"

    # SMS - CHoCH Bearish (Quebra o fundo anterior)
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
    
    if len(HISTORICO_PRECOS) > 300:
        HISTORICO_PRECOS.pop(0)

    velas_m1 = calcular_velas_memoria(HISTORICO_PRECOS, 5)
    velas_m5 = calcular_velas_memoria(HISTORICO_PRECOS, 15)
    velas_h1 = calcular_velas_memoria(HISTORICO_PRECOS, 40)

    if len(velas_m1) < 4:
        print(f"⏳ A acumular ticks para análise SMC + Wyckoff... Ticks: {len(HISTORICO_PRECOS)}/20")
        return

    # 1. Análise H1 (Bias e Níveis)
    bias_h1, suporte_h1, resistencia_h1 = analisar_bias_h1(velas_h1)

    # 2. Análise Wyckoff e SMS (M5 e M1)
    wyckoff_evt, sms_choch = detectar_wyckoff_e_sms(velas_m5, suporte_h1, resistencia_h1)

    # 3. Análise FVG (M5 e M1)
    fvg_m5, gap_m5 = detectar_fvg(velas_m5)
    fvg_m1, gap_m1 = detectar_fvg(velas_m1)

    print(f"📊 [H1] Bias: {bias_h1} | Sup: {suporte_h1:.2f} | Res: {resistencia_h1:.2f} | Preço: {preco_atual:.2f}")
    print(f"🏛️ [WYCKOFF/SMS] Evento: {wyckoff_evt} | CHoCH: {sms_choch}")
    print(f"🔍 [FVG] M5: {fvg_m5} | M1: {fvg_m1}")

    # ---------------------------------------------------------
    # COMPRA INSTITUCIONAL (BUY): H1 Bullish + Wyckoff Spring/CHoCH + FVG
    # ---------------------------------------------------------
    if bias_h1 == "BULLISH":
        if wyckoff_evt == "SPRING (SPRING_LIQUIDITY_SWEEP)" or sms_choch == "BULLISH_CHOCH":
            if fvg_m5 == "BULLISH" or fvg_m1 == "BULLISH":
                print("🚀 [SINAL ALTA PRECISÃO] Entrada de Compra SMC + Wyckoff!")
                bot_status["last_signals"].append("BUY XAUUSD - Wyckoff Spring + CHoCH + FVG")
                from bot_engine import executar_ordem
                await executar_ordem(connection, "XAUUSD", "BUY", 0.01, sl=preco_atual - 15.0, tp=preco_atual + 45.0)
                HISTORICO_PRECOS.clear()

    # ---------------------------------------------------------
    # VENDA INSTITUCIONAL (SELL): H1 Bearish + Wyckoff UTAD/CHoCH + FVG
    # ---------------------------------------------------------
    elif bias_h1 == "BEARISH":
        if wyckoff_evt == "UTAD (UTAD_LIQUIDITY_SWEEP)" or sms_choch == "BEARISH_CHOCH":
            if fvg_m5 == "BEARISH" or fvg_m1 == "BEARISH":
                print("🚀 [SINAL ALTA PRECISÃO] Entrada de Venda SMC + Wyckoff!")
                bot_status["last_signals"].append("SELL XAUUSD - Wyckoff UTAD + CHoCH + FVG")
                from bot_engine import executar_ordem
                await executar_ordem(connection, "XAUUSD", "SELL", 0.01, sl=preco_atual + 15.0, tp=preco_atual - 45.0)
                HISTORICO_PRECOS.clear()

