from tak import State, Result, evaluate_easy, evaluate_medium, evaluate_hard
import csv, time

def test_negamax(state, depth, pruning, caching, evaluation_function):
    '''Obtains the total time needed by negamax algorithm to find a solution.'''
    move = state.negamax(depth, evaluation_function, pruning, caching, True)
    return (State.total_time, move)

def write_csv(filename, statistics):
    '''Writes the statistics to csv file.'''
    file = open(filename, "a")
    csv_file = csv.writer(file)
    csv_file.writerow(statistics)
    file.close()

def test_totals(board_size, n):
    '''Obtains the total time and branching factor for each of the first n iterations of the negamax algorithm (or until the game ends).'''

    details = str(board_size) + "TThard3"
    times = [details]
    choices = [details]
    
    state = State(board_size)
    for _ in range(n):
        (time, move) = test_negamax(state, 3, True, True, evaluate_hard)
        times.append(time)
        moves = len(state.possible_moves())
        choices.append(moves)
        if moves == 0:
            break
        state = move.play(state)
    
    write_csv("times.csv", times)
    write_csv("moves.csv", choices)

def test_heuristics(evaluation, n):
    '''Measures the impact of the evaluation function used on the totla time taken.'''

    details = "4TT" + evaluation + "3"
    if evaluation == "easy":
        evaluation_function = evaluate_easy
    elif evaluation == "medium":
        evaluation_function = evaluate_medium
    else: # evaluation == "hard"
        evaluation_function = evaluate_hard
    
    times = [details]
    
    state = State(4)
    for _ in range(n):
        (time, move) = test_negamax(state, 3, True, True, evaluation_function)
        times.append(time)
        if state.objective() != Result.NOT_FINISHED:
            break
        state = move.play(state)
    
    write_csv("heuristics.csv", times)

def test_parameters(cuts, caching, n):
    '''Measures the impact of the optimizations to the negamax algorithm on the total time taken.'''

    details = "4"
    if cuts:
        details += "T"
    else:
        details += "F"
    if caching:
        details += "T"
    else:
        details += "F"
    details += "hard3"

    times = [details]
    
    state = State(4)
    for _ in range(n):
        (time, move) = test_negamax(state, 3, cuts, caching, evaluate_hard)
        times.append(time)
        if state.objective() != Result.NOT_FINISHED:
            break
        state = move.play(state)
    
    write_csv("parameters.csv", times)

def test_time_percentage(n):
    '''Measures the percentage of the total time spent calculating possible moves, evaluating positions or playing moves.'''

    state = State(4)

    time_possible_moves = 0
    time_evaluating = 0
    time_playing_moves = 0
    total_time = 0

    for _ in range(n):
        move = state.negamax(3, evaluate_hard, True, True, True)

        time_possible_moves += State.nm_time_possible_moves
        time_evaluating += State.nm_time_evaluating
        time_playing_moves += State.nm_time_playing_moves
        total_time += State.total_time

        if state.objective() != Result.NOT_FINISHED:
            break

        state = move.play(state)
    
    time_other = total_time - time_possible_moves - time_evaluating - time_playing_moves

    # Calculate percentages
    time_possible_moves /= total_time
    time_evaluating /= total_time
    time_playing_moves /= total_time
    time_other /= total_time

    write_csv('time_percentage.csv', ['Time calculating possible moves (%)', 'Time evaluating positions (%)', 'Time playing moves (%)', 'Time performing other operations (%)'])
    write_csv('time_percentage.csv', [time_possible_moves, time_evaluating, time_playing_moves, time_other])

def statistics():
    '''Obtains statistics for the negamax algorithm.'''
    
    iterations = 25
    
    # Branching Factor and Total Times depending on Board Size
    for board_size in range(3, 6):
        test_totals(board_size, iterations)
    
    # Parameters
    for cuts in [True, False]:
        for caching in [True, False]:
            test_parameters(cuts, caching, iterations)
    
    # Heuristics
    for difficulty in ["easy", "medium", "hard"]:
        test_heuristics(difficulty, iterations)
    
    # Time Percentage
    test_time_percentage(iterations)

if __name__ == "__main__":
    start = time.time()
    statistics()
    end = time.time()
    print(end - start)
