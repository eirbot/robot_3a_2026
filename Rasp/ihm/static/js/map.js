// map.js corrigé — Mise à jour de la carte en utilisant l'événement 'robot_position'

let ctxMap = null;
let imgTable = new Image();
let imgRobot = new Image();
let robotPos = { x: 1500, y: 1000, theta: 0 };

// Initialisation de la page carte
document.addEventListener('DOMContentLoaded', () => {
    initMapPage();
});

function initMapPage() {
    const canvas = document.getElementById('mapCanvas');
    ctxMap = canvas.getContext('2d');
    imgTable.src = '/static/img/table_coupe_2026.png';
    imgRobot.src = '/static/img/robot.png';
    imgTable.onload = drawMap;
    imgRobot.onload = drawMap;
    // On s’enregistre auprès du serveur pour recevoir la position
    socket.emit('map_connect');
}

// Réception de la position du robot
socket.on('robot_position', (pos) => {
    robotPos = pos;
    const info = document.getElementById('pos-text');
    if (info) {
        info.innerText = `X: ${pos.x.toFixed(0)} Y: ${pos.y.toFixed(0)} θ: ${pos.theta.toFixed(1)}°`;
    }
    drawMap();
});

// Dessin de la table et du robot
function drawMap() {
    if (!ctxMap) return;
    const canvas = document.getElementById('mapCanvas');
    const w = canvas.width;
    const h = canvas.height;
    ctxMap.clearRect(0, 0, w, h);
    if (imgTable.complete && imgTable.naturalWidth > 0) ctxMap.drawImage(imgTable, 0, 0, w, h);
    else {
        ctxMap.fillStyle = '#222';
        ctxMap.fillRect(0, 0, w, h);
    }
    if (imgRobot.complete && imgRobot.naturalWidth > 0) {
        const scaleX = w / 3000;
        const scaleY = h / 2000;
        const px = robotPos.x * scaleX;
        const py = h - (robotPos.y * scaleY);
        const size = 300 * scaleX;
        ctxMap.save();
        ctxMap.translate(px, py);
        ctxMap.rotate(-robotPos.theta * Math.PI / 180);
        ctxMap.drawImage(imgRobot, -size / 2, -size / 2, size, size);
        ctxMap.restore();
    }
}
