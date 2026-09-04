import os
import asyncio
import logging
from metaapi_cloud_sdk import MetaApi

# Silencia logs de conexão para não poluir o terminal do Railway
logging.basicConfig(level=logging.ERROR)

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
        print("❌ ERRO: META_API_KEY ou META_API_ACCOUNT_ID não configurados nas variáveis de ambiente.")
        return

    # Inicializa o SDK oficial da MetaApi especificando a região 'london' e timeouts maiores
    api = MetaApi(API_KEY, {
        "region": "london",
        "requestTimeout": 30000,
        "connectWithTimeout": 30000
    })

    try:
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)

        if account.state != "DEPLOYED":
            print("⏳ A implantar conta na nuvem da MetaApi...")
            await account.deploy()

        print("⏳ A aguardar sincronização com o broker MetaTrader...")
        await account.wait_connected()

        # Obtém a conexão RPC para enviar ordens e ler preços
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()

        bot_status["online"] = True
        bot_status["connected"] = True
        print("⚡ Conectado com sucesso ao MetaTrader 5 via MetaApi SDK!")

        from strategy import analisar_estrategia

        while True:
            try:
                await analisar_estrategia(connection, bot_status)
            except Exception as e:
                print(f"⚠️ Erro no loop de varredura: {e}")

            await asyncio.sleep(5)

    except Exception as err:
        print(f"❌ Erro crítico de conexão: {err}")
        bot_status["online"] = False
        bot_status["connected"] = False
