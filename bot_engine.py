import os
import asyncio
from datetime import datetime
from metaapi_cloud_sdk import MetaApi

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

    api =O erro nos logs indica um problema recorrente de conexão na MetaApi: **`TimeoutException: It seems like the account is not connected to broker yet or SDK settings you use does not match the account region.`**

O SDK não está conseguindo comunicar com a sua conta no broker dentro do tempo limite. Como resolver diretamente no seu código e na dashboard:

**1. Definir a região na inicialização do SDK**
A MetaApi precisa saber exatamente em qual região a sua conta está alocada (`vint Hill`, `london`, `singapore`, etc.). No seu script onde instancia o `MetaApi`, adicione o parâmetro de região explicitamente ou use a instância da conta:

```python
# Ao instanciar a MetaApi, você pode especificar a região (ou verificar na dashboard da MetaApi qual é a região da sua conta):
api = MetaApi(token, {'region': 'london'}) # Exemplo: 'london' ou a região configurada na sua conta
