# Backgammon Backend Server

## Overview
This is a real-time Flask-SocketIO backend server for a two-player online backgammon game. The server manages game state, player connections, and real-time updates between clients using WebSocket communication.

**Current State:** Production-ready backend server running on port 5000

## Recent Changes
*November 17, 2025:* Initial implementation completed
- Created Flask-SocketIO server with complete backgammon game logic
- Implemented all Socket.IO event handlers (create-game, join-game, roll-dice, move-piece, end-turn)
- Added server-authoritative game state management
- Implemented human-readable Game ID generation (e.g., ABC-DEF-GHI)
- Set up player disconnect detection and handling
- Added comprehensive move validation logic

## Project Architecture

### Technology Stack
- **Language:** Python 3.11
- **Framework:** Flask 3.0.0
- **Real-time Communication:** Flask-SocketIO 5.3.5
- **Async Server:** Eventlet 0.33.3

### File Structure
```
.
├── app.py              # Main Flask-SocketIO server with all game logic
├── requirements.txt    # Python dependencies
├── README.md          # Setup and API documentation
├── replit.md          # Project overview (this file)
└── .gitignore         # Git ignore patterns
```

### Key Components

**app.py:**
- Flask and SocketIO initialization
- In-memory game session storage using dictionary
- Game ID generation (human-readable format: ABC-DEF-GHI)
- Initial board setup with standard backgammon configuration
- Socket.IO event handlers for all game operations
- Move validation logic
- Player disconnect handling

**Game State Management:**
- Games stored in-memory: `games: Dict[str, GameSession]`
- Session ID to Game ID mapping: `sid_to_game: Dict[str, str]`
- Each game session tracks: board state, turn, players, dice, available moves

**Socket.IO Events Implemented:**
- Client → Server: `create-game`, `join-game`, `roll-dice`, `move-piece`, `end-turn`
- Server → Client: `game-created`, `game-started`, `dice-rolled`, `board-updated`, `new-turn`, `player-disconnected`, `error`

### Board Representation
The board is an array of 24 points (indices 0-23):
- Each point has: `{checkers: int, player: 'white' | 'black' | None}`
- Standard backgammon initial setup implemented
- White starts at points: 0(2), 11(5), 16(3), 18(5)
- Black starts at points: 23(2), 12(5), 7(3), 5(5)

## Running the Server

**Start Server:**
```bash
python app.py
```
The server runs on http://0.0.0.0:5000

**Workflow:** 
- Name: `backgammon-server`
- Command: `python app.py`
- Port: 5000 (WebView)

## API Endpoints

**HTTP:**
- `GET /` - Server status and active games count
- `GET /health` - Health check

**WebSocket Events:**
See README.md for complete Socket.IO event documentation

## Development Notes

### Move Validation
The `is_valid_move()` function checks:
- Dice values available
- Point indices valid (0-23)
- Player owns the piece being moved
- Direction is correct (white moves up, black moves down)
- Distance matches a die value
- Destination point allows the move (opponent has ≤1 checker)

### Session Management
- Each game gets a unique room in Socket.IO
- Players join rooms to receive game-specific broadcasts
- Sessions are deleted when a player disconnects
- SID tracking prevents players from joining multiple games

## Future Enhancements
- Persistent game state storage with database integration
- Game history and move replay functionality
- Spectator mode for watching ongoing games
- Matchmaking system for random opponent pairing
- Player statistics and leaderboard
