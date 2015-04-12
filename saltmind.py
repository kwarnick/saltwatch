""" Implements all the modeling and prediction. This is needed for intelligent betting.
"""

import sys
import numpy as np
import saltstorage as ss
import saltdoc as sd
from sklearn.cross_validation import train_test_split
import pickle


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

    #neighborhood_ids_2 = [[match[0] for match in matches if match[1]==pid] + [match[1] for match in matches if match[0]==pid] for pid in pid_list]
    # ^ Would need the weights too, in the same order. Probably just one big list comprehension grabbing both. No clear time savings either. Oh well, leave for now.
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
    neighborhood_averages = [np.dot(ranks, weights)/total_weight for (ranks,weights,total_weight) in zip(neighborhood_ranks, neighborhood_weights, neighborhood_total_weights)]
    return neighborhood_averages


def calc_neighborhood_ranks(neighborhood_ids, ranks):
    neighborhood_ranks = []
    for neighborhood in neighborhood_ids:
        neighborhood_ranks.append([ranks[pid] for pid in neighborhood])
    return neighborhood_ranks


def calc_neighborhood_sizes(neighborhood_ids):
    neighborhood_sizes = [len(x) for x in neighborhood_ids]
    return neighborhood_sizes


def calc_neighborhood_total_weights(neighborhood_weights):
    neighborhood_total_weights = [sum(weights) for weights in neighborhood_weights]
    return neighborhood_total_weights


def train_model(matches, pid_list, lookup, ranks, weights, neighborhood_ids, neighborhood_weights, neighborhood_sizes, neighborhood_total_weights, 
        validation_matches=[], neighbor_regularization=0.4, MAX_ITER=200, base_lr=1.0, frac_lr_const=0.0, verbose=True):

    if verbose:
        print('Initial scores: ')
        if len(validation_matches)>0:
            score_performance(ranks, validation_matches, 'validation')
        score_performance(ranks, matches, 'training')
        print('')

    best_val_score = 0.0
    best_ranks = ranks.copy()
    iterations_since_new_best_score = 0
    for i in range(MAX_ITER):
        if verbose:
            print('Iteration {:d}'.format(i))
        neighborhood_ranks = calc_neighborhood_ranks(neighborhood_ids, ranks)
        neighborhood_averages = calc_neighborhood_averages(neighborhood_ranks, neighborhood_weights, neighborhood_total_weights)
        #learning_rate = 5.*np.power((1+0.1*MAX_ITER)/(i+0.1*MAX_ITER), 0.602) + 15.
        learning_rate = base_lr*((1-frac_lr_const)*np.power((1+0.1*MAX_ITER)/(i+0.1*MAX_ITER), 0.602) + frac_lr_const)
        #learning_rate = 1
        indices = np.random.permutation(len(matches))
        
        for weight, match in zip(weights[indices], matches[indices]):
            pred = predict_one_outcome(ranks, match[0], match[1])
            pred_factor = weight*(match[2]-pred)*pred*(1-pred)
            ranks[match[0]] -= learning_rate *  (pred_factor + neighbor_regularization/neighborhood_sizes[lookup[match[0]]]*(ranks[match[0]]-neighborhood_averages[lookup[match[0]]]))
            ranks[match[1]] -= learning_rate * (-pred_factor + neighbor_regularization/neighborhood_sizes[lookup[match[1]]]*(ranks[match[1]]-neighborhood_averages[lookup[match[1]]]))
            #ranks[match[0]] -= learning_rate *  (pred_factor + neighbor_regularization*(ranks[match[0]]-neighborhood_averages[lookup[match[0]]]))
            #ranks[match[1]] -= learning_rate * (-pred_factor + neighbor_regularization*(ranks[match[1]]-neighborhood_averages[lookup[match[1]]]))
       
        if len(validation_matches)>0:
            val_score, _, _ = score_performance(ranks, validation_matches, 'validation', verbose=verbose, return_values=True)
            if val_score > best_val_score:
                best_val_score = val_score
                best_ranks = ranks
                iterations_since_new_best_score = 0
            elif val_score == best_val_score:
                best_ranks = ranks
                iterations_since_new_best_score +=1
            else:
                iterations_since_new_best_score +=1
            if iterations_since_new_best_score>200:
                if verbose:
                    print('Validation criteria reached, terminating iteration.')
                break
        else:
            best_ranks = ranks
        if verbose:
            score_performance(ranks, matches, 'training')
            print('')

    if verbose and len(validation_matches)>0:
        print('Best validation score: {:.2f}'.format(best_val_score))

    return best_ranks


