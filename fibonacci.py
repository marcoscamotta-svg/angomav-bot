from rich.console import Console
from rich.table import Table
from rich.prompt import FloatPrompt

console = Console()

def calcular_fibonacci():
    console.print("\n[bold cyan]=== CALCULADORA DE NÍVEIS DE FIBONACCI ===[/bold cyan]\n")

    high = FloatPrompt.ask("Preço Máximo (High)")
    low = FloatPrompt.ask("Preço Mínimo (Low)")

    diff = high - low

    table = Table(title="Níveis de Fibonacci", header_style="bold magenta")
    table.add_column("Nível", style="cyan", justify="left")
    table.add_column("Preço (Tendência de Alta)", style="green", justify="right")
    table.add_column("Preço (Tendência de Baixa)", style="yellow", justify="right")

    retracoes = [0.236, 0.382, 0.500, 0.618, 0.786]
    expansoes = [1.272, 1.618, 2.000]

    for r in retracoes:
        alta = high - (diff * r)
        baixa = low + (diff * r)
        table.add_row(f"Retração {r*100:.1f}%", f"{alta:.4f}", f"{baixa:.4f}")

    for e in expansoes:
        alta = high + (diff * (e - 1))
        baixa = low - (diff * (e - 1))
        table.add_row(f"Expansão {e*100:.1f}%", f"{alta:.4f}", f"{baixa:.4f}")

    console.print(table)

if __name__ == "__main__":
    calcular_fibonacci()

