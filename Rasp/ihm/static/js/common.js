// --- CRITIQUE : On attache socket à window pour qu'il soit global ---
window.socket = io();
let localState = {};

// --- SOCKET IO GLOBAL ---
window.socket.on('state_update', (state) => {
    localState = state;
    // Gestion des classes globales (couleur équipe, animation match)
    document.body.classList.remove('mode-BLEUE', 'mode-JAUNE');
    document.body.classList.add('mode-' + state.team);

    if (state.match_finished) document.body.classList.add('breathing-' + state.team);
    else document.body.classList.remove('breathing-BLEUE', 'breathing-JAUNE');
});

window.socket.on('sys_info', (data) => {
    const d = document.getElementById('sys-info');
    if (d) d.innerHTML = `IP: ${data.ip} | Bat: ${data.volt}<br>CPU: ${data.cpu}`;
});

// --- FONCTIONS PARTAGÉES ---
function sendAction(act) {
    // Petit feedback visuel console
    console.log("Envoi action :", act);
    // Use fetch API instead of socket.emit because the server exposes a REST endpoint
    fetch('/api/action/' + act, { method: 'POST' });
}

// --- LOGIQUE PARTAGÉE STRATÉGIES ---
function loadBlocklyStrats(selectId) {
    fetch('/api/list_blockly_strats')
        .then(r => r.json())
        .then(data => {
            const sel = document.getElementById(selectId);
            if (sel) {
                // Save current selection to restore it if it still exists
                const currentVal = sel.value;

                sel.innerHTML = '<option value="" disabled>Choisir...</option>';
                data.forEach(s => {
                    let opt = document.createElement('option');
                    opt.value = s;
                    opt.innerText = s;
                    if (s === currentVal) opt.selected = true;
                    sel.appendChild(opt);
                });

                // If nothing selected, restore initial "Choisir..."
                if (!sel.value && sel.querySelector('option[disabled]')) {
                    sel.querySelector('option[disabled]').selected = true;
                }
            }
        })
        .catch(e => console.error("Erreur chargement strats", e));
}
