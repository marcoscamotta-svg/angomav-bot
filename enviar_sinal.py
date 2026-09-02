import requests
import json

# IP ou Domínio da sua VPS onde o receptor está a rodar
VPS_URL = "http://SEU_IP_DA_VPS:5000/webhook"

def enviar_ordem_para_mt5(acao, preco_atual, sl, tp, risco_perc=0.01):
    payload = {
        "token_seguranca": "MINHA_CHAVE_SECRETA_PROP",
        "simbolo": "XAUUSD",
        "acao": acao,            # "BUY" ou "SELL"
        "preco": preco_atual,
        "sl": sl,
        "tp": tp,
        "risco": risco_perc
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        resposta = requests.post(VPS_URL, data=json.dumps(payload), headers=headers, timeout=5)
        print(f"[*] Resposta da VPS: {resposta.status_code} - {resposta.text}")
    except Exception as e:
        print(f"[!] Erro ao enviar sinal para a VPS: {e}")

if __name__ == "__main__":
    # Exemplo de teste manual de envio:
    print("[*] Enviando sinal de teste de COMPRA no XAUUSD...")
    enviar_ordem_para_mt5(
        acao="BUY",
        preco_atual=2500.50,
        sl=2495.00,
        tp=2515.00,
        risco_perc=0.01
    )
