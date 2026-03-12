// ══════════════════════════════════════════════════════════════
//  MATHSPHERE — MAIN.JS  (Corrected Final)
//  Fixes:
//  1. history object includes ALL modes
//  2. image upload sends mime_type (not media_type) — matches app.py
//  3. 429 rate-limit handling on all fetch calls
//  4. askPYQ uses setTimeout before sendPanel (input timing fix)
//  5. sendPanel window lookup handles pyq nested inside .pyq-body
//  6. isQuotaError / renderErrorMessage defined locally too
//  7. MAX_MESSAGE_LENGTH validated client-side
// ══════════════════════════════════════════════════════════════

// ── STATE ──────────────────────────────────────────────────────
var uploadedImage = null;
var history = {
    math:[], projects:[], mathematician:[], legends:[], applications:[], graph_analysis:[],
    intuition:[], storytelling:[], socratic:[], concept_map:[],
    daily_puzzle:[], visual_proof:[], career:[], pyq:[],
    wrong:[], checker:[], formula_sheet:[], mock_test:[], eli10:[], three_depths:[]
};
var MAX_HISTORY        = 15;

// ── KEEP ALIVE — ping server every 10 min to prevent Render spin-down ──
function keepAlive() {
    fetch('/ping').catch(() => {});
}
setInterval(keepAlive, 10 * 60 * 1000);
keepAlive();

var MAX_MESSAGE_LENGTH = 5000;

function pushHistory(mode, role, content) {
    if (!history[mode]) history[mode] = [];
    history[mode].push({ role: role, content: content });
    if (history[mode].length > MAX_HISTORY * 2) history[mode].splice(0, 2);
}
function getHistory(mode) { return history[mode] || []; }

// ── TAB ────────────────────────────────────────────────────────
function switchTab(mode, btn) {
    document.querySelectorAll('.nav-btn').forEach(function(b) { b.classList.remove('active'); });
    document.querySelectorAll('.tab-content').forEach(function(t) { t.classList.remove('active'); });
    if (btn) btn.classList.add('active');
    var el = document.getElementById('tab-' + mode);
    if (el) el.classList.add('active');
}

// ── FILL HELPERS ───────────────────────────────────────────────
function fillQuestion(text) {
    var inp = document.getElementById('userInput');
    if (!inp) return;
    inp.value = text;
    autoResize(inp);
    inp.focus();
}

function fillPanel(mode, text) {
    var inp = document.getElementById(mode + 'Input') ||
              document.getElementById(mode + 'sInput');
    if (!inp) { console.error('fillPanel: input not found for mode:', mode); return; }
    inp.value = text;
    autoResize(inp);
    sendPanel(mode);
}

// ── INPUT HELPERS ──────────────────────────────────────────────
function handleKey(event, mode) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        if (mode === 'math') sendMessage(); else sendPanel(mode);
    }
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 100) + 'px';
}

// ── IMAGE UPLOAD ───────────────────────────────────────────────
function handleImageUpload(event) {
    var file = event.target.files[0];
    if (!file) return;

    var allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (allowed.indexOf(file.type) === -1) {
        alert('Please upload a valid image file (JPG, PNG, GIF, WEBP)');
        event.target.value = '';
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        alert('Image too large. Please upload an image smaller than 10MB.');
        event.target.value = '';
        return;
    }

    var reader = new FileReader();
    reader.onload = function(e) {
        var dataUrl = e.target.result;
        uploadedImage = {
            data:      dataUrl.split(',')[1],
            mime_type: file.type,   // FIX: mime_type matches app.py process_image()
            preview:   dataUrl
        };
        var preview    = document.getElementById('previewImg');
        var previewBox = document.getElementById('imagePreview');
        if (preview)    preview.src = dataUrl;
        if (previewBox) previewBox.classList.remove('hidden');
    };
    reader.onerror = function() {
        alert('Failed to read image file. Please try again.');
        event.target.value = '';
    };
    reader.readAsDataURL(file);
}

function removeImage() {
    uploadedImage = null;
    var previewBox  = document.getElementById('imagePreview');
    var imageUpload = document.getElementById('imageUpload');
    if (previewBox)  previewBox.classList.add('hidden');
    if (imageUpload) imageUpload.value = '';
}

// ── HANDWRITTEN MATH UPLOAD ────────────────────────────────────
function handleHandwrittenUpload(event) {
    var file = event.target.files[0];
    if (!file) return;
    var allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (allowed.indexOf(file.type) === -1) {
        alert('Please upload a valid image file (JPG, PNG, GIF, WEBP)');
        event.target.value = '';
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        alert('Image too large. Please upload an image smaller than 10MB.');
        event.target.value = '';
        return;
    }
    var reader = new FileReader();
    reader.onload = function(e) {
        var dataUrl = e.target.result;
        uploadedImage = {
            data:      dataUrl.split(',')[1],
            mime_type: file.type,
            preview:   dataUrl,
            isHandwritten: true
        };
        var preview    = document.getElementById('previewImg');
        var previewBox = document.getElementById('imagePreview');
        if (preview)    preview.src = dataUrl;
        if (previewBox) {
            previewBox.classList.remove('hidden');
            previewBox.querySelector('.preview-label').textContent = '✎ Handwritten math attached';
        }
        // Pre-fill the input with a helpful prompt
        var inp = document.getElementById('userInput');
        if (inp && !inp.value.trim()) {
            inp.value = 'Solve this handwritten problem step by step';
            autoResize(inp);
        }
    };
    reader.onerror = function() {
        alert('Failed to read image. Please try again.');
        event.target.value = '';
    };
    reader.readAsDataURL(file);
}

// ── BADGE ──────────────────────────────────────────────────────
function setBadge(text, color) {
    var b = document.getElementById('apiBadge');
    if (!b) return;
    b.textContent       = text;
    b.style.color       = color;
    b.style.borderColor = color + '40';
    b.style.background  = color + '12';
}

