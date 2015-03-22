import requests
import pickle
from time import time
import os
import saltstorage as ss

STATE_JSON_URL = 'http://www-cdn-twitch.saltybet.com/state.json'

#HEADERS = {
#        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0'
#    }

HEADERS = {
        'Host': 'www-cdn-twitch.saltybet.com:8000',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': 'http://www.saltybet.com/',
        'Origin': 'http://www.saltybet.com',
        'Connection': 'keep-alive',
}

# Modes
MATCHMAKING = 'M'
EXHIBITION = 'E'
TOURNAMENT = 'T'
UNKNOWN = 'U'
mode = UNKNOWN  

# Statuses
OPEN = 'O'
LOCKED = 'L'
RESULTS = 'R'
status = UNKNOWN # Shamelessly borrowed from the modes


def get_state():
    #s = requests.Session()
    #s.headers.update(HEADERS)    
    #r = s.get(STATE_JSON_URL)
    r = requests.get(STATE_JSON_URL, headers=HEADERS)
    state = r.json()

    return state


def identify_status(state):

    # Determine the status being reported by the current state info
    if state['status'] == u'1' or state['status'] == u'2':
        status = RESULTS
    elif state['status'] == u'open':
        status = OPEN
    elif state['status'] == u'locked':
        status = LOCKED
    else:
        status = UNKNOWN

    return status


def identify_mode(state, status):
    
    # Now using the status and the state info, determine the current game mode
    if status == RESULTS:
        # u'99 more matches until the next tournament!' (not 100 matches)
        # u'Tournament mode will be activated after the next match!'
        # u'16 characters are left in the bracket!' (Last match results have message about the first tournament match)
        if ((u'more matches until the next tournament' in state['remaining'] and state['remaining'][:3] != u'100') or 
          state['remaining'] == u'Tournament mode will be activated after the next match!' or
          state['remaining'] == u'16 characters are left in the bracket!'): 
            mode = MATCHMAKING
        
        # u'15 characters are left in the bracket!' (not 16 characters)
        # u'FINAL ROUND! Stay tuned for exhibitions after the tournament!'
        # u'25 exhibition matches left!' (Last match results have message about the first exhibition match)
        elif ((u'characters are left in the bracket!' in state['remaining'] and state['remaining'][:2] != u'16') or 
          state['remaining'] == u'FINAL ROUND! Stay tuned for exhibitions after the tournament!' or 
          state['remaining'] == u'25 exhibition matches left!'):
            mode = TOURNAMENT
        
        # u'24 exhibition matches left!' (not 25 matches)
        # u'Matchmaking mode will be activated after the next exhibition match!'
        # u'100 more matches until the next tournament!' (Last match results have message about the first matchmaking match)
        elif ((u'exhibition matches left!' in state['remaining'] and state['remaining'][:2] != u'25') or 
          state['remaining'] == u'Matchmaking mode will be activated after the next exhibition match!' or
          state['remainining'] ==  u'100 more matches until the next tournament!'):
            mode = EXHIBITION
        
        else:
            mode = UNKNOWN

    if status == OPEN or status == LOCKED:
        # u'100 more matches until the next tournament!'
        # u'Tournament mode will be activated after the next match!'
        if (u'more matches until the next tournament!' in state['remaining'] or
          state['remaining'] == u'Tournament mode will be activated after the next match!'):
            mode = MATCHMAKING

        # u'16 characters are left in the bracket!'
        # u'FINAL ROUND! Stay tuned for exhibitions after the tournament!'
        elif (u'characters left in the bracket!' in state['remaining'] or
          state['remaining'] == u'FINAL ROUND! Stay tuned for exhibitions after the tournament!'):
            mode = TOURNAMENT

        # u'25 exhibition matches left!'
        # u'Matchmaking mode will be activated after the next exhibition match!'
        elif (u'exhibition matches left!' in state['remaining'] or
          state['remaining'] == u'Matchmaking mode will be activated after the next exhibition match!'):
            mode = EXHIBITION

        else:
            mode = UNKNOWN

    if status == UNKNOWN:
        mode = UNKNOWN

    # Specially log any states that do not get categorized
    if mode == UNKNOWN or status == UNKNOWN:
        with open('help_me_id_this.txt', 'a') as myfile:
            myfile.write(mode+' '+status+' '+str(state)+'\n')

    # Log all win states for verification/debugging purposes
    if status == RESULTS:
        with open('win_state_log.txt', 'a') as myfile:
            myfile.write(mode+' '+status+' '+str(state)+'\n')

    # Log all captured states for verification/debugging purposes
    with open('full_state_log.txt', 'a') as myfile:
        myfile.write(mode+' '+status+' '+str(state)+'\n')

    return mode


def process_state(state):
    status = identify_status(state)
    mode = identify_mode(state, status)
    
    p1_id = ss.get_player_id_by_name(state['p1name'])  # ID for P1
    p2_id = ss.get_player_id_by_name(state['p2name'])  # ID for P2
    if status == RESULTS:
        winner = int(state['status'])-1         # Winner - 0/1 for p1/p2
    else:                                       
        winner = -1                             # Winner undefined        
    p1total = int(state['p1total'].replace(',','')) # $ bet on P1
    p2total = int(state['p2total'].replace(',','')) # $ bet on P2
    timestamp = int(time())                    # Timestamp (Unix epoch seconds)
    match = [p1_id, p2_id, winner, p1total, p2total, timestamp]

    return mode, status, match







