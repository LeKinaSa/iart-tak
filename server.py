from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus

import json

from tak import State, Player, evaluate_easy, evaluate_medium

state = None
player_types = {}
possible_moves = []

def start_game(params: dict) -> dict:
    '''
    Start a new game with the specified parameters (board size and the type of each player).
    Returns the starting state in a JSON-compatible format.
    '''
    global state, player_types

    state = State(params['size'])
    player_types[Player.WHITE] = params['white_type']
    player_types[Player.BLACK] = params['black_type']

    return {'state': state.to_dict(), 'result': state.objective().value}

def get_possible_moves(params: dict) -> dict:
    '''Returns a list of all possible moves in a JSON-compatible format.'''
    global state, possible_moves

    possible_moves = state.possible_moves()
    return {'possible_moves': [move.to_dict() for move in possible_moves]}

def make_move(params: dict) -> dict:
    '''Makes a move and returns the resulting state in a JSON-compatible format.'''
    global state, possible_moves
    
    if possible_moves:
        move = possible_moves[params['move_idx']]
        state = move.play(state)
    
    return {'state': state.to_dict(), 'result': state.objective().value}


# Search depths for each board size (for level 3 AI)
depths = {
    3: 5,
    4: 4,
    5: 3
}

def get_move_hint(params: dict) -> dict:
    '''Returns the computer's best move for the current game state in a JSON-compatible format.'''
    depth = depths[state.board_size]
    return state.negamax(depth, pruning=True, caching=True).to_dict()

def get_computer_move(params: dict) -> dict:
    '''
    Obtains the computer move and corresponding game state in a JSON-compatible format.
    The evaluation function used and the negamax depth are decided by the level of the AI chosen previously.
    '''
    global state, player_types

    player_type = player_types[state.current_player]
    depth = depths[state.board_size]

    if player_type == 'ai1':
        move = state.negamax(depth - 2, evaluate_easy, True, True)
    elif player_type == 'ai2':
        move = state.negamax(depth - 1, evaluate_medium, True, True)
    elif player_type == 'ai3':
        move = state.negamax(depth, pruning=True, caching=True)

    if move:
        state = move.play(state)
        return {'state': state.to_dict(), 'result': state.objective().value, 'move': move.to_dict()}

    return {}

# Each URL (request) is mapped to a different function
# These functions take in a dictionary and return a dictionary
endpoints = {
    '/start_game': start_game,
    '/get_possible_moves': get_possible_moves,
    '/make_move': make_move,
    '/get_move_hint': get_move_hint,
    '/get_computer_move': get_computer_move
}


class _RequestHandler(BaseHTTPRequestHandler):
    # Server code adapted from https://gist.github.com/nitaku/10d0662536f37a087e1b
    def _set_headers(self):
        self.send_response(HTTPStatus.OK.value)
        self.send_header('Content-type', 'application/json')
        # Allow requests from any origin, so CORS policies don't
        # prevent local development.
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        '''Handle GET requests'''
        self._set_headers()
        self.wfile.write(json.dumps([{"Hello" : "There"}]).encode('utf-8'))

    def do_POST(self):
        '''Handle POST requests (using one of the endpoints defined previously)'''
        length = int(self.headers.get('content-length'))
        message = json.loads(self.rfile.read(length))
        if self.path in endpoints:
            res = endpoints[self.path](message)
        else:
            print("Path {self.path} was not expected")
            res = {}

        self._set_headers()
        self.wfile.write(json.dumps(res).encode('utf-8'))

    def do_OPTIONS(self):
        # Send allow-origin header for preflight POST XHRs.
        self.send_response(HTTPStatus.NO_CONTENT.value)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST')
        self.send_header('Access-Control-Allow-Headers', 'content-type')
        self.end_headers()


def run_server():
    server_address = ('', 8001)
    httpd = HTTPServer(server_address, _RequestHandler)
    print('Serving at %s:%d' % server_address)
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()