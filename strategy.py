import asyncio

# Memória persistente do robô para construir a estrutura dos 3 timeframes
HISTORICO_PRECOS = []

def calcular_velas_memoria(precos, tamanho_vela):
    """
    Agrupa os preços em blocos para simular candles históricos.
    """
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

    # 1. Obter preço atual do XAUUSD
    try:
        price_data = await connection.get_symbol_price("XAUUSD")
        preco_atual = price_data.get("bid", 0.0)
    except Exception as e:
        print(f"⚠️ Erro ao obter preço do XAUUSD: {e}")
        return

    if preco_atual == 0.0:
        return

    HISTORICO_PRECOS.append(preco_atual)
    
    # Mantém os últimos 300 ticks na memória para calcular a estrutura
    if len(HISTORICO_PRECOS) > 300:
        HISTORICO_PRECOS.pop(0)

    # Simulação proporcional de timeframes para a sessão
    velas_m1 = calcular_velas_memoria(HISTORICO_PRECOS, 5)   # Cada 5 ticks = 1m
    velas_m5 = calcular_velas_memoria(HISTORICO_PRECOS, 15)  # Cada 15 ticks = 5m
    velas_h1 = calcular_velas_memoria(HISTORICO_PRECOS, 40)  # Cada 40 ticks = H1

    if len(velas_m1) < 3:
        print(f"⏳ A acumular dados de mercado... Ticks recolhidos: {len(HISTORICO_PRECOS)}/15")
        return

    # 2. Análise H1 (Bias + Suporte / Resistência)
    bias_h1, suporte_h1, resistencia_h1 = analisar_bias_h1(velas_h1)

    # 3. Análise M5 e M1 (Deteção de FVG)
    fvg_m5, gap_m5 = detectar_fvg(velas_m5)
    fvg_m1, gap_m1 = detectar_fvg(velas_m1)

    print(f"📊 [H1] Bias: {bias_h1} | Sup: {suporte_h1:.2f} | Res: {resistencia_h1:.2f} | Preço: {preco_atual:.2f}")
    print(f"🔍 [MONITOR] FVG M5: {fvg_m5} | FVG M1: {fvg_m1}")

    # 4. Execução Confluente de Compra (BUY)
    if bias_h1 == "BULLISH" and preco_atual > suporte_h1:
        if fvg_m5 == "BULLISH" and fvg_m1 == "BULLISH":
            print("🚀 [SINAL] Confluência Completa de COMPRA Encontrada!")
            bot_status["last_signals"].append(f"BUY XAUUSD - Multi-Timeframe")
            from bot_engine import executar_ordem
            await executar_ordem(connection, "XAUUSD", "BUY", 0.01, sl=preco_atual - 15.0, tp=preco_atual + 45.0)
            HISTORICO_PRECOS.clear()

    # 5. Execução Confluente de Venda (SELL)
    elif bias_h1 == "BEARISH" and preco_atual < resistencia_h1:
        if fvg_m5 == "BEARISH" and fvg_m1 == "BEARISH":
            print("🚀 [SINAL] Confluência Completa de VENDA Encontrada!")
            bot_status["last_signals"].append(f"SELL XAUUSD - Multi-Timeframe")
            from bot_engine import executar_ordem
            await executar_ordem(connection, "XAUUSD", "SELL", 0.01, sl=preco_atual + 15.0, tp=preco_atual - 45.0)
            HISTORICO_PRECOS.clear()
