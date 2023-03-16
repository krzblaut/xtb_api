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
        self.shopping_list = self.config['shopping_list']
        self.balance_required = self.config['balance_required']
        self.acc_balance, self.acc_equity, self.acc_currency = self.get_account_info()
        
    def make_trades(self):
        if self.validate() == True:
            print('walidacja ok')
            self.sclient = APIStreamClient(ssId=self.ssid, tickFun=self.process_ticks)
            self.sclient.subscribePrices(self.get_symbols())
            self.calculate_position_sizes()
            for x in self.shopping_list:
                if x['volume'] > 0:
                    status, order_number = self.open_order(
                        symbol = x['symbol'], 
                        price = x['ask'],
                        volume= x['volume']
                        )
                    x['order_placed'] = status
                    time.sleep(2)
                    x['order_number'] = order_number
                    if self.check_order(order_number) == 3:
                        x['trade_status'] = 'success'
                    else:
                        x['trade_status'] = 'failed'
                    time.sleep(0.2)
                else:
                    x['order_placed'] = False
                    x['trade_status'] = 'Not enough funds to buy at least one stock.'
            print(self.shopping_list)

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
    
    def check_trading_hours(self):
        symbols = self.get_symbols()
        trading_hours_response = self.client.execute(trading_hours_command(symbols))
        time, day = self.get_time()
        for i in trading_hours_response['returnData']:
            open_hours = []
            for x in i['trading']:
                if x['day'] == day:
                    open_hours.append((x['fromT'], x['toT']))
            for x in self.shopping_list:
                if x['symbol'] == i['symbol']:
                    x['trading_hours'] = open_hours

    def check_if_market_opened(self):
        self.check_trading_hours()
        ms_time, day = self.get_time()
        status = True
        symbol_closed = []
        for instrument in self.shopping_list:
            if instrument['trading_hours'][0][0] < ms_time < instrument['trading_hours'][0][-1] or \
               instrument['trading_hours'][-1][0] < ms_time < instrument['trading_hours'][-1][-1]:
                pass
            else:
                symbol_closed.append(instrument['symbol'])
                status = False
        if status == False:
            print('market closed for symbols: ', symbol_closed)
        return status

    def get_time(self):
        cet = pytz.timezone('Europe/Berlin')
        now = datetime.now(cet)
        midnight = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=cet)
        delta = now - midnight
        milliseconds_since_midnight = int(delta.total_seconds() * 1000)
        week_day = now.weekday() + 1
        return milliseconds_since_midnight, week_day

    def validate(self):
        if self.login_response['status'] == False:
            print('login error, check credentials')
            return False
        elif self.acc_balance < self.balance_required:
            print('account balance smaller then required.')
            return False
        elif self.validate_tickers() == False:
            return False
        elif self.validate_shopping_list_percentage() == False:
            return False
        elif self.check_if_market_opened() == False:
            return False
        else:
            return True

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
            #send notification
            print('naucz sie dodawać zjebie')
            status = False
        return status
        
    def validate_tickers(self):
        invalid_tickers = []
        status = True
        for x in self.shopping_list:
            latest_price_response = self.client.execute(latest_price_command(x['symbol']))
            if latest_price_response['status'] == False:
                invalid_tickers.append(x['symbol'])
                status = False
            else:
                x['ask'] = latest_price_response['returnData']['ask']
                x['currency'] = latest_price_response['returnData']['currency']
            time.sleep(0.2)
        if status == False: 
            #send notification
            print(f'Tickers {invalid_tickers} are invalid.')
        return status
    
    def get_account_info(self):
        balance_response = self.client.execute(get_balance_command())
        print(balance_response)
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


xtb = xtbTrader()
xtb.make_trades()

