// ══════════════════════════════════════════════════════════════
//  MATHSPHERE — MAIN.JS  (Updated with all new features)
// ══════════════════════════════════════════════════════════════

// ── STATE ──────────────────────────────────────────────────────
let uploadedImage = null;
const history = {
    math:[], projects:[], mathematician:[], applications:[], graph_analysis:[],
    intuition:[], storytelling:[], socratic:[], concept_map:[],
    daily_puzzle:[], visual_proof:[], career:[], pyq:[]
};
const MAX_HISTORY = 15;

function pushHistory(mode, role, content) {
    if (!history[mode]) history[mode] = [];
    history[mode].push({ role, content });
    if (history[mode].length > MAX_HISTORY * 2) history[mode].splice(0, 2);
}
function getHistory(mode) { return history[mode] || []; }

// ── TAB ────────────────────────────────────────────────────────
function switchTab(mode, btn) {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    if (btn) btn.classList.add('active');
    const el = document.getElementById(`tab-${mode}`);
    if (el) el.classList.add('active');
}

// ── FILL HELPERS ───────────────────────────────────────────────
function fillQuestion(text) {
    const inp = document.getElementById('userInput');
    inp.value = text;
    autoResize(inp);
    inp.focus();
}

function fillPanel(mode, text) {
    // Map mode to input id — handle both naming conventions
    const idCandidates = [
        `${mode}Input`,
        `${mode}sInput`,
    ];
    let inp = null;
    for (const id of idCandidates) {
        inp = document.getElementById(id);
        if (inp) break;
    }
    if (!inp) {
        console.error('fillPanel: input not found for mode:', mode);
        return;
    }
    inp.value = text;
    autoResize(inp);
    sendPanel(mode);
}

// ── INPUT HELPERS ──────────────────────────────────────────────
function handleKey(event, mode) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        mode === 'math' ? sendMessage() : sendPanel(mode);
    }
}
function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 100) + 'px';
}

// ── IMAGE ──────────────────────────────────────────────────────
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        uploadedImage = { data: e.target.result.split(',')[1], media_type: file.type, preview: e.target.result };
        document.getElementById('previewImg').src = e.target.result;
        document.getElementById('imagePreview').classList.remove('hidden');
    };
    reader.readAsDataURL(file);
}
function removeImage() {
    uploadedImage = null;
    document.getElementById('imagePreview').classList.add('hidden');
    document.getElementById('imageUpload').value = '';
}

// ── BADGE ──────────────────────────────────────────────────────
function setBadge(text, color) {
    const b = document.getElementById('apiBadge');
    if (!b) return;
    b.textContent = text;
    b.style.color = color;
    b.style.borderColor = color + '40';
    b.style.background = color + '12';
}

// ── TYPING ─────────────────────────────────────────────────────
function addTyping(winId) {
    const win = document.getElementById(winId);
    if (!win) return;
    const el = document.createElement('div');
    el.id = 'typing_' + winId;
    el.className = 'message bot';
    el.innerHTML = `<div class="msg-avatar">⚡</div>
        <div class="typing-indicator"><span></span><span></span><span></span></div>`;
    win.appendChild(el);
    win.scrollTop = win.scrollHeight;
}
function removeTyping(winId) {
    const el = document.getElementById('typing_' + winId);
    if (el) el.remove();
}

// ── UTILS (renderer.js handles esc, linkify, renderMathContent, typesetEl) ──

// ── ADD MESSAGE (chat window) ───────────────────────────────────
function addMessage(role, content, imgPreview = null, source = null) {
    const win = document.getElementById('chatWindow');
    if (!win) return;
    const welcome = win.querySelector('.welcome');
    if (welcome) welcome.style.display = 'none';

    const isError = role === 'bot' && isQuotaError(content);
    const isOlympiad = role === 'bot' && source?.includes('✦');

    const msg = document.createElement('div');
    msg.className = `message ${role}${isOlympiad ? ' olympiad-mode' : ''}`;

    const avatar = document.createElement('div');
    avatar.className = 'msg-avatar';
    avatar.textContent = role === 'user' ? 'U' : '⚡';

    const contentDiv = document.createElement('div');
    contentDiv.className = `msg-content${isError ? ' error-bubble' : ''}`;

    if (imgPreview) {
        const img = document.createElement('img');
        img.src = imgPreview;
        contentDiv.appendChild(img);
    }

    const textDiv = document.createElement('div');
    textDiv.innerHTML = isError ? renderErrorMessage(content) : renderMathContent(content);
    contentDiv.appendChild(textDiv);

    if (role === 'bot' && !isError) {
        const footer = document.createElement('div');
        footer.className = 'msg-footer';
        if (source) {
            const s = document.createElement('span');
            s.className = isOlympiad ? 'source-tag source-tag--pro' : 'source-tag';
            s.textContent = isOlympiad ? `✦ Olympiad · ${source}` : `via ${source}`;
            footer.appendChild(s);
        }
        const whyBtn = document.createElement('button');
        whyBtn.className = 'why-btn';
        whyBtn.textContent = '💡 Why does this work?';
        whyBtn.dataset.context = content.substring(0, 600);
        whyBtn.onclick = () => askWhy(whyBtn.dataset.context);
        footer.appendChild(whyBtn);
        contentDiv.appendChild(footer);
    }

    msg.appendChild(avatar);
    msg.appendChild(contentDiv);
    win.appendChild(msg);
    win.scrollTop = win.scrollHeight;
    if (!isError) typesetEl(contentDiv);
}

