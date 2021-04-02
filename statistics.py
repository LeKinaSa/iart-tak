from tak import State
from random import seed, randint
import csv

def test_negamax(state, depth, cuts, caching):
    state.negamax(depth, cuts, caching, True)
    return State.total_time

def write_csv(details, times):
    file = open("Statistics.csv", "w")
    csv_file = csv.writer(file)
    csv_file.writerow(details)
    csv_file.writerow(times)
    file.close()

def test(board_size, depth, cuts, caching):
    details = str(board_size)
    if cuts:
        details += "T"
    else:
        details += "F"
    if caching:
        details += "T"
    else:
        details += "F"
    details += str(depth)

    times = []
    state = State(board_size)
    for _ in range(20):
        times.append(test_negamax(state, depth, cuts, caching))
        moves = state.possible_moves()
        if len(moves) == 0:
            break
        move = moves[randint(0, len(moves) - 1)]
        state = move.play(state)
    
    write_csv(details, times)

def statistics():
    seed()
    for board_size in range(3, 5):
        for n in range(6):
            test(board_size, n,  True,  True)
        for n in range(5):
            test(board_size, n,  True, False)
        for n in range(5):
            test(board_size, n, False,  True)
        for n in range(5):
            test(board_size, n, False, False)
    return

statistics()

# State.nm_calls
# State.nm_prunings
# State.nm_cache_hits
# State.nm_time_possible_moves
# State.nm_time_evaluating
# State.total_time
