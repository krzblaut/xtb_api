from api import xtb
from buy_stocks import BuyStocks
from xAPIConnector import APIClient, APIStreamClient
import time 
from datetime import datetime, timedelta

# stock CFD _4
# stock _9

# Command templates
def baseCommand(commandName, arguments=None):
    if arguments==None:
        arguments = dict()
    return dict([('command', commandName), ('arguments', arguments)])

def loginCommand(userId, password, appName=''):
    return baseCommand('login', dict(userId=userId, password=password, appName=appName))

def latest_price_command(symbol):
    return baseCommand('getSymbol', dict(symbol=symbol))


eurusd_price = 0 

# example function for processing ticks from Streaming socket
def procTick(msg): 
    global eurusd_price 
    print(msg)
    eurusd_price = msg['data']['ask']
    # print("TICK: ", msg)

# example function for processing trades from Streaming socket
def procTradeExample(msg): 
    print("TRADE: ", msg)

# example function for processing trades from Streaming socket
def procBalanceExample(msg): 
    print("BALANCE: ", msg)

# example function for processing trades from Streaming socket
def procTradeStatusExample(msg): 
    print("TRADE STATUS: ", msg)

# example function for processing trades from Streaming socket
def procProfitExample(msg): 
    print("PROFIT: ", msg)

    
def main():

    # enter your login credentials here
    userId = 14457664
    password = "!hvW7r#KxioVLnG8p3uxHebr"

    # create & connect to RR socket
    client = APIClient()
    
    # connect to RR socket, login
    loginResponse = client.execute(loginCommand(userId=userId, password=password))

    # check if user logged in correctly
    if(loginResponse['status'] == False):
        print('Login failed. Error code: {0}'.format(loginResponse['errorCode']))
        return

    latest_price_response = client.execute(latest_price_command('PKN.PL_9'))

    if latest_price_response['status'] == False:
        print('coś się zjebało')
    else:
        print(latest_price_response['returnData']['ask'])


    # get ssId from login response
    ssid = loginResponse['streamSessionId']
    

    sclient = APIStreamClient(ssId=ssid, tickFun=procTick, tradeFun=procTradeExample, profitFun=procProfitExample, tradeStatusFun=procTradeStatusExample)
    

    # subscribe for prices
    sclient.subscribePrices(['EURUSD', 'USDJPY'])

    # subscribe for balance

    sclient.subscribeBalance()
    # subscribe for profits
    # sclient.subscribeProfits()



    # curr_eurusd_price = eurusd_price
    # print(curr_eurusd_price)
    # while True:
        
    #     if curr_eurusd_price != eurusd_price:
    #         curr_eurusd_price = eurusd_price
    #         print('current tick: ',curr_eurusd_price)
    #         print('price from get_symbol: ', latest_price_response['returnData']['ask'])

    time.sleep(100)
    # gracefully close streaming socket
    # sclient.disconnect()
    
    # gracefully close RR socket
    client.disconnect()
    
    
if __name__ == "__main__":
    main()	