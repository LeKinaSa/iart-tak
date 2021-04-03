from tak import State, evaluate_easy, evaluate_medium, evaluate_hard
import csv, time

def test_negamax(state, depth, pruning, caching, evaluation_function):
    '''Obtains the total time needed by negamax algorithm to find a solution.'''
    move = state.negamax(depth, evaluation_function, pruning, caching, True)
    return (State.total_time, move)

def write_csv(times, moves):
    '''Write the statistics to csv files.'''
    file = open("times.csv", "a")
    csv_file = csv.writer(file)
    csv_file.writerow(times)
    file.close()
    file = open("moves.csv", "a")
    csv_file = csv.writer(file)
    csv_file.writerow(moves)
    file.close()

def test(board_size, depth, cuts, caching, evaluation):
    '''Obtains the total time for each of 20 iterations of the negamax algorithm (or until the game ends).'''
    iterations = 50

    details = str(board_size)
    if cuts:
        details += "T"
    else:
        details += "F"
    if caching:
        details += "T"
    else:
        details += "F"
    details += evaluation
    if evaluation == "easy":
        evaluation_function = evaluate_easy
    elif evaluation == "medium":
        evaluation_function = evaluate_medium
    else:
        evaluation_function = evaluate_hard
    details += str(depth)
    
    times = [details]
    choices = [details]
    state = State(board_size)
    for _ in range(iterations):
        (time, move) = test_negamax(state, depth, cuts, caching, evaluation_function)
        times.append(time)
        moves = state.possible_moves()
        choices.append(len(moves))
        if len(moves) == 0 or move == None:
            break
        state = move.play(state)
    
    write_csv(times, choices)

def statistics():
    '''Obtain statistics for the total execution times from our negamax algorithm.'''
    
    for difficulty in ["easy", "medium", "hard"]:
        board_size = 3
        for n in range(1, 6):
            test(board_size, n,  True,  True, difficulty)
        
        if difficulty != "easy":
            break
        
        for n in range(1, 5):
            test(board_size, n,  True, False, difficulty)
            test(board_size, n, False,  True, difficulty)
            test(board_size, n, False, False, difficulty)
        
        board_size = 4
        for n in range(1, 5):
            test(board_size, n,  True,  True, difficulty)
            test(board_size, n,  True, False, difficulty)
            test(board_size, n, False,  True, difficulty)
            test(board_size, n, False, False, difficulty)

        board_size = 5
        for n in range(1, 4):
            test(board_size, n, True, True, difficulty)
    return

if __name__ == "__main__":
    start = time.time()
    statistics()
    end = time.time()
    print(end - start)
