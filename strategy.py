# ==========================================
# ESTRATEGIA SMC / WYCKOFF - XAUUSD (M5)
# ==========================================

async def analisar_estrategia(connection, bot_status):
    """
    Le os ultimos dados de M5 do XAUUSD e procura por Fair Value Gaps (FVG).
    Modo Alerta: Apenas regista os sinais nos logs sem abrir ordens reais.
    """
    try:
        candles = await connection.get_candlesticks("XAUUSD", "5m", limit=15)
        
        if not candles or len(candles) < 3:
            return

        v1 = candles[-3]
        v2 = candles[-2]
        v3 = candles[-1]

        # Bullish FVG (Gap de Alta)
        if v3['low'] > v1['high']:
            gap_size = round(v3['low'] - v1['high'], 2)
            msg = f"🟢 [SINAL M5 XAUUSD] Bullish FVG detetado! Gap: {gap_size}"
            print(msg)
            if msg not in bot_status["last_signals"]:
                bot_status["last_signals"].insert(0, msg)
                bot_status["last_signals"] = bot_status["last_signals"][:5]

        # Bearish FVG (Gap de Baixa)
        elif v3['high'] < v1['low']:
            gap_size = round(v1['low'] - v3['high'], 2)
            msg = f"🔴 [SINAL M5 XAUUSD] Bearish FVG detetado! Gap: {gap_size}"
            print(msg)
            if msg not in bot_status["last_signals"]:
                bot_status["last_signals"].insert(0, msg)
                bot_status["last_signals"] = bot_status["last_signals"][:5]

    except Exception as e:
        pass