def score_numcorrect(Y_pred, Y):
    not_just_guessing = Y_pred!=0.5
    just_guessing = Y_pred==0.5
    return np.sum((Y_pred[not_just_guessing]>0.5) == Y[not_just_guessing]) + int((len(Y)-np.sum(not_just_guessing))/2.)


def score_avg_error(Y_pred, Y):
    return np.mean(np.abs(Y_pred - Y))


def score_median_error(Y_pred, Y):
    return np.median(np.abs(Y_pred-Y))


def prepare_inputs(matches, pid_dict, pname_dict, initial_ranks={}, verbose=True):
    # Per-player attributes
    pid_list, lookup, ranks = prepare_player_related_inputs(matches, pid_dict, pname_dict, initial_ranks=initial_ranks)
    if verbose:
        print('{:d} players found in {:d} matches'.format(len(pid_list), len(matches)))
    
    # Per-match attributes
    weights, neighborhood_ids, neighborhood_weights, neighborhood_sizes, neighborhood_total_weights = prepare_match_related_inputs(matches, pid_list)

    return pid_list, lookup, ranks, weights, neighborhood_ids, neighborhood_weights, neighborhood_sizes, neighborhood_total_weights


def prepare_player_related_inputs(matches, pid_dict, pname_dict, initial_ranks={}): 
    # Get a concise list of the player IDs that appear in the provided matches
    _, concise_names_list = sd.check_dictionary_conciseness(matches, pname_dict, return_concise_names=True, verbose=False)

    # Create new index lookup list for player IDs
    pid_list = [pid_dict[name] for name in concise_names_list]
    lookup = {pid:i for i,pid in enumerate(pid_list)}
    
    # Merge initial ranks onto default values
    ranks = {pid:20. for pid in pid_list}
    for key in initial_ranks.keys():
        ranks[key] = initial_ranks[key]

    return pid_list, lookup, ranks


def prepare_match_related_inputs(matches, pid_list):
    weights = calc_weights(matches[:,5].astype(float), np.min(matches[:,5]), np.max(matches[:,5]))
    neighborhood_ids, neighborhood_weights = calc_neighborhoods(matches, weights, pid_list)
    neighborhood_sizes = calc_neighborhood_sizes(neighborhood_ids)
    neighborhood_total_weights = calc_neighborhood_total_weights(neighborhood_weights)

    return weights, neighborhood_ids, neighborhood_weights, neighborhood_sizes, neighborhood_total_weights


def score_performance(ranks, matches, desc_str, verbose=True, return_values=False):
    pred = predict_outcomes(ranks, matches[:,0], matches[:,1])
    numcorrect = score_numcorrect(pred, matches[:,2])
    pct_correct = float(numcorrect)/len(matches)*100
    avg_error = score_avg_error(pred, matches[:,2])
    median_error = score_median_error(pred, matches[:,2])
    if verbose:
        print('{:d}/{:d} = {:.2f}% correct in {}, avg/median error {:.3f}/{:.3f}'.format(numcorrect, len(matches), pct_correct, desc_str, avg_error, median_error))
    if return_values:
        return pct_correct, avg_error, median_error


