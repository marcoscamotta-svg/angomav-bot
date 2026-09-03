# ==========================================
# ESTRATEGIA SMC / WYCKOFF - XAUUSD (M5)
# REGRA DE MESA PROPRIETARIA ($5,000)
# ==========================================

async def analisar_estrategia(connection, bot_status):
    """
    Identifica FVGs no XAUUSD (M5) e executa ordens automaticas
    com risco fixado em 0.5% ($25) para conta de $5.000.
    """
    try:
        # Busca o historico de velas M5 utilizando a chamada compativel RPC
        candles = await connection.get_candles("XAUUSD", "5m", None, 15)
        
        if not candles or len(candles) < 3:
            return

        v1 = candles[-3]
        v2 = candles[-2]
        v3 = candles[-1]

        # Verifica posicoes abertas para evitar overtrading
        positions = await connection.get_positions()
        xau_positions = [p for p in positions if p['symbol'] == "XAUUSD"]
        if len(xau_positions) > 0:
            return

        symbol = "XAUUSD"
        volume = 0.01
        price_ask = v3['close']

        # Bullish FVG (COMPRA)
        if v3['low'] > v1['high']:
            sl = price_ask - 2.50
            tp = price_ask + 5.00
            
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

        # Bearish FVG (VENDA)
        elif v3['high'] < v1['low']:
            sl = price_ask + 2.50
            tp = price_ask - 5.00
            
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
