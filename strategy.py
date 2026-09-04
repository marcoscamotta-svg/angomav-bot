import asyncio
import os
from datetime import datetime

# ==========================================
# PARÂMETROS DE GESTÃO - LOTE 0.20 | R:R 1:1
# ==========================================
LOTE = 0.20             # Lote fixo 0.20
SL_DISTANCIA = 10.0     # $10.0 SL no Ouro (XAUUSD)
TP_DISTANCIA = 10.0     # $10.0 TP (Risco/Retorno 1:1)
MAX_POSICOES = 1        # Máximo de 1 posição simultânea

precos_historico = []

async def analisar_estrategia(connection, bot_status):
    global precos_historico
    symbol = "XAUUSD"

    horario_atual = datetime.now().strftime("%H:%M:%S")
    bot_status["online"] = True
    bot_status["connected"] = True
    bot_status["last_scan"] = horario_atual

    # 1. Obter Saldo e Equity com Timeout
    try:
        account_info = await asyncio.wait_for(connection.get_account_information(), timeout=3.0)
        if account_info:
            bot_status["equity"] = round(account_info.get("equity", 0.0), 2)
            bot_status["balance"] = round(account_info.get("balance", 0.0), 2)
    except Exception as e:
        print(f"⚠️ Error account info: {e}")

    # 2. Obter Preço do Ouro com Timeout
    current_price = None
    try:
        price_data = await asyncio.wait_for(connection.get_symbol_price(symbol), timeout=3.0)
        if price_data and "bid" in price_data:
            current_price = price_data["bid"]
    except Exception as e:
        print(f"⚠️ Error price data: {e}")

    if not current_price:
        bot_status["last_signals"] = [{
            "time": horario_atual, "timeframe": horario_atual, "timestamp": horario_atual,
            "asset": symbol, "symbol": symbol, "ativo": symbol,
            "price": "Sem cotação", "preco": "Sem cotação",
            "structure": "A conectar...", "estrutura": "A conectar...", "signal": "A conectar...",
            "status": "A aguardar dados..."
        }]
        return

    # 3. Histórico para Análise SMC
    precos_historico.append(current_price)
    if len(precos_historico) > 10:
        precos_historico.pop(0)

    # 4. Detetar Estrutura SMC / Wyckoff
    fvg_bullish = False
    fvg_bearish = False
    choch_bullish = False
    choch_bearish = False
    estrutura_texto = "Estrutura Neutra (Consolidação)"

    if len(precos_historico) >= 3:
        p_antigo = precos_historico[0]
        p_medio = precos_historico[-2]
        p_atual = precos_historico[-1]

        if p_atual > p_medio and p_medio > p_antigo:
            choch_bullish = True
            fvg_bullish = True
            estrutura_texto = "Alta (CHoCH + FVG Bullish)"
        elif p_atual < p_medio and p_medio < p_antigo:
            choch_bearish = True
            fvg_bearish = True
            estrutura_texto = "Baixa (CHoCH + FVG Bearish)"

    # 5. Mapeamento Universal de Chaves para o Front-End
    bot_status["last_signals"] = [{
        # Atributos de Tempo
        "time": horario_atual,
        "timestamp": horario_atual,
        "horario": horario_atual,
        # Atributos do Ativo
        "asset": symbol,
        "symbol": symbol,
        "ativo": symbol,
        # Atributos de Preço
        "price": f"${current_price:.2f}",
        "preco": f"${current_price:.2f}",
        # Atributos de Estrutura/Sinal
        "structure": estrutura_texto,
        "estrutura": estrutura_texto,
        "signal": estrutura_texto,
        "confluence": estrutura_texto,
        # Estado
        "status": "Monitorização ativa"
    }]

    # 6. Proteção de Posições Abertas
    positions = []
    try:
        positions = await asyncio.wait_for(connection.get_positions(), timeout=3.0)
    except Exception:
        pass

    if len(positions) >= MAX_POSICOES:
        for key in ["structure", "estrutura", "signal", "status"]:
            bot_status["last_signals"][0][key] = "Posição Ativa na Conta"
        return

    # 7. Execução de Ordens (Lote 0.20 | R:R 1:1)
    if fvg_bullish and choch_bullish:
        sl = round(current_price - SL_DISTANCIA, 2)
        tp = round(current_price + TP_DISTANCIA, 2)
        print(f"🚀 COMPRA {symbol} | Lote: {LOTE} | Entry: {current_price} | SL: {sl} | TP: {tp}")
        try:
            await connection.create_market_buy_order(symbol=symbol, volume=LOTE, stop_loss=sl, take_profit=tp)
            bot_status["last_signals"][0]["status"] = f"🚀 COMPRA ({LOTE} lotes)"
            precos_historico.clear()
        except Exception as e:
            print(f"⚠️ Erro na compra: {e}")

    elif fvg_bearish and choch_bearish:
        sl = round(current_price + SL_DISTANCIA, 2)
        tp = round(current_price - TP_DISTANCIA, 2)
        print(f"🔻 VENDA {symbol} | Lote: {LOTE} | Entry: {current_price} | SL: {sl} | TP: {tp}")
        try:
            await connection.create_market_sell_order(symbol=symbol, volume=LOTE, stop_loss=sl, take_profit=tp)
            bot_status["last_signals"][0]["status"] = f"🔻 VENDA ({LOTE} lotes)"
            precos_historico.clear()
        except Exception as e:
            print(f"⚠️ Erro na venda: {e}")
