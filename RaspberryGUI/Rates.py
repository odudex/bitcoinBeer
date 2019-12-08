
"""Rates.py: Get BTC prices to different currencies """

__author__      = "Eduardo Schoenknecht"
__credits__ = ["Eduardo Schoenknecht", "Felipe Borges Alves", "Paulo Eduardo Alves"]

import requests

def get_rate_USD():
    r = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json')
    return int(r.json()['bpi']['USD']['rate_float'])

def get_rate_BRL():
    r = requests.get('https://api.bitvalor.com/v1/ticker.json')
    return int(r.json()['ticker_24h']['total']['last'])
