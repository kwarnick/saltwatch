""" Implements all the modeling and prediction. This is needed for intelligent betting.
"""

import sys
import numpy as np
import saltstorage as ss
import saltdoc as sd
from sklearn.cross_validation import train_test_split


def predict_outcomes(ranks, pid1, pid2):
    # 0 means p1 wins, 1 means p2 wins
    if len(pid1)==1:
        return predict_one_outcome(ranks, pid1, pid2)
    else:
        return np.array([predict_one_outcome(ranks, id1, id2) for id1,id2 in zip(pid1,pid2)])


def predict_one_outcome(ranks, pid1, pid2):
    try:
        return 1./(1+np.exp(ranks[pid1]-ranks[pid2]))
    except KeyError:
        return 0.5


def calc_weights(t, tmin, tmax):
    return np.power((1+t-tmin)/(1+tmax-tmin), 2.)
  

def calc_neighborhoods(matches, weights, pid_list):
    neighborhood_ids = []
    neighborhood_weights = []
    for pid in pid_list:
        this_ids = []
        this_weights = []
        for match, weight in zip(matches, weights):
            if match[0]==pid:
                this_ids.append(match[1])
                this_weights.append(weight)
            elif match[1]==pid:
                this_ids.append(match[0])
                this_weights.append(weight)
        if len(this_ids)==0 or len(this_weights)==0:
            print('No neighborhood!', pid)
        neighborhood_ids.append(this_ids)
        neighborhood_weights.append(this_weights)
    return neighborhood_ids, neighborhood_weights
        

def calc_neighborhood_averages(neighborhood_ranks, neighborhood_weights, neighborhood_total_weights):
    do_dot = np.vectorize(np.dot)
    neighborhood_averages = do_dot(neighborhood_ranks, neighborhood_weights) / neighborhood_total_weights
    return neighborhood_averages


def calc_neighborhood_ranks(neighborhood_ids, ranks):
    neighborhood_ranks = []
    for neighborhood in neighborhood_ids:
        neighborhood_ranks.append([ranks[pid] for pid in neighborhood])
    return neighborhood_ranks


def calc_neighborhood_sizes(neighborhood_ids):
    do_len = np.vectorize(len)
    neighborhood_sizes = np.array(do_len(neighborhood_ids), dtype=int)
    return neighborhood_sizes


def calc_neighborhood_total_weights(neighborhood_weights):
    do_sum = np.vectorize(np.sum)
    neighborhood_total_weights = do_sum(neighborhood_weights)
    return neighborhood_total_weights


def train_model(matches, pid_dict, pname_dict, initial_ranks, validation_matches=[], neighbor_regularization=0.3, verbose=True):
    # Per-player attributes
    pid_list, lookup, ranks = prepare_inputs(matches, pid_dict, pname_dict, initial_ranks)
    if verbose:
        print('{:d} players found in {:d} matches'.format(len(pid_list), len(matches)))
    
    # Per-match attributes
    weights = calc_weights(matches[:,5].astype(float), np.min(matches[:,5]), np.max(matches[:,5]))
    neighborhood_ids, neighborhood_weights = calc_neighborhoods(matches, weights, pid_list)
    neighborhood_sizes = calc_neighborhood_sizes(neighborhood_ids)
    neighborhood_total_weights = calc_neighborhood_total_weights(neighborhood_weights)

    if verbose:
        print('Initial scores: ')
        score_performance(ranks, matches, 'training')
        if len(validation_matches):
            score_performance(ranks, validation_matches, 'validation')
        print('')

    MAX_ITER = 50
    for i in range(MAX_ITER):
        print('Iteration {:d}'.format(i))
        neighborhood_ranks = calc_neighborhood_ranks(neighborhood_ids, ranks)
        neighborhood_averages = calc_neighborhood_averages(neighborhood_ranks, neighborhood_weights, neighborhood_total_weights)
        learning_rate = np.power((1+0.1*MAX_ITER)/(i+0.1*MAX_ITER), 0.602)
        indices = np.random.permutation(len(matches))
        
        for weight, match in zip(weights[indices], matches[indices]):
            pred = predict_one_outcome(ranks, match[0], match[1])
            pred_factor = weight*(pred-match[2])*pred*(1-pred)
            ranks[match[0]] += learning_rate *  (pred_factor + neighbor_regularization/neighborhood_sizes[lookup[match[0]]]*(ranks[match[0]]-neighborhood_averages[lookup[match[0]]]))
            ranks[match[1]] += learning_rate * (-pred_factor + neighbor_regularization/neighborhood_sizes[lookup[match[1]]]*(ranks[match[1]]-neighborhood_averages[lookup[match[1]]]))
       
        if verbose:
            score_performance(ranks, matches, 'training')
            if len(validation_matches):
                score_performance(ranks, validation_matches, 'validation')
            print('')

    # Repackage neighborhood sizes for export
    times_seen = {}
    for pid, size in zip(pid_list, neighborhood_sizes):
        times_seen[pid] = size

    return ranks, times_seen


