import os
import threading
import asyncio
from flask import Flask, jsonify
from bot_engine import run_trading_bot, bot_status

app = Flask(__name__)

# Rota de API do status
@app.route('/api/status', methods=['GET'])
def get_api_status():
    return jsonify({
        "connected": bot_status.get("online", False) or bot_status.get("connected", False),
        "equity": bot_status.get("equity", 0.0),
        "balance": bot_status.get("balance", 0.0),
        "last_update": bot_status.get("last_scan", "--:--:--"),
        "last_signals": bot_status.get("last_signals", [])
    })

# Rota principal para o HTML
@app.route('/')
def index():
    return """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ANGOMAV TRADING BOT</title>
    <style>
        body { background-color: #0b0e14; color: #e1e6ed; font-family: sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 15px; }
        .title { font-size: 18px; font-weight: bold; color: #38bdf8; }
        .badge { padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 12px; }
        .badge-online { background-color: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981; }
        .badge-offline { background-color: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef4444; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-top: 20px; }
        .card { background: #151c28; border-radius: 8px; padding: 15px; border: 1px solid #1e293b; }
        .card-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; margin-bottom: 5px; }
        .card-value { font-size: 20px; font-weight: bold; color: #f8fafc; }
        .signals-card { margin-top: 20px; background: #151c28; border-radius: 8px; padding: 15px; border: 1px solid #1e293b; }
        .signal-item { padding: 10px 0; border-bottom: 1px solid #1e293b; font-family: monospace; font-size: 13px; color: #38bdf8; }
        .empty { color: #64748b; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🚀 ANGOMAV TRADING BOT</div>
            <div id="status-badge" class="badge badge-offline">● CONECTANDO...</div>
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
                <div class="card-value" id="last-update" style="font-size: 16px;">--:--:--</div>
            </div>
        </div>

        <div class="signals-card">
            <div class="card-label">📊 Feed de Confluências (SMC / Wyckoff)</div>
            <div id="signals-list">
                <div class="empty">A carregar dados do mercado...</div>
            </div>
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
                    badge.innerText = '● ONLINE';
                } else {
                    badge.className = 'badge badge-offline';
                    badge.innerText = '● CONECTANDO...';
                }

                document.getElementById('equity').innerText = '$' + (data.equity || 0).toFixed(2);
                document.getElementById('balance').innerText = '$' + (data.balance || 0).toFixed(2);
                document.getElementById('last-update').innerText = data.last_update || '--:--:--';

                const listContainer = document.getElementById('signals-list');
                if (data.last_signals && data.last_signals.length > 0) {
                    listContainer.innerHTML = '';
                    data.last_signals.forEach(sig => {
                        const div = document.createElement('div');
                        div.className = 'signal-item';
                        if (typeof sig === 'string') {
                            div.innerText = sig;
                        } else {
                            div.innerText = `${sig.timeframe_h1} | ${sig.timeframe_m15} | ${sig.timeframe_m1}`;
                        }
                        listContainer.appendChild(div);
                    });
                }
            } catch (e) {
                console.error("Erro ao atualizar dashboard:", e);
            }
        }

        setInterval(updateDashboard, 3000);
        updateDashboard();
    </script>
</body>
</html>
    """

def start_bot_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_trading_bot())

# Inicialização automática da thread no carregamento do módulo pelo Gunicorn
t = threading.Thread(target=start_bot_thread, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
