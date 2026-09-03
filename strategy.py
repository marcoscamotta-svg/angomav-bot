import asyncio
from datetime import datetime

# Memória interna simples para guardar as últimas cotações
precos_historico = []

async def analisar_estrategia(connection, bot_status):
    """
    Análise SMC em Tempo Real para XAU/USD (Sem chamadas pesadas de histórico)
    """
    global precos_historico
    try:
        symbol = "XAUUSD"
        current_price = 0.0

        # 1. Puxa Cotação Atual
        try:
            price_data = await connection.get_symbol_price(symbol)
            if price_data:
                current_price = price_data.get("bid", 0.0)
        except Exception as e:
            print(f"⚠️ Erro ao puxar preço: {e}")
            return

        # 2. Puxa Dados da Conta
        try:
            account_info = await connection.get_account_information()
            if account_info:
                bot_status["equity"] = round(account_info.get("equity", 0), 2)
                bot_status["balance"] = round(account_info.get("balance", 0), 2)
        except Exception:
            pass

        if current_price == 0.0:
            return

        hora_atual = datetime.now().strftime("%H:%M:%S")
        bot_status["online"] = True
        bot_status["connected"] = True
        bot_status["last_scan"] = hora_atual

        # Guardar preço na memória interna (máximo 10 cotações)
        precos_historico.append(current_price)
        if len(precos_historico) > 10:
            precos_historico.pop(0)

        # 3. Lógica SMC/Breakout com base na flutuação recente de preço
        fvg_bullish = False
        fvg_bearish = False
        choch_bullish = False
        choch_bearish = False

        if len(precos_historico) >= 3:
            p_antigo = precos_historico[0]
            p_medio = precos_historico[-2]
            p_atual = precos_historico[-1]

            # Quebra de Estrutura / Momentum de Alta
            if p_atual > p_medio and p_medio > p_antigo:
                choch_bullish = True
                fvg_bullish = True
            # Quebra de Estrutura / Momentum de Baixa
            elif p_atual < p_medio and p_medio < p_antigo:
                choch_bearish = True
                fvg_bearish = True

        bias_str = "BULLISH" if choch_bullish else ("BEARISH" if choch_bearish else "NEUTRO")
        
        sinal_objeto = {
            "timeframe_h1": f"Ativo: {symbol} | Preço Atual: {current_price} | Viés: {bias_str}",
            "timeframe_m15": f"Estrutura Alta: {fvg_bullish}",
            "timeframe_m1": f"Rompimento Recente: {choch_bullish or choch_bearish}"
        }
        bot_status["last_signals"] = [sinal_objeto]

        # 4. Execução de Ordens com Trava de Segurança
        try:
            positions = await connection.get_positions()
        except Exception:
            positions = []

        if len(positions) == 0:
            volume = 0.01  # Lote padrão no Ouro
            
            # GATILHO COMPRA
            if fvg_bullish and choch_bullish:
                sl = round(current_price - 3.0, 2)
                tp = round(current_price + 6.0, 2)
                
                print(f"🚀 [SINAL DETETADO] A abrir COMPRA em {symbol} | Preço: {current_price}")
                try:
                    result = await connection.create_market_buy_order(
                        symbol=symbol, volume=volume, stop_loss=sl, take_profit=tp
                    )
                    print(f"✅ Ordem executada: {result}")
                    precos_historico.clear() # Limpa memória após entrada
                except Exception as err_order:
                    print(f"⚠️ Erro na ordem: {err_order}")

            # GATILHO VENDA
            elif fvg_bearish and choch_bearish:
                sl = round(current_price + 3.0, 2)
                tp = round(current_price - 6.0, 2)
                
                print(f"🔻 [SINAL DETETADO] A abrir VENDA em {symbol} | Preço: {current_price}")
                try:
                    result = await connection.create_market_sell_order(
                        symbol=symbol, volume=volume, stop_loss=sl, take_profit=tp
                    )
                    print(f"✅ Ordem executada: {result}")
                    precos_historico.clear() # Limpa memória após entrada
                except Exception as err_order:
                    print(f"⚠️ Erro na ordem: {err_order}")

    except Exception as e:
        print(f"⚠️ Erro no ciclo: {e}")
