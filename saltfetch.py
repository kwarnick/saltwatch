import requests
import pickle
import time
import os

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



def load_persistent_data():
    global player_id_dict, player_name_dict
    global matches

    if os.path.isfile(PLAYERS_FILENAME):
        player_id_dict, player_name_dict = pickle.load(open(PLAYERS_FILENAME, 'rb'))
    else:
        player_id_dict, player_name_dict = {}, {}

    if os.path.isfile(MATCHES_FILENAME):
        matches = pickle.load(open(MATCHES_FILENAME, 'rb'))
    else:
        matches = []


def save_persistent_data():
    if player_id_dict and player_name_dict:
        pickle.dump([player_id_dict, player_name_dict], open(PLAYERS_FILENAME, 'wb'))
    else:
        pickle.dump([{}, {}], open(PLAYERS_FILENAME, 'wb'))

    if matches:
        pickle.dump(matches, open(MATCHES_FILENAME, 'wb'))
    else:
        pickle.dump([], open(MATCHES_FILENAME, 'wb'))


def get_state():
    #s = requests.Session()
    #s.headers.update(HEADERS)    
    #r = s.get(STATE_JSON_URL)
    r = requests.get(STATE_JSON_URL, headers=HEADERS)
    state = r.json()

    return state


def process_state(state):
    global matches, mode
    
    ## Consider also using alerts to track changes in game mode, rather than just identifying mode by the 'remaining' message.
    # Check for notification of a winner in the status
    if state['status'] == u'1' or state['status'] == u'2':
    
        ## Detect game mode from the 'remaining' message, which was written before the match whose results we are collecting ##

        # Detect 'remaining' messages indicating matchmaking matches:
        # u'99 more matches until the next tournament!' (not 100 matches)
        # u'Tournament mode will be activated after the next match!'
        if ((u'tournament' in state['remaining'] or u'Tournament' in state['remaining']) and state['remaining'] != u'100 more matches until the next tournament!') or state['remaining' == u'16 characters are left in the bracket!':
            mode = MATCHMAKING
            save_match(state)
        
        # Detect 'remaining' messages indicating tournament matches:
        # u'15 characters are left in the bracket!' (not 16 characters)
        # u'FINAL ROUND! Stay tuned for exhibitions after the tournament!'
        elif ((u'bracket' in state['remaining'] or u'FINAL' in state['remaining']) and state['remaining'] != u'16 characters are left in the bracket!') or state['remaining'] == u'25 exhibition matches left!':
            mode = TOURNAMENT
            save_match(state)
        
        # Detect 'remaining' message indicating exhibition matches:
        # u'24 exhibition matches left!' (not 25 matches)
        # u'Matchmaking mode will be activated after the next exhibition match!'
        # u'100 more matches until the next tournament!'
        # (Don't count these - can't handle custom teams. Need OCR/CV to identify what players are on each team.)    
        elif ((u'exhibition match' in state['remaining'] or state['remaining'] == u'100 more matches until the next tournament!') and state['remaining'] != u'25 exhibition matches left!') or state['remaining'] == u'100 more matches until the next tournament!':
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


def save_match(state):
    global mode

    p1_id = get_player_id_by_name(state['p1name'])  # ID for P1
    p2_id = get_player_id_by_name(state['p2name'])  # ID for P2
    winner = int(state['status'])-1                 # Winner - 0/1 for p1/p2
    p1total = int(state['p1total'].replace(',','')) # $ bet on P1
    p2total = int(state['p2total'].replace(',','')) # $ bet on P2
    timestamp = int(time.time())                    # Timestamp (Unix epoch seconds)
    last_match = [p1_id, p2_id, winner, p1total, p2total, timestamp]
    matches.append(last_match)
    print(mode+' match saved: '+str(last_match)) 



def get_player_id_by_name( pname ):
    global player_name_dict
    global player_id_dict

    # Keep dictionaries updated if name is new
    if pname not in player_id_dict:
        if player_id_dict:
            new_id = max(player_id_dict.values())+1
            player_id_dict[pname] = new_id
            player_name_dict[new_id] = pname
        else:
            player_id_dict[pname] = 0
            player_name_dict[0] = pname

    return player_id_dict[pname]
