import websocket, json, openpyxl
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

class xtb:

    def __init__(self):
        load_dotenv()
        self.username = os.getenv('XTB_USER_ID')
        self.password = os.getenv('XTB_PASSWORD')
        self.exec_start = self.get_time()
        self.connect()
        self.login()

    def login(self):
        login ={
            "command": "login",
            "arguments": {
                "userId": self.username,
                "password": self.password
            }
        }
        login_json = json.dumps(login)
        result = self.send(login_json)
        result = json.loads(result)
        status = result["status"]
        if str(status)=="True":
            print('logged in.')
            return True
        else:
            print('could not log in.')
            return False
        
    def logout(self):
        logout ={
            "command": "logout"
        }
        logout_json = json.dumps(logout)
        result = self.send(logout_json)
        result = json.loads(result)
        status = result["status"]
        self.disconnect()
        if str(status)=="True":
            return True
        else:
            return False
        
    def connect(self):
        try:
            self.ws=websocket.create_connection("wss://ws.xtb.com/demo")
            print('connected.')
            return True
        except:
            return False

    def disconnect(self):
        try:
            self.ws.close()
            return True
        except:
            return False

    def send(self, msg):
        self.is_on()
        self.ws.send(msg)
        result = self.ws.recv()
        return result+"\n"
    
    def is_on(self):
        temp1 = self.exec_start
        temp2 = self.get_time()
        temp = temp2 - temp1
        temp = temp.total_seconds()
        temp = float(temp)
        if temp>=8.0:
            self.connect()
        self.exec_start = self.get_time()

    def get_time(self):
        time = datetime.today().strftime('%m/%d/%Y %H:%M:%S%f')
        time = datetime.strptime(time, '%m/%d/%Y %H:%M:%S%f')
        return time
    
    def ping(self):
        ping ={
            "command": "ping"
        }
        ping_json = json.dumps(ping)
        result = self.send(ping_json)
        result = json.loads(result)
        return result["status"]
    
    def get_Balance(self):
        balance ={
            "command": "getMarginLevel"
        }
        balance_json = json.dumps(balance)
        result = self.send(balance_json)
        result = json.loads(result)
        balance = result["returnData"]["balance"]
        return balance

    def get_AllSymbols(self):
        allsymbols ={
            "command": "getAllSymbols"
        }
        allsymbols_json = json.dumps(allsymbols)
        result = self.send(allsymbols_json)
        result = json.loads(result)
        return result