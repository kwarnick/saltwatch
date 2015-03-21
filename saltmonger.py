""" This module provides functions for making and managing bets. 
Relies on saltmind for outcome prediction and bet recommendations. 
"""

import requests

LOGIN_URL = 'http://www.saltybet.com/authenticate?signin=1'
LOGIN_PAYLOAD = {'email': 'giant_snark@myway.com',
                 'pword': 'onDP@RMWs^%4',
                 'authenticate': 'signin',
                 }
BALANCE_URL = 'http://www.saltybet.com/ajax_tournament_end.php'
TOURNAMENT_BALANCE_URL = 'http://www.saltybet.com/ajax_tournament_start.php'
BET_URL = 'http://www.saltybet.com/ajax_place_bet.php'

HEADERS = {'Host': 'www.saltybet.com',
           'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Language': 'en-US,en;q=0.5',
           'Accept-Encoding': 'gzip, deflate',
           'Referer': 'http://www.saltybet.com/authenticate?signin=1',
           'Connection': 'keep-alive',
           'Content-Type': 'application/x-www-form-urlencoded',
           'Cookie': 'Cookie    __cfduid=d6a0f1d27beecad87f73784ed9130a45b1426561551; _ga=GA1.2.1576583260.1426561550; PHPSESSID=5u3a54tkltusd3d5mm4r281dc3; _gat=1',
           }


s = requests.Session()

def login(): 
    global s
    s.post(LOGIN_URL, data=LOGIN_PAYLOAD)


def get_balance():
    balance = int(s.get(BALANCE_URL).content)
    return balance


def get_tournament_balance():
    balance = int(s.get(TOURNAMENT_BALANCE_URL).content)
    return balance


def place_bet(player, wager):
    # Example bet payload: {'selectedplayer': 'player1', 'wager': 100}
    r = s.post(BET_URL, data={'selectedplayer': 'player'+str(player+1), 'wager': wager})
        
    if r.content=='1':
        return True
    return False
