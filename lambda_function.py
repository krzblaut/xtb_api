import json
from xtb_api import xtbTrader

def lambda_handler(event, context):
    xtb = xtbTrader()
    xtb.make_trades()
    return {
        'statusCode': 200,
        'body': json.dumps('Excecution successful')
    }
