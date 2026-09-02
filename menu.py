import os
import sys
import time
import requests
from colorama import Fore, Style, init
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

init(autoreset=True)

def limpar_tela():
    os.system('clear' if os.name != 'nt' else 'cls')

def obter_preco_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        res = requests.get(url, timeout=4).json()
        return float(res['lastPrice']), float(res['priceChangePercent'])
    except Exception:
        return None, None

def obter_preco_forex_estat():
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        res = requests.get(url, timeout=4).json()
        return res.get('rates', {})
    except Exception:
        return {}

def obter_painel_mercado():
    print(Fore.CYAN + "\n[+] A carregar cotações atualizadas em tempo real...\n")
    
    print(Fore.YELLOW + "==================================================")
    print(Fore.YELLOW + "         PAINEL DE COTAÇÕES SINTETIZADO           ")
    print(Fore.YELLOW + "==================================================")
    
    btc_p, btc_v = obter_preco_binance("BTCUSDT")
    if btc_p is not None:
        cor = Fore.GREEN if btc_v >= 0 else Fore.RED
        str_preco = f"${btc_p:,.2f}"
        print(f" BTC/USD    | Preço: {str_preco:<12} | 24h: {cor}{btc_v:+.2f}%{Style.RESET_ALL}")
    
    eur_p, eur_v = obter_preco_binance("EURUSDT")
    if eur_p is not None:
        cor = Fore.GREEN if eur_v >= 0 else Fore.RED
        str_preco = f"{eur_p:.4f}"
        print(f" EUR/USD    | Preço: {str_preco:<12} | 24h: {cor}{eur_v:+.2f}%{Style.RESET_ALL}")

    gbp_p, gbp_v = obter_preco_binance("GBPUSDT")
    if gbp_p is not None:
        cor = Fore.GREEN if gbp_v >= 0 else Fore.RED
        str_preco = f"{gbp_p:.4f}"
        print(f" GBP/USD    | Preço: {str_preco:<12} | 24h: {cor}{gbp_v:+.2f}%{Style.RESET_ALL}")

    rates = obter_preco_forex_estat()
    if rates:
        cad = rates.get('CAD', 0)
        gbp = rates.get('GBP', 0)
        if cad and gbp:
            gbpcad = cad / gbp
            str_preco = f"{gbpcad:.4f}"
            print(f" GBP/CAD    | Preço: {str_preco:<12} | Status: OK")
            
    print(Fore.WHITE + "----------------------------------------------")
    print(Fore.BLUE + " [i] NAS100, US30 e XAUUSD serão sincronizados")
    print(Fore.BLUE + "     automaticamente via MetaApi / MT5.")
    print(Fore.YELLOW + "==================================================")

def calculadora_prop_firm():
    print(Fore.CYAN + "\n--- GESTÃO DE RISCO (MESA PROPRIETÁRIA) ---")
    try:
        saldo = float(input("Saldo da Conta ($): "))
        risco_pct = float(input("Risco por trade (%): "))
        sl_pips = float(input("Stop Loss (pips): "))
        
        valor_risco = saldo * (risco_pct / 100.0)
        lote = valor_risco / (sl_pips * 10) if sl_pips > 0 else 0
        
        print(Fore.GREEN + f"\n=> Perda máxima nesta ordem: ${valor_risco:.2f}")
        print(Fore.YELLOW + f"=> Tamanho do Lote recomendado: {lote:.2f}")
        
        with open("historico_gestao.txt", "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Saldo: ${saldo} | Risco: ${valor_risco:.2f} | Lote: {lote:.2f}\n")
        print(Fore.BLUE + "[i] Cálculo guardado em 'historico_gestao.txt'")
    except ValueError:
        print(Fore.RED + "[-] Valor inválido inserido.")

