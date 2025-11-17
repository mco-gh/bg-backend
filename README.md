# Backgammon Backend Server

A real-time Flask-SocketIO backend server for a two-player online backgammon game.

## Features

- Real-time WebSocket communication using Socket.IO
- Server-authoritative game state to prevent cheating
- Human-readable game IDs (e.g., ABC-DEF-GHI)
- Support for two players per game session
- Complete backgammon game logic including:
  - Dice rolling
  - Move validation
  - Turn management
  - Player disconnect handling

## Technology Stack

- **Language:** Python 3.11
- **Framework:** Flask
- **Real-time Communication:** Flask-SocketIO
- **Async Server:** Eventlet

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Setup (Optional)

Create a `.env` file in the project root:

```
SESSION_SECRET=your-secret-key-here
PORT=5000
```

If not provided, defaults will be used.

## Running the Server

### Development Mode

Start the server with:

```bash
python app.py
```

The server will start on `http://0.0.0.0:5000` by default.

### Production Deployment

The server is configured for production deployment on Replit using:
- **Deployment Type**: Reserved VM (always running, required for WebSocket connections)
- **Web Server**: Gunicorn with Eventlet worker class
- **Run Command**: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 --reuse-port app:app`

The deployment automatically uses the `/health` endpoint for health checks.

## Testing the Backend

### Web Test Harness

A comprehensive web-based test harness is available at the root URL (`http://localhost:5000/`). The test harness includes:

**Features:**
- **Dual-Client Interface**: Test both players simultaneously in a single browser window
- **Real-time Board Visualization**: See the complete game state including all 24 points
- **Bar and Off Counters**: Track hit checkers and borne-off pieces
- **Event Logging**: Monitor all Socket.IO events and server responses
- **Manual Controls**: Create games, join games, roll dice, move pieces, and end turns
- **Automated Test Scenarios**: 
  - Basic Game Flow
  - Hit & Bar Re-entry
  - Bearing Off (Exact)
  - Bearing Off (Overshoot)
  - Win Condition
  - Error Handling

**How to Use:**
1. Open `http://localhost:5000/` in your browser
2. Click "Create Game" on Player 1's panel
3. Copy the Game ID to Player 2's input field and click "Join Game"
4. Use the Roll Dice, Move Piece, and End Turn controls to play
5. Or run automated test scenarios with the scenario buttons at the bottom

**Testing All Features:**
- **Regular Moves**: Enter point indices (0-23) in the From/To fields
- **Bar Entry**: Use `-1` as the From point to move from the bar
- **Bearing Off**: Use `24` (white) or `-1` (black) as the To point to bear off
- **Monitor State**: Watch the bar/off counters and event logs to verify mechanics

## API Documentation

### Socket.IO Events

#### Client → Server Events

**1. `create-game`**
- **Payload:** `{}`
- **Description:** Creates a new game session and returns a unique game ID
- **Response:** `game-created` event with `{ "gameId": "ABC-DEF-GHI" }`

**2. `join-game`**
- **Payload:** `{ "gameId": "ABC-DEF-GHI" }`
- **Description:** Joins an existing game as the second player
- **Response:** `game-started` event to both players with initial board state

**3. `roll-dice`**
- **Payload:** `{ "gameId": "ABC-DEF-GHI" }`
- **Description:** Rolls two dice for the current player's turn
- **Response:** `dice-rolled` event with `{ "dice": [1-6, 1-6], "turn": "white"|"black" }`

**4. `move-piece`**
- **Payload:** `{ "gameId": "ABC-DEF-GHI", "fromPointIndex": -1 to 23, "toPointIndex": -1 to 24 }`
- **Description:** Moves a checker from one point to another
  - Use `fromPointIndex: -1` to move from the bar
  - Use `toPointIndex: 24` (white) or `-1` (black) to bear off
- **Response:** `board-updated` event with new board state

**5. `end-turn`**
- **Payload:** `{ "gameId": "ABC-DEF-GHI" }`
- **Description:** Ends the current player's turn
- **Response:** `new-turn` event with `{ "turn": "white"|"black" }`

#### Server → Client Events

**1. `game-created`**
- **Payload:** `{ "gameId": "ABC-DEF-GHI" }`
- **Description:** Confirms game creation with unique ID

**2. `game-started`**
- **Payload:** `{ "boardState": [...], "turn": "white", "players": { "white": "sid1", "black": "sid2" }, "whiteBar": 0, "blackBar": 0, "whiteOff": 0, "blackOff": 0 }`
- **Description:** Signals that both players are connected

**3. `dice-rolled`**
- **Payload:** `{ "dice": [number, number], "turn": "white"|"black" }`
- **Description:** Broadcasts dice roll results

**4. `board-updated`**
- **Payload:** `{ "boardState": [...], "whiteBar": int, "blackBar": int, "whiteOff": int, "blackOff": int }`
- **Description:** Broadcasts updated board state after a move, including bar and off counts

**5. `new-turn`**
- **Payload:** `{ "turn": "white"|"black" }`
- **Description:** Signals turn change

**6. `player-disconnected`**
- **Payload:** `{ "message": "The other player has disconnected" }`
- **Description:** Notifies when opponent disconnects

**7. `error`**
- **Payload:** `{ "message": "Error description" }`
- **Description:** Sends error messages for invalid actions

**8. `game-won`**
- **Payload:** `{ "winner": "white"|"black" }`
- **Description:** Announces when a player has borne off all 15 checkers and won the game

### HTTP Endpoints

**GET `/`**
- Returns server status and number of active games

**GET `/health`**
- Health check endpoint

## Game State Structure

### Board State
The board is represented as an array of 24 `PointState` objects:

```python
{
  "checkers": int,      # Number of checkers on this point
  "player": "white" | "black" | None  # Owner of the checkers
}
```

### Bar and Off Positions
- **Bar:** Checkers that have been hit are placed on the bar
  - `whiteBar`: Count of white checkers on the bar
  - `blackBar`: Count of black checkers on the bar
  - Players must re-enter from the bar before making other moves
  - Use `fromPointIndex: -1` to move from bar

- **Off:** Checkers that have been borne off (removed from the board)
  - `whiteOff`: Count of white checkers borne off
  - `blackOff`: Count of black checkers borne off
  - Players can only bear off when all checkers are in their home board
  - Use `toPointIndex: 24` (white) or `-1` (black) to bear off
  - Game is won when a player bears off all 15 checkers

### Initial Board Setup
- Points are indexed 0-23
- White pieces start at points: 0 (2), 11 (5), 16 (3), 18 (5)
- Black pieces start at points: 23 (2), 12 (5), 7 (3), 5 (5)
- White's home board: points 18-23
- Black's home board: points 0-5

## Development

### Project Structure

```
.
├── app.py              # Main Flask-SocketIO server
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .env               # Environment variables (optional)
```

### Testing with a Client

Connect to the server using a Socket.IO client:

```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000');

// Create a game
socket.emit('create-game', {});

socket.on('game-created', (data) => {
  console.log('Game ID:', data.gameId);
});
```

## License

This project is provided as-is for educational and development purposes.
