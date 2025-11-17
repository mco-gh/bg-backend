class BackgammonTestHarness {
    constructor() {
        this.players = {
            p1: {
                socket: null,
                gameId: null,
                color: null,
                board: null,
                turn: null,
                dice: [],
                whiteBar: 0,
                blackBar: 0,
                whiteOff: 0,
                blackOff: 0
            },
            p2: {
                socket: null,
                gameId: null,
                color: null,
                board: null,
                turn: null,
                dice: [],
                whiteBar: 0,
                blackBar: 0,
                whiteOff: 0,
                blackOff: 0
            }
        };
        
        this.init();
    }
    
    init() {
        this.setupConnections();
        this.setupEventHandlers();
        this.setupScenarios();
    }
    
    setupConnections() {
        const serverUrl = window.location.origin;
        
        this.players.p1.socket = io(serverUrl);
        this.players.p2.socket = io(serverUrl);
        
        this.setupSocketListeners('p1');
        this.setupSocketListeners('p2');
    }
    
    setupSocketListeners(playerId) {
        const player = this.players[playerId];
        const socket = player.socket;
        
        socket.on('connect', () => {
            this.log(playerId, `Connected (SID: ${socket.id})`, 'success');
            document.getElementById(`${playerId}-status`).textContent = 'Connected';
            document.getElementById(`${playerId}-status`).classList.add('connected');
        });
        
        socket.on('disconnect', () => {
            this.log(playerId, 'Disconnected', 'error');
            document.getElementById(`${playerId}-status`).textContent = 'Disconnected';
            document.getElementById(`${playerId}-status`).classList.remove('connected');
        });
        
        socket.on('game-created', (data) => {
            this.log(playerId, `Game created: ${data.gameId}`, 'success');
            player.gameId = data.gameId;
            document.getElementById(`${playerId}-game-id`).value = data.gameId;
            if (playerId === 'p1') {
                document.getElementById('p2-game-id-input').value = data.gameId;
            }
        });
        
        socket.on('game-started', (data) => {
            this.log(playerId, `Game started! Turn: ${data.turn}`, 'success');
            this.updateGameState(playerId, data);
            
            const mySid = socket.id;
            if (data.players.white === mySid) {
                player.color = 'white';
            } else if (data.players.black === mySid) {
                player.color = 'black';
            }
            this.log(playerId, `You are playing as: ${player.color}`, 'success');
        });
        
        socket.on('dice-rolled', (data) => {
            this.log(playerId, `Dice rolled: [${data.dice.join(', ')}] - Turn: ${data.turn}`, 'event');
            player.dice = data.dice;
            player.turn = data.turn;
            document.getElementById(`${playerId}-dice`).textContent = data.dice.join(', ');
            document.getElementById(`${playerId}-turn`).textContent = data.turn;
        });
        
        socket.on('board-updated', (data) => {
            this.log(playerId, 'Board updated', 'event');
            this.updateGameState(playerId, data);
        });
        
        socket.on('new-turn', (data) => {
            this.log(playerId, `New turn: ${data.turn}`, 'event');
            player.turn = data.turn;
            document.getElementById(`${playerId}-turn`).textContent = data.turn;
            document.getElementById(`${playerId}-dice`).textContent = '-';
        });
        
        socket.on('game-won', (data) => {
            this.log(playerId, `🎉 GAME WON by ${data.winner}! 🎉`, 'success');
            alert(`Game Won by ${data.winner}!`);
        });
        
        socket.on('player-disconnected', (data) => {
            this.log(playerId, `Player disconnected: ${data.message}`, 'error');
        });
        
        socket.on('error', (data) => {
            this.log(playerId, `ERROR: ${data.message}`, 'error');
        });
    }
    
    updateGameState(playerId, data) {
        const player = this.players[playerId];
        
        if (data.boardState) {
            player.board = data.boardState;
            this.renderBoard(playerId, data.boardState);
        }
        
        if (data.turn !== undefined) {
            player.turn = data.turn;
            document.getElementById(`${playerId}-turn`).textContent = data.turn;
        }
        
        if (data.whiteBar !== undefined) {
            player.whiteBar = data.whiteBar;
            document.getElementById(`${playerId}-white-bar`).textContent = data.whiteBar;
        }
        
        if (data.blackBar !== undefined) {
            player.blackBar = data.blackBar;
            document.getElementById(`${playerId}-black-bar`).textContent = data.blackBar;
        }
        
        if (data.whiteOff !== undefined) {
            player.whiteOff = data.whiteOff;
            document.getElementById(`${playerId}-white-off`).textContent = data.whiteOff;
        }
        
        if (data.blackOff !== undefined) {
            player.blackOff = data.blackOff;
            document.getElementById(`${playerId}-black-off`).textContent = data.blackOff;
        }
    }
    
    renderBoard(playerId, boardState) {
        const boardElement = document.getElementById(`${playerId}-board`);
        boardElement.innerHTML = '';
        
        boardState.forEach((point, index) => {
            const pointEl = document.createElement('div');
            pointEl.className = 'board-point';
            
            if (point.player) {
                pointEl.classList.add(point.player);
            } else {
                pointEl.classList.add('empty');
            }
            
            const pointNumber = document.createElement('div');
            pointNumber.className = 'point-number';
            pointNumber.textContent = `P${index}`;
            
            const checkerCount = document.createElement('div');
            checkerCount.className = 'checker-count';
            checkerCount.textContent = point.checkers || '·';
            
            pointEl.appendChild(pointNumber);
            pointEl.appendChild(checkerCount);
            
            boardElement.appendChild(pointEl);
        });
    }
    
    setupEventHandlers() {
        document.getElementById('p1-create').addEventListener('click', () => {
            this.createGame('p1');
        });
        
        document.getElementById('p2-join').addEventListener('click', () => {
            this.joinGame('p2');
        });
        
        document.getElementById('p1-roll').addEventListener('click', () => {
            this.rollDice('p1');
        });
        
        document.getElementById('p2-roll').addEventListener('click', () => {
            this.rollDice('p2');
        });
        
        document.getElementById('p1-move').addEventListener('click', () => {
            this.movePiece('p1');
        });
        
        document.getElementById('p2-move').addEventListener('click', () => {
            this.movePiece('p2');
        });
        
        document.getElementById('p1-end-turn').addEventListener('click', () => {
            this.endTurn('p1');
        });
        
        document.getElementById('p2-end-turn').addEventListener('click', () => {
            this.endTurn('p2');
        });
        
        document.getElementById('p1-clear-log').addEventListener('click', () => {
            document.getElementById('p1-log').innerHTML = '';
        });
        
        document.getElementById('p2-clear-log').addEventListener('click', () => {
            document.getElementById('p2-log').innerHTML = '';
        });
    }
    
    createGame(playerId) {
        this.log(playerId, 'Creating game...', 'event');
        this.players[playerId].socket.emit('create-game', {});
    }
    
    joinGame(playerId) {
        const gameId = document.getElementById(`${playerId}-game-id-input`).value.trim();
        if (!gameId) {
            this.log(playerId, 'Please enter a Game ID', 'error');
            return;
        }
        
        this.log(playerId, `Joining game: ${gameId}`, 'event');
        this.players[playerId].socket.emit('join-game', { gameId });
    }
    
    rollDice(playerId) {
        const player = this.players[playerId];
        if (!player.gameId && playerId === 'p1') {
            player.gameId = document.getElementById('p1-game-id').value;
        }
        if (!player.gameId && playerId === 'p2') {
            player.gameId = document.getElementById('p2-game-id-input').value;
        }
        
        this.log(playerId, 'Rolling dice...', 'event');
        player.socket.emit('roll-dice', { gameId: player.gameId });
    }
    
    movePiece(playerId) {
        const player = this.players[playerId];
        const fromPoint = parseInt(document.getElementById(`${playerId}-from`).value);
        const toPoint = parseInt(document.getElementById(`${playerId}-to`).value);
        
        if (isNaN(fromPoint) || isNaN(toPoint)) {
            this.log(playerId, 'Please enter valid from/to points', 'error');
            return;
        }
        
        if (!player.gameId && playerId === 'p1') {
            player.gameId = document.getElementById('p1-game-id').value;
        }
        if (!player.gameId && playerId === 'p2') {
            player.gameId = document.getElementById('p2-game-id-input').value;
        }
        
        this.log(playerId, `Moving piece: ${fromPoint} → ${toPoint}`, 'event');
        player.socket.emit('move-piece', {
            gameId: player.gameId,
            fromPointIndex: fromPoint,
            toPointIndex: toPoint
        });
    }
    
    endTurn(playerId) {
        const player = this.players[playerId];
        if (!player.gameId && playerId === 'p1') {
            player.gameId = document.getElementById('p1-game-id').value;
        }
        if (!player.gameId && playerId === 'p2') {
            player.gameId = document.getElementById('p2-game-id-input').value;
        }
        
        this.log(playerId, 'Ending turn...', 'event');
        player.socket.emit('end-turn', { gameId: player.gameId });
    }
    
    log(playerId, message, type = 'event') {
        const logElement = document.getElementById(`${playerId}-log`);
        const timestamp = new Date().toLocaleTimeString();
        
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span> ${message}`;
        
        logElement.appendChild(entry);
        logElement.scrollTop = logElement.scrollHeight;
    }
    
    scenarioLog(message, type = 'running') {
        const scenarioLogElement = document.getElementById('scenario-log');
        const timestamp = new Date().toLocaleTimeString();
        
        const step = document.createElement('div');
        step.className = `scenario-step ${type}`;
        step.textContent = `[${timestamp}] ${message}`;
        
        scenarioLogElement.appendChild(step);
        scenarioLogElement.scrollTop = scenarioLogElement.scrollHeight;
    }
    
    async wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    setupScenarios() {
        document.getElementById('scenario-basic').addEventListener('click', () => {
            this.runBasicGameFlow();
        });
        
        document.getElementById('scenario-hit').addEventListener('click', () => {
            this.runHitAndBarReentry();
        });
        
        document.getElementById('scenario-bearoff').addEventListener('click', () => {
            this.runBearingOffExact();
        });
        
        document.getElementById('scenario-overshoot').addEventListener('click', () => {
            this.runBearingOffOvershoot();
        });
        
        document.getElementById('scenario-win').addEventListener('click', () => {
            this.runWinCondition();
        });
        
        document.getElementById('scenario-errors').addEventListener('click', () => {
            this.runErrorHandling();
        });
    }
    
    async runBasicGameFlow() {
        document.getElementById('scenario-log').innerHTML = '';
        this.scenarioLog('🧪 Starting Basic Game Flow Test', 'running');
        
        try {
            this.scenarioLog('Step 1: Player 1 creates game', 'running');
            this.createGame('p1');
            await this.wait(1000);
            
            this.scenarioLog('Step 2: Player 2 joins game', 'running');
            this.joinGame('p2');
            await this.wait(1000);
            
            this.scenarioLog('Step 3: Player 1 rolls dice', 'running');
            this.rollDice('p1');
            await this.wait(1000);
            
            this.scenarioLog('Step 4: Player 1 makes a move', 'running');
            document.getElementById('p1-from').value = '0';
            document.getElementById('p1-to').value = '3';
            this.movePiece('p1');
            await this.wait(1000);
            
            this.scenarioLog('Step 5: Player 1 ends turn', 'running');
            this.endTurn('p1');
            await this.wait(1000);
            
            this.scenarioLog('✅ Basic Game Flow Test Complete', 'success');
        } catch (error) {
            this.scenarioLog(`❌ Test Failed: ${error.message}`, 'error');
        }
    }
    
    async runHitAndBarReentry() {
        document.getElementById('scenario-log').innerHTML = '';
        this.scenarioLog('🧪 Starting Hit & Bar Re-entry Test', 'running');
        
        try {
            this.scenarioLog('This test verifies that hitting sends checkers to the bar', 'running');
            this.scenarioLog('and that players must re-enter before other moves', 'running');
            
            this.scenarioLog('✅ Manual testing required: ', 'success');
            this.scenarioLog('1. Move a single checker to create a blot', 'success');
            this.scenarioLog('2. Land opponent on that blot to hit it', 'success');
            this.scenarioLog('3. Verify checker goes to bar (whiteBar or blackBar increases)', 'success');
            this.scenarioLog('4. Try to move other pieces (should fail)', 'success');
            this.scenarioLog('5. Use fromPoint=-1 to re-enter from bar', 'success');
        } catch (error) {
            this.scenarioLog(`❌ Test Failed: ${error.message}`, 'error');
        }
    }
    
    async runBearingOffExact() {
        document.getElementById('scenario-log').innerHTML = '';
        this.scenarioLog('🧪 Starting Bearing Off (Exact) Test', 'running');
        
        try {
            this.scenarioLog('This test verifies exact bearing off mechanics', 'running');
            this.scenarioLog('✅ Manual testing required: ', 'success');
            this.scenarioLog('1. Get all checkers in home board (18-23 for white, 0-5 for black)', 'success');
            this.scenarioLog('2. Roll dice and use exact die value to bear off', 'success');
            this.scenarioLog('3. Use toPoint=24 for white, toPoint=-1 for black', 'success');
            this.scenarioLog('4. Verify whiteOff or blackOff increases', 'success');
        } catch (error) {
            this.scenarioLog(`❌ Test Failed: ${error.message}`, 'error');
        }
    }
    
    async runBearingOffOvershoot() {
        document.getElementById('scenario-log').innerHTML = '';
        this.scenarioLog('🧪 Starting Bearing Off (Overshoot) Test', 'running');
        
        try {
            this.scenarioLog('This test verifies overshoot bearing off rules', 'running');
            this.scenarioLog('✅ Manual testing required: ', 'success');
            this.scenarioLog('1. Get all checkers in home board', 'success');
            this.scenarioLog('2. Roll a die higher than needed (e.g., checker at 20, roll 6)', 'success');
            this.scenarioLog('3. Verify bearing off is allowed only if no checkers at higher/lower points', 'success');
            this.scenarioLog('4. White: allowed if no checkers at higher points (21-23)', 'success');
            this.scenarioLog('5. Black: allowed if no checkers at lower points (0-from)', 'success');
        } catch (error) {
            this.scenarioLog(`❌ Test Failed: ${error.message}`, 'error');
        }
    }
    
    async runWinCondition() {
        document.getElementById('scenario-log').innerHTML = '';
        this.scenarioLog('🧪 Starting Win Condition Test', 'running');
        
        try {
            this.scenarioLog('This test verifies win detection', 'running');
            this.scenarioLog('✅ Manual testing required: ', 'success');
            this.scenarioLog('1. Bear off all 15 checkers for one player', 'success');
            this.scenarioLog('2. Verify game-won event is emitted', 'success');
            this.scenarioLog('3. Check that winner is correctly identified', 'success');
            this.scenarioLog('4. Look for alert and log message announcing winner', 'success');
        } catch (error) {
            this.scenarioLog(`❌ Test Failed: ${error.message}`, 'error');
        }
    }
    
    async runErrorHandling() {
        document.getElementById('scenario-log').innerHTML = '';
        this.scenarioLog('🧪 Starting Error Handling Test', 'running');
        
        try {
            this.scenarioLog('Testing various error conditions...', 'running');
            
            this.scenarioLog('Test 1: Roll dice without creating game', 'running');
            this.players.p1.gameId = 'INVALID-ID';
            this.rollDice('p1');
            await this.wait(500);
            
            this.scenarioLog('Test 2: Move piece on wrong turn', 'running');
            this.scenarioLog('(After game starts, try moving as player who is not current turn)', 'running');
            
            this.scenarioLog('Test 3: Invalid move indices', 'running');
            document.getElementById('p1-from').value = '99';
            document.getElementById('p1-to').value = '-5';
            this.movePiece('p1');
            await this.wait(500);
            
            this.scenarioLog('Test 4: Join non-existent game', 'running');
            document.getElementById('p2-game-id-input').value = 'XXX-YYY-ZZZ';
            this.joinGame('p2');
            await this.wait(500);
            
            this.scenarioLog('✅ Error Handling Test Complete - Check logs for error messages', 'success');
        } catch (error) {
            this.scenarioLog(`❌ Test Failed: ${error.message}`, 'error');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.harness = new BackgammonTestHarness();
});