// ── TYPING INDICATORS ──────────────────────────────────────────
function addTyping(winId) {
    var win = document.getElementById(winId);
    if (!win) return;
    var el = document.createElement('div');
    el.id        = 'typing_' + winId;
    el.className = 'message bot';
    el.innerHTML = '<div class="msg-avatar">⚡</div>' +
                   '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    win.appendChild(el);
    win.scrollTop = win.scrollHeight;
}
function removeTyping(winId) {
    var el = document.getElementById('typing_' + winId);
    if (el) el.remove();
}
function addTypingPanel(winId) {
    var win = document.getElementById(winId);
    if (!win) return;
    var el = document.createElement('div');
    el.id        = 'typing_panel_' + winId;
    el.className = 'message bot';
    el.innerHTML = '<div class="msg-avatar">⚡</div>' +
                   '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    win.appendChild(el);
    win.scrollTop = win.scrollHeight;
}
function removeTypingPanel(winId) {
    var el = document.getElementById('typing_panel_' + winId);
    if (el) el.remove();
}

// ── ERROR HELPERS ──────────────────────────────────────────────
function isQuotaError(text) {
    if (!text) return false;
    var t = text.toLowerCase();
    return t.includes('quota') || t.includes('rate limit') ||
           t.includes('429')   || t.includes('resource exhausted') ||
           t.includes('unavailable');
}
function renderErrorMessage(content) {
    if (content && (content.includes('429') || content.toLowerCase().includes('rate limit'))) {
        return '<div class="error-bubble rate-limit-error">' +
               '<span>⏳</span> Rate limit reached. Please wait a moment and try again.</div>';
    }
    if (content && content.toLowerCase().includes('quota')) {
        return '<div class="error-bubble quota-error">' +
               '<span>⚠️</span> API quota exceeded. Please try again later.</div>';
    }
    return '<div class="error-bubble"><span>⚠️</span> ' + (content || 'An error occurred.') + '</div>';
}

// ── ADD MESSAGE (main chat window) ─────────────────────────────
function addMessage(role, content, imgPreview, source) {
    var win = document.getElementById('chatWindow');
    if (!win) return;

    var welcome = win.querySelector('.welcome');
    if (welcome) welcome.style.display = 'none';

    var isError    = (role === 'bot') && isQuotaError(content);
    var isOlympiad = (role === 'bot') && source && source.includes('✦');

    var msg       = document.createElement('div');
    msg.className = 'message ' + role + (isOlympiad ? ' olympiad-mode' : '');

    var avatar         = document.createElement('div');
    avatar.className   = 'msg-avatar';
    avatar.textContent = (role === 'user') ? 'U' : '⚡';

    var contentDiv       = document.createElement('div');
    contentDiv.className = 'msg-content' + (isError ? ' error-bubble' : '');

    if (imgPreview) {
        var img           = document.createElement('img');
        img.src           = imgPreview;
        img.alt           = 'Uploaded problem';
        img.style.cssText = 'max-width:260px;border-radius:8px;margin-bottom:8px;display:block;';
        contentDiv.appendChild(img);
    }

    var textDiv       = document.createElement('div');
    textDiv.innerHTML = isError
        ? renderErrorMessage(content)
        : renderMathContent(content);
    contentDiv.appendChild(textDiv);

    if (role === 'bot' && !isError) {
        var footer       = document.createElement('div');
        footer.className = 'msg-footer';

        if (source) {
            var s           = document.createElement('span');
            s.className     = isOlympiad ? 'source-tag source-tag--pro' : 'source-tag';
            s.textContent   = isOlympiad ? '✦ Olympiad · ' + source : 'via ' + source;
            footer.appendChild(s);
        }

        var whyBtn             = document.createElement('button');
        whyBtn.className       = 'why-btn';
        whyBtn.textContent     = '💡 Why does this work?';
        whyBtn.dataset.context = content.substring(0, 600);
        whyBtn.onclick         = function() { askWhy(whyBtn.dataset.context); };
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
    var input      = document.getElementById('userInput');
    var message    = input.value.trim();
    var diffEl     = document.getElementById('difficulty');
    var difficulty = diffEl ? diffEl.value : 'Undergraduate';

    if (!message && !uploadedImage) return;

    if (message.length > MAX_MESSAGE_LENGTH) {
        addMessage('bot', 'Message too long. Please keep it under ' + MAX_MESSAGE_LENGTH + ' characters.');
        return;
    }

    addMessage('user', message || (uploadedImage && uploadedImage.isHandwritten ? '✎ Solving handwritten problem…' : '📷 Analyzing image…'), uploadedImage && uploadedImage.preview);
    input.value        = '';
    input.style.height = 'auto';

    var imageData = uploadedImage ? {
        data:      uploadedImage.data,
        mime_type: uploadedImage.mime_type
    } : null;

    removeImage();
    addTyping('chatWindow');
    setBadge('Thinking…', '#f5a623');

    // If no text message but image uploaded, use a strong extraction prompt
    var baseMessage = message;
    if (!message && imageData) {
        baseMessage = 'Read this image carefully. Transcribe all mathematics you see, then solve every question completely step by step.';
    } else if (message && imageData && message.length < 20) {
        // Short message + image — prepend extraction instruction
        baseMessage = 'Image contains mathematics. ' + message;
    }
    var fullMessage = baseMessage + (difficulty ? '\n[Difficulty: ' + difficulty + ']' : '');
    pushHistory('math', 'user', fullMessage);

    try {
        var ctrl2 = new AbortController();
        var timer2 = setTimeout(() => ctrl2.abort(), 90000);
        var res = await fetch('/ask', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            signal:  ctrl2.signal,
            body:    JSON.stringify({
                message: fullMessage,
                mode:    'math',
                image:   imageData,
                history: getHistory('math').slice(0, -1)
            })
        });
        clearTimeout(timer2);

        if (res.status === 429) {
            removeTyping('chatWindow');
            addMessage('bot', '⏳ You are sending messages too fast. Please wait a moment and try again.');
            setBadge('Rate limited', '#f5a623');
            return;
        }
        if (!res.ok) {
            removeTyping('chatWindow');
            addMessage('bot', '⚠️ Server error (' + res.status + '). Please try again.');
            setBadge('Error', '#ef4444');
            return;
        }

        var data  = await res.json();
        removeTyping('chatWindow');
        var reply = data.response || data.error || 'No response received.';
        pushHistory('math', 'assistant', reply);
        addMessage('bot', reply, null, data.source);

        var isErr = isQuotaError(reply);
        setBadge(
            isErr ? 'Quota limit' : (data.source + ' ✓'),
            isErr ? '#ef4444'     : '#22c55e'
        );

    } catch(e) {
        removeTyping('chatWindow');
        console.error('sendMessage error:', e);
        addMessage('bot', 'Connection error. Please check your internet and try again.');
        setBadge('Error', '#ef4444');
    }
}