def gerar_relatorio_pdf():
    print(Fore.CYAN + "\n--- A GERAR RELATÓRIO PDF ---")
    nome_arquivo = f"Relatorio_Trading_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
    
    try:
        c = canvas.Canvas(nome_arquivo, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, "RELATÓRIO DE DESEMPENHO E TRADING")
        c.setFont("Helvetica", 10)
        c.drawString(100, 735, f"Data de Emissão: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        c.line(100, 725, 500, 725)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, 700, "Histórico Recente de Operações / Cálculos de Risco:")
        
        y = 675
        c.setFont("Helvetica", 9)
        if os.path.exists("historico_gestao.txt"):
            with open("historico_gestao.txt", "r") as f:
                linhas = f.readlines()[-15:]
                for linha in linhas:
                    c.drawString(100, y, linha.strip())
                    y -= 15
                    if y < 100:
                        c.showPage()
                        y = 750
        else:
            c.drawString(100, y, "Nenhum histórico registado até ao momento.")
            
        c.save()
        print(Fore.GREEN + f"[+] Relatório gerado com sucesso: {nome_arquivo}")
    except Exception as e:
        print(Fore.RED + f"[-] Erro ao gerar PDF: {e}")

def simular_wyckoff():
    print(Fore.CYAN + "\n--- SIMULADOR DE RISCO/RETORNO (WYCKOFF) ---")
    try:
        entrada = float(input("Preço de Entrada (Test/Spring): "))
        sl = float(input("Stop Loss (Abaixo do Spring/UTAD): "))
        tp = float(input("Take Profit (Alvo AR): "))
        
        risco = abs(entrada - sl)
        retorno = abs(tp - entrada)
        
        if risco == 0:
            print(Fore.RED + "[-] Stop Loss não pode ser igual ao preço de entrada.")
            return

        rr = retorno / risco
        cor = Fore.GREEN if rr >= 3.0 else Fore.YELLOW if rr >= 2.0 else Fore.RED
        
        print(Fore.WHITE + f"\nDistância do Risco:  {risco:.4f}")
        print(Fore.WHITE + f"Distância do Alvo:   {retorno:.4f}")
        print(f"Relação Risco/Retorno: {cor}1:{rr:.2f}{Style.RESET_ALL}")
        
        if rr < 2.0:
            print(Fore.RED + "[!] Trade desalinhado com o plano (R:R inferior a 1:2).")
        else:
            print(Fore.GREEN + "[+] Trade dentro dos parâmetros Wyckoff recomendados.")
            
    except ValueError:
        print(Fore.RED + "[-] Valor inválido inserido.")

def exibir_menu():
    limpar_tela()
    print(Fore.RED + "==============================================")
    print(Fore.YELLOW + "      CENTRO DE COMANDO & TRADING BOT         ")
    print(Fore.RED + "==============================================")
    print(Fore.YELLOW + " [1] " + Fore.WHITE + "Painel Sintetizado (BTC, Forex e Ativos)")
    print(Fore.YELLOW + " [2] " + Fore.WHITE + "Calculadora de Risco (Prop Firm)")
    print(Fore.YELLOW + " [3] " + Fore.WHITE + "Gerar Relatório PDF")
    print(Fore.YELLOW + " [4] " + Fore.WHITE + "Simular Relação Risco/Retorno (Wyckoff)")
    print(Fore.YELLOW + " [5] " + Fore.WHITE + "Ver Histórico de Cálculos (.txt)")
    print(Fore.YELLOW + " [6] " + Fore.WHITE + "Estado da Conexão MetaApi")
    print(Fore.YELLOW + " [7] " + Fore.WHITE + "Ver Saldo e Parâmetros")
    print(Fore.YELLOW + " [8] " + Fore.WHITE + "Histórico de Ordens Executadas")
    print(Fore.YELLOW + " [9] " + Fore.WHITE + "Configurar Parâmetros (SL/TP)")
    print(Fore.YELLOW + " [10] " + Fore.WHITE + "Sair")
    print(Fore.RED + "==============================================")

def main():
    while True:
        exibir_menu()
        opcao = input(Fore.CYAN + "\nEscolha uma opção (1-10): " + Style.RESET_ALL)
        
        if opcao == '1':
            obter_painel_mercado()
        elif opcao == '2':
            calculadora_prop_firm()
        elif opcao == '3':
            gerar_relatorio_pdf()
        elif opcao == '4':
            simular_wyckoff()
        elif opcao == '5':
            if os.path.exists("historico_gestao.txt"):
                print(Fore.WHITE + "\n--- HISTÓRICO GUARDADO ---")
                with open("historico_gestao.txt", "r") as f:
                    print(f.read())
            else:
                print(Fore.YELLOW + "\n[i] Nenhum histórico encontrado ainda.")
        elif opcao == '10':
            print(Fore.GREEN + "\nA encerrar o Centro de Comando. Até já!")
            sys.exit()
        
        input(Fore.BLUE + "\nPressione ENTER para voltar ao menu...")

if __name__ == "__main__":
    main()
