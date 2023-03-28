import json
from xAPIConnector import APIClient, APIStreamClient
import time
import dateutil.tz
from datetime import datetime
import boto3


# template for trades report
html_template = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Trading report</title>
        </head>
    <body>
        <table cellpadding="15" align="center">
            {trades_table}
        </table>
    </body>
    </html>"""


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
        with open('config.json', 'r') as f:
            self.config = json.load(f)
            self.id = self.config['username'] 
            self.password = self.config['password']
            self.shopping_list = self.config['shopping_list']
            self.balance_required = self.config['balance_required']
            self.sender = self.config['from_mail']
            self.receiver = self.config['to_mail']
            
        self.client = APIClient()
        self.login_response = self.login()
        self.ssid = self.login_response['streamSessionId']
        # creating shopping_list dict from config.json file
        self.acc_balance, self.acc_equity, self.acc_currency = self.get_account_info()
        self.ses = boto3.client('ses', region_name='eu-north-1')


    def login(self):
        """
        Attempts to log in using credentials from config.json. If failed sends e-mail notification.
        """
        loginResponse = self.client.execute(
            loginCommand(userId=self.id, password=self.password)
            )
        if loginResponse['status'] == False: 
            self.send_mail("XTB API error", 
                           'Could not login, please check XTB account credentials in config.json file. \n'
                           'Error code: {0}'.format(loginResponse['errorCode']))
        return loginResponse
    
    def get_account_info(self):
        """
        Returns balance, equity and currency of an account 
        """
        balance_response = self.client.execute(get_balance_command())
        account_balance = balance_response['returnData']['balance'] 
        account_equity = balance_response['returnData']['equity'] 
        account_currency = balance_response['returnData']['currency'] 
        return account_balance, account_equity, account_currency
    
    def check_shopping_list_percentage(self):
        """
        Verifies if sum of percentages in shopping_list dict does not exceed 100. If it does sends e-mail notification.
        Returns True or False when percentage sum is greater than 100.
        """
        percentage_sum = 0
        status = True
        for instrument in self.shopping_list:
            if instrument['percentage'] < 0:
                self.send_mail("XTB API error", 'Percentage for each symbol must not be smaller than 0')
                status = False
            percentage_sum += instrument['percentage'] 
        if percentage_sum > 100:
            self.send_mail("XTB API error", 'Sum of percentages for all positions in shopping'
                           'list is greater than 100.')
            status = False
        return status
    
    def check_tickers(self):
        """
        Checks if tickers in shopping_list dict are valid. If at least one ticker is invalid sends
        e-mail notification. Returns True if when all tickers are correct or False when at least one is not.
        """
        invalid_tickers = []
        status = True
        for x in self.shopping_list:
            latest_price_response = self.client.execute(latest_price_command(x['symbol']))
            if latest_price_response['status'] == True:
                x['ask'] = latest_price_response['returnData']['ask']
                x['currency'] = latest_price_response['returnData']['currency']
            elif latest_price_response['status'] == False:
                time.sleep(0.2)
                latest_price_response = self.client.execute(latest_price_command(x['symbol'] + '_9'))
                if latest_price_response['status'] == True:
                    x['symbol'] += '_9'
                    x['ask'] = latest_price_response['returnData']['ask']
                    x['currency'] = latest_price_response['returnData']['currency']
                else:
                    invalid_tickers.append(x['symbol'])
                    status = False
            time.sleep(0.2)
        if status == False: 
            self.send_mail("XTB API error", f'Tickers {invalid_tickers} are invalid. \n')
        return status

    def check_if_market_opened(self):
        """
        Checks if market fo each symbol in shopping_list is opened. Returns True if market for all tickers is opened.
        If market for at least one symbol is closed sends e-mail notification and returns False. 
        """
        self.check_trading_hours()
        ms_time, day = self.get_time()
        status = True
        symbols_closed = []
        for instrument in self.shopping_list:
            if instrument['trading_hours'][0][0] < ms_time < instrument['trading_hours'][0][-1] or \
               instrument['trading_hours'][-1][0] < ms_time < instrument['trading_hours'][-1][-1]:
                pass
            else:
                symbols_closed.append(instrument['symbol'])
                status = False
        if status == False:
            self.send_mail("XTB API error", 
                           f'Unable to proceed with the transaction, market closed for symbols: {symbols_closed}. \
                            Please change execution time so that market is opened for all positions in shopping list')
        return status
                
    def get_time(self):
        """
        Returns current time as milliseconds since midnight and current day of the week as a number from 0 to 6
        """
        cet = dateutil.tz.gettz('Europe/Berlin')
        now = datetime.now(cet)
        midnight = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=cet)
        delta = now - midnight
        milliseconds_since_midnight = int(delta.total_seconds() * 1000)
        week_day = now.weekday() + 1
        return milliseconds_since_midnight, week_day

    def check_trading_hours(self):
        """
        Adds trading hours for each symbol to self.shopping_list dict. Trading hours are described as milliseconds 
        since midnight. 
        """
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

    def process_ticks(self, msg):
        """
        Processes messages containing ticks from XTB API. Updates 'ask' value for corresponding symbol in shopping_list dict.  
        Shopping_list is a global variable thus ask price will always be the latest.
        """
        for x in self.shopping_list:
            if x['symbol'] == msg['data']['symbol']:
                x['ask'] = msg['data']['ask']

    def get_symbols(self):
        """ 
        returns list of symbols in shopping_list
        """
        symbols = [ x['symbol'] for x in self.shopping_list]
        return symbols
    
    def calculate_position_sizes(self):
        """
        Calculates postions size for each symbol regarding its latest price and percentage of balance to be allocated.
        Volume to be bought is assigned to 'volume' value for each symbol in shopping_list dict.
        """
        for x in self.shopping_list:
            if x['currency'] == self.acc_currency:
                x['volume'] = int(((x['percentage']/100)*self.acc_balance)/x['ask'])
            else:
                latest_price_response = self.client.execute(
                    latest_price_command(x['currency']+'PLN'))
                time.sleep(0.2)
                exchange_rate = latest_price_response['returnData']['ask']
                x['volume'] = int(((x['percentage']/100)*self.acc_balance)/(x['ask']*exchange_rate))

    def validate(self):
        """
        Checks if all conditions are fulfilled to start transactions. If any of conditions is False retruns False.
        """
        if self.login_response['status'] == False:
            return False
        elif self.check_tickers() == False:
            return False
        elif self.check_shopping_list_percentage() == False:
            return False
        elif self.check_if_market_opened() == False:
            return False
        elif self.acc_balance < self.balance_required:
            return False
        else:
            return True

    def open_order(self, symbol, price, volume, transaction_type=0, order=0, cmd=0, comment="", expiration=0, sl=0, tp=0):
        """
        Opens order. Returns True and orders number if order was sent successfully.
        """
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

        open_order_response = self.client.execute(
            open_order_command(tradeTransInfo=TRADE_TRANS_INFO))
        if open_order_response['status'] == True:
            return True, open_order_response['returnData']['order']
        else:
            return False, 0

    def check_order(self, order):
        check_order_response = self.client.execute(check_order_command(order))
        status = check_order_response['returnData']['requestStatus']
        return status
    
    def make_trades(self):
        """
        Checks if validate() function returns True, if so initiates APIStreamClient and subscribes to tick 
        prices of symbols from shopping_list dict. Then calculates positions for all symbols. 
        Makes transactions based on symbols, prices and volumes in shopping_list dict provided that volume calculated 
        for symbol is greater than 0. Checks if trades were placed successfully and sends trade report e-mail.
        """
        if self.validate() == True:
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
                    time.sleep(0.5)
                    x['order_number'] = order_number
                    if self.check_order(order_number) == 3:
                        x['trade_status'] = 'success'
                    else:
                        x['trade_status'] = 'failed'
                    time.sleep(0.2)
                else:
                    x['order_placed'] = False
                    x['trade_status'] = 'Not enough funds to buy at least one stock.'
            self.report_trades()
            self.sclient.disconnect()
            self.client.disconnect()
    
    def send_mail(self, subject, msg):
        """
        sends email with specific subject and message
        """
        self.ses.send_email(
            Destination={
                'ToAddresses': [
                    self.receiver,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': 'UTF-8',
                        'Data': msg,
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': subject,
                },
            },
            Source=self.sender,
        )
    
    def report_trades(self):
        """
        creates html table listing details of all trades made. Sends table as e-mail
        """
        trades_table = [['symbol', 'price', 'volume', 'order status']]
        for x in self.shopping_list:
            trades_table.append([x['symbol'], x['ask'], x['volume'], x['trade_status']])
        table_rows = ''
        for row in trades_table:
            table_cells = ''
            for cell in row:
                table_cells += f'<td>{cell}</td>'
            table_rows += f'<tr>{table_cells}</tr>'
        html_output = html_template.format(trades_table=table_rows)
        response = self.ses.send_email(
            Destination={
                'ToAddresses': [
                    self.receiver,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Data': html_output,
                    },
                },
                'Subject': {
                    'Data': "Shopping report",
                },
            },
            Source=self.sender,
        )