// ── SEND PANEL ─────────────────────────────────────────────────
async async function sendPanel(mode) {
    var inputEl = document.getElementById(mode + 'Input') ||
                  document.getElementById(mode + 'sInput');
    if (!inputEl) { console.error('Input not found for mode:', mode); return; }

    var message = inputEl.value.trim();
    if (!message) return;

    if (message.length > MAX_MESSAGE_LENGTH) {
        alert('Message too long. Please keep it under ' + MAX_MESSAGE_LENGTH + ' characters.');
        return;
    }

    // FIX: pyqWindow is inside .pyq-body — try multiple id patterns
    var winIds = [
        mode + 'Window',
        mode + 'sWindow',
        mode.replace(/_/g, '') + 'Window'
    ];
    var win = null;
    for (var wi = 0; wi < winIds.length; wi++) {
        win = document.getElementById(winIds[wi]);
        if (win) break;
    }
    if (!win) { console.error('Window not found for mode:', mode); return; }

    var welcome = win.querySelector('.panel-welcome, .pyq-welcome');
    if (welcome) welcome.style.display = 'none';

    var userDiv       = document.createElement('div');
    userDiv.className = 'user-query';
    userDiv.textContent = message;
    win.appendChild(userDiv);

    inputEl.value        = '';
    inputEl.style.height = 'auto';

    addTypingPanel(win.id);
    setBadge('Thinking…', '#f5a623');

    var prompts = {
        projects:     'Give me 5 detailed mathematics project ideas related to: ' + message,
        mathematician:'Tell me everything about the mathematician: ' + message,
        legends:      'Tell me the full story of the mathematical legend: ' + message,
        applications: 'Give me the 5 most important real-world applications of: ' + message,
        intuition:    'Build my mathematical intuition for this concept using story, analogy, visual thinking and flowchart: ' + message,
        storytelling: 'Tell me the complete mathematical story of this topic with visual flowchart and structure: ' + message,
        socratic:     'Help me think through this using the Socratic method with visual hints: ' + message,
        concept_map:  'Generate a complete concept map with visual learning flowchart for: ' + message,
        daily_puzzle: message,
        visual_proof: 'Explain the visual proof step by step of: ' + message,
        career:       'Give me a complete career pathway guide with roadmap and resources for someone interested in: ' + message,
        pyq:          message,
        wrong:        'A student attempted this problem and made a mistake. Diagnose exactly where they went wrong and how to fix it: ' + message,
        checker:      'Check if this answer is correct and explain why: ' + message,
        formula_sheet:'Generate a complete exam-ready formula sheet for this topic: ' + message,
        mock_test:    'Generate a 5-question mock test with complete solutions for this topic: ' + message,
        eli10:        'Explain this mathematics concept as if I am 10 years old: ' + message,
        three_depths: 'Explain this concept at three depths — one line, full explanation, and deep theory: ' + message
    };

    var fullMessage = prompts[mode] || message;
    pushHistory(mode, 'user', fullMessage);

    var controller = new AbortController();
    var timer = setTimeout(() => controller.abort(), 90000);
    try {
        var res = await fetch('/ask', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            signal:  controller.signal,
            body:    JSON.stringify({
                message: fullMessage,
                mode:    mode,
                history: getHistory(mode).slice(0, -1)
            })
        });
        clearTimeout(timer);

        if (res.status === 429) {
            removeTypingPanel(win.id);
            var e1       = document.createElement('div');
            e1.className = 'panel-response';
            e1.innerHTML = renderErrorMessage('rate limit');
            win.appendChild(e1);
            win.scrollTop = win.scrollHeight;
            setBadge('Rate limited', '#f5a623');
            return;
        }
        if (!res.ok) {
            removeTypingPanel(win.id);
            var e2       = document.createElement('div');
            e2.className = 'panel-response';
            e2.innerHTML = renderErrorMessage('Server error ' + res.status);
            win.appendChild(e2);
            win.scrollTop = win.scrollHeight;
            setBadge('Error', '#ef4444');
            return;
        }

        var data  = await res.json();
        removeTypingPanel(win.id);
        var reply = data.response || data.error || 'No response received.';
        pushHistory(mode, 'assistant', reply);

        var respDiv       = document.createElement('div');
        respDiv.className = 'panel-response';
        respDiv.innerHTML = isQuotaError(reply)
            ? renderErrorMessage(reply)
            : renderMathContent(reply);
        win.appendChild(respDiv);
        win.scrollTop = win.scrollHeight;
        if (!isQuotaError(reply)) typesetEl(respDiv);

        setBadge((data.source || 'AI') + ' ✓', '#22c55e');

    } catch(e) {
        clearTimeout(timer);
        removeTypingPanel(win.id);
        console.error('Panel send error:', e);
        var msg = e.name === 'AbortError' ? 'Request timed out. Server may be waking up — please try again in 10 seconds.' : 'Connection error: ' + e.message;
        var e3       = document.createElement('div');
        e3.className = 'panel-response';
        e3.innerHTML = renderErrorMessage(msg);
        win.appendChild(e3);
        win.scrollTop = win.scrollHeight;
        setBadge('Error', '#ef4444');
    }
}

// ── WHY BUTTON ─────────────────────────────────────────────────
async function askWhy(context) {
    var msg = 'Give a deeper conceptual explanation of WHY this mathematical method works. ' +
              'Focus on intuition and underlying theory. Based on: "' + context + '"';
    addMessage('user', '💡 Why does this work?');
    pushHistory('math', 'user', msg);
    addTyping('chatWindow');

    try {
        var res = await fetch('/ask', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ message: msg, mode: 'math', history: getHistory('math').slice(0, -1) })
        });
        if (res.status === 429) {
            removeTyping('chatWindow');
            addMessage('bot', '⏳ Rate limit reached. Please wait a moment and try again.');
            return;
        }
        var data  = await res.json();
        removeTyping('chatWindow');
        var reply = data.response || 'Could not fetch explanation.';
        pushHistory('math', 'assistant', reply);
        addMessage('bot', reply, null, data.source);
    } catch(e) {
        removeTyping('chatWindow');
        console.error('askWhy error:', e);
        addMessage('bot', 'Could not fetch explanation. Please try again.');
    }
}

