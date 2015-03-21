"""
Functions to help repair / reindex dictionaries and match history files. 
Primarily to remove old/invalid/unwanted characters and clean up the indexing.
"""

import numpy as np
import saltfetch as sf




def check_dictionary_reversibility(dict1, dict2):
    print('Checking reversibility of dictionaries, lengths {:d}=={:d}'.format(len(dict1), len(dict2)))

    reversible = True
    for key in dict1:
        try:
            if dict2[dict1[key]] != key:
                print('Reversal mismatch. dict1: {} -> {}, dict2: {} -> {}'.format(key, dict1[key], dict1[key], dict2[dict1[key]]))
                reversible = False
        except:
            print('Value {} from dict1 not found in keys for dict2'.format(dict1[key]))
            reversible = False

    return reversible


def check_dictionary_value_uniqueness(pdict):
    values = pdict.values()
    unique_values = np.unique(values)
    
    unique = True
    if len(values) != len(unique_values):
        print('Values uniqueness test failed: {} values reduced to {} unique values'.format(len(values), len(unique_values)))
        unique = False
    
    return unique


def build_new_dicts(names):
    pid_dict = {name:i for i,name in enumerate(names)}
    pname_dict = {i:name for i,name in enumerate(names)}

    print('New dictionaries built for {:d} names'.format(len(names)))

    return pid_dict, pname_dict


def translate_matches_to_new_dict(matches, old_pname_dict, new_pid_dict):
    print('Processing {:d} matches'.format(len(matches)))
    
    new_matches = []
    for match in matches:
        new_match = match
        valid_entry = True

        for i in range(2):
            name = old_pname_dict[new_match[i]]
            try:
                new_id = new_pid_dict[name]
            except KeyError:
                print('{} not found in new player name list, match skipped: '.format(name))
                print(match)
                valid_entry = False
                break   
            new_match[i] = new_id

        if valid_entry:
            new_matches.append[new_match]

    print('{:d} matches translated, {:d} skipped'.format(len(new_matches), len(matches)-len(matches)))

    return new_matches


def check_matches_translatability(matches, pname_dict):
    print('Checking ability to identify all players from {:d} matches'.format(len(matches)))
   
    translatable = True
    for match in matches:
        for pid in match[:2]:
            try:
                pname_dict[pid]
            except KeyError:
                print('ID {:d} not found in dictionary'.format(pid))
                translatable = False

    return translatable


def check_dictionary_conciseness(matches, pname_dict):
    print('Checking if all {:d} player IDs appear in at least one match'.format(len(pname_dict)))

    concise = True
    for pid in pname_dict.keys():
        num_appearances = np.sum(np.logical_or(np.array(matches)[:][:,0]==pid, np.array(matches)[:][:,1]==pid))
        if num_appearances == 0:
            print('\'{}\' does not appear in any match'.format(name))
            concise = False

    return concise


def do_checkup(matches, pid_dict, pname_dict):
    # Check that dictionaries are 1-1 mappings (bijections)
    if not check_dictionary_value_uniqueness(pid_dict):
        print('WARNING: Player ID dictionary has duplicate values')
    if not check_dictionary_value_uniqueness(pname_dict):
        print('WARNING: Player name dictionary has duplicate values')
    if not check_dictionary_reversibility(pid_dict, pname_dict):
        print('WARNING: Player ID dictionary is not reversible by player name dictionary')
    if not check_dictionary_reversibility(pname_dict, pid_dict):
        print('WARNING: Player name dictionary is not reversible by player name dictionary')
    
    # Check that matches are fully translatable 
    if not check_matches_translatability(matches, pname_dict):
        print('WARNING: Matches are not all translatable.')

    # Check that dictionary contains no unnecessary entries (all entries appear in at least one match)
    if not check_dictionary_conciseness(matches, pname_dict):
        print('WARNING: Dictionary is not concise.')


def combine_dictionaries(pname_dict1, pname_dict2):
    full_name_set = {pname_dict1.keys()} + {pname_dict2.keys()}
    pid_dict, pname_dict = build_new_dicts(full_name_set) 

    return pid_dict, pname_dict


if __name__ == "__main__":
    sf.load_persistent_data()
    do_checkup(sf.matches, sf.player_id_dict, sf.player_name_dict)

