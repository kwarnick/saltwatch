""" This module provides functions for making and managing bets. 
Relies on saltmind for outcome prediction and bet recommendations. 
"""

import requests
import random
import saltprocessing as sp
import saltstorage as ss
import saltmind as sm
from time import time
import numpy as np

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


def place_saltmind_bet(mode, match):
    # Get prediction value, predicted winner, and current balance
    pred = sm.predict_one_outcome(ss.ranks, match[0], match[1])
    if pred == 0.5:
        player = random.randint(0,1)
    else:
        player = int(round(pred))
    # Get the predicted prob. of chosen player winning. Guaranteed 0.5 >= conf >= 1.0
    conf = abs(pred-0.5)+0.5  
    odds = conf/(1-conf)
    # Decrease odds by past prediction accuracies
    reduced_odds = 1 + (odds-1) * ss.acc[match[player]] * ss.acc[match[1-player]]
    logodds = np.log(reduced_odds)
    print('Final log odds: {:.2f} of possible {:.2f}'.format(logodds, np.log(odds)))

    # Determine wager based on mode, prediction and balance
    if mode == sp.MATCHMAKING:
        balance = get_balance()
        if balance <= 2000:
            wager = balance
        elif logodds > 12:
            wager = int(balance/100.)
        else:
            wager = 100
    elif mode == sp.TOURNAMENT:
        balance = get_tournament_balance()
        if balance <= 2000:
            wager = balance
        else:
            wager = int(balance/2.)
    elif mode == sp.EXHIBITION:
        balance = get_balance()
        wager = 1

    # Place bet with the chosen wager and player
    success = place_bet(player, wager)
    if success:
        ss.add_bet([mode, player, reduced_odds, wager, balance, int(time())])
        return True
    else:
        return False


def display_player_statistics(pid):
    try:
        print('{:4}:  Record:  {:2}/{:2}/{:2} {:3d}%   Rank: {:5.2f}   Acc/TPR/TNR: {:3d}%/{:3d}%/{:3d}%'.format(pid, ss.wins[pid], ss.losses[pid], ss.times_seen[pid], (int(ss.wins[pid]/float(ss.times_seen[pid])*100) if ss.times_seen[pid]>0 else 0), ss.ranks[pid], int(ss.acc[pid]*100), int(ss.tpr[pid]*100), int(ss.tnr[pid]*100)))
    except KeyError:
        print('    :  Record:   0/ 0/ 0    %   Rank:         Acc/TPR/TNR:    %/   %/   %')


def display_outcome_prediction(pid1, pid2):
    try:
        outcome = sm.predict_one_outcome(ss.ranks, pid1, pid2)
        if outcome<0.5:
            print('{} wins with {:.2f}% probability'.format(ss.player_name_dict[pid1], (1-outcome)*100))
        elif outcome>0.5:
            print('{} wins with {:.2f}% probability'.format(ss.player_name_dict[pid2], outcome*100))
        else:
            print('No prediction available.')
    except KeyError:
        print('No prediction available')


def act_on_processed_state(mode, status, match):
    if status == sp.OPEN:
        display_player_statistics(match[0])
        display_player_statistics(match[1])
        display_outcome_prediction(match[0], match[1])
        place_saltmind_bet(mode, match)
