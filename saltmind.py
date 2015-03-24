""" Implements all the modeling and prediction. This is needed for intelligent betting.
"""

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
        

def calc_neighborhood_averages_and_sizes(neighborhood_ids, neighborhood_weights, ranks):
    neighborhood_ranks = []
    for neighborhood in neighborhood_ids:
        neighborhood_ranks.append([ranks[pid] for pid in neighborhood])
    
    for neighborhood in neighborhood_weights:
        if np.sum(neighborhood)==0:
            print(neighborhood)
    do_sum = np.vectorize(np.sum)
    neighborhood_total_weights = do_sum(neighborhood_weights)
    #print('neighborhood total weights', np.max(neighborhood_total_weights), np.min(neighborhood_total_weights))

    do_dot = np.vectorize(np.dot)
    neighborhood_averages = do_dot(neighborhood_ranks, neighborhood_weights) / neighborhood_total_weights
    #print('neighborhood average ranks', np.max(neighborhood_averages), np.min(neighborhood_averages))
    
    do_len = np.vectorize(len)
    neighborhood_sizes = np.array(do_len(neighborhood_ranks), dtype=int)

    return neighborhood_averages, neighborhood_sizes


def train_model(matches, validation_matches, pid_dict, pname_dict, initial_ranks, neighbor_regularization=0.77):
    # Per-match attributes
    weights = calc_weights(matches[:,5].astype(float), np.min(matches[:,5]), np.max(matches[:,5]))
    print('{} weights from {} matches spanning {} - {}'.format(len(weights), len(matches[:,5]), min(weights), max(weights)))
    
    # Per-player attributes
    pid_list, lookup, ranks = prepare_inputs(matches, pid_dict, pname_dict, initial_ranks)
    print('{:d} players found in matches'.format(len(pid_list)))
    print('Player IDs span {:d} - {:d}'.format(min(pid_list), max(pid_list)))
    
    neighborhood_ids, neighborhood_weights = calc_neighborhoods(matches, weights, pid_list)
    print('{:d} neighborhood listings and {:d} neighborhood weights calculated'.format(len(neighborhood_ids), len(neighborhood_weights)))
   
    print('Initial scores: ')
    pred = predict_outcomes(ranks, matches[:,0], matches[:,1])
    pred = np.array([0.5]*len(matches))
    numcorrect = score_numcorrect(pred, matches[:,2])
    avg_error = score_avg_error(pred, matches[:,2])
    print('{:d}/{:d} = {:.2f}% correct in-sample, average gross error {:.2f}'.format(numcorrect, len(matches), float(numcorrect)/len(matches)*100, avg_error))
    v_pred = predict_outcomes(ranks, validation_matches[:,0], validation_matches[:,1])
    v_numcorrect = score_numcorrect(v_pred, validation_matches[:,2])
    v_avg_error = score_avg_error(v_pred, validation_matches[:,2])
    print('{:d}/{:d} = {:.2f}% correct out-of-sample, average gross error {:.2f}'.format(v_numcorrect, len(validation_matches), float(v_numcorrect)/len(validation_matches)*100, v_avg_error))

    MAX_ITER = 50
    for i in range(MAX_ITER):
        print('Iteration {:d}'.format(i))
        neighborhood_averages, neighborhood_sizes = calc_neighborhood_averages_and_sizes(neighborhood_ids, neighborhood_weights, ranks)
        learning_rate = np.power((1+0.1*MAX_ITER)/(i+0.1*MAX_ITER), 0.602)
        #learning_rate = 1.
        # Randomize the order in which the matches will be processed this iteration
        indices = np.random.permutation(len(matches))
        for weight, match in zip(weights[indices], matches[indices]):
            pred = predict_one_outcome(ranks, match[0], match[1])
            # Update ranks
            pred_factor = weight*(pred-match[2])*pred*(1-pred)
            ranks[match[0]] += learning_rate *  (pred_factor + neighbor_regularization/neighborhood_sizes[lookup[match[0]]]*(ranks[match[0]]-neighborhood_averages[lookup[match[0]]]))
            ranks[match[1]] += learning_rate * (-pred_factor + neighbor_regularization/neighborhood_sizes[lookup[match[1]]]*(ranks[match[1]]-neighborhood_averages[lookup[match[1]]]))

        pred = predict_outcomes(ranks, matches[:,0], matches[:,1])
        numcorrect = score_numcorrect(pred, matches[:,2])
        avg_error = score_avg_error(pred, matches[:,2])
        median_error = score_median_error(pred, matches[:,2])
        print('{:d}/{:d} = {:.2f}% correct in-sample, avg/median gross error {:.3f}/{:.3f}'.format(numcorrect, len(matches), float(numcorrect)/len(matches)*100, avg_error, median_error))
        v_pred = predict_outcomes(ranks, validation_matches[:,0], validation_matches[:,1])
        v_numcorrect = score_numcorrect(v_pred, validation_matches[:,2])
        v_avg_error = score_avg_error(v_pred, validation_matches[:,2])
        v_median_error = score_median_error(v_pred, validation_matches[:,2])
        print('{:d}/{:d} = {:.2f}% correct out-of-sample, avg/median gross error {:.3f}/{:3f}'.format(v_numcorrect, len(validation_matches), float(v_numcorrect)/len(validation_matches)*100, v_avg_error, v_median_error))
    return ranks


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
    _, concise_names_list = sd.check_dictionary_conciseness(train_matches, pname_dict, return_concise_names=True, verbose=False)

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


if __name__ == "__main__":
    ss.load_persistent_data()
    matches = np.array(ss.matches)
    NUM_TEST_MATCHES = 200
    NUM_VALIDATION_MATCHES = 200
    train_matches, validation_matches = train_test_split(matches[:-NUM_TEST_MATCHES], test_size=NUM_VALIDATION_MATCHES)
    test_matches = matches[-NUM_TEST_MATCHES:]

    new_ranks = train_model(train_matches, validation_matches, ss.player_id_dict, ss.player_name_dict, {}, neighbor_regularization=0.05)

    test_pred = predict_outcomes(new_ranks, test_matches[:,0], test_matches[:,1])
    test_numcorrect = score_numcorrect(test_pred, test_matches[:,2])
    test_avg_error = score_avg_error(test_pred, test_matches[:,2])
    test_median_error = score_median_error(test_pred, test_matches[:,2])
    print('{:d}/{:d} = {:.2f}% correct in test, avg/median gross error {:.3f}/{:.3f}'.format(test_numcorrect, len(test_matches), float(test_numcorrect)/len(test_matches)*100, test_avg_error, test_median_error))

    ss.save_model(new_ranks)
