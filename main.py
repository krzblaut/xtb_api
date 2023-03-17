
from xAPIConnector import APIClient, APIStreamClient
import xtb_info
import time 
from datetime import datetime, timedelta

    
def main():
    xapi = xtb_info()
    
    pass



    
if __name__ == "__main__":
    main()	




# def main():

#     # enter your login credentials here
#     userId = 14457664
#     password = "!hvW7r#KxioVLnG8p3uxHebr"

#     # create & connect to RR socket
#     client = APIClient()
    
#     # connect to RR socket, login
#     loginResponse = client.execute(loginCommand(userId=userId, password=password))
#     logger.info(str(loginResponse)) 

#     # check if user logged in correctly
#     if(loginResponse['status'] == False):
#         print('Login failed. Error code: {0}'.format(loginResponse['errorCode']))
#         return

#     # get ssId from login response
#     ssid = loginResponse['streamSessionId']
    
#     # second method of invoking commands
#     # resp = client.commandExecute('getAllSymbols')
    
#     # create & connect to Streaming socket with given ssID
#     # and functions for processing ticks, trades, profit and tradeStatus
#     sclient = APIStreamClient(ssId=ssid, tickFun=procTickExample, tradeFun=procTradeExample, profitFun=procProfitExample, tradeStatusFun=procTradeStatusExample)
    
#     # subscribe for trades
#     # sclient.subscribeTrades()
    
#     # subscribe for prices
#     sclient.subscribePrices(['EURUSD'])

#     # subscribe for balance

#     # sclient.subscribeBalance()
#     # subscribe for profits
#     # sclient.subscribeProfits()

#     # this is an example, make it run for 5 seconds
#     time.sleep(100)
    
#     # gracefully close streaming socket
#     sclient.disconnect()
    
#     # gracefully close RR socket
#     client.disconnect()
    
    
# if __name__ == "__main__":
#     main()	
