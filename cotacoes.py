import requests
from rich.console import Console
from rich.table import Table

console = Console()

def buscar_cotacoes():
    console.print("\n[bold cyan][*] Buscando cotações de mercado...[/bold cyan]\n")

    table = Table(title="Cotações em Tempo Real", header_style="bold magenta")
    table.add_column("Ativo", style="cyan", justify="left")
    table.add_column("Preço (USD / BRL)", style="green", justify="right")
    table.add_column("Variação (24h)", style="yellow", justify="right")

    headers = {"User-Agent": "Mozilla/5.0"}

    # 1. Binance API (Cripto)
    try:
        res_btc = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", headers=headers, timeout=5).json()
        btc_price = float(res_btc["lastPrice"])
        btc_var = float(res_btc["priceChangePercent"])
        table.add_row("Bitcoin (BTC/USDT)", f"${btc_price:,.2f}", f"{btc_var:+.2f}%")
    except Exception:
        table.add_row("Bitcoin (BTC)", "Erro na conexão", "-")

    # 2. AwesomeAPI (Câmbio)
    try:
        res_cambio = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL", headers=headers, timeout=5).json()
        usd_brl = float(res_cambio["USDBRL"]["bid"])
        usd_var = float(res_cambio["USDBRL"]["pctChange"])
        table.add_row("Dólar (USD/BRL)", f"R$ {usd_brl:.2f}", f"{usd_var:+.2f}%")

        eur_brl = float(res_cambio["EURBRL"]["bid"])
        eur_var = float(res_cambio["EURBRL"]["pctChange"])
        table.add_row("Euro (EUR/BRL)", f"R$ {eur_brl:.2f}", f"{eur_var:+.2f}%")
    except Exception:
        table.add_row("Câmbio API", "Erro na conexão", "-")

    console.print(table)

if __name__ == "__main__":
    buscar_cotacoes()