// ── SEND MATH ──────────────────────────────────────────────────
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    const difficulty = document.getElementById('difficulty')?.value || 'Undergraduate';
    if (!message && !uploadedImage) return;

    addMessage('user', message || 'Analyzing image…', uploadedImage?.preview);
    input.value = '';
    input.style.height = 'auto';

    const imageData = uploadedImage ? { data: uploadedImage.data, media_type: uploadedImage.media_type } : null;
    removeImage();
    addTyping('chatWindow');
    setBadge('Thinking…', '#f5a623');

    const fullMessage = message + (difficulty ? `\n[Difficulty: ${difficulty}]` : '');
    pushHistory('math', 'user', fullMessage);

    try {
        const res = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: fullMessage,
                mode: 'math',
                image: imageData,
                history: getHistory('math').slice(0, -1)
            })
        });
        const data = await res.json();
        removeTyping('chatWindow');
        const reply = data.response || data.error;
        pushHistory('math', 'assistant', reply);
        addMessage('bot', reply, null, data.source);
        const isErr = isQuotaError(reply);
        setBadge(isErr ? 'Quota limit' : (data.source + ' ✓'), isErr ? '#ef4444' : '#22c55e');
    } catch (e) {
        removeTyping('chatWindow');
        addMessage('bot', 'Connection error. Is the Flask server running?');
        setBadge('Error', '#ef4444');
    }
}

// ── SEND PANEL ─────────────────────────────────────────────────
async function sendPanel(mode) {
    // Find input element
    const idCandidates = [`${mode}Input`, `${mode}sInput`];
    let inputEl = null;
    for (const id of idCandidates) {
        inputEl = document.getElementById(id);
        if (inputEl) break;
    }
    if (!inputEl) { console.error('Input not found for mode:', mode); return; }

    const message = inputEl.value.trim();
    if (!message) return;

    // Find window — try both naming conventions
    const winIdCandidates = [
        `${mode}Window`,
        `${mode}sWindow`,
        // for compound names like concept_map
        mode.replace('_', '') + 'Window'
    ];
    let win = null;
    for (const id of winIdCandidates) {
        win = document.getElementById(id);
        if (win) break;
    }
    if (!win) { console.error('Window not found for mode:', mode); return; }

    const welcome = win.querySelector('.panel-welcome');
    if (welcome) welcome.style.display = 'none';

    // User query bubble
    const userDiv = document.createElement('div');
    userDiv.className = 'user-query';
    userDiv.textContent = message;
    win.appendChild(userDiv);

    inputEl.value = '';
    inputEl.style.height = 'auto';

    addTypingPanel(win.id);
    setBadge('Thinking…', '#f5a623');

    // Build contextual message
    const prompts = {
        projects:      `Give me 5 detailed mathematics project ideas related to: ${message}`,
        mathematician: `Tell me everything about the mathematician: ${message}`,
        applications:  `Give me 12 detailed real-world applications of: ${message}`,
        intuition:     `Build my intuition for this mathematical concept: ${message}`,
        storytelling:  `Tell me the complete mathematical story of: ${message}`,
        socratic:      `Help me think through this using the Socratic method: ${message}`,
        concept_map:   `Generate a complete concept map for: ${message}`,
        daily_puzzle:  message,
        visual_proof:  `Explain the visual proof of: ${message}`,
        career:        `Give me a complete career pathway guide for someone interested in: ${message}`
    };

    const fullMessage = prompts[mode] || message;
    pushHistory(mode, 'user', fullMessage);

    try {
        const res = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: fullMessage,
                mode,
                history: getHistory(mode).slice(0, -1)
            })
        });
        const data = await res.json();
        removeTypingPanel(win.id);
        const reply = data.response || data.error;
        pushHistory(mode, 'assistant', reply);

        const respDiv = document.createElement('div');
        respDiv.className = 'panel-response';
        respDiv.innerHTML = isQuotaError(reply)
            ? renderErrorMessage(reply)
            : renderMathContent(reply);
        win.appendChild(respDiv);
        win.scrollTop = win.scrollHeight;
        if (!isQuotaError(reply)) typesetEl(respDiv);
        setBadge(data.source + ' ✓', '#22c55e');
    } catch (e) {
        removeTypingPanel(win.id);
        console.error('Panel send error:', e);
        setBadge('Error', '#ef4444');
    }
}

function addTypingPanel(winId) {
    const win = document.getElementById(winId);
    if (!win) return;
    const el = document.createElement('div');
    el.id = 'typing_panel_' + winId;
    el.className = 'message bot';
    el.innerHTML = `<div class="msg-avatar">⚡</div>
        <div class="typing-indicator"><span></span><span></span><span></span></div>`;
    win.appendChild(el);
    win.scrollTop = win.scrollHeight;
}
function removeTypingPanel(winId) {
    const el = document.getElementById('typing_panel_' + winId);
    if (el) el.remove();
}

