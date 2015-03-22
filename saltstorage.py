""" Manage the storage and loading of persistent data. 
Player dictionaries, match histories, betting histories, etc.
"""

import os
import pickle
import saltprocessing as sp


def load_persistent_data():
    global player_id_dict, player_name_dict
    global matches

    if os.path.isfile(PLAYERS_FILENAME):
        player_id_dict, player_name_dict = pickle.load(open(PLAYERS_FILENAME, 'rb'))
    else:
        print('File {} not found, starting new player dictionaries'.format(PLAYERS_FILENAME))
        player_id_dict, player_name_dict = {}, {}

    if os.path.isfile(MATCHES_FILENAME):
        matches = pickle.load(open(MATCHES_FILENAME, 'rb'))
    else:
        print('File {} not found, starting new match history'.format(MATCHES_FILENAME))
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


def save_match(state):
    p1_id = get_player_id_by_name(state['p1name'])  # ID for P1
    p2_id = get_player_id_by_name(state['p2name'])  # ID for P2
    winner = int(state['status'])-1                 # Winner - 0/1 for p1/p2
    p1total = int(state['p1total'].replace(',','')) # $ bet on P1
    p2total = int(state['p2total'].replace(',','')) # $ bet on P2
    timestamp = int(time.time())                    # Timestamp (Unix epoch seconds)
    last_match = [p1_id, p2_id, winner, p1total, p2total, timestamp]
    matches.append(last_match)
    print(sp.mode+' match saved: '+str(last_match))



def get_player_id_by_name(pname):
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