// ── CLEAR CHAT ─────────────────────────────────────────────────
function clearChat() {
    history.math = [];
    var win = document.getElementById('chatWindow');
    if (!win) return;
    win.innerHTML =
        '<div class="welcome"><div class="welcome-bg"></div><div class="welcome-inner">' +
        '<div class="welcome-symbol">∑</div>' +
        '<h1 class="welcome-title">Ask Anupam</h1>' +
        '<p class="welcome-sub">Your personal mathematics guide — Class 11 to IMO level.<br>' +
        'Ask anything. Upload any problem. Every answer is step by step.</p>' +
        '<div class="welcome-chips">' +
        '<button class="chip" onclick="fillQuestion(\'Explain eigenvalues with examples\')">Eigenvalues</button>' +
        '<button class="chip" onclick="fillQuestion(\'What is Bayes theorem and how to apply it?\')">Bayes Theorem</button>' +
        '<button class="chip" onclick="fillQuestion(\'Prove that √2 is irrational\')">Prove √2 irrational</button>' +
        '<button class="chip" onclick="fillQuestion(\'Explain Fourier Transform intuitively\')">Fourier Transform</button>' +
        '</div>' +
        '<div class="difficulty-row"><span class="diff-label">Level</span>' +
        '<select id="difficulty" class="diff-select">' +
        '<option value="Class 11/12">Class 11 / 12</option>' +
        '<option value="Undergraduate" selected>Undergraduate</option>' +
        '<option value="JEE Advanced / IMO">JEE Advanced / IMO</option>' +
        '<option value="Research Level">Research Level</option>' +
        '</select>' +
        '<button class="clear-btn" onclick="clearChat()">Clear Chat</button>' +
        '</div></div></div>';
    setBadge('● Ready', '#22c55e');
}

// ══════════════════════════════════════════════════════════════
//  GRAPH PLOTTER
// ══════════════════════════════════════════════════════════════
function buildEvaluator(raw) {
    var expr = raw.trim()
        .replace(/\^/g,       '**')
        .replace(/(\d)(x)/gi, '$1*$2')
        .replace(/(\d)\(/g,   '$1*(')
        .replace(/\)(x)/gi,   ')*$1')
        .replace(/\)(\d)/g,   ')*$1');

    var fns = [
        ['log10','Math.log10'],['log2','Math.log2'],
        ['asin','Math.asin'],['acos','Math.acos'],['atan','Math.atan'],
        ['sinh','Math.sinh'],['cosh','Math.cosh'],['tanh','Math.tanh'],
        ['sqrt','Math.sqrt'],['cbrt','Math.cbrt'],
        ['ceil','Math.ceil'],['floor','Math.floor'],['round','Math.round'],
        ['sign','Math.sign'],['exp','Math.exp'],['abs','Math.abs'],
        ['sin','Math.sin'],['cos','Math.cos'],['tan','Math.tan'],
        ['log','Math.log'],['ln','Math.log']
    ];
    fns.forEach(function(p) {
        expr = expr.replace(new RegExp('\\b' + p[0] + '\\b', 'g'), p[1]);
    });
    expr = expr.replace(/\bpi\b/gi, 'Math.PI');
    expr = expr.replace(/(?<![A-Za-z.])e(?![A-Za-z.(])/g, 'Math.E');

    try { new Function('x', '"use strict"; return ' + expr + ';'); }
    catch(e) { throw new Error('Cannot parse: ' + raw); }

    return new Function('x', '"use strict"; return ' + expr + ';');
}

function generatePoints(evalFn, xMin, xMax, steps) {
    var xs = [], ys = [], step = (xMax - xMin) / steps;
    for (var i = 0; i <= steps; i++) {
        var x = xMin + i * step;
        xs.push(parseFloat(x.toFixed(6)));
        try {
            var y = evalFn(x);
            ys.push((isFinite(y) && Math.abs(y) < 1e8) ? parseFloat(y.toFixed(8)) : null);
        } catch(e) { ys.push(null); }
    }
    return { xs: xs, ys: ys };
}

function quickPlot(fn) {
    var inp = document.getElementById('functionInput');
    if (inp) inp.value = fn;
    plotFunction();
}

