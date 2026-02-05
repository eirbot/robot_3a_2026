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
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                x: { display: true, ticks: { maxTicksLimit: 10 } },
                y: { beginAtZero: true, grid: { color: '#333' } }
            }
        }
    });
}

// Récupère la liste des stratégies
function fetchStrats() {
    fetch('/api/list_blockly_strats')
        .then(r => r.json())
        .then(data => {
            const sel = document.getElementById('strat-select');
            if (sel) {
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
            if (el) el.checked = val;
        };

        setCheck('chk-lidar', c.lidar);
        setCheck('chk-lidar-simu', c.lidar_simu);
        setCheck('chk-skip-homolog', c.skip_homologation);
        setCheck('chk-ekf', c.ekf);
        let camStatus = (typeof c.camera === 'object') ? c.camera.enabled : c.camera;
        setCheck('chk-cam', camStatus);
        setCheck('chk-avoid', c.avoidance);
        setCheck('chk-side', (state.team === 'JAUNE'));

        // Gestion Mode Stratégie
        const stratMode = c.strat_mode || "DYNAMIC";
        const modeSel = document.getElementById('strat-mode');
        if (modeSel) modeSel.value = stratMode;

        const box = document.getElementById('static-strat-box');
        if (box) box.style.display = (stratMode === 'STATIC') ? 'block' : 'none';

        const stratSel = document.getElementById('strat-select');
        if (stratSel && c.static_strat) {
            stratSel.value = c.static_strat;
        }
    }
});

// Envoi modifications de la stratégie
// Envoi modifs stratégie + Mise à jour VISUELLE immédiate
async function updateStratConfig() {
    const mode = document.getElementById('strat-mode').value;
    const file = document.getElementById('strat-select').value;

    // --- PARTIE AJOUTÉE : Gestion visuelle locale ---
    // On force l'affichage sans attendre le retour du serveur/socket
    const box = document.getElementById('static-strat-box');
    if (box) {
        box.style.display = (mode === 'STATIC') ? 'block' : 'none';
    }
    // -----------------------------------------------

    // Envoi au serveur (Backend)
    await fetch('/api/config_edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'strat_mode', val: mode })
    });

    if (mode === 'STATIC' && file) {
        await fetch('/api/config_edit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'static_strat', val: file })
        });
    }
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
        currentChart.data.datasets[0].data.push(parseFloat(data.current));
        // 10 minutes d'historique à 10Hz = 600 x 10 = 6000 points
        if (currentChart.data.labels.length > 6000) {
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
    if (el) el.className = 'status-dot ' + (isOk ? 'status-ok' : 'status-err');
}

async function toggleConfig(key, checkbox) {
    // AJOUTE CETTE LIGNE
    console.log("CLICK DETECTÉ SUR :", key, "VALEUR :", checkbox.checked);

    await fetch('/api/config_edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: key, val: checkbox.checked })
    });
}

function flashESP(target) {
    if (confirm("Flasher l'ESP " + target + " ?")) {
        fetch('/api/flash_esp/' + target, { method: 'POST' }).then(r => r.json()).then(d => alert(d.msg));
    }
}

function reloadCam() {
    const img = document.getElementById('cam-feed');
    if (img) img.src = "/video_feed?" + new Date().getTime();
}


function updateBrightness(val) {
    // Le slider est de 0 à 100
    // On veut que 100% = 0.5 (Max)
    const factor = 0.5;
    const computed = (parseFloat(val) / 100.0) * factor;

    console.log("Brightness set to:", val, "% ->", computed);
    fetch('/api/set_brightness', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: computed })
    });
}
