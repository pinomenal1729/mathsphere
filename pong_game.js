// Canvas and context
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Game objects
const paddleWidth = 10;
const paddleHeight = 80;
const ballSize = 8;

let player = {
    x: 10,
    y: canvas.height / 2 - paddleHeight / 2,
    width: paddleWidth,
    height: paddleHeight,
    dy: 0,
    speed: 6
};

let computer = {
    x: canvas.width - paddleWidth - 10,
    y: canvas.height / 2 - paddleHeight / 2,
    width: paddleWidth,
    height: paddleHeight,
    dy: 0,
    speed: 4.5
};

let ball = {
    x: canvas.width / 2,
    y: canvas.height / 2,
    dx: -5,
    dy: 5,
    radius: ballSize,
    maxSpeed: 8
};

let score = {
    player: 0,
    computer: 0
};

// Game state
let gameRunning = true;
const winScore = 5;

// Keyboard input
const keys = {};
window.addEventListener('keydown', (e) => {
    keys[e.key] = true;
});

window.addEventListener('keyup', (e) => {
    keys[e.key] = false;
});

// Mouse input
canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseY = e.clientY - rect.top;
    player.y = Math.max(0, Math.min(mouseY - paddleHeight / 2, canvas.height - paddleHeight));
});

// Update player paddle with arrow keys
function updatePlayer() {
    if (keys['ArrowUp'] && player.y > 0) {
        player.y -= player.speed;
    }
    if (keys['ArrowDown'] && player.y < canvas.height - paddleHeight) {
        player.y += player.speed;
    }
}

// Update computer paddle (AI)
function updateComputer() {
    const computerCenter = computer.y + paddleHeight / 2;
    const ballCenter = ball.y;
    
    // AI difficulty: track the ball with some smoothing
    const difference = ballCenter - computerCenter;
    const threshold = paddleHeight / 3; // Dead zone for more human-like play
    
    if (difference > threshold) {
        computer.y = Math.min(computer.y + computer.speed, canvas.height - paddleHeight);
    } else if (difference < -threshold) {
        computer.y = Math.max(computer.y - computer.speed, 0);
    }
}

// Update ball physics
function updateBall() {
    ball.x += ball.dx;
    ball.y += ball.dy;

    // Top and bottom wall collision
    if (ball.y - ball.radius < 0 || ball.y + ball.radius > canvas.height) {
        ball.dy = -ball.dy;
        ball.y = Math.max(ball.radius, Math.min(canvas.height - ball.radius, ball.y));
    }

    // Paddle collision - Player
    if (
        ball.x - ball.radius < player.x + player.width &&
        ball.y > player.y &&
        ball.y < player.y + player.height &&
        ball.dx < 0
    ) {
        ball.dx = -ball.dx;
        // Add spin based on where the ball hits the paddle
        const hitPos = (ball.y - (player.y + paddleHeight / 2)) / (paddleHeight / 2);
        ball.dy += hitPos * 3;
        ball.x = player.x + player.width + ball.radius;
    }

    // Paddle collision - Computer
    if (
        ball.x + ball.radius > computer.x &&
        ball.y > computer.y &&
        ball.y < computer.y + computer.height &&
        ball.dx > 0
    ) {
        ball.dx = -ball.dx;
        // Add spin based on where the ball hits the paddle
        const hitPos = (ball.y - (computer.y + paddleHeight / 2)) / (paddleHeight / 2);
        ball.dy += hitPos * 3;
        ball.x = computer.x - ball.radius;
    }

    // Limit ball speed
    const speed = Math.sqrt(ball.dx * ball.dx + ball.dy * ball.dy);
    if (speed > ball.maxSpeed) {
        ball.dx = (ball.dx / speed) * ball.maxSpeed;
        ball.dy = (ball.dy / speed) * ball.maxSpeed;
    }

    // Score points
    if (ball.x < 0) {
        score.computer++;
        resetBall();
    } else if (ball.x > canvas.width) {
        score.player++;
        resetBall();
    }

    // Check win condition
    if (score.player >= winScore || score.computer >= winScore) {
        gameRunning = false;
    }
}

// Reset ball to center
function resetBall() {
    ball.x = canvas.width / 2;
    ball.y = canvas.height / 2;
    const angle = (Math.random() - 0.5) * Math.PI / 3;
    const speed = 5;
    ball.dx = speed * Math.cos(angle) * (Math.random() > 0.5 ? 1 : -1);
    ball.dy = speed * Math.sin(angle);
}

// Draw functions
function drawPaddle(paddle) {
    ctx.fillStyle = '#00ff88';
    ctx.fillRect(paddle.x, paddle.y, paddle.width, paddle.height);
    ctx.strokeStyle = '#00ffff';
    ctx.lineWidth = 2;
    ctx.strokeRect(paddle.x, paddle.y, paddle.width, paddle.height);
}

function drawBall() {
    ctx.fillStyle = '#ffff00';
    ctx.beginPath();
    ctx.arc(ball.x, ball.y, ball.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#ffaa00';
    ctx.lineWidth = 2;
    ctx.stroke();
}

function drawCenterLine() {
    ctx.strokeStyle = 'rgba(0, 255, 136, 0.3)';
    ctx.setLineDash([10, 10]);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(canvas.width / 2, 0);
    ctx.lineTo(canvas.width / 2, canvas.height);
    ctx.stroke();
    ctx.setLineDash([]);
}

function drawGame() {
    // Clear canvas
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw center line
    drawCenterLine();

    // Draw paddles and ball
    drawPaddle(player);
    drawPaddle(computer);
    drawBall();

    // Draw game over message
    if (!gameRunning) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#00ff88';
        ctx.font = 'bold 48px Arial';
        ctx.textAlign = 'center';
        
        const winner = score.player > score.computer ? 'YOU WIN! 🏆' : 'GAME OVER!';
        ctx.fillText(winner, canvas.width / 2, canvas.height / 2 - 30);
        
        ctx.font = '24px Arial';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('Click Reset Game to play again', canvas.width / 2, canvas.height / 2 + 30);
    }
}

function updateScore() {
    document.getElementById('playerScore').textContent = score.player;
    document.getElementById('computerScore').textContent = score.computer;
}

// Main game loop
function gameLoop() {
    if (gameRunning) {
        updatePlayer();
        updateComputer();
        updateBall();
    }
    
    updateScore();
    drawGame();
    requestAnimationFrame(gameLoop);
}

// Reset game
function resetGame() {
    score.player = 0;
    score.computer = 0;
    gameRunning = true;
    resetBall();
    player.y = canvas.height / 2 - paddleHeight / 2;
    computer.y = canvas.height / 2 - paddleHeight / 2;
    updateScore();
}

// Start the game
gameLoop();