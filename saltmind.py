""" Implements all the modeling and prediction. This is needed for intelligent betting.
"""

import numpy as np
import saltstorage as ss


def predict_outcomes(rank1, rank2):
    # 0 means p1 wins, 1 means p2 wins
    return 1./(1+np.exp(rank1-rank2))


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
        neighborhood_ids.append(this_ids)
        neighborhood_weights.append(this_weights)
    return neighborhood_ids, neighborhood_weights
        

def calc_neighborhood_averages_and_sizes(neighborhood_ids, neighborhood_weights, ranks):
    neighborhood_ranks = []
    for neighborhood in neighborhood_ids:
        neighborhood_ranks.append(ranks[neighborhood])
        
    do_sum = np.vectorize(np.sum)
    neighborhood_total_weights = do_sum(neighborhood_weights)

    print(np.max(neighborhood_total_weights), np.min(neighborhood_total_weights))
    do_dot = np.vectorize(np.dot)
    neighborhood_averages = do_dot(neighborhood_ranks, neighborhood_weights) / neighborhood_total_weights
    
    do_len = np.vectorize(len)
    neighborhood_sizes = np.array(do_len(neighborhood_ranks), dtype=int)

    return neighborhood_averages, neighborhood_sizes


def get_input_data():
    matches = np.array(ss.matches)
    pid_list = np.array(list(ss.player_name_dict.keys()), dtype=int)
    ranks = np.ones(len(ss.player_id_dict), dtype=float)
    return matches, ranks, pid_list


def train_model(matches, ranks, pid_list, neighbor_regularization=0.77):
    weights = calc_weights(matches[:,5].astype(float), np.min(matches[:,5]), np.max(matches[:,5]))
    print('weights', len(weights), np.max(weights), np.min(weights)
    neighborhood_ids, neighborhood_weights = calc_neighborhoods(matches, weights, pid_list)
    
    MAX_ITER = 50
    for i in range(MAX_ITER):
        print('Iteration {:d}'.format(i))
        neighborhood_averages, neighborhood_sizes = calc_neighborhood_averages_and_sizes(neighborhood_ids, neighborhood_weights, ranks)
        learning_rate = np.power((1+0.1*MAX_ITER)/(i+0.1*MAX_ITER), 0.602)
        # Randomize the order in which the matches will be processed this iteration
        indices = np.random.permutation(len(matches))
        for weight, match in zip(weights[indices], matches[indices]):
            pred = predict_outcomes(ranks[match[0]], ranks[match[1]])
            # Update ranks
            pred_factor = weight*(pred-match[2])*pred*(1-pred)
            ranks[match[0]] -= learning_rate *  (pred_factor + neighbor_regularization/neighborhood_sizes[match[0]]*(ranks[match[0]]-neighborhood_averages[match[0]]))
            ranks[match[1]] -= learning_rate * (-pred_factor + neighbor_regularization/neighborhood_sizes[match[1]]*(ranks[match[1]]-neighborhood_averages[match[1]]))

        in_sample_predictions = predict_outcomes(ranks[matches[:,0]], ranks[matches[:,1]])
        test_gross_error = np.sum(np.abs(in_sample_predictions - matches[:,2]))
        print('Gross error: {:.2f} over {:d} matches, {:.2f} average'.format(test_gross_error, len(matches), test_gross_error/len(matches)))
    return ranks


if __name__ == "__main__":
    ss.load_persistent_data()
    matches, ranks, pid_list = get_input_data()
    NUM_TEST_MATCHES = 200
    train_matches = np.array(matches[:-NUM_TEST_MATCHES])
    test_matches = np.array(matches[-NUM_TEST_MATCHES:])
    new_ranks = train_model(train_matches, ranks, pid_list)

    test_predictions = predict_outcomes(new_ranks[test_matches[:,0]], new_ranks[test_matches[:,1]])
    test_outcomes = test_matches[:,2]
    print(np.shape(test_outcomes), np.shape(test_predictions))
    test_gross_error = np.sum(np.abs(test_predictions - test_outcomes))
    test_numcorrect = np.sum((test_predictions>0.5) == test_outcomes)
    print('Gross error: {:.2f} over {:d} test matches, {:.2f} average'.format(test_gross_error, NUM_TEST_MATCHES, test_gross_error/NUM_TEST_MATCHES))
    print('Prediction error: {} correct over {} test matches, {:.2f}%'.format(test_numcorrect, NUM_TEST_MATCHES, float(test_numcorrect)/NUM_TEST_MATCHES*100))

    ss.save_model(ranks)
