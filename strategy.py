import asyncio
from datetime import datetime

async def analisar_estrategia(connection, bot_status):
    """
    Análise SMC (FVG + CHoCH) Real com Leitura Leve de Velas em XAU/USD (Ouro)
    """
    try:
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

        if current_price == 0.0:
            return  # Aguarda a próxima varredura se a cotação ainda não carregou

        hora_atual = datetime.now().strftime("%H:%M:%S")
        bot_status["online"] = True
        bot_status["connected"] = True
        bot_status["last_scan"] = hora_atual

        # 3. Leitura LEVE do Histórico de Velas (Apenas 5 velas para não dar timeout)
        candles_m15 = []
        candles_m1 = []

        try:
            # Puxa 5 velas do gráfico M15
            candles_m15 = await connection.get_historical_candles(symbol, "15m", None, 5)
        except Exception:
            pass

        try:
            # Puxa 5 velas do gráfico M1
            candles_m1 = await connection.get_historical_candles(symbol, "1m", None, 5)
        except Exception:
            pass

        # Variáveis de Estado da Estrutura SMC
        fvg_bullish = False
        fvg_bearish = False
        choch_bullish = False
        choch_bearish = False

        # Validação de Fair Value Gap (FVG) Real em M15
        if candles_m15 and len(candles_m15) >= 3:
            candle_1 = candles_m15[-3]  # Vela 1
            candle_3 = candles_m15[-1]  # Vela 3 (Mais recente)

            # Bullish FVG: A mínima da Vela 3 é estritamente maior que a máxima da Vela 1
            if candle_3['low'] > candle_1['high']:
                fvg_bullish = True
            # Bearish FVG: A máxima da Vela 3 é estritamente menor que a mínima da Vela 1
            elif candle_3['high'] < candle_1['low']:
                fvg_bearish = True

        # Validação de Breakout / CHoCH Real em M1
        if candles_m1 and len(candles_m1) >= 2:
            prev_candle = candles_m1[-2]
            last_candle = candles_m1[-1]

            # CHoCH de Alta: Fecho da vela atual quebra o topo da vela anterior
            if last_candle['close'] > prev_candle['high']:
                choch_bullish = True
            # CHoCH de Baixa: Fecho da vela atual quebra o fundo da vela anterior
            elif last_candle['close'] < prev_candle['low']:
                choch_bearish = True

        # Define Viés Visual para o Dashboard Web
        bias_str = "BULLISH" if (fvg_bullish or choch_bullish) else ("BEARISH" if (fvg_bearish or choch_bearish) else "NEUTRO")
        
        sinal_objeto = {
            "timeframe_h1": f"Ativo: {symbol} | Preço: {current_price} | Viés: {bias_str}",
            "timeframe_m15": f"M15 FVG Bullish: {fvg_bullish} | Bearish: {fvg_bearish}",
            "timeframe_m1": f"M1 CHoCH Bullish: {choch_bullish} | Bearish: {choch_bearish}"
        }
        bot_status["last_signals"] = [sinal_objeto]

        # 4. Módulo de Execução de Ordens no MetaTrader 5
        try:
            positions = await connection.get_positions()
        except Exception:
            positions = []

        # Só executa se NÃO houver posições abertas na conta
        if len(positions) == 0:
            volume = 0.01  # Lote padrão
            
            # GATILHO COMPRA: FVG M15 + CHoCH M1
            if fvg_bullish and choch_bullish:
                sl = round(current_price - 3.0, 2)
                tp = round(current_price + 6.0, 2)
                
                print(f"🚀 [SINAL REAL SMC] A abrir COMPRA em {symbol} | Lote: {volume} | SL: {sl} | TP: {tp}")
                try:
                    result = await connection.create_market_buy_order(
                        symbol=symbol, volume=volume, stop_loss=sl, take_profit=tp
                    )
                    print(f"✅ Ordem executada com sucesso: {result}")
                except Exception as err_order:
                    print(f"⚠️ Erro ao enviar ordem no MetaTrader: {err_order}")

            # GATILHO VENDA: FVG M15 + CHoCH M1
            elif fvg_bearish and choch_bearish:
                sl = round(current_price + 3.0, 2)
                tp = round(current_price - 6.0, 2)
                
                print(f"🔻 [SINAL REAL SMC] A abrir VENDA em {symbol} | Lote: {volume} | SL: {sl} | TP: {tp}")
                try:
                    result = await connection.create_market_sell_order(
                        symbol=symbol, volume=volume, stop_loss=sl, take_profit=tp
                    )
                    print(f"✅ Ordem executada com sucesso: {result}")
                except Exception as err_order:
                    print(f"⚠️ Erro ao enviar ordem no MetaTrader: {err_order}")

    except Exception as e:
        print(f"⚠️ Erro geral na análise da estratégia: {e}")
