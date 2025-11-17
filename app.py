from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, field, asdict
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET', 'default-secret-key-change-me')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

Player = Literal['white', 'black']

@dataclass
class PointState:
    checkers: int
    player: Optional[Player]

@dataclass
class GameSession:
    game_id: str
    board_state: List[Dict]
    turn: Player
    player1_sid: Optional[str] = None
    player2_sid: Optional[str] = None
    white_player_sid: Optional[str] = None
    black_player_sid: Optional[str] = None
    dice: List[int] = field(default_factory=list)
    available_moves: List[int] = field(default_factory=list)
    
    def to_dict(self):
        return {
            'game_id': self.game_id,
            'board_state': self.board_state,
            'turn': self.turn,
            'player1_sid': self.player1_sid,
            'player2_sid': self.player2_sid,
            'white_player_sid': self.white_player_sid,
            'black_player_sid': self.black_player_sid,
            'dice': self.dice,
            'available_moves': self.available_moves
        }

games: Dict[str, GameSession] = {}
sid_to_game: Dict[str, str] = {}

def generate_game_id() -> str:
    parts = []
    for _ in range(3):
        part = ''.join(random.choices(string.ascii_uppercase, k=3))
        parts.append(part)
    return '-'.join(parts)

def initialize_board() -> List[Dict]:
    board = []
    for i in range(24):
        board.append({'checkers': 0, 'player': None})
    
    board[0] = {'checkers': 2, 'player': 'white'}
    board[11] = {'checkers': 5, 'player': 'white'}
    board[16] = {'checkers': 3, 'player': 'white'}
    board[18] = {'checkers': 5, 'player': 'white'}
    
    board[23] = {'checkers': 2, 'player': 'black'}
    board[12] = {'checkers': 5, 'player': 'black'}
    board[7] = {'checkers': 3, 'player': 'black'}
    board[5] = {'checkers': 5, 'player': 'black'}
    
    return board

def get_player_color(game: GameSession, sid: str) -> Optional[Player]:
    if game.white_player_sid == sid:
        return 'white'
    elif game.black_player_sid == sid:
        return 'black'
    return None

def is_valid_move(game: GameSession, from_point: int, to_point: int, player: Player) -> bool:
    if not game.available_moves:
        return False
    
    if from_point < 0 or from_point >= 24 or to_point < 0 or to_point >= 24:
        return False
    
    if game.board_state[from_point]['player'] != player:
        return False
    
    if game.board_state[from_point]['checkers'] == 0:
        return False
    
    distance = abs(to_point - from_point)
    
    if player == 'white':
        if to_point <= from_point:
            return False
        distance = to_point - from_point
    else:
        if to_point >= from_point:
            return False
        distance = from_point - to_point
    
    if distance not in game.available_moves:
        return False
    
    dest_point = game.board_state[to_point]
    if dest_point['player'] is not None and dest_point['player'] != player:
        if dest_point['checkers'] > 1:
            return False
    
    return True

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connected', {'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    
    if request.sid in sid_to_game:
        game_id = sid_to_game[request.sid]
        if game_id in games:
            game = games[game_id]
            
            emit('player-disconnected', {
                'message': 'The other player has disconnected'
            }, room=game_id, skip_sid=request.sid)
            
            del sid_to_game[request.sid]
            
            if game.player1_sid == request.sid or game.player2_sid == request.sid:
                del games[game_id]
                print(f'Game {game_id} deleted due to player disconnect')

@socketio.on('create-game')
def handle_create_game():
    game_id = generate_game_id()
    
    while game_id in games:
        game_id = generate_game_id()
    
    board_state = initialize_board()
    
    game = GameSession(
        game_id=game_id,
        board_state=board_state,
        turn='white',
        player1_sid=request.sid
    )
    
    games[game_id] = game
    sid_to_game[request.sid] = game_id
    
    join_room(game_id)
    
    print(f'Game created: {game_id} by {request.sid}')
    
    emit('game-created', {'gameId': game_id})

