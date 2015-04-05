import saltmind as sm
import numpy as np

test_matches = [[0, 1, 0, 0, 0, 1], 
                [0, 2, 0, 0, 0, 1], 
                [1, 2, 0, 0, 0, 1],
                [0, 3, 0, 0, 0, 1]]

test_pid_dict = {0:0, 1:1, 2:2, 3:3}
test_pname_dict = {0:0, 1:1, 2:2, 3:3}

N_VAL = 0
N_TEST = 0
initial_ranks = {}
neighbor_regularization = 0.00
MAX_ITER = 100
random_state = 1334


new_ranks, wins, losses, times_seen, acc, tpr, tnr = sm.run_one_model(np.array(test_matches), test_pid_dict, test_pname_dict, N_VAL, N_TEST, initial_ranks, neighbor_regularization, MAX_ITER, verbose=True, random_state=random_state)

print(new_ranks)
print(wins)
print(losses)
print(times_seen)
print('')


N_VAL = 0
N_TEST = 0
initial_ranks = {}
neighbor_regularization = 1.
MAX_ITER = 100
random_state = 1334


new_ranks, wins, losses, times_seen, acc, tpr, tnr = sm.run_one_model(np.array(test_matches), test_pid_dict, test_pname_dict, N_VAL, N_TEST, initial_ranks, neighbor_regularization, MAX_ITER, verbose=True, random_state=random_state)

print(new_ranks)
print(wins)
print(losses)
print(times_seen)
print('')

