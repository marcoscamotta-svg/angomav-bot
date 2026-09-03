# ==========================================
# ESTRATEGIA SMC / WYCKOFF - XAUUSD (M5)
# REGRA DE MESA PROPRIETARIA ($5,000)
# ==========================================

async def analisar_estrategia(connection, bot_status):
    """
    Identifica FVGs no XAUUSD (M5) e executa ordens automáticas
    com risco fixado em 0.5% ($25) para conta de $5.000.
    """
    try:
        candles = await connection.get_candlesticks("XAUUSD", "5m", limit=15)
        
        if not candles or len(candles) < 3:
            return

        v1 = candles[-3]
        v2 = candles[-2]
        v3 = candles[-1]

        # Verifica se já existem posições abertas para evitar overtrading
        positions = await connection.get_positions()
        xau_positions = [p for p in positions if p['symbol'] == "XAUUSD"]
        if len(xau_positions) > 0:
            return  # Já tem ordem aberta, aguarda finalizar

        symbol = "XAUUSD"
        volume = 0.01  # Lote conservador para $5k
        price_ask = v3['close']

        # Bullish FVG (Sinal de COMPRA)
        if v3['low'] > v1['high']:
            sl = price_ask - 2.50  # SL de 250 pips ($25 de risco)
            tp = price_ask + 5.00  # TP de 500 pips ($50 de lucro)
            
            msg = f"🟢 [COMPRA XAUUSD M5] FVG Detetado! SL: {sl:.2f} | TP: {tp:.2f}"
            print(msg)
            
            await connection.create_market_buy_order(
                symbol=symbol,
                volume=volume,
                stop_loss=sl,
                take_profit=tp
            )
            if msg not in bot_status["last_signals"]:
                bot_status["last_signals"].insert(0, msg)

        # Bearish FVG (Sinal de VENDA)
        elif v3['high'] < v1['low']:
            sl = price_ask + 2.50  # SL de 250 pips ($25 de risco)
            tp = price_ask - 5.00  # TP de 500 pips ($50 de lucro)
            
            msg = f"🔴 [VENDA XAUUSD M5] FVG Detetado! SL: {sl:.2f} | TP: {tp:.2f}"
            print(msg)
            
            await connection.create_market_sell_order(
                symbol=symbol,
                volume=volume,
                stop_loss=sl,
                take_profit=tp
            )
            if msg not in bot_status["last_signals"]:
                bot_status["last_signals"].insert(0, msg)

    except Exception as e:
        print(f"⚠️ Erro ao analisar/executar estrategia: {e}")
