""" Manage the storage and loading of persistent data. 
Player dictionaries, match histories, betting histories, etc.
"""

import os
import pickle
import saltprocessing as sp

# If Python 2.x, change default string encoding to utf-8
import sys
if sys.version_info[0]==2:
    reload(sys)
    sys.setdefaultencoding('utf-8')


MATCHES_FILENAME = 'matches.p'
matches = []

PLAYERS_FILENAME = 'players.p'
player_id_dict, player_name_dict = {}, {}

RANKS_FILENAME = 'ranks.p'
ranks = {}
wins = {}
losses = {}
times_seen = {}
acc = {}
tpr = {}
tnr = {}

BETS_FILENAME = 'bets.p'
bets = []


def load_persistent_data():
    load_dictionaries()
    load_matches()
    load_bets()


def save_persistent_data():
    save_dictionaries()
    save_matches()
    save_bets()


def save_dictionaries():
    pickle.dump([player_id_dict, player_name_dict], open(PLAYERS_FILENAME, 'wb'))
    print('{:d} characters saved'.format(len(player_id_dict)))


def load_dictionaries():
    global player_id_dict, player_name_dict
    if os.path.isfile(PLAYERS_FILENAME):
        player_id_dict, player_name_dict = pickle.load(open(PLAYERS_FILENAME, 'rb'))
        print('{:d} characters loaded'.format(len(player_id_dict)))
    else:
        print('File {} not found, starting new player dictionaries'.format(PLAYERS_FILENAME))
        player_id_dict, player_name_dict = {}, {}


def save_matches():
    pickle.dump(matches, open(MATCHES_FILENAME, 'wb'))
    print('{:d} match results saved'.format(len(matches)))

    
def load_matches():
    global matches
    if os.path.isfile(MATCHES_FILENAME):
        matches = pickle.load(open(MATCHES_FILENAME, 'rb'))
        print('{:d} match results loaded'.format(len(matches)))
    else:
        print('File {} not found, starting new match history'.format(MATCHES_FILENAME))
        matches = []


def save_player_stats():
    pickle.dump([ranks, wins, losses, times_seen, acc, tpr, tnr], open(RANKS_FILENAME, 'wb'))
    if not (len(ranks) == len(wins) == len(losses) == len(times_seen) == len(acc) == len(tpr) == len(tnr)):
        print('Stat list length mismatch!', len(ranks), len(wins), len(losses), len(times_seen), len(acc), len(tpr), len(tnr))
    print('{:d} players\' stats saved'.format(len(ranks)))


def load_player_stats():
    global ranks, wins, losses, times_seen, acc, tpr, tnr
    if os.path.isfile(RANKS_FILENAME):
        ranks, wins, losses, times_seen, acc, tpr, tnr = pickle.load(open(RANKS_FILENAME, 'rb'))
        if not (len(ranks) == len(wins) == len(losses) == len(times_seen) == len(acc) == len(tpr) == len(tnr)):
            print('Stat list length mismatch!', len(ranks), len(wins), len(losses), len(times_seen), len(acc), len(tpr), len(tnr))
        print('{:d} players\' stats loaded'.format(len(ranks)))
    else:
        print('File {} not found'.format(RANKS_FILENAME))
        ranks, wins, losses, times_seen, acc, tpr, tnr = {}, {}, {}, {}, {}, {}, {}


def save_bets():
    pickle.dump(bets, open(BETS_FILENAME, 'wb'))
    print('{:d} past bets saved'.format(len(bets)))


def load_bets():
    global bets
    if os.path.isfile(BETS_FILENAME):
        bets = pickle.load(open(BETS_FILENAME, 'rb'))
        print('{:d} past bets loaded'.format(len(bets)))
    else:
        print('File {} not found, starting new bet history'.format(BETS_FILENAME))
        bets = []


def add_match(match):
    global matches 
    matches.append(match)


def add_bet(bet):
    global bets
    bets.append(bet)
 

def replace_player_stats(new_ranks, new_wins, new_losses, new_times_seen, new_acc, new_tpr, new_tnr):
    global ranks, wins, losses, times_seen, acc, tpr, tnr
    ranks = new_ranks
    wins = new_wins
    losses = new_losses
    times_seen = new_times_seen
    acc = new_acc
    tpr = new_tpr
    tnr = new_tnr


def get_player_id_by_name(pname):
    try:
        return player_id_dict[pname]
    except KeyError:
        return -1


def assign_new_player_id(pname):
    global player_id_dict
    global player_name_dict

    if player_id_dict:
        new_id = max(player_id_dict.values())+1
    else:
        new_id = 0
    player_id_dict[pname] = new_id
    player_name_dict[new_id] = pname
    print('{} assigned to ID {:d}'.format(pname, new_id))

    return new_id
    

def act_on_processed_state(mode, status, match):
    if mode == sp.MATCHMAKING or mode == sp.TOURNAMENT:
        if status == sp.RESULTS:
            add_match(match)
            print(mode+' match saved: '+str(match))
