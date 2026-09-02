import ssl
import socket
import urllib.request
from rich.console import Console
from rich.table import Table

console = Console()

def auditar_site(dominio):
    console.print(f"\n[bold cyan][*] A auditar segurança do domínio: {dominio}[/bold cyan]\n")
    
    try:
        contexto = ssl.create_default_context()
        with socket.create_connection((dominio, 443)) as sock:
            with contexto.wrap_socket(sock, server_hostname=dominio) as ssock:
                cert = ssock.getpeercert()
                versao_tls = ssock.version()
                
                emissor = dict(x[0] for x in cert['issuer'])
                
                tabela_ssl = Table(title="Informações do Certificado SSL/TLS", border_style="blue")
                tabela_ssl.add_column("Métrica", style="yellow")
                tabela_ssl.add_column("Valor", style="green")
                
                tabela_ssl.add_row("Versão do Protocolo", versao_tls)
                tabela_ssl.add_row("Emissor (CA)", emissor.get('organizationName', 'N/A'))
                tabela_ssl.add_row("Validade Final", cert.get('notAfter', 'N/A'))
                
                console.print(tabela_ssl)
    except Exception as e:
        console.print(f"[bold red][!] Erro SSL: {e}[/bold red]")

    try:
        url = f"https://{dominio}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resposta:
            headers = resposta.info()
            
            tabela_sec = Table(title="Cabeçalhos de Segurança", border_style="magenta")
            tabela_sec.add_column("Cabeçalho", style="cyan")
            tabela_sec.add_column("Estado", style="white")
            
            hsts = headers.get("Strict-Transport-Security")
            csp = headers.get("Content-Security-Policy")
            x_frame = headers.get("X-Frame-Options")
            
            tabela_sec.add_row("HSTS", f"[green]{hsts}[/green]" if hsts else "[red]Ausente[/red]")
            tabela_sec.add_row("CSP", "[green]Configurado[/green]" if csp else "[red]Ausente[/red]")
            tabela_sec.add_row("X-Frame-Options", f"[green]{x_frame}[/green]" if x_frame else "[red]Ausente[/red]")
            
            console.print(tabela_sec)
    except Exception as e:
        console.print(f"[bold red][!] Erro nos Cabeçalhos: {e}[/bold red]")

if __name__ == "__main__":
    dom = input("Digite o domínio para auditar (ex: github.com): ").strip()
    if dom:
        auditar_site(dom)