@socketio.on('join-game')
def handle_join_game(data):
    game_id = data.get('gameId')
    
    if not game_id:
        emit('error', {'message': 'Game ID is required'})
        return
    
    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return
    
    game = games[game_id]
    
    if game.player2_sid is not None:
        emit('error', {'message': 'Game is full'})
        return
    
    game.player2_sid = request.sid
    game.white_player_sid = game.player1_sid
    game.black_player_sid = game.player2_sid
    
    sid_to_game[request.sid] = game_id
    join_room(game_id)
    
    print(f'Player {request.sid} joined game {game_id}')
    
    emit('game-started', {
        'boardState': game.board_state,
        'turn': game.turn,
        'players': {
            'white': game.white_player_sid,
            'black': game.black_player_sid
        }
    }, room=game_id)

@socketio.on('roll-dice')
def handle_roll_dice(data):
    game_id = data.get('gameId')
    
    if not game_id:
        emit('error', {'message': 'Game ID is required'})
        return
    
    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return
    
    game = games[game_id]
    
    player_color = get_player_color(game, request.sid)
    
    if player_color != game.turn:
        emit('error', {'message': 'Not your turn'})
        return
    
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    
    game.dice = [dice1, dice2]
    
    if dice1 == dice2:
        game.available_moves = [dice1, dice1, dice1, dice1]
    else:
        game.available_moves = [dice1, dice2]
    
    print(f'Dice rolled in game {game_id}: {game.dice}')
    
    emit('dice-rolled', {
        'dice': game.dice,
        'turn': game.turn
    }, room=game_id)

@socketio.on('move-piece')
def handle_move_piece(data):
    game_id = data.get('gameId')
    from_point = data.get('fromPointIndex')
    to_point = data.get('toPointIndex')
    
    if not game_id:
        emit('error', {'message': 'Game ID is required'})
        return
    
    if from_point is None or to_point is None:
        emit('error', {'message': 'From and to point indices are required'})
        return
    
    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return
    
    game = games[game_id]
    
    player_color = get_player_color(game, request.sid)
    
    if player_color is None:
        emit('error', {'message': 'Player not in game'})
        return
    
    if player_color != game.turn:
        emit('error', {'message': 'Not your turn'})
        return
    
    if not is_valid_move(game, from_point, to_point, player_color):
        emit('error', {'message': 'Invalid move'})
        return
    
    if player_color == 'white':
        distance = to_point - from_point
    else:
        distance = from_point - to_point
    
    if distance in game.available_moves:
        game.available_moves.remove(distance)
    else:
        emit('error', {'message': 'Invalid move - dice value not available'})
        return
    
    game.board_state[from_point]['checkers'] -= 1
    if game.board_state[from_point]['checkers'] == 0:
        game.board_state[from_point]['player'] = None
    
    dest_point = game.board_state[to_point]
    if dest_point['player'] is not None and dest_point['player'] != player_color:
        if dest_point['checkers'] == 1:
            game.board_state[to_point]['checkers'] = 1
            game.board_state[to_point]['player'] = player_color
    else:
        game.board_state[to_point]['checkers'] += 1
        game.board_state[to_point]['player'] = player_color
    
    print(f'Piece moved in game {game_id}: {from_point} -> {to_point}')
    
    emit('board-updated', {
        'boardState': game.board_state
    }, room=game_id)

@socketio.on('end-turn')
def handle_end_turn(data):
    game_id = data.get('gameId')
    
    if not game_id:
        emit('error', {'message': 'Game ID is required'})
        return
    
    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return
    
    game = games[game_id]
    
    player_color = get_player_color(game, request.sid)
    
    if player_color != game.turn:
        emit('error', {'message': 'Not your turn'})
        return
    
    game.available_moves = []
    game.dice = []
    
    game.turn = 'black' if game.turn == 'white' else 'white'
    
    print(f'Turn ended in game {game_id}, new turn: {game.turn}')
    
    emit('new-turn', {
        'turn': game.turn
    }, room=game_id)

@app.route('/')
def index():
    return {
        'status': 'Backgammon Server Running',
        'active_games': len(games)
    }

@app.route('/health')
def health():
    return {'status': 'healthy', 'games': len(games)}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f'Starting Backgammon server on port {port}...')
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
