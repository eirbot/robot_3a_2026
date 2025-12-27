/**
 * RASPBERRY PI ROBOT STUDIO
 * Fichier : Rasp/ihm/static/blockly_script.js
 * Version : Avec visualisation des actions (Icones)
 */

document.addEventListener("DOMContentLoaded", function() {

    // ============================================================
    // 1. DÉFINITION DES BLOCS (Apparence & Champs)
    // ============================================================

    Blockly.Blocks['robot_goto'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Aller à X")
                .appendField(new Blockly.FieldNumber(1000), "X")
                .appendField("Y")
                .appendField(new Blockly.FieldNumber(1000), "Y")
                .appendField("θ")
                .appendField(new Blockly.FieldNumber(0), "THETA");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230);
            this.setTooltip("Déplace le robot vers un point (X,Y) en mm");
        }
    };

    Blockly.Blocks['prendre_kapla'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("✊ Prendre Kapla (H:")
                .appendField(new Blockly.FieldNumber(0), "HAUTEUR")
                .appendField("mm)");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(120);
        }
    };

    Blockly.Blocks['retourner_kapla'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("🤌 Retourne Kapla");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(120);
        }
    };

    Blockly.Blocks['poser_kapla'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("🖐️ Poser Kapla (H:")
                .appendField(new Blockly.FieldNumber(0), "HAUTEUR")
                .appendField("mm)");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(120);
        }
    };

    Blockly.Blocks['robot_stop'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("🛑 Arrêter le robot");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(0);
        }
    };

    // ============================================================
    // 2. GÉNÉRATEUR PYTHON (Traduction Bloc -> Code)
    // ============================================================

    Blockly.Python.forBlock['robot_goto'] = function(block) {
        var x = block.getFieldValue('X');
        var y = block.getFieldValue('Y');
        var theta = block.getFieldValue('THETA');
        return `robot.goto(${x}, ${y}, ${theta})\n`;
    };

    Blockly.Python.forBlock['prendre_kapla'] = function(block) {
        var h = block.getFieldValue('HAUTEUR');
        return `robot.prendreKapla(hauteur=${h})\n`;
    };

    Blockly.Python.forBlock['retourner_kapla'] = function(block) {
        return `robot.retournerKapla()\n`;
    };

    Blockly.Python.forBlock['poser_kapla'] = function(block) {
        var h = block.getFieldValue('HAUTEUR');
        return `robot.poseKapla(hauteur=${h})\n`;
    };

    Blockly.Python.forBlock['robot_stop'] = function(block) {
        return 'robot.stop()\n';
    };

    // ============================================================
    // 3. INITIALISATION DU WORKSPACE
    // ============================================================

    var blocklyArea = document.getElementById('blocklyArea');
    var blocklyDiv = document.getElementById('blocklyDiv');
    
    var workspace = Blockly.inject(blocklyDiv, {
        toolbox: document.getElementById('toolbox'),
        scrollbars: true,
        trashcan: true,
        sounds: false
    });

    var onresize = function(e) { Blockly.svgResize(workspace); };
    window.addEventListener('resize', onresize, false);
    onresize();


    // ============================================================
    // 4. MOTEUR DE SIMULATION (Canvas)
    // ============================================================

    const canvas = document.getElementById('simCanvas');
    const ctx = canvas.getContext('2d');
    const imgTable = document.getElementById('imgTable');
    const imgRobot = document.getElementById('imgRobot');
    const consoleDiv = document.getElementById('simConsole');

    const TABLE_WIDTH_MM = 3000;
    const TABLE_HEIGHT_MM = 2000;
    
    // État du Robot Virtuel
    let robotSim = {
        x: 250,
        y: 1000,
        theta: 0,
        targetX: 250,
        targetY: 1000,
        targetTheta: 0,
        isMoving: false,
        currentIcon: null // <--- NOUVEAU: Stocke l'icône à afficher (ex: "✊")
    };

    let actionQueue = []; 

    function mmToPx(x_mm, y_mm) {
        const scale = canvas.width / TABLE_WIDTH_MM;
        return {
            x: x_mm * scale,
            y: canvas.height - (y_mm * scale) 
        };
    }

    function logSim(msg) {
        consoleDiv.innerHTML += `<div>> ${msg}</div>`;
        consoleDiv.scrollTop = consoleDiv.scrollHeight;
    }

    // --- BOUCLE DE DESSIN ---
    function draw() {
        // A. Effacer
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // B. Table
        if (imgTable.complete && imgTable.naturalHeight !== 0) {
            ctx.drawImage(imgTable, 0, 0, canvas.width, canvas.height);
        } else {
            ctx.fillStyle = "#2e8b57";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }

        // C. Animation Mouvement
        if (robotSim.isMoving) {
            const speed = 40; 
            let dx = robotSim.targetX - robotSim.x;
            let dy = robotSim.targetY - robotSim.y;
            let dist = Math.sqrt(dx*dx + dy*dy);

            if (dist > speed) {
                let angle = Math.atan2(dy, dx);
                robotSim.x += Math.cos(angle) * speed;
                robotSim.y += Math.sin(angle) * speed;
                robotSim.theta = robotSim.targetTheta; // Rotation instantanée pour l'instant
            } else {
                robotSim.x = robotSim.targetX;
                robotSim.y = robotSim.targetY;
                robotSim.theta = robotSim.targetTheta;
                robotSim.isMoving = false;
                processNextAction(); 
            }
        }

        // D. Robot
        let pos = mmToPx(robotSim.x, robotSim.y);
        const robotSizePx = (300 / TABLE_WIDTH_MM) * canvas.width;

        ctx.save();
        ctx.translate(pos.x, pos.y);
        ctx.rotate(-robotSim.theta * Math.PI / 180); 
        
        if (imgRobot.complete && imgRobot.naturalHeight !== 0) {
            ctx.drawImage(imgRobot, -robotSizePx/2, -robotSizePx/2, robotSizePx, robotSizePx);
        } else {
            ctx.fillStyle = "#007bff";
            ctx.beginPath();
            ctx.arc(0, 0, robotSizePx/2, 0, 2 * Math.PI);
            ctx.fill();
            ctx.strokeStyle = "white"; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(robotSizePx/2, 0); ctx.stroke();
        }
        ctx.restore();

        // E. VISUALISATION ACTION (Nouveau !)
        // On dessine l'icône APRÈS le restore() pour qu'elle ne tourne pas avec le robot
        if (robotSim.currentIcon) {
            ctx.font = "40px Arial"; // Gros emoji
            ctx.textAlign = "center";
            // On affiche un peu au-dessus du robot (y - 40px)
            ctx.fillText(robotSim.currentIcon, pos.x, pos.y - robotSizePx/2 - 10);
        }

        requestAnimationFrame(draw);
    }

    // --- LOGIQUE SÉQUENTIELLE ---
    function processNextAction() {
        if (actionQueue.length > 0) {
            const action = actionQueue.shift();
            
            if (action.type === 'goto') {
                logSim(`Déplacement -> (${action.x}, ${action.y})`);
                robotSim.targetX = action.x;
                robotSim.targetY = action.y;
                robotSim.targetTheta = action.theta;
                robotSim.isMoving = true;
            } 
            else if (action.type === 'action') {
                // 1. Définir l'icône visuelle
                let icon = "⚙️"; // Défaut
                if (action.msg.includes("Prise")) icon = "✊";
                if (action.msg.includes("Retourne")) icon = "🤌";
                if (action.msg.includes("Pose")) icon = "🖐️";
                if (action.msg.includes("STOP")) icon = "🛑";
                
                robotSim.currentIcon = icon; // Affiche l'icône
                logSim(`⚡ Action : ${action.msg}`);
                
                // 2. Pause plus longue (1000ms = 1 seconde)
                setTimeout(() => {
                    robotSim.currentIcon = null; // Cache l'icône
                    processNextAction();        // Passe à la suite
                }, 1000);
            }
        } else {
            logSim("🏁 Fin de la séquence.");
        }
    }

    // --- PARSEUR ---
    function runSimulation() {
        actionQueue = []; 
        consoleDiv.innerHTML = "";
        logSim("🚀 Démarrage Simulation...");

        var topBlocks = workspace.getTopBlocks(true);
        if (topBlocks.length === 0) { logSim("⚠️ Aucun bloc !"); return; }

        // Tri haut -> bas
        topBlocks.sort((a, b) => a.getRelativeToSurfaceXY().y - b.getRelativeToSurfaceXY().y);
        var currentBlock = topBlocks[0];

        // Reset
        robotSim.x = 250; robotSim.y = 1000;
        robotSim.targetX = 250; robotSim.targetY = 1000;
        robotSim.isMoving = false;
        robotSim.currentIcon = null;

        while (currentBlock) {
            var type = currentBlock.type;

            if (type === 'robot_goto') {
                let x = parseInt(currentBlock.getFieldValue('X'));
                let y = parseInt(currentBlock.getFieldValue('Y'));
                let t = parseInt(currentBlock.getFieldValue('THETA'));
                actionQueue.push({type: 'goto', x: x, y: y, theta: t});
            }
            else if (type === 'prendre_kapla') {
                actionQueue.push({type: 'action', msg: "Prise Kapla"});
            }
            else if (type === 'retourner_kapla') {
                actionQueue.push({type: 'action', msg: "Retourner Kapla"});
            }
            else if (type === 'poser_kapla') {
                actionQueue.push({type: 'action', msg: "Pose Kapla"});
            }
            else if (type === 'robot_stop') {
                actionQueue.push({type: 'action', msg: "STOP"});
            }
            
            currentBlock = currentBlock.getNextBlock();
        }

        processNextAction();
    }

    var simuBtn = document.getElementById('simuBtn');
    if(simuBtn) simuBtn.addEventListener('click', runSimulation);
    
    requestAnimationFrame(draw);


    // ============================================================
    // 5. GESTION SAUVEGARDE / CHARGEMENT
    // ============================================================
    // (Cette partie ne change pas, elle est reprise pour avoir un fichier complet)

    function refreshStratList() {
        fetch('/api/list_blockly_strats')
            .then(res => res.json())
            .then(data => {
                var select = document.getElementById('stratSelect');
                select.innerHTML = '<option value="" disabled selected>Choisir...</option>';
                data.forEach(name => {
                    var opt = document.createElement('option');
                    opt.value = name; opt.innerText = name; select.appendChild(opt);
                });
            })
            .catch(err => console.error(err));
    }
    refreshStratList();

    document.getElementById('loadBtn').addEventListener('click', function() {
        var name = document.getElementById('stratSelect').value;
        var statusSpan = document.getElementById('status');
        if(!name) { alert("Sélectionne une stratégie !"); return; }
        
        statusSpan.innerText = "Chargement...";
        fetch('/api/load_strat/' + name)
            .then(res => res.json())
            .then(data => {
                if(data.status === 'success') {
                    workspace.clear();
                    var dom = Blockly.utils.xml.textToDom(data.xml);
                    Blockly.Xml.domToWorkspace(dom, workspace);
                    document.getElementById('filename').value = name;
                    statusSpan.innerText = "✅ Chargé : " + name;
                    statusSpan.style.color = "#0f0";
                } else {
                    statusSpan.innerText = "❌ Erreur";
                    statusSpan.style.color = "#f00";
                }
            });
    });

    document.getElementById('saveBtn').addEventListener('click', function() {
        var filename = document.getElementById('filename').value;
        var statusSpan = document.getElementById('status');
        if(!filename) { alert("Nom manquant !"); return; }

        var codeBrut = Blockly.Python.workspaceToCode(workspace);
        var codeIndente = codeBrut.replace(/^/gm, "    ");
        
        var finalCode = `
# Fichier généré par Blockly
from strat.actions import RobotActions
import time

METADATA = {
    "name": "${filename}",
    "score": 0 
}

def run(robot: RobotActions):
    print("--- Début Stratégie Blockly : ${filename} ---")
${codeIndente}
    print("--- Fin Stratégie Blockly ---")
        `;

        var xmlDom = Blockly.Xml.workspaceToDom(workspace);
        var xmlText = Blockly.Xml.domToText(xmlDom);

        statusSpan.innerText = "Envoi...";
        statusSpan.style.color = "white";

        fetch('/api/save_strat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: filename, code: finalCode, xml: xmlText })
        })
        .then(response => response.json())
        .then(data => {
            if(data.status === 'success') {
                statusSpan.innerText = "✅ Sauvegardé !";
                statusSpan.style.color = "#0f0";
                refreshStratList(); 
            } else {
                statusSpan.innerText = "❌ Erreur: " + data.msg;
                statusSpan.style.color = "#f00";
            }
        })
        .catch(err => {
            console.error(err);
            statusSpan.innerText = "❌ Erreur Réseau";
        });
    });

});