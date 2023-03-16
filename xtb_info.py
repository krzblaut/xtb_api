import json
from xAPIConnector import APIClient, APIStreamClient
import time
import pytz
from datetime import datetime, timedelta

# Command templates
def baseCommand(commandName, arguments=None):
    if arguments==None:
        arguments = dict()
    return dict([('command', commandName), ('arguments', arguments)])

def loginCommand(userId, password, appName=''):
    return baseCommand('login', dict(userId=userId, password=password, appName=appName))

def latest_price_command(symbol):
    return baseCommand('getSymbol', dict(symbol=symbol))

def trading_hours_command(symbols):
    return baseCommand('getTradingHours', dict(symbols=symbols))

def get_balance_command():
    return baseCommand('getMarginLevel')

def open_order_command(tradeTransInfo):
    return baseCommand('tradeTransaction', dict(tradeTransInfo=tradeTransInfo))

def check_order_command(order):
    return baseCommand('tradeTransactionStatus', dict(order=order))


class xtbTrader:

    global shopping_list

    def __init__(self):
        self.config = json.load(open('config.json'))
        self.client = APIClient()
        self.id = self.config['username'] 
        self.password = self.config['password']
        self.login_response = self.login()
        self.ssid = self.login_response['streamSessionId']
        self.sclient = APIStreamClient(ssId=self.ssid, tickFun=self.process_ticks)
        self.shopping_list = self.config['shopping_list']
        self.balance_required = self.config['balance_required']
        self.acc_balance, self.acc_equity, self.acc_currency = self.get_account_info()
        
    def make_trades(self):
        if self.validate() == True:
            self.sclient.subscribePrices(self.get_symbols())
            self.calculate_position_sizes()
        #     for x in self.shopping_list:
        #         status, order_number = self.open_order(
        #             symbol = x['symbol'], 
        #             price = x['ask'],
        #             volume= x['volume']
        #             )
        #         x['order_placed'] = status
        #         time.sleep(2)
        #         x['order_number'] = order_number
        #         if self.check_order(order_number) == 3:
        #             x['trade_status'] = 'success'
        #         else:
        #             x['trade_status'] = 'failed'
        #         time.sleep(0.2)
        # print(self.shopping_list)

    def open_order(self, symbol, price, volume, transaction_type=0, order=0, cmd=0, comment="", expiration=0, sl=0, tp=0):
        TRADE_TRANS_INFO = {
            "cmd": cmd,
            "customComment": comment,
            "expiration": expiration,
            "offset": -1,
            "order": order,
            "price": price,
            "sl": sl,
            "symbol": symbol,
            "tp": tp,
            "type": transaction_type,
            "volume": volume
        }

        open_order_response = self.client.execute(open_order_command(tradeTransInfo=TRADE_TRANS_INFO))
        if open_order_response['status'] == True:
            return True, open_order_response['returnData']['order']
        else:
            return False, 0

    def check_order(self, order):
        check_order_response = self.client.execute(check_order_command(order))
        status = check_order_response['returnData']['requestStatus']
        return status
    
    def check_trade_hours(self):
        symbols = self.get_symbols()
        trading_hours_response = self.client.execute(trading_hours_command(symbols))
        for i in trading_hours_response['returnData']:
            print(i)
        print(trading_hours_response)
        #TUTAJ SKOŃCZYŁEM

    def get_time(self):
        cet = pytz.timezone('Europe/Berlin')
        now = datetime.now(cet)
        midnight = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=cet)
        delta = now - midnight
        milliseconds_since_midnight = int(delta.total_seconds() * 1000)
        week_day = now.weekday() + 1
        return milliseconds_since_midnight, week_day


    def validate(self):
        if self.login_response['status']  and \
            self.validate_shopping_list_percentage()  and \
            self.validate_tickers() and self.acc_balance > self.balance_required:
            return True
        else:
            return False

    def login(self):
        loginResponse = self.client.execute(
            loginCommand(userId=self.id, password=self.password)
            )
        if loginResponse['status'] == False:
            print('Login failed. Error code: {0}'.format(loginResponse['errorCode']))
        return loginResponse
        
    def validate_shopping_list_percentage(self):
        percentage_sum = 0
        status = True
        for instrument in self.shopping_list:
            percentage_sum += instrument['percentage'] 
        if percentage_sum > 100:
            # send email notification
            status = False
        return status
        
    def validate_tickers(self):
        invalid_tickers = []
        status = True
        for x in self.shopping_list:
            latest_price_response = self.client.execute(latest_price_command(x['symbol']))
            print(latest_price_response)
            if latest_price_response['status'] == False:
                invalid_tickers.append(x['symbol'])
                status = False
            else:
                x['ask'] = latest_price_response['returnData']['ask']
                x['currency'] = latest_price_response['returnData']['currency']
        if status == False:
            # send email notification 
            print(f'Tickers {invalid_tickers} are invalid.')
        return status
    
    def get_account_info(self):
        balance_response = self.client.execute(get_balance_command())
        account_balance = balance_response['returnData']['balance'] 
        account_equity = balance_response['returnData']['equity'] 
        account_currency = balance_response['returnData']['currency'] 
        return account_balance, account_equity, account_currency
    
    def get_symbols(self):
        symbols = [ x['symbol'] for x in self.shopping_list]
        return symbols
    
    def calculate_position_sizes(self):
        for x in self.shopping_list:
            if x['currency'] == self.acc_currency:
                x['volume'] = int(((x['percentage']/100)*self.acc_balance)/x['ask'])
            else:
                latest_price_response = self.client.execute(
                    latest_price_command(x['currency']+'PLN'))
                time.sleep(0.2)
                exchange_rate = latest_price_response['returnData']['ask']
                x['volume'] = int(((x['percentage']/100)*self.acc_balance)/(x['ask']*exchange_rate))
                
    def process_ticks(self, msg):
        for x in self.shopping_list:
            if x['symbol'] == msg['data']['symbol']:
                x['ask'] = msg['data']['ask']
        # [ x['ask'] = msg['data']['ask'] for x in self.shopping_list if x['symbol'] == msg['data']['symbol'] ]
        

xtb = xtbTrader()
# print(xtb.shopping_list)
print(xtb.get_time())

