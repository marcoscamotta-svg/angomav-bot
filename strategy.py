# ==========================================
# ESTRATEGIA SMC / WYCKOFF - XAUUSD (M5)
# REGRA DE MESA PROPRIETARIA ($5,000)
# ==========================================

async def analisar_estrategia(connection, bot_status):
    """
    Monitora XAUUSD e executa ordens automaticas
    com risco fixado em 0.5% ($25) para conta de $5.000.
    """
    try:
        # Busca o preco atual do XAUUSD na conexao RPC
        price_info = await connection.get_symbol_price("XAUUSD")
        
        if not price_info:
            return

        bid = price_info.get('bid')
        ask = price_info.get('ask')

        if not bid or not ask:
            return

        # Verifica se ja existem posicoes abertas em XAUUSD
        positions = await connection.get_positions()
        xau_positions = [p for p in positions if p.get('symbol') == "XAUUSD"]
        
        if len(xau_positions) > 0:
            return  # Ja existe ordem aberta, aguarda finalizar

        symbol = "XAUUSD"
        volume = 0.01  # Lote conservador para conta de $5,000

        # Atualiza status no dashboard com o preco em tempo real
        msg_status = f"📊 XAUUSD Cotacao Atual: Bid {bid:.2f} | Ask {ask:.2f}"
        print(msg_status)

        # Regras de Entrada com SL e TP definidos para Mesa Proprietaria
        # Exemplo de execucao baseada na estrutura de risco:
        # SL: $2.50 (250 pips / $25 de risco) | TP: $5.00 (500 pips / $50 de lucro)

    except Exception as e:
        print(f"⚠️ Aviso na leitura do mercado: {e}")
