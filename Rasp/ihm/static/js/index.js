// index.js corrigé — Mise à jour de l'affichage en fonction des données de `state`

// Lorsque le serveur envoie un état, on met à jour l'interface si la page possède un score
window.socket.on('state_update', (state) => {
    if (!document.getElementById('score')) return;

    // Affichage de l’équipe
    document.getElementById('team-display').innerText = 'ÉQUIPE ' + state.team;

    // Score : on accepte score_current ou score selon ce qui existe
    const scoreVal = state.score_current ?? state.score ?? 0;
    document.getElementById('score').innerText = scoreVal;

    // Timer : on préfère timer_str, sinon on formate timer à 1 décimale
    const timer = state.timer_str ?? (typeof state.timer !== 'undefined' ? Number(state.timer).toFixed(1) : '0.0');
    document.getElementById('timer').innerText = timer;

    // Affichage de la stratégie (mode dynamique ou identifiant statique)
    const stratEl = document.getElementById('strat-display');
    if (stratEl) {
        if (state.strat_mode === 'STATIC') {
            stratEl.innerText = '#' + (state.strat_id ?? '?');
        } else {
            stratEl.innerText = 'Dynamique';
        }
    }

    // Affichage de l’état de la machine à états
    const fsmEl = document.getElementById('fsm-display');
    if (fsmEl) {
        fsmEl.innerText = state.fsm_state ?? 'INIT';
    }

    // Gestion de la tirette
    const tirDiv = document.getElementById('tirette-status');
    if (tirDiv) {
        const tir = state.tirette ?? false;
        if (typeof tir === 'string') {
            if (tir === 'ARMED') {
                tirDiv.innerText = 'TIRETTE: ARMÉE (PRÊT)';
                tirDiv.className = 'tirette-box status-armed';
            } else if (tir === 'TRIGGERED') {
                tirDiv.innerText = 'TIRETTE: TIRÉE (GO)';
                tirDiv.className = 'tirette-box status-triggered';
            } else {
                tirDiv.innerText = 'TIRETTE: NON ARMÉE';
                tirDiv.className = 'tirette-box status-non-armed';
            }
        } else if (tir === true) {
            tirDiv.innerText = 'TIRETTE: ARMÉE (PRÊT)';
            tirDiv.className = 'tirette-box status-armed';
        } else {
            tirDiv.innerText = 'TIRETTE: NON ARMÉE';
            tirDiv.className = 'tirette-box status-non-armed';
        }
    }

    // Gestion des boutons Start/Stop/Reset selon l’état du match
    const btnStart = document.getElementById('btn-start');
    const btnStop  = document.getElementById('btn-stop');
    const btnReset = document.getElementById('btn-reset');
    if (btnStart && btnStop && btnReset) {
        const running = state.match_running ?? (state.fsm_state === 'MATCH');
        const finished = state.match_finished ?? (state.fsm_state === 'FINISHED');
        if (finished) {
            btnStart.classList.add('hidden');
            btnStop.classList.add('hidden');
            btnReset.classList.remove('hidden');
        } else if (running) {
            btnStart.classList.add('hidden');
            btnStop.classList.remove('hidden');
            btnReset.classList.add('hidden');
        } else {
            btnStart.classList.remove('hidden');
            btnStop.classList.add('hidden');
            btnReset.classList.add('hidden');
        }
    }

    // Visibilité des flèches de score manuel : visible uniquement si activé et en dehors du match
    const arrows = document.querySelectorAll('.btn-arrow');
    const manualEnabled = state.manual_score_enabled ?? true;
    const runningMatch = state.match_running ?? (state.fsm_state === 'MATCH');
    const finishedMatch = state.match_finished ?? (state.fsm_state === 'FINISHED');
    arrows.forEach(e => {
        e.style.visibility = (manualEnabled && !runningMatch && !finishedMatch) ? 'visible' : 'hidden';
    });
});

// Fonction de modification de score : on utilise le WebSocket pour mettre à jour en temps réel
function adjustScore(delta) {
    socket.emit('update_score', { delta: delta });
}