def score_numcorrect(Y_pred, Y):
    not_just_guessing = Y_pred!=0.5
    just_guessing = Y_pred==0.5
    return np.sum((Y_pred[not_just_guessing]>0.5) == Y[not_just_guessing]) + int((len(Y)-np.sum(not_just_guessing))/2.)


def score_avg_error(Y_pred, Y):
    return np.mean(np.abs(Y_pred - Y))


def score_median_error(Y_pred, Y):
    return np.median(np.abs(Y_pred-Y))


def prepare_inputs(matches, pid_dict, pname_dict, initial_ranks): 
    # Get a concise list of the player IDs that appear in the provided matches
    _, concise_names_list = sd.check_dictionary_conciseness(matches, pname_dict, return_concise_names=True, verbose=False)

    # Create new index lookup list for player IDs
    #new_pid_dict, new_pname_dict = sd.build_new_dicts(concise_names_list)
    #new_matches = translate_matches_to_new_dict(matches, ss.player_name_dict, new_pid_dict, verbose=False)
    pid_list = [pid_dict[name] for name in concise_names_list]
    lookup = {pid:i for i,pid in enumerate(pid_list)}
    
    # Merge initial ranks onto default values
    ranks = {pid:1. for pid in pid_list}
    for key in initial_ranks.keys():
        ranks[key] = initial_ranks[key]

    return pid_list, lookup, ranks


def score_performance(ranks, matches, desc_str, verbose=True, return_values=False):
    pred = predict_outcomes(ranks, matches[:,0], matches[:,1])
    numcorrect = score_numcorrect(pred, matches[:,2])
    pct_correct = float(numcorrect)/len(matches)*100
    avg_error = score_avg_error(pred, matches[:,2])
    median_error = score_median_error(pred, matches[:,2])
    if verbose:
        print('{:d}/{:d} = {:.2f}% correct in {}, avg/median gross error {:.3f}/{:.3f}'.format(numcorrect, len(matches), pct_correct, desc_str, avg_error, median_error))
    if return_values:
        return pct_correct, avg_error, median_error


def test_one_model_training(matches, pid_dict, pname_dict, initial_ranks, N_VAL, N_TEST, neighbor_regularization=0.3, random_state=1334):
    train_matches, validation_matches = train_test_split(matches[:-N_TEST], test_size=N_VAL)
    test_matches = matches[-N_TEST:]
    
    new_ranks, times_seen = train_model(train_matches, pid_dict, pname_dict, initial_ranks, validation_matches=validation_matches, neighbor_regularization=neighbor_regularization)

    score_performance(new_ranks, test_matches, 'test')

    return new_ranks, times_seen


if __name__ == "__main__":
    if len(sys.argv)>1:
        neighbor_regularization = float(sys.argv[1])
    else:
        neighbor_regularization = 0.01
    if len(sys.argv)>2:
        N_VAL = int(sys.argv[2])
    else:
        N_VAL = 0
    if len(sys.argv)>3:
        N_TEST = int(sys.argv[3])
    else:
        N_TEST = 0
    if len(sys.argv)>4:
        random_state = int(sys.argv[4])
    else:
        random_state = 1334
    
    ss.load_persistent_data()
    matches = np.array(ss.matches)
    if N_VAL>0 and N_TEST>0:
        # Test a given set of model hyperparameters, separating validation and test sets from the training set
        new_ranks, times_seen = test_one_model_training(matches, ss.player_id_dict, ss.player_name_dict, {}, 200, 200, neighbor_regularization=neighbor_regularization, random_state=random_state)
    elif N_VAL==0 and N_TEST==0:
        # Get final model using the chosen hyperparameters across all available data
        new_ranks, times_seen = train_model(matches, ss.player_id_dict, ss.player_name_dict, {}, [], neighbor_regularization=neighbor_regularization)
        ss.save_model(new_ranks, times_seen)
