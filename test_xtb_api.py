import unittest
from unittest.mock import Mock, patch, call
from datetime import datetime, timezone
from xtb_api import xtbTrader, latest_price_command, trading_hours_command, get_balance_command, open_order_command
import os
from freezegun import freeze_time


class TestXtbTrader(unittest.TestCase):

    def setUp(self):
        self.xtb_trader = xtbTrader()
        self.xtb_trader.send_mail = Mock()

    def test_login(self):
        self.assertTrue(self.xtb_trader.login_response['status'])

    def test_latest_price_command(self):
        response = self.xtb_trader.client.execute(latest_price_command('AAPL.US_9'))
        self.assertTrue(response['status'])

    def test_get_trading_hours_command(self):
        response = self.xtb_trader.client.execute(trading_hours_command(['AAPL.US_9']))
        self.assertTrue(response['status'])

    def test_get_balance_command(self):
        response = self.xtb_trader.client.execute(get_balance_command())
        self.assertTrue(response['status'])

    def test_open_order_command(self):
        TRADE_TRANS_INFO = {
            "cmd": 0,
            "customComment": '',
            "expiration": 0,
            "offset": -1,
            "order": 0,
            "price": 200,
            "sl": 0,
            "symbol": 'AAPL.US_9',
            "tp": 0,
            "type": 0,
            "volume": 0.1
        }
        response = self.xtb_trader.client.execute(open_order_command(tradeTransInfo=TRADE_TRANS_INFO))
        self.assertTrue(response['status'])

    def test_get_account_info_return(self):
        self.assertEquals(type(self.xtb_trader.acc_balance), float)
        self.assertEquals(type(self.xtb_trader.acc_currency), str)
        self.assertEquals(type(self.xtb_trader.acc_equity), float)

    def test_check_shopping_list_percentage_over_100(self):
        self.xtb_trader.shopping_list = [
            {'symbol': 'AAPL.US', 'percentage': 60},
            {'symbol': 'GOOGL.US', 'percentage': 50}
        ]
        self.assertFalse(self.xtb_trader.check_shopping_list_percentage())
        self.xtb_trader.send_mail.assert_called_once_with("XTB API error", 
                                                          'Sum of percentages for all positions in shopping'
                                                          'list is greater than 100.')

    def test_check_shopping_list_negative_percentage(self):
        self.xtb_trader.shopping_list = [
            {'symbol': 'AAPL.US', 'percentage': 60},
            {'symbol': 'GOOGL.US', 'percentage': -50}
        ]
        self.assertFalse(self.xtb_trader.check_shopping_list_percentage())
        self.xtb_trader.send_mail.assert_called_once_with("XTB API error", 
                                                          'Percentage for each symbol must not be smaller than 0')
    
    def test_check_tickers_invalid_tickers(self):
        self.xtb_trader.shopping_list = [
            {'symbol': 'INVALID', 'percentage': 50},
            {'symbol': 'AAPL.US_9', 'percentage': 50}
        ]
        result = self.xtb_trader.check_tickers()
        self.xtb_trader.send_mail.assert_called_once_with("XTB API error",
                                                          "Tickers ['INVALID'] are invalid. \n")
        self.assertFalse(result)

    def test_check_tickers_valid_tickers(self):
        self.xtb_trader.shopping_list = [
            {'symbol': 'AAPL.US_9', 'percentage': 50},
            {'symbol': 'GOOGL.US_9', 'percentage': 50}
        ]
        result = self.xtb_trader.check_tickers()
        self.assertTrue(result)

    def test_check_tickers_adds_9(self):
        self.xtb_trader.shopping_list = [
            {'symbol': 'AAPL.US', 'percentage': 50},
            {'symbol': 'GOOGL.US_9', 'percentage': 50}
        ]
        expected_shopping_list_outcome = [
            {'symbol': 'AAPL.US_9', 'percentage': 50},
            {'symbol': 'GOOGL.US_9', 'percentage': 50}
        ]
        result = self.xtb_trader.check_tickers()
        self.assertTrue(result)
        self.assertEqual(self.xtb_trader.shopping_list[0]['symbol'], 
                         expected_shopping_list_outcome[0]['symbol'])

    @freeze_time("2023-03-30 12:30:00", tz_offset=-2)
    def test_get_time(self):
        result = self.xtb_trader.get_time()
        self.assertEquals(len(result), 2)
        self.assertEquals(type(result[0]), int)
        self.assertEquals(type(result[1]), int)
        self.assertEquals(result[0], 45000000)
        self.assertEquals(result[1], 4)

    def test_check_trading_hours_open(self):
        self.xtb_trader.shopping_list = [
            {'symbol': 'AAPL.US_9', 'percentage': 50}
        ]
        response = {'status': True, 
                    'returnData': 
                        [{'symbol': 'AAPL.US_9', 
                          'trading': 
                                [
                                {'day': 1, 'fromT': 57600000, 'toT': 86400000},
                                {'day': 2, 'fromT': 57600000, 'toT': 86400000},
                                {'day': 3, 'fromT': 57600000, 'toT': 86400000},
                                {'day': 4, 'fromT': 57600000, 'toT': 86400000},
                                {'day': 5, 'fromT': 57600000, 'toT': 86400000},
                                {'day': 6, 'fromT': 57600000, 'toT': 86400000},
                                {'day': 7, 'fromT': 57600000, 'toT': 86400000}
                                ]
                        }]
                    }
        self.xtb_trader.client.execute = Mock(return_value=response)
        expected_shopping_list_outcome = [
            {'symbol': 'AAPL.US_9', 'percentage': 50, 'trading_hours': [(57600000,86400000)]}
        ]
        self.xtb_trader.check_trading_hours()
        self.assertEqual(self.xtb_trader.shopping_list[0]['trading_hours'], 
                         expected_shopping_list_outcome[0]['trading_hours'])
        self.assertEqual(self.xtb_trader.shopping_list[-1]['trading_hours'], 
                         expected_shopping_list_outcome[-1]['trading_hours'])
        
    def test_check_trading_hours_holiday(self):
        self.xtb_trader.shopping_list = [
            {'symbol': 'AAPL.US_9', 'percentage': 50},
            {'symbol': 'GOOGL.US_9', 'percentage': 50}
        ]
        response = 70000000, 7
        self.xtb_trader.get_time = Mock(return_value=response)
        self.xtb_trader.check_trading_hours()
        expected_shopping_list_outcome = [
            {'symbol': 'AAPL.US_9', 'percentage': 50, 'trading_hours': [(0,0)]},
            {'symbol': 'GOOGL.US_9', 'percentage': 50, 'trading_hours': [(0,0)]}
        ]
        self.assertEqual(self.xtb_trader.shopping_list[0]['trading_hours'], 
                         expected_shopping_list_outcome[0]['trading_hours'])

    def test_check_if_market_opened_holiday(self):
        self.xtb_trader.shopping_list = [
            {'symbol': 'AAPL.US_9', 'percentage': 50}
        ]
        response = 70000000, 7
        self.xtb_trader.get_time = Mock(return_value=response)
        response = self.xtb_trader.check_if_market_opened()
        self.xtb_trader.send_mail.assert_called_once_with("XTB API error", 
                           f"Unable to proceed with the transaction, market closed for symbols: ['AAPL.US_9']. \
                            Please change execution time so that market is opened for all positions in shopping list")
        self.assertFalse(response)

    def test_calculate_position_sizes(self):
        self.xtb_trader.acc_currency = 'PLN'
        self.xtb_trader.acc_balance = 10000
        self.xtb_trader.shopping_list = [
            {'symbol': 'AAPL.US_9', 'percentage': 50, 'ask': 69, 'currency': 'USD'},
            {'symbol': 'PKN.PL_9', 'percentage': 50, 'ask': 420, 'currency': 'PLN'}
        ]
        response = {
	                "status": True,
	                "returnData": {'ask': 4.20}	
                }
        self.xtb_trader.client.execute = Mock(return_value=response)
        self.xtb_trader.calculate_position_sizes()
        self.assertEqual(self.xtb_trader.shopping_list[0]['volume'], 17)
        self.assertEqual(self.xtb_trader.shopping_list[1]['volume'], 11)

if __name__ == '__main__':
    unittest.main()