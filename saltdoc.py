"""
Functions to help repair / reindex dictionaries and match history files. 
Primarily to remove old/invalid/unwanted characters and clean up the indexing.
"""

import numpy as np


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

        # Translate each match, skipping ones that include an untranslatable name
        for i in range(2):
            name = old_pname_dict[new_match[i]]     # Get player's name
            try:
                new_id = new_pid_dict[name]         # Translate to new ID
            except KeyError:
                print('{} not found in new player name list, match skipped: '.format(name))
                print(match)
                valid_entry = False
                break   
            new_match[i] = new_id

        if valid_entry:
            new_matches.append(new_match)

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


def check_dictionary_conciseness(matches, pname_dict, return_concise_names=False):
    print('Checking if all {:d} player IDs appear in at least one match'.format(len(pname_dict)))

    concise = True
    concise_names_list = []
    for pid in pname_dict.keys():
        num_appearances = np.sum(np.logical_or(np.array(matches)[:][:,0]==pid, np.array(matches)[:][:,1]==pid))
        if num_appearances == 0:
            print('{} does not appear in any match'.format(pname_dict[pid]))
            concise = False
        else:
            concise_names_list.append(pname_dict[pid])

    if return_concise_names:
        return concise, concise_names_list
    else:
        return concise


def do_checkup(matches, pid_dict, pname_dict):
    healthy = True

    # Check that dictionaries are 1-1 mappings (bijections)
    if not check_dictionary_value_uniqueness(pid_dict):
        print('WARNING: Player ID dictionary has duplicate values')
        healthy = False
    if not check_dictionary_value_uniqueness(pname_dict):
        print('WARNING: Player name dictionary has duplicate values')
        healthy = False        
    if not check_dictionary_reversibility(pid_dict, pname_dict):
        print('WARNING: Player ID dictionary is not reversible by player name dictionary')
        healthy = False
    if not check_dictionary_reversibility(pname_dict, pid_dict):
        print('WARNING: Player name dictionary is not reversible by player name dictionary')
        healthy = False
    
    # Check that matches are fully translatable 
    if not check_matches_translatability(matches, pname_dict):
        print('WARNING: Matches are not all translatable.')
        healthy = False

    # Check that dictionary contains no unnecessary entries (all entries appear in at least one match)
    if not check_dictionary_conciseness(matches, pname_dict):
        print('WARNING: Dictionary is not concise.')
        healthy = False

    return healthy  


def combine_dictionaries(pname_dict1, pname_dict2):
    full_name_set = {pname_dict1.keys()} + {pname_dict2.keys()}
    pid_dict, pname_dict = build_new_dicts(full_name_set) 

    return pid_dict, pname_dict


def do_surgery_remove_teams(matches, pid_dict, pname_dict):
    if (do_checkup(matches, pid_dict, pname_dict)):
        print('Health check passed. Proceeding with team removal surgery.\n')
    else:
        print('Health check failed! Aborting.\n')
        return None, None, None
    
    # Find teams in name list and remove them
    new_names = [name for name in pid_dict.keys() if not name[:4]==u'Team']
    num_removed = len(pid_dict.keys())-len(new_names)
    if num_removed == 0:
        print('No teams found! Aborting.')
        return matches, pid_dict, pname_dict
    else:
        print('{:d} teams found and removed:'.format(num_removed))
        print([name for name in pid_dict.keys() if name[:4]==u'Team'])

    
    # Build new dictionaries from new name list
    new_pid_dict, new_pname_dict = build_new_dicts(new_names)

    # Translate matches to new dictionaries
    new_matches = translate_matches_to_new_dict(matches, pname_dict, new_pid_dict)

    # Removing teams means removing matches they played. If a valid player only played against teams, they will
    # be absent from the new match list. If so, reindex the dictionaries and matches.
    concise, concise_name_list = check_dictionary_conciseness(new_matches, new_pname_dict, return_concise_names=True)
    if not concise:
        print('Orphaned names found as result of team match skipping, repairing...')
        concise_pid_dict, concise_pname_dict = build_new_dicts(concise_name_list)
        concise_matches = translate_matches_to_new_dict(new_matches, new_pname_dict, concise_pid_dict)
        # Push final results onto expected variable names
        new_pid_dict = concise_pid_dict
        new_pname_dict = concise_pname_dict
        new_matches = concise_matches
    
    print('')
    if do_checkup(new_matches, new_pid_dict, new_pname_dict):
        print('Health check passed for new matches and dictionaries.\n')
        return new_matches, new_pid_dict, new_pname_dict
    else:
        print('Health check failed for new matches and dictionaries! Aborting.\n')
        return None, None, None



