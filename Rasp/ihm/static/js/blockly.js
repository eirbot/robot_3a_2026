/**
 * RASPBERRY PI ROBOT STUDIO
 * Fichier : Rasp/ihm/static/blockly_script.js
 * Version : COMPLÈTE (Bézier, Grid 200mm, Preview, Mouse, Collisions, Start Block)
 */

document.addEventListener("DOMContentLoaded", function () {

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
    const DEFAULT_START_Y = 0;
    const DEFAULT_START_THETA = 0;


    // ============================================================
    // 1. DÉFINITION DES BLOCS BLOCKLY
    // ============================================================

    // --- DATA FETCHING FOR DROPDOWNS ---
    window.BLOCKLY_ANIMATIONS = [["Aucune", ""]];
    window.BLOCKLY_SOUNDS = [["Aucun", ""]];

    function fetchDropdownData() {
        // Animations
        fetch('/api/led_animations')
            .then(r => r.json())
            .then(data => {
                let keys = Object.keys(data);
                if (keys.length > 0) {
                    window.BLOCKLY_ANIMATIONS = keys.map(k => [k, k]);
                }
            });

        // Sounds
        fetch('/api/list_audio_files')
            .then(r => r.json())
            .then(data => {
                if (data.length > 0) {
                    window.BLOCKLY_SOUNDS = data.map(f => [f, f]);
                }
            });
    }
    fetchDropdownData();


    // --- BLOC DÉPART ---
    Blockly.Blocks['robot_start'] = {
        init: function () {
            this.appendDummyInput()
                .appendField("🏁 Départ Match (Bleu)")
                .appendField("X").appendField(new Blockly.FieldNumber(250), "X")
                .appendField("Y").appendField(new Blockly.FieldNumber(0), "Y")
                .appendField("θ").appendField(new Blockly.FieldNumber(0), "THETA");
            this.setNextStatement(true, null);
            this.setColour(290); // Violet
            this.setTooltip("Définit la position de départ pour la simulation.");
        }
    };

    // --- BLOC GOTO ---
    Blockly.Blocks['robot_goto'] = {
        init: function () {
            this.appendDummyInput()
                .appendField("Aller à X").appendField(new Blockly.FieldNumber(1000), "X")
                .appendField("Y").appendField(new Blockly.FieldNumber(0), "Y")
                .appendField("θ").appendField(new Blockly.FieldNumber(0), "THETA");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230); // Bleu
            this.setTooltip("Déplacement en ligne droite puis rotation finale.");
        }
    };

    // --- ACTIONNEURS ---
    Blockly.Blocks['prendre_kapla'] = { init: function () { this.appendDummyInput().appendField("✊ Prendre Kapla (H:").appendField(new Blockly.FieldNumber(0), "HAUTEUR").appendField("mm)"); this.setPreviousStatement(true, null); this.setNextStatement(true, null); this.setColour(120); } };
    Blockly.Blocks['retourner_kapla'] = { init: function () { this.appendDummyInput().appendField("🤌 Retourne Kapla"); this.setPreviousStatement(true, null); this.setNextStatement(true, null); this.setColour(120); } };
    Blockly.Blocks['poser_kapla'] = { init: function () { this.appendDummyInput().appendField("🖐️ Poser Kapla (H:").appendField(new Blockly.FieldNumber(0), "HAUTEUR").appendField("mm)"); this.setPreviousStatement(true, null); this.setNextStatement(true, null); this.setColour(120); } };
    Blockly.Blocks['robot_stop'] = { init: function () { this.appendDummyInput().appendField("🛑 Arrêter le robot"); this.setPreviousStatement(true, null); this.setNextStatement(true, null); this.setColour(0); } };

    // --- NOUVEAUX ACTIONNEURS (BAS & HAUT NIVEAU) ---
    Blockly.Blocks['actionneur_unique'] = {
        init: function () {
            this.appendDummyInput()
                .appendField("⚙️ Actionneur")
                .appendField(new Blockly.FieldDropdown([["1", "1"], ["2", "2"], ["3", "3"], ["4", "4"]]), "ID")
                .appendField("Action:")
                .appendField(new Blockly.FieldDropdown([["FLIP (Prendre + Tourne)", "FLIP"], ["nFLIP (Prendre sans tourner)", "nFLIP"], ["DOWN (Poser)", "DOWN"], ["INIT (Match)", "INIT"], ["RESET (Rangé)", "RESET"]]), "CMD");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(120);
            this.setTooltip("Contrôle individuel bas niveau pour un actionneur.");
        }
    };

    Blockly.Blocks['prendre_tous_kaplas'] = {
        init: function () {
            this.appendDummyInput()
                .appendField("👁️ Prendre 4 Kaplas (Auto Caméra)");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(120);
            this.setTooltip("Analyse via la caméra et définit s'il faut faire FLIP ou nFLIP pour chaque Kapla.");
        }
    };

    // --- SONS & LUMIERES ---
    Blockly.Blocks['play_animation'] = {
        init: function () {
            this.appendDummyInput()
                .appendField("🎨 Jouer Animation")
                .appendField(new Blockly.FieldDropdown(function () { return window.BLOCKLY_ANIMATIONS; }), "ANIM_NAME");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(300); // Violet foncé
            this.setTooltip("Lance une animation LED.");
        }
    };

    Blockly.Blocks['play_sound'] = {
        init: function () {
            this.appendDummyInput()
                .appendField("🎵 Jouer Son")
                .appendField(new Blockly.FieldDropdown(function () { return window.BLOCKLY_SOUNDS; }), "SOUND_NAME");
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(300);
            this.setTooltip("Joue un fichier audio.");
        }
    };

    // --- GÉNÉRATEURS PYTHON ---
    Blockly.Python.forBlock['robot_start'] = function (block) { return `robot.set_pos(${block.getFieldValue('X')}, ${block.getFieldValue('Y')}, ${block.getFieldValue('THETA')})\n`; };
    Blockly.Python.forBlock['robot_goto'] = function (block) { return `robot.goto(${block.getFieldValue('X')}, ${block.getFieldValue('Y')}, ${block.getFieldValue('THETA')})\n`; };
    Blockly.Python.forBlock['prendre_kapla'] = function (block) { return `robot.prendreKapla(hauteur=${block.getFieldValue('HAUTEUR')})\n`; };
    Blockly.Python.forBlock['retourner_kapla'] = function (block) { return `robot.retournerKapla()\n`; };
    Blockly.Python.forBlock['poser_kapla'] = function (block) { return `robot.poseKapla(hauteur=${block.getFieldValue('HAUTEUR')})\n`; };
    Blockly.Python.forBlock['robot_stop'] = function (block) { return 'robot.stop()\n'; };

    Blockly.Python.forBlock['actionneur_unique'] = function (block) {
        return `robot.cmd_actionneurs(act${block.getFieldValue('ID')}='${block.getFieldValue('CMD')}')\n`;
    };

    Blockly.Python.forBlock['prendre_tous_kaplas'] = function (block) {
        return `robot.prendre_kaplas_camera()\n`;
    };

    Blockly.Python.forBlock['play_animation'] = function (block) { return `robot.play_animation("${block.getFieldValue('ANIM_NAME')}")\n`; };
    Blockly.Python.forBlock['play_sound'] = function (block) { return `robot.play_sound("${block.getFieldValue('SOUND_NAME')}")\n`; };

    // --- INITIALISATION WORKSPACE ---
    var workspace = Blockly.inject('blocklyDiv', {
        toolbox: document.getElementById('toolbox'),
        scrollbars: true, trashcan: true, sounds: false
    });
    window.addEventListener('resize', function () { Blockly.svgResize(workspace); }, false);


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

    // Convertit Millimètres vers Pixels Écran (Nouveau Repère)
    function worldToScreen(x_mm, y_mm) {
        const scaleX = canvas.width / TABLE_WIDTH; // 3000 -> correspond à Y
        const scaleY = canvas.height / TABLE_HEIGHT; // 2000 -> correspond à X
        return {
            x: (canvas.width / 2) + (y_mm * scaleX),
            y: x_mm * scaleY
        };
    }

    // Convertit Pixels Écran vers Millimètres (Pour la souris)
    function screenToWorld(px, py) {
        const scaleX = canvas.width / TABLE_WIDTH;
        const scaleY = canvas.height / TABLE_HEIGHT;
        return {
            x: Math.round(py / scaleY),
            y: Math.round((px - (canvas.width / 2)) / scaleX)
        };
    }

    // Calcul Point Segment (t entre 0 et 1)
    function getSegmentPoint(t, p0, p3) {
        return {
            x: p0.x + t * (p3.x - p0.x),
            y: p0.y + t * (p3.y - p0.y)
        };
    }

    // Vérifie si un point est hors de la table
    function isOutOfBounds(p) {
        // X : 0 à 2000, Y : -1500 à 1500
        return p.x < 0 || p.x > TABLE_HEIGHT || p.y < -1500 || p.y > 1500;
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

        // Lignes pour Y (gauche à droite)
        for (let y = -1500; y <= 1500; y += GRID_STEP) {
            let p = worldToScreen(0, y);
            ctx.beginPath(); ctx.moveTo(p.x, 0); ctx.lineTo(p.x, canvas.height); ctx.stroke();
            if (y % 500 === 0) ctx.fillText(y, p.x, 10);
        }
        // Lignes pour X (haut en bas)
        ctx.textAlign = "left";
        for (let x = 0; x <= 2000; x += GRID_STEP) {
            let p = worldToScreen(x, 0);
            ctx.beginPath(); ctx.moveTo(0, p.y); ctx.lineTo(canvas.width, p.y); ctx.stroke();
            if (x % 500 === 0 && x > 0) ctx.fillText(x, 5, p.y - 2);
        }
    }

    function drawStraightPath(bz, color, width) {
        let p0 = worldToScreen(bz.p0.x, bz.p0.y);
        let p3 = worldToScreen(bz.p3.x, bz.p3.y);

        ctx.beginPath();
        ctx.moveTo(p0.x, p0.y);
        ctx.lineTo(p3.x, p3.y);
        ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke();
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
                let mid = getSegmentPoint(0.5, bz.p0, bz.p3);
                if (isOutOfBounds(bz.p3) || isOutOfBounds(mid)) {
                    drawStraightPath(bz, "rgba(255, 140, 0, 0.8)", 3); // Orange Alerte
                } else {
                    drawStraightPath(bz, "rgba(0, 255, 255, 0.6)", 2); // Cyan OK
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
                let pos = getSegmentPoint(robot.bezier.t, robot.bezier.p0, robot.bezier.p3);

                // Calcul orientation (Tangente)
                let dx = robot.bezier.p3.x - robot.bezier.p0.x;
                let dy = robot.bezier.p3.y - robot.bezier.p0.y;
                if (dx !== 0 || dy !== 0) {
                    robot.theta = Math.atan2(dy, dx) * (180 / Math.PI);
                }

                robot.x = pos.x;
                robot.y = pos.y;
                drawStraightPath(robot.bezier, "rgba(255, 0, 0, 0.8)", 4);
            }
        }

        // 5. Robot
        let screenPos = worldToScreen(robot.x, robot.y);
        const robotSizePx = (370 / TABLE_WIDTH) * canvas.width;

        ctx.save();
        ctx.translate(screenPos.x, screenPos.y);

        // Gestion Rotation : Adaptation au nouveau repère
        // Dans le repère map: MapTheta=0 -> X_map (vers le bas)
        // MapTheta=90 -> Y_map (vers la droite sur l'écran)
        let rotationRad = -robot.theta * (Math.PI / 180) + Math.PI / 2;

        // Correction Orientation Image
        if (ROBOT_IMAGE_ORIENTATION === 'UP') rotationRad += Math.PI / 2;
        if (ROBOT_IMAGE_ORIENTATION === 'DOWN') rotationRad -= Math.PI / 2;
        if (ROBOT_IMAGE_ORIENTATION === 'LEFT') rotationRad += Math.PI;

        ctx.rotate(rotationRad);

        if (imgRobot.complete && imgRobot.naturalHeight !== 0) {
            ctx.drawImage(imgRobot, -robotSizePx / 2, -robotSizePx / 2, robotSizePx, robotSizePx);
        } else {
            // Dessin secours
            ctx.fillStyle = "#007bff";
            ctx.beginPath();
            ctx.moveTo(robotSizePx / 2, 0);
            ctx.lineTo(-robotSizePx / 2, -robotSizePx / 2);
            ctx.lineTo(-robotSizePx / 2, robotSizePx / 2);
            ctx.fill();
        }
        ctx.restore();

        // 6. Icone Action
        if (robot.currentIcon) {
            ctx.font = "40px Arial"; ctx.textAlign = "center";
            ctx.fillText(robot.currentIcon, screenPos.x, screenPos.y - robotSizePx / 2 - 10);
        }

        requestAnimationFrame(draw);
    }


    // ============================================================
    // 3. LISTENERS & INTERACTION SOURIS
    // ============================================================

    canvas.addEventListener('mousemove', function (evt) {
        var rect = canvas.getBoundingClientRect();
        var scaleX_mouse = canvas.width / rect.width;
        var scaleY_mouse = canvas.height / rect.height;
        var mx = (evt.clientX - rect.left) * scaleX_mouse;
        var my = (evt.clientY - rect.top) * scaleY_mouse;

        let worldPos = screenToWorld(mx, my);

        // Affiche tooltip
        coordTooltip.style.display = 'block';
        coordTooltip.style.left = (evt.pageX + 15) + 'px';
        coordTooltip.style.top = (evt.pageY + 15) + 'px';
        coordTooltip.innerHTML = `X: <b>${worldPos.x}</b><br>Y: <b>${worldPos.y}</b>`;
    });

    canvas.addEventListener('mouseout', function () {
        coordTooltip.style.display = 'none';
    });

    // Clic pour logguer la position
    canvas.addEventListener('click', function (evt) {
        var rect = canvas.getBoundingClientRect();
        var scaleX_mouse = canvas.width / rect.width;
        var scaleY_mouse = canvas.height / rect.height;
        let worldPos = screenToWorld((evt.clientX - rect.left) * scaleX_mouse, (evt.clientY - rect.top) * scaleY_mouse);
        logSim(`📍 Clic: X=${worldPos.x}, Y=${worldPos.y}`);
    });


    // ============================================================
    // 4. PARSING & LOGIQUE SÉQUENTIELLE
    // ============================================================

    function applySymmetry(x, y, theta) {
        let symToggle = document.getElementById('symToggle');
        if (symToggle && symToggle.checked) {
            return { x: x, y: -y, theta: -theta };
        }
        return { x: x, y: y, theta: theta };
    }

    function parseSequence(firstBlock, currentX, currentY, currentTheta) {
        let queue = []; let pPath = [];
        let simX = currentX, simY = currentY, simTheta = currentTheta;

        let currentBlock = firstBlock;
        while (currentBlock) {
            let blockId = currentBlock.id;

            if (currentBlock.type === 'robot_start') {
                let rawX = parseInt(currentBlock.getFieldValue('X'));
                let rawY = parseInt(currentBlock.getFieldValue('Y'));
                let rawTheta = parseInt(currentBlock.getFieldValue('THETA'));

                let sym = applySymmetry(rawX, rawY, rawTheta);
                simX = sym.x; simY = sym.y; simTheta = sym.theta;

                queue.push({ type: 'start', x: simX, y: simY, theta: simTheta, blockId: blockId });
            }
            else if (currentBlock.type === 'robot_goto') {
                let rawX = parseInt(currentBlock.getFieldValue('X'));
                let rawY = parseInt(currentBlock.getFieldValue('Y'));
                let rawTheta = parseInt(currentBlock.getFieldValue('THETA'));

                let sym = applySymmetry(rawX, rawY, rawTheta);
                let targetX = sym.x; let targetY = sym.y; let targetTheta = sym.theta;

                let p0 = { x: simX, y: simY };
                let p3 = { x: targetX, y: targetY };

                queue.push({ type: 'goto', x: targetX, y: targetY, theta: targetTheta, blockId: blockId });
                pPath.push({ p0, p3, blockId: blockId });

                simX = targetX; simY = targetY; simTheta = targetTheta;
            }
            else if (currentBlock.type === 'controls_repeat_ext') {
                let times = 0;
                let timesBlock = currentBlock.getInputTargetBlock('TIMES');
                if (timesBlock && timesBlock.type === 'math_number') {
                    times = parseInt(timesBlock.getFieldValue('NUM'));
                }
                let doBlock = currentBlock.getInputTargetBlock('DO');
                for (let i = 0; i < times; i++) {
                    let subResult = parseSequence(doBlock, simX, simY, simTheta);
                    queue = queue.concat(subResult.queue);
                    pPath = pPath.concat(subResult.path);
                    simX = subResult.endX; simY = subResult.endY; simTheta = subResult.endTheta;
                }
            }
            else if (currentBlock.type.includes('kapla') || currentBlock.type.includes('stop') || currentBlock.type.includes('play_') || currentBlock.type.includes('actionneur')) {
                let msg = "Action";
                if (currentBlock.type === 'prendre_kapla') msg = "Prise Kapla";
                if (currentBlock.type === 'retourner_kapla') msg = "Retourne Kapla";
                if (currentBlock.type === 'poser_kapla') msg = "Pose Kapla";
                if (currentBlock.type === 'robot_stop') msg = "STOP";
                if (currentBlock.type === 'play_animation') msg = "Animation: " + currentBlock.getFieldValue('ANIM_NAME');
                if (currentBlock.type === 'play_sound') msg = "Son: " + currentBlock.getFieldValue('SOUND_NAME');
                if (currentBlock.type === 'actionneur_unique') msg = `Act. ${currentBlock.getFieldValue('ID')}: ${currentBlock.getFieldValue('CMD')}`;
                if (currentBlock.type === 'prendre_tous_kaplas') msg = "Prise 4 Kaplas (Caméra)";

                queue.push({ type: 'action', msg: msg, blockId: blockId });
            }
            currentBlock = currentBlock.getNextBlock();
        }
        return { queue, path: pPath, endX: simX, endY: simY, endTheta: simTheta };
    }

    function parseBlocks(isPreview) {
        var topBlocks = workspace.getTopBlocks(true);
        if (topBlocks.length === 0) return { queue: [], path: [] };
        topBlocks.sort((a, b) => a.getRelativeToSurfaceXY().y - b.getRelativeToSurfaceXY().y);

        let res = parseSequence(topBlocks[0], DEFAULT_START_X, DEFAULT_START_Y, DEFAULT_START_THETA);
        return { queue: res.queue, path: res.path };
    }

    function generatePreview() {
        clearBlockWarnings(); // Reset
        let result = parseBlocks(true);
        previewPath = result.path;

        let errorCount = 0;
        previewPath.forEach(bz => {
            let mid = getSegmentPoint(0.5, bz.p0, bz.p3);
            if (isOutOfBounds(bz.p3) || isOutOfBounds(mid)) {
                // MARQUAGE ERREUR
                markBlockError(bz.blockId, "Hors table !");
                errorCount++;
            }
        });
        if (errorCount > 0) logSim(`⚠️ ${errorCount} erreurs détectées.`);
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

            if (action.type === 'start') {
                robot.x = action.x;
                robot.y = action.y;
                robot.theta = action.theta;
                logSim(`📍 Départ: ${action.x}, ${action.y}`);
                processNextAction();
            }
            else if (action.type === 'goto') {
                logSim(`Go (${action.x}, ${action.y})`);

                let p0 = { x: robot.x, y: robot.y };
                let p3 = { x: action.x, y: action.y };

                robot.bezier = { p0, p3, targetTheta: action.theta, t: 0 };
                robot.isMoving = true;
            }
            else if (action.type === 'action') {
                robot.currentIcon = getIcon(action.msg);
                logSim(action.msg);

                // --- FEEDBACK RÉEL (TEST) ---
                if (action.msg.includes("Animation: ")) {
                    let animName = action.msg.split(": ")[1];
                    fetch('/api/play_animation', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: animName })
                    });
                } else if (action.msg.includes("Son: ")) {
                    let soundName = action.msg.split(": ")[1];
                    fetch('/api/play_test', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filename: soundName })
                    });
                }
                // -----------------------------

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
        if (msg.includes("Animation")) return "🎨";
        if (msg.includes("Son")) return "🎵";
        return "⚙️";
    }

    function logSim(msg) {
        consoleDiv.innerHTML += `<div>> ${msg}</div>`;
        consoleDiv.scrollTop = consoleDiv.scrollHeight;
    }


    // ============================================================
    // 5. GESTION API (LOAD/SAVE/LIST) & BOUTONS
    // ============================================================

    var simuBtn = document.getElementById('simuBtn'); if (simuBtn) simuBtn.addEventListener('click', runSimulation);
    var previewBtn = document.getElementById('previewBtn'); if (previewBtn) previewBtn.addEventListener('click', generatePreview);

    // Chargement initial des stratégies
    loadBlocklyStrats('stratSelect');

    document.getElementById('loadBtn').addEventListener('click', function () {
        var n = document.getElementById('stratSelect').value;
        if (!n) return;
        fetch('/api/load_strat/' + n)
            .then(r => r.json())
            .then(d => {
                if (d.status === 'success') {
                    workspace.clear();
                    Blockly.Xml.domToWorkspace(Blockly.utils.xml.textToDom(d.xml), workspace);
                    document.getElementById('filename').value = n;
                }
            });
    });

    document.getElementById('saveBtn').addEventListener('click', function () {
        var f = document.getElementById('filename').value;
        if (!f) return;
        var c = Blockly.Python.workspaceToCode(workspace).replace(/^/gm, "    ");
        var final = `from strat.actions import RobotActions\nimport time\nMETADATA={"name":"${f}","score":0}\ndef run(robot: RobotActions):\n    print("Start ${f}")\n${c}\n    print("End")`;

        fetch('/api/save_strat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename: f,
                code: final,
                xml: Blockly.Xml.domToText(Blockly.Xml.workspaceToDom(workspace))
            })
        })
            .then(r => r.json())
            .then(d => {
                if (d.status === 'success') {
                    loadBlocklyStrats('stratSelect');
                    document.getElementById('status').innerText = "✅ Sauvegardé";
                }
            });
    });

    requestAnimationFrame(draw);
});