// ── WHY BUTTON ─────────────────────────────────────────────────
async function askWhy(context) {
    const msg = `Give a deeper conceptual explanation of WHY this mathematical method works. Focus on intuition and underlying theory. Based on: "${context}"`;
    addMessage('user', '💡 Why does this work?');
    pushHistory('math', 'user', msg);
    addTyping('chatWindow');

    try {
        const res = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, mode: 'math', history: getHistory('math').slice(0,-1) })
        });
        const data = await res.json();
        removeTyping('chatWindow');
        const reply = data.response || 'Could not fetch explanation.';
        pushHistory('math', 'assistant', reply);
        addMessage('bot', reply, null, data.source);
    } catch {
        removeTyping('chatWindow');
        addMessage('bot', 'Could not fetch explanation.');
    }
}

// ── CLEAR CHAT ─────────────────────────────────────────────────
function clearChat() {
    history.math = [];
    const win = document.getElementById('chatWindow');
    win.innerHTML = `
    <div class="welcome">
        <div class="welcome-bg"></div>
        <div class="welcome-inner">
            <div class="welcome-symbol">∑</div>
            <h1 class="welcome-title">Ask Anupam</h1>
            <p class="welcome-sub">Your personal mathematics guide — Class 11 to IMO level.<br>Ask anything. Upload any problem. Every answer is step by step.</p>
            <div class="welcome-chips">
                <button class="chip" onclick="fillQuestion('Explain eigenvalues with examples')">Eigenvalues</button>
                <button class="chip" onclick="fillQuestion('What is Bayes theorem and how to apply it?')">Bayes Theorem</button>
                <button class="chip" onclick="fillQuestion('Prove that √2 is irrational')">Prove √2 irrational</button>
                <button class="chip" onclick="fillQuestion('Explain Fourier Transform intuitively')">Fourier Transform</button>
            </div>
            <div class="difficulty-row">
                <span class="diff-label">Level</span>
                <select id="difficulty" class="diff-select">
                    <option value="Class 11/12">Class 11 / 12</option>
                    <option value="Undergraduate" selected>Undergraduate</option>
                    <option value="JEE Advanced / IMO">JEE Advanced / IMO</option>
                    <option value="Research Level">Research Level</option>
                </select>
                <button class="clear-btn" onclick="clearChat()">Clear Chat</button>
            </div>
        </div>
    </div>`;
    setBadge('● Ready', '#22c55e');
}

// ══════════════════════════════════════════════════════════════
//  GRAPH PLOTTER
// ══════════════════════════════════════════════════════════════

function buildEvaluator(raw) {
    let expr = raw.trim();

    expr = expr.replace(/\^/g, '**');
    expr = expr.replace(/(\d)(x)/gi,  '$1*$2');
    expr = expr.replace(/(\d)\(/g,    '$1*(');
    expr = expr.replace(/\)(x)/gi,    ')*$1');
    expr = expr.replace(/\)(\d)/g,    ')*$1');

    const fns = [
        ['log10','Math.log10'],['log2','Math.log2'],
        ['asin','Math.asin'],['acos','Math.acos'],['atan','Math.atan'],
        ['sinh','Math.sinh'],['cosh','Math.cosh'],['tanh','Math.tanh'],
        ['sqrt','Math.sqrt'],['cbrt','Math.cbrt'],
        ['ceil','Math.ceil'],['floor','Math.floor'],['round','Math.round'],
        ['sign','Math.sign'],['exp','Math.exp'],['abs','Math.abs'],
        ['sin','Math.sin'],['cos','Math.cos'],['tan','Math.tan'],
        ['log','Math.log'],['ln','Math.log'],
    ];
    fns.forEach(([n,m]) => expr = expr.replace(new RegExp(`\\b${n}\\b`,'g'), m));
    expr = expr.replace(/\bpi\b/gi, 'Math.PI');
    expr = expr.replace(/(?<![A-Za-z.])e(?![A-Za-z.(])/g, 'Math.E');

    try { new Function('x', `'use strict'; return ${expr};`); }
    catch { throw new Error(`Cannot parse: ${raw}`); }
    return new Function('x', `'use strict'; return ${expr};`);
}

function generatePoints(evalFn, xMin, xMax, steps) {
    const xs = [], ys = [];
    const step = (xMax - xMin) / steps;
    for (let i = 0; i <= steps; i++) {
        const x = xMin + i * step;
        xs.push(parseFloat(x.toFixed(6)));
        try {
            const y = evalFn(x);
            ys.push((isFinite(y) && Math.abs(y) < 1e8)
                ? parseFloat(y.toFixed(8)) : null);
        } catch { ys.push(null); }
    }
    return { xs, ys };
}

function quickPlot(fn) {
    document.getElementById('functionInput').value = fn;
    plotFunction();
}

