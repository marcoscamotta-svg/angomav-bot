import socket
import subprocess
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()

def obter_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
        return ip_local
    except Exception:
        return None

def explorar():
    console.print("\n[bold cyan][*] Identificando interface de rede...[/bold cyan]\n")
    meu_ip = obter_ip_local()
    
    if not meu_ip:
        console.print("[bold red][!] Não foi possível detectar o IP local. Verifique a conexão.[/bold red]")
        return
    
    ip_partes = meu_ip.split(".")
    base_ip = f"{ip_partes[0]}.{ip_partes[1]}.{ip_partes[2]}"
    gateway_provavel = f"{base_ip}.1"
    
    info = f"""[bold yellow]Seu IP Local:[/bold yellow] [bold green]{meu_ip}[/bold green]
[bold yellow]Gateway Sugerido:[/bold yellow] [bold cyan]{gateway_provavel}[/bold cyan]"""
    
    console.print(Panel(info, title="Interface Wi-Fi", border_style="green"))
    
    gateway = Prompt.ask("Confirme ou digite o IP do Gateway (Router)", default=gateway_provavel)
    
    console.print(f"\n[bold yellow][*] Mapeando dispositivos na rede {base_ip}.0/24...[/bold yellow]\n")
    
    table = Table(title="Dispositivos Encontrados na Rede", header_style="bold magenta")
    table.add_column("IP do Dispositivo", style="cyan", justify="left")
    table.add_column("Estado", style="green", justify="center")

    try:
        cmd = f"nmap -sn {base_ip}.0/24"
        resultado = subprocess.check_output(cmd, shell=True).decode("utf-8")
        
        ips_encontrados = re.findall(r"Nmap scan report for ([\d\.]+)", resultado)
        
        if ips_encontrados:
            for ip in ips_encontrados:
                status = "Router / Gateway" if ip == gateway else "Ativo (Host)"
                table.add_row(ip, status)
            console.print(table)
            
            # Opção para analisar um IP
            if Prompt.ask("\nDeseja verificar os serviços ativos de algum IP?", choices=["s", "n"], default="s") == "s":
                subprocess.run(["python", "analisar_servicos.py"])
        else:
            console.print("[bold red]Nenhum dispositivo respondeu ao ping sweep.[/bold red]")
            
    except Exception as e:
        console.print(f"[bold red]Erro na varredura: {e}[/bold red]")

if __name__ == "__main__":
    explorar()
