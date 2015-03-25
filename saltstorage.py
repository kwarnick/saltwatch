""" Manage the storage and loading of persistent data. 
Player dictionaries, match histories, betting histories, etc.
"""

import os
import pickle
import saltprocessing as sp


PLAYERS_FILENAME = 'players.p'
MATCHES_FILENAME = 'matches.p'
RANKS_FILENAME = 'ranks.p'
player_id_dict, player_name_dict = {}, {}
matches = []
ranks = {}
times_seen = {}


def load_persistent_data():
    global player_id_dict, player_name_dict
    global matches
    global ranks, times_seen

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
        print('{:d} match results saved'.format(len(matches)))
    else:
        pickle.dump([], open(MATCHES_FILENAME, 'wb'))


def save_model(new_ranks, new_times_seen):
    global ranks, times_seen
    ranks = new_ranks
    times_seen = new_times_seen
    pickle.dump([ranks, times_seen], open(RANKS_FILENAME, 'wb'))


def load_model():
    global ranks, times_seen
    if os.path.isfile(RANKS_FILENAME):
        ranks, times_seen = pickle.load(open(RANKS_FILENAME, 'rb'))
        print('{:d} ranks loaded'.format(len(ranks)))
    else:
        print('File {} not found'.format(RANKS_FILENAME))
        ranks = {}
        times_seen = {}
    

def save_match(match):
    global matches 
    matches.append(match)


def get_player_id_by_name(pname):
    if pname not in player_id_dict:
        return -1
    return player_id_dict[pname]


def assign_new_player_id(pname):
    global player_id_dict
    global player_name_dict

    if player_id_dict:
        new_id = max(player_id_dict.values())+1
    else:
        new_id = 0
    player_id_dict[pname] = new_id
    player_name_dict[new_id] = pname

    return new_id
    

def act_on_processed_state(mode, status, match):
    if mode == sp.MATCHMAKING or mode == sp.TOURNAMENT:
        if status == sp.RESULTS:
            save_match(match)
            print(mode+' match saved: '+str(match))
