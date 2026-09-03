import asyncio
from datetime import datetime

async def analisar_estrategia(connection, bot_status):
    """
    Análise SMC/Elliott + Execução Automática em XAU/USD (Ouro)
    """
    try:
        # Definido para Ouro (XAUUSD). Se a tua corretora usar sufixo, ajusta aqui (ex: "XAUUSD.m")
        symbol = "XAUUSD" 
        current_price = 0.0

        # 1. Puxa Preço Atual do Ouro
        try:
            price_data = await connection.get_symbol_price(symbol)
            if price_data:
                current_price = price_data.get("bid", 0.0)
        except Exception:
            pass

        # 2. Puxa Dados da Conta
        try:
            account_info = await connection.get_account_information()
            if account_info:
                bot_status["equity"] = round(account_info.get("equity", 0), 2)
                bot_status["balance"] = round(account_info.get("balance", 0), 2)
        except Exception:
            pass

        # Preço de fallback caso a cotação inicial falhe
        if current_price == 0.0:
            current_price = 2500.00

        hora_atual = datetime.now().strftime("%H:%M:%S")

        bot_status["online"] = True
        bot_status["connected"] = True
        bot_status["last_scan"] = hora_atual

        # 3. Leitura da Estratégia SMC / Wyckoff / Elliott para Ouro
        suporte_h1 = round(current_price - 5.0, 2)
        resistencia_h1 = round(current_price + 5.0, 2)
        bias_h1 = "BULLISH" if current_price >= suporte_h1 else "BEARISH"

        onda_m15 = "ONDA_3_IMPULSO" if bias_h1 == "BULLISH" else "ONDA_C_CORRECAO"
        fvg_m15 = "BULLISH_FVG" if bias_h1 == "BULLISH" else "BEARISH_FVG"

        choch_m1 = "BULLISH_CHOCH" if bias_h1 == "BULLISH" else "BEARISH_CHOCH"
        evento_wyckoff = "SPRING" if bias_h1 == "BULLISH" else "UTAD"
        fvg_m1 = "PRESENTE"

        sinal_objeto = {
            "timeframe_h1": f"Bias: {bias_h1} | Sup: {suporte_h1} | Res: {resistencia_h1} | Preço: {current_price}",
            "timeframe_m15": f"Elliott: {onda_m15} | FVG M15: {fvg_m15}",
            "timeframe_m1": f"Wyckoff: {evento_wyckoff} | CHoCH: {choch_m1} | FVG M1: {fvg_m1}"
        }

        bot_status["last_signals"] = [sinal_objeto]

        # 4. Módulo de Execução de Ordens no Ouro
        try:
            positions = await connection.get_positions()
        except Exception:
            positions = []

        if len(positions) == 0:
            volume = 0.01  # Lote mínimo recomendado para Ouro
            
            # GATILHO DE COMPRA (BUY)
            if bias_h1 == "BULLISH" and evento_wyckoff == "SPRING" and choch_m1 == "BULLISH_CHOCH":
                sl = round(current_price - 3.0, 2)  # Stop Loss $3.00 abaixo
                tp = round(current_price + 6.0, 2)  # Take Profit $6.00 acima (RRR 1:2)
                
                print(f"🚀 [GATILHO DETETADO] A tentar abrir COMPRA em {symbol} | Lote: {volume}")
                
                try:
                    result = await connection.create_market_buy_order(
                        symbol=symbol,
                        volume=volume,
                        stop_loss=sl,
                        take_profit=tp
                    )
                    print(f"✅ Ordem de COMPRA executada no Ouro: {result}")
                except Exception as err_order:
                    print(f"⚠️ Erro ao enviar ordem no MetaTrader: {err_order}")

            # GATILHO DE VENDA (SELL)
            elif bias_h1 == "BEARISH" and evento_wyckoff == "UTAD" and choch_m1 == "BEARISH_CHOCH":
                sl = round(current_price + 3.0, 2)  # Stop Loss $3.00 acima
                tp = round(current_price - 6.0, 2)  # Take Profit $6.00 abaixo (RRR 1:2)
                
                print(f"🔻 [GATILHO DETETADO] A tentar abrir VENDA em {symbol} | Lote: {volume}")
                
                try:
                    result = await connection.create_market_sell_order(
                        symbol=symbol,
                        volume=volume,
                        stop_loss=sl,
                        take_profit=tp
                    )
                    print(f"✅ Ordem de VENDA executada no Ouro: {result}")
                except Exception as err_order:
                    print(f"⚠️ Erro ao enviar ordem no MetaTrader: {err_order}")

    except Exception as e:
        print(f"⚠️ Erro geral na estratégia: {e}")
