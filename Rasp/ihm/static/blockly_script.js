/**
 * RASPBERRY PI ROBOT STUDIO
 * Fichier : Rasp/ihm/static/blockly_script.js
 * Version : COMPLÈTE (Bézier, Grid 200mm, Preview, Mouse, Collisions, Start Block)
 */

document.addEventListener("DOMContentLoaded", function() {

    // ============================================================
    // 0. CONFIGURATION
    // ============================================================
    
    // Orientation Image Robot :
    // 'RIGHT' (->), 'UP' (^), 'LEFT' (<), 'DOWN' (v)
    // Réglé sur 'DOWN' car ton image nécessite une rotation de 180°
    const ROBOT_IMAGE_ORIENTATION = 'DOWN'; 

    const TABLE_WIDTH = 3000;
    const TABLE_HEIGHT = 2000;
    const GRID_STEP = 200; // Quadrillage tous les 200mm

    // Valeurs par défaut si le bloc "Départ" n'est pas utilisé
    const DEFAULT_START_X = 250;
    const DEFAULT_START_Y = 1000;
    const DEFAULT_START_THETA = 0;


    // ============================================================
    // 1. DÉFINITION DES BLOCS BLOCKLY
    // ============================================================
    
    // --- BLOC DÉPART ---
    Blockly.Blocks['robot_start'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("🏁 Départ Match (Bleu)")
                .appendField("X").appendField(new Blockly.FieldNumber(250), "X")
                .appendField("Y").appendField(new Blockly.FieldNumber(1000), "Y")
                .appendField("θ").appendField(new Blockly.FieldNumber(0), "THETA");
            this.setNextStatement(true, null);
            this.setColour(290); // Violet
            this.setTooltip("Définit la position de départ pour la simulation.");
        }
    };

    // --- BLOC GOTO (BÉZIER) ---
    Blockly.Blocks['robot_goto'] = {
        init: function() {
            this.appendDummyInput()
                .appendField("Aller à X").appendField(new Blockly.FieldNumber(1000), "X")
                .appendField("Y").appendField(new Blockly.FieldNumber(1000), "Y")
                .appendField("θ").appendField(new Blockly.FieldNumber(0), "THETA")
                .appendField("Force").appendField(new Blockly.FieldNumber(400), "FORCE");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230); // Bleu
            this.setTooltip("Déplacement courbe. Force = distance du point de contrôle.");
        }
    };
    
    // --- ACTIONNEURS ---
    Blockly.Blocks['prendre_kapla'] = { init: function() { this.appendDummyInput().appendField("✊ Prendre Kapla (H:").appendField(new Blockly.FieldNumber(0), "HAUTEUR").appendField("mm)"); this.setPreviousStatement(true, null); this.setNextStatement(true, null); this.setColour(120); }};
    Blockly.Blocks['retourner_kapla'] = { init: function() { this.appendDummyInput().appendField("🤌 Retourne Kapla"); this.setPreviousStatement(true, null); this.setNextStatement(true, null); this.setColour(120); }};
    Blockly.Blocks['poser_kapla'] = { init: function() { this.appendDummyInput().appendField("🖐️ Poser Kapla (H:").appendField(new Blockly.FieldNumber(0), "HAUTEUR").appendField("mm)"); this.setPreviousStatement(true, null); this.setNextStatement(true, null); this.setColour(120); }};
    Blockly.Blocks['robot_stop'] = { init: function() { this.appendDummyInput().appendField("🛑 Arrêter le robot"); this.setPreviousStatement(true, null); this.setNextStatement(true, null); this.setColour(0); }};

    // --- GÉNÉRATEURS PYTHON ---
    Blockly.Python.forBlock['robot_start'] = function(block) { return `robot.set_pos(${block.getFieldValue('X')}, ${block.getFieldValue('Y')}, ${block.getFieldValue('THETA')})\n`; };
    Blockly.Python.forBlock['robot_goto'] = function(block) { return `robot.goto(${block.getFieldValue('X')}, ${block.getFieldValue('Y')}, ${block.getFieldValue('THETA')}, force=${block.getFieldValue('FORCE')})\n`; };
    Blockly.Python.forBlock['prendre_kapla'] = function(block) { return `robot.prendreKapla(hauteur=${block.getFieldValue('HAUTEUR')})\n`; };
    Blockly.Python.forBlock['retourner_kapla'] = function(block) { return `robot.retournerKapla()\n`; };
    Blockly.Python.forBlock['poser_kapla'] = function(block) { return `robot.poseKapla(hauteur=${block.getFieldValue('HAUTEUR')})\n`; };
    Blockly.Python.forBlock['robot_stop'] = function(block) { return 'robot.stop()\n'; };

    // --- INITIALISATION WORKSPACE ---
    var workspace = Blockly.inject('blocklyDiv', {
        toolbox: document.getElementById('toolbox'),
        scrollbars: true, trashcan: true, sounds: false
    });
    window.addEventListener('resize', function() { Blockly.svgResize(workspace); }, false);


    // ============================================================
    // 2. MOTEUR GRAPHIQUE (CANVAS)
    // ============================================================

    const canvas = document.getElementById('simCanvas');
    const ctx = canvas.getContext('2d');
    const imgTable = document.getElementById('imgTable');
    const imgRobot = document.getElementById('imgRobot');
    const consoleDiv = document.getElementById('simConsole');
    
    // Création de l'infobulle (Tooltip) pour la souris
    const coordTooltip = document.createElement('div');
    coordTooltip.style.position = 'absolute';
    coordTooltip.style.background = 'rgba(0, 0, 0, 0.8)';
    coordTooltip.style.color = '#fff';
    coordTooltip.style.padding = '4px 8px';
    coordTooltip.style.borderRadius = '4px';
    coordTooltip.style.pointerEvents = 'none'; // Click-through
    coordTooltip.style.display = 'none';
    coordTooltip.style.fontSize = '12px';
    coordTooltip.style.fontFamily = 'monospace';
    coordTooltip.style.zIndex = '1000';
    document.body.appendChild(coordTooltip);

    // État du Robot
    let robot = {
        x: DEFAULT_START_X, 
        y: DEFAULT_START_Y, 
        theta: DEFAULT_START_THETA, 
        currentIcon: null, 
        bezier: null, 
        isMoving: false
    };
    
    let actionQueue = []; 
    let previewPath = []; 

    // --- FONCTIONS DE CONVERSION ---

    // Convertit Millimètres (Y Haut) vers Pixels Écran (Y Bas)
    function worldToScreen(x_mm, y_mm) {
        const scale = canvas.width / TABLE_WIDTH;
        return { 
            x: x_mm * scale, 
            y: canvas.height - (y_mm * scale) 
        };
    }
    
    // Convertit Pixels Écran vers Millimètres (Pour la souris)
    function screenToWorld(px, py) {
        const scale = canvas.width / TABLE_WIDTH;
        return {
            x: Math.round(px / scale),
            y: Math.round((canvas.height - py) / scale)
        };
    }

    // Calcul Point Bézier (t entre 0 et 1)
    function getBezierPoint(t, p0, p1, p2, p3) {
        let u = 1 - t; let tt = t * t; let uu = u * u; let uuu = uu * u; let ttt = tt * t;
        return {
            x: uuu * p0.x + 3 * uu * t * p1.x + 3 * u * tt * p2.x + ttt * p3.x,
            y: uuu * p0.y + 3 * uu * t * p1.y + 3 * u * tt * p2.y + ttt * p3.y
        };
    }

    // Vérifie si un point est hors de la table
    function isOutOfBounds(p) {
        return p.x < 0 || p.x > TABLE_WIDTH || p.y < 0 || p.y > TABLE_HEIGHT;
    }

    // --- ERREURS & BLOCKLY ---
    function clearBlockWarnings() {
        workspace.getAllBlocks().forEach(b => b.setWarningText(null)); 
        workspace.highlightBlock(null);
        canvas.classList.remove("collision-alert"); 
    }

    function markBlockError(blockId, msg) {
        if (!blockId) return;
        let block = workspace.getBlockById(blockId);
        if (block) block.setWarningText("⚠️ " + msg);
        canvas.classList.add("collision-alert");
    }

    // --- FONCTIONS DE DESSIN ---

    function drawGrid() {
        ctx.strokeStyle = "rgba(0, 0, 0, 0.15)"; // Gris foncé transparent
        ctx.fillStyle = "rgba(0, 0, 0, 0.6)";    // Texte gris foncé
        ctx.lineWidth = 1;
        ctx.font = "10px Arial";
        ctx.textAlign = "center";

        // Verticales
        for(let x=0; x<=TABLE_WIDTH; x+=GRID_STEP) {
            let p = worldToScreen(x, 0);
            ctx.beginPath(); ctx.moveTo(p.x, 0); ctx.lineTo(p.x, canvas.height); ctx.stroke();
            ctx.fillText(x, p.x, canvas.height - 5);
        }
        // Horizontales
        ctx.textAlign = "left";
        for(let y=0; y<=TABLE_HEIGHT; y+=GRID_STEP) {
            let p = worldToScreen(0, y);
            ctx.beginPath(); ctx.moveTo(0, p.y); ctx.lineTo(canvas.width, p.y); ctx.stroke();
            if(y > 0) ctx.fillText(y, 5, p.y - 2);
        }
    }

    function drawBezierCurve(bz, color, width) {
        let p0 = worldToScreen(bz.p0.x, bz.p0.y);
        let p1 = worldToScreen(bz.p1.x, bz.p1.y);
        let p2 = worldToScreen(bz.p2.x, bz.p2.y);
        let p3 = worldToScreen(bz.p3.x, bz.p3.y);

        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y);
        ctx.bezierCurveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y);
        ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke();
        
        // Points de contrôle P1/P2 en jaune si c'est la courbe active
        if(color.includes("255, 0, 0")) {
            ctx.fillStyle = "yellow";
            ctx.beginPath(); ctx.arc(p1.x, p1.y, 3, 0, 2*Math.PI); ctx.fill();
            ctx.beginPath(); ctx.arc(p2.x, p2.y, 3, 0, 2*Math.PI); ctx.fill();
        }
    }

    // BOUCLE DE RENDU PRINCIPALE
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 1. Fond de Table
        if (imgTable.complete && imgTable.naturalHeight !== 0) ctx.drawImage(imgTable, 0, 0, canvas.width, canvas.height);
        else { ctx.fillStyle = "#2e8b57"; ctx.fillRect(0, 0, canvas.width, canvas.height); }
        
        // 2. Grille
        drawGrid();

        // 3. Prévisualisation (Trait Cyan ou Orange si erreur)
        if (previewPath.length > 0) {
            previewPath.forEach(bz => {
                // Check simple sur le point d'arrivée et un point milieu
                let mid = getBezierPoint(0.5, bz.p0, bz.p1, bz.p2, bz.p3);
                if (isOutOfBounds(bz.p3) || isOutOfBounds(mid)) {
                     drawBezierCurve(bz, "rgba(255, 140, 0, 0.8)", 3); // Orange Alerte
                } else {
                     drawBezierCurve(bz, "rgba(0, 255, 255, 0.6)", 2); // Cyan OK
                }
            });
        }

        // 4. Mouvement Actif (Trait Rouge)
        if (robot.isMoving && robot.bezier) {
            robot.bezier.t += 0.015; // Vitesse animation

            if (robot.bezier.t >= 1) {
                // Fin du segment
                robot.x = robot.bezier.p3.x; 
                robot.y = robot.bezier.p3.y; 
                robot.theta = robot.bezier.targetTheta;
                robot.isMoving = false; 
                processNextAction();
            } else {
                // Calcul position courante
                let pos = getBezierPoint(robot.bezier.t, robot.bezier.p0, robot.bezier.p1, robot.bezier.p2, robot.bezier.p3);
                
                // Calcul orientation (Tangente)
                let nextPos = getBezierPoint(robot.bezier.t + 0.01, robot.bezier.p0, robot.bezier.p1, robot.bezier.p2, robot.bezier.p3);
                let dx = nextPos.x - pos.x; 
                let dy = nextPos.y - pos.y;
                robot.theta = Math.atan2(dy, dx) * (180 / Math.PI);

                // Check collision temps réel
                if(isOutOfBounds(pos)) {
                    // Optionnel : afficher alerte dans console
                }

                robot.x = pos.x; 
                robot.y = pos.y;
                drawBezierCurve(robot.bezier, "rgba(255, 0, 0, 0.8)", 4);
            }
        }

        // 5. Robot
        let screenPos = worldToScreen(robot.x, robot.y);
        const robotSizePx = (300 / TABLE_WIDTH) * canvas.width;
        
        ctx.save();
        ctx.translate(screenPos.x, screenPos.y);
        
        // Gestion Rotation : Math (CCW) vers Canvas (CW) -> Inverse signe
        let rotationRad = -robot.theta * (Math.PI / 180);
        
        // Correction Orientation Image
        if (ROBOT_IMAGE_ORIENTATION === 'UP') rotationRad += Math.PI/2;
        if (ROBOT_IMAGE_ORIENTATION === 'DOWN') rotationRad -= Math.PI/2;
        if (ROBOT_IMAGE_ORIENTATION === 'LEFT') rotationRad += Math.PI;

        ctx.rotate(rotationRad);
        
        if (imgRobot.complete && imgRobot.naturalHeight !== 0) {
            ctx.drawImage(imgRobot, -robotSizePx/2, -robotSizePx/2, robotSizePx, robotSizePx);
        } else {
            // Dessin secours
            ctx.fillStyle = "#007bff"; 
            ctx.beginPath(); 
            ctx.moveTo(robotSizePx/2, 0); 
            ctx.lineTo(-robotSizePx/2, -robotSizePx/2); 
            ctx.lineTo(-robotSizePx/2, robotSizePx/2); 
            ctx.fill(); 
        }
        ctx.restore();

        // 6. Icone Action
        if (robot.currentIcon) {
            ctx.font = "40px Arial"; ctx.textAlign = "center";
            ctx.fillText(robot.currentIcon, screenPos.x, screenPos.y - robotSizePx/2 - 10);
        }
        
        requestAnimationFrame(draw);
    }


    // ============================================================
    // 3. LISTENERS & INTERACTION SOURIS
    // ============================================================
    
    // Suivi souris pour tooltip
    canvas.addEventListener('mousemove', function(evt) {
        var rect = canvas.getBoundingClientRect();
        var mx = evt.clientX - rect.left;
        var my = evt.clientY - rect.top;
        
        let worldPos = screenToWorld(mx, my);
        
        // Affiche tooltip
        coordTooltip.style.display = 'block';
        coordTooltip.style.left = (evt.pageX + 15) + 'px';
        coordTooltip.style.top = (evt.pageY + 15) + 'px';
        coordTooltip.innerHTML = `X: <b>${worldPos.x}</b><br>Y: <b>${worldPos.y}</b>`;
    });

    canvas.addEventListener('mouseout', function() {
        coordTooltip.style.display = 'none';
    });
    
    // Clic pour logguer la position
    canvas.addEventListener('click', function(evt) {
        var rect = canvas.getBoundingClientRect();
        let worldPos = screenToWorld(evt.clientX - rect.left, evt.clientY - rect.top);
        logSim(`📍 Clic: X=${worldPos.x}, Y=${worldPos.y}`);
    });


    // ============================================================
    // 4. PARSING & LOGIQUE SÉQUENTIELLE
    // ============================================================
    
    // Analyse les blocs et retourne une file d'actions + le chemin complet
    function parseBlocks(isPreview) {
        let queue = []; let pPath = [];
        let simX = DEFAULT_START_X, simY = DEFAULT_START_Y, simTheta = DEFAULT_START_THETA;

        var topBlocks = workspace.getTopBlocks(true);
        if (topBlocks.length === 0) return {queue: [], path: []};
        topBlocks.sort((a, b) => a.getRelativeToSurfaceXY().y - b.getRelativeToSurfaceXY().y);

        var currentBlock = topBlocks[0];
        while (currentBlock) {
            let blockId = currentBlock.id; // ON RECUPERE L'ID

            if (currentBlock.type === 'robot_start') {
                simX = parseInt(currentBlock.getFieldValue('X'));
                simY = parseInt(currentBlock.getFieldValue('Y'));
                simTheta = parseInt(currentBlock.getFieldValue('THETA'));
                if(!isPreview) {
                    robot.x = simX; robot.y = simY; robot.theta = simTheta;
                    logSim(`📍 Départ: ${simX}, ${simY}`);
                }
            }
            else if (currentBlock.type === 'robot_goto') {
                let targetX = parseInt(currentBlock.getFieldValue('X'));
                let targetY = parseInt(currentBlock.getFieldValue('Y'));
                let targetTheta = parseInt(currentBlock.getFieldValue('THETA'));
                let force = parseInt(currentBlock.getFieldValue('FORCE'));

                let p0 = {x: simX, y: simY};
                let p3 = {x: targetX, y: targetY};
                let radStart = simTheta * (Math.PI / 180);
                let radEnd = targetTheta * (Math.PI / 180);

                let p1 = { x: p0.x + force * Math.cos(radStart), y: p0.y + force * Math.sin(radStart) };
                let p2 = { x: p3.x - force * Math.cos(radEnd), y: p3.y - force * Math.sin(radEnd) };

                // AJOUT DE blockId ICI
                queue.push({ type: 'goto', x: targetX, y: targetY, theta: targetTheta, force: force, blockId: blockId });
                pPath.push({ p0, p1, p2, p3, blockId: blockId });

                simX = targetX; simY = targetY; simTheta = targetTheta;
            }
            else if (currentBlock.type.includes('kapla') || currentBlock.type.includes('stop')) {
                let msg = "Action";
                if(currentBlock.type === 'prendre_kapla') msg = "Prise Kapla";
                if(currentBlock.type === 'retourner_kapla') msg = "Retourne Kapla";
                if(currentBlock.type === 'poser_kapla') msg = "Pose Kapla";
                if(currentBlock.type === 'robot_stop') msg = "STOP";
                // AJOUT DE blockId ICI
                queue.push({type: 'action', msg: msg, blockId: blockId});
            }
            currentBlock = currentBlock.getNextBlock();
        }
        return {queue, path: pPath};
    }

    function generatePreview() {
        clearBlockWarnings(); // Reset
        let result = parseBlocks(true); 
        previewPath = result.path;
        
        let errorCount = 0;
        previewPath.forEach(bz => {
            let mid = getBezierPoint(0.5, bz.p0, bz.p1, bz.p2, bz.p3);
            if (isOutOfBounds(bz.p3) || isOutOfBounds(mid)) {
                // MARQUAGE ERREUR
                markBlockError(bz.blockId, "Hors table !");
                errorCount++;
            }
        });
        if(errorCount > 0) logSim(`⚠️ ${errorCount} erreurs détectées.`);
        else logSim("👁️ Aperçu généré.");
    }

    function runSimulation() {
        clearBlockWarnings(); // NETTOYAGE
        previewPath = []; 
        consoleDiv.innerHTML = ""; 
        logSim("🚀 Simulation...");
        robot.isMoving = false; robot.bezier = null; robot.currentIcon = null; robot.currentBlockId = null;
        
        let result = parseBlocks(false);
        actionQueue = result.queue;
        processNextAction();
    }

    function processNextAction() {
        if (actionQueue.length > 0) {
            const action = actionQueue.shift();
            
            // HIGHLIGHT DU BLOC
            if (action.blockId) {
                robot.currentBlockId = action.blockId;
                workspace.highlightBlock(action.blockId);
            }

            if (action.type === 'goto') {
                logSim(`Go (${action.x}, ${action.y})`);
                
                let p0 = {x: robot.x, y: robot.y};
                let p3 = {x: action.x, y: action.y};
                let force = action.force;
                let radStart = robot.theta * (Math.PI / 180);
                let radEnd = action.theta * (Math.PI / 180);

                let p1 = { x: p0.x + force * Math.cos(radStart), y: p0.y + force * Math.sin(radStart) };
                let p2 = { x: p3.x - force * Math.cos(radEnd), y: p3.y - force * Math.sin(radEnd) };

                robot.bezier = { p0, p1, p2, p3, targetTheta: action.theta, t: 0 };
                robot.isMoving = true;
            } 
            else if (action.type === 'action') {
                robot.currentIcon = getIcon(action.msg);
                logSim(action.msg);
                setTimeout(() => { robot.currentIcon = null; processNextAction(); }, 1000);
            }
        } else {
            logSim("🏁 Terminé.");
            workspace.highlightBlock(null); // ETEINDRE HIGHLIGHT
        }
    }
    
    function getIcon(msg) {
        if (msg.includes("Prise")) return "✊";
        if (msg.includes("Retourne")) return "🤌";
        if (msg.includes("Pose")) return "🖐️";
        if (msg.includes("STOP")) return "🛑";
        return "⚙️";
    }
    
    function logSim(msg) { 
        consoleDiv.innerHTML += `<div>> ${msg}</div>`; 
        consoleDiv.scrollTop = consoleDiv.scrollHeight; 
    }


    // ============================================================
    // 5. GESTION API (LOAD/SAVE/LIST) & BOUTONS
    // ============================================================

    var simuBtn = document.getElementById('simuBtn'); if(simuBtn) simuBtn.addEventListener('click', runSimulation);
    var previewBtn = document.getElementById('previewBtn'); if(previewBtn) previewBtn.addEventListener('click', generatePreview);

    function refreshStratList() {
        fetch('/api/list_blockly_strats')
            .then(r=>r.json())
            .then(d=>{ 
                var s=document.getElementById('stratSelect'); 
                s.innerHTML='<option value="" disabled selected>Choisir...</option>'; 
                d.forEach(n=>{var o=document.createElement('option');o.value=n;o.innerText=n;s.appendChild(o)}); 
            }); 
    }
    refreshStratList();

    document.getElementById('loadBtn').addEventListener('click', function() { 
        var n=document.getElementById('stratSelect').value; 
        if(!n)return; 
        fetch('/api/load_strat/'+n)
            .then(r=>r.json())
            .then(d=>{ 
                if(d.status==='success'){
                    workspace.clear();
                    Blockly.Xml.domToWorkspace(Blockly.utils.xml.textToDom(d.xml),workspace);
                    document.getElementById('filename').value=n;
                } 
            }); 
    });

    document.getElementById('saveBtn').addEventListener('click', function() { 
        var f=document.getElementById('filename').value; 
        if(!f)return; 
        var c=Blockly.Python.workspaceToCode(workspace).replace(/^/gm,"    "); 
        var final=`from strat.actions import RobotActions\nimport time\nMETADATA={"name":"${f}","score":0}\ndef run(robot: RobotActions):\n    print("Start ${f}")\n${c}\n    print("End")`; 
        
        fetch('/api/save_strat',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({
                filename:f,
                code:final,
                xml:Blockly.Xml.domToText(Blockly.Xml.workspaceToDom(workspace))
            })
        })
        .then(r=>r.json())
        .then(d=>{
            if(d.status==='success'){
                refreshStratList();
                document.getElementById('status').innerText="✅ Sauvegardé";
            }
        }); 
    });

    requestAnimationFrame(draw);
});