async function plotFunction() {
    const raw = document.getElementById('functionInput').value.trim();
    if (!raw) return;

    const plotArea = document.getElementById('plotArea');
    const analysisDiv = document.getElementById('graphAnalysis');

    plotArea.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;
        height:300px;color:var(--text3);font-size:13px;">Plotting f(x) = ${esc(raw)}…</div>`;
    analysisDiv.style.display = 'none';
    await new Promise(r => setTimeout(r, 30));

    let evalFn;
    try {
        evalFn = buildEvaluator(raw);
    } catch (e) {
        plotArea.innerHTML = `<div style="display:flex;flex-direction:column;align-items:center;
            justify-content:center;height:300px;color:#ef4444;font-size:13px;padding:20px;text-align:center;">
            <div style="margin-bottom:8px;">Cannot parse: <code style="color:var(--amber)">${esc(raw)}</code></div>
            <div style="color:var(--text3);font-size:11px;">
            Try: x^2 · sin(x) · cos(x) · x^3-3*x · 1/x · sqrt(x) · e^x · ln(x) · abs(x)</div></div>`;
        return;
    }

    try {
        const { xs, ys } = generatePoints(evalFn, -10, 10, 800);
        const validYs = ys.filter(y => y !== null);

        if (!validYs.length) {
            plotArea.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;
                height:300px;color:#ef4444;font-size:13px;">No real values in x ∈ [−10, 10].</div>`;
            return;
        }

        const yMin = Math.max(Math.min(...validYs), -100);
        const yMax = Math.min(Math.max(...validYs), 100);
        const yPad = Math.max((yMax - yMin) * 0.1, 0.5);

        Plotly.newPlot('plotArea', [{
            x: xs, y: ys,
            type: 'scatter', mode: 'lines',
            line: { color: '#00d4aa', width: 2.5, shape: 'linear' },
            name: `f(x) = ${raw}`,
            connectgaps: false,
            hovertemplate: 'x = %{x:.3f}<br>f(x) = %{y:.4f}<extra></extra>'
        }], {
            paper_bgcolor: '#06060f', plot_bgcolor:  '#0a0a18',
            font: { color: '#8888b0', size: 11, family: 'DM Sans' },
            margin: { t: 44, r: 24, b: 52, l: 58 },
            title: {
                text: `f(x) = ${raw}`,
                font: { color: '#00d4aa', size: 14, family: 'Syne' },
                x: 0.5, xanchor: 'center'
            },
            xaxis: {
                gridcolor: '#161628', zerolinecolor: '#f5a623', zerolinewidth: 1.5,
                linecolor: '#1e1e3a', tickfont: { color: '#44446a', size: 10 },
                title: { text: 'x', font: { color: '#44446a' } }
            },
            yaxis: {
                gridcolor: '#161628', zerolinecolor: '#f5a623', zerolinewidth: 1.5,
                linecolor: '#1e1e3a', tickfont: { color: '#44446a', size: 10 },
                title: { text: 'f(x)', font: { color: '#44446a' } },
                range: [yMin - yPad, yMax + yPad]
            },
            hovermode: 'x unified',
            hoverlabel: {
                bgcolor: '#0a0a18', bordercolor: '#00d4aa',
                font: { color: '#eeeef8', size: 12, family: 'JetBrains Mono' }
            }
        }, {
            responsive: true, displayModeBar: true, displaylogo: false,
            modeBarButtonsToRemove: ['toImage','sendDataToCloud','lasso2d','select2d']
        });

        await fetchGraphAnalysis(raw);

    } catch (e) {
        console.error('Plot error:', e);
        plotArea.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;
            height:300px;color:#ef4444;font-size:13px;">Plotting failed. Try a simpler expression.</div>`;
    }
}

async function fetchGraphAnalysis(fn) {
    const div = document.getElementById('graphAnalysis');
    div.style.display = 'block';
    div.innerHTML = `<div style="display:flex;gap:8px;align-items:center;color:var(--text3);font-size:13px;">
        <div class="typing-indicator" style="padding:0;background:transparent;border:none;">
        <span></span><span></span><span></span></div>&nbsp;Analyzing f(x) = ${esc(fn)}…</div>`;

    try {
        const res = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: `Analyze the function f(x) = ${fn}`,
                mode: 'graph_analysis',
                history: []
            })
        });
        const data = await res.json();
        div.innerHTML = renderMathContent(data.response || data.error);
        typesetEl(div);
    } catch {
        div.innerHTML = '<p style="color:var(--text3)">Analysis unavailable.</p>';
    }
}

// ══════════════════════════════════════════════════════════════
//  EXAMINATION HUB — Static data + interaction
// ══════════════════════════════════════════════════════════════

