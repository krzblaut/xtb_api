import json
from xAPIConnector import APIClient, APIStreamClient


class GetInfo:

    def __init__(self):
        self.config = json.load(open('config.json'))
        self.client = APIClient()
        self.api = xtb(self.config['username'], self.config['password'])