import os
import threading
import asyncio
from flask import Flask, jsonify
from metaapi_cloud_sdk import MetaApi
from bot_engine import run_trading_bot, bot_status

app = Flask(__name__)

# Configurações do MetaApi via Variáveis de Ambiente
TOKEN = os.environ.get("META_API_TOKEN")
ACCOUNT_ID = os.environ.get("META_API_ACCOUNT_ID")

api = MetaApi(TOKEN) if TOKEN else None

# ==========================================
# MÓDULO DE EXECUÇÃO AUTOMÁTICA DE TRADING
# ==========================================

async def executar_ordem_mercado(symbol: str, action: str, volume: float, stop_loss: float = None, take_profit: float = None):
    """
    Executa ordens de COMPRA (BUY) ou VENDA (SELL) a mercado no MT5 via MetaApi.
    """
    if not api or not ACCOUNT_ID:
        print("❌ MetaApi Token ou Account ID não configurados.")
        return None

    try:
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronization()

        print(f"🚀 Enviando ordem de {action}: {symbol} | Lote: {volume}")

        if action.upper() == "BUY":
            result = await connection.create_market_buy_order(
                symbol=symbol,
                volume=volume,
                stop_loss=stop_loss,
                take_profit=take_profit,
                options={'comment': 'Angomav Bot SMC Auto'}
            )
        elif action.upper() == "SELL":
            result = await connection.create_market_sell_order(
                symbol=symbol,
                volume=volume,
                stop_loss=stop_loss,
                take_profit=take_profit,
                options={'comment': 'Angomav Bot SMC Auto'}
            )
        else:
            print(f"❌ Ação inválida: {action}")
            return None

        print(f"✅ Ordem executada com sucesso! Ticket: {result.get('orderId')}")
        return result

    except Exception as e:
        print(f"❌ Erro ao executar ordem de {action}: {e}")
        return None

async def fechar_todas_posicoes(symbol: str = None):
    """
    Fecha posições abertas no MT5. Se 'symbol' for fornecido, fecha apenas desse par.
    """
    if not api or not ACCOUNT_ID:
        return

    try:
        account = await api.metatrader_account_api.get_account(ACCOUNT_ID)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronization()

        positions = await connection.get_positions()
        
        for pos in positions:
            if symbol is None or pos['symbol'] == symbol:
                print(f"🛑 Fechando posição #{pos['id']} ({pos['symbol']})...")
                await connection.close_position(pos['id'])
                print(f"✅ Posição #{pos['id']} fechada com sucesso.")

    except Exception as e:
        print(f"❌ Erro ao fechar posições: {e}")

# ==========================================
# INTERFACE WEB / DASHBOARD (FLASK)
# ==========================================

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Angomav Bot - SMC Terminal</title>
        <style>
            body { background-color: #0b0e14; color: #e1e6ed; font-family: sans-serif; margin: 0; padding: 20px; }
            .container { max-width: 900px; margin: 0 auto; }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #2a323d; padding-bottom: 15px; margin-bottom: 20px; }
            .title { font-size: 20px; font-weight: bold; color: #58a6ff; }
            .badge { padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: bold; }
            .badge-online { background-color: rgba(0, 255, 136, 0.15); color: #00ff88; border: 1px solid #00ff88; }
            .badge-offline { background-color: rgba(255, 68, 68, 0.15); color: #ff4444; border: 1px solid #ff4444; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .card { background: #151a21; border-radius: 8px; padding: 15px; border: 1px solid #2a323d; }
            .card-label { font-size: 12px; color: #8b949e; text-transform: uppercase; margin-bottom: 5px; }
            .card-value { font-size: 20px; font-weight: bold; color: #f0f6fc; }
            .signals-card { background: #151a21; border-radius: 8px; padding: 20px; border: 1px solid #2a323d; }
            ul { list-style: none; padding: 0; margin: 0; }
            li { padding: 10px 0; border-bottom: 1px solid #2a323d; color: #00ff88; font-family: monospace; }
            .empty { color: #8b949e; font-style: italic; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="title">🚀 ANGOMAV TRADING BOT</div>
                <div id="status-badge" class="badge badge-offline">● CONECTANDO</div>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="card-label">Capital Líquido (Equity)</div>
                    <div class="card-value" id="equity">$0.00</div>
                </div>
                <div class="card">
                    <div class="card-label">Saldo (Balance)</div>
                    <div class="card-value" id="balance">$0.00</div>
                </div>
                <div class="card">
                    <div class="card-label">Última Varredura</div>
                    <div class="card-value" id="last-update" style="font-size: 14px;">--:--:--</div>
                </div>
            </div>

            <div class="signals-card">
                <h3>📊 Feed de Confluências (SMC / Wyckoff)</h3>
                <ul id="signals-list">
                    <li class="empty">A carregar dados do mercado...</li>
                </ul>
            </div>
        </div>

        <script>
            async function updateDashboard() {
                try {
                    const res = await fetch('/api/status');
                    const data = await res.json();

                    const badge = document.getElementById('status-badge');
                    if (data.connected) {
                        badge.className = 'badge badge-online';
                        badge.innerText = '● ONLINE (MT5)';
                    } else {
                        badge.className = 'badge badge-offline';
                        badge.innerText = '● CONECTANDO...';
                    }

                    document.getElementById('equity').innerText = '$' + Number(data.equity).toFixed(2);
                    document.getElementById('balance').innerText = '$' + Number(data.balance).toFixed(2);
                    document.getElementById('last-update').innerText = data.last_update.split(' ')[1] || data.last_update;

                    const list = document.getElementById('signals-list');
                    if (data.last_signals && data.last_signals.length > 0) {
                        list.innerHTML = data.last_signals.map(s => `<li>${s}</li>`).join('');
                    } else {
                        list.innerHTML = '<li class="empty">A varrer ativos (EURUSD, XAUUSD...)... Sem confluências no momento.</li>';
                    }
                } catch (e) {
                    console.error("Erro ao atualizar o dashboard:", e);
                }
            }

            setInterval(updateDashboard, 3000);
            updateDashboard();
        </script>
    </body>
    </html>
    """

@app.route('/api/status')
def get_status():
    return jsonify(bot_status)

def run_bot_in_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_trading_bot())

# Inicia o robô em segundo plano no arranque
t = threading.Thread(target=run_bot_in_thread, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
