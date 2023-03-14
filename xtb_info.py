import json
from xAPIConnector import APIClient, APIStreamClient
import time

# Command templates
def baseCommand(commandName, arguments=None):
    if arguments==None:
        arguments = dict()
    return dict([('command', commandName), ('arguments', arguments)])

def loginCommand(userId, password, appName=''):
    return baseCommand('login', dict(userId=userId, password=password, appName=appName))

def latest_price_command(symbol):
    return baseCommand('getSymbol', dict(symbol=symbol))

def get_balance_command():
    return baseCommand('getMarginLevel')


class XtbData:

    global shopping_list
    global balance 

    def __init__(self):
        self.config = json.load(open('config.json'))
        self.client = APIClient()
        self.id = self.config['username'] 
        self.password = self.config['password']
        self.login_response = self.login()
        self.ssid = self.login_response['streamSessionId']
        self.sclient = APIStreamClient(ssId=self.ssid, tickFun=self.process_ticks)
        self.shopping_list = self.config['shopping_list']
        self.symbols = self.get_symbols()
        self.sclient.subscribePrices(self.symbols)

    def login(self):
        loginResponse = self.client.execute(
            loginCommand(userId=self.id, password=self.password)
            )
        if(loginResponse['status'] == False):
            print('Login failed. Error code: {0}'.format(loginResponse['errorCode']))
        return loginResponse
        
    def validate_shopping_list_percentage(self):
        percentage_sum = 0
        status = True
        for instrument in self.config['shopping_list']:
            percentage_sum += instrument['percentage'] 
        if percentage_sum != 100:
            # send email notification
            status = False
        return status
        
    def validate_tickers(self):
        invalid_tickers = []
        status = True
        for symbol in self.symbols:
            latest_price_response = self.client.execute(latest_price_command(symbol))
            if latest_price_response['status'] == False:
                invalid_tickers.append(symbol)
                status = False
        if status == False:
            # send email notification 
            print(f'Tickers {invalid_tickers} are invalid.')
        return status
    
    def get_balance(self):
        balance_response = self.client.execute(get_balance_command)
        print(balance_response)

    def get_symbols(self):
        symbols = [ x['symbol'] for x in self.shopping_list]
        return symbols

    def process_ticks(self, msg):
        # print(msg)
        for x in self.shopping_list:
            if x['symbol'] == msg['data']['symbol']:
                x['ask'] = msg['data']['ask']

        print(self.shopping_list)


        # [ x['ask'] = msg['data']['ask'] for x in self.shopping_list if x['symbol'] == msg['data']['symbol'] ]
        

xtb = XtbData()
print(xtb.validate_tickers())
xtb.get_balance()
time.sleep(100)