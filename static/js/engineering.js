// ══════════════════════════════════════════════════════════════
//  MATHSPHERE ENGINEERING — engineering.js
//  Mode switcher + full engineering interface + GATE Exam Module
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
    loading:        false,
    // GATE state
    gateMode:       false,
    gateBranch:     null,
    gateActiveTab:  'practice',
    gateInfo:       null,
    gateTopicKey:   null,
    gateSubtopic:   null
};

var GATE_BRANCHES = {
    cs: { label: 'Computer Science', icon: '\uD83D\uDCBB', color: '#4f9cf7', short: 'CS' },
    ec: { label: 'Electronics & Comm', icon: '\uD83D\uDCE1', color: '#22d3ee', short: 'EC' },
    me: { label: 'Mechanical', icon: '\u2699\uFE0F', color: '#fb923c', short: 'ME' },
    ce: { label: 'Civil', icon: '\uD83C\uDFD7\uFE0F', color: '#4ade80', short: 'CE' },
    ee: { label: 'Electrical', icon: '\u26A1', color: '#fbbf24', short: 'EE' }
};

var GATE_TOPICS = {
    linear_algebra:    { label: 'Linear Algebra', icon: '\uD83D\uDCD0' },
    calculus:          { label: 'Calculus', icon: '\u222B' },
    probability:       { label: 'Probability & Statistics', icon: '\uD83C\uDFB2' },
    diff_equations:    { label: 'Differential Equations', icon: '\uD83D\uDCC8' },
    complex_analysis:  { label: 'Complex Analysis', icon: '\uD83C\uDF00' },
    numerical_methods: { label: 'Numerical Methods', icon: '\uD83D\uDD22' },
    transforms:        { label: 'Transforms', icon: '\uD83D\uDD04' }
};

