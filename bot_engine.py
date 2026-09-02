import asyncio
import os
import math
from datetime import datetime, timedelta
from metaapi_cloud_sdk import MetaApi

# Configurações de Ambiente
TOKEN = os.environ.get("META_API_TOKEN")
ACCOUNT_ID = os.environ.get("META_API_ACCOUNT_ID")

# Parâmetros de Estratégia e Risco
RISK_PERCENTAGE = 0.005  # 0.5% de risco por trade
SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "XAUUSD", "BTCUSD"]
TIMEFRAME = "1h"  # Timeframe base para OB e FVG

# Dicionário global para exportar dados para o Dashboard Web (sem interferir no bot)
bot_status = {
    "connected": False,
    "last_update": "A iniciar...",
    "symbols": SYMBOLS,
    "equity": 0,
    "balance": 0,
    "last_signals": []
}


def calculate_lot_size(account_equity, sl_pips, pip_value=10):
    """Calcula o tamanho do lote para arriscar exatamente 0.5% da conta."""
    risk_amount = account_equity * RISK_PERCENTAGE
    if sl_pips <= 0:
        return 0.01

    lot = risk_amount / (sl_pips * pip_value)
    lot = round(max(0.01, lot), 2)
    return lot


def detect_fvg(candles):
    """Detecta Fair Value Gap (FVG) de Compra (Bullish) ou Venda (Bearish)."""
    if len(candles) < 3:
        return None

    c1, c2, c3 = candles[-3], candles[-2], candles[-1]

    # Bullish FVG
    if c1['high'] < c3['low'] and c2['low'] > c1['high']:
        gap_size = c3['low'] - c1['high']
        return {"type": "BULLISH_FVG", "top": c3['low'], "bottom": c1['high'], "gap": gap_size}

    # Bearish FVG
    if c1['low'] > c3['high'] and c2['high'] < c1['low']:
        gap_size = c1['low'] - c3['high']
        return {"type": "BEARISH_FVG", "top": c1['low'], "bottom": c3['high'], "gap": gap_size}

    return None


def detect_order_block(candles):
    """Identifica o Order Block que originou a expansão de preço."""
    if len(candles) < 4:
        return None

    c1, c2, c3, c4 = candles[-4], candles[-3], candles[-2], candles[-1]

    # Order Block Bullish
    if c2['close'] < c2['open'] and c4['close'] > c2['high']:
        return {"type": "BULLISH_OB", "high": c2['high'], "low": c2['low']}

    # Order Block Bearish
    if c2['close'] > c2['open'] and c4['close'] < c2['low']:
        return {"type": "BEARISH_OB", "high": c2['high'], "low": c2['low']}

    return None


async def run_trading_bot():
    if not TOKEN or not ACCOUNT_ID:
        print("Erro: META_API_TOKEN ou META_API_ACCOUNT_ID não foram configurados nas variáveis de ambiente.")
        return

    api = MetaApi(TOKEN)

    try:
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)

        print("Verificando deploy da conta no MetaApi...")
        if account.state != 'DEPLOYED':
            print("Garantindo deploy da conta...")
            await account.deploy()

        print("Aguardando conexão ativa com o servidor MetaTrader...")
        await account.wait_connected()

        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()

        print("Robô ativo e sincronizado! Monitorizando ativos...")
        bot_status["connected"] = True

        while True:
            try:
                account_information = await connection.get_account_information()
                bot_status["equity"] = account_information.get('equity', 0)
                bot_status["balance"] = account_information.get('balance', 0)
            except Exception as e:
                print(f"Erro ao obter informações da conta: {e}")

            bot_status["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for symbol in SYMBOLS:
                try:
                    start_time = datetime.utcnow() - timedelta(days=5)
                    candles = await account.get_historical_candles(symbol, TIMEFRAME, start_time, 100)

                    if not candles or len(candles) < 5:
                        continue

                    fvg = detect_fvg(candles)
                    ob = detect_order_block(candles)

                    if fvg and ob:
                        signal_info = None
                        if fvg['type'] == "BULLISH_FVG" and ob['type'] == "BULLISH_OB":
                            print(f"[{datetime.now()}] CONFLUÊNCIA DE COMPRA ENCONTRADA em {symbol}!")
                            signal_info = f"BUY {symbol} - OB + FVG Confluência"

                        elif fvg['type'] == "BEARISH_FVG" and ob['type'] == "BEARISH_OB":
                            print(f"[{datetime.now()}] CONFLUÊNCIA DE VENDA ENCONTRADA em {symbol}!")
                            signal_info = f"SELL {symbol} - OB + FVG Confluência"

                        if signal_info and signal_info not in bot_status["last_signals"]:
                            bot_status["last_signals"].insert(0, f"[{datetime.now().strftime('%H:%M')}] {signal_info}")
                            bot_status["last_signals"] = bot_status["last_signals"][:10]  # Guarda os últimos 10

                except Exception as e:
                    print(f"Erro ao analisar o símbolo {symbol}: {e}")

            await asyncio.sleep(60)

    except Exception as e:
        print(f"Erro na execução do robô: {e}")
        bot_status["connected"] = False


if __name__ == "__main__":
    asyncio.run(run_trading_bot())

