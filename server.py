from http.server import HTTPServer, BaseHTTPRequestHandler
from http import HTTPStatus

import json

from tak import State

state = None
white_type = None
black_type = None
possible_moves = []

def _sum(l : dict) -> dict:
    return {"result" : sum(l["numbers"])}

def start_game(params: dict) -> dict:
    global state, white_type, black_type

    state = State(params['size'])
    white_type = params['white_type']
    black_type = params['black_type']

    return state.to_dict()

def get_possible_moves(params: dict) -> dict:
    global state, possible_moves

    possible_moves = state.possible_moves()
    return {'possible_moves': [move.to_dict() for move in possible_moves]}

def make_move(params: dict) -> dict:
    global state, possible_moves
    
    if possible_moves:
        move = possible_moves[params['move_idx']]
        state = move.play(state)
    
    return state.to_dict()

# Add your endpoints here
endpoints = {
    '/sum' : _sum,
    '/start_game': start_game,
    '/get_possible_moves': get_possible_moves,
    '/make_move': make_move
}


class _RequestHandler(BaseHTTPRequestHandler):
    # Borrowing from https://gist.github.com/nitaku/10d0662536f37a087e1b
    def _set_headers(self):
        self.send_response(HTTPStatus.OK.value)
        self.send_header('Content-type', 'application/json')
        # Allow requests from any origin, so CORS policies don't
        # prevent local development.
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps([{"Hello" : "There"}]).encode('utf-8'))

    def do_POST(self):
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
    print('serving at %s:%d' % server_address)
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()