async function plotFunction() {
    var inputEl = document.getElementById('functionInput');
    if (!inputEl) return;
    var raw = inputEl.value.trim();
    if (!raw) return;

    var plotArea    = document.getElementById('plotArea');
    var analysisDiv = document.getElementById('graphAnalysis');
    if (!plotArea) return;

    plotArea.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;' +
        'height:300px;color:var(--text3);font-size:13px;">Plotting f(x) = ' + esc(raw) + '…</div>';
    if (analysisDiv) analysisDiv.style.display = 'none';
    await new Promise(function(r) { setTimeout(r, 30); });

    var evalFn;
    try { evalFn = buildEvaluator(raw); }
    catch(e) {
        plotArea.innerHTML = '<div style="display:flex;flex-direction:column;align-items:center;' +
            'justify-content:center;height:300px;color:#ef4444;font-size:13px;padding:20px;text-align:center;">' +
            '<div style="margin-bottom:8px;">Cannot parse: <code style="color:var(--amber)">' +
            esc(raw) + '</code></div><div style="color:var(--text3);font-size:11px;">' +
            'Try: x^2 · sin(x) · cos(x) · x^3-3*x · 1/x · sqrt(x) · e^x · ln(x) · abs(x)</div></div>';
        return;
    }

    try {
        var pts    = generatePoints(evalFn, -10, 10, 800);
        var validY = pts.ys.filter(function(y) { return y !== null; });

        if (!validY.length) {
            plotArea.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;' +
                'height:300px;color:#ef4444;font-size:13px;">No real values in x ∈ [−10, 10].</div>';
            return;
        }

        var yMin = Math.max(Math.min.apply(null, validY), -100);
        var yMax = Math.min(Math.max.apply(null, validY),  100);
        var yPad = Math.max((yMax - yMin) * 0.1, 0.5);

        Plotly.newPlot('plotArea', [{
            x: pts.xs, y: pts.ys,
            type: 'scatter', mode: 'lines',
            line: { color: '#00d4aa', width: 2.5, shape: 'linear' },
            name: 'f(x) = ' + raw, connectgaps: false,
            hovertemplate: 'x = %{x:.3f}<br>f(x) = %{y:.4f}<extra></extra>'
        }], {
            paper_bgcolor: '#06060f', plot_bgcolor: '#0a0a18',
            font: { color: '#8888b0', size: 11, family: 'DM Sans' },
            margin: { t: 44, r: 24, b: 52, l: 58 },
            title: { text: 'f(x) = ' + raw, font: { color: '#00d4aa', size: 14, family: 'Syne' }, x: 0.5, xanchor: 'center' },
            xaxis: { gridcolor: '#161628', zerolinecolor: '#f5a623', zerolinewidth: 1.5, linecolor: '#1e1e3a', tickfont: { color: '#44446a', size: 10 }, title: { text: 'x', font: { color: '#44446a' } } },
            yaxis: { gridcolor: '#161628', zerolinecolor: '#f5a623', zerolinewidth: 1.5, linecolor: '#1e1e3a', tickfont: { color: '#44446a', size: 10 }, title: { text: 'f(x)', font: { color: '#44446a' } }, range: [yMin - yPad, yMax + yPad] },
            hovermode: 'x unified',
            hoverlabel: { bgcolor: '#0a0a18', bordercolor: '#00d4aa', font: { color: '#eeeef8', size: 12, family: 'JetBrains Mono' } }
        }, {
            responsive: true, displayModeBar: true, displaylogo: false,
            modeBarButtonsToRemove: ['toImage','sendDataToCloud','lasso2d','select2d']
        });

        await fetchGraphAnalysis(raw);

    } catch(e) {
        console.error('Plot error:', e);
        plotArea.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;' +
            'height:300px;color:#ef4444;font-size:13px;">Plotting failed. Try a simpler expression.</div>';
    }
}

async function fetchGraphAnalysis(fn) {
    var div = document.getElementById('graphAnalysis');
    if (!div) return;
    div.style.display = 'block';
    div.innerHTML = '<div style="display:flex;gap:8px;align-items:center;color:var(--text3);font-size:13px;">' +
        '<div class="typing-indicator" style="padding:0;background:transparent;border:none;">' +
        '<span></span><span></span><span></span></div>&nbsp;Analyzing f(x) = ' + esc(fn) + '…</div>';

    try {
        var res = await fetch('/ask', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: 'Analyze the function f(x) = ' + fn, mode: 'graph_analysis', history: [] })
        });
        if (res.status === 429) {
            div.innerHTML = '<p style="color:var(--text3)">Rate limit reached. Analysis unavailable.</p>';
            return;
        }
        var data = await res.json();
        div.innerHTML = renderMathContent(data.response || data.error);
        typesetEl(div);
    } catch(e) {
        console.error('Graph analysis error:', e);
        div.innerHTML = '<p style="color:var(--text3)">Analysis unavailable.</p>';
    }
}

