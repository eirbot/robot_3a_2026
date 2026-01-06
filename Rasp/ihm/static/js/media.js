function playTrack(mode, file) { fetch('/api/play_sound', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mode: mode, file: file})}); }
function setTrack(slot, file) { fetch('/api/set_sound_config', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({slot: slot, file: file})}).then(()=>location.reload()); }

async function sendColor() {
    const val = document.getElementById('col-picker').value;
    await fetch('/api/led_control', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mode: 'color', value: val})});
}
async function sendGradient() {
    const c1 = document.getElementById('grad-1').value; const c2 = document.getElementById('grad-2').value;
    await fetch('/api/led_control', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mode: 'gradient', c1: c1, c2: c2})});
}