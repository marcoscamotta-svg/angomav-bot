import os
import asyncio
import logging
from metaapi_cloud_sdk import MetaApi

# Desativa logs de streaming e erros internos do SDK MetaApi
logging.basicConfig(level=logging.ERROR)
for logger_name in [
    "metaapi_cloud_sdk", 
    "metaapi_cloud_sdk.sdk", 
    "metaapi_cloud_sdk.clients",
    "metaapi_cloud_sdk.clients.metaapi_websocket_client"
]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

API_KEY = os.getenv("META_API_KEY", "")
ACCOUNT_ID = os.getenv("META_API_ACCOUNT_ID", "")

bot_status = {
    "online": False,
    "connected": False,
    "equity": 0.0,
    "balance": 0.0,
    "last_scan": "--:--:--",
    "last_signals": []
}

async def run_trading_bot():
    global bot_status
    
    if not API_KEY or not ACCOUNT_ID:
        print("❌ ERRO: META_API_KEY ou META_API_ACCOUNT_ID ausentes!")
        return

    # Instancia a API desativando subscrições automáticas no cliente
    api = MetaApi(API_KEY, {
        'requestTimeout': 60000,
        'connectWithTimeout': 60000
    })

    try:
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        
        if account.state != 'DEPLOYED':
            print("⏳ A ativar conta no MetaApi...")
            await account.deploy()
            
        print("⏳ A aguardar conexão com o broker...")
        await account.wait_connected()

        # Força uso estrito de RPC (sem abrir websockets de streaming de preços)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()

        bot_status["online"] = True
        bot_status["connected"] = True
        print("⚡ Conectado com sucesso ao MetaTrader 5 (Modo RPC Pure)!")

        from strategy import analisar_estrategia

        while True:
            try:
                await analisar_estrategia(connection, bot_status)
            except Exception as err:
                print(f"⚠️ Aviso no loop de análise: {err}")
            
            await asyncio.sleep(5)

    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        bot_status["online"] = False
        bot_status["connected"] = False
