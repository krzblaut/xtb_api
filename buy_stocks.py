from api import xtb
import os
import json


# stock CFD _4
# stock _9


class BuyStocks:

    def __init__(self):
        
        self.config = json.load(open('config.json'))
        self.api = xtb(self.config['username'], self.config['password'])

    def config_validation(self):
        msg = 'config file valid.'
        login_status, login_msg = self.check_connection()
        shopping_list_status, shopping_list_msg = self.validate_shopping_list()
        if login_status == False:
            return False, login_msg
        if shopping_list_status == False:
            return False, shopping_list_msg
        else:
            return True, msg

    def validate_shopping_list(self):
        msg = 'shopping list valid'
        percentage_sum = 0
        priority_list = []
        for instrument in self.config['shopping_list']:
            percentage_sum += instrument['percentage'] 
            priority_list.append(instrument['priority'])
        if percentage_sum != 100:
            msg = 'Percentage sum is not equal to 100.'
            return False, msg 
        if len(set(priority_list)) != len(priority_list):
            msg = 'Each instrument must have unique priority integer.'
            return False, msg
        else:
            return True, msg
    
    def check_connection(self):
        msg = 'login success'
        if self.api.login_status == False:
            msg = 'Could not log in, check credentials.'
            return False, msg
        return True, msg
    
    def calculate_positions(self):
        pass


    
# bs = BuyStocks()
# print(bs.check_connection())

