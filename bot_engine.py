import os
import asyncio
import aiohttp
from datetime import datetime

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

class MetaApiREST:
    def __init__(self, token, account_id):
        self.token = token
        self.account_id = account_id
        # Endpoint de cliente direto da MetaApi (Região London)
        self.base_url = f"https://mt-client-api-v1.london.agillictrade.ai/users/current/accounts/{account_id}"
        self.headers = {
            "auth-token": token,
            "content-type": "application/json"
        }

    async def get_account_information(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/account-information", headers=self.headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            print(f"⚠️ Erro ao obter info da conta: {e}")
        return None

    async def get_symbol_price(self, symbol):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/symbols/{symbol}/current-price", headers=self.headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            print(f"⚠️ Erro ao obter preço do símbolo: {e}")
        return None

    async def get_positions(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/positions", headers=self.headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            print(f"⚠️ Erro ao obter posições: {e}")
        return []

    async def create_market_buy_order(self, symbol, volume, stop_loss, take_profit):
        payload = {
            "actionType": "ORDER_TYPE_BUY",
            "symbol": symbol,
            "volume": volume,
            "stopLoss": stop_loss,
            "takeProfit": take_profit
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/trade", json=payload, headers=self.headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return await resp.json()
        except Exception as e:
            print(f"⚠️ Erro na ordem de compra: {e}")
            return None

    async def create_market_sell_order(self, symbol, volume, stop_loss, take_profit):
        payload = {
            "actionType": "ORDER_TYPE_SELL",
            "symbol": symbol,
            "volume": volume,
            "stopLoss": stop_loss,
            "takeProfit": take_profit
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/trade", json=payload, headers=self.headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return await resp.json()
        except Exception as e:
            print(f"⚠️ Erro na ordem de venda: {e}")
            return None

async def run_trading_bot():
    global bot_status
    if not API_KEY or not ACCOUNT_ID:
        print("❌ ERRO: META_API_KEY ou META_API_ACCOUNT_ID não configurados.")
        return

    connection = MetaApiREST(API_KEY, ACCOUNT_ID)
    bot_status["online"] = True
    bot_status["connected"] = True
    print("⚡ Engine iniciada via REST HTTP (Livre de bloqueios/WebSockets)!")

    from strategy import analisar_estrategia

    while True:
        try:
            await analisar_estrategia(connection, bot_status)
        except Exception as e:
            print(f"⚠️ Erro na varredura da estratégia: {e}")
        
        await asyncio.sleep(5)
