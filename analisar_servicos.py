import subprocess
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()

def testar_latencia(ip):
    console.print(f"\n[bold cyan][*] Testando latência para {ip}...[/bold cyan]\n")
    try:
        cmd = f"ping -c 5 {ip}"
        resultado = subprocess.check_output(cmd, shell=True).decode("utf-8")
        tempos = re.findall(r"time=([\d\.]+)\s*ms", resultado)
        
        if tempos:
            tempos_float = [float(t) for t in tempos]
            avg_t = sum(tempos_float) / len(tempos_float)
            info = f"""[bold yellow]Pacotes Enviados:[/bold yellow] 5 | [bold green]Recebidos:[/bold green] {len(tempos_float)}
[bold yellow]Latência Média:[/bold yellow] {avg_t:.1f} ms"""
            console.print(Panel(info, title=f"Teste de Ping - {ip}", border_style="green"))
        else:
            console.print("[bold red][!] O dispositivo não respondeu ao ping.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Erro ao testar latência: {e}[/bold red]")

def checar_portas_nmap(ip):
    console.print(f"\n[bold yellow][*] A escanear portas ativas em {ip}...[/bold yellow]\n")
    table = Table(title=f"Serviços / Portas Abertas em {ip}", header_style="bold magenta")
    table.add_column("Porta / Protocolo", style="cyan", justify="center")
    table.add_column("Estado", style="green", justify="center")
    table.add_column("Serviço", style="yellow")

    try:
        cmd = f"nmap --top-ports 100 --open {ip}"
        resultado = subprocess.check_output(cmd, shell=True).decode("utf-8")
        linhas_portas = re.findall(r"(\d+/\w+)\s+(open)\s+(\S+)", resultado)
        
        if linhas_portas:
            for porta, estado, servico in linhas_portas:
                table.add_row(porta, estado.upper(), servico)
            console.print(table)
        else:
            console.print(f"[bold red][!] Nenhuma porta aberta encontrada nas 100 portas principais de {ip}.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Erro durante a análise: {e}[/bold red]")

def menu_dispositivo():
    console.print("\n[bold cyan]=== ANALISADOR DE DISPOSITIVO ESPECÍFICO ===[/bold cyan]\n")
    ip = Prompt.ask("Digite o IP do dispositivo (ex: 192.168.8.1 ou 192.168.8.46)", default="192.168.8.1")
    
    while True:
        console.print(f"\n[bold yellow]IP Selecionado:[/bold yellow] [bold green]{ip}[/bold green]")
        console.print("[1] Testar Latência (Ping)")
        console.print("[2] Escanear Portas (Nmap)")
        console.print("[3] Escolher outro IP")
        console.print("[4] Voltar ao Menu Principal\n")
        
        op = input("Escolha uma opção (1-4): ").strip()
        
        if op == "1":
            testar_latencia(ip)
        elif op == "2":
            checar_portas_nmap(ip)
        elif op == "3":
            ip = input("Digite o novo IP: ").strip()
        elif op == "4":
            break
        else:
            console.print("[bold red]Opção inválida! Digite um número de 1 a 4.[/bold red]")

if __name__ == "__main__":
    menu_dispositivo()
