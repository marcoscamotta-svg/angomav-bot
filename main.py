import os
from flask import Flask, render_template, jsonify
import asyncio
from metaapi_cloud_sdk import MetaApi

app = Flask(__name__, template_folder='.')

TOKEN = os.environ.get('META_API_TOKEN')
ACCOUNT_ID = os.environ.get('META_API_ACCOUNT_ID')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/account')
def get_account_info():
    if not TOKEN or not ACCOUNT_ID:
        return jsonify({"error": "Variaveis de ambiente nao configuradas"}), 400
    
    async def fetch_data():
        api = MetaApi(TOKEN)
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        initial_state = account.state
        return {
            "name": account.name,
            "type": account.type,
            "state": initial_state,
            "server": account.server
        }

    try:
        data = asyncio.run(fetch_data())
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
