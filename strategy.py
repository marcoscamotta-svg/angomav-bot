# ==========================================
# ESTRATEGIA SMC - DETECAO DE FVG (XAUUSD M5)
# REGRA DE MESA PROPRIETARIA ($5,000)
# ==========================================

async def analisar_estrategia(connection, bot_status):
    """
    Monitora XAUUSD, calcula a estrutura de FVG e executa
    ordens respeitando o risco de $25 (0.5%) por trade.
    """
    try:
        # 1. Obter cotação atual
        price_info = await connection.get_symbol_price("XAUUSD")
        if not price_info or 'bid' not in price_info:
            return

        bid = price_info['bid']
        ask = price_info['ask']

        # 2. Verificar se já existe posição aberta (evita overtrading)
        positions = await connection.get_positions()
        xau_positions = [p for p in positions if p.get('symbol') == "XAUUSD"]
        if len(xau_positions) > 0:
            return

        # 3. Ler histórico de preços M5 via MetaApi RPC
        terminal_state = connection.terminal_state
        candles = terminal_state.price_history.get("XAUUSD", {}).get("5m", [])

        if len(candles) < 3:
            print(f"👀 [MONITOR] XAUUSD | Bid: {bid:.2f} | Ask: {ask:.2f} (Aguardando matriz M5...)")
            return

        v1 = candles[-3] # Vela 1
        v2 = candles[-2] # Vela 2
        v3 = candles[-1] # Vela 3

        symbol = "XAUUSD"
        volume = 0.01

        # Bullish FVG (Sinal de COMPRA: Mínima da V3 > Máxima da V1)
        if v3['low'] > v1['high']:
            sl = ask - 2.50  # SL 250 pips ($25)
            tp = ask + 5.00  # TP 500 pips ($50)
            
            msg = f"🟢 [COMPRA] FVG de Alta Detetado! SL: {sl:.2f} | TP: {tp:.2f}"
            print(msg)
            
            await connection.create_market_buy_order(
                symbol=symbol,
                volume=volume,
                stop_loss=sl,
                take_profit=tp
            )
            if msg not in bot_status["last_signals"]:
                bot_status["last_signals"].insert(0, msg)

        # Bearish FVG (Sinal de VENDA: Máxima da V3 < Mínima da V1)
        elif v3['high'] < v1['low']:
            sl = bid + 2.50  # SL 250 pips ($25)
            tp = bid - 5.00  # TP 500 pips ($50)
            
            msg = f"🔴 [VENDA] FVG de Baixa Detetado! SL: {sl:.2f} | TP: {tp:.2f}"
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
        print(f"⚠️ Erro ao analisar estratégia: {e}")
