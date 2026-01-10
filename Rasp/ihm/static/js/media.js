// Rasp/ihm/static/js/media.js

let audioList = [];
let currentFile = null;
let contextFile = null; // Fichier ciblé par le clic droit

const audioPlayer = document.getElementById('audio-preview');
const fileListDiv = document.getElementById('file-list');
const contextMenu = document.getElementById('context-menu');

// --- 1. INITIALISATION & LISTENERS ---
document.addEventListener('DOMContentLoaded', () => {
    loadFiles();
    
    // Gestion du volume de la pré-écoute (Browser)
    const volSlider = document.getElementById('vol-slider');
    if (volSlider) {
        volSlider.addEventListener('input', (e) => {
            audioPlayer.volume = e.target.value;
        });
    }

    // Fermer le menu contextuel si on clique n'importe où ailleurs
    document.addEventListener('click', (e) => {
        if (!contextMenu.contains(e.target)) {
            contextMenu.style.display = 'none';
        }
    });
    
    // Initialisation du Drag & Drop
    setupDragAndDrop();
});

// Charger la liste des fichiers depuis le serveur
async function loadFiles() {
    try {
        const res = await fetch('/api/list_audio_files');
        audioList = await res.json();
        renderList();
    } catch (e) {
        console.error("Erreur chargement liste audio:", e);
        fileListDiv.innerHTML = "<div class='empty-msg'>Erreur de connexion</div>";
    }
}

// Afficher la liste dans la colonne de gauche
function renderList() {
    fileListDiv.innerHTML = "";
    
    if (audioList.length === 0) {
        fileListDiv.innerHTML = "<div class='empty-msg'>Aucun fichier audio.</div>";
        return;
    }

    audioList.forEach(file => {
        const div = document.createElement('div');
        div.className = 'file-item';
        // On met le titre pour voir le nom complet au survol (fix CSS overflow)
        div.title = file; 
        div.innerHTML = `<span class="file-icon">🎵</span> ${file}`;
        
        // Double Clic Gauche -> Jouer Préview
        div.addEventListener('dblclick', () => playFile(file));
        
        // Clic Droit -> Menu Contextuel
        div.addEventListener('contextmenu', (e) => showContextMenu(e, file));
        
        // Highlight visuel si c'est le fichier en cours
        if (file === currentFile) div.classList.add('active');
        
        fileListDiv.appendChild(div);
    });
}

// --- 2. LECTEUR AUDIO (PREVIEW & ROBOT) ---

// Jouer dans le navigateur (Preview)
function playFile(filename) {
    currentFile = filename;
    
    const nowPlayingText = document.getElementById('now-playing-text');
    nowPlayingText.innerText = filename;
    nowPlayingText.title = filename; // Tooltip pour lire le nom complet
    
    // Mise à jour visuelle de la liste
    document.querySelectorAll('.file-item').forEach(el => {
        el.classList.remove('active');
        if (el.innerText.includes(filename)) el.classList.add('active');
    });

    // Chargement et lecture HTML5
    audioPlayer.src = `/audio_files/${filename}`;
    audioPlayer.play().catch(e => console.error("Erreur lecture browser:", e));
}

// Bouton Précédent
function playPrev() {
    if (!currentFile || audioList.length === 0) return;
    let idx = audioList.indexOf(currentFile);
    if (idx > 0) playFile(audioList[idx - 1]);
    else playFile(audioList[audioList.length - 1]); // Boucle vers la fin
}

// Bouton Suivant
function playNext() {
    if (!currentFile || audioList.length === 0) {
        if (audioList.length > 0) playFile(audioList[0]);
        return;
    }
    let idx = audioList.indexOf(currentFile);
    if (idx < audioList.length - 1) playFile(audioList[idx + 1]);
    else playFile(audioList[0]); // Boucle vers le début
}

// --- NOUVEAU : Jouer sur le vrai Robot (Haut-parleurs) ---
async function playOnRobot() {
    if (!currentFile) {
        alert("Veuillez d'abord sélectionner une musique (double-clic) !");
        return;
    }
    
    // On envoie la commande au backend
    await fetch('/api/play_test', { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify({filename: currentFile})
    });
}

// --- 3. MENU CONTEXTUEL (Clic Droit) ---
function showContextMenu(e, filename) {
    e.preventDefault(); // Empêche le menu natif du navigateur
    contextFile = filename;
    
    const ctxTitle = document.getElementById('ctx-filename');
    ctxTitle.innerText = filename;
    ctxTitle.title = filename; // Tooltip
    
    // Positionner le menu à l'endroit de la souris
    contextMenu.style.display = 'block';
    contextMenu.style.left = `${e.pageX}px`;
    contextMenu.style.top = `${e.pageY}px`;
}

async function assignTrack(key) {
    if (!contextFile) return;
    
    // 1. Mise à jour visuelle immédiate
    const displayEl = document.getElementById(`assign-${key}`);
    if (displayEl) {
        displayEl.innerText = contextFile;
        displayEl.title = contextFile; // Tooltip
    }
    
    // 2. Envoi au serveur (Sauvegarde Config)
    // On utilise la clé imbriquée 'audio.tracks.intro' grâce au fix récursif du backend
    await fetch('/api/config_edit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            key: `audio.tracks.${key}`, 
            val: contextFile
        })
    });
    
    // Fermer le menu
    contextMenu.style.display = 'none';
}

function deleteTrack() {
    alert("Fonctionnalité 'Supprimer' à venir ! (Pour l'instant, supprimez via SSH/FTP)");
    contextMenu.style.display = 'none';
}

// --- 4. DRAG & DROP (UPLOAD) ---
function setupDragAndDrop() {
    const dropZone = document.querySelector('.panel-left');
    
    // Empêcher les comportements par défaut du navigateur
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

    // Effets visuels
    dropZone.addEventListener('dragenter', () => dropZone.classList.add('dragover'));
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    // Gestion du lâcher de fichier
    dropZone.addEventListener('drop', handleDrop);

    async function handleDrop(e) {
        dropZone.classList.remove('dragover');
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            const formData = new FormData();
            formData.append('file', files[0]);

            // Feedback visuel temporaire
            const tempDiv = document.createElement('div');
            tempDiv.className = 'file-item';
            tempDiv.innerText = `⏳ Upload de ${files[0].name}...`;
            fileListDiv.insertBefore(tempDiv, fileListDiv.firstChild);

            try {
                const res = await fetch('/api/upload_sound', { method: 'POST', body: formData });
                if (res.ok) {
                    loadFiles(); // Recharger la liste propre
                } else {
                    alert("Erreur lors de l'upload.");
                    tempDiv.remove();
                }
            } catch (err) {
                console.error(err);
                tempDiv.remove();
            }
        }
    }
}

// --- 5. LEDS (Fonction héritée) ---
function setLed(mode) {
    fetch('/api/led_control', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({mode: 'color', value: mode})
    });
}

// --- 6. SOCKET UPDATE (Mise à jour Auto) ---
// Permet de voir les assignations (intro/match...) dès le chargement de la page
window.socket.on('state_update', (state) => {
    if(state.config && state.config.audio && state.config.audio.tracks) {
        const tracks = state.config.audio.tracks;
        
        updateAssignDisplay('intro', tracks.intro);
        updateAssignDisplay('match_loop', tracks.match_loop);
        updateAssignDisplay('outro', tracks.outro);
    }
});

function updateAssignDisplay(key, val) {
    const el = document.getElementById(`assign-${key}`);
    if (el && val) {
        el.innerText = val;
        el.title = val; // Tooltip indispensable pour les noms longs
    }
}