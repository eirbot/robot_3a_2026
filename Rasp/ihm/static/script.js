const socket = io();

// Globales
let currentChart = null;
let ctxMap = null;
let imgTable = new Image();
let imgRobot = new Image();
let robotPos = { x: 1500, y: 1000, theta: 0 };
let localState = {};

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById('currentChart')) initDebugPage();
    if (document.getElementById('mapCanvas')) initMapPage();
});

// --- SOCKET IO ---
socket.on('state_update', (state) => {
    localState = state;
    document.body.classList.remove('mode-BLEUE', 'mode-JAUNE');
    document.body.classList.add('mode-' + state.team);

    if (state.match_finished) document.body.classList.add('breathing-' + state.team);
    else document.body.classList.remove('breathing-BLEUE', 'breathing-JAUNE');

    if (document.getElementById('score')) updateIndexPage(state);
    if (document.getElementById('chk-lidar')) updateDebugUI(state);
});

socket.on('sys_info', (data) => {
    const d = document.getElementById('sys-info');
    if(d) d.innerHTML = `IP: ${data.ip} | Bat: ${data.volt}<br>CPU: ${data.cpu}`;
    if (currentChart) updateChart(data);
    
    // MISE A JOUR DES STATUTS PERIPHERIQUES
    if (data.devs && document.getElementById('status-lidar')) {
        updateDevStatus('lidar', data.devs.lidar);
        updateDevStatus('esp_motors', data.devs.esp_motors);
        updateDevStatus('esp_arms', data.devs.esp_arms);
        updateDevStatus('camera', data.devs.camera);
    }
});

// RECEPTION DES LOGS
socket.on('new_log', (data) => {
    const container = document.getElementById('log-container');
    if (!container) return; // Si on n'est pas sur la page debug

    // Création de la ligne HTML
    const div = document.createElement('div');
    div.className = "log-line";
    
    // Définition de la classe couleur (info ou error)
    const typeClass = (data.type === 'error') ? 'log-error' : 'log-info';
    
    div.innerHTML = `<span class="log-time">${data.time}</span> <span class="${typeClass}">${data.msg}</span>`;
    
    // Ajout et Scroll automatique vers le bas
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    
    // Limite à 100 lignes pour ne pas faire laguer le navigateur
    if (container.childElementCount > 100) {
        container.removeChild(container.firstChild);
    }
});

socket.on('robot_position', (pos) => {
    robotPos = pos;
    if (ctxMap) drawMap();
});

// --- INDEX ---
function updateIndexPage(state) {
    document.getElementById('score').innerText = state.score_current;
    document.getElementById('timer').innerText = state.timer_str;
    
    const stratDiv = document.getElementById('strat-display');
    if(stratDiv) stratDiv.innerText = (state.strat_mode === 'STATIC') ? `#${state.strat_id} (${state.score_current}pts)` : "Dynamique";
    
    const teamDiv = document.getElementById('team-display');
    teamDiv.innerText = "ÉQUIPE " + state.team;
    teamDiv.className = "team-box team-" + state.team;

    const tirDiv = document.getElementById('tirette-status');
    if(tirDiv) {
        tirDiv.className = "tirette-box status-" + state.tirette.toLowerCase();
        if(state.tirette === "ARMED") tirDiv.innerText = "TIRETTE: ARMÉE (PRÊT)";
        else if(state.tirette === "TRIGGERED") tirDiv.innerText = "TIRETTE: TIRÉE (GO)";
        else tirDiv.innerText = "TIRETTE: NON ARMÉE";
    }

    // --- AJOUT POUR LE BADGE FSM ---
    const fsmBadge = document.getElementById('fsm-display');
    if(fsmBadge) {
        fsmBadge.innerText = state.fsm_state || "INIT";
        fsmBadge.className = "badge"; // reset classes
        if(state.fsm_state === "RUNNING") fsmBadge.classList.add("badge-run");
        else if(state.fsm_state === "FINISHED") fsmBadge.classList.add("badge-end");
        else fsmBadge.classList.add("badge-wait");
    }
    // -----------------------------

    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const btnReset = document.getElementById('btn-reset');
    const otherControls = document.querySelectorAll('.controls button:not(#btn-start):not(#btn-stop):not(#btn-reset), .controls a');

    if (state.match_finished) {
        btnStart.classList.add('hidden'); btnStop.classList.add('hidden'); btnReset.classList.remove('hidden');
        otherControls.forEach(el => el.classList.add('hidden'));
    } 
    else if (state.match_running) {
        btnStart.classList.add('hidden'); btnStop.classList.remove('hidden'); btnReset.classList.add('hidden');
        otherControls.forEach(el => el.classList.add('hidden'));
    }
    else {
        btnStart.classList.remove('hidden'); btnStop.classList.add('hidden'); btnReset.classList.add('hidden');
        otherControls.forEach(el => el.classList.remove('hidden'));
    }

    const arrows = document.querySelectorAll('.btn-arrow');
    if (state.manual_score_enabled && !state.match_running && !state.match_finished) {
        arrows.forEach(e => e.style.visibility = "visible");
    } else {
        arrows.forEach(e => e.style.visibility = "hidden");
    }
}

function adjustScore(delta) { socket.emit('update_score', {delta: delta}); }
function sendAction(cmd) { if(navigator.vibrate) navigator.vibrate(50); socket.emit('action', {cmd: cmd}); }
function confirmReboot() { if(confirm("Reboot ?")) sendAction('reboot'); }
function confirmShutdown() { if(confirm("Shutdown ?")) sendAction('shutdown'); }

