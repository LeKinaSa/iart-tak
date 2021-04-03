from tak import State, evaluate_easy, evaluate_medium, evaluate_hard
from random import seed, randint
import csv

def test_negamax(state, depth, pruning, caching, evaluation_function):
    '''Obtains the total time needed by negamax algorithm to find a solution.'''
    state.negamax(depth, evaluation_function, pruning, caching, True)
    return State.total_time

def write_csv(times):
    '''Write the statistics csv file.'''
    file = open("Statistics.csv", "a")
    csv_file = csv.writer(file)
    csv_file.writerow(times)
    file.close()

def test(board_size, depth, cuts, caching, evaluation):
    '''Obtains the total time for each of 20 iterations of the negamax algorithm (or until the game ends).'''
    iterations = 20

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
    details += evaluation
    if evaluation == "easy":
        evaluation_function = evaluate_easy
    elif evaluation == "medium":
        evaluation_function = evaluate_medium
    else:
        evaluation_function = evaluate_hard

    times = [details]
    state = State(board_size)
    for _ in range(iterations):
        times.append(test_negamax(state, depth, cuts, caching, evaluation_function))
        moves = state.possible_moves()
        if len(moves) == 0:
            break
        move = moves[randint(0, len(moves) - 1)]
        state = move.play(state)
    
    write_csv(times)

def statistics():
    '''Obtain statistics for our negamax algorithm.'''
    seed()
    for board_size in range(3, 5):
        for n in range(6):
            test(board_size, n,  True,  True, "easy")
        for n in range(5):
            test(board_size, n,  True, False, "easy")
        for n in range(4):
            test(board_size, n, False,  True, "easy")
        for n in range(2):
            test(board_size, n, False, False, "easy")
    return

statistics()

# State.nm_calls
# State.nm_prunings
# State.nm_cache_hits
# State.nm_time_possible_moves
# State.nm_time_evaluating
# State.total_time
