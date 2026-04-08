// ══════════════════════════════════════════════════════════════
//  MATHSPHERE ENGINEERING — engineering.js
//  Mode switcher + full engineering interface
//  Next-Level version with particle backgrounds,
//  aurora effects, holographic cards, mouse tracking
// ══════════════════════════════════════════════════════════════
(function() {
'use strict';

var state = {
    mode:           'general',
    activeTab:      'learn',
    activeSem:      null,
    activeTopic:    null,
    activeSubtopic: null,
    activeSection:  'definition',
    syllabus:       null,
    loading:        false
};

document.addEventListener('DOMContentLoaded', function() {
    injectLanding();
    injectEngApp();
    loadSyllabus();
    setupMouseTracking();
    var saved = localStorage.getItem('msMode');
    if (saved === 'engineering') activateEngineering();
    else if (saved === 'general') activateGeneral();
    else showLanding();
});

// ══════════════════════════════════════════════════════════════
//  MOUSE TRACKING — for holographic card effects
// ══════════════════════════════════════════════════════════════
function setupMouseTracking() {
    document.addEventListener('mousemove', function(e) {
        var cards = document.querySelectorAll('.landing-card');
        cards.forEach(function(card) {
            var rect = card.getBoundingClientRect();
            var x = ((e.clientX - rect.left) / rect.width) * 100;
            var y = ((e.clientY - rect.top) / rect.height) * 100;
            card.style.setProperty('--mouse-x', x + '%');
            card.style.setProperty('--mouse-y', y + '%');
        });
    });
}

// ══════════════════════════════════════════════════════════════
//  LANDING OVERLAY — with particles, orbs, aurora
// ══════════════════════════════════════════════════════════════
function injectLanding() {
    var el = document.createElement('div');
    el.id = 'mode-landing';
    el.className = 'hidden';

    // Build particle elements (15 particles)
    var particleHTML = '<div class="landing-particles">';
    for (var i = 1; i <= 15; i++) {
        particleHTML += '<div class="p"></div>';
    }
    particleHTML += '</div>';

    el.innerHTML = [
        // Aurora layer
        '<div class="landing-aurora"></div>',
        // Floating orbs
        '<div class="landing-orb landing-orb--1"></div>',
        '<div class="landing-orb landing-orb--2"></div>',
        '<div class="landing-orb landing-orb--3"></div>',
        // Particles
        particleHTML,
        // Content
        '<div class="landing-eyebrow">MathSphere Platform</div>',
        '<div class="landing-title-main">Mathematics for <span>Engineers</span></div>',
        '<div class="landing-sub">Choose your learning environment. Switch anytime from the header. Built for IIT/NIT students who take their exams seriously.</div>',
        '<div class="landing-cards">',
        '  <div class="landing-card landing-card--general" onclick="window.engModule.chooseMode(\'general\')">',
        '    <div class="landing-card-tag">All Levels</div>',
        '    <div class="landing-card-icon-wrap">&#x2211;</div>',
        '    <div class="landing-card-title">General Mathematics</div>',
        '    <div class="landing-card-desc">Ask Anupam, Intuition Builder, Story Mode, PYQ Practice, Graph Plotter, Mock Tests — from Class 11 to research level.</div>',
        '    <div class="landing-card-arrow">Open General Mode &rarr;</div>',
        '  </div>',
        '  <div class="landing-card landing-card--engineering" onclick="window.engModule.chooseMode(\'engineering\')">',
        '    <div class="landing-card-tag">B.Tech Sem 1&ndash;4</div>',
        '    <div class="landing-card-icon-wrap" style="font-family:var(--e-mono);font-size:18px">&#x222B;&#x2207;</div>',
        '    <div class="landing-card-title">Engineering Mathematics</div>',
        '    <div class="landing-card-desc">IIT/NIT syllabus. 200+ subtopics. Visual Intuition, PYQs from universities across India, Formula Booklet, Misconception Detector.</div>',
        '    <div class="landing-card-arrow">Open Engineering Mode &rarr;</div>',
        '  </div>',
        '</div>',
        '<div class="landing-footer">Your choice is saved automatically</div>'
    ].join('');
    document.body.appendChild(el);
}

// ══════════════════════════════════════════════════════════════
//  ENGINEERING APP — with animated background orbs
// ══════════════════════════════════════════════════════════════
function injectEngApp() {
    var el = document.createElement('div');
    el.id = 'eng-app';
    el.innerHTML = [
        // Animated background
        '<div class="eng-app-bg">',
        '  <div class="orb orb--1"></div>',
        '  <div class="orb orb--2"></div>',
        '  <div class="orb orb--3"></div>',
        '</div>',

        // Header
        '<div class="eng-header">',
        '  <button class="eng-hamburger" id="eng-hamburger" onclick="window.engModule.toggleSidebar()" aria-label="Menu">',
        '    <span></span><span></span><span></span>',
        '  </button>',
        '  <div class="eng-header-brand">',
        '    <div class="eng-logo-mark">E</div>',
        '    <div>',
        '      <div class="eng-logo-text">MathSphere</div>',
        '      <div class="eng-logo-sub">Engineering Mathematics</div>',
        '    </div>',
        '  </div>',
        '  <div class="eng-tabs">',
        '    <button class="eng-tab active" data-tab="learn"         onclick="window.engModule.switchTab(\'learn\',this)">Learn</button>',
        '    <button class="eng-tab"        data-tab="revision"      onclick="window.engModule.switchTab(\'revision\',this)">Quick Revision</button>',
        '    <button class="eng-tab"        data-tab="formulabook"   onclick="window.engModule.switchTab(\'formulabook\',this)">Formula Booklet</button>',
        '    <button class="eng-tab"        data-tab="connections"   onclick="window.engModule.switchTab(\'connections\',this)">Subject Connections</button>',
        '    <button class="eng-tab"        data-tab="pyq"           onclick="window.engModule.switchTab(\'pyq\',this)">PYQ Bank</button>',
        '    <button class="eng-tab"        data-tab="mocktest"      onclick="window.engModule.switchTab(\'mocktest\',this)">Mock Test</button>',
        '    <button class="eng-tab"        data-tab="misconception" onclick="window.engModule.switchTab(\'misconception\',this)">Misconception Detector</button>',
        '    <button class="eng-tab"        data-tab="ask"           onclick="window.engModule.switchTab(\'ask\',this)">Ask AI</button>',
        '  </div>',
        '  <div class="eng-header-right">',
        '    <div class="eng-status">ONLINE</div>',
        '    <button class="mode-switch-btn" onclick="window.engModule.showLanding()">&#x21C4; Mode</button>',
        '  </div>',
        '</div>',

        // Body
        '<div class="eng-body">',

        // Sidebar
        '  <div class="eng-sidebar">',
        '    <div class="eng-sem-pills" id="eng-sem-pills">',
        '      <button class="eng-sem-pill" data-sem="sem1" onclick="window.engModule.selectSem(\'sem1\',this)">Sem 1</button>',
        '      <button class="eng-sem-pill" data-sem="sem2" onclick="window.engModule.selectSem(\'sem2\',this)">Sem 2</button>',
        '      <button class="eng-sem-pill" data-sem="sem3" onclick="window.engModule.selectSem(\'sem3\',this)">Sem 3</button>',
        '      <button class="eng-sem-pill" data-sem="sem4" onclick="window.engModule.selectSem(\'sem4\',this)">Sem 4</button>',
        '    </div>',
        '    <div class="eng-topic-list" id="eng-topic-list"></div>',
        '  </div>',

        // Content area
        '  <div class="eng-content">',

        // Subtopic chips
        '    <div class="eng-subtopic-bar hidden" id="eng-subtopic-bar"></div>',

        // Section buttons (Learn tab)
        '    <div class="eng-section-bar hidden" id="eng-section-bar">',
        '      <button class="eng-sec-btn active" data-sec="definition" onclick="window.engModule.selectSection(\'definition\',this)">Definition</button>',
        '      <button class="eng-sec-btn"        data-sec="intuition"  onclick="window.engModule.selectSection(\'intuition\',this)">Visual Intuition</button>',
        '      <button class="eng-sec-btn"        data-sec="theorem"    onclick="window.engModule.selectSection(\'theorem\',this)">Theorems</button>',
        '      <button class="eng-sec-btn"        data-sec="examples"   onclick="window.engModule.selectSection(\'examples\',this)">Examples</button>',
        '      <button class="eng-sec-btn"        data-sec="practice"   onclick="window.engModule.selectSection(\'practice\',this)">Practice</button>',
        '    </div>',

        // PYQ filters
        '    <div class="eng-filters hidden" id="eng-pyq-filters">',
        '      <span class="eng-filter-label">University</span>',
        '      <select class="eng-select" id="eng-univ-select">',
        '        <option value="all">All India</option>',
        '        <option value="mumbai">Mumbai University</option>',
        '        <option value="vtu">VTU Bangalore</option>',
        '        <option value="anna">Anna University</option>',
        '        <option value="aktu">AKTU Lucknow</option>',
        '        <option value="abroad">International</option>',
        '      </select>',
        '      <span class="eng-filter-label">Difficulty</span>',
        '      <select class="eng-select" id="eng-diff-select">',
        '        <option value="easy">Easy (2-4 marks)</option>',
        '        <option value="medium" selected>Medium (4-6 marks)</option>',
        '        <option value="hard">Hard (6-10 marks)</option>',
        '      </select>',
        '      <button class="eng-gen-btn" onclick="window.engModule.fetchPYQ()">Generate PYQs</button>',
        '    </div>',

        // Mock test config
        '    <div class="eng-mock-config hidden" id="eng-mock-config">',
        '      <span class="eng-mock-label">Questions</span>',
        '      <select class="eng-select" id="eng-numq-select">',
        '        <option value="5">5 Questions</option>',
        '        <option value="10" selected>10 Questions</option>',
        '        <option value="20">20 Questions</option>',
        '      </select>',
        '      <span class="eng-mock-label">Marks each</span>',
        '      <select class="eng-select" id="eng-marks-select">',
        '        <option value="2">2 Marks</option>',
        '        <option value="5" selected>5 Marks</option>',
        '        <option value="10">10 Marks</option>',
        '      </select>',
        '      <button class="eng-gen-btn" onclick="window.engModule.fetchMockTest()">Generate Paper</button>',
        '    </div>',

        // Output
        '    <div class="eng-output" id="eng-output">',
        '      <div class="eng-welcome" id="eng-welcome">',
        '        <div class="eng-welcome-symbol">&#x2207;</div>',
        '        <div class="eng-welcome-title">Engineering Mathematics</div>',
        '        <div class="eng-welcome-sub">Select a semester, choose a topic, then pick a subtopic to begin. Seven powerful tabs — Learn, Revision, Formula Booklet, Subject Connections, PYQ Bank, Mock Test, Misconception Detector, and Ask AI.</div>',
        '      </div>',
        '    </div>',

        // Ask AI input
        '    <div class="eng-ask-area hidden" id="eng-ask-area">',
        '      <div class="eng-input-box">',
        '        <textarea id="eng-ask-input" rows="1" placeholder="Ask any engineering mathematics question..." oninput="this.style.height=\'auto\';this.style.height=this.scrollHeight+\'px\'" onkeydown="if(event.key===\'Enter\'&&!event.shiftKey){event.preventDefault();window.engModule.askAI()}"></textarea>',
        '        <button class="eng-send" onclick="window.engModule.askAI()">',
        '          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
        '        </button>',
        '      </div>',
        '    </div>',

        '  </div>',
        '</div>'
    ].join('');
    document.body.appendChild(el);

    // Mobile overlay
    var overlay = document.createElement('div');
    overlay.id = 'eng-mobile-overlay';
    overlay.className = 'eng-mobile-overlay';
    overlay.addEventListener('click', function() { closeSidebar(); });
    document.body.appendChild(overlay);
}

// ══════════════════════════════════════════════════════════════
//  SYLLABUS LOAD
// ══════════════════════════════════════════════════════════════
function loadSyllabus() {
    fetch('/eng/syllabus')
        .then(function(r){ return r.json(); })
        .then(function(data){ state.syllabus = data; })
        .catch(function(e){ console.warn('Syllabus load failed', e); });
}

// ══════════════════════════════════════════════════════════════
//  MOBILE SIDEBAR DRAWER
// ══════════════════════════════════════════════════════════════
function toggleSidebar() {
    var sidebar = document.getElementById('eng-app').querySelector('.eng-sidebar');
    var overlay = document.getElementById('eng-mobile-overlay');
    if (!sidebar) return;
    var isOpen = sidebar.classList.contains('mobile-open');
    if (isOpen) {
        sidebar.classList.remove('mobile-open');
        if (overlay) overlay.classList.remove('visible');
    } else {
        sidebar.classList.add('mobile-open');
        if (overlay) overlay.classList.add('visible');
    }
}

function closeSidebar() {
    var sidebar = document.getElementById('eng-app').querySelector('.eng-sidebar');
    var overlay = document.getElementById('eng-mobile-overlay');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('visible');
}

// ══════════════════════════════════════════════════════════════
//  MODE SWITCHING
// ══════════════════════════════════════════════════════════════
function showLanding() {
    document.getElementById('mode-landing').classList.remove('hidden');
    var app = document.getElementById('app');
    if (app) app.style.display = 'none';
    document.getElementById('eng-app').classList.remove('active');
    state.mode = null;
}

function chooseMode(mode) {
    localStorage.setItem('msMode', mode);
    document.getElementById('mode-landing').classList.add('hidden');
    if (mode === 'engineering') activateEngineering();
    else activateGeneral();
}

function activateGeneral() {
    state.mode = 'general';
    var app = document.getElementById('app');
    if (app) app.style.display = '';
    document.getElementById('eng-app').classList.remove('active');
    injectSwitchBtnIntoGeneral();
}

function activateEngineering() {
    state.mode = 'engineering';
    var app = document.getElementById('app');
    if (app) app.style.display = 'none';
    document.getElementById('eng-app').classList.add('active');
}

function injectSwitchBtnIntoGeneral() {
    var right = document.querySelector('.header-right');
    if (!right || document.getElementById('gen-switch-btn')) return;
    var btn = document.createElement('button');
    btn.id = 'gen-switch-btn';
    btn.className = 'mode-switch-btn';
    btn.textContent = 'Switch Mode';
    btn.onclick = function() { window.engModule.showLanding(); };
    right.insertBefore(btn, right.firstChild);
}

// ══════════════════════════════════════════════════════════════
//  TAB SWITCHING
// ══════════════════════════════════════════════════════════════
function switchTab(tab, btn) {
    state.activeTab = tab;
    document.querySelectorAll('.eng-tab').forEach(function(b){ b.classList.remove('active'); });
    btn.classList.add('active');

    toggleEl('eng-section-bar',  tab === 'learn' && state.activeSubtopic);
    toggleEl('eng-pyq-filters',  tab === 'pyq' && state.activeSubtopic);
    toggleEl('eng-mock-config',  tab === 'mocktest' && state.activeSubtopic);
    toggleEl('eng-ask-area',     tab === 'ask');
    toggleEl('eng-subtopic-bar', tab !== 'ask' && tab !== 'misconception' && state.activeTopic);

    if (state.activeSubtopic) {
        if (tab === 'revision')    fetchContent('revision');
        if (tab === 'formulabook') fetchFormulaBooklet();
        if (tab === 'connections') fetchConnections();
    }

    if (tab === 'ask') {
        setOutput(buildWelcomeHTML('?', 'Ask Engineering AI', 'Ask any B.Tech mathematics question. Context-aware answers tuned for semester exam preparation.'));
    }

    if (tab === 'misconception') {
        if (state.activeTopic) fetchMisconceptions();
        else setOutput(buildWelcomeHTML('&#x26A0;', 'Misconception Detector', 'Select a semester and topic from the left. Diagnostic questions will reveal hidden wrong beliefs that cost marks in university exams.'));
    }

    if (tab === 'connections' && !state.activeSubtopic) {
        setOutput(buildWelcomeHTML('&#x2194;', 'Subject Connections Map', 'Discover exactly where your mathematics appears in Circuits, Mechanics, Control Systems, Signals, and more.'));
    }

    if (tab === 'formulabook' && !state.activeSubtopic) {
        setOutput(buildWelcomeHTML('&#x2131;', 'Formula Booklet', 'Select a semester, topic, and subtopic to generate a complete formula reference with physical meanings, units, and examples.'));
    }

    if (tab === 'learn' && !state.activeSubtopic && !state.activeTopic) {
        setOutput(buildWelcomeHTML('&#x2207;', 'Engineering Mathematics', 'Select a semester, choose a topic, then pick a subtopic to begin learning.'));
    }
}

// ══════════════════════════════════════════════════════════════
//  WELCOME HTML BUILDER — reusable
// ══════════════════════════════════════════════════════════════
function buildWelcomeHTML(symbol, title, sub) {
    return [
        '<div class="eng-welcome">',
        '  <div class="eng-welcome-symbol">' + symbol + '</div>',
        '  <div class="eng-welcome-title">' + title + '</div>',
        '  <div class="eng-welcome-sub">' + sub + '</div>',
        '</div>'
    ].join('');
}

// ══════════════════════════════════════════════════════════════
//  MISCONCEPTION MODULE
// ══════════════════════════════════════════════════════════════
function fetchMisconceptions() {
    if (!state.activeTopic) return;
    showLoading('Loading diagnostic questions for ' + getTopicLabel(state.activeTopic) + '...');
    postToAPI('/eng/misconceptions', { topic: state.activeTopic }, function(data) {
        if (data.questions && data.questions.length) {
            renderMisconceptionQuestions(data.questions);
        } else {
            setOutput(buildWelcomeHTML('&#x26A0;', 'No questions yet', 'Misconception questions for this topic are being developed. Try another topic.'));
        }
    });
}

function renderMisconceptionQuestions(questions) {
    var dangerColors = {
        HIGH:     { color: '#ef4444', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.2)' },
        CRITICAL: { color: '#dc2626', bg: 'rgba(220,38,38,0.10)', border: 'rgba(220,38,38,0.25)' },
        MEDIUM:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)' }
    };

    var html = '<div style="padding:4px 0;">';
    // Header
    html += '<div style="margin-bottom:24px;">';
    html += '<div style="font-family:var(--e-mono);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#ef4444;margin-bottom:6px;">&#x26A0; Misconception Detector</div>';
    html += '<div style="font-size:20px;font-weight:800;color:var(--e-t1);letter-spacing:-.4px;">' + getTopicLabel(state.activeTopic) + '</div>';
    html += '<div style="font-size:12.5px;color:var(--e-t3);margin-top:8px;line-height:1.7;">Answer each question honestly. Your first instinct matters. The AI will analyse your thinking and identify misconceptions.</div>';
    html += '</div>';

    questions.forEach(function(q, i) {
        var d = dangerColors[q.danger] || dangerColors.MEDIUM;
        html += '<div class="eng-card" style="animation-delay:' + (i * 0.08) + 's" id="mc-card-' + q.id + '">';
        // Card header
        html += '<div class="eng-card-header" style="background:' + d.bg + ';border-left:3px solid ' + d.color + ';">';
        html += '<div style="flex:1;font-size:13px;font-weight:700;color:var(--e-t1);">Question ' + (i+1) + '</div>';
        html += '<div class="eng-card-tag" style="background:' + d.bg + ';color:' + d.color + ';border:1px solid ' + d.border + ';">' + q.danger + ' risk</div>';
        html += '</div>';
        // Card body
        html += '<div class="eng-card-body">';
        html += '<div style="font-size:13.5px;color:var(--e-t1);line-height:1.8;margin-bottom:14px;">' + q.question + '</div>';
        html += '<textarea id="mc-answer-' + q.id + '" placeholder="Write your answer here — in your own words..." style="width:100%;min-height:88px;background:var(--e-bg3);border:1px solid var(--e-border2);border-radius:10px;padding:12px 14px;color:var(--e-t1);font-size:13px;font-family:var(--e-sans);resize:vertical;outline:none;line-height:1.65;transition:border-color 200ms;"></textarea>';
        html += '<button onclick="window.engModule.submitMisconception(\'' + q.id + '\')" style="margin-top:12px;padding:8px 20px;background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);color:#ef4444;border-radius:8px;font-size:12px;font-weight:700;font-family:var(--e-sans);cursor:pointer;transition:all 200ms;">Diagnose My Thinking</button>';
        html += '<div id="mc-result-' + q.id + '" style="margin-top:14px;"></div>';
        html += '</div>';
        html += '</div>';
    });

    html += '</div>';
    setOutput(html);
}

function submitMisconception(questionId) {
    var textarea = document.getElementById('mc-answer-' + questionId);
    if (!textarea) return;
    var answer = textarea.value.trim();
    if (!answer) {
        textarea.style.borderColor = '#ef4444';
        textarea.placeholder = 'Please write your answer first...';
        return;
    }
    var resultDiv = document.getElementById('mc-result-' + questionId);
    if (resultDiv) {
        resultDiv.innerHTML = '<div style="display:flex;align-items:center;gap:12px;color:var(--e-t3);font-size:12px;font-family:var(--e-mono);padding:10px 0;"><div class="eng-spinner"></div>Analysing your thinking...</div>';
    }
    postToAPI('/eng/diagnose', {
        topic:       state.activeTopic,
        question_id: questionId,
        answer:      answer
    }, function(data) {
        if (resultDiv) {
            var rendered = typeof renderMathContent === 'function' ? renderMathContent(data.response) : data.response.replace(/\n/g, '<br>');
            resultDiv.innerHTML = '<div style="background:var(--e-bg3);border:1px solid rgba(239,68,68,0.15);border-left:3px solid #ef4444;border-radius:0 10px 10px 0;padding:16px 18px;font-size:13px;line-height:1.85;color:var(--e-t2);animation:e-in 0.3s var(--e-ease);">' + rendered + '</div>';
            typesetOutput();
        }
    });
}

// ══════════════════════════════════════════════════════════════
//  NAVIGATION
// ══════════════════════════════════════════════════════════════
function selectSem(sem, btn) {
    state.activeSem = sem;
    state.activeTopic = null;
    state.activeSubtopic = null;
    document.querySelectorAll('.eng-sem-pill').forEach(function(b){ b.classList.remove('active'); });
    btn.classList.add('active');
    renderTopicList(sem);
    clearSubtopics();
    clearSectionBar();
    clearFilters();
    var label = (state.syllabus && state.syllabus[sem]) ? state.syllabus[sem].label : sem;
    setOutput(buildWelcomeHTML('&#x222B;', label, 'Select a topic from the left to begin.'));
}

function renderTopicList(sem) {
    var list = document.getElementById('eng-topic-list');
    if (!list || !state.syllabus || !state.syllabus[sem]) { if(list) list.innerHTML = ''; return; }
    var topics = state.syllabus[sem].topics;
    list.innerHTML = '';
    var idx = 0;
    Object.keys(topics).forEach(function(key) {
        var t = topics[key];
        var btn = document.createElement('button');
        btn.className = 'eng-topic-btn';
        btn.setAttribute('data-topic', key);
        btn.textContent = t.label;
        btn.style.animation = 'e-in 0.25s var(--e-ease) ' + (idx * 0.04) + 's both';
        btn.addEventListener('click', function() {
            selectTopic(key, btn);
        });
        var group = document.createElement('div');
        group.className = 'eng-topic-group';
        group.appendChild(btn);
        list.appendChild(group);
        idx++;
    });
}

function selectTopic(topicKey, btn) {
    state.activeTopic = topicKey;
    state.activeSubtopic = null;
    document.querySelectorAll('.eng-topic-btn').forEach(function(b){ b.classList.remove('active'); });
    btn.classList.add('active');
    renderSubtopics(topicKey);
    clearSectionBar();
    clearFilters();
    closeSidebar();

    if (state.activeTab === 'misconception') {
        fetchMisconceptions();
        return;
    }
    if (state.activeTab === 'connections') {
        fetchConnections();
        return;
    }
    setOutput(buildWelcomeHTML('{ }', btn.textContent, 'Select a subtopic above to load content.'));
}

function renderSubtopics(topicKey) {
    var bar = document.getElementById('eng-subtopic-bar');
    if (!bar || !state.syllabus || !state.activeSem) { if(bar) bar.classList.add('hidden'); return; }
    var sem = state.syllabus[state.activeSem];
    if (!sem || !sem.topics[topicKey]) { bar.classList.add('hidden'); return; }
    if (state.activeTab === 'connections') { bar.classList.add('hidden'); return; }

    var subs = sem.topics[topicKey].subtopics;
    bar.innerHTML = '';
    subs.forEach(function(s, idx) {
        var btn = document.createElement('button');
        btn.className = 'eng-chip';
        btn.setAttribute('data-sub', s);
        btn.textContent = s;
        btn.style.animation = 'e-in 0.2s var(--e-ease) ' + (idx * 0.03) + 's both';
        btn.addEventListener('click', function() {
            selectSubtopic(s, btn);
        });
        bar.appendChild(btn);
    });
    bar.classList.remove('hidden');
}

function selectSubtopic(sub, btn) {
    state.activeSubtopic = sub;
    document.querySelectorAll('.eng-chip').forEach(function(b){ b.classList.remove('active'); });
    btn.classList.add('active');

    if (state.activeTab === 'learn') {
        document.getElementById('eng-section-bar').classList.remove('hidden');
        document.querySelectorAll('.eng-sec-btn').forEach(function(b){ b.classList.remove('active'); });
        document.querySelector('.eng-sec-btn[data-sec="definition"]').classList.add('active');
        state.activeSection = 'definition';
        fetchContent('learn');
    } else if (state.activeTab === 'revision') {
        document.getElementById('eng-section-bar').classList.add('hidden');
        fetchContent('revision');
    } else if (state.activeTab === 'formulabook') {
        document.getElementById('eng-section-bar').classList.add('hidden');
        fetchFormulaBooklet();
    } else if (state.activeTab === 'connections') {
        fetchConnections();
    } else if (state.activeTab === 'pyq') {
        document.getElementById('eng-pyq-filters').classList.remove('hidden');
        document.getElementById('eng-section-bar').classList.add('hidden');
        fetchPYQ();
    } else if (state.activeTab === 'mocktest') {
        document.getElementById('eng-mock-config').classList.remove('hidden');
        document.getElementById('eng-section-bar').classList.add('hidden');
    }
    toggleEl('eng-ask-area', state.activeTab === 'ask');
}

function selectSection(sec, btn) {
    state.activeSection = sec;
    document.querySelectorAll('.eng-sec-btn').forEach(function(b){ b.classList.remove('active'); });
    btn.classList.add('active');
    if (state.activeSubtopic) fetchContent('learn');
}

// ══════════════════════════════════════════════════════════════
//  API CALLS
// ══════════════════════════════════════════════════════════════
function fetchContent(mode) {
    if (!state.activeSubtopic) return;
    var label = mode === 'learn' ? state.activeSection : 'revision notes';
    showLoading('Generating ' + label + ' for ' + state.activeSubtopic + '...');
    var payload = { topic: state.activeTopic, subtopic: state.activeSubtopic };
    if (mode === 'learn') payload.section = state.activeSection;
    var endpoint = mode === 'learn' ? '/eng/learn' : '/eng/revision';
    postToAPI(endpoint, payload, function(data) {
        renderResponse(data.response, data.source, data.references || [], data.prerequisites || []);
    });
}

function fetchFormulaBooklet() {
    if (!state.activeSubtopic) return;
    showLoading('Generating Formula Booklet for ' + state.activeSubtopic + '...');
    postToAPI('/eng/formulabooklet', {
        topic: state.activeTopic,
        subtopic: state.activeSubtopic
    }, function(data) {
        renderResponse(data.response, data.source, data.references || []);
    });
}

function fetchConnections() {
    var displayName = state.activeSubtopic || (state.activeTopic ? getTopicLabel(state.activeTopic) : '');
    if (!state.activeTopic) return;
    showLoading('Mapping connections for ' + displayName + '...');
    postToAPI('/eng/connections', {
        topic: state.activeTopic,
        subtopic: state.activeSubtopic || displayName
    }, function(data) {
        if (data.connections) {
            renderConnectionsCard(data.connections, displayName, data.references || []);
        } else {
            renderResponse(data.response, data.source, data.references || []);
        }
    });
}

function getTopicLabel(topicKey) {
    if (!state.syllabus || !state.activeSem) return topicKey;
    var sem = state.syllabus[state.activeSem];
    if (sem && sem.topics[topicKey]) return sem.topics[topicKey].label;
    return topicKey;
}

function renderConnectionsCard(connections, topicLabel, refs) {
    var palettes = [
        { color: '#4f9cf7', bg: 'rgba(79,156,247,0.08)', border: 'rgba(79,156,247,0.2)' },
        { color: '#4ade80', bg: 'rgba(74,222,128,0.08)', border: 'rgba(74,222,128,0.2)' },
        { color: '#fbbf24', bg: 'rgba(251,191,36,0.08)', border: 'rgba(251,191,36,0.2)' },
        { color: '#f87171', bg: 'rgba(248,113,113,0.08)', border: 'rgba(248,113,113,0.2)' },
        { color: '#a78bfa', bg: 'rgba(167,139,250,0.08)', border: 'rgba(167,139,250,0.2)' },
        { color: '#22d3ee', bg: 'rgba(34,211,238,0.08)', border: 'rgba(34,211,238,0.2)' }
    ];

    var html = '<div style="padding:4px 0">';
    html += '<div style="margin-bottom:24px;">';
    html += '<div style="font-family:var(--e-mono);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#22d3ee;margin-bottom:6px;">&#x2194; Subject Connections Map</div>';
    html += '<div style="font-size:20px;font-weight:800;color:var(--e-t1);letter-spacing:-.4px;">' + topicLabel + '</div>';
    html += '<div style="font-size:12.5px;color:var(--e-t3);margin-top:6px;">Where this mathematics powers your engineering subjects</div>';
    html += '</div>';

    connections.forEach(function(c, i) {
        var p = palettes[i % palettes.length];
        html += '<div class="eng-card" style="animation-delay:' + (i * 0.08) + 's">';
        html += '<div class="eng-card-header" style="background:' + p.bg + ';border-left:3px solid ' + p.color + ';">';
        html += '<div style="flex:1;">';
        html += '<div style="font-size:14px;font-weight:700;color:' + p.color + ';letter-spacing:-.2px;">' + c.subject + '</div>';
        html += '<div style="font-size:11px;color:var(--e-t3);margin-top:2px;font-family:var(--e-mono);">' + c.semester + '</div>';
        html += '</div>';
        html += '<div class="eng-card-tag" style="background:' + p.bg + ';color:' + p.color + ';border:1px solid ' + p.border + ';">Engineering</div>';
        html += '</div>';
        html += '<div class="eng-card-body">';
        html += '<div style="font-size:12.5px;color:var(--e-t2);line-height:1.75;margin-bottom:12px;">' + c.how + '</div>';
        html += '<div style="background:var(--e-bg3);border:1px solid var(--e-border);border-radius:8px;padding:12px 16px;font-family:var(--e-mono);font-size:12px;color:var(--e-t2);">';
        html += '<span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:' + p.color + ';display:block;margin-bottom:8px;">Example</span>';
        html += c.example;
        html += '</div>';
        html += '</div>';
        html += '</div>';
    });

    html += '</div>';

    var refsHtml = buildRefsHTML(refs);
    setOutput('<div class="eng-response">' + html + '</div>' + refsHtml);
    typesetOutput();
}

function fetchPYQ() {
    if (!state.activeSubtopic) return;
    var univ = document.getElementById('eng-univ-select').value;
    var diff = document.getElementById('eng-diff-select').value;
    showLoading('Fetching PYQs on ' + state.activeSubtopic + '...');
    postToAPI('/eng/pyq', {
        topic: state.activeTopic,
        subtopic: state.activeSubtopic,
        university: univ,
        difficulty: diff
    }, function(data) {
        renderResponse(data.response, data.source, data.references || []);
    });
}

function fetchMockTest() {
    if (!state.activeSubtopic) return;
    var numQ  = document.getElementById('eng-numq-select').value;
    var marks = document.getElementById('eng-marks-select').value;
    showLoading('Generating ' + numQ + '-question mock test...');
    postToAPI('/eng/mocktest', {
        topic: state.activeTopic,
        subtopic: state.activeSubtopic,
        num_questions: numQ,
        marks_each: marks
    }, function(data) {
        renderResponse(data.response, data.source, []);
    });
}

function askAI() {
    var inp = document.getElementById('eng-ask-input');
    var q = inp.value.trim();
    if (!q) return;
    inp.value = '';
    inp.style.height = 'auto';
    showLoading('Thinking...');
    postToAPI('/eng/ask', { question: q }, function(data) {
        renderResponse(data.response, data.source, []);
    });
}

function postToAPI(endpoint, payload, cb) {
    state.loading = true;
    fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(function(r){ return r.json(); })
    .then(function(data){
        state.loading = false;
        if (data.error) {
            setOutput('<div class="eng-response"><p style="color:var(--e-rose)">Error: ' + data.error + '</p></div>');
        } else {
            cb(data);
        }
    })
    .catch(function(e){
        state.loading = false;
        setOutput('<div class="eng-response"><p style="color:var(--e-rose)">Network error. Please try again.</p></div>');
    });
}

// ══════════════════════════════════════════════════════════════
//  RENDERING
// ══════════════════════════════════════════════════════════════
function showLoading(msg) {
    setOutput('<div class="eng-loading"><div class="eng-spinner"></div><span>' + (msg || 'Loading...') + '</span></div>');
}

function renderResponse(text, source, refs, prereqs) {
    var rendered = '';
    if (typeof renderMathContent === 'function') {
        rendered = renderMathContent(text);
    } else {
        rendered = '<p class="vr-para">' +
            text.replace(/\n{2,}/g, '</p><p class="vr-para">')
                .replace(/\n/g, '<br>') + '</p>';
    }

    // Prerequisites
    var prereqHtml = '';
    if (prereqs && prereqs.length) {
        var pills = prereqs.map(function(p) {
            return '<span class="eng-prereq-pill">' + p + '</span>';
        }).join('');
        prereqHtml = '<div class="eng-prereq-banner">';
        prereqHtml += '<div class="eng-prereq-label">Prerequisites</div>';
        prereqHtml += '<div class="eng-prereq-pills">' + pills + '</div>';
        prereqHtml += '</div>';
    }

    var sourceHtml = source
        ? '<div style="margin-top:14px;font-size:10px;font-family:var(--e-mono);color:var(--e-t4);display:flex;align-items:center;gap:6px;"><span style="width:4px;height:4px;border-radius:50%;background:var(--e-blue);display:inline-block;"></span>Source: ' + source + '</div>'
        : '';

    var refsHtml = buildRefsHTML(refs);

    setOutput(prereqHtml + '<div class="eng-response">' + rendered + sourceHtml + '</div>' + refsHtml);
    typesetOutput();
}

function buildRefsHTML(refs) {
    if (!refs || !refs.length) return '';
    var links = refs.map(function(url) {
        var label = url.replace(/^https?:\/\/(?:www\.)?/, '').split('/')[0];
        return '<a href="' + url + '" target="_blank" rel="noopener">&#x1F517; ' + label + '</a>';
    }).join('');
    return [
        '<div class="eng-refs">',
        '  <div class="eng-refs-title">References &amp; Further Reading</div>',
        '  <div class="eng-refs-list">' + links + '</div>',
        '</div>'
    ].join('');
}

function typesetOutput() {
    var out = document.getElementById('eng-output');
    if (!out) return;
    if (typeof typesetEl === 'function') {
        typesetEl(out);
    } else if (window.MathJax && window.MathJax.typesetPromise) {
        setTimeout(function() {
            window.MathJax.typesetPromise([out]).catch(function(){});
        }, 60);
    }
}

function setOutput(html) {
    var out = document.getElementById('eng-output');
    if (out) {
        out.innerHTML = html;
        // Scroll to top of output on new content
        out.scrollTop = 0;
    }
}

// ══════════════════════════════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════════════════════════════
function toggleEl(id, show) {
    var el = document.getElementById(id);
    if (!el) return;
    if (show) el.classList.remove('hidden');
    else el.classList.add('hidden');
}
function clearSubtopics() {
    var bar = document.getElementById('eng-subtopic-bar');
    if (bar) { bar.innerHTML = ''; bar.classList.add('hidden'); }
}
function clearSectionBar() {
    var bar = document.getElementById('eng-section-bar');
    if (bar) bar.classList.add('hidden');
}
function clearFilters() {
    toggleEl('eng-pyq-filters', false);
    toggleEl('eng-mock-config', false);
}

// ══════════════════════════════════════════════════════════════
//  PUBLIC API
// ══════════════════════════════════════════════════════════════
window.engModule = {
    chooseMode:           chooseMode,
    showLanding:          showLanding,
    switchTab:            switchTab,
    selectSem:            selectSem,
    selectTopic:          selectTopic,
    selectSubtopic:       selectSubtopic,
    selectSection:        selectSection,
    fetchPYQ:             fetchPYQ,
    fetchMockTest:        fetchMockTest,
    askAI:                askAI,
    toggleSidebar:        toggleSidebar,
    submitMisconception:  submitMisconception
};

})();