def run_one_model(matches, pid_dict, pname_dict, N_VAL, N_TEST, initial_ranks, neighbor_regularization, MAX_ITER, base_lr, frac_lr_const, verbose=True, random_state=1334):
    # Prepare inputs for training models from the current data sets
    pid_list, lookup, ranks, weights, neighborhood_ids, neighborhood_weights, neighborhood_sizes, neighborhood_total_weights = prepare_inputs(matches, pid_dict, pname_dict, initial_ranks=initial_ranks)
    
    # Separate validation and training sets from the test set
    if N_TEST>0:
        train_val_matches = matches[:-N_TEST]
        test_matches = matches[-N_TEST:]
    elif N_TEST==0:
        train_val_matches = matches
        test_matches = []

    # Split the validation and training sets
    if N_VAL>0:
        train_matches, validation_matches = train_test_split(train_val_matches, test_size=N_VAL, random_state=random_state)
    elif N_VAL==0:
        train_matches = train_val_matches
        validation_matches = []

    # Train the model, score and save if relevant
    new_ranks = train_model(train_matches, pid_list, lookup, ranks.copy(), weights, neighborhood_ids, neighborhood_weights, neighborhood_sizes, neighborhood_total_weights, validation_matches=validation_matches, neighbor_regularization=neighbor_regularization, MAX_ITER=MAX_ITER, base_lr=base_lr, frac_lr_const=frac_lr_const, verbose=verbose)

    if len(test_matches)>0:
        score = score_performance(new_ranks, test_matches, 'test', return_values=True)

    wins, losses, times_seen = evaluate_player_stats(matches, pid_list, neighborhood_sizes)

    acc, tpr, tnr = evaluate_prediction_stats(matches, pid_list, new_ranks)
    
    return new_ranks, wins, losses, times_seen, acc, tpr, tnr


def evaluate_prediction_stats(matches, pid_list, ranks):
    predictions = predict_outcomes(ranks, matches[:,0], matches[:,1])

    tp = {pid:0.0 for pid in pid_list}
    fp = {pid:0.0 for pid in pid_list}
    tn = {pid:0.0 for pid in pid_list}
    fn = {pid:0.0 for pid in pid_list}
    
    for match,pred_val in zip(matches,predictions):
        # Get player IDs of the winner and loser
        if match[2] == 0:
            winner_id = match[0]
            loser_id = match[1]
        elif match[2] == 1:
            winner_id = match[1]
            loser_id = match[0]
        # See whether match[0] or match[1] was predicted to win
        if pred_val == 0.5:
            pred = int(round(np.random.random()))  
        else:
            pred = int(round(pred_val))
        # Log the statistics from this match
        if match[2] == pred:
            tp[winner_id] += 1
            tn[loser_id] += 1
        else:
            fp[winner_id] += 1
            fn[loser_id] += 1

    totals = {pid:tp[pid]+tn[pid]+fp[pid]+fn[pid] for pid in pid_list}
    totals_p = {pid:tp[pid]+fp[pid] for pid in pid_list}
    totals_n = {pid:tn[pid]+fn[pid] for pid in pid_list}
    totals_correct = {pid:tp[pid]+tn[pid] for pid in pid_list}

    acc = {pid:(totals_correct[pid])/float(totals[pid]) if not totals[pid]==0 else 0.0 for pid in pid_list}
    tpr = {pid:(tp[pid])/float(totals_p[pid]) if not totals_p[pid]==0 else 0.0 for pid in pid_list}
    tnr = {pid:(tn[pid])/float(totals_n[pid]) if not totals_n[pid]==0 else 0.0 for pid in pid_list}

    return acc, tpr, tnr


def evaluate_player_stats(matches, pid_list, neighborhood_sizes):
    # Repackage neighborhood sizes for export
    times_seen = {}
    for pid, size in zip(pid_list, neighborhood_sizes):
        times_seen[pid] = size

    # get wins and losses
    w = {pid:0 for pid in pid_list}
    l = {pid:0 for pid in pid_list}
    for match in matches:
        # match[2] indicates whether match[0] or match[1] won
        if match[2] == 0:
            w[match[0]] += 1
            l[match[1]] += 1
        elif match[2] == 1:
            w[match[1]] += 1
            l[match[0]] += 1

    # check that wins + losses = times_seen
    for pid in pid_list:
        if not (w[pid] + l[pid] == times_seen[pid]):
            print('Player id {} has an invalid w/l/t count of {}/{]/{}'.format(pid, w[pid], l[pid], times_seen[pid]))

    return w, l, times_seen


