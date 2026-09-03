import os
import asyncio
from datetime import datetime
from metaapi_cloud_sdk import MetaApi

TOKEN = os.environ.get("META_API_TOKEN")
ACCOUNT_ID = os.environ.get("META_API_ACCOUNT_ID")

bot_status = {
    "connected": False,
    "equity": 0.0,
    "balance": 0.0,
    "last_update": "--",
    "last_signals": []
}

api = MetaApi(TOKEN) if TOKEN else None

# ==========================================
# FUNÇÕES DE EXECUÇÃO DE TRADES (MT5)
# ==========================================

async def abrir_posicao(connection, symbol: str, action: str, volume: float, sl: float = None, tp: float = None):
    """
    Executa ordens de COMPRA (BUY) ou VENDA (SELL) no MT5 via MetaApi.
    """
    try:
        print(f"🚀 [ORDEM] Enviando ordem de {action} para {symbol} | Lote: {volume}")
        if action.upper() == "BUY":
            res = await connection.create_market_buy_order(
                symbol=symbol,
                volume=volume,
                stop_loss=sl,
                take_profit=tp,
                options={'comment': 'Angomav SMC Bot'}
            )
        elif action.upper() == "SELL":
            res = await connection.create_market_sell_order(
                symbol=symbol,
                volume=volume,
                stop_loss=sl,
                take_profit=tp,
                options={'comment': 'Angomav SMC Bot'}
            )
        print(f"✅ [ORDEM] Executada com sucesso! Ticket ID: {res.get('orderId')}")
        return res
    except Exception as e:
        print(f"❌ [ERRO TRADING] Falha ao executar {action}: {e}")
        return None

async def fechar_todas_posicoes(connection, symbol: str = None):
    """
    Fecha todas as posições abertas ou apenas do símbolo especificado.
    """
    try:
        positions = await connection.get_positions()
        for pos in positions:
            if symbol is None or pos['symbol'] == symbol:
                print(f"🛑 [FECHO] Fechando posição #{pos['id']} ({pos['symbol']})...")
                await connection.close_position(pos['id'])
                print(f"✅ [FECHO] Posição #{pos['id']} encerrada.")
    except Exception as e:
        print(f"❌ [ERRO TRADING] Falha ao fechar posições: {e}")

# ==========================================
# MOTOR DE VARREDURA E ANÁLISE (SMC/WYCKOFF)
# ==========================================

async def run_trading_bot():
    if not api or not ACCOUNT_ID:
        print("❌ Variáveis META_API_TOKEN ou META_API_ACCOUNT_ID não foram encontradas.")
        return

    while True:
        try:
            account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
            connection = account.get_rpc_connection()
            await connection.connect()
            await connection.wait_synchronization()

            bot_status["connected"] = True
            print("⚡ Conectado com sucesso ao servidor da MetaApi!")

            while True:
                # 1. Atualizar Métricas da Conta
                account_information = await connection.get_account_information()
                bot_status["equity"] = account_information.get("equity", 0.0)
                bot_status["balance"] = account_information.get("balance", 0.0)
                bot_status["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 2. Varredura e Execução
                # Nota: Integra aqui a tua lógica de sinal/indicador.
                # Exemplo de chamada de ordem (descomentar quando a condição do teu sinal for atingida):
                # await abrir_posicao(connection, symbol="EURUSD", action="BUY", volume=0.01, sl=1.0800, tp=1.0900)
                # await fechar_todas_posicoes(connection, symbol="EURUSD")

                await asyncio.sleep(10)

        except Exception as e:
            bot_status["connected"] = False
            print(f"⚠️ Erro no loop do bot: {e}. Reconectando em 15s...")
            await asyncio.sleep(15)