// ══════════════════════════════════════════════════════════════
//  EXAMINATION HUB DATA
// ══════════════════════════════════════════════════════════════
var EXAM_DATA = {
    gate: {
        name: 'GATE Mathematics (MA)', color: 'teal', icon: '🏛️',
        syllabus: {
            'Calculus': [
                'Functions of two or more variables, continuity, directional derivatives',
                'Partial derivatives, total derivative, maxima and minima, saddle point',
                'Method of Lagrange multipliers',
                'Double and triple integrals and their applications',
                'Line integrals and surface integrals',
                "Green's theorem, Stokes' theorem, Gauss divergence theorem"
            ],
            'Linear Algebra': [
                'Finite-dimensional vector spaces over real and complex number fields',
                'Linear transformations and their matrix representations, rank',
                'Systems of linear equations, eigenvalues and eigenvectors',
                'Minimal polynomial, Cayley-Hamilton theorem',
                'Diagonalisation, Jordan canonical form',
                'Symmetric, skew-symmetric, Hermitian, skew-Hermitian matrices'
            ],
            'Real Analysis': [
                'Sequences and series of real numbers, convergence criteria',
                "Limits, continuity, uniform continuity, differentiability",
                "Mean value theorems, indeterminate forms, L'Hopital's rule",
                'Maxima and minima of functions of single and two variables',
                'Riemann integration, improper integrals',
                'Sequences and series of functions, uniform convergence'
            ],
            'Complex Analysis': [
                'Algebra of complex numbers, the complex plane',
                'Polynomials, power series, transcendental functions',
                'Analytic functions, Cauchy-Riemann equations',
                "Contour integral, Cauchy's theorem, Cauchy's integral formula",
                "Liouville's theorem, maximum modulus principle",
                'Taylor series, Laurent series, calculus of residues'
            ],
            'Ordinary Differential Equations': [
                'First order ODE, exactness, integrating factor',
                'Second order linear ODE with constant coefficients',
                'Variation of parameters, Cauchy-Euler equation',
                'Power series solutions, Legendre and Bessel equations',
                'Systems of linear first order ODE',
                'Sturm-Liouville boundary value problems'
            ],
            'Algebra': [
                'Groups, subgroups, normal subgroups, quotient groups',
                'Homomorphisms, isomorphisms, permutation groups',
                'Rings, ideals, prime and maximal ideals, quotient rings',
                'Fields, finite fields, field extensions'
            ],
            'Functional Analysis': [
                'Normed linear spaces, Banach spaces, Hilbert spaces',
                'Bounded linear operators and functionals',
                'Hahn-Banach theorem, open mapping theorem, closed graph theorem',
                'Riesz representation theorem'
            ],
            'Numerical Analysis': [
                'Systems of linear equations: Gaussian elimination, LU decomposition',
                'Iterative methods: Gauss-Seidel, Jacobi',
                'Nonlinear equations: Newton-Raphson, bisection, secant method',
                'Interpolation: Lagrange and Newton, finite differences',
                "Numerical integration: Trapezoidal rule, Simpson's rule",
                "Numerical solution of ODEs: Euler's method, Runge-Kutta"
            ],
            'Partial Differential Equations': [
                'First order linear and quasilinear PDE',
                'Second order PDE: classification, canonical forms',
                'Method of separation of variables for Laplace, heat and wave equations',
                "D'Alembert's solution of wave equation"
            ],
            'Topology': [
                'Basis, subspace topology, order topology, product topology',
                'Metric topology, quotient topology',
                'Connectedness, compactness, Heine-Borel theorem',
                "Urysohn's lemma, Tietze extension theorem"
            ],
            'Linear Programming': [
                'Linear programming problem, feasible and optimal solutions',
                'Graphical method, simplex method',
                'Duality in linear programming, transportation problem'
            ]
        },
        pattern: {
            duration: '3 Hours', total_marks: 100,
            sections: [
                { name: 'General Aptitude (GA)', questions: 10, marks: 15,   type: 'MCQ',             negative: '1/3 for 1-mark, 2/3 for 2-mark MCQs' },
                { name: 'Mathematics Core',      questions: 55, marks: 85,   type: 'MCQ + MSQ + NAT', negative: 'Only MCQs have negative marking'       }
            ],
            question_types: [
                { type: 'MCQ', desc: 'Multiple Choice — one correct answer',          negative: 'Yes (−1/3 or −2/3)' },
                { type: 'MSQ', desc: 'Multiple Select — one or more correct answers', negative: 'No' },
                { type: 'NAT', desc: 'Numerical Answer Type — type the number',       negative: 'No' }
            ],
            notes: ['Exam conducted by IITs on rotation', 'Score valid for 3 years', 'CBT (Computer Based Test) mode']
        },
        weightage: [
            { topic: 'Linear Algebra',                  marks: '10–12', priority: 'high'   },
            { topic: 'Real Analysis',                   marks: '10–12', priority: 'high'   },
            { topic: 'Calculus',                        marks: '8–10',  priority: 'high'   },
            { topic: 'Complex Analysis',                marks: '7–9',   priority: 'high'   },
            { topic: 'Ordinary Differential Equations', marks: '7–9',   priority: 'high'   },
            { topic: 'Algebra (Groups & Rings)',         marks: '6–8',   priority: 'medium' },
            { topic: 'Functional Analysis',             marks: '5–7',   priority: 'medium' },
            { topic: 'Numerical Analysis',              marks: '5–7',   priority: 'medium' },
            { topic: 'Partial Differential Equations',  marks: '5–7',   priority: 'medium' },
            { topic: 'Topology',                        marks: '4–6',   priority: 'medium' },
            { topic: 'Linear Programming',              marks: '3–5',   priority: 'low'    },
            { topic: 'General Aptitude',                marks: '15',    priority: 'high'   }
        ]
    },

    csirnet: {
        name: 'CSIR NET Mathematical Sciences', color: 'rose', icon: '🔬',
        syllabus: {
            'Unit 1 — Analysis & Linear Algebra': [
                'Elementary set theory, finite, countable and uncountable sets',
                'Real number system as a complete ordered field, Archimedean property',
                'Sequences and series, convergence, limsup, liminf',
                'Bolzano-Weierstrass theorem, Heine-Borel theorem',
                'Continuity, uniform continuity, differentiability, mean value theorem',
                'Functions of several variables, maxima, minima',
                'Riemann integration, improper integrals',
                'Vector spaces, subspaces, linear dependence, basis, dimension',
                'Linear transformations, rank-nullity, matrix representation',
                'Systems of linear equations, eigenvalues, eigenvectors',
                'Cayley-Hamilton theorem, symmetric matrices, positive definite matrices',
                'LU decomposition, QR factorization'
            ],
            'Unit 2 — Complex Analysis, Topology & Algebra': [
                'Algebra of complex numbers, analytic functions, Cauchy-Riemann equations',
                "Contour integrals, Cauchy's theorem, Cauchy integral formula",
                "Liouville's theorem, Taylor and Laurent series",
                'Calculus of residues, conformal mappings, Mobius transformations',
                'Metric spaces: sequences, completeness, compactness, connectedness',
                'Normed linear spaces, Banach spaces',
                'Permutations, combinations, pigeonhole principle',
                'Fundamental theorem of arithmetic, divisibility, congruences',
                "Chinese Remainder Theorem, Euler's phi-function",
                "Groups, subgroups, normal subgroups, Lagrange's theorem",
                'Homomorphisms, quotient groups, Sylow theorems',
                'Rings, ideals, integral domains, fields'
            ],
            'Unit 3 — ODEs, PDEs, Numerical Analysis, Classical Mechanics': [
                "First order ODEs: existence, uniqueness, Picard's theorem",
                'General theory of nth order linear ODEs, Wronskian',
                'Power series solutions, Legendre equation, Bessel equation',
                'Partial differential equations: classification, characteristics',
                'Wave equation, heat equation, Laplace equation',
                'Boundary value problems, separation of variables',
                'Numerical solution of algebraic equations: bisection, Newton-Raphson',
                "Numerical integration: Trapezoidal, Simpson rules",
                'Numerical solution of ODEs: Euler, predictor-corrector methods',
                'Calculus of variations: Euler-Lagrange equation',
                'Classical mechanics: Lagrangian and Hamiltonian formulations',
                'Conservation laws, central force problem'
            ],
            'Unit 4 — Statistics & Probability': [
                'Probability theory, random variables, probability distributions',
                'Standard distributions: Binomial, Poisson, Normal, Exponential, Gamma',
                'Sampling distributions, Central Limit Theorem',
                'Methods of estimation: MLE, method of moments',
                'Confidence intervals, hypothesis testing',
                'Chi-square test, t-test, F-test',
                'Regression and correlation analysis',
                'Markov chains, stationary distributions',
                'Bayesian inference basics',
                'Simple random sampling, stratified sampling'
            ]
        },
        pattern: {
            duration: '3 Hours', total_marks: 200,
            sections: [
                { name: 'Part A — General Aptitude',   questions: '20 (attempt 15)', marks: 30, type: 'MCQ', negative: '25% for wrong answer' },
                { name: 'Part B — Subject (Moderate)', questions: '40 (attempt 25)', marks: 75, type: 'MCQ', negative: '25% for wrong answer' },
                { name: 'Part C — Subject (Advanced)', questions: '60 (attempt 20)', marks: 95, type: 'MCQ', negative: 'No negative marking'  }
            ],
            question_types: [
                { type: 'Part A', desc: 'General Science, Quantitative Reasoning, Research Aptitude', negative: 'Yes (25%)' },
                { type: 'Part B', desc: 'Standard level subject questions from syllabus',             negative: 'Yes (25%)' },
                { type: 'Part C', desc: 'Higher-order, application-based subject questions',          negative: 'No'        }
            ],
            notes: ['Conducted by NTA twice a year (June and December)', 'Qualifies for JRF and Lectureship', 'All MCQ based exam']
        },
        weightage: [
            { topic: 'Linear Algebra',           marks: '20–25', priority: 'high'   },
            { topic: 'Real Analysis',            marks: '20–25', priority: 'high'   },
            { topic: 'Complex Analysis',         marks: '15–20', priority: 'high'   },
            { topic: 'Abstract Algebra',         marks: '15–18', priority: 'high'   },
            { topic: 'ODEs & PDEs',              marks: '12–15', priority: 'high'   },
            { topic: 'Topology',                 marks: '10–12', priority: 'medium' },
            { topic: 'Numerical Analysis',       marks: '8–10',  priority: 'medium' },
            { topic: 'Statistics & Probability', marks: '10–15', priority: 'medium' },
            { topic: 'Calculus of Variations',   marks: '5–8',   priority: 'low'    },
            { topic: 'Classical Mechanics',      marks: '5–8',   priority: 'low'    },
            { topic: 'General Aptitude (Part A)', marks: '30',   priority: 'high'   }
        ]
    },

    iitjam: {
        name: 'IIT JAM Mathematics (MA)', color: 'amber', icon: '⚙️',
        syllabus: {
            'Sequences & Series of Real Numbers': [
                'Sequences and series of real numbers, convergence criteria',
                'Absolute and conditional convergence, tests for convergence',
                'Power series, radius of convergence',
                "Cauchy's criterion, Ratio test, Root test, Leibniz test"
            ],
            'Functions of One Real Variable': [
                'Limits, continuity, intermediate value property',
                "Differentiability, Rolle's theorem, mean value theorem",
                "L'Hopital's rule, Taylor's theorem",
                'Maxima and minima, curve sketching'
            ],
            'Functions of Two or Three Real Variables': [
                'Limit, continuity, partial derivatives',
                'Differentiability, gradient, directional derivatives',
                'Maxima and minima with Lagrange multipliers',
                'Double and triple integrals'
            ],
            'Integral Calculus': [
                'Integration as the inverse of differentiation',
                'Definite integrals and their properties',
                'Fundamental theorem of calculus',
                'Double and triple integrals, change of order',
                'Calculating surface area and volume'
            ],
            'Differential Equations': [
                'Ordinary differential equations of first order (separable, homogeneous, exact)',
                "Integrating factor, Bernoulli's equation",
                'Second order linear ODE with constant and variable coefficients',
                'Variation of parameters, Cauchy-Euler equation',
                'Systems of first order ODEs'
            ],
            'Vector Calculus': [
                'Scalar and vector fields, gradient, divergence, curl',
                'Line integrals, surface integrals, volume integrals',
                "Green's theorem, Stokes' theorem, Gauss divergence theorem"
            ],
            'Group Theory': [
                'Groups, subgroups, Abelian groups, cyclic groups',
                "Normal subgroups, quotient groups, Lagrange's theorem",
                'Permutation groups, homomorphisms, isomorphism theorems'
            ],
            'Linear Algebra': [
                'Finite-dimensional vector spaces, basis, dimension',
                'Linear transformations, rank-nullity theorem',
                'Matrices, determinants, system of linear equations',
                'Eigenvalues, eigenvectors, Cayley-Hamilton theorem',
                'Symmetric matrices, positive definite matrices'
            ],
            'Real Analysis': [
                'Interior, closure, boundary of sets in R',
                'Compact sets, connected sets',
                'Limits and continuity of functions',
                'Uniform continuity, differentiability',
                'Sequences and series of functions, uniform convergence'
            ]
        },
        pattern: {
            duration: '3 Hours', total_marks: 100,
            sections: [
                { name: 'Section A — MCQ', questions: 30, marks: '30×(1 or 2) = 50', type: 'MCQ',                    negative: '1/3 for 1-mark, 2/3 for 2-mark' },
                { name: 'Section B — MSQ', questions: 10, marks: '10×2 = 20',         type: 'MSQ (1 or more correct)', negative: 'No' },
                { name: 'Section C — NAT', questions: 20, marks: '20×(1 or 2) = 30',  type: 'Numerical Answer Type',  negative: 'No' }
            ],
            question_types: [
                { type: 'MCQ (Sec A)', desc: '10 questions of 1 mark + 20 questions of 2 marks',               negative: 'Yes' },
                { type: 'MSQ (Sec B)', desc: '10 questions of 2 marks — may have multiple correct answers',    negative: 'No'  },
                { type: 'NAT (Sec C)', desc: '10 of 1 mark + 10 of 2 marks — enter number via virtual keypad', negative: 'No'  }
            ],
            notes: ['Conducted by IITs for MSc and Integrated PhD admissions', '~3000 seats at IITs, IISc, NIT, IISER', 'CBT mode, English only', 'No age restriction']
        },
        weightage: [
            { topic: 'Calculus (Single Variable)', marks: '15–20', priority: 'high'   },
            { topic: 'Linear Algebra',             marks: '12–18', priority: 'high'   },
            { topic: 'Real Analysis',              marks: '12–16', priority: 'high'   },
            { topic: 'Differential Equations',    marks: '10–14', priority: 'high'   },
            { topic: 'Multivariable Calculus',    marks: '10–14', priority: 'high'   },
            { topic: 'Vector Calculus',           marks: '8–12',  priority: 'medium' },
            { topic: 'Group Theory',              marks: '8–12',  priority: 'medium' },
            { topic: 'Sequences & Series',        marks: '8–10',  priority: 'medium' },
            { topic: 'Integral Calculus',         marks: '6–10',  priority: 'medium' }
        ]
    }
};

