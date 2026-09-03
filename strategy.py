import time

# ==========================================
# ESTRATEGIA SMC - GERADOR DE CANDLES M5
# REGRA DE MESA PROPRIETARIA ($5,000)
# ==========================================

async def analisar_estrategia(connection, bot_status):
    """
    Constrói velas M5 em tempo real a partir de ticks RPC
    e calcula a presença de Fair Value Gaps (FVG).
    """
    try:
        # 1. Obter cotação atual
        price_info = await connection.get_symbol_price("XAUUSD")
        if not price_info or 'bid' not in price_info:
            return

        bid = price_info['bid']
        ask = price_info['ask']
        preco_atual = (bid + ask) / 2.0
        agora = time.time()

        # 2. Inicializar estrutura de candles M5 no estado do bot
        if "m5_candles" not in bot_status:
            bot_status["m5_candles"] = []
            bot_status["current_candle"] = None

        curr = bot_status["current_candle"]

        # Intervalo de 5 minutos (300 segundos)
        if curr is None or (agora - curr["start_time"]) >= 300:
            if curr is not None:
                bot_status["m5_candles"].append(curr)
                if len(bot_status["m5_candles"]) > 10:
                    bot_status["m5_candles"].pop(0)

            # Novo candle M5
            bot_status["current_candle"] = {
                "start_time": agora,
                "open": preco_atual,
                "high": preco_atual,
                "low": preco_atual,
                "close": preco_atual
            }
        else:
            # Atualizar candle M5 em andamento
            curr["high"] = max(curr["high"], preco_atual)
            curr["low"] = min(curr["low"], preco_atual)
            curr["close"] = preco_atual

        candles = bot_status["m5_candles"]

        # Log simples de monitorização no celular
        print(f"👀 [M5 MONITOR] Preço: {preco_atual:.2f} | Candles concluídos: {len(candles)}/3")

        # 3. Análise de FVG assim que tivermos 3 velas M5 fechadas
        if len(candles) >= 3:
            v1, v2, v3 = candles[-3], candles[-2], candles[-1]

            # Trava para evitar mais de 1 ordem aberta
            positions = await connection.get_positions()
            xau_positions = [p for p in positions if p.get('symbol') == "XAUUSD"]
            if len(xau_positions) > 0:
                return

            symbol = "XAUUSD"
            volume = 0.01

            # Bullish FVG
            if v3['low'] > v1['high']:
                sl = ask - 2.50
                tp = ask + 5.00
                msg = f"🟢 [COMPRA FVG] SL: {sl:.2f} | TP: {tp:.2f}"
                print(msg)
                await connection.create_market_buy_order(symbol=symbol, volume=volume, stop_loss=sl, take_profit=tp)

            # Bearish FVG
            elif v3['high'] < v1['low']:
                sl = bid + 2.50
                tp = bid - 5.00
                msg = f"🔴 [VENDA FVG] SL: {sl:.2f} | TP: {tp:.2f}"
                print(msg)
                await connection.create_market_sell_order(symbol=symbol, volume=volume, stop_loss=sl, take_profit=tp)

    except Exception as e:
        print(f"⚠️ Erro no processamento M5: {e}")
