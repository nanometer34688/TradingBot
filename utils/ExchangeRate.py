import MetaTrader5 as mt5

class CurrencyRates:
    def __init__(self, symbol,base_currency="GBP"):
        self.symbol = symbol
        mt5.initialize()  
        self.mapped_currency = { # Indicies in their base currency
            "UK100" : "GBP",
            "NAS100": "USD",
            "GER40": "EUR",
            "US30": "USD",
            "US500": "USD",
            "XRPUSD": "USD",
            "XAUUSD":"USD"
        }
        self.base_currency = base_currency

    def calcualte_exchange_rate(self):
        if self.symbol in self.mapped_currency:
            currency = self.mapped_currency[self.symbol]
            if currency == self.base_currency:
                return 1 # No need to change exchage rate
        else:
            currency = self.symbol[:3]
        try:
            symbol = self.base_currency + currency     
            print(symbol)
            price = mt5.symbol_info_tick(symbol).ask # BUY
        except:
            symbol = currency + self.base_currency     
            print(symbol)
            price = mt5.symbol_info_tick(symbol).ask # BUY
        return price

if __name__ == "__main__":
    cr = CurrencyRates("AUDJPY")
    exch = cr.calcualte_exchange_rate()
    print(exch)