def hyperparameter_search(initial_ranks):
    N_VAL = 500
    N_TEST = 500
    nr_vals = [0]
    MAX_ITER = 500
    base_lr_vals = np.logspace(0.8, 1.3, 15)
    frac_lr_const_vals = np.linspace(0, 1, 11)

    ss.load_persistent_data()
    matches = np.array(ss.matches)
    
    pid_list, lookup, ranks, weights, neighborhood_ids, neighborhood_weights, neighborhood_sizes, neighborhood_total_weights = prepare_inputs(matches, ss.player_id_dict, ss.player_name_dict, initial_ranks=initial_ranks)

    if N_VAL>0:
        train_matches, validation_matches = train_test_split(matches[:-N_TEST], test_size=N_VAL)
    else:
        train_matches = matches[:-N_TEST]
        validation_matches = []
    test_matches = matches[-N_TEST:]
 
    import itertools
    params = list(itertools.product(*[nr_vals, base_lr_vals, frac_lr_const_vals]))
    scores = np.zeros((len(params),3))
    for i, (neighbor_regularization, base_lr, frac_lr_const) in enumerate(params):
        new_ranks = train_model(train_matches, pid_list, lookup, ranks.copy(), weights, neighborhood_ids, neighborhood_weights, neighborhood_sizes, neighborhood_total_weights, validation_matches=validation_matches, neighbor_regularization=neighbor_regularization, MAX_ITER=MAX_ITER, base_lr=base_lr, frac_lr_const=frac_lr_const, verbose=False)
        scores[i,:] = score_performance(new_ranks, test_matches, 'test', return_values=True)
        print('Ranks {:0.3f} - {:0.3f}'.format(np.min(list(new_ranks.values())), np.max(list(new_ranks.values()))))
    
    indices = np.lexsort((scores[:,1], -scores[:,0]))  # Second one has first sort priority
    print('')
    print('Top 10 parameters by high accuracy and then by low average error: ')
    for index in indices[:10]:
        print('{}:  {:.2f}% accuracy, {:.3f}/{:.3f} avg/median error'.format(params[index], scores[index,0], scores[index,1], scores[index,2]))
    
    pickle.dump([scores, params], open('hyperparam_results.p','wb'))

    return scores, params


if __name__ == "__main__":
    if len(sys.argv)>1:
        neighbor_regularization = float(sys.argv[1])
    else:
        neighbor_regularization = 0.00
    if len(sys.argv)>2:
        N_VAL = int(sys.argv[2])
    else:
        N_VAL = 200
    if len(sys.argv)>3:
        N_TEST = int(sys.argv[3])
    else:
        N_TEST = 0
    if len(sys.argv)>4:
        MAX_ITER = int(sys.argv[4])
    else:
        MAX_ITER = 500
    if len(sys.argv)>5:
        random_state = int(sys.argv[5])
    else:
        random_state = 1334
    base_lr = 7.5
    frac_lr_const = 0.2

    ss.load_persistent_data()
    ss.load_player_stats()
    matches = np.array(ss.matches)
    #initial_ranks = ss.ranks
    initial_ranks = {}
    
    new_ranks, wins, losses, times_seen, acc, tpr, tnr  = run_one_model(matches, ss.player_id_dict, ss.player_name_dict, N_VAL, N_TEST, initial_ranks, neighbor_regularization, MAX_ITER, base_lr=base_lr, frac_lr_const=frac_lr_const, verbose=True, random_state=random_state)
     
    if N_TEST==0:
        ss.replace_player_stats(new_ranks, wins, losses, times_seen, acc, tpr, tnr)
        ss.save_player_stats()