// ── PYQ TOPICS ─────────────────────────────────────────────────
var PYQ_TOPICS = {
    gate:    ['Real Analysis','Linear Algebra','Complex Analysis','ODEs','PDEs',
              'Algebra','Functional Analysis','Numerical Analysis','Topology','Linear Programming','Calculus'],
    csirnet: ['Real Analysis','Linear Algebra','Complex Analysis','Abstract Algebra',
              'Topology','ODEs','PDEs','Statistics','Numerical Analysis','Classical Mechanics'],
    iitjam:  ['Calculus','Real Analysis','Linear Algebra','Differential Equations',
              'Vector Calculus','Group Theory','Sequences & Series','Multivariable Calculus']
};

var currentExam    = 'gate';
var currentExamTab = 'syllabus';
var currentPYQExam = 'gate';

// ── EXAM HUB ───────────────────────────────────────────────────
function selectExam(exam) {
    currentExam = exam;
    document.querySelectorAll('.exam-sel-btn').forEach(function(b) { b.classList.remove('active'); });
    var btn = document.getElementById('esel-' + exam);
    if (btn) btn.classList.add('active');
    renderExamContent();
}

function switchExamTab(tab, btn) {
    currentExamTab = tab;
    document.querySelectorAll('.exam-tab-btn').forEach(function(b) { b.classList.remove('active'); });
    if (btn) btn.classList.add('active');
    renderExamContent();
}

