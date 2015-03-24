""" Implements all the modeling and prediction. This is needed for intelligent betting.
"""

import numpy as np
import saltstorage as ss
import saltdoc as sd


def predict_outcomes(ranks, pid1, pid2):
    # 0 means p1 wins, 1 means p2 wins
    if len(pid1)==1:
        return predict_one_outcome(ranks, pid1, pid2)
    else:
        return [predict_one_outcome(ranks, id1, id2) for id1,id2 in zip(pid1,pid2)]


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
        #if len(this_ids)==0 or len(this_weights)==0:
        #    print('No neighborhood!', pid)
        neighborhood_ids.append(this_ids)
        neighborhood_weights.append(this_weights)
    return neighborhood_ids, neighborhood_weights
        

def calc_neighborhood_averages_and_sizes(neighborhood_ids, neighborhood_weights, ranks):
    neighborhood_ranks = []
    for neighborhood in neighborhood_ids:
        neighborhood_ranks.append([ranks[pid] for pid in neighborhood])
    
    for neighborhood in neighborhood_weights:
        if np.sum(neighborhood_weights)==0:
            print(neighborhood)
    do_sum = np.vectorize(np.sum)
    neighborhood_total_weights = do_sum(neighborhood_weights)
    print('neighborhood total weights', np.max(neighborhood_total_weights), np.min(neighborhood_total_weights))

    do_dot = np.vectorize(np.dot)
    neighborhood_averages = do_dot(neighborhood_ranks, neighborhood_weights) / neighborhood_total_weights
    print('neighborhood average ranks', np.max(neighborhood_averages), np.min(neighborhood_averages))
    
    do_len = np.vectorize(len)
    neighborhood_sizes = np.array(do_len(neighborhood_ranks), dtype=int)

    return neighborhood_averages, neighborhood_sizes


def train_model(matches, pname_dict, initial_ranks, neighbor_regularization=0.77):
    # Per-match attributes
    weights = calc_weights(matches[:,5].astype(float), np.min(matches[:,5]), np.max(matches[:,5]))
    print('{} weights from {} matches spanning {} - {}'.format(len(weights), len(matches[:,5]), min(weights), max(weights)))
    
    # Per-player attributes
    pid_list, lookup, ranks = prepare_inputs(matches, pname_dict, initial_ranks)
    print('{:d} players found in matches'.format(len(pid_list)))
    print('Player IDs span {:d} - {:d}'.format(min(pid_list), max(pid_list)))
    
    neighborhood_ids, neighborhood_weights = calc_neighborhoods(matches, weights, pid_list)
    print('{:d} neighborhood listings and {:d} neighborhood weights calculated'.format(len(neighborhood_ids), len(neighborhood_weights)))
    
    MAX_ITER = 5
    for i in range(MAX_ITER):
        print('Iteration {:d}'.format(i))
        neighborhood_averages, neighborhood_sizes = calc_neighborhood_averages_and_sizes(neighborhood_ids, neighborhood_weights, ranks)
        learning_rate = np.power((1+0.1*MAX_ITER)/(i+0.1*MAX_ITER), 0.602)
        # Randomize the order in which the matches will be processed this iteration
        indices = np.random.permutation(len(matches))
        print(np.max(indices), len(matches), len(weights))
        for weight, match in zip(weights[indices], matches[indices]):
            pred = predict_one_outcome(ranks, match[0], match[1])
            # Update ranks
            pred_factor = weight*(pred-match[2])*pred*(1-pred)
            try:
                ranks[match[0]] -= learning_rate *  (pred_factor + neighbor_regularization/neighborhood_sizes[lookup[match[0]]]*(ranks[match[0]]-neighborhood_averages[lookup[match[0]]]))
                ranks[match[1]] -= learning_rate * (-pred_factor + neighbor_regularization/neighborhood_sizes[lookup[match[1]]]*(ranks[match[1]]-neighborhood_averages[lookup[match[1]]]))
            except:
                print(len(neighborhood_sizes), lookup[match[0]], lookup[match[1]])

        in_sample_predictions = predict_outcomes(ranks, matches[:,0], matches[:,1])
        test_gross_error = np.sum(np.abs(in_sample_predictions - matches[:,2]))
        print('Gross error: {:.2f} over {:d} matches, {:.2f} average'.format(test_gross_error, len(matches), test_gross_error/len(matches)))
    return ranks


def prepare_inputs(matches, pname_dict, initial_ranks): 
    # Get a concise list of the player IDs that appear in the provided matches
    _, concise_names_list = sd.check_dictionary_conciseness(train_matches, pname_dict, return_concise_names=True, verbose=False)

    # Create new index lookup list for player IDs
    #new_pid_dict, new_pname_dict = sd.build_new_dicts(concise_names_list)
    #new_matches = translate_matches_to_new_dict(matches, ss.player_name_dict, new_pid_dict, verbose=False)
    pid_list = list(ss.player_name_dict.keys())
    lookup = [np.where(pid_list==pid)[0] for pid in pid_list]
    
    # Merge initial ranks onto default values
    ranks = {pid:1. for pid in pid_list}
    for key in initial_ranks.keys():
        ranks[key] = initial_ranks[key]

    return pid_list, lookup, ranks


if __name__ == "__main__":
    ss.load_persistent_data()
    matches = np.array(ss.matches)
    NUM_TEST_MATCHES = 200
    train_matches = matches[:-NUM_TEST_MATCHES]
    test_matches = matches[-NUM_TEST_MATCHES:]

    new_ranks = train_model(train_matches, ss.player_name_dict, {})

    test_predictions = predict_outcomes(new_ranks, test_matches[:,0], test_matches[:,1])
    test_outcomes = test_matches[:,2]
    print(np.shape(test_outcomes), np.shape(test_predictions))
    test_gross_error = np.sum(np.abs(test_predictions - test_outcomes))
    test_numcorrect = np.sum((test_predictions>0.5) == test_outcomes)
    print('Gross error: {:.2f} over {:d} test matches, {:.2f} average'.format(test_gross_error, NUM_TEST_MATCHES, test_gross_error/NUM_TEST_MATCHES))
    print('Prediction error: {} correct over {} test matches, {:.2f}%'.format(test_numcorrect, NUM_TEST_MATCHES, float(test_numcorrect)/NUM_TEST_MATCHES*100))

    ss.save_model(ranks)
