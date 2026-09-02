import os
import asyncio
import threading
from flask import Flask, jsonify, render_template
from metaapi_cloud_sdk import MetaApi
from bot_engine import run_trading_bot

app = Flask(__name__)

# Configurações do MetaApi
TOKEN = os.environ.get("META_API_TOKEN")
ACCOUNT_ID = os.environ.get("META_API_ACCOUNT_ID")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/account')
def get_account():
    if not TOKEN or not ACCOUNT_ID:
        return jsonify({"error": "Variaveis de ambiente nao configuradas"}), 400

    async def fetch_metaapi_data():
        api = MetaApi(TOKEN)
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        await account.read_gtd_mode()
        
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        
        account_information = await connection.get_account_information()
        return account_information

    try:
        data = asyncio.run(fetch_metaapi_data())
        return jsonify({
            "nome": data.get("name"),
            "servidor": data.get("server"),
            "estado": data.get("state"),
            "tipo": data.get("type")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Função para arrancar o robô em segundo plano
def start_bot_thread():
    if TOKEN and ACCOUNT_ID:
        print("Iniciando a engine do robô de trading em segundo plano...")
        asyncio.run(run_trading_bot())

# Inicia a thread do robô
threading.Thread(target=start_bot_thread, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
