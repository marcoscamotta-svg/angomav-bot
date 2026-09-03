import asyncio
import os
import urllib.parse
import urllib.request
from datetime import datetime

# Configurações do WhatsApp (CallMeBot)
WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE", "")  # Ex: 2449XXXXXXXX
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")

precos_historico = []

def enviar_whatsapp(mensagem):
    """ Envia alerta instantâneo para o WhatsApp """
    if not WHATSAPP_PHONE or not WHATSAPP_API_KEY:
        return
    try:
        texto_enc = urllib.parse.quote(mensagem)
        url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={texto_enc}&apikey={WHATSAPP_API_KEY}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"⚠️ Erro ao enviar WhatsApp: {e}")

async def analisar_estrategia(connection, bot_status):
    global precos_historico
    symbol = "XAUUSD"
    current_price = 0.0

    try:
        price_data = await connection.get_symbol_price(symbol)
        if price_data:
            current_price = price_data.get("bid", 0.0)
    except Exception:
        return

    if current_price == 0.0:
        return

    try:
        account_info = await connection.get_account_information()
        if account_info:
            bot_status["equity"] = round(account_info.get("equity", 0), 2)
            bot_status["balance"] = round(account_info.get("balance", 0), 2)
    except Exception:
        pass

    hora_atual = datetime.now().strftime("%H:%M:%S")
    bot_status["online"] = True
    bot_status["connected"] = True
    bot_status["last_scan"] = hora_atual

    precos_historico.append(current_price)
    if len(precos_historico) > 10:
        precos_historico.pop(0)

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

    bias_str = "BULLISH" if choch_bullish else ("BEARISH" if choch_bearish else "NEUTRO")
    
    bot_status["last_signals"] = [{
        "timeframe_h1": f"Ativo: {symbol} | Preço: {current_price} | Viés: {bias_str}",
        "timeframe_m15": f"Estrutura Alta: {fvg_bullish}",
        "timeframe_m1": f"Rompimento: {choch_bullish or choch_bearish}"
    }]

    positions = []
    try:
        positions = await connection.get_positions()
    except Exception:
        pass

    if len(positions) == 0:
        volume = 0.01
        
        # NOVAS DISTÂNCIAS DE SL E TP (Amplia o respiro da operação)
        DISTANCIA_SL = 10.0  # $10 de Stop Loss
        DISTANCIA_TP = 20.0  # $20 de Take Profit (R:R 1:2)

        # GATILHO COMPRA
        if fvg_bullish and choch_bullish:
            sl = round(current_price - DISTANCIA_SL, 2)
            tp = round(current_price + DISTANCIA_TP, 2)
            
            print(f"🚀 [SINAL DETETADO] COMPRA em {symbol} | Preço: {current_price}")
            try:
                result = await connection.create_market_buy_order(
                    symbol=symbol, volume=volume, stop_loss=sl, take_profit=tp
                )
                print(f"✅ Ordem executada: {result}")
                
                # Notificação WhatsApp
                msg = f"🚀 *COMPRA EXECUTADA (XAUUSD)*\n📍 Preço: {current_price}\n🛑 SL: {sl}\n🎯 TP: {tp}\n📦 Lote: {volume}"
                enviar_whatsapp(msg)
                
                precos_historico.clear()
            except Exception as err_order:
                print(f"⚠️ Erro ao enviar ordem: {err_order}")

        # GATILHO VENDA
        elif fvg_bearish and choch_bearish:
            sl = round(current_price + DISTANCIA_SL, 2)
            tp = round(current_price - DISTANCIA_TP, 2)
            
            print(f"🔻 [SINAL DETETADO] VENDA em {symbol} | Preço: {current_price}")
            try:
                result = await connection.create_market_sell_order(
                    symbol=symbol, volume=volume, stop_loss=sl, take_profit=tp
                )
                print(f"✅ Ordem executada: {result}")
                
                # Notificação WhatsApp
                msg = f"🔻 *VENDA EXECUTADA (XAUUSD)*\n📍 Preço: {current_price}\n🛑 SL: {sl}\n🎯 TP: {tp}\n📦 Lote: {volume}"
                enviar_whatsapp(msg)
                
                precos_historico.clear()
            except Exception as err_order:
                print(f"⚠️ Erro ao enviar ordem: {err_order}")
