import asyncio

async def analisar_estrategia(connection, bot_status):
    """
    Constrói velas de 5m em memória e analisa o FVG mantendo apenas a janela das últimas 3 velas.
    """
    if "candles_m5" not in bot_status:
        bot_status["candles_m5"] = []
        bot_status["temp_ticks"] = []

    # 1. Obter preço atual do XAUUSD
    price_data = await connection.get_symbol_price("XAUUSD")
    current_price = price_data.get("bid", 0.0)

    if current_price == 0.0:
        return

    bot_status["temp_ticks"].append(current_price)

    # Simulação: Cada 20 ticks formam 1 vela de 5m (ajuste para acumulação)
    if len(bot_status["temp_ticks"]) >= 20:
        high_p = max(bot_status["temp_ticks"])
        low_p = min(bot_status["temp_ticks"])
        close_p = bot_status["temp_ticks"][-1]
        open_p = bot_status["temp_ticks"][0]

        nueva_vela = {
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p
        }

        bot_status["candles_m5"].append(nueva_vela)
        bot_status["temp_ticks"] = []  # Reseta ticks para a próxima vela

        # Mantém SEMPRE apenas as últimas 3 velas fechadas na memória
        if len(bot_status["candles_m5"]) > 3:
            bot_status["candles_m5"].pop(0)

    total_candles = len(bot_status["candles_m5"])
    print(f"👀 [M5 MONITOR] Preço: {current_price:.2f} | Candles concluídos: {total_candles}/3")

    # 2. Quando tivermos exatamente 3 velas na memória, avalia o FVG
    if total_candles == 3:
        v1 = bot_status["candles_m5"][0]
        v2 = bot_status["candles_m5"][1]
        v3 = bot_status["candles_m5"][2]

        # FVG de Alta (Bullish FVG)
        if v3["low"] > v1["high"]:
            gap = v3["low"] - v1["high"]
            print(f"🚀 [SINAL SMC] Bullish FVG Detetado! Gap: {gap:.2f}")
            bot_status["last_signals"].append(f"BUY XAUUSD - FVG ({gap:.2f})")
            
            # Importa e executa ordem de Compra
            from bot_engine import executar_ordem
            sl_price = current_price - 25.0  # Stop Loss de 250 pips ($25 em 0.01)
            tp_price = current_price + 50.0  # Take Profit de 500 pips ($50 em 0.01)
            await executar_ordem(connection, "XAUUSD", "BUY", 0.01, sl=sl_price, tp=tp_price)
            
            # Limpa as velas para reiniciar o ciclo de análise
            bot_status["candles_m5"] = []

        # FVG de Baixa (Bearish FVG)
        elif v3["high"] < v1["low"]:
            gap = v1["low"] - v3["high"]
            print(f"🚀 [SINAL SMC] Bearish FVG Detetado! Gap: {gap:.2f}")
            bot_status["last_signals"].append(f"SELL XAUUSD - FVG ({gap:.2f})")
            
            # Importa e executa ordem de Venda
            from bot_engine import executar_ordem
            sl_price = current_price + 25.0
            tp_price = current_price - 50.0
            await executar_ordem(connection, "XAUUSD", "SELL", 0.01, sl=sl_price, tp=tp_price)
            
            # Limpa as velas para reiniciar o ciclo de análise
            bot_status["candles_m5"] = []
