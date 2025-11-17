from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, field, asdict
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
secret_key = os.getenv('SESSION_SECRET')
if not secret_key:
    print("WARNING: SESSION_SECRET not set. Using development key. DO NOT USE IN PRODUCTION!")
    secret_key = 'dev-secret-key-change-in-production'
app.config['SECRET_KEY'] = secret_key
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
    white_bar: int = 0
    black_bar: int = 0
    white_off: int = 0
    black_off: int = 0
    
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
            'available_moves': self.available_moves,
            'white_bar': self.white_bar,
            'black_bar': self.black_bar,
            'white_off': self.white_off,
            'black_off': self.black_off
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

def has_checkers_on_bar(game: GameSession, player: Player) -> bool:
    if player == 'white':
        return game.white_bar > 0
    else:
        return game.black_bar > 0

def all_checkers_in_home_board(game: GameSession, player: Player) -> bool:
    if player == 'white':
        for i in range(18):
            if game.board_state[i]['player'] == 'white' and game.board_state[i]['checkers'] > 0:
                return False
        return game.white_bar == 0
    else:
        for i in range(6, 24):
            if game.board_state[i]['player'] == 'black' and game.board_state[i]['checkers'] > 0:
                return False
        return game.black_bar == 0

def is_valid_move(game: GameSession, from_point: int, to_point: int, player: Player) -> bool:
    if not game.available_moves:
        return False
    
    if has_checkers_on_bar(game, player):
        if from_point != -1:
            return False
    
    if from_point == -1:
        if not has_checkers_on_bar(game, player):
            return False
        
        if player == 'white':
            distance = to_point + 1
            if to_point < 0 or to_point >= 24:
                return False
        else:
            distance = 24 - to_point
            if to_point < 0 or to_point >= 24:
                return False
        
        if distance not in game.available_moves:
            return False
        
        dest_point = game.board_state[to_point]
        if dest_point['player'] is not None and dest_point['player'] != player:
            if dest_point['checkers'] > 1:
                return False
        return True
    
    if to_point == 24 or to_point == -1:
        if not all_checkers_in_home_board(game, player):
            return False
        
        if from_point < 0 or from_point >= 24:
            return False
        
        if game.board_state[from_point]['player'] != player:
            return False
        
        if game.board_state[from_point]['checkers'] == 0:
            return False
        
        if player == 'white':
            if to_point != 24:
                return False
            distance = 24 - from_point
        else:
            if to_point != -1:
                return False
            distance = from_point + 1
        
        if distance not in game.available_moves:
            max_die = max(game.available_moves) if game.available_moves else 0
            if distance > max_die:
                return False
            
            if player == 'white':
                for i in range(from_point + 1, 24):
                    if game.board_state[i]['player'] == 'white' and game.board_state[i]['checkers'] > 0:
                        return False
            else:
                for i in range(from_point):
                    if game.board_state[i]['player'] == 'black' and game.board_state[i]['checkers'] > 0:
                        return False
        
        return True
    
    if from_point < 0 or from_point >= 24 or to_point < 0 or to_point >= 24:
        return False
    
    if game.board_state[from_point]['player'] != player:
        return False
    
    if game.board_state[from_point]['checkers'] == 0:
        return False
    
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
        },
        'whiteBar': game.white_bar,
        'blackBar': game.black_bar,
        'whiteOff': game.white_off,
        'blackOff': game.black_off
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
    
    if from_point == -1:
        if player_color == 'white':
            distance = to_point + 1
            game.white_bar -= 1
        else:
            distance = 24 - to_point
            game.black_bar -= 1
        
        if distance in game.available_moves:
            game.available_moves.remove(distance)
        else:
            emit('error', {'message': 'Invalid move - dice value not available'})
            return
        
        dest_point = game.board_state[to_point]
        if dest_point['player'] is not None and dest_point['player'] != player_color:
            if dest_point['checkers'] == 1:
                if player_color == 'white':
                    game.black_bar += 1
                else:
                    game.white_bar += 1
                game.board_state[to_point]['checkers'] = 1
                game.board_state[to_point]['player'] = player_color
        else:
            game.board_state[to_point]['checkers'] += 1
            game.board_state[to_point]['player'] = player_color
    
    elif to_point == 24 or to_point == -1:
        if player_color == 'white':
            distance = 24 - from_point
            game.white_off += 1
        else:
            distance = from_point + 1
            game.black_off += 1
        
        if distance in game.available_moves:
            game.available_moves.remove(distance)
        else:
            max_die = max(game.available_moves) if game.available_moves else 0
            if distance > max_die:
                emit('error', {'message': 'Invalid move - dice value not available'})
                return
            game.available_moves.remove(max_die)
        
        game.board_state[from_point]['checkers'] -= 1
        if game.board_state[from_point]['checkers'] == 0:
            game.board_state[from_point]['player'] = None
    
    else:
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
                if player_color == 'white':
                    game.black_bar += 1
                else:
                    game.white_bar += 1
                game.board_state[to_point]['checkers'] = 1
                game.board_state[to_point]['player'] = player_color
        else:
            game.board_state[to_point]['checkers'] += 1
            game.board_state[to_point]['player'] = player_color
    
    print(f'Piece moved in game {game_id}: {from_point} -> {to_point}')
    
    if game.white_off == 15:
        emit('game-won', {'winner': 'white'}, room=game_id)
    elif game.black_off == 15:
        emit('game-won', {'winner': 'black'}, room=game_id)
    
    emit('board-updated', {
        'boardState': game.board_state,
        'whiteBar': game.white_bar,
        'blackBar': game.black_bar,
        'whiteOff': game.white_off,
        'blackOff': game.black_off
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
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/status')
def status():
    return {
        'status': 'Backgammon Server Running',
        'active_games': len(games)
    }

@app.route('/health')
def health():
    return {'status': 'healthy', 'games': len(games)}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    print(f'Starting Backgammon server on port {port}...')
    print(f'Debug mode: {debug_mode}')
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode)
