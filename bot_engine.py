import os
import asyncio
from datetime import datetime
from metaapi_cloud_sdk import MetaApi

# Puxa credenciais das Variáveis de Ambiente do Railway
API_KEY = os.getenv("META_API_KEY", "")
ACCOUNT_ID = os.getenv("META_API_ACCOUNT_ID", "")

# Dicionário de estado global consultado pelo servidor web (main.py)
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
        print("❌ ERRO: META_API_KEY ou META_API_ACCOUNT_ID ausentes nas variáveis de ambiente!")
        return

    # Instancia a SDK definindo a região 'london' e aumentando o timeout para evitar desconexões
    api = MetaApi(API_KEY, {
        'region': 'london',
        'requestTimeout': 30000
    })

    try:
        # Acede à conta no MetaApi
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        
        # Garante que a conta está implantada (DEPLOYED)
        if account.state != 'DEPLOYED':
            print("⏳ A aguardar deployment da conta no MetaApi...")
            await account.deploy()
            await account.wait_connected()

        # Estabelece conexão RPC com a conta do MetaTrader 5
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        
        bot_status["online"] = True
        bot_status["connected"] = True
        print("⚡ Conectado com sucesso ao servidor do MetaApi (London Region)!")

        # Importa o módulo da estratégia
        from strategy import analisar_estrategia

        # Loop principal de análise e execução contínua
        while True:
            try:
                await analisar_estrategia(connection, bot_status)
            except Exception as err:
                print(f"⚠️ Erro ao executar ciclo da estratégia: {err}")
            
            # Intervalo entre varreduras (5 segundos)
            await asyncio.sleep(5)

    except Exception as e:
        print(f"❌ Erro na conexão com o MetaApi: {e}")
        bot_status["online"] = False
        bot_status["connected"] = False
