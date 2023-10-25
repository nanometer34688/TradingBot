import datetime
import time
import pandas as pd

class SilverBullet():
    def __init__(self, oanda, discord) -> None:
        self.oanda = oanda
        self.trading_hours ={"StartHour":20, "EndHour":15}
        self.instrument = "SPX500_USD"
        self.discord = discord

        # Handle 1 trade each way
        self.bullish_trade = False
        self.bearish_trade = False

    def in_trading_window(self):
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%H:%M:%S")
        print("\r" + "Current time: " + formatted_time, end="")
        time.sleep(1)  # Wait for 10 second before the next time update
        if current_time.hour == self.trading_hours["StartHour"]:
            return True
        else:
            # RESET TO ALLOW TRADING FOR NEXT SESSION
            self.bullish_trade = False
            self.bearish_trade = False
        return False

    def look_for_trades(self):
        if self.in_trading_window():
            candles = self.oanda.get_candles(instrument=self.instrument, count=5)[:-1] # Last one is incomplete candle
            formatted_candles = self.format_candles(candles)

            ### STEP 1 - FIND THE FVG ###
            fvg = self.find_fair_value_gaps(formatted_candles)
            if fvg:
                print(fvg)
            if "type" in fvg:
                if "BUY" == fvg["type"] and not self.bullish_trade:
                    tradeDetails = {"type":"BUY",
                                    "StopLoss":float(fvg["sl"]),
                                    "symbol":self.instrument,
                                    "price":float(fvg["price"])}
                    self.bullish_trade = True
                    fixed_trade = self.fix_stop_loss(tradeDetails)
                    self.set_pending_order(fixed_trade)

                elif "SELL" == fvg["type"] and not self.bearish_trade:
                    tradeDetails = {"type":"SELL",
                                    "StopLoss":float(fvg["sl"]),
                                    "symbol":self.instrument,
                                    "price":float(fvg["price"])}
                    self.bearish_trade = True
                    fixed_trade = self.fix_stop_loss(tradeDetails)
                    self.set_pending_order(fixed_trade)

    def fix_stop_loss(self, trade_details):
        price = trade_details["price"]
        sl = trade_details["StopLoss"]
        if abs(price - sl) < 3:
            if trade_details["type"] == "BUY":
                trade_details["StopLoss"] = price + 3
            else:
                trade_details["StopLoss"] = price - 3
        return trade_details
    
    def set_pending_order(self, tradeDetails):
        ret = self.oanda.calculate_trade(tradeDetails=tradeDetails, trade_order_type="LIMIT")
        print(ret)
        try:
            ret = self.discord.send_message(str(tradeDetails)) # SEND DISCORD MESSAGE
            print(ret)
        except Exception as e:
            print("DISCORD ERROR: ", e)
        return ret        

    def format_candles(self, candles):
        # Extract data for DataFrame
        formatted_data = [
            {
                'time': entry['time'],
                'Low': entry['mid']['l'],
                'High': entry['mid']['h'],
                'Open': entry['mid']['o'],
                'Close': entry['mid']['c']
            }
            for entry in candles
        ]

        # Create a DataFrame
        df = pd.DataFrame(formatted_data)
        return df


    def find_fair_value_gaps(self, df):
        for i in range(3, len(df)):
            current_candle = df.iloc[i]
            previous_candle = df.iloc[i - 1]
            preceding_candle = df.iloc[i - 2]

            # Check for fair value gaps due to large buying pressure
            if (
                current_candle["Low"] > preceding_candle["High"] and
                previous_candle["Close"] > preceding_candle["High"] 
            ):
                entry_price = current_candle["Low"]
                sl = preceding_candle["Low"]
                data = {"price":entry_price,
                        "sl":sl,
                        "type": "BUY"}
                return data

            # Check for fair value gaps due to large selling pressure
            if (
                current_candle["High"] < preceding_candle["Low"] and
                previous_candle["Close"] < preceding_candle["Low"]
            ):
                entry_price = current_candle["High"]
                sl = preceding_candle["High"]
                data = {"price":entry_price,
                        "sl":sl,
                        "type": "SELL"}
                return data
        return {}