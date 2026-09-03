import asyncio

async def obter_historico(connection, symbol, timeframe, count=20):
    """
    Procura o histórico recente de velas via MetaApi para análise de estrutura.
    """
    try:
        candles = await connection.get_historical_candles(symbol, timeframe, limit=count)
        return candles
    except Exception as e:
        print(f"⚠️ Erro ao procurar candles {timeframe}: {e}")
        return []

def analisar_bias_h1(candles_h1):
    """
    1. Identifica a tendência em H1 (Altista ou Baixista).
    2. Identifica os níveis de Suporte e Resistência relevantes.
    """
    if len(candles_h1) < 5:
        return "NEUTRO", None, None

    # Obter máximas e mínimas recentes
    highs = [c['high'] for c in candles_h1]
    lows = [c['low'] for c in candles_h1]

    resistencia = max(highs[-10:])
    suporte = min(lows[-10:])
    
    ultimo_fecho = candles_h1[-1]['close']
    fecho_anterior = candles_h1[-5]['close']

    # Determinação do Bias baseada em Highs/Lows e direção do fecho
    if ultimo_fecho > fecho_anterior:
        bias = "BULLISH"
    elif ultimo_fecho < fecho_anterior:
        bias = "BEARISH"
    else:
        bias = "NEUTRO"

    return bias, suporte, resistencia

def detectar_fvg(candles):
    """
    Identifica Fair Value Gaps (Ineficiências) na sequência de 3 velas.
    """
    if len(candles) < 3:
        return None, 0.0

    v1, v2, v3 = candles[-3], candles[-2], candles[-1]

    # FVG de Alta
    if v3['low'] > v1['high']:
        gap = v3['low'] - v1['high']
        return "BULLISH", gap

    # FVG de Baixa
    elif v3['high'] < v1['low']:
        gap = v1['low'] - v3['high']
        return "BEARISH", gap

    return None, 0.0


async def analisar_estrategia(connection, bot_status):
    """
    Motor SMC Completo: H1 (Bias + Suporte/Resistência) -> M5 (Estrutura) -> M1 (Refinamento)
    """
    symbol = "XAUUSD"

    # 1. Carregar histórico de velas dos 3 Timeframes
    candles_h1 = await obter_historico(connection, symbol, "1h", count=15)
    candles_m5 = await obter_historico(connection, symbol, "5m", count=10)
    candles_m1 = await obter_historico(connection, symbol, "1m", count=10)

    if not candles_h1 or not candles_m5 or not candles_m1:
        print("⏳ A aguardar sincronização dos dados históricos dos 3 timeframes...")
        return

    # 2. Análise H1: Tendência Maior + Suporte/Resistência
    bias_h1, suporte_h1, resistencia_h1 = analisar_bias_h1(candles_h1)
    preco_atual = candles_m1[-1]['close']

    print(f"\n📊 [ANALISE H1] Bias: {bias_h1} | Suporte: {suporte_h1:.2f} | Resistência: {resistencia_h1:.2f} | Preço: {preco_atual:.2f}")

    # 3. Análise M5: Estrutura FVG
    tipo_fvg_m5, gap_m5 = detectar_fvg(candles_m5)

    # 4. Análise M1: Confirmação de Entrada
    tipo_fvg_m1, gap_m1 = detectar_fvg(candles_m1)

    # ---------------------------------------------------------
    # CONFLUÊNCIA DE COMPRA (BUY)
    # ---------------------------------------------------------
    # Regras: Bias H1 deve ser BULLISH + Preço acima do Suporte H1 + FVG em M5 + Confirmação em M1
    if bias_h1 == "BULLISH" and preco_atual > suporte_h1:
        if tipo_fvg_m5 == "BULLISH" and tipo_fvg_m1 == "BULLISH":
            print(f"🚀 [SINAL CONFLUENTE - BUY] H1 Bullish + FVG M5 + FVG M1! Gap M1: {gap_m1:.2f}")
            bot_status["last_signals"].append(f"BUY {symbol} - Confluência Multi-Timeframe")

            from bot_engine import executar_ordem
            sl_price = preco_atual - 15.0  # Stop Loss reduzido para $15 (150 pips) devido à precisão M1
            tp_price = preco_atual + 45.0  # Risco/Retorno 1:3 ($45 de ganho)
            await executar_ordem(connection, symbol, "BUY", 0.01, sl=sl_price, tp=tp_price)

    # ---------------------------------------------------------
    # CONFLUÊNCIA DE VENDA (SELL)
    # ---------------------------------------------------------
    # Regras: Bias H1 deve ser BEARISH + Preço abaixo da Resistência H1 + FVG em M5 + Confirmação em M1
    elif bias_h1 == "BEARISH" and preco_atual < resistencia_h1:
        if tipo_fvg_m5 == "BEARISH" and tipo_fvg_m1 == "BEARISH":
            print(f"🚀 [SINAL CONFLUENTE - SELL] H1 Bearish + FVG M5 + FVG M1! Gap M1: {gap_m1:.2f}")
            bot_status["last_signals"].append(f"SELL {symbol} - Confluência Multi-Timeframe")

            from bot_engine import executar_ordem
            sl_price = preco_atual + 15.0
            tp_price = preco_atual - 45.0
            await executar_ordem(connection, symbol, "SELL", 0.01, sl=sl_price, tp=tp_price)

    else:
        print("🔍 Sem confluência no momento. O robô rejeitou ordens fora da tendência H1.")
