import oandapyV20
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.pricing as pricing
from oandapyV20.contrib.requests import (
    LimitOrderRequest,
    MarketOrderRequest,
    TakeProfitDetails,
    StopLossDetails,
    TrailingStopLossDetails)
from oandapyV20.definitions.orders import TimeInForce
import oandapyV20.endpoints.instruments as instruments
from utils import InstrumentDetails
import json
import math

class Oanda:
    def __init__(self, access_token, debug=False):
        self.client = oandapyV20.API(access_token=access_token)
        self.accountID = ""
        self.debug = debug

        # TRADE INIT
        self.trade_type = "" # BUY/SELL
        self.sl = 0.0
        self.symbol = ""
        self.tv_price = 0.0 # TradingView price
        self.instrument_type = ""
        self.RR = 2 # Risk to Reward
        self.price = 0
        self.lot_size = 0
        self.cash_risk = 0.0
        self.comment = "" # Used to send to OANDA


    def choose_account(self, accountID=None):
        if accountID == None:
            r = accounts.AccountList()
            response = self.client.request(r)
            num_of_accounts = len(response["accounts"])
            print("{} Account(s) found".format(num_of_accounts))
            print(num_of_accounts)
            print(type(num_of_accounts))
            if num_of_accounts > 1:
                print("More than 1 account found")
                accounts_str = ""
                for i, account in enumerate(response["accounts"]):
                    tags = account["tags"][0] if len(account["tags"]) > 0 else ""
                    accounts_str += "\n{}: {}".format(i, account["id"] + " - " + tags)
                choosing = True
                while choosing:
                    user_input = input("Accounts found: \n{}\nWhich account would you like to use?: ".format(accounts_str))
                    if user_input.isnumeric():
                        if int(user_input) >= 0 and int(user_input) < len(response["accounts"]):
                            self.accountID = response["accounts"][int(user_input)]["id"]
                            print("Using account: {}".format(self.accountID))
                            choosing = False
            else:
                self.accountID = response["accounts"][0]["id"]
                print("Using account: {}".format(self.accountID))
        else:
            self.accountID = accountID

    def get_open_trades(self):
        try:
            r = trades.OpenTrades(accountID=self.accountID)
            return self.client.request(r)["trades"]
        except Exception as e:
            print("[ERROR] - {}".format(e))
            return False
    
    def create_market_order(self, instrument="EUR_USD", units=1,takeProfitOnFill=None, stopLossOnFill=1.019):
        print("TAKE PROFIT: {}\nSTOP LOSS: {}\nUNITS: {}".format(takeProfitOnFill, stopLossOnFill,units))
        if takeProfitOnFill == None:
            mktOrder = MarketOrderRequest(instrument=instrument,
                                        units=units,
                                        stopLossOnFill=StopLossDetails(price=stopLossOnFill).data,
                                        timeInForce=TimeInForce.FOK,
                                        ).data
        else: 
            mktOrder = MarketOrderRequest(instrument=instrument,
                                      units=units,
                                      stopLossOnFill=StopLossDetails(price=stopLossOnFill).data,
                                      takeProfitOnFill=TakeProfitDetails(price=takeProfitOnFill).data,
                                      timeInForce=TimeInForce.FOK,
                                      ).data
        r = orders.OrderCreate(accountID=self.accountID, data=mktOrder)
        rv = self.client.request(r)
        if self.debug:
            print("Response: {}\n{}".format(r.status_code, json.dumps(rv, indent=2)))
        return rv
    
    def create_limit_order(self, instrument="EUR_USD", units=1,takeProfitOnFill=None, stopLossOnFill=1.019):
        print("limit")
        limitOrder = LimitOrderRequest(instrument=instrument,
                                       units=units,
                                       price=self.price,
                                       stopLossOnFill=StopLossDetails(price=stopLossOnFill).data,
                                       takeProfitOnFill=TakeProfitDetails(price=takeProfitOnFill).data,
                                       timeInForce=TimeInForce.GTC,).data
        r = orders.OrderCreate(accountID=self.accountID, data=limitOrder)
        rv = self.client.request(r)
        if self.debug:
            print("Response: {}\n{}".format(r.status_code, json.dumps(rv, indent=2)))
        return rv
    
    def close_all_open_orders(self):
        orders = self.get_open_trades()
        if orders["trades"]:
            for trade in orders["trades"]:
                print("Closing Trade ID {}".format(trade["id"]))
                self.close_trade_order(trade["id"])

    def close_trade_order(self, trade_id):
        r = trades.TradeClose(accountID=self.accountID, tradeID=trade_id)
        rv = self.client.request(r)
        if self.debug:
            print("Response: {}\n{}".format(r.status_code, json.dumps(rv, indent=2)))

    def get_trade_status(self, trade_id):
        open_trades = self.get_open_trades()
        if open_trades:
            for trade in open_trades["trades"]:
                if trade_id == trade["id"]:
                    return trade
        return False
    
    def get_trade_data(self, tradeID):
        trades = self.get_open_trades()["trades"]
        trade_data = []
        for trade in trades:
            if trade["id"] == tradeID:
                trade_data = trade
                break
        return trade_data
    
    def get_account_value(self):
        r = accounts.AccountDetails(self.accountID)
        details = self.client.request(r)
        return details["account"]["balance"]
    
    def get_cash_risk(self, risk_perc=1):
        account_value = self.get_account_value()
        return float(account_value) * risk_perc
    
    def get_current_price(self, instrument="NAS100_USD"):
        params = {
            "granularity": "M1",
            "count": 1,
        }
        r = instruments.InstrumentsCandles(instrument=instrument, params=params)
        response = self.client.request(r)
        price = response["candles"][0]["mid"]["c"]
        return price
    
    def get_candles(self, instrument="NAS100_USD", granularity="M1", count=100):
        params = {
            "granularity": granularity,
            "count": count,
        }
        r = instruments.InstrumentsCandles(instrument=instrument, params=params)
        response = self.client.request(r)
        candles = response["candles"]
        return candles
        
    def getInstrumentsList(self, type="CFD"):
        params = {"instruments": None}
        r = accounts.AccountInstruments(accountID=self.accountID, params=params)
        instruments = []
        try:
            rv = self.client.request(r)
        except oandapyV20.exceptions.V20Error as err:
            print("Error:", r.status_code, err)
        else:
            print("The result:")
            res = json.dumps(rv, indent=2)
            result = json.loads(res)
            for instrument in result['instruments']:
                if (instrument['type'] == type):
                    instruments.append([instrument['name'], instrument['displayName']])

        return instruments
    
    def convert_instrument(self, instrument):
        instruments = {"GBPJPY": "GBP_JPY",
                       "EURUSD": "EUR_USD",
                       "NAS100": "NAS100_USD",
                       "XAUUSD": "XAU_USD",
                       "GBPUSD": "GBP_USD"}
        if instrument in instruments:
            return instruments[instrument]
        else:
            return instrument

    def calculate_tp(self):
        if self.trade_type == "BUY":
            take_profit = self.price + (abs(self.sl-self.price) * self.RR) 
        else:
            take_profit = self.price - (abs(self.sl-self.price) * self.RR)
        return take_profit

    def calculate_exchange_rate(self):
        mapped_currency = { # Indicies in their base currency
            "NAS100_USD": "USD",
            "XAU_USD":"USD",
            "EUR_USD": "USD",
            "SPX500_USD": "USD"
        }
        currency = "GBP_" + mapped_currency[self.symbol]
        return float(self.get_current_price(currency))
    
    def replace_order(self, orderID, data):
        print(self.accountID, orderID, data)
        r = orders.OrderReplace(accountID=self.accountID, orderID=orderID, data=data)
        return self.client.request(r)
    
    def update_trade(self, tradeID, data):
        print(self.accountID, tradeID, data)
        r = trades.TradeCRCDO(self.accountID, tradeID, data)
        return self.client.request(r)
    
    def cancel_order(self, orderID, perc_units=1.0):
        trade = self.get_trade_data(orderID)
        unitsOrdered = float(trade["currentUnits"])
        units_to_close = unitsOrdered * perc_units
        data = {
                "units": str(int(abs(units_to_close)))
                }
        print(data)
        r = trades.TradeClose(self.accountID, tradeID=orderID, data=data)
        return self.client.request(r)
    
    def get_current_trade_perc(self, tradeID):
        trade = self.get_trade_data(tradeID)
        if trade:
            instrument = trade["instrument"]
            order_price = float(trade["price"])
            order_stop_loss = float(trade["stopLossOrder"]["price"])
            current_price = float(self.get_current_price(instrument))
            unitsOrdered = float(trade["currentUnits"])
            orderType = "BUY" if unitsOrdered > 0 else "SELL"
            percentage_gain = 0 # Init
            try:
                if orderType == "BUY":
                    percentage_gain = ((current_price - order_price) / abs(order_stop_loss-order_price))
                if orderType == "SELL":
                    percentage_gain = ((order_price - current_price) / abs(order_stop_loss-order_price))
            except ZeroDivisionError:
                print('Cannot devide by zero.')
            return percentage_gain
        return False
    
    def generate_take_profit_data(self, take_profit_amount):
        data = {
            "takeProfit": {
                "timeInForce": "GTC",
                "price": str(take_profit_amount)
            }
        }
        return data

    def generate_stop_loss_data(self, stop_loss_amount):
        data = {
            "stopLoss": {
                "timeInForce": "GTC",
                "price": str(stop_loss_amount)
            }
        }
        return data
    
    def get_size_position(self, method=1):
        '''
        Helper function to calcuate the position size given a known amount of risk.
    
        *Args*
        - price: Float, the current price of the instrument
        - stop: Float, price level of the stop loss
        - risk: Float, the amount of the account equity to risk
    
        *Kwargs*
        - JPY_pair: Bool, whether the instrument being traded is part of a JPY
        pair. The muliplier used for calculations will be changed as a result.
        - Method: Int,
            - 0: Acc currency and counter currency are the same
            - 1: Acc currency is same as base currency
            - 2: Acc currency is neither same as base or counter currency
        - exchange_rate: Float, is the exchange rate between the account currency
        and the counter currency. Required for method 2.
        '''
        JPY_pair = False
        if "JPY" in self.symbol:
            JPY_pair = True
        if self.instrument_type == "index":  # Check if index
           multiplier = 0.001 # no multiplier
        elif JPY_pair: # check if a YEN cross and change the multiplier
            print("JPY PAIR")
            multiplier = 0.01
        else: #check if other currency
            multiplier = 0.0001
            
       
        #Calc how much to risk
        stop_pips_int = abs((self.price - self.sl) / multiplier)
        print("stop_pips_int", stop_pips_int)
        pip_value = self.cash_risk / stop_pips_int
        print("Per point risk", pip_value)

        # pip_value = pip_value * exchange_rate
        # units = pip_value / multiplier
        # print(units)

        if method == 1:
            #pip_value = pip_value * price
            units = pip_value / multiplier

        elif method == 2:    
            pip_value = pip_value * self.exchange_rate
            units = pip_value / multiplier
            units = units/100000
        elif method == 3:   
            pip_value = pip_value * self.exchange_rate
            units = pip_value / multiplier
            units = units/100
        else: # is method 0
            units = pip_value / multiplier
            units = units * self.exchange_rate
        print("units", units)
        lot_size = (math.floor(units * 100)/100.0)/10

        if self.instrument_type == "index":
            lot_size = round(lot_size, 2)
        if self.instrument_type == "gold":
            lot_size = round(lot_size, 2)
        if self.instrument_type == "forex":       
            lot_size = round(lot_size, 2)
        return float(lot_size)
    
    def format_prices(self, price):
        if self.instrument_type == "index" or self.instrument_type == "gold":
            formatted_price = round(price, 2)
            formatted_price = "{:.2f}".format(formatted_price)
        elif "JPY" in self.symbol:
            formatted_price = round(price, 3)
            formatted_price = "{:.3f}".format(formatted_price)
        elif self.instrument_type == "forex":
            formatted_price = round(price, 5)
            formatted_price = "{:.5f}".format(formatted_price)
        return formatted_price

    def format_units(self, units):
        if self.instrument_type == "index":
            formatted_units = round(units, 2)
            formatted_units = "{:.1f}".format(formatted_units)
        if self.instrument_type == "gold":
            formatted_units = round(units, 2)
            formatted_units = "{:.1f}".format(formatted_units)
        if self.instrument_type == "forex":       
            formatted_units = round(units, 1)
            formatted_units = "{:.0f}".format(formatted_units)
        return formatted_units 

    def calculate_trade(self,tradeDetails, risk_perc=0.02, trade_order_type="LIMIT"):
        self.trade_type = tradeDetails["type"] # BUY/SELL
        self.sl = float(tradeDetails["StopLoss"])
        self.symbol = tradeDetails["symbol"]
        self.instrument_type = "forex" if self.symbol not in InstrumentDetails.instrument_details else InstrumentDetails.instrument_details[self.symbol] # Works out what instrument it is for pip dp
        self.symbol = self.convert_instrument(self.symbol)
        # tv_price = float(tradeDetails["price"]) # TradingView price
        self.cash_risk = self.get_cash_risk(risk_perc)

        self.price  = tradeDetails["price"] #float(self.get_current_price(self.symbol)) #- tv_price # Difference in price with TradingView and your Broker
        self.sl = self.sl 

        self.sl = round(self.sl, 1) if self.instrument_type == "index" or  self.instrument_type == "gold" else round(self.sl, 3) if "JPY" in self.symbol else round(self.sl, 4)
        self.tp = self.calculate_tp() 
        self.tp = round(self.tp, 1) if self.instrument_type == "index" or  self.instrument_type == "gold" else round(self.tp, 3) if "JPY" in self.symbol else round(self.tp, 4)

        print("PRICE: {}\nSYMBOL :{}\nCASH RISK: {}\n".format(self.price, self.symbol, self.cash_risk))

        self.exchange_rate = float(self.price) if "GBP" in self.symbol else self.calculate_exchange_rate()
        method = 0 if self.instrument_type == "index" else 3 if self.instrument_type == "gold" else 2
        print("METHOD", method)
        self.lot_size = self.calculate_position_size()
        print( self.lot_size ," self.lot_size ")
        print("exchange_rate", self.exchange_rate)
        print(self.lot_size)
        print(self.instrument_type)
        print(self.sl)
        trade_type = 1
        if self.trade_type == "SELL":
            trade_type = -1

        if self.instrument_type == "forex":
            units = self.lot_size * 100000 * trade_type
        elif self.instrument_type == "gold":
            units = self.lot_size * 100 * trade_type
        else:
            units = self.lot_size * trade_type

        units = int(float(self.format_units(units)))

        formatted_tp = self.format_prices(self.tp) 
        formatted_sl = self.format_prices(self.sl) 
        if trade_order_type == "LIMIT":
            return self.create_limit_order(instrument=self.symbol, units=units,takeProfitOnFill=formatted_tp, stopLossOnFill=formatted_sl)
        else:
            return self.create_market_order(instrument=self.symbol, units=units,takeProfitOnFill=formatted_tp, stopLossOnFill=formatted_sl)
    
    def calculate_position_size(self):
        # Calculate the dollar amount at risk per unit
        dollars_at_risk_per_unit = abs(self.price - self.sl)
        print("DATA")
        print(dollars_at_risk_per_unit, self.price , self.sl)
        
        # Calculate the unit amount to risk the specified amount
        unit_amount = self.cash_risk / dollars_at_risk_per_unit
        print(unit_amount, self.cash_risk , dollars_at_risk_per_unit)
        print("DATA END")
        return unit_amount

    def get_live_pricing(self, instrument):
        print(self.accountID)
        return pricing.PricingStream(accountID=self.accountID, params={"instruments": instrument})