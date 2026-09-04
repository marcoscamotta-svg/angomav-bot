import os
import asyncio
import logging
from metaapi_cloud_sdk import MetaApi

# Desativa logs de erro do streaming do SDK para não poluir o terminal
logging.basicConfig(level=logging.ERROR)
for logger in ["metaapi_cloud_sdk", "metaapi_cloud_sdk.sdk", "metaapi_cloud_sdk.clients"]:
    logging.getLogger(logger).setLevel(logging.CRITICAL)

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
        print("❌ ERRO: META_API_KEY ou META_API_ACCOUNT_ID ausentes.")
        return

    # Instância sem passar 'region' fixa e desativando subscrição de streaming
    api = MetaApi(API_KEY, {
        "requestTimeout": 30000,
        "connectWithTimeout": 30000,
        "subscriptions": {
            "disabled": True  # Bloqueia as conexões WebSocket de streaming que causam a exceção
        }
    })

    try:
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)

        if account.state != "DEPLOYED":
            print("⏳ A implantar conta na nuvem...")
            await account.deploy()

        print("⏳ A aguardar conexão com o broker...")
        await account.wait_connected()

        # Obtém a conexão RPC
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()

        bot_status["online"] = True
        bot_status["connected"] = True
        print("⚡ Conectado ao MetaTrader 5 via MetaApi (Modo RPC)!")

        from strategy import analisar_estrategia

        while True:
            try:
                await analisar_estrategia(connection, bot_status)
            except Exception as e:
                print(f"⚠️ Aviso no loop: {e}")

            await asyncio.sleep(5)

    except Exception as err:
        print(f"❌ Erro de conexão: {err}")
        bot_status["online"] = False
        bot_status["connected"] = False
