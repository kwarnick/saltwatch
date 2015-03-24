""" This module provides functions for making and managing bets. 
Relies on saltmind for outcome prediction and bet recommendations. 
"""

import requests
import random
import saltprocessing as sp
import saltstorage as ss
import saltmind as sm

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
    # Example bet payload: {'selectedplayer': 'player2', 'wager': 100}
    r = s.post(BET_URL, data={'selectedplayer': 'player'+str(player+1), 'wager': wager})
        
    if len(r.content) > 0:
        print('Bet {:d} on player {:d}'.format(wager, player+1))
        return True
    print('Bet placement failed: {:d} on player {:d}'.format(wager, player+1))
    return False


def get_random_bet(wager=1):
    player = random.randint(0,1)
    return player, wager


def place_random_bet(wager=1):
    player, wager = get_random_bet(wager)
    return place_bet(player, wager)


def place_saltmind_bet(match, wager=1):
    pred = sm.predict_one_outcome(ss.ranks, match[0], match[1])
    if pred==0.5:
        place_random_bet(1)
    else:
        player = round(pred)
        place_bet(player, wager)


def act_on_processed_state(mode, status, match):
    if mode == sp.MATCHMAKING or mode == sp.TOURNAMENT:
        if status == sp.OPEN:
            place_saltmind_bet(match, wager=10)

    #if status == sp.OPEN:
    #    place_random_bet()
