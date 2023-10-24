
from forex_python.converter import CurrencyRates
import pprint
from utils import ExchangeRate, InstrumentDetails
class Trade:
    def __init__(self, tradeDetails, mt5_con, cash_risk=100, RR=2):  
        self.trade_type = tradeDetails["type"] # BUY/SELL
        self.sl = float(tradeDetails["StopLoss"])
        self.symbol = tradeDetails["symbol"]
        self.tv_price = float(tradeDetails["price"]) # TradingView price
        self.instrument_type = "forex" if self.symbol not in InstrumentDetails.instrument_details else InstrumentDetails.instrument_details[self.symbol] # Works out what instrument it is for pip dp
        self.RR = RR
        self.MT5_CONNECTION = mt5_con
        self.price = 0
        self.lot_size = 0
        self.cash_risk = cash_risk
        self.comment = "" # Used to send to MT5
    
    def get_mt5_tv_price_difference(self):
        # Becuase the TradingView price may be different to the broker you are using on MT5, we need to make sure the SL and TP are set appropriately
        mt5_price = self.get_current_price()
        difference = mt5_price - self.tv_price
        return difference*1

    def get_current_price(self):
        price = float(self.MT5_CONNECTION.get_price(self.trade_type))
        return price

    def calculate_tp(self):
        if self.trade_type == "BUY":
            take_profit = self.price + (abs(self.sl-self.price) * self.RR) 
        else:
            take_profit = self.price - (abs(self.sl-self.price) * self.RR)
        return take_profit

    def calculate_lot_size(self):
        JPY_pair = True if "JPY" in self.symbol else False
        method = 0 if self.instrument_type == "index" else 3 if self.instrument_type == "gold" else 2
        lot_size = self.MT5_CONNECTION.size_position(
                                        price = self.price,
                                        tradeType=self.trade_type, 
                                        stop=self.sl, 
                                        cash_risk=self.cash_risk, 
                                        method=method, 
                                        exchange_rate=self.exchange_rate, 
                                        JPY_pair=JPY_pair, 
                                        instrument_type=self.instrument_type)
        return lot_size

    def calculate_trade(self):
        # self.price = self.get_current_price()
        price_difference = self.get_mt5_tv_price_difference() # Difference in price with TradingView and your Broker
        self.price = self.tv_price+ price_difference 
        self.sl = self.sl + price_difference
        self.tp = self.calculate_tp() + price_difference
        exchange = ExchangeRate.CurrencyRates(self.symbol)
        self.exchange_rate = self.price if "GBP" in self.symbol else exchange.calcualte_exchange_rate()
        print("EXCHANGE RATE ", self.exchange_rate)
        self.lot_size = self.calculate_lot_size()

    def place_order(self):
        if "JPY" in self.symbol:
            self.tp = float("{:.3f}".format(self.tp))
            self.sl = float("{:.3f}".format(self.sl))
        rtn = self.MT5_CONNECTION.place_order(order_type=self.trade_type, 
                                    volume=self.lot_size, 
                                    stop_loss=self.sl, 
                                    tp=self.tp, 
                                    comment=self.comment, 
                                    direct=True, 
                                    instrument_type=self.instrument_type)
        return {"msg":str(rtn)}

    def print_details(self):
        variables = vars(self)
        print()
        print("--------------------TRADE DETAILS--------------------")
        pprint.pprint(variables)
        print("-------------------END TRADE DETAILS-----------------")
        print()

