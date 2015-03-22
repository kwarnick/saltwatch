import requests
import pickle
import time
import os
import saltstorage as ss

STATE_JSON_URL = 'http://www-cdn-twitch.saltybet.com/state.json'
PLAYERS_FILENAME = 'players.p'
MATCHES_FILENAME = 'matches.p'

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
UNKNOWN = 'U'
status = UNKNOWN


def get_state():
    #s = requests.Session()
    #s.headers.update(HEADERS)    
    #r = s.get(STATE_JSON_URL)
    r = requests.get(STATE_JSON_URL, headers=HEADERS)
    state = r.json()

    return state


def process_state(state):
    global mode, status
    
    ## Consider also using alerts to track changes in game mode, rather than just identifying mode by the 'remaining' message.
    # Check for notification of a winner in the status
    if state['status'] == u'1' or state['status'] == u'2':
        status = RESULTS
    
        ## Detect game mode from the 'remaining' message, which was written before the match whose results we are collecting ##

        # Detect 'remaining' messages indicating matchmaking matches:
        # u'99 more matches until the next tournament!' (not 100 matches)
        # u'Tournament mode will be activated after the next match!'
        # u'16 characters are left in the bracket!' (Last match results have message about the first tournament match)
        if ((u'more matches until the next tournament' in state['remaining'] and state['remaining'][:3] != u'100') or 
          state['remaining'] == u'Tournament mode will be activated after the next match!' or
          state['remaining'] == u'16 characters are left in the bracket!'): 
            mode = MATCHMAKING
            #save_match(state)
        
        # Detect 'remaining' messages indicating tournament matches:
        # u'15 characters are left in the bracket!' (not 16 characters)
        # u'FINAL ROUND! Stay tuned for exhibitions after the tournament!'
        # u'25 exhibition matches left!' (Last match results have message about the first exhibition match)
        elif ((u'characters are left in the bracket!' in state['remaining'] and state['remaining'][:2] != u'16') or 
          state['remaining'] == u'FINAL ROUND! Stay tuned for exhibitions after the tournament!' or 
          state['remaining'] == u'25 exhibition matches left!'):
            mode = TOURNAMENT
            #save_match(state)
        
        # Detect 'remaining' message indicating exhibition matches:
        # u'24 exhibition matches left!' (not 25 matches)
        # u'Matchmaking mode will be activated after the next exhibition match!'
        # u'100 more matches until the next tournament!' (Last match results have message about the first matchmaking match)
        # (Don't count these - can't handle custom teams. Need OCR/CV to identify what players are on each team.)
        # (Also, exhibition matches are often rigged / played with in some strange way. They aren't typical setups.)
        elif ((u'exhibition matches left!' in state['remaining'] and state['remaining'][:2] != u'25') or 
          state['remaining'] == u'Matchmaking mode will be activated after the next exhibition match!' or
          state['remainining'] ==  u'100 more matches until the next tournament!'):
            mode = EXHIBITION
        
        # Nothing should reach this state. If something does, fix it!
        else:
            mode = UNKNOWN
            print('Mode not recognized!')
            with open('help_me_id_this.txt', 'a') as myfile:
                myfile.write(str(state)+'\n')


        # Log all win states for debugging purposes
        with open('win_state_log.txt', 'a') as myfile:
            myfile.write(mode+' '+str(state)+'\n')

