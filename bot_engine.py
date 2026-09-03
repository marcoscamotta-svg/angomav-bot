import os
import asyncio
from datetime import datetime
from metaapi_cloud_sdk import MetaApi
from strategy import analisar_estrategia

TOKEN = os.environ.get("META_API_TOKEN")
ACCOUNT_ID = os.environ.get("META_API_ACCOUNT_ID")

bot_status = {
    "connected": False,
    "equity": 0.0,
    "balance": 0.0,
    "last_update": "-",
    "last_signals": []
}

# ==========================================
# FUNÇÕES DE EXECUÇÃO DE ORDENS (MT5)
# ==========================================

async def executar_ordem(connection, symbol, action, volume, sl=None, tp=None):
    """
    Executa ordem de COMPRA (BUY) ou VENDA (SELL) a mercado no MT5 via MetaApi.
    """
    try:
        print(f"🚀 [ORDEM] Enviando ordem para {symbol} | Ação: {action}")
        if action.upper() == "BUY":
            res = await connection.create_market_buy_order(
                symbol=symbol,
                volume=volume,
                stop_loss=sl,
                take_profit=tp
            )
        elif action.upper() == "SELL":
            res = await connection.create_market_sell_order(
                symbol=symbol,
                volume=volume,
                stop_loss=sl,
                take_profit=tp
            )
        print("✅ [ORDEM] Executada com sucesso no MT5!")
        return res
    except Exception as e:
        print(f"❌ [ERRO TRADING] Falha ao executar {action}: {e}")
        return None

async def fechar_todas_posicoes(connection, symbol=None):
    """
    Fecha posições abertas no MT5.
    """
    try:
        positions = await connection.get_positions()
        for pos in positions:
            if symbol is None or pos['symbol'] == symbol:
                print(f"🔴 [FECHO] Encerrando posição #{pos['id']} ({pos['symbol']})...")
                await connection.close_position(pos['id'])
                print(f"✅ [FECHO] Posição #{pos['id']} encerrada.")
    except Exception as e:
        print(f"❌ [ERRO FECHO] Falha ao fechar posições: {e}")

# ==========================================
# LOOP DE VARREDURA / ANÁLISE
# ==========================================

async def run_trading_bot():
    if not TOKEN or not ACCOUNT_ID:
        print("❌ Variaveis META_API_TOKEN ou META_API_ACCOUNT_ID nao foram encontradas!")
        return

    # Desativa a subscricao automatica em background para evitar TimeoutException
    api = MetaApi(TOKEN, {'subscribeToMarketData': False})

    while True:
        try:
            account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
            connection = account.get_rpc_connection()
            await connection.connect()
            
            # Sincronização leve e sem timeout rígido
            try:
                await connection.wait_synchronized(timeout_in_seconds=15)
            except Exception as sync_err:
                print(f"⚠️ Aviso na sincronização inicial (continuando): {sync_err}")

            bot_status["connected"] = True
            print("⚡ Conectado com sucesso ao servidor da MetaApi!")

            while True:
                # 1. Atualiza métricas da conta
                account_information = await connection.get_account_information()
                bot_status["equity"] = account_information.get("equity", 0.0)
                bot_status["balance"] = account_information.get("balance", 0.0)
                bot_status["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 2. Executa a análise isolada do strategy.py
                try:
                    await analisar_estrategia(connection, bot_status)
                except Exception as strat_err:
                    print(f"⚠️ Aviso na estratégia: {strat_err}")

                await asyncio.sleep(15)

        except Exception as e:
            bot_status["connected"] = False
            print(f"❌ Erro no loop do bot: {e}. Reconectando em 15s...")
            await asyncio.sleep(15)
