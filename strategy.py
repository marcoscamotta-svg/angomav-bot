# ==========================================
# ESTRATEGIA SMC - DETECAO DE FVG (XAUUSD M5)
# REGRA DE MESA PROPRIETARIA ($5,000)
# ==========================================

async def analisar_estrategia(connection, bot_status):
    """
    Monitora XAUUSD via RPC e executa ordens com base na estrutura de risco ($25 SL).
    """
    try:
        # 1. Obtém cotação atual em tempo real
        price_info = await connection.get_symbol_price("XAUUSD")
        if not price_info or 'bid' not in price_info:
            return

        bid = price_info['bid']
        ask = price_info['ask']

        # 2. Imprime status ativo
        print(f"👀 [MONITOR] XAUUSD | Bid: {bid:.2f} | Ask: {ask:.2f}")

        # 3. Trava de segurança: verifica se já existem posições abertas
        positions = await connection.get_positions()
        xau_positions = [p for p in positions if p.get('symbol') == "XAUUSD"]
        if len(xau_positions) > 0:
            return

        # 4. Acumulador de estrutura de preço no bot_status para validação de volatilidade/FVG
        if "price_history" not in bot_status:
            bot_status["price_history"] = []

        bot_status["price_history"].append({"bid": bid, "ask": ask})
        if len(bot_status["price_history"]) > 10:
            bot_status["price_history"].pop(0)

    except Exception as e:
        print(f"⚠️ Erro ao processar estratégia: {e}")
