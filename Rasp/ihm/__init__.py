import sys
from ihm.shared import app, socketio
import ihm.routes
import ihm.events
from ihm.tasks import background_loop

# Classe simple pour rediriger les prints vers l'IHM
class LogCapture:
    def __init__(self, original, tag):
        self.orig = original
        self.tag = tag
        self.encoding = getattr(original, 'encoding', 'utf-8')
    def write(self, msg):
        try: self.orig.write(msg); self.orig.flush()
        except: pass
        if msg and msg.strip():
            try: socketio.emit('new_log', {'msg': msg.strip(), 'type': self.tag, 'time': ""})
            except: pass
    def flush(self): 
        try: self.orig.flush()
        except: pass
    def __getattr__(self, name): return getattr(self.orig, name)

def run_ihm():
    # Redirection Logs
    sys.stdout = LogCapture(sys.stdout, 'info')
    sys.stderr = LogCapture(sys.stderr, 'error')
    
    print("[IHM] Démarrage Serveur Web...")
    socketio.start_background_task(background_loop)
    # On lance en mode bloquant (c'est le main qui gérera les threads)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)