var GATE_FORMULA_CATS = {
    linear_algebra_shortcuts: { label: 'Linear Algebra Shortcuts', icon: '\uD83D\uDCD0' },
    calculus_shortcuts:       { label: 'Calculus Shortcuts', icon: '\u222B' },
    probability_shortcuts:    { label: 'Probability Shortcuts', icon: '\uD83C\uDFB2' },
    de_shortcuts:             { label: 'DE Shortcuts', icon: '\uD83D\uDCC8' },
    complex_shortcuts:        { label: 'Complex Shortcuts', icon: '\uD83C\uDF00' }
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
//  MOUSE TRACKING
// ══════════════════════════════════════════════════════════════
function setupMouseTracking() {
    document.addEventListener('mousemove', function(e) {
        var cards = document.querySelectorAll('.landing-card, .gate-branch-card');
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
//  LANDING OVERLAY
// ══════════════════════════════════════════════════════════════
function injectLanding() {
    var el = document.createElement('div');
    el.id = 'mode-landing';
    el.className = 'hidden';

    var particleHTML = '<div class="landing-particles">';
    for (var i = 1; i <= 15; i++) {
        particleHTML += '<div class="p"></div>';
    }
    particleHTML += '</div>';

    el.innerHTML = [
        '<div class="landing-aurora"></div>',
        '<div class="landing-orb landing-orb--1"></div>',
        '<div class="landing-orb landing-orb--2"></div>',
        '<div class="landing-orb landing-orb--3"></div>',
        particleHTML,
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
//  ENGINEERING APP SHELL
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
        '  <div class="eng-tabs" id="eng-tabs-bar">',
        '    <button class="eng-tab active" data-tab="learn"         onclick="window.engModule.switchTab(\'learn\',this)">Learn</button>',
        '    <button class="eng-tab"        data-tab="revision"      onclick="window.engModule.switchTab(\'revision\',this)">Quick Revision</button>',
        '    <button class="eng-tab"        data-tab="formulabook"   onclick="window.engModule.switchTab(\'formulabook\',this)">Formula Booklet</button>',
        '    <button class="eng-tab"        data-tab="connections"   onclick="window.engModule.switchTab(\'connections\',this)">Subject Connections</button>',
        '    <button class="eng-tab"        data-tab="pyq"           onclick="window.engModule.switchTab(\'pyq\',this)">PYQ Bank</button>',
        '    <button class="eng-tab"        data-tab="mocktest"      onclick="window.engModule.switchTab(\'mocktest\',this)">Mock Test</button>',
        '    <button class="eng-tab"        data-tab="misconception" onclick="window.engModule.switchTab(\'misconception\',this)">Misconception Detector</button>',
        '    <button class="eng-tab"        data-tab="ask"           onclick="window.engModule.switchTab(\'ask\',this)">Ask AI</button>',
        '    <button class="eng-tab eng-tab--gate" data-tab="gate"   onclick="window.engModule.switchTab(\'gate\',this)">&#x1F3AF; GATE Exam</button>',
        '  </div>',
        '  <div class="eng-header-right">',
        '    <div class="eng-status">ONLINE</div>',
        '    <button class="mode-switch-btn" onclick="window.engModule.showLanding()">&#x21C4; Mode</button>',
        '  </div>',
        '</div>',

        // Body
        '<div class="eng-body">',

        // Sidebar
        '  <div class="eng-sidebar" id="eng-sidebar">',
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

        // GATE config bar
        '    <div class="eng-gate-config hidden" id="eng-gate-config"></div>',

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
//  MOBILE SIDEBAR
// ══════════════════════════════════════════════════════════════
function toggleSidebar() {
    var sidebar = document.getElementById('eng-sidebar');
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
    var sidebar = document.getElementById('eng-sidebar');
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

    // Exit GATE mode if switching away
    if (tab !== 'gate') {
        state.gateMode = false;
        toggleEl('eng-gate-config', false);
        // Show normal sidebar
        var sidebar = document.getElementById('eng-sidebar');
        if (sidebar) sidebar.classList.remove('gate-sidebar-mode');
    }

    toggleEl('eng-section-bar',  tab === 'learn' && state.activeSubtopic);
    toggleEl('eng-pyq-filters',  tab === 'pyq' && state.activeSubtopic);
    toggleEl('eng-mock-config',  tab === 'mocktest' && state.activeSubtopic);
    toggleEl('eng-ask-area',     tab === 'ask');
    toggleEl('eng-subtopic-bar', tab !== 'ask' && tab !== 'misconception' && tab !== 'gate' && state.activeTopic);
    toggleEl('eng-gate-config',  false);

    if (tab === 'gate') {
        state.gateMode = true;
        toggleEl('eng-section-bar', false);
        toggleEl('eng-pyq-filters', false);
        toggleEl('eng-mock-config', false);
        toggleEl('eng-ask-area', false);
        toggleEl('eng-subtopic-bar', false);
        showGateDashboard();
        return;
    }

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
//  WELCOME HTML BUILDER
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
//  GATE EXAM MODULE — Dashboard
// ══════════════════════════════════════════════════════════════
function showGateDashboard() {
    // Transform sidebar for GATE
    var sidebar = document.getElementById('eng-sidebar');
    if (sidebar) sidebar.classList.add('gate-sidebar-mode');

    // Build GATE sidebar content
    renderGateSidebar();

    if (!state.gateBranch) {
        renderGateBranchSelection();
    } else {
        renderGateMainPanel();
    }
}

function renderGateSidebar() {
    var semPills = document.getElementById('eng-sem-pills');
    var topicList = document.getElementById('eng-topic-list');

    if (semPills) {
        semPills.innerHTML = [
            '<button class="eng-sem-pill gate-back-pill" onclick="window.engModule.gateBackToBranches()">',
            '  &#x2190; Branches',
            '</button>',
            '<button class="eng-sem-pill gate-exam-pill active">',
            '  &#x1F3AF; GATE',
            '</button>'
        ].join('');
    }

    if (topicList) {
        var html = '';

        // GATE Tabs in sidebar
        var gateTabs = [
            { key: 'practice',       label: 'Practice Questions', icon: '&#x270D;' },
            { key: 'mock',           label: 'Mock Test', icon: '&#x1F4DD;' },
            { key: 'strategy',       label: 'Prep Strategy', icon: '&#x1F4C8;' },
            { key: 'formulas',       label: 'Quick Formulas', icon: '&#x26A1;' },
            { key: 'misconceptions', label: 'Trap Questions', icon: '&#x26A0;' },
            { key: 'syllabus',       label: 'Branch Syllabus', icon: '&#x1F4DA;' },
            { key: 'analysis',       label: 'Topic Analysis', icon: '&#x1F50D;' }
        ];

        gateTabs.forEach(function(t, idx) {
            var isActive = state.gateActiveTab === t.key;
            html += '<div class="eng-topic-group">';
            html += '<button class="eng-topic-btn' + (isActive ? ' active' : '') + '" ';
            html += 'data-gate-tab="' + t.key + '" ';
            html += 'style="animation:e-in 0.25s var(--e-ease) ' + (idx * 0.04) + 's both" ';
            html += 'onclick="window.engModule.switchGateTab(\'' + t.key + '\')">';
            html += '<span style="font-size:14px;">' + t.icon + '</span> ';
            html += t.label;
            html += '</button>';
            html += '</div>';
        });

        topicList.innerHTML = html;
    }
}

function renderGateBranchSelection() {
    var html = '<div class="gate-dashboard">';

    // Hero
    html += '<div class="gate-hero">';
    html += '<div class="gate-hero-badge">COMPETITIVE EXAM PREPARATION</div>';
    html += '<div class="gate-hero-title">GATE Exam <span class="gate-hero-accent">Module</span></div>';
    html += '<div class="gate-hero-sub">Practice MCQ, NAT & MSQ questions. Take mock tests. Get AI-powered prep strategies. Master shortcut formulas and avoid common traps.</div>';
    html += '</div>';

    // Branch cards
    html += '<div class="gate-branch-grid">';
    Object.keys(GATE_BRANCHES).forEach(function(key) {
        var b = GATE_BRANCHES[key];
        html += '<div class="gate-branch-card" style="--branch-color:' + b.color + '" onclick="window.engModule.selectGateBranch(\'' + key + '\')">';
        html += '<div class="gate-branch-icon">' + b.icon + '</div>';
        html += '<div class="gate-branch-short">' + b.short + '</div>';
        html += '<div class="gate-branch-label">' + b.label + '</div>';
        html += '<div class="gate-branch-arrow">Select &rarr;</div>';
        html += '</div>';
    });
    html += '</div>';

    // Quick info
    html += '<div class="gate-info-strip">';
    html += '<div class="gate-info-item"><span class="gate-info-num">5</span><span class="gate-info-label">Branches</span></div>';
    html += '<div class="gate-info-item"><span class="gate-info-num">7</span><span class="gate-info-label">Topic Areas</span></div>';
    html += '<div class="gate-info-item"><span class="gate-info-num">50+</span><span class="gate-info-label">Shortcut Formulas</span></div>';
    html += '<div class="gate-info-item"><span class="gate-info-num">20+</span><span class="gate-info-label">Trap Questions</span></div>';
    html += '</div>';

    // Also show JAM and CSIR cards
   

    html += '</div>';
    setOutput(html);
}

function selectGateBranch(branch) {
    state.gateBranch = branch;
    renderGateSidebar();
    renderGateMainPanel();

    // Load branch syllabus
    postToAPI('/eng/gate/syllabus', { branch: branch }, function(data) {
        state.gateSyllabus = data;
    });
}

function gateBackToBranches() {
    state.gateBranch = null;
    state.gateActiveTab = 'practice';
    renderGateSidebar();
    renderGateBranchSelection();
}

function switchGateTab(tab) {
    state.gateActiveTab = tab;

    // Update sidebar active states
    document.querySelectorAll('[data-gate-tab]').forEach(function(btn) {
        btn.classList.toggle('active', btn.getAttribute('data-gate-tab') === tab);
    });

    renderGateMainPanel();
}

function renderGateMainPanel() {
    var branch = state.gateBranch;
    var tab = state.gateActiveTab;
    var bInfo = branch ? GATE_BRANCHES[branch] : null;
    var branchLabel = bInfo ? bInfo.label + ' (' + bInfo.short + ')' : '';

    switch(tab) {
        case 'practice':    renderGatePractice(branch, branchLabel); break;
        case 'mock':        renderGateMock(branch, branchLabel); break;
        case 'strategy':    renderGateStrategy(branch, branchLabel); break;
        case 'formulas':    renderGateFormulas(); break;
        case 'misconceptions': renderGateMisconceptions(); break;
        case 'syllabus':    renderGateSyllabusPanel(branch, branchLabel); break;
        case 'analysis':    renderGateAnalysis(); break;
        default:            renderGatePractice(branch, branchLabel);
    }
}

// ══════════════════════════════════════════════════════════════
//  GATE — Practice Questions Panel
// ══════════════════════════════════════════════════════════════
function renderGatePractice(branch, branchLabel) {
    if (!branch) { renderGateBranchSelection(); return; }

    var html = '<div class="gate-panel">';

    // Header
    html += '<div class="gate-panel-header">';
    html += '<div class="gate-panel-badge" style="--badge-color:' + GATE_BRANCHES[branch].color + '">' + GATE_BRANCHES[branch].icon + ' GATE ' + GATE_BRANCHES[branch].short + '</div>';
    html += '<div class="gate-panel-title">Practice Questions</div>';
    html += '<div class="gate-panel-sub">Generate GATE-style MCQ, NAT, and MSQ questions with detailed solutions</div>';
    html += '</div>';

    // Topic selector
    html += '<div class="gate-form-section">';
    html += '<div class="gate-form-label">Select Topic</div>';
    html += '<div class="gate-topic-chips" id="gate-practice-topics">';
    Object.keys(GATE_TOPICS).forEach(function(key) {
        var t = GATE_TOPICS[key];
        var isActive = state.gateTopicKey === key;
        html += '<button class="gate-topic-chip' + (isActive ? ' active' : '') + '" onclick="window.engModule.selectGateTopic(\'' + key + '\')" data-topic="' + key + '">';
        html += '<span>' + t.icon + '</span> ' + t.label;
        html += '</button>';
    });
    html += '</div>';
    html += '</div>';

    // Subtopic input
    html += '<div class="gate-form-section">';
    html += '<div class="gate-form-label">Subtopic (specific area)</div>';
    html += '<input type="text" class="gate-input" id="gate-subtopic-input" placeholder="e.g., Eigenvalues, Cayley-Hamilton, Rank of matrix..." value="' + (state.gateSubtopic || '') + '">';
    html += '</div>';

    // Question type and difficulty
    html += '<div class="gate-form-row">';
    html += '<div class="gate-form-section gate-form-half">';
    html += '<div class="gate-form-label">Question Type</div>';
    html += '<select class="eng-select gate-select" id="gate-qtype-select">';
    html += '<option value="MCQ">MCQ (Multiple Choice)</option>';
    html += '<option value="NAT">NAT (Numerical Answer)</option>';
    html += '<option value="MSQ">MSQ (Multiple Select)</option>';
    html += '</select>';
    html += '</div>';
    html += '<div class="gate-form-section gate-form-half">';
    html += '<div class="gate-form-label">Difficulty</div>';
    html += '<select class="eng-select gate-select" id="gate-diff-select">';
    html += '<option value="easy">Easy (1 mark)</option>';
    html += '<option value="medium" selected>Medium (2 marks)</option>';
    html += '<option value="hard">Hard (2 marks, tricky)</option>';
    html += '</select>';
    html += '</div>';
    html += '</div>';

    // Generate button
    html += '<button class="gate-action-btn gate-action-primary" onclick="window.engModule.fetchGatePractice()">';
    html += '&#x270D; Generate GATE Practice Question';
    html += '</button>';

    // Result area
    html += '<div id="gate-practice-result"></div>';

    html += '</div>';
    setOutput(html);
}

function selectGateTopic(topicKey) {
    state.gateTopicKey = topicKey;
    document.querySelectorAll('.gate-topic-chip').forEach(function(c) {
        c.classList.toggle('active', c.getAttribute('data-topic') === topicKey);
    });
}

function fetchGatePractice() {
    var subtopicInput = document.getElementById('gate-subtopic-input');
    var subtopic = subtopicInput ? subtopicInput.value.trim() : '';
    if (!subtopic && !state.gateTopicKey) {
        alert('Please select a topic or enter a subtopic');
        return;
    }
    if (!subtopic) subtopic = GATE_TOPICS[state.gateTopicKey].label;

    var qtype = document.getElementById('gate-qtype-select').value;
    var diff = document.getElementById('gate-diff-select').value;

    var resultDiv = document.getElementById('gate-practice-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Generating GATE ' + qtype + ' question on ' + subtopic + '...</span></div>';
    }

    postToAPI('/eng/gate/practice', {
        subtopic: subtopic,
        branch: state.gateBranch,
        difficulty: diff,
        question_type: qtype
    }, function(data) {
        if (resultDiv) {
            var rendered = renderContent(data.response || data.question || JSON.stringify(data));
            resultDiv.innerHTML = '<div class="eng-response gate-response">' + rendered + '</div>';
            typesetOutput();
        }
        // Track progress
        postToAPI('/eng/progress/update', { type: 'gate_question' }, function(){});
    });
}

// ══════════════════════════════════════════════════════════════
//  GATE — Mock Test Panel
// ══════════════════════════════════════════════════════════════
function renderGateMock(branch, branchLabel) {
    if (!branch) { renderGateBranchSelection(); return; }

    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header">';
    html += '<div class="gate-panel-badge" style="--badge-color:' + GATE_BRANCHES[branch].color + '">' + GATE_BRANCHES[branch].icon + ' GATE ' + GATE_BRANCHES[branch].short + '</div>';
    html += '<div class="gate-panel-title">Mock Test Generator</div>';
    html += '<div class="gate-panel-sub">Simulate real GATE exam conditions with timed mock tests</div>';
    html += '</div>';

    html += '<div class="gate-form-row">';
    html += '<div class="gate-form-section gate-form-half">';
    html += '<div class="gate-form-label">Number of Questions</div>';
    html += '<select class="eng-select gate-select" id="gate-mock-numq">';
    html += '<option value="5">5 Questions (Quick)</option>';
    html += '<option value="10" selected>10 Questions (Standard)</option>';
    html += '<option value="15">15 Questions (Extended)</option>';
    html += '<option value="25">25 Questions (Full Section)</option>';
    html += '</select>';
    html += '</div>';
    html += '<div class="gate-form-section gate-form-half">';
    html += '<div class="gate-form-label">Time Limit (minutes)</div>';
    html += '<select class="eng-select gate-select" id="gate-mock-time">';
    html += '<option value="15">15 minutes</option>';
    html += '<option value="30" selected>30 minutes</option>';
    html += '<option value="45">45 minutes</option>';
    html += '<option value="60">60 minutes</option>';
    html += '<option value="180">180 minutes (Full Paper)</option>';
    html += '</select>';
    html += '</div>';
    html += '</div>';

    html += '<button class="gate-action-btn gate-action-primary" onclick="window.engModule.fetchGateMock()">';
    html += '&#x1F4DD; Generate Mock Test';
    html += '</button>';

    html += '<div id="gate-mock-result"></div>';
    html += '</div>';
    setOutput(html);
}

function fetchGateMock() {
    var numQ = document.getElementById('gate-mock-numq').value;
    var time = document.getElementById('gate-mock-time').value;

    var resultDiv = document.getElementById('gate-mock-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Generating ' + numQ + '-question GATE mock test...</span></div>';
    }

    postToAPI('/eng/gate/mock', {
        branch: state.gateBranch,
        num_questions: parseInt(numQ),
        time_minutes: parseInt(time)
    }, function(data) {
        if (resultDiv) {
            var rendered = renderContent(data.response || data.mock_test || JSON.stringify(data));
            resultDiv.innerHTML = '<div class="eng-response gate-response">' + rendered + '</div>';
            typesetOutput();
        }
        postToAPI('/eng/progress/update', { type: 'gate_mock' }, function(){});
    });
}

// ══════════════════════════════════════════════════════════════
//  GATE — Strategy Panel
// ══════════════════════════════════════════════════════════════
function renderGateStrategy(branch, branchLabel) {
    if (!branch) { renderGateBranchSelection(); return; }

    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header">';
    html += '<div class="gate-panel-badge" style="--badge-color:' + GATE_BRANCHES[branch].color + '">' + GATE_BRANCHES[branch].icon + ' GATE ' + GATE_BRANCHES[branch].short + '</div>';
    html += '<div class="gate-panel-title">Preparation Strategy</div>';
    html += '<div class="gate-panel-sub">AI-generated personalized preparation plan for your GATE exam</div>';
    html += '</div>';

    html += '<div class="gate-form-section">';
    html += '<div class="gate-form-label">Months until GATE exam</div>';
    html += '<select class="eng-select gate-select" id="gate-strategy-months">';
    html += '<option value="1">1 Month (Crash Course)</option>';
    html += '<option value="2">2 Months</option>';
    html += '<option value="3" selected>3 Months</option>';
    html += '<option value="6">6 Months (Recommended)</option>';
    html += '<option value="9">9 Months</option>';
    html += '<option value="12">12 Months (Full Prep)</option>';
    html += '</select>';
    html += '</div>';

    html += '<button class="gate-action-btn gate-action-primary" onclick="window.engModule.fetchGateStrategy()">';
    html += '&#x1F4C8; Generate My Strategy';
    html += '</button>';

    html += '<div id="gate-strategy-result"></div>';
    html += '</div>';
    setOutput(html);
}

function fetchGateStrategy() {
    var months = document.getElementById('gate-strategy-months').value;

    var resultDiv = document.getElementById('gate-strategy-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Crafting your ' + months + '-month GATE strategy...</span></div>';
    }

    postToAPI('/eng/gate/strategy', {
        branch: state.gateBranch,
        months: parseInt(months)
    }, function(data) {
        if (resultDiv) {
            var rendered = renderContent(data.response || data.strategy || JSON.stringify(data));
            resultDiv.innerHTML = '<div class="eng-response gate-response">' + rendered + '</div>';
            typesetOutput();
        }
    });
}

// ══════════════════════════════════════════════════════════════
//  GATE — Quick Formulas Panel
// ══════════════════════════════════════════════════════════════
function renderGateFormulas() {
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header">';
    html += '<div class="gate-panel-badge" style="--badge-color:#fbbf24">&#x26A1; GATE Shortcuts</div>';
    html += '<div class="gate-panel-title">Quick Formulas & Shortcuts</div>';
    html += '<div class="gate-panel-sub">50+ shortcut formulas organized by category. Memorize these for instant answers.</div>';
    html += '</div>';

    html += '<div class="gate-formula-grid">';
    Object.keys(GATE_FORMULA_CATS).forEach(function(key) {
        var cat = GATE_FORMULA_CATS[key];
        html += '<div class="gate-formula-card" onclick="window.engModule.fetchGateFormulas(\'' + key + '\')">';
        html += '<div class="gate-formula-icon">' + cat.icon + '</div>';
        html += '<div class="gate-formula-label">' + cat.label + '</div>';
        html += '<div class="gate-formula-arrow">View &rarr;</div>';
        html += '</div>';
    });
    html += '</div>';

    html += '<div id="gate-formula-result"></div>';
    html += '</div>';
    setOutput(html);
}

function fetchGateFormulas(category) {
    var resultDiv = document.getElementById('gate-formula-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Loading ' + GATE_FORMULA_CATS[category].label + '...</span></div>';
    }

    postToAPI('/eng/gate/formulas', { category: category }, function(data) {
        if (resultDiv) {
            var content = '';
            if (data.formulas && Array.isArray(data.formulas)) {
                content = renderFormulaList(data.formulas, category);
            } else if (data.response) {
                content = '<div class="eng-response gate-response">' + renderContent(data.response) + '</div>';
            } else {
                content = '<div class="eng-response gate-response">' + renderContent(JSON.stringify(data)) + '</div>';
            }
            resultDiv.innerHTML = content;
            typesetOutput();
        }
    });
}

function renderFormulaList(formulas, category) {
    var html = '<div style="margin-top:20px;">';
    html += '<div class="gate-section-title">' + GATE_FORMULA_CATS[category].icon + ' ' + GATE_FORMULA_CATS[category].label + '</div>';

    formulas.forEach(function(f, i) {
        html += '<div class="eng-card" style="animation-delay:' + (i * 0.06) + 's">';
        html += '<div class="eng-card-header" style="background:rgba(251,191,36,0.06);border-left:3px solid #fbbf24;">';
        html += '<div style="flex:1;font-size:13px;font-weight:700;color:var(--e-t1);">' + (f.name || f.title || 'Formula ' + (i+1)) + '</div>';
        if (f.marks_saved) {
            html += '<div class="eng-card-tag" style="background:rgba(74,222,128,0.08);color:#4ade80;border:1px solid rgba(74,222,128,0.2);">Saves ' + f.marks_saved + '</div>';
        }
        html += '</div>';
        html += '<div class="eng-card-body">';
        if (f.formula) html += '<div style="font-family:var(--e-mono);font-size:14px;color:var(--e-cyan);margin-bottom:8px;padding:12px;background:var(--e-bg3);border-radius:8px;border:1px solid var(--e-border);">' + f.formula + '</div>';
        if (f.when_to_use) html += '<div style="font-size:12.5px;color:var(--e-t2);line-height:1.7;"><strong style="color:var(--e-amber);">When to use:</strong> ' + f.when_to_use + '</div>';
        if (f.example) html += '<div style="font-size:12.5px;color:var(--e-t2);line-height:1.7;margin-top:6px;"><strong style="color:var(--e-blue);">Example:</strong> ' + f.example + '</div>';
        if (f.description) html += '<div style="font-size:12.5px;color:var(--e-t2);line-height:1.7;">' + f.description + '</div>';
        html += '</div></div>';
    });

    html += '</div>';
    return html;
}

// ══════════════════════════════════════════════════════════════
//  GATE — Misconceptions / Trap Questions Panel
// ══════════════════════════════════════════════════════════════
function renderGateMisconceptions() {
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header">';
    html += '<div class="gate-panel-badge" style="--badge-color:#f87171">&#x26A0; GATE Traps</div>';
    html += '<div class="gate-panel-title">Common Misconceptions & Traps</div>';
    html += '<div class="gate-panel-sub">20+ trap questions GATE loves to ask. Understand them before the exam catches you.</div>';
    html += '</div>';

    html += '<div class="gate-form-section">';
    html += '<div class="gate-form-label">Select Topic Area</div>';
    html += '<div class="gate-topic-chips">';
    Object.keys(GATE_TOPICS).forEach(function(key) {
        var t = GATE_TOPICS[key];
        html += '<button class="gate-topic-chip" onclick="window.engModule.fetchGateMisconceptions(\'' + key + '\')" data-topic="' + key + '">';
        html += '<span>' + t.icon + '</span> ' + t.label;
        html += '</button>';
    });
    html += '</div>';
    html += '</div>';

    html += '<div id="gate-misconception-result"></div>';
    html += '</div>';
    setOutput(html);
}

function fetchGateMisconceptions(topic) {
    var resultDiv = document.getElementById('gate-misconception-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Loading trap questions for ' + GATE_TOPICS[topic].label + '...</span></div>';
    }

    postToAPI('/eng/gate/misconceptions', { topic: topic }, function(data) {
        if (resultDiv) {
            var content = '';
            if (data.misconceptions && Array.isArray(data.misconceptions)) {
                content = renderMisconceptionsList(data.misconceptions, topic);
            } else if (data.response) {
                content = '<div class="eng-response gate-response">' + renderContent(data.response) + '</div>';
            } else {
                content = '<div class="eng-response gate-response">' + renderContent(JSON.stringify(data)) + '</div>';
            }
            resultDiv.innerHTML = content;
            typesetOutput();
        }
    });
}

function renderMisconceptionsList(misconceptions, topic) {
    var html = '<div style="margin-top:20px;">';
    html += '<div class="gate-section-title">&#x26A0; ' + GATE_TOPICS[topic].label + ' — Common Traps</div>';

    misconceptions.forEach(function(m, i) {
        var danger = m.danger || m.severity || 'HIGH';
        var colors = {
            HIGH:     { color: '#ef4444', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.2)' },
            CRITICAL: { color: '#dc2626', bg: 'rgba(220,38,38,0.10)', border: 'rgba(220,38,38,0.25)' },
            MEDIUM:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)' }
        };
        var c = colors[danger] || colors.HIGH;

        html += '<div class="eng-card" style="animation-delay:' + (i * 0.06) + 's">';
        html += '<div class="eng-card-header" style="background:' + c.bg + ';border-left:3px solid ' + c.color + ';">';
        html += '<div style="flex:1;font-size:13px;font-weight:700;color:var(--e-t1);">' + (m.title || m.misconception || 'Trap ' + (i+1)) + '</div>';
        html += '<div class="eng-card-tag" style="background:' + c.bg + ';color:' + c.color + ';border:1px solid ' + c.border + ';">' + danger + '</div>';
        html += '</div>';
        html += '<div class="eng-card-body">';
        if (m.wrong_thinking) html += '<div style="font-size:12.5px;color:#ef4444;line-height:1.7;margin-bottom:8px;"><strong>&#x2717; Wrong thinking:</strong> ' + m.wrong_thinking + '</div>';
        if (m.correct_thinking) html += '<div style="font-size:12.5px;color:#4ade80;line-height:1.7;margin-bottom:8px;"><strong>&#x2713; Correct thinking:</strong> ' + m.correct_thinking + '</div>';
        if (m.trap_question) html += '<div style="font-size:12.5px;color:var(--e-t2);line-height:1.7;padding:10px;background:var(--e-bg3);border-radius:8px;border:1px solid var(--e-border);"><strong style="color:var(--e-amber);">Trap question:</strong> ' + m.trap_question + '</div>';
        if (m.description) html += '<div style="font-size:12.5px;color:var(--e-t2);line-height:1.7;">' + m.description + '</div>';
        html += '</div></div>';
    });

    html += '</div>';
    return html;
}

// ══════════════════════════════════════════════════════════════
//  GATE — Branch Syllabus Panel
// ══════════════════════════════════════════════════════════════
function renderGateSyllabusPanel(branch, branchLabel) {
    if (!branch) { renderGateBranchSelection(); return; }

    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header">';
    html += '<div class="gate-panel-badge" style="--badge-color:' + GATE_BRANCHES[branch].color + '">' + GATE_BRANCHES[branch].icon + ' GATE ' + GATE_BRANCHES[branch].short + '</div>';
    html += '<div class="gate-panel-title">Branch Syllabus & Weightage</div>';
    html += '<div class="gate-panel-sub">Complete mathematics syllabus for GATE ' + branchLabel + '</div>';
    html += '</div>';

    html += '<div id="gate-syllabus-result"><div class="eng-loading"><div class="eng-spinner"></div><span>Loading syllabus for ' + branchLabel + '...</span></div></div>';
    html += '</div>';
    setOutput(html);

    postToAPI('/eng/gate/syllabus', { branch: branch }, function(data) {
        var resultDiv = document.getElementById('gate-syllabus-result');
        if (resultDiv) {
            if (data.syllabus || data.topics) {
                var content = renderSyllabusData(data, branch);
                resultDiv.innerHTML = content;
            } else if (data.response) {
                resultDiv.innerHTML = '<div class="eng-response gate-response">' + renderContent(data.response) + '</div>';
            } else {
                resultDiv.innerHTML = '<div class="eng-response gate-response">' + renderContent(JSON.stringify(data)) + '</div>';
            }
            typesetOutput();
        }
    });
}

function renderSyllabusData(data, branch) {
    var html = '<div style="margin-top:16px;">';

    if (data.syllabus && typeof data.syllabus === 'object') {
        Object.keys(data.syllabus).forEach(function(section, i) {
            var topics = data.syllabus[section];
            html += '<div class="eng-card" style="animation-delay:' + (i * 0.06) + 's">';
            html += '<div class="eng-card-header" style="background:rgba(79,156,247,0.06);border-left:3px solid ' + GATE_BRANCHES[branch].color + ';">';
            html += '<div style="font-size:14px;font-weight:700;color:var(--e-t1);">' + section + '</div>';
            html += '</div>';
            html += '<div class="eng-card-body">';
            if (Array.isArray(topics)) {
                html += '<ul style="margin:0;padding-left:20px;">';
                topics.forEach(function(t) {
                    html += '<li style="font-size:13px;color:var(--e-t2);line-height:1.8;">' + t + '</li>';
                });
                html += '</ul>';
            } else {
                html += '<div style="font-size:13px;color:var(--e-t2);line-height:1.8;">' + JSON.stringify(topics) + '</div>';
            }
            html += '</div></div>';
        });
    }

    if (data.weightage && typeof data.weightage === 'object') {
        html += '<div class="gate-section-title" style="margin-top:24px;">Topic Weightage</div>';
        Object.keys(data.weightage).forEach(function(topic, i) {
            var weight = data.weightage[topic];
            html += '<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;animation:e-in 0.25s var(--e-ease) ' + (i * 0.04) + 's both;">';
            html += '<div style="flex:1;font-size:13px;color:var(--e-t2);">' + topic + '</div>';
            html += '<div style="width:200px;height:6px;background:var(--e-bg3);border-radius:3px;overflow:hidden;">';
            html += '<div style="width:' + weight + '%;height:100%;background:' + GATE_BRANCHES[branch].color + ';border-radius:3px;transition:width 0.5s;"></div>';
            html += '</div>';
            html += '<div style="font-size:12px;font-family:var(--e-mono);color:' + GATE_BRANCHES[branch].color + ';min-width:36px;text-align:right;">' + weight + '%</div>';
            html += '</div>';
        });
    }

    // If the response is just text
    if (data.response) {
        html += '<div class="eng-response gate-response" style="margin-top:16px;">' + renderContent(data.response) + '</div>';
    }

    html += '</div>';
    return html;
}

// ══════════════════════════════════════════════════════════════
//  GATE — Topic Analysis Panel
// ══════════════════════════════════════════════════════════════
function renderGateAnalysis() {
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header">';
    html += '<div class="gate-panel-badge" style="--badge-color:#a78bfa">&#x1F50D; Deep Analysis</div>';
    html += '<div class="gate-panel-title">Topic-wise GATE Analysis</div>';
    html += '<div class="gate-panel-sub">Frequency, traps, time strategy, and scoring patterns for each topic</div>';
    html += '</div>';

    html += '<div class="gate-form-section">';
    html += '<div class="gate-form-label">Select Topic</div>';
    html += '<div class="gate-topic-chips">';
    Object.keys(GATE_TOPICS).forEach(function(key) {
        var t = GATE_TOPICS[key];
        html += '<button class="gate-topic-chip" onclick="window.engModule.fetchGateAnalysis(\'' + key + '\')" data-topic="' + key + '">';
        html += '<span>' + t.icon + '</span> ' + t.label;
        html += '</button>';
    });
    html += '</div>';
    html += '</div>';

    html += '<div id="gate-analysis-result"></div>';
    html += '</div>';
    setOutput(html);
}

function fetchGateAnalysis(topic) {
    var resultDiv = document.getElementById('gate-analysis-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Analysing ' + GATE_TOPICS[topic].label + ' patterns...</span></div>';
    }

    postToAPI('/eng/gate/analysis', { topic: topic }, function(data) {
        if (resultDiv) {
            if (data.analysis && typeof data.analysis === 'object') {
                                var a = data.analysis;
                var html = '<div style="margin-top:20px;">';
                html += '<div class="gate-section-title">' + GATE_TOPICS[topic].icon + ' ' + GATE_TOPICS[topic].label + ' — GATE Analysis</div>';

                if (a.frequency) {
                    html += '<div class="eng-card"><div class="eng-card-header" style="background:rgba(79,156,247,0.06);border-left:3px solid #4f9cf7;">';
                    html += '<div style="font-size:13px;font-weight:700;color:var(--e-t1);">Frequency in GATE</div></div>';
                    html += '<div class="eng-card-body"><div style="font-size:13px;color:var(--e-t2);line-height:1.8;">' + a.frequency + '</div></div></div>';
                }
                if (a.traps) {
                    html += '<div class="eng-card"><div class="eng-card-header" style="background:rgba(248,113,113,0.06);border-left:3px solid #f87171;">';
                    html += '<div style="font-size:13px;font-weight:700;color:var(--e-t1);">Common Traps</div></div>';
                    html += '<div class="eng-card-body"><div style="font-size:13px;color:var(--e-t2);line-height:1.8;">' + (Array.isArray(a.traps) ? a.traps.join('<br>') : a.traps) + '</div></div></div>';
                }
                if (a.time_strategy) {
                    html += '<div class="eng-card"><div class="eng-card-header" style="background:rgba(74,222,128,0.06);border-left:3px solid #4ade80;">';
                    html += '<div style="font-size:13px;font-weight:700;color:var(--e-t1);">Time Strategy</div></div>';
                    html += '<div class="eng-card-body"><div style="font-size:13px;color:var(--e-t2);line-height:1.8;">' + a.time_strategy + '</div></div></div>';
                }
                if (a.scoring_pattern) {
                    html += '<div class="eng-card"><div class="eng-card-header" style="background:rgba(251,191,36,0.06);border-left:3px solid #fbbf24;">';
                    html += '<div style="font-size:13px;font-weight:700;color:var(--e-t1);">Scoring Pattern</div></div>';
                    html += '<div class="eng-card-body"><div style="font-size:13px;color:var(--e-t2);line-height:1.8;">' + a.scoring_pattern + '</div></div></div>';
                }
                html += '</div>';
                resultDiv.innerHTML = html;
            } else if (data.response) {
                resultDiv.innerHTML = '<div class="eng-response gate-response">' + renderContent(data.response) + '</div>';
            } else {
                resultDiv.innerHTML = '<div class="eng-response gate-response">' + renderContent(JSON.stringify(data)) + '</div>';
            }
            typesetOutput();
        }
    });
}

// ══════════════════════════════════════════════════════════════
//  GATE — IIT JAM Practice Panel
// ══════════════════════════════════════════════════════════════
function renderJAMPractice() {
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header">';
    html += '<div class="gate-panel-badge" style="--badge-color:#a78bfa">&#x1F393; IIT JAM</div>';
    html += '<div class="gate-panel-title">IIT JAM Mathematics Practice</div>';
    html += '<div class="gate-panel-sub">Generate JAM-style practice questions with detailed solutions</div>';
    html += '</div>';

    html += '<div class="gate-form-section">';
    html += '<div class="gate-form-label">Subtopic</div>';
    html += '<input type="text" class="gate-input" id="jam-subtopic-input" placeholder="e.g., Real Analysis, Group Theory, Linear Algebra...">';
    html += '</div>';

    html += '<div class="gate-form-row">';
    html += '<div class="gate-form-section gate-form-half">';
    html += '<div class="gate-form-label">Paper Section</div>';
    html += '<select class="eng-select gate-select" id="jam-paper-select">';
    html += '<option value="A">Section A (MCQ)</option>';
    html += '<option value="B" selected>Section B (MSQ)</option>';
    html += '<option value="C">Section C (NAT)</option>';
    html += '</select>';
    html += '</div>';
    html += '<div class="gate-form-section gate-form-half">';
    html += '<div class="gate-form-label">Difficulty</div>';
    html += '<select class="eng-select gate-select" id="jam-diff-select">';
    html += '<option value="easy">Easy</option>';
    html += '<option value="medium" selected>Medium</option>';
    html += '<option value="hard">Hard</option>';
    html += '</select>';
    html += '</div>';
    html += '</div>';

    html += '<button class="gate-action-btn gate-action-primary" onclick="window.engModule.fetchJAMPractice()">';
    html += '&#x1F393; Generate JAM Question';
    html += '</button>';

    html += '<div id="jam-practice-result"></div>';
    html += '</div>';
    setOutput(html);
}

function fetchJAMPractice() {
    var subtopic = document.getElementById('jam-subtopic-input').value.trim();
    if (!subtopic) { alert('Please enter a subtopic'); return; }
    var paper = document.getElementById('jam-paper-select').value;
    var diff = document.getElementById('jam-diff-select').value;

    var resultDiv = document.getElementById('jam-practice-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Generating IIT JAM question on ' + subtopic + '...</span></div>';
    }

    postToAPI('/eng/jam/practice', {
        subtopic: subtopic,
        paper: paper,
        difficulty: diff
    }, function(data) {
        if (resultDiv) {
            var rendered = renderContent(data.response || data.question || JSON.stringify(data));
            resultDiv.innerHTML = '<div class="eng-response gate-response">' + rendered + '</div>';
            typesetOutput();
        }
    });
}

// ══════════════════════════════════════════════════════════════
//  GATE — CSIR NET Practice Panel
// ══════════════════════════════════════════════════════════════
function renderCSIRPractice() {
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header">';
    html += '<div class="gate-panel-badge" style="--badge-color:#22d3ee">&#x1F52C; CSIR NET</div>';
    html += '<div class="gate-panel-title">CSIR NET Mathematical Sciences</div>';
    html += '<div class="gate-panel-sub">Generate CSIR NET practice questions with detailed solutions</div>';
    html += '</div>';

    html += '<div class="gate-form-section">';
    html += '<div class="gate-form-label">Subtopic</div>';
    html += '<input type="text" class="gate-input" id="csir-subtopic-input" placeholder="e.g., Measure Theory, Functional Analysis, Topology...">';
    html += '</div>';

    html += '<div class="gate-form-row">';
    html += '<div class="gate-form-section gate-form-half">';
    html += '<div class="gate-form-label">Paper Part</div>';
    html += '<select class="eng-select gate-select" id="csir-part-select">';
    html += '<option value="A">Part A (General)</option>';
    html += '<option value="B" selected>Part B (Core)</option>';
    html += '<option value="C">Part C (Advanced)</option>';
    html += '</select>';
    html += '</div>';
    html += '<div class="gate-form-section gate-form-half">';
    html += '<div class="gate-form-label">Difficulty</div>';
    html += '<select class="eng-select gate-select" id="csir-diff-select">';
    html += '<option value="easy">Easy</option>';
    html += '<option value="medium" selected>Medium</option>';
    html += '<option value="hard">Hard</option>';
    html += '</select>';
    html += '</div>';
    html += '</div>';

    html += '<button class="gate-action-btn gate-action-primary" onclick="window.engModule.fetchCSIRPractice()">';
    html += '&#x1F52C; Generate CSIR NET Question';
    html += '</button>';

    html += '<div id="csir-practice-result"></div>';
    html += '</div>';
    setOutput(html);
}

function fetchCSIRPractice() {
    var subtopic = document.getElementById('csir-subtopic-input').value.trim();
    if (!subtopic) { alert('Please enter a subtopic'); return; }
    var part = document.getElementById('csir-part-select').value;
    var diff = document.getElementById('csir-diff-select').value;

    var resultDiv = document.getElementById('csir-practice-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Generating CSIR NET question on ' + subtopic + '...</span></div>';
    }

    postToAPI('/eng/csir/practice', {
        subtopic: subtopic,
        part: part,
        difficulty: diff
    }, function(data) {
        if (resultDiv) {
            var rendered = renderContent(data.response || data.question || JSON.stringify(data));
            resultDiv.innerHTML = '<div class="eng-response gate-response">' + rendered + '</div>';
            typesetOutput();
        }
    });
}

// ══════════════════════════════════════════════════════════════
//  MISCONCEPTION MODULE (University level — original)
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
    html += '<div style="margin-bottom:24px;">';
    html += '<div style="font-family:var(--e-mono);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#ef4444;margin-bottom:6px;">&#x26A0; Misconception Detector</div>';
    html += '<div style="font-size:20px;font-weight:800;color:var(--e-t1);letter-spacing:-.4px;">' + getTopicLabel(state.activeTopic) + '</div>';
    html += '<div style="font-size:12.5px;color:var(--e-t3);margin-top:8px;line-height:1.7;">Answer each question honestly. Your first instinct matters. The AI will analyse your thinking and identify misconceptions.</div>';
    html += '</div>';

    questions.forEach(function(q, i) {
        var d = dangerColors[q.danger] || dangerColors.MEDIUM;
        html += '<div class="eng-card" style="animation-delay:' + (i * 0.08) + 's" id="mc-card-' + q.id + '">';
        html += '<div class="eng-card-header" style="background:' + d.bg + ';border-left:3px solid ' + d.color + ';">';
        html += '<div style="flex:1;font-size:13px;font-weight:700;color:var(--e-t1);">Question ' + (i+1) + '</div>';
        html += '<div class="eng-card-tag" style="background:' + d.bg + ';color:' + d.color + ';border:1px solid ' + d.border + ';">' + q.danger + ' risk</div>';
        html += '</div>';
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
            var rendered = renderContent(data.response);
            resultDiv.innerHTML = '<div style="background:var(--e-bg3);border:1px solid rgba(239,68,68,0.15);border-left:3px solid #ef4444;border-radius:0 10px 10px 0;padding:16px 18px;font-size:13px;line-height:1.85;color:var(--e-t2);animation:e-in 0.3s var(--e-ease);">' + rendered + '</div>';
            typesetOutput();
        }
    });
}

// ══════════════════════════════════════════════════════════════
//  NAVIGATION
// ══════════════════════════════════════════════════════════════
function selectSem(sem, btn) {
    // Exit gate mode when selecting semester
    if (state.gateMode) {
        state.gateMode = false;
        state.activeTab = 'learn';
        document.querySelectorAll('.eng-tab').forEach(function(b){ b.classList.remove('active'); });
        document.querySelector('.eng-tab[data-tab="learn"]').classList.add('active');
        var sidebar = document.getElementById('eng-sidebar');
        if (sidebar) sidebar.classList.remove('gate-sidebar-mode');
        toggleEl('eng-gate-config', false);
    }

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
//  API CALLS (University level)
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
            var errorTarget = document.querySelector('[id$="-result"]');
            var errorHTML = '<div class="eng-response"><p style="color:var(--e-rose)">Error: ' + data.error + '</p></div>';
            if (errorTarget && state.gateMode) {
                errorTarget.innerHTML = errorHTML;
            } else {
                setOutput(errorHTML);
            }
        } else {
            cb(data);
        }
    })
    .catch(function(e){
        state.loading = false;
        var errorHTML = '<div class="eng-response"><p style="color:var(--e-rose)">Network error. Please try again.</p></div>';
        var errorTarget = document.querySelector('[id$="-result"]');
        if (errorTarget && state.gateMode) {
            errorTarget.innerHTML = errorHTML;
        } else {
            setOutput(errorHTML);
        }
    });
}

// ══════════════════════════════════════════════════════════════
//  RENDERING
// ══════════════════════════════════════════════════════════════
function showLoading(msg) {
    setOutput('<div class="eng-loading"><div class="eng-spinner"></div><span>' + (msg || 'Loading...') + '</span></div>');
}

function renderContent(text) {
    if (typeof renderMathContent === 'function') {
        return renderMathContent(text);
    }
    return '<p class="vr-para">' +
        text.replace(/\n{2,}/g, '</p><p class="vr-para">')
            .replace(/\n/g, '<br>') + '</p>';
}

function renderResponse(text, source, refs, prereqs) {
    var rendered = renderContent(text);

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
    chooseMode:            chooseMode,
    showLanding:           showLanding,
    switchTab:             switchTab,
    selectSem:             selectSem,
    selectTopic:           selectTopic,
    selectSubtopic:        selectSubtopic,
    selectSection:         selectSection,
    fetchPYQ:              fetchPYQ,
    fetchMockTest:         fetchMockTest,
    askAI:                 askAI,
    toggleSidebar:         toggleSidebar,
    submitMisconception:   submitMisconception,
    // GATE
    selectGateBranch:      selectGateBranch,
    gateBackToBranches:    gateBackToBranches,
    switchGateTab:         switchGateTab,
    selectGateTopic:       selectGateTopic,
    fetchGatePractice:     fetchGatePractice,
    fetchGateMock:         fetchGateMock,
    fetchGateStrategy:     fetchGateStrategy,
    fetchGateFormulas:     fetchGateFormulas,
    fetchGateMisconceptions: fetchGateMisconceptions,
    fetchGateAnalysis:     fetchGateAnalysis,
    fetchJAMPractice:      fetchJAMPractice,
    fetchCSIRPractice:     fetchCSIRPractice
};

})();
