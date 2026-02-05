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

    // Initialisation LED Grid
    generateLedGrid();

    // Initialisation Onglet par défaut
    switchTab('audio');
});

// --- TABS LOGIC ---
function switchTab(tabName) {
    // Masquer tous les onglets
    document.getElementById('tab-audio').style.display = 'none';
    document.getElementById('tab-leds').style.display = 'none';

    // Désactiver tous les boutons
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    // Activer le bon
    document.getElementById('tab-' + tabName).style.display = 'flex';

    // Trouver le bouton correspondant (simple hack index 0=audio, 1=leds)
    const btns = document.querySelectorAll('.tab-btn');
    if (tabName === 'audio') btns[0].classList.add('active');
    else btns[1].classList.add('active');
}

// --- LED MATRIX & PIXEL CONTROL ---
const LED_COUNT = 60;

function generateLedGrid() {
    const container = document.getElementById('led-visualizer');
    if (!container) return;
    container.innerHTML = '';

    for (let i = 0; i < LED_COUNT; i++) {
        const px = document.createElement('div');
        px.className = 'led-pixel';
        px.title = `LED #${i}`;
        px.dataset.index = i;
        px.onclick = () => setPixel(i);
        container.appendChild(px);
    }
}

function setPixel(index) {
    // Récupère la couleur courante du picker
    const hex = document.getElementById('led-color-picker').value;
    const rgb = hexToRgb(hex);
    if (!rgb) return;

    // Mise à jour visuelle locale immédiate
    const px = document.querySelector(`.led-pixel[data-index="${index}"]`);
    if (px) px.style.backgroundColor = hex;

    // Envoi au backend : PIXEL:INDEX,R,G,B
    fetch('/api/led_control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            mode: 'pixel',
            value: `${index},${rgb.r},${rgb.g},${rgb.b}`
        })
    });
}

function fillPixels() {
    // Remplit tout avec la couleur courante
    const hex = document.getElementById('led-color-picker').value;
    setLedColor(hex, true); // true = force send

    // Update visuel local
    document.querySelectorAll('.led-pixel').forEach(px => px.style.backgroundColor = hex);
}

function clearPixels() {
    setLed('OFF');
    // Update visuel local
    document.querySelectorAll('.led-pixel').forEach(px => px.style.backgroundColor = '#222');
}

// --- 5. LEDS (Fonction héritée & Nouvelle UI) ---
function setLed(mode) {
    // Legacy support pour OFF
    if (mode === 'OFF') {
        fetch('/api/led_control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: 'color', value: 'OFF' })
        });
    }
}

function setLedColor(hex, sendNow = true) {
    // Met à jour le color picker si la commande vient d'un bouton preset
    const picker = document.getElementById('led-color-picker');
    if (picker && hex.startsWith('#')) picker.value = hex;

    // Si on ne veut pas envoyer tout de suite (ex: juste changer la couleur du "pinceau")
    if (!sendNow) return;

    // Conversion HEX -> RGB
    const rgb = hexToRgb(hex);
    if (!rgb) return;

    // Envoi de la commande "COLOR:R,G,B"
    const rgbString = `${rgb.r},${rgb.g},${rgb.b}`;

    // Debounce léger pour ne pas spammer si on glisse sur le picker
    clearTimeout(window.ledTimeout);
    window.ledTimeout = setTimeout(() => {
        fetch('/api/led_control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: 'color', value: rgbString })
        });

        // Update visuel de la grille aussi
        document.querySelectorAll('.led-pixel').forEach(px => px.style.backgroundColor = hex);
    }, 50);
}

function setLedAnim(anim) {
    // Envoi commande d'animation (ex: RAINBOW, FLASH...)
    fetch('/api/led_control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'anim', value: anim })
    });
}

// Helper Hex -> RGB
function hexToRgb(hex) {
    // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
    var shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    hex = hex.replace(shorthandRegex, function (m, r, g, b) {
        return r + r + g + g + b + b;
    });

    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

// --- 6. SOCKET UPDATE (Mise à jour Auto) ---
// Permet de voir les assignations (intro/match...) dès le chargement de la page
window.socket.on('state_update', (state) => {
    if (state.config && state.config.audio && state.config.audio.tracks) {
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