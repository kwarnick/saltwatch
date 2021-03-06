""" Implements all the modeling and prediction. This is needed for intelligent betting.
"""

import sys
import numpy as np
import saltstorage as ss
import saltdoc as sd
from sklearn.cross_validation import train_test_split
import pickle


def predict_outcomes(ranks, pid1, pid2):
    # <0.5 means p1 wins, >0.5 means p2 wins
    if len(pid1)==1:
        return predict_one_outcome(ranks, pid1, pid2)
    else:
        return np.array([predict_one_outcome(ranks, id1, id2) for id1,id2 in zip(pid1,pid2)])


def predict_one_outcome(ranks, pid1, pid2):
    try:
        return np.divide(1, 1+np.power(10,((ranks[pid1]-ranks[pid2])/400.)))
    except KeyError:
        return 0.5


def calc_weights(t, tmin, tmax, min_weight=0.):
    return (1-min_weight)*np.power((1+t-tmin)/(1+tmax-tmin), 2.) + min_weight
  

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
            if iterations_since_new_best_score>250:
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


def prepare_inputs(matches, pid_dict, pname_dict, initial_ranks={}, min_weight=0., verbose=True):
    # Per-player attributes
    pid_list, lookup, ranks = prepare_player_related_inputs(matches, pid_dict, pname_dict, initial_ranks=initial_ranks)
    if verbose:
        print('{:d} players found in {:d} matches'.format(len(pid_list), len(matches)))
    
    # Per-match attributes
    weights, neighborhood_ids, neighborhood_weights, neighborhood_sizes, neighborhood_total_weights = prepare_match_related_inputs(matches, pid_list, min_weight=min_weight)

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


def prepare_match_related_inputs(matches, pid_list, min_weight=0.):
    weights = calc_weights(matches[:,5].astype(float), np.min(matches[:,5]), np.max(matches[:,5]), min_weight=min_weight)
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


def calc_delta(E, epsilon=0.05):
    clipped_E  = np.clip(E, epsilon, 1.-epsilon)
    return 400*np.log10((1-clipped_E)/clipped_E)


def run_one_model(matches, pid_dict, pname_dict, N_VAL, N_TEST, initial_ranks, neighbor_regularization, MAX_ITER, base_lr, frac_lr_const, min_weight, verbose=True, random_state=1334):
    
    from sklearn.cross_validation import KFold
    kf = KFold(len(matches), n_folds=50, shuffle=True)
    for train_index, test_index in kf:
        break

    num_characters = np.max(matches[:,:2])+1
    transition = np.zeros(shape=(num_characters, num_characters), dtype=np.int16)
    for match in matches[train_index]:
        transition[match[match[2]], match[1-match[2]]] += 1
    times_seen = np.sum(transition, axis=0) + np.sum(transition, axis=1)
    win_rate = np.sum(transition, axis=1) / times_seen.astype(float)
    weights = transition + transition.T

    np.seterr(invalid='ignore')

    power_levels = np.random.randn(num_characters)
    for i in range(20):
        for pid in range(num_characters):
            opponents = np.where(weights[pid,:])[0]
            if len(opponents)==0:
                continue
            E = np.divide(transition[pid].astype(float), weights[pid])[opponents]
            E = np.nan_to_num(E)
            deltas = calc_delta(E, epsilon=0.05)
            #idx_max = np.where(E==1)[0]
            #idx_min = np.where(E==0)[0]
            suggested_vals = power_levels[opponents] - deltas
            #if len(idx_max)>0:
            #    suggested_vals[idx_max] = np.max(suggested_vals[idx_max])
            #if len(idx_min)>0:
            #    suggested_vals[idx_min] = np.min(suggested_vals[idx_min])
            final_val = np.average(suggested_vals, weights=weights[pid, opponents])
            power_levels[pid] = final_val

    rows, cols = np.where(transition)
    probs = np.zeros(shape=(len(power_levels),len(power_levels)))
    for row,col in zip(rows, cols):
        probs[row,col] = predict_one_outcome(power_levels, row, col)
    preds = probs>0.5
    preds[probs==0.5] = 0.5

    correct = 0
    for row,col in zip(rows, cols):
        winner = float(transition[row,col])/weights[row,col]<0.5
        if preds[row,col] == winner:
            correct += transition[row,col]
    print('Training accuracy {}'.format(correct/np.sum(transition)))

    correct = 0
    for row,col,winner in matches[test_index,:3]:
        pred = predict_one_outcome(power_levels, row, col) > 0.5
        if pred==winner:
            correct += 1
    print('Test accuracy {}'.format(correct/float(len(test_index))))

    new_ranks = {pid:power_levels[pid] for pid in range(num_characters)}
    wins = {pid:val for pid,val in zip(range(num_characters),np.sum(transition, axis=1))}
    losses = {pid:val for pid,val in zip(range(num_characters),np.sum(transition, axis=0))}
    times_seen = {pid:val for pid,val in zip(range(num_characters),times_seen)}
   
    acc, tpr, tnr = evaluate_prediction_stats(matches, list(range(num_characters)), new_ranks) 

    return new_ranks, wins, losses, times_seen, acc, tpr, tnr


