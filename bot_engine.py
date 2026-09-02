import asyncio
import os
import math
from metaapi_cloud_sdk import MetaApi

# Configurações de Ambiente
TOKEN = os.environ.get("META_API_TOKEN")
ACCOUNT_ID = os.environ.get("META_API_ACCOUNT_ID")

# Parâmetros da Estratégia e Risco
RISK_PERCENTAGE = 0.005  # 0.5% de risco por trade
SYMBOLS = ["XAUUSD", "BTCUSD", "GBPUSD", "GBPCAD", "EURUSD", "NAS100", "GER40"]
TIMEFRAME = "5m"         # Timeframe base para OB e FVG


def calculate_lot_size(account_equity, sl_pips, pip_value=10):
    """
    Calcula o tamanho do lote para arriscar exatamente 0.5% da conta.
    """
    risk_amount = account_equity * RISK_PERCENTAGE
    if sl_pips <= 0:
        return 0.01
    
    lot = risk_amount / (sl_pips * pip_value)
    lot = round(max(0.01, lot), 2)
    return lot


def detect_fvg(candles):
    """
    Deteta Fair Value Gap (FVG) de Compra (Bullish) ou Venda (Bearish).
    """
    if len(candles) < 3:
        return None

    c1, c2, c3 = candles[-3], candles[-2], candles[-1]

    # Bullish FVG
    if c3['high'] > c1['low'] and c2['close'] > c1['high']:
        gap_size = c3['low'] - c1['high']
        if gap_size > 0:
            return {"type": "BULLISH_FVG", "top": c3['low'], "bottom": c1['high']}

    # Bearish FVG
    if c3['low'] < c1['high'] and c2['close'] < c1['low']:
        gap_size = c1['low'] - c3['high']
        if gap_size > 0:
            return {"type": "BEARISH_FVG", "top": c1['low'], "bottom": c3['high']}

    return None


def detect_order_block(candles):
    """
    Identifica o Order Block que originou a expansão de preço.
    """
    if len(candles) < 4:
        return None

    c1, c2, c3, c4 = candles[-4], candles[-3], candles[-2], candles[-1]

    # Order Block Bullish
    if c2['close'] < c2['open'] and c4['close'] > c3['high']:
        return {"type": "BULLISH_OB", "high": c2['high'], "low": c2['low']}

    # Order Block Bearish
    if c2['close'] > c2['open'] and c4['close'] < c3['low']:
        return {"type": "BEARISH_OB", "high": c2['high'], "low": c2['low']}

    return None


async def run_trading_bot():
    api = MetaApi(TOKEN)
    account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
    
    print("Verificando deploy da conta no MetaApi...")
    try:
        if account.state != 'DEPLOYED':
            print("Garantindo deploy da conta...")
            await account.deploy()
    except Exception as e:
        print(f"Aviso no status de deploy: {e}")

    print("Aguardando conexão ativa com o servidor MetaTrader...")
    await account.wait_connected()
    
    connection = account.get_rpc_connection()
    await connection.connect()
    await connection.wait_synchronized()
    
    print("Robô ativo e sincronizado! Monitorizando ativos...")

    while True:
        try:
            account_information = await connection.get_account_information()
            equity = account_information['equity']

            for symbol in SYMBOLS:
                candles = await connection.get_historical_candles(symbol, TIMEFRAME, limit=10)
                
                fvg = detect_fvg(candles)
                ob = detect_order_block(candles)

                if fvg and ob:
                    if fvg['type'] == "BULLISH_FVG" and ob['type'] == "BULLISH_OB":
                        sl_price = ob['low']
                        entry_price = candles[-1]['close']
                        sl_pips = abs(entry_price - sl_price) * 10000

                        lot = calculate_lot_size(equity, sl_pips)
                        tp_price = entry_price + (abs(entry_price - sl_price) * 2)

                        print(f"[{symbol}] Oportunidade de COMPRA detetada! Lote: {lot} | SL: {sl_price} | TP: {tp_price}")

                    elif fvg['type'] == "BEARISH_FVG" and ob['type'] == "BEARISH_OB":
                        sl_price = ob['high']
                        entry_price = candles[-1]['close']
                        sl_pips = abs(entry_price - sl_price) * 10000

                        lot = calculate_lot_size(equity, sl_pips)
                        tp_price = entry_price - (abs(entry_price - sl_price) * 2)

                        print(f"[{symbol}] Oportunidade de VENDA detetada! Lote: {lot} | SL: {sl_price} | TP: {tp_price}")

            await asyncio.sleep(60)

        except Exception as e:
            print(f"Erro durante o ciclo de análise: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_trading_bot())