const EXAM_DATA = {
    gate: {
        name: "GATE Mathematics (MA)",
        color: "teal",
        icon: "🏛️",
        syllabus: {
            "Calculus": ["Functions of two or more variables, continuity, directional derivatives", "Partial derivatives, total derivative, maxima and minima, saddle point", "Method of Lagrange multipliers", "Double and triple integrals and their applications", "Line integrals and surface integrals", "Green's theorem, Stokes' theorem, Gauss divergence theorem"],
            "Linear Algebra": ["Finite-dimensional vector spaces over real and complex number fields", "Linear transformations and their matrix representations, rank", "Systems of linear equations, eigenvalues and eigenvectors", "Minimal polynomial, Cayley-Hamilton theorem", "Diagonalisation, Jordan canonical form", "Symmetric, skew-symmetric, Hermitian, skew-Hermitian matrices"],
            "Real Analysis": ["Sequences and series of real numbers, convergence criteria", "Limits, continuity, uniform continuity, differentiability", "Mean value theorems, indeterminate forms, L'Hopital's rule", "Maxima and minima of functions of single and two variables", "Riemann integration, improper integrals", "Sequences and series of functions, uniform convergence"],
            "Complex Analysis": ["Algebra of complex numbers, the complex plane", "Polynomials, power series, transcendental functions", "Analytic functions, Cauchy-Riemann equations", "Contour integral, Cauchy's theorem, Cauchy's integral formula", "Liouville's theorem, maximum modulus principle", "Taylor series, Laurent series, calculus of residues"],
            "Ordinary Differential Equations": ["First order ODE, exactness, integrating factor", "Second order linear ODE with constant coefficients", "Variation of parameters, Cauchy-Euler equation", "Power series solutions, Legendre and Bessel equations", "Systems of linear first order ODE", "Sturm-Liouville boundary value problems"],
            "Algebra": ["Groups, subgroups, normal subgroups, quotient groups", "Homomorphisms, isomorphisms, permutation groups", "Rings, ideals, prime and maximal ideals, quotient rings", "Fields, finite fields, field extensions"],
            "Functional Analysis": ["Normed linear spaces, Banach spaces, Hilbert spaces", "Bounded linear operators and functionals", "Hahn-Banach theorem, open mapping theorem, closed graph theorem", "Riesz representation theorem"],
            "Numerical Analysis": ["Systems of linear equations: Gaussian elimination, LU decomposition", "Iterative methods: Gauss-Seidel, Jacobi", "Nonlinear equations: Newton-Raphson, bisection, secant method", "Interpolation: Lagrange and Newton, finite differences", "Numerical integration: Trapezoidal rule, Simpson's rule", "Numerical solution of ODEs: Euler's method, Runge-Kutta"],
            "Partial Differential Equations": ["First order linear and quasilinear PDE", "Second order PDE: classification, canonical forms", "Method of separation of variables for Laplace, heat and wave equations", "D'Alembert's solution of wave equation"],
            "Topology": ["Basis, subspace topology, order topology, product topology", "Metric topology, quotient topology", "Connectedness, compactness, Heine-Borel theorem", "Urysohn's lemma, Tietze extension theorem"],
            "Linear Programming": ["Linear programming problem, feasible and optimal solutions", "Graphical method, simplex method", "Duality in linear programming, transportation problem"],
        },
        pattern: {
            duration: '3 Hours',
            total_marks: 100,
            general_aptitude: '15 marks (GA Section)',
            core_math: '85 marks',
            sections: [
                { name: 'General Aptitude (GA)', questions: 10, marks: 15, type: 'MCQ', negative: '1/3 for 1-mark, 2/3 for 2-mark MCQs' },
                { name: 'Mathematics Core', questions: 55, marks: 85, type: 'MCQ + MSQ + NAT', negative: 'Only MCQs have negative marking' },
            ],
            question_types: [
                { type: 'MCQ', desc: 'Multiple Choice — one correct answer', negative: 'Yes (−1/3 or −2/3)' },
                { type: 'MSQ', desc: 'Multiple Select — one or more correct answers', negative: 'No' },
                { type: 'NAT', desc: 'Numerical Answer Type — type the number', negative: 'No' },
            ],
            notes: ['Exam conducted by IITs on rotation (2026: IIT Guwahati)', 'Score valid for 3 years', 'CBT (Computer Based Test) mode'],
        },
        weightage: [
            { topic: 'Linear Algebra', marks: '10–12', priority: 'high' },
            { topic: 'Real Analysis', marks: '10–12', priority: 'high' },
            { topic: 'Calculus', marks: '8–10', priority: 'high' },
            { topic: 'Complex Analysis', marks: '7–9', priority: 'high' },
            { topic: 'Ordinary Differential Equations', marks: '7–9', priority: 'high' },
            { topic: 'Algebra (Groups & Rings)', marks: '6–8', priority: 'medium' },
            { topic: 'Functional Analysis', marks: '5–7', priority: 'medium' },
            { topic: 'Numerical Analysis', marks: '5–7', priority: 'medium' },
            { topic: 'Partial Differential Equations', marks: '5–7', priority: 'medium' },
            { topic: 'Topology', marks: '4–6', priority: 'medium' },
            { topic: 'Linear Programming', marks: '3–5', priority: 'low' },
            { topic: 'General Aptitude', marks: '15', priority: 'high' },
        ],
    },
    csirnet: {
        name: "CSIR NET Mathematical Sciences",
        color: "rose",
        icon: "🔬",
        syllabus: {
            "Unit 1 — Analysis & Linear Algebra": [
                "Elementary set theory, finite, countable and uncountable sets",
                "Real number system as a complete ordered field, Archimedean property",
                "Sequences and series, convergence, limsup, liminf",
                "Bolzano-Weierstrass theorem, Heine-Borel theorem",
                "Continuity, uniform continuity, differentiability, mean value theorem",
                "Functions of several variables, maxima, minima",
                "Riemann integration, improper integrals",
                "Vector spaces, subspaces, linear dependence, basis, dimension",
                "Linear transformations, rank-nullity, matrix representation",
                "Systems of linear equations, eigenvalues, eigenvectors",
                "Cayley-Hamilton theorem, symmetric matrices, positive definite matrices",
                "LU decomposition, QR factorization",
            ],
            "Unit 2 — Complex Analysis, Topology & Algebra": [
                "Algebra of complex numbers, analytic functions, Cauchy-Riemann equations",
                "Contour integrals, Cauchy's theorem, Cauchy integral formula",
                "Liouville's theorem, Taylor and Laurent series",
                "Calculus of residues, conformal mappings, Mobius transformations",
                "Metric spaces: sequences, completeness, compactness, connectedness",
                "Normed linear spaces, Banach spaces",
                "Permutations, combinations, pigeonhole principle",
                "Fundamental theorem of arithmetic, divisibility, congruences",
                "Chinese Remainder Theorem, Euler's phi-function",
                "Groups, subgroups, normal subgroups, Lagrange's theorem",
                "Homomorphisms, quotient groups, Sylow theorems",
                "Rings, ideals, integral domains, fields",
            ],
            "Unit 3 — ODEs, PDEs, Numerical Analysis, Classical Mechanics": [
                "First order ODEs: existence, uniqueness, Picard's theorem",
                "General theory of nth order linear ODEs, Wronskian",
                "Power series solutions, Legendre equation, Bessel equation",
                "Partial differential equations: classification, characteristics",
                "Wave equation, heat equation, Laplace equation",
                "Boundary value problems, separation of variables",
                "Numerical solution of algebraic equations: bisection, Newton-Raphson",
                "Numerical integration: Trapezoidal, Simpson rules",
                "Numerical solution of ODEs: Euler, predictor-corrector methods",
                "Calculus of variations: Euler-Lagrange equation",
                "Classical mechanics: Lagrangian and Hamiltonian formulations",
                "Conservation laws, central force problem",
            ],
            "Unit 4 — Statistics & Probability": [
                "Probability theory, random variables, probability distributions",
                "Standard distributions: Binomial, Poisson, Normal, Exponential, Gamma",
                "Sampling distributions, Central Limit Theorem",
                "Methods of estimation: MLE, method of moments",
                "Confidence intervals, hypothesis testing",
                "Chi-square test, t-test, F-test",
                "Regression and correlation analysis",
                "Markov chains, stationary distributions",
                "Bayesian inference basics",
                "Simple random sampling, stratified sampling",
            ],
        },
        pattern: {
            duration: '3 Hours',
            total_marks: 200,
            sections: [
                { name: 'Part A — General Aptitude', questions: '20 (attempt 15)', marks: 30, type: 'MCQ', negative: '25% for wrong answer' },
                { name: 'Part B — Subject (Moderate)', questions: '40 (attempt 25)', marks: 75, type: 'MCQ', negative: '25% for wrong answer' },
                { name: 'Part C — Subject (Advanced)', questions: '60 (attempt 20)', marks: 95, type: 'MCQ', negative: 'No negative marking' },
            ],
            question_types: [
                { type: 'Part A', desc: 'General Science, Quantitative Reasoning, Research Aptitude', negative: 'Yes (25%)' },
                { type: 'Part B', desc: 'Standard level subject questions from syllabus', negative: 'Yes (25%)' },
                { type: 'Part C', desc: 'Higher-order, application-based subject questions', negative: 'No' },
            ],
            notes: ['Conducted by NTA twice a year (June and December)', 'Qualifies for JRF (Junior Research Fellowship) and Lectureship', 'All MCQ based exam'],
        },
        weightage: [
            { topic: 'Linear Algebra', marks: '20–25', priority: 'high' },
            { topic: 'Real Analysis', marks: '20–25', priority: 'high' },
            { topic: 'Complex Analysis', marks: '15–20', priority: 'high' },
            { topic: 'Abstract Algebra', marks: '15–18', priority: 'high' },
            { topic: 'ODEs & PDEs', marks: '12–15', priority: 'high' },
            { topic: 'Topology', marks: '10–12', priority: 'medium' },
            { topic: 'Numerical Analysis', marks: '8–10', priority: 'medium' },
            { topic: 'Statistics & Probability', marks: '10–15', priority: 'medium' },
            { topic: 'Calculus of Variations', marks: '5–8', priority: 'low' },
            { topic: 'Classical Mechanics', marks: '5–8', priority: 'low' },
            { topic: 'General Aptitude (Part A)', marks: 30, priority: 'high' },
        ],
    },
    iitjam: {
        name: "IIT JAM Mathematics (MA)",
        color: "amber",
        icon: "⚙️",
        syllabus: {
            "Sequences & Series of Real Numbers": [
                "Sequences and series of real numbers, convergence criteria",
                "Absolute and conditional convergence, tests for convergence",
                "Power series, radius of convergence",
                "Cauchy's criterion, Ratio test, Root test, Leibniz test",
            ],
            "Functions of One Real Variable": [
                "Limits, continuity, intermediate value property",
                "Differentiability, Rolle's theorem, mean value theorem",
                "L'Hopital's rule, Taylor's theorem",
                "Maxima and minima, curve sketching",
            ],
            "Functions of Two or Three Real Variables": [
                "Limit, continuity, partial derivatives",
                "Differentiability, gradient, directional derivatives",
                "Maxima and minima with Lagrange multipliers",
                "Double and triple integrals",
            ],
            "Integral Calculus": [
                "Integration as the inverse of differentiation",
                "Definite integrals and their properties",
                "Fundamental theorem of calculus",
                "Double and triple integrals, change of order",
                "Calculating surface area and volume",
            ],
            "Differential Equations": [
                "Ordinary differential equations of first order (separable, homogeneous, exact)",
                "Integrating factor, Bernoulli's equation",
                "Second order linear ODE with constant and variable coefficients",
                "Variation of parameters, Cauchy-Euler equation",
                "Systems of first order ODEs",
            ],
            "Vector Calculus": [
                "Scalar and vector fields, gradient, divergence, curl",
                "Line integrals, surface integrals, volume integrals",
                "Green's theorem, Stokes' theorem, Gauss divergence theorem",
            ],
            "Group Theory": [
                "Groups, subgroups, Abelian groups, cyclic groups",
                "Normal subgroups, quotient groups, Lagrange's theorem",
                "Permutation groups, homomorphisms, isomorphism theorems",
            ],
            "Linear Algebra": [
                "Finite-dimensional vector spaces, basis, dimension",
                "Linear transformations, rank-nullity theorem",
                "Matrices, determinants, system of linear equations",
                "Eigenvalues, eigenvectors, Cayley-Hamilton theorem",
                "Symmetric matrices, positive definite matrices",
            ],
            "Real Analysis": [
                "Interior, closure, boundary of sets in R",
                "Compact sets, connected sets",
                "Limits and continuity of functions",
                "Uniform continuity, differentiability",
                "Sequences and series of functions, uniform convergence",
            ],
        },
        pattern: {
            duration: '3 Hours',
            total_marks: 100,
            sections: [
                { name: 'Section A — MCQ', questions: 30, marks: '30×(1 or 2) = 50', type: 'MCQ', negative: '1/3 for 1-mark, 2/3 for 2-mark' },
                { name: 'Section B — MSQ', questions: 10, marks: '10×2 = 20', type: 'MSQ (1 or more correct)', negative: 'No' },
                { name: 'Section C — NAT', questions: 20, marks: '20×(1 or 2) = 30', type: 'Numerical Answer Type', negative: 'No' },
            ],
            question_types: [
                { type: 'MCQ (Sec A)', desc: '10 questions of 1 mark + 20 questions of 2 marks', negative: 'Yes' },
                { type: 'MSQ (Sec B)', desc: '10 questions of 2 marks — may have multiple correct answers', negative: 'No' },
                { type: 'NAT (Sec C)', desc: '10 of 1 mark + 10 of 2 marks — enter number via virtual keypad', negative: 'No' },
            ],
            notes: ['Conducted by IITs for MSc and Integrated PhD admissions', '~3000 seats at IITs, IISc, NIT, IISER', 'CBT mode, English only', 'No age restriction, all nationalities eligible'],
        },
        weightage: [
            { topic: 'Calculus (Single Variable)', marks: '15–20', priority: 'high' },
            { topic: 'Linear Algebra', marks: '12–18', priority: 'high' },
            { topic: 'Real Analysis', marks: '12–16', priority: 'high' },
            { topic: 'Differential Equations', marks: '10–14', priority: 'high' },
            { topic: 'Multivariable Calculus', marks: '10–14', priority: 'high' },
            { topic: 'Vector Calculus', marks: '8–12', priority: 'medium' },
            { topic: 'Group Theory', marks: '8–12', priority: 'medium' },
            { topic: 'Sequences & Series', marks: '8–10', priority: 'medium' },
            { topic: 'Integral Calculus', marks: '6–10', priority: 'medium' },
        ],
    },
};