def evaluate_prediction_stats(matches, pid_list, ranks):
    predictions = predict_outcomes(ranks, matches[:,0], matches[:,1])

    tp = {pid:0.0 for pid in pid_list}
    fp = {pid:0.0 for pid in pid_list}
    tn = {pid:0.0 for pid in pid_list}
    fn = {pid:0.0 for pid in pid_list}
    
    for match,pred_val in zip(matches,predictions):
        # Get player IDs of the winner and loser
        winner_id = match[match[2]]
        loser_id = match[1-match[2]]
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
        winner = match[match[2]]
        loser = match[1-match[2]]
        w[winner] += 1
        l[loser] += 1

    # check that wins + losses = times_seen
    for pid in pid_list:
        if not (w[pid] + l[pid] == times_seen[pid]):
            print('Player id {} has an invalid w/l/t count of {}/{}/{}'.format(pid, w[pid], l[pid], times_seen[pid]))

    return w, l, times_seen


def hyperparameter_search(initial_ranks):
    N_VAL = 1000
    N_TEST = 1000
    MAX_ITER = 500
    min_weight = 0.
    nr_vals = [0]
    base_lr_vals = np.linspace(1,20,77)
    frac_lr_const_vals = np.linspace(0, 1, 21)

    ss.load_persistent_data()
    matches = np.array(ss.matches)

    pid_list, lookup, ranks, weights, neighborhood_ids, neighborhood_weights, neighborhood_sizes, neighborhood_total_weights = prepare_inputs(matches, ss.player_id_dict, ss.player_name_dict, initial_ranks=initial_ranks, min_weight=min_weight)

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
        N_VAL = 500
    if len(sys.argv)>3:
        N_TEST = int(sys.argv[3])
    else:
        N_TEST = 0
    if len(sys.argv)>4:
        MAX_ITER = int(sys.argv[4])
    else:
        MAX_ITER = 300
    if len(sys.argv)>5:
        random_state = int(sys.argv[5])
    else:
        random_state = 1334
    base_lr = 2 #4.5 #1.6  
    frac_lr_const = 0. #0.4
    min_weight = 0.

    ss.load_persistent_data()
    ss.load_player_stats()
    matches = np.array(ss.matches)
    #initial_ranks = ss.ranks
    initial_ranks = {}
    
    new_ranks, wins, losses, times_seen, acc, tpr, tnr  = run_one_model(matches, ss.player_id_dict, ss.player_name_dict, N_VAL, N_TEST, initial_ranks, neighbor_regularization, MAX_ITER, base_lr=base_lr, frac_lr_const=frac_lr_const, min_weight=min_weight, verbose=True, random_state=random_state)
     
    if N_TEST==0:
        ss.replace_player_stats(new_ranks, wins, losses, times_seen, acc, tpr, tnr)
        ss.save_player_stats()