// --- DEBUG ---
function initDebugPage() {
    const ctx = document.getElementById('currentChart').getContext('2d');
    Chart.defaults.color = '#ccc'; Chart.defaults.borderColor = '#444';
    currentChart = new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Courant (A)', data: [], borderColor: '#C3E88D', backgroundColor: 'rgba(195, 232, 141, 0.1)', borderWidth: 2, fill: true, pointRadius: 0 }] },
        options: { animation: false, responsive: true, scales: { y: { beginAtZero: true, grid: { color: '#333' } }, x: { display: false } }, plugins: { legend: { labels: { color: '#fff' } } } }
    });
}

function updateDebugUI(state) {
    document.getElementById('chk-lidar').checked = state.lidar_enabled;
    document.getElementById('chk-music').checked = state.music_enabled;
    document.getElementById('chk-leds').checked = state.leds_enabled;
    document.getElementById('chk-score').checked = state.manual_score_enabled;
    document.getElementById('sel-strat-mode').value = state.strat_mode;
    document.getElementById('sel-strat-id').value = state.strat_id;
    document.getElementById('row-strat-id').style.display = (state.strat_mode === 'STATIC') ? 'flex' : 'none';
}

function sendConfigUpdate() {
    socket.emit('update_config', {
        lidar_enabled: document.getElementById('chk-lidar').checked,
        music_enabled: document.getElementById('chk-music').checked,
        leds_enabled: document.getElementById('chk-leds').checked,
        manual_score_enabled: document.getElementById('chk-score').checked,
        strat_mode: document.getElementById('sel-strat-mode').value,
        strat_id: document.getElementById('sel-strat-id').value
    });
}

async function sendSerial() {
    const port = document.getElementById('serial-port').value;
    const cmd = document.getElementById('serial-cmd').value;
    const output = document.getElementById('serial-output');
    output.innerHTML += `<div>> ${cmd}</div>`;
    try {
        const res = await fetch('/api/send_serial', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({port: port, cmd: cmd})});
        const json = await res.json();
        output.innerHTML += `<div style="color:${json.status=='ok'?'#aaa':'#f55'}">${json.response || json.msg}</div>`;
        output.scrollTop = output.scrollHeight;
    } catch(e) { output.innerHTML += `<div style="color:red">Erreur JS</div>`; }
}

function updateChart(data) {
    const val = parseFloat(data.current) || 0;
    currentChart.data.labels.push("");
    currentChart.data.datasets[0].data.push(val);
    if (currentChart.data.labels.length > 50) { currentChart.data.labels.shift(); currentChart.data.datasets[0].data.shift(); }
    currentChart.update();
}

async function flashESP(target) {
    if(!confirm("Flash " + target + " ?")) return;
    const btn = document.getElementById('btn-flash-' + target);
    btn.innerText = "..."; btn.disabled = true;
    try { await fetch('/api/flash', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target: target})}); alert("OK"); } catch(e) { alert("Erreur"); }
    btn.innerText = "Flash " + target.toUpperCase(); btn.disabled = false;
}

// Fonction pour vider les logs
function clearLogs() {
    const container = document.getElementById('log-container');
    if(container) container.innerHTML = '<div class="log-line"><span class="log-info">--- Logs effacés ---</span></div>';
}

function updateDevStatus(id, isOk) {
    const el = document.getElementById('status-' + id);
    if (el) {
        el.className = 'status-dot ' + (isOk ? 'status-ok' : 'status-err');
    }
}

function reloadCam() {
    const img = document.getElementById('cam-feed');
    const err = document.querySelector('.cam-error');
    if(img) {
        // On ajoute un timestamp pour forcer le navigateur à recharger l'image sans cache
        img.src = "/video_feed?" + new Date().getTime();
        img.style.display = 'block';
        if(err) err.style.display = 'none';
    }
}

// --- MEDIA ---
function initMediaPage() {}
async function setTrack(event, filename) {
    if(!confirm("Track " + event + " -> " + filename + " ?")) return;
    await fetch('/api/set_audio_track', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({event: event, filename: filename})});
    location.reload();
}
async function sendColor(hex) {
    const val = hex || document.getElementById('col-picker').value;
    await fetch('/api/led_control', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mode: 'color', value: val})});
}
async function sendGradient() {
    const c1 = document.getElementById('grad-1').value; const c2 = document.getElementById('grad-2').value;
    await fetch('/api/led_control', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mode: 'gradient', c1: c1, c2: c2})});
}

// --- MAP ---
function initMapPage() {
    const canvas = document.getElementById('mapCanvas');
    ctxMap = canvas.getContext('2d');
    imgTable.src = "/static/table_coupe_2026.png"; imgRobot.src = "/static/robot.png";
    imgTable.onload = drawMap; imgRobot.onload = drawMap;
    socket.emit('map_connect');
}

function drawMap() {
    if (!ctxMap) return;
    const canvas = document.getElementById('mapCanvas');
    const w = canvas.width; const h = canvas.height;
    ctxMap.clearRect(0, 0, w, h);
    if (imgTable.complete && imgTable.naturalWidth > 0) ctxMap.drawImage(imgTable, 0, 0, w, h);
    else { ctxMap.fillStyle="#222"; ctxMap.fillRect(0,0,w,h); }
    if (imgRobot.complete && imgRobot.naturalWidth > 0) {
        const sx = w / 3000; const sy = h / 2000;
        const px = robotPos.x * sx; const py = robotPos.y * sy;
        ctxMap.save(); ctxMap.translate(px, py); ctxMap.rotate(robotPos.theta * Math.PI / 180);
        ctxMap.drawImage(imgRobot, -45, -45, 90, 90); ctxMap.restore();
    }
}