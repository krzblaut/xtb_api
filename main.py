from api import xtb
from buy_stocks import BuyStocks
from xAPIConnector import APIClient, APIStreamClient
import time 
from datetime import datetime, timedelta

# stock CFD _4
# stock _9




pkn_current_price = 0 


# example function for processing ticks from Streaming socket
def procTick(msg): 
    global pkn_current_price 
    pkn_current_price = msg['data']['ask']
    print("TICK: ", msg)
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
        pkn_latest_price = latest_price_response['returnData']['ask']


    # get ssId from login response
    ssid = loginResponse['streamSessionId']
    

    sclient = APIStreamClient(ssId=ssid, tickFun=procTick, tradeFun=procTradeExample, profitFun=procProfitExample, tradeStatusFun=procTradeStatusExample)
    

    # subscribe for prices
    sclient.subscribePrices(['PKN.PL_9', 'EURUSD', '11B.PL'])

    # subscribe for balance

    # sclient.subscribeBalance()
    # subscribe for profits
    # sclient.subscribeProfits()


    print("z ostatniego kwotowania: ", pkn_latest_price)


    while True:
        if pkn_latest_price != pkn_current_price:
            pkn_latest_price = pkn_current_price
            print('z ostatniego ticku: ',pkn_latest_price)


    time.sleep(100)
    # gracefully close streaming socket
    # sclient.disconnect()

    # gracefully close RR socket
    client.disconnect()
    
    
if __name__ == "__main__":
    main()	