// Topic lists for PYQ selector
const PYQ_TOPICS = {
    gate: ['Real Analysis','Linear Algebra','Complex Analysis','ODEs','PDEs','Algebra','Functional Analysis','Numerical Analysis','Topology','Linear Programming','Calculus'],
    csirnet: ['Real Analysis','Linear Algebra','Complex Analysis','Abstract Algebra','Topology','ODEs','PDEs','Statistics','Numerical Analysis','Classical Mechanics'],
    iitjam: ['Calculus','Real Analysis','Linear Algebra','Differential Equations','Vector Calculus','Group Theory','Sequences & Series','Multivariable Calculus'],
};

let currentExam = 'gate';
let currentExamTab = 'syllabus';
let currentPYQExam = 'gate';

// ── EXAM HUB LOGIC ─────────────────────────────────────────────
function selectExam(exam) {
    currentExam = exam;
    document.querySelectorAll('.exam-sel-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('esel-' + exam).classList.add('active');
    renderExamContent();
}

function switchExamTab(tab, btn) {
    currentExamTab = tab;
    document.querySelectorAll('.exam-tab-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    renderExamContent();
}

function renderExamContent() {
    const data = EXAM_DATA[currentExam];
    const area = document.getElementById('examContentArea');
    if (!area || !data) return;

    if (currentExamTab === 'syllabus') {
        let html = `<div class="exam-syllabus">`;
        for (const [unit, topics] of Object.entries(data.syllabus)) {
            html += `<div class="exam-unit">
                <div class="exam-unit-title">${unit}</div>
                <ul class="exam-unit-list">` +
                topics.map(t => `<li>${t}</li>`).join('') +
                `</ul></div>`;
        }
        html += `</div>`;
        area.innerHTML = html;
    }

    else if (currentExamTab === 'pattern') {
        const p = data.pattern;
        let html = `<div class="exam-pattern">
            <div class="exam-pattern-grid">
                <div class="ep-card ep-teal"><div class="ep-val">${p.duration}</div><div class="ep-label">Duration</div></div>
                <div class="ep-card ep-amber"><div class="ep-val">${p.total_marks}</div><div class="ep-label">Total Marks</div></div>
                <div class="ep-card ep-rose"><div class="ep-val">CBT</div><div class="ep-label">Mode</div></div>
                <div class="ep-card ep-purple"><div class="ep-val">3</div><div class="ep-label">Sections</div></div>
            </div>
            <div class="exam-sections-title">Section-Wise Breakdown</div>
            <div class="exam-sections">`;
        for (const s of p.sections) {
            html += `<div class="exam-section-row">
                <div class="esr-name">${s.name}</div>
                <div class="esr-details">
                    <span class="esr-chip esr-q">📝 ${s.questions} Questions</span>
                    <span class="esr-chip esr-m">⚖️ ${s.marks} Marks</span>
                    <span class="esr-chip esr-t">📋 ${s.type}</span>
                    <span class="esr-chip esr-n ${s.negative.startsWith('No') ? 'esr-no' : 'esr-yes'}">
                        ${s.negative.startsWith('No') ? '✅ No Negative' : '⚠️ ' + s.negative}
                    </span>
                </div>
            </div>`;
        }
        html += `</div>
            <div class="exam-notes">` +
            p.notes.map(n => `<div class="exam-note">ℹ️ ${n}</div>`).join('') +
            `</div></div>`;
        area.innerHTML = html;
    }

    else if (currentExamTab === 'weightage') {
        const w = data.weightage;
        let html = `<div class="exam-weightage">
            <p class="ew-note">Based on analysis of 5+ years of previous papers. Marks are approximate ranges.</p>`;
        for (const item of w) {
            const pClass = item.priority === 'high' ? 'ewp-high' : item.priority === 'medium' ? 'ewp-med' : 'ewp-low';
            const pLabel = item.priority === 'high' ? '🔴 High Priority' : item.priority === 'medium' ? '🟡 Medium' : '🟢 Lower';
            html += `<div class="ew-row">
                <div class="ew-topic">${item.topic}</div>
                <div class="ew-marks">${item.marks} marks</div>
                <div class="ew-priority ${pClass}">${pLabel}</div>
            </div>`;
        }
        html += `</div>`;
        area.innerHTML = html;
    }
}

// ── PYQ LOGIC ──────────────────────────────────────────────────
function selectPYQExam(exam) {
    currentPYQExam = exam;
    document.querySelectorAll('.pyq-sel-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('psel-' + exam).classList.add('active');
    renderPYQTopics();
}

function renderPYQTopics() {
    const bar = document.getElementById('pyqTopicBar');
    if (!bar) return;
    const topics = PYQ_TOPICS[currentPYQExam] || [];
    bar.innerHTML = topics.map(t =>
        `<button class="pyq-topic-btn" onclick="askPYQ('${currentPYQExam}','${t}','recent')">${t}</button>`
    ).join('');
}

function askPYQ(exam, topic, year) {
    const examNames = { gate: 'GATE Mathematics (MA)', csirnet: 'CSIR NET Mathematical Sciences', iitjam: 'IIT JAM Mathematics' };
    const msg = `Give me ${year === 'recent' ? 'recent' : year} previous year questions from ${examNames[exam]} on the topic: ${topic}. Include complete solutions.`;
    const inp = document.getElementById('pyqInput');
    if (inp) { inp.value = msg; autoResize(inp); }
    const welcome = document.getElementById('pyqWelcome');
    if (welcome) welcome.style.display = 'none';
    sendPanel('pyq');
}

// Init exam hub and PYQ on page load
window.addEventListener('DOMContentLoaded', () => {
    renderExamContent();
    renderPYQTopics();
});