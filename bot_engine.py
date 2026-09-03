import os
import asyncio
from metaapi_cloud_sdk import MetaApi

API_KEY = os.getenv("META_API_KEY")
ACCOUNT_ID = os.getenv("META_API_ACCOUNT_ID")

# Variável de estado esperada pelo main.py
bot_status = {
    "online": False,
    "last_signals": []
}

async def run_trading_bot(bot_status_param=None):
    global bot_status
    target_status = bot_status_param if bot_status_param is not None else bot_status

    if not API_KEY or not ACCOUNT_ID:
        print("❌ ERRO: META_API_KEY ou META_API_ACCOUNT_ID ausentes!")
        return

    api = MetaApi(API_KEY)

    try:
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        
        if account.state != 'DEPLOYED':
            await account.deploy()

        await account.wait_connected()
        
        connection = account.get_rpc_connection()
        await connection.connect()

        target_status["online"] = True
        print("⚡ Conectado com sucesso ao servidor da MetaApi!")

        from strategy import analisar_estrategia

        while True:
            try:
                await analisar_estrategia(connection, target_status)
            except Exception as err:
                if "TimeoutException" not in str(err):
                    print(f"⚠️ AVISO: {err}")
            
            await asyncio.sleep(10)

    except Exception as e:
        print(f"❌ Erro na conexão MetaApi: {e}")
        target_status["online"] = False

async def executar_ordem(connection, symbol, action, volume, sl=None, tp=None):
    try:
        if action == "BUY":
            result = await connection.create_market_buy_order(symbol, volume, sl, tp)
        else:
            result = await connection.create_market_sell_order(symbol, volume, sl, tp)
        print(f"✅ Ordem {action} executada com sucesso! Result: {result}")
        return result
    except Exception as e:
        print(f"❌ Erro ao executar ordem {action}: {e}")
        return None