function renderExamContent() {
    var data = EXAM_DATA[currentExam];
    var area = document.getElementById('examContentArea');
    if (!area || !data) return;

    if (currentExamTab === 'syllabus') {
        var html = '<div class="exam-syllabus">';
        for (var unit in data.syllabus) {
            html += '<div class="exam-unit"><div class="exam-unit-title">' + unit + '</div>' +
                    '<ul class="exam-unit-list">' +
                    data.syllabus[unit].map(function(t) { return '<li>' + t + '</li>'; }).join('') +
                    '</ul></div>';
        }
        area.innerHTML = html + '</div>';
    }
    else if (currentExamTab === 'pattern') {
        var p    = data.pattern;
        var html = '<div class="exam-pattern"><div class="exam-pattern-grid">' +
                   '<div class="ep-card ep-teal"><div class="ep-val">'   + p.duration    + '</div><div class="ep-label">Duration</div></div>' +
                   '<div class="ep-card ep-amber"><div class="ep-val">'  + p.total_marks + '</div><div class="ep-label">Total Marks</div></div>' +
                   '<div class="ep-card ep-rose"><div class="ep-val">CBT</div><div class="ep-label">Mode</div></div>' +
                   '<div class="ep-card ep-purple"><div class="ep-val">' + p.sections.length + '</div><div class="ep-label">Sections</div></div>' +
                   '</div><div class="exam-sections-title">Section-Wise Breakdown</div><div class="exam-sections">';
        p.sections.forEach(function(s) {
            var noNeg = s.negative.startsWith('No');
            html += '<div class="exam-section-row"><div class="esr-name">' + s.name + '</div>' +
                    '<div class="esr-details">' +
                    '<span class="esr-chip esr-q">📝 ' + s.questions + ' Questions</span>' +
                    '<span class="esr-chip esr-m">⚖️ ' + s.marks + ' Marks</span>' +
                    '<span class="esr-chip esr-t">📋 ' + s.type + '</span>' +
                    '<span class="esr-chip esr-n ' + (noNeg ? 'esr-no' : 'esr-yes') + '">' +
                    (noNeg ? '✅ No Negative' : '⚠️ ' + s.negative) + '</span></div></div>';
        });
        html += '</div><div class="exam-notes">' +
                p.notes.map(function(n) { return '<div class="exam-note">ℹ️ ' + n + '</div>'; }).join('') +
                '</div></div>';
        area.innerHTML = html;
    }
    else if (currentExamTab === 'weightage') {
        var html = '<div class="exam-weightage"><p class="ew-note">Based on analysis of 5+ years of previous papers. Marks are approximate ranges.</p>';
        data.weightage.forEach(function(item) {
            var pc = item.priority === 'high' ? 'ewp-high' : item.priority === 'medium' ? 'ewp-med' : 'ewp-low';
            var pl = item.priority === 'high' ? '🔴 High Priority' : item.priority === 'medium' ? '🟡 Medium' : '🟢 Lower';
            html += '<div class="ew-row">' +
                    '<div class="ew-topic">'   + item.topic + '</div>' +
                    '<div class="ew-marks">'   + item.marks + ' marks</div>' +
                    '<div class="ew-priority ' + pc + '">' + pl + '</div></div>';
        });
        area.innerHTML = html + '</div>';
    }
}

// ── PYQ ────────────────────────────────────────────────────────
function selectPYQExam(exam) {
    currentPYQExam = exam;
    document.querySelectorAll('.pyq-sel-btn').forEach(function(b) { b.classList.remove('active'); });
    var btn = document.getElementById('psel-' + exam);
    if (btn) btn.classList.add('active');
    renderPYQTopics();
}

function renderPYQTopics() {
    var bar    = document.getElementById('pyqTopicBar');
    if (!bar) return;
    var topics = PYQ_TOPICS[currentPYQExam] || [];
    bar.innerHTML = topics.map(function(t) {
        return '<button class="pyq-topic-btn" onclick="askPYQ(\'' +
               currentPYQExam + '\',\'' + t + '\',\'recent\')">' + t + '</button>';
    }).join('');
}

// FIX: setTimeout ensures inp.value is set before sendPanel reads it
function askPYQ(exam, topic, year) {
    var examNames = {
        gate:    'GATE Mathematics (MA)',
        csirnet: 'CSIR NET Mathematical Sciences',
        iitjam:  'IIT JAM Mathematics'
    };
    var yearStr = (year === 'recent') ? 'recent (last 5 years)' : year;
    var msg = 'Give me 3 ' + yearStr + ' previous year questions from ' + examNames[exam] +
              ' on the topic: ' + topic +
              '. For each question: show the approach first, then complete step-by-step solution, common mistakes, final answer, verification, key concept tested, and exam strategy.';

    var inp = document.getElementById('pyqInput');
    if (inp) { inp.value = msg; autoResize(inp); }

    var welcome = document.getElementById('pyqWelcome');
    if (welcome) welcome.style.display = 'none';

    setTimeout(function() { sendPanel('pyq'); }, 50);
}

// ── INIT ───────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', function() {
    renderExamContent();
    renderPYQTopics();
});