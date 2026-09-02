import os
import zipfile
from datetime import datetime
from rich.console import Console

console = Console()

def criar_backup():
    console.print("\n[bold cyan][*] Iniciando backup dos scripts...[/bold cyan]")

    data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_zip = f"Backup_Scripts_{data_str}.zip"
    pasta_destino = os.path.expanduser("~/storage/downloads")
    caminho_zip = os.path.join(pasta_destino, nome_zip)

    home_dir = os.path.expanduser("~")

    try:
        with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for raiz, _, arquivos in os.walk(home_dir):
                # Ignora a pasta storage para não duplicar downloads no zip
                if "storage" in raiz:
                    continue
                for arq in arquivos:
                    if arq.endswith(".py") or arq.endswith(".sh"):
                        caminho_completo = os.path.join(raiz, arq)
                        nome_relativo = os.path.relpath(caminho_completo, home_dir)
                        zipf.write(caminho_completo, nome_relativo)

        console.print(f"[bold green][+] Backup criado com sucesso em:[/bold green]\n{caminho_zip}")
    except Exception as e:
        console.print(f"[bold red][!] Erro ao gerar backup: {e}[/bold red]")

if __name__ == "__main__":
    criar_backup()

