const socket = io();

const logContainer = document.getElementById('logs');
const userInput = document.getElementById('user-input');
const clockElement = document.getElementById('clock');
const greetingText = document.getElementById('greeting-text');

function updateClock() {
    const now = new Date();
    clockElement.innerText = now.toLocaleTimeString();
}
setInterval(updateClock, 1000);

socket.on('log', (data) => {
    const p = document.createElement('p');
    p.innerText = `[${new Date().toLocaleTimeString()}] ${data.message}`;
    if (data.type === 'system') p.classList.add('dim');
    logContainer.appendChild(p);
    logContainer.scrollTop = logContainer.scrollHeight;
});

socket.on('stats', (data) => {
    document.getElementById('cpu-load').innerText = data.cpu + '%';
    document.getElementById('mem-load').innerText = data.mem + '%';
});

socket.on('browser_update', (data) => {
    document.getElementById('browser-status').innerText = data.status;
    if (data.screenshot) {
        const img = document.getElementById('browser-shot');
        img.src = 'data:image/png;base64,' + data.screenshot;
        img.style.display = 'block';
        document.getElementById('browser-status').style.display = 'none';
    }
});

socket.on('command_result', (data) => {
    greetingText.innerText = data.response;
});

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const cmd = userInput.value;
        socket.emit('command', { message: cmd });
        userInput.value = '';
        
        const p = document.createElement('p');
        p.style.color = '#FFB347';
        p.innerText = `> ${cmd}`;
        logContainer.appendChild(p);
    }
});
