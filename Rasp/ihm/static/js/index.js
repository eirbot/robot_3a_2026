window.socket.on('state_update', (state) => {
    // Sécurité : on vérifie qu'on est bien sur l'index
    if (!document.getElementById('score')) return;

    document.getElementById('team-display').innerText = "ÉQUIPE " + state.team;
    document.getElementById('score').innerText = state.score;
    document.getElementById('timer').innerText = state.timer.toFixed(1);
    document.getElementById('fsm-display').innerText = state.fsm_state;
    document.getElementById('strat-display').innerText = state.strategy;

    const tir = document.getElementById('tirette-status');
    if (tir) {
        if (state.tirette) {
            tir.innerText = "TIRETTE: ARMÉE (PRÊT)";
            tir.className = "tirette-box status-armed";
        } else {
            tir.innerText = "TIRETTE: NON ARMÉE";
            tir.className = "tirette-box status-non-armed";
        }
    }

    // Gestion boutons Start/Stop
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const btnReset = document.getElementById('btn-reset');

    if (btnStart && btnStop && btnReset) {
        if (state.fsm_state === 'MATCH') {
            btnStart.classList.add('hidden');
            btnStop.classList.remove('hidden');
            btnReset.classList.add('hidden');
        } else if (state.fsm_state === 'FINISHED') {
            btnStart.classList.add('hidden');
            btnStop.classList.add('hidden');
            btnReset.classList.remove('hidden');
        } else {
            btnStart.classList.remove('hidden');
            btnStop.classList.add('hidden');
            btnReset.classList.add('hidden');
        }
    }
});

function adjustScore(delta) { 
    fetch('/api/score_edit', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({delta: delta})}); 
}