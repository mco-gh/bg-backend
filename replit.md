# Backgammon Backend Server

## Overview
This is a real-time Flask-SocketIO backend server for a two-player online backgammon game. The server manages game state, player connections, and real-time updates between clients using WebSocket communication.

**Current State:** Production-ready backend server running on port 5000

## Recent Changes
*November 17, 2025:* Complete backgammon implementation with all official rules
- Created Flask-SocketIO server with complete backgammon game logic
- Implemented all Socket.IO event handlers (create-game, join-game, roll-dice, move-piece, end-turn)
- Added server-authoritative game state management
- Implemented human-readable Game ID generation (e.g., ABC-DEF-GHI)
- Set up player disconnect detection and handling
- Implemented complete backgammon mechanics:
  - Bar positions for hit checkers (white_bar, black_bar)
  - Off positions for borne-off checkers (white_off, black_off)
  - Hit logic that sends opponent checkers to the bar
  - Forced re-entry from bar before other moves
  - Bearing off with proper validation (home board requirement, overshoot rules)
  - Win detection when a player bears off all 15 checkers
- Fixed security issues (debug mode off in production, SESSION_SECRET warning)
- Fixed critical bearing-off validation bug for correct overshoot handling

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
- Each game session tracks: board state, turn, players, dice, available moves, bar counts, off counts

**Socket.IO Events Implemented:**
- Client → Server: `create-game`, `join-game`, `roll-dice`, `move-piece`, `end-turn`
- Server → Client: `game-created`, `game-started`, `dice-rolled`, `board-updated`, `new-turn`, `player-disconnected`, `game-won`, `error`

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
The `is_valid_move()` function handles three types of moves:

**1. Re-entry from Bar (from_point = -1):**
- Required when player has checkers on bar (forced before other moves)
- Validates dice value matches distance
- Checks destination allows entry (opponent has ≤1 checker)

**2. Regular Moves (0-23 → 0-23):**
- Point indices valid (0-23)
- Player owns the piece being moved
- Direction is correct (white moves up, black moves down)
- Distance matches a die value
- Destination point allows the move (opponent has ≤1 checker)

**3. Bearing Off (to_point = 24 for white, -1 for black):**
- Only allowed when all checkers are in home board (18-23 for white, 0-5 for black)
- Validates dice value or allows overshoot if no checkers at further points
- White overshoot: allowed only if no white checkers at higher points
- Black overshoot: allowed only if no black checkers at lower points

### Session Management
- Each game gets a unique room in Socket.IO
- Players join rooms to receive game-specific broadcasts
- Sessions are deleted when a player disconnects
- SID tracking prevents players from joining multiple games

### Backgammon Mechanics
- **Hitting:** When a checker lands on an opponent's blot (single checker), the opponent's checker is sent to the bar
- **Bar Re-entry:** Players with checkers on the bar must re-enter them before making other moves
- **Bearing Off:** Players can only bear off when all 15 checkers are in their home board
- **Overshoot Bearing Off:** Players can use a higher die than needed only if no checkers remain at further points
- **Win Condition:** First player to bear off all 15 checkers wins

## Future Enhancements
- Persistent game state storage with database integration
- Game history and move replay functionality
- Spectator mode for watching ongoing games
- Matchmaking system for random opponent pairing
- Player statistics and leaderboard
