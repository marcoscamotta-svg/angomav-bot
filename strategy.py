import asyncio
import os
from datetime import datetime

# ==========================================
# PARÂMETROS DE GESTÃO - LOTE 0.30 | R:R 1:1
# ==========================================
LOTE = 0.30             # Lote ajustado para 0.30
SL_DISTANCIA = 10.0     # $10.0 de Stop Loss no Ouro (XAUUSD)
TP_DISTANCIA = 10.0     # $10.0 de Take Profit (Risco/Retorno 1:1)
MAX_POSICOES = 1        # Permite apenas 1 posição aberta por vez

precos_historico = []

async def analisar_estrategia(connection, bot_status):
    global precos_historico
    symbol = "XAUUSD"

    # 1. Obter Preço Atual
    try:
        price_data = await connection.get_symbol_price(symbol)
        if not price_data or "bid" not in price_data:
            return
        current_price = price_data["bid"]
    except Exception:
        return

    # 2. Atualizar Status e Saldo
    try:
        account_info = await connection.get_account_information()
        if account_info:
            bot_status["equity"] = round(account_info.get("equity", 0), 2)
            bot_status["balance"] = round(account_info.get("balance", 0), 2)
    except Exception:
        pass

    bot_status["online"] = True
    bot_status["connected"] = True
    bot_status["last_scan"] = datetime.now().strftime("%H:%M:%S")

    # 3. Guardar histórico de preços para lógica SMC
    precos_historico.append(current_price)
    if len(precos_historico) > 10:
        precos_historico.pop(0)

    # 4. Verificar se já existem posições abertas
    positions = []
    try:
        positions = await connection.get_positions()
    except Exception:
        pass

    # Trava de Segurança: Não abre nova posição se já houver 1 aberta
    if len(positions) >= MAX_POSICOES:
        return

    # 5. Deteção de Gatilho SMC (CHoCH + FVG Simplificado)
    fvg_bullish = False
    fvg_bearish = False
    choch_bullish = False
    choch_bearish = False

    if len(precos_historico) >= 3:
        p_antigo = precos_historico[0]
        p_medio = precos_historico[-2]
        p_atual = precos_historico[-1]

        if p_atual > p_medio and p_medio > p_antigo:
            choch_bullish = True
            fvg_bullish = True
        elif p_atual < p_medio and p_medio < p_antigo:
            choch_bearish = True
            fvg_bearish = True

    # 6. Execução de Ordens com Lote 0.30 e R:R 1:1 ($10 SL / $10 TP)
    if fvg_bullish and choch_bullish:
        sl = round(current_price - SL_DISTANCIA, 2)
        tp = round(current_price + TP_DISTANCIA, 2)
        
        print(f"🚀 [MESA PROPRIETÁRIA] COMPRA em {symbol} | Lote: {LOTE} | Entrada: {current_price} | SL: {sl} | TP: {tp}")
        try:
            await connection.create_market_buy_order(
                symbol=symbol, volume=LOTE, stop_loss=sl, take_profit=tp
            )
            precos_historico.clear()
        except Exception as e:
            print(f"⚠️ Erro ao executar compra: {e}")

    elif fvg_bearish and choch_bearish:
        sl = round(current_price + SL_DISTANCIA, 2)
        tp = round(current_price - TP_DISTANCIA, 2)
        
        print(f"🔻 [MESA PROPRIETÁRIA] VENDA em {symbol} | Lote: {LOTE} | Entrada: {current_price} | SL: {sl} | TP: {tp}")
        try:
            await connection.create_market_sell_order(
                symbol=symbol, volume=LOTE, stop_loss=sl, take_profit=tp
            )
            precos_historico.clear()
        except Exception as e:
            print(f"⚠️ Erro ao executar venda: {e}")
