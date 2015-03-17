import requests
import pickle
import os

STATE_JSON_URL = 'http://www-cdn-twitch.saltybet.com/state.json'
PLAYERS_FILENAME = 'players.p'
MATCHES_FILENAME = 'matches.p'

HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0'
    }
"""
Host: www-cdn-twitch.saltybet.com:8000
User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://www.saltybet.com/
Origin: http://www.saltybet.com
Cookie: __cfduid=d6a0f1d27beecad87f73784ed9130a45b1426561551; _ga=GA1.2.1576583260.1426561550; _gat=1
Connection: keep-alive

"""




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
    s = requests.Session()
    s.headers.update(HEADERS)    
    r = s.get(STATE_JSON_URL)
    state = r.json()

    return state


def process_state(state):
    global matches

    if state['status'] == u'1' or state['status'] == u'2':
        p1_id = get_player_id_by_name(state['p1name'])
        p2_id = get_player_id_by_name(state['p2name'])
        p1total = int(state['p1total'].replace(',',''))
        p2total = int(state['p2total'].replace(',',''))
        winner = int(state['status'])
        last_match = [p1_id, p2_id, winner, p1total, p2total]
        matches.append(last_match)
        print('Match saved: ', last_match) 




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


#def connect_to_

def predict_winner(p1_id, p2_id):
    return oracle.predict(p1_id, p2_id)

# def get_best_bet(prediction) # Do we have the odds? The money bet on each player? Anything?
    

