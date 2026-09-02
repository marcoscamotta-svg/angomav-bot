import requests
import socket
from rich.console import Console
from rich.panel import Panel

console = Console()

def checar_rede():
    console.print("\n[bold cyan][*] Verificando conexão e dados da rede...[/bold cyan]\n")

    # IP Local
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
    except Exception:
        ip_local = "Indisponível"

    # IP Público e Localização via API
    try:
        res = requests.get("https://ipapi.co/json/", timeout=5).json()
        ip_pub = res.get("ip", "Erro")
        cidade = res.get("city", "Desconhecido")
        pais = res.get("country_name", "Desconhecido")
        org = res.get("org", "Desconhecido")
    except Exception:
        ip_pub, cidade, pais, org = "Indisponível", "Erro", "Erro", "Erro"

    info = f"""[bold yellow]IP Local (Wi-Fi/Rede):[/bold yellow] [green]{ip_local}[/green]

