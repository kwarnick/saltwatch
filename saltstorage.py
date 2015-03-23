""" Manage the storage and loading of persistent data. 
Player dictionaries, match histories, betting histories, etc.
"""

import os
import pickle
import saltprocessing as sp


PLAYERS_FILENAME = 'players.p'
MATCHES_FILENAME = 'matches.p'
player_id_dict, player_name_dict = {}, {}
matches = []

def load_persistent_data():
    global player_id_dict, player_name_dict
    global matches

    if os.path.isfile(PLAYERS_FILENAME):
        player_id_dict, player_name_dict = pickle.load(open(PLAYERS_FILENAME, 'rb'))
        print('{:d} characters loaded'.format(len(player_id_dict)))
    else:
        print('File {} not found, starting new player dictionaries'.format(PLAYERS_FILENAME))
        player_id_dict, player_name_dict = {}, {}

    if os.path.isfile(MATCHES_FILENAME):
        matches = pickle.load(open(MATCHES_FILENAME, 'rb'))
        print('{:d} match results loaded'.format(len(matches)))
    else:
        print('File {} not found, starting new match history'.format(MATCHES_FILENAME))
        matches = []


def save_persistent_data():
    if player_id_dict and player_name_dict:
        pickle.dump([player_id_dict, player_name_dict], open(PLAYERS_FILENAME, 'wb'))
        print('{:d} characters saved'.format(len(player_id_dict)))
    else:
        pickle.dump([{}, {}], open(PLAYERS_FILENAME, 'wb'))

    if matches:
        pickle.dump(matches, open(MATCHES_FILENAME, 'wb'))
        print('{:d} matches saved'.format(len(matches)))
    else:
        pickle.dump([], open(MATCHES_FILENAME, 'wb'))


def save_match(match):
    global matches 
    matches.append(match)


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


def act_on_processed_state(mode, status, match):

    if mode == sp.MATCHMAKING or mode == sp.TOURNAMENT:
        if status == sp.RESULTS:
            save_match(match)
            print(mode+' match saved: '+str(match))
