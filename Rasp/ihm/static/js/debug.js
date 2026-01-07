let currentChart = null;

// Au chargement de la page debug, initialisation du graphique et chargement des stratégies Blockly

document.addEventListener("DOMContentLoaded", () => {
    initDebugPage();
    fetchStrats(); // Charge la liste pour le mode Statique
});

function initDebugPage() {
    const canvas = document.getElementById('currentChart');
    if (!canvas) return; // Sécurité si le canvas n'existe pas

    const ctx = canvas.getContext('2d');
    currentChart = new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Courant (A)', data: [], borderColor: '#FFCB6B', borderWidth: 2, tension: 0.3 }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { x: { display: false }, y: { beginAtZero: true, grid: { color: '#333' } } } }
    });
}

// Récupère la liste des stratégies
function fetchStrats() {
    fetch('/api/list_blockly_strats')
        .then(r => r.json())
        .then(data => {
            const sel = document.getElementById('strat-select');
            if(sel) {
                sel.innerHTML = '<option value="" disabled selected>Choisir un fichier...</option>';
                data.forEach(s => {
                    let opt = document.createElement('option');
                    opt.value = s;
                    opt.innerText = s;
                    sel.appendChild(opt);
                });
            }
        })
        .catch(err => console.error("Erreur chargement strats:", err));
}

// Mise à jour Config via l'événement state_update
window.socket.on('state_update', (state) => {
    // Si on est sur la page Debug
    if (document.getElementById('chk-lidar')) {
        const c = state.config || {}; // Protection si config vide
        
        // Helper pour cocher sans erreur si l'élément manque
        const setCheck = (id, val) => { 
            const el = document.getElementById(id); 
            if(el) el.checked = val; 
        };

        setCheck('chk-lidar', c.lidar);
        setCheck('chk-lidar-simu', c.lidar_simu);
        setCheck('chk-skip-homolog', c.skip_homologation);
        setCheck('chk-ekf', c.ekf);
        setCheck('chk-cam', c.camera);
        setCheck('chk-avoid', c.avoidance);
        setCheck('chk-side', (state.team === 'JAUNE'));

        // Gestion Mode Stratégie
        const stratMode = c.strat_mode || "DYNAMIC";
        const modeSel = document.getElementById('strat-mode');
        if(modeSel) modeSel.value = stratMode;
        
        const box = document.getElementById('static-strat-box');
        if(box) box.style.display = (stratMode === 'STATIC') ? 'block' : 'none';
        
        const stratSel = document.getElementById('strat-select');
        if (stratSel && c.static_strat) {
            stratSel.value = c.static_strat;
        }
    }
});

// Envoi modifications de la stratégie
async function updateStratConfig() {
    const mode = document.getElementById('strat-mode').value;
    const file = document.getElementById('strat-select').value;
    const payload = { strat_mode: mode };
    if (mode === 'STATIC' && file) {
        payload.static_strat = file;
    }
    // Envoie via WebSocket pour mise à jour et retour immédiat
    socket.emit('update_config', payload);
}

// Reception des logs
window.socket.on('new_log', (log) => {
    const box = document.getElementById('logs-box');
    if (box) {
        const div = document.createElement('div');
        div.className = 'log-line';
        let cls = 'log-info';
        if (log.msg.includes('[WARN]')) cls = 'log-warn';
        if (log.msg.includes('[ERR]')) cls = 'log-err';
        div.innerHTML = `<span class="log-time">${log.time}</span> <span class="${cls}">${log.msg}</span>`;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    }
});

// Infos système & mise à jour du graphique et des statuts périphériques
window.socket.on('sys_info', (data) => {
    if (currentChart) {
        const now = new Date().toLocaleTimeString();
        currentChart.data.labels.push(now);
        currentChart.data.datasets[0].data.push(data.current);
        if (currentChart.data.labels.length > 20) {
            currentChart.data.labels.shift();
            currentChart.data.datasets[0].data.shift();
        }
        currentChart.update();
    }
    if (data.devs && document.getElementById('status-lidar')) {
        updateDevStatus('status-lidar', data.devs.lidar);
        updateDevStatus('status-esp_motors', data.devs.esp_motors);
        updateDevStatus('status-esp_arms', data.devs.esp_arms);
        updateDevStatus('status-camera', data.devs.camera);
    }
});

function updateDevStatus(id, isOk) {
    const el = document.getElementById(id);
    if(el) el.className = 'status-dot ' + (isOk ? 'status-ok' : 'status-err');
}

function toggleConfig(key, checkbox) {
    // Mise à jour via WebSocket (au lieu de fetch)
    socket.emit('update_config', { [key]: checkbox.checked });
}

function flashESP(target) {
    if(confirm("Flasher l'ESP " + target + " ?")) {
        fetch('/api/flash_esp/' + target, {method:'POST'}).then(r=>r.json()).then(d=>alert(d.msg));
    }
}

function reloadCam() {
    const img = document.getElementById('cam-feed');
    if(img) img.src = "/video_feed?" + new Date().getTime();
}
