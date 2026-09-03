import asyncio

async def obter_historico(connection, symbol, timeframe, count=20):
    """
    Busca o histórico recente de velas via MetaApi RPC utilizando get_candle_series.
    Timeframes MetaApi RPC: '1m', '5m', '1h', etc.
    """
    try:
        # Método nativo do MetaApi RPC
        candles = await connection.get_candle_series(symbol, timeframe, count)
        return candles
    except Exception as e:
        # Fallback de segurança para evitar interrupções
        print(f"⚠️ Erro ao procurar candles {timeframe}: {e}")
        return []

def analisar_bias_h1(candles_h1):
    """
    1. Identifica a tendência em H1 (Altista ou Baixista).
    2. Identifica os níveis de Suporte e Resistência relevantes.
    """
    if not candles_h1 or len(candles_h1) < 5:
        return "NEUTRO", 0.0, 0.0

    highs = [c.get('high', 0.0) for c in candles_h1]
    lows = [c.get('low', 0.0) for c in candles_h1]

    resistencia = max(highs) if highs else 0.0
    suporte = min(lows) if lows else 0.0
    
    ultimo_fecho = candles_h1[-1].get('close', 0.0)
    fecho_anterior = candles_h1[0].get('close', 0.0)

    if ultimo_fecho > fecho_anterior:
        bias = "BULLISH"
    elif ultimo_fecho < fecho_anterior:
        bias = "BEARISH"
    else:
        bias = "NEUTRO"

    return bias, suporte, resistencia

def detectar_fvg(candles):
    """
    Identifica Fair Value Gaps (Ineficiências) na sequência de velas.
    """
    if not candles or len(candles) < 3:
        return None, 0.0

    v1, v2, v3 = candles[-3], candles[-2], candles[-1]

    v1_high = v1.get('high', 0.0)
    v1_low = v1.get('low', 0.0)
    v3_high = v3.get('high', 0.0)
    v3_low = v3.get('low', 0.0)

    # FVG de Alta
    if v3_low > v1_high and v1_high > 0:
        gap = v3_low - v1_high
        return "BULLISH", gap

    # FVG de Baixa
    elif v3_high < v1_low and v3_high > 0:
        gap = v1_low - v3_high
        return "BEARISH", gap

    return None, 0.0


async def analisar_estrategia(connection, bot_status):
    """
    Motor SMC Completo: H1 (Bias + Suporte/Resistência) -> M5 (Estrutura) -> M1 (Refinamento)
    """
    symbol = "XAUUSD"

    # Timeframes oficiais MetaApi: '1h', '5m', '1m'
    candles_h1 = await obter_historico(connection, symbol, "1h", count=15)
    candles_m5 = await obter_historico(connection, symbol, "5m", count=10)
    candles_m1 = await obter_historico(connection, symbol, "1m", count=10)

    if not candles_h1 or not candles_m5 or not candles_m1:
        print("⏳ A aguardar sincronização dos dados históricos dos 3 timeframes...")
        return

    # 1. Análise H1: Tendência Maior + Suporte/Resistência
    bias_h1, suporte_h1, resistencia_h1 = analisar_bias_h1(candles_h1)
    preco_atual = candles_m1[-1].get('close', 0.0)

    print(f"\n📊 [ANALISE H1] Bias: {bias_h1} | Suporte: {suporte_h1:.2f} | Resistência: {resistencia_h1:.2f} | Preço: {preco_atual:.2f}")

    # 2. Análise M5: Estrutura FVG
    tipo_fvg_m5, gap_m5 = detectar_fvg(candles_m5)

    # 3. Análise M1: Confirmação de Entrada
    tipo_fvg_m1, gap_m1 = detectar_fvg(candles_m1)

    print(f"🔍 [MONITOR] FVG M5: {tipo_fvg_m5} ({gap_m5:.2f}) | FVG M1: {tipo_fvg_m1} ({gap_m1:.2f})")

    # ---------------------------------------------------------
    # CONFLUÊNCIA DE COMPRA (BUY)
    # ---------------------------------------------------------
    if bias_h1 == "BULLISH" and preco_atual > suporte_h1:
        if tipo_fvg_m5 == "BULLISH" and tipo_fvg_m1 == "BULLISH":
            print(f"🚀 [SINAL CONFLUENTE - BUY] H1 Bullish + FVG M5 + FVG M1! Gap M1: {gap_m1:.2f}")
            bot_status["last_signals"].append(f"BUY {symbol} - Confluência Multi-Timeframe")

            from bot_engine import executar_ordem
            sl_price = preco_atual - 15.0
            tp_price = preco_atual + 45.0
            await executar_ordem(connection, symbol, "BUY", 0.01, sl=sl_price, tp=tp_price)

    # ---------------------------------------------------------
    # CONFLUÊNCIA DE VENDA (SELL)
    # ---------------------------------------------------------
    elif bias_h1 == "BEARISH" and preco_atual < resistencia_h1:
        if tipo_fvg_m5 == "BEARISH" and tipo_fvg_m1 == "BEARISH":
            print(f"🚀 [SINAL CONFLUENTE - SELL] H1 Bearish + FVG M5 + FVG M1! Gap M1: {gap_m1:.2f}")
            bot_status["last_signals"].append(f"SELL {symbol} - Confluência Multi-Timeframe")

            from bot_engine import executar_ordem
            sl_price = preco_atual + 15.0
            tp_price = preco_atual - 45.0
            await executar_ordem(connection, symbol, "SELL", 0.01, sl=sl_price, tp=tp_price)

    else:
        print("🔍 Sem confluência no momento. Fora da tendência principal de H1.")
