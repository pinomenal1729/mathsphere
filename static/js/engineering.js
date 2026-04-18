// ══════════════════════════════════════════════════════════════
//  MATHSPHERE ENGINEERING — engineering.js  (v4.0 Mobile-First)
//  By Anupam Nigam
//  Key changes:
//  - Sidebar is persistent on desktop, drawer on mobile
//  - Hamburger properly controls mobile drawer
//  - Tab bar scrolls to active tab on mobile
//  - Touch-friendly inputs (no iOS zoom)
//  - Gate dashboard fully responsive
//  - All overlapping issues fixed
// ══════════════════════════════════════════════════════════════
(function () {
  'use strict';

  var state = {
    mode: 'general',
    activeTab: 'learn',
    activeSem: null,
    activeTopic: null,
    activeSubtopic: null,
    activeSection: 'definition',
    syllabus: null,
    loading: false,
    gateMode: false,
    gateBranch: null,
    gateActiveTab: 'practice',
    gateTopicKey: null,
    gateSubtopic: null
  };

  var GATE_BRANCHES = {
    cs: { label: 'Computer Science', icon: '💻', color: '#4f9cf7', short: 'CS' },
    ec: { label: 'Electronics & Comm', icon: '📡', color: '#22d3ee', short: 'EC' },
    me: { label: 'Mechanical', icon: '⚙️', color: '#fb923c', short: 'ME' },
    ce: { label: 'Civil', icon: '🏗️', color: '#4ade80', short: 'CE' },
    ee: { label: 'Electrical', icon: '⚡', color: '#fbbf24', short: 'EE' }
  };

  var GATE_TOPICS = {
    linear_algebra:    { label: 'Linear Algebra',          icon: '📐' },
    calculus:          { label: 'Calculus',                 icon: '∫' },
    probability:       { label: 'Probability & Stats',      icon: '🎲' },
    diff_equations:    { label: 'Differential Equations',   icon: '📈' },
    complex_analysis:  { label: 'Complex Analysis',         icon: '🌀' },
    numerical_methods: { label: 'Numerical Methods',        icon: '🔢' },
    transforms:        { label: 'Transforms',               icon: '🔄' }
  };

  var GATE_FORMULA_CATS = {
    linear_algebra_shortcuts: { label: 'Linear Algebra Shortcuts', icon: '📐' },
    calculus_shortcuts:       { label: 'Calculus Shortcuts',        icon: '∫'  },
    probability_shortcuts:    { label: 'Probability Shortcuts',     icon: '🎲' },
    de_shortcuts:             { label: 'DE Shortcuts',              icon: '📈' },
    complex_shortcuts:        { label: 'Complex Shortcuts',         icon: '🌀' }
  };

  // ── DOM READY ────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    injectLanding();
    injectEngApp();
    loadSyllabus();

    var saved = localStorage.getItem('msMode');
    if (saved === 'engineering') activateEngineering();
    else if (saved === 'general') activateGeneral();
    else showLanding();
  });

  // ── LANDING ─────────────────────────────────────────────────
  function injectLanding() {
    var el = document.createElement('div');
    el.id = 'mode-landing';
    el.className = 'hidden';
    el.innerHTML = [
      '<div class="landing-eyebrow">MathSphere Platform</div>',
      '<div class="landing-title-main">Mathematics for <span>Engineers</span></div>',
      '<div class="landing-sub">Choose your learning environment. Switch anytime from the header.</div>',
      '<div class="landing-cards">',
      '  <div class="landing-card landing-card--general" onclick="window.engModule.chooseMode(\'general\')">',
      '    <div class="landing-card-tag">All Levels</div>',
      '    <div class="landing-card-icon-wrap">∑</div>',
      '    <div class="landing-card-title">General Mathematics</div>',
      '    <div class="landing-card-desc">Ask Anupam, Intuition Builder, Story Mode, PYQ Practice, Graph Plotter — Class 11 to research level.</div>',
      '    <div class="landing-card-arrow">Open General Mode →</div>',
      '  </div>',
      '  <div class="landing-card landing-card--engineering" onclick="window.engModule.chooseMode(\'engineering\')">',
      '    <div class="landing-card-tag">B.Tech Sem 1–4</div>',
      '    <div class="landing-card-icon-wrap" style="font-family:var(--e-mono);font-size:16px">∫∇</div>',
      '    <div class="landing-card-title">Engineering Mathematics</div>',
      '    <div class="landing-card-desc">IIT/NIT syllabus. 200+ subtopics. Visual Intuition, PYQs, Formula Booklet, GATE Exam Module.</div>',
      '    <div class="landing-card-arrow">Open Engineering Mode →</div>',
      '  </div>',
      '</div>',
      '<div class="landing-footer">Your choice is saved automatically</div>'
    ].join('');
    document.body.appendChild(el);
  }

  // ── ENG APP SHELL ────────────────────────────────────────────
  function injectEngApp() {
    var el = document.createElement('div');
    el.id = 'eng-app';
    el.innerHTML = buildAppHTML();
    document.body.appendChild(el);

    // Mobile overlay
    var overlay = document.createElement('div');
    overlay.id = 'eng-mobile-overlay';
    overlay.className = 'eng-mobile-overlay';
    overlay.addEventListener('click', closeSidebar);
    document.body.appendChild(overlay);

    // Wire hamburger
    var ham = document.getElementById('eng-hamburger');
    if (ham) ham.addEventListener('click', toggleSidebar);
  }

  function buildAppHTML() {
    return [
      // HEADER
      '<div class="eng-header">',
      '  <button class="eng-hamburger" id="eng-hamburger" aria-label="Menu">',
      '    <span></span><span></span><span></span>',
      '  </button>',
      '  <div class="eng-header-brand">',
      '    <div class="eng-logo-mark">E</div>',
      '    <div>',
      '      <div class="eng-logo-text">MathSphere</div>',
      '      <div class="eng-logo-sub">Engineering</div>',
      '    </div>',
      '  </div>',

      // Tab bar — scrollable
      '  <div class="eng-tabs" id="eng-tabs-bar" role="tablist">',
      '    <button class="eng-tab active" data-tab="learn"         role="tab" onclick="window.engModule.switchTab(\'learn\',this)">Learn</button>',
      '    <button class="eng-tab"        data-tab="revision"      role="tab" onclick="window.engModule.switchTab(\'revision\',this)">Revision</button>',
      '    <button class="eng-tab"        data-tab="formulabook"   role="tab" onclick="window.engModule.switchTab(\'formulabook\',this)">Formulas</button>',
      '    <button class="eng-tab"        data-tab="connections"   role="tab" onclick="window.engModule.switchTab(\'connections\',this)">Connections</button>',
      '    <button class="eng-tab"        data-tab="pyq"           role="tab" onclick="window.engModule.switchTab(\'pyq\',this)">PYQ</button>',
      '    <button class="eng-tab"        data-tab="mocktest"      role="tab" onclick="window.engModule.switchTab(\'mocktest\',this)">Mock Test</button>',
      '    <button class="eng-tab"        data-tab="misconception" role="tab" onclick="window.engModule.switchTab(\'misconception\',this)">Misconceptions</button>',
      '    <button class="eng-tab"        data-tab="ask"           role="tab" onclick="window.engModule.switchTab(\'ask\',this)">Ask AI</button>',
      '    <button class="eng-tab eng-tab--gate" data-tab="gate"   role="tab" onclick="window.engModule.switchTab(\'gate\',this)">🎯 GATE</button>',
      '  </div>',

      '  <div class="eng-header-right">',
      '    <div class="eng-status">LIVE</div>',
      '    <button class="mode-switch-btn" onclick="window.engModule.showLanding()">⇄ Mode</button>',
      '  </div>',
      '</div>',

      // BODY
      '<div class="eng-body">',

      // SIDEBAR
      '  <div class="eng-sidebar" id="eng-sidebar">',
      '    <div class="eng-sem-pills" id="eng-sem-pills">',
      '      <button class="eng-sem-pill" data-sem="sem1" onclick="window.engModule.selectSem(\'sem1\',this)">Sem 1</button>',
      '      <button class="eng-sem-pill" data-sem="sem2" onclick="window.engModule.selectSem(\'sem2\',this)">Sem 2</button>',
      '      <button class="eng-sem-pill" data-sem="sem3" onclick="window.engModule.selectSem(\'sem3\',this)">Sem 3</button>',
      '      <button class="eng-sem-pill" data-sem="sem4" onclick="window.engModule.selectSem(\'sem4\',this)">Sem 4</button>',
      '    </div>',
      '    <div class="eng-topic-list" id="eng-topic-list"></div>',
      '  </div>',

      // CONTENT
      '  <div class="eng-content">',

      // Subtopic chips
      '    <div class="eng-subtopic-bar hidden" id="eng-subtopic-bar" role="group" aria-label="Subtopics"></div>',

      // Section buttons
      '    <div class="eng-section-bar hidden" id="eng-section-bar">',
      '      <button class="eng-sec-btn active" data-sec="definition" onclick="window.engModule.selectSection(\'definition\',this)">Definition</button>',
      '      <button class="eng-sec-btn"        data-sec="intuition"  onclick="window.engModule.selectSection(\'intuition\',this)">Intuition</button>',
      '      <button class="eng-sec-btn"        data-sec="theorem"    onclick="window.engModule.selectSection(\'theorem\',this)">Theorems</button>',
      '      <button class="eng-sec-btn"        data-sec="examples"   onclick="window.engModule.selectSection(\'examples\',this)">Examples</button>',
      '      <button class="eng-sec-btn"        data-sec="practice"   onclick="window.engModule.selectSection(\'practice\',this)">Practice</button>',
      '    </div>',

      // PYQ filters
      '    <div class="eng-filters hidden" id="eng-pyq-filters">',
      '      <span class="eng-filter-label">Uni</span>',
      '      <select class="eng-select" id="eng-univ-select">',
      '        <option value="all">All India</option>',
      '        <option value="mumbai">Mumbai Univ</option>',
      '        <option value="vtu">VTU Bangalore</option>',
      '        <option value="anna">Anna Univ</option>',
      '        <option value="aktu">AKTU</option>',
      '        <option value="abroad">International</option>',
      '      </select>',
      '      <span class="eng-filter-label">Diff</span>',
      '      <select class="eng-select" id="eng-diff-select">',
      '        <option value="easy">Easy</option>',
      '        <option value="medium" selected>Medium</option>',
      '        <option value="hard">Hard</option>',
      '      </select>',
      '      <button class="eng-gen-btn" onclick="window.engModule.fetchPYQ()">Generate PYQs</button>',
      '    </div>',

      // Mock config
      '    <div class="eng-mock-config hidden" id="eng-mock-config">',
      '      <span class="eng-mock-label">Qs</span>',
      '      <select class="eng-select" id="eng-numq-select">',
      '        <option value="5">5 Qs</option>',
      '        <option value="10" selected>10 Qs</option>',
      '        <option value="20">20 Qs</option>',
      '      </select>',
      '      <span class="eng-mock-label">Marks</span>',
      '      <select class="eng-select" id="eng-marks-select">',
      '        <option value="2">2M</option>',
      '        <option value="5" selected>5M</option>',
      '        <option value="10">10M</option>',
      '      </select>',
      '      <button class="eng-gen-btn" onclick="window.engModule.fetchMockTest()">Generate</button>',
      '    </div>',

      // Gate config
      '    <div class="eng-gate-config hidden" id="eng-gate-config"></div>',

      // Output
      '    <div class="eng-output" id="eng-output">',
      '      ' + buildWelcomeHTML('∇', 'Engineering Mathematics', 'Select a semester → topic → subtopic to begin. Use the tabs above for different modes.'),
      '    </div>',

      // Ask AI area
      '    <div class="eng-ask-area hidden" id="eng-ask-area">',
      '      <div class="eng-input-box">',
      '        <textarea id="eng-ask-input" rows="1" placeholder="Ask any engineering maths question…"',
      '          oninput="this.style.height=\'auto\';this.style.height=Math.min(this.scrollHeight,120)+\'px\'"',
      '          onkeydown="if(event.key===\'Enter\'&&!event.shiftKey){event.preventDefault();window.engModule.askAI()}"></textarea>',
      '        <button class="eng-send" onclick="window.engModule.askAI()" aria-label="Send">',
      '          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
      '        </button>',
      '      </div>',
      '    </div>',

      '  </div>',  // /eng-content
      '</div>'    // /eng-body
    ].join('');
  }

  // ── SIDEBAR TOGGLE (MOBILE) ──────────────────────────────────
  function toggleSidebar() {
    var sidebar  = document.getElementById('eng-sidebar');
    var overlay  = document.getElementById('eng-mobile-overlay');
    var ham      = document.getElementById('eng-hamburger');
    if (!sidebar) return;

    // On desktop sidebar is always open — ignore toggle
    if (window.innerWidth >= 768) return;

    var isOpen = sidebar.classList.contains('mobile-open');
    if (isOpen) {
      closeSidebar();
    } else {
      sidebar.classList.add('mobile-open');
      if (overlay) overlay.classList.add('visible');
      if (ham)     ham.classList.add('open');
      document.body.style.overflow = 'hidden'; // prevent body scroll
    }
  }

  function closeSidebar() {
    var sidebar = document.getElementById('eng-sidebar');
    var overlay = document.getElementById('eng-mobile-overlay');
    var ham     = document.getElementById('eng-hamburger');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('visible');
    if (ham)     ham.classList.remove('open');
    document.body.style.overflow = '';
  }

  // Scroll active tab into view on mobile
  function scrollTabIntoView(btn) {
    if (!btn) return;
    var bar = document.getElementById('eng-tabs-bar');
    if (!bar) return;
    // Smooth scroll the tab strip so active tab is centered
    var btnRect = btn.getBoundingClientRect();
    var barRect = bar.getBoundingClientRect();
    var offset  = btnRect.left - barRect.left - (barRect.width / 2) + (btnRect.width / 2);
    bar.scrollBy({ left: offset, behavior: 'smooth' });
  }

  // ── SYLLABUS ─────────────────────────────────────────────────
  function loadSyllabus() {
    fetch('/eng/syllabus')
      .then(function (r) { return r.json(); })
      .then(function (d) { state.syllabus = d; })
      .catch(function (e) { console.warn('Syllabus load failed', e); });
  }

  // ── MODE SWITCHING ───────────────────────────────────────────
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
    btn.onclick = function () { window.engModule.showLanding(); };
    right.insertBefore(btn, right.firstChild);
  }

  // ── TAB SWITCHING ────────────────────────────────────────────
  function switchTab(tab, btn) {
    state.activeTab = tab;

    document.querySelectorAll('.eng-tab').forEach(function (b) { b.classList.remove('active'); });
    if (btn) {
      btn.classList.add('active');
      scrollTabIntoView(btn);
    }

    // Reset gate mode
    if (tab !== 'gate') {
      state.gateMode = false;
      toggleEl('eng-gate-config', false);
      var sidebar = document.getElementById('eng-sidebar');
      if (sidebar) sidebar.classList.remove('gate-sidebar-mode');
      // Restore normal sem pills
      restoreNormalSemPills();
    }

    // Hide all bars first
    toggleEl('eng-section-bar',  false);
    toggleEl('eng-pyq-filters',  false);
    toggleEl('eng-mock-config',  false);
    toggleEl('eng-gate-config',  false);
    toggleEl('eng-ask-area',     false);
    toggleEl('eng-subtopic-bar', tab !== 'ask' && tab !== 'misconception' && tab !== 'gate' && !!state.activeTopic);

    if (tab === 'gate') {
      state.gateMode = true;
      showGateDashboard();
      return;
    }

    if (tab === 'ask') {
      toggleEl('eng-ask-area', true);
      setOutput(buildWelcomeHTML('?', 'Ask Engineering AI', 'Ask any B.Tech mathematics question.'));
      return;
    }

    if (tab === 'misconception') {
      if (state.activeTopic) fetchMisconceptions();
      else setOutput(buildWelcomeHTML('⚠', 'Misconception Detector', 'Select a semester and topic from the left panel.'));
      return;
    }

    if (tab === 'connections') {
      if (state.activeTopic) fetchConnections();
      else setOutput(buildWelcomeHTML('↔', 'Subject Connections Map', 'Select a topic to see where this maths powers your engineering subjects.'));
      return;
    }

    if (tab === 'formulabook') {
      if (state.activeSubtopic) fetchFormulaBooklet();
      else setOutput(buildWelcomeHTML('ℱ', 'Formula Booklet', 'Select a subtopic to generate a complete formula reference.'));
      return;
    }

    if (!state.activeSubtopic && !state.activeTopic) {
      setOutput(buildWelcomeHTML('∇', 'Engineering Mathematics', 'Select a semester → topic → subtopic to begin.'));
      return;
    }

    if (state.activeSubtopic) {
      if (tab === 'learn')     { toggleEl('eng-section-bar', true); fetchContent('learn'); }
      if (tab === 'revision')  fetchContent('revision');
      if (tab === 'pyq')       { toggleEl('eng-pyq-filters', true); fetchPYQ(); }
      if (tab === 'mocktest')  toggleEl('eng-mock-config', true);
    }
  }

  // ── WELCOME HTML ─────────────────────────────────────────────
  function buildWelcomeHTML(symbol, title, sub) {
    return [
      '<div class="eng-welcome">',
      '  <div class="eng-welcome-symbol">' + symbol + '</div>',
      '  <div class="eng-welcome-title">' + title + '</div>',
      '  <div class="eng-welcome-sub">' + sub + '</div>',
      '</div>'
    ].join('');
  }

  // ── NORMAL SEM PILLS ─────────────────────────────────────────
  function restoreNormalSemPills() {
    var pills = document.getElementById('eng-sem-pills');
    if (!pills) return;
    // Only restore if currently in gate mode pills
    if (!pills.querySelector('.gate-back-pill')) return;
    pills.innerHTML = [
      '<button class="eng-sem-pill' + (state.activeSem === 'sem1' ? ' active' : '') + '" data-sem="sem1" onclick="window.engModule.selectSem(\'sem1\',this)">Sem 1</button>',
      '<button class="eng-sem-pill' + (state.activeSem === 'sem2' ? ' active' : '') + '" data-sem="sem2" onclick="window.engModule.selectSem(\'sem2\',this)">Sem 2</button>',
      '<button class="eng-sem-pill' + (state.activeSem === 'sem3' ? ' active' : '') + '" data-sem="sem3" onclick="window.engModule.selectSem(\'sem3\',this)">Sem 3</button>',
      '<button class="eng-sem-pill' + (state.activeSem === 'sem4' ? ' active' : '') + '" data-sem="sem4" onclick="window.engModule.selectSem(\'sem4\',this)">Sem 4</button>'
    ].join('');
    // Restore topic list
    if (state.activeSem) renderTopicList(state.activeSem);
  }

  // ── GATE MODULE ──────────────────────────────────────────────
  function showGateDashboard() {
    var sidebar = document.getElementById('eng-sidebar');
    if (sidebar) sidebar.classList.add('gate-sidebar-mode');
    renderGateSidebar();
    if (!state.gateBranch) renderGateBranchSelection();
    else renderGateMainPanel();
  }

  function renderGateSidebar() {
    var semPills  = document.getElementById('eng-sem-pills');
    var topicList = document.getElementById('eng-topic-list');
    if (semPills) {
      semPills.innerHTML = [
        '<button class="eng-sem-pill gate-back-pill" onclick="window.engModule.gateBackToBranches()">← Branches</button>',
        '<button class="eng-sem-pill gate-exam-pill active">🎯 GATE</button>'
      ].join('');
    }
    if (topicList) {
      var tabs = [
        { key: 'practice',        label: 'Practice Questions', icon: '✍' },
        { key: 'mock',            label: 'Mock Test',           icon: '📝' },
        { key: 'strategy',        label: 'Prep Strategy',       icon: '📈' },
        { key: 'formulas',        label: 'Quick Formulas',      icon: '⚡' },
        { key: 'misconceptions',  label: 'Trap Questions',      icon: '⚠' },
        { key: 'syllabus',        label: 'Branch Syllabus',     icon: '📚' },
        { key: 'analysis',        label: 'Topic Analysis',      icon: '🔍' }
      ];
      var html = '';
      tabs.forEach(function (t, i) {
        var active = state.gateActiveTab === t.key;
        html += '<div class="eng-topic-group">';
        html += '<button class="eng-topic-btn' + (active ? ' active' : '') + '"';
        html += ' data-gate-tab="' + t.key + '"';
        html += ' style="animation:e-in .25s var(--e-ease) ' + (i * .04) + 's both"';
        html += ' onclick="window.engModule.switchGateTab(\'' + t.key + '\')">';
        html += '<span style="font-size:14px">' + t.icon + '</span> ' + t.label;
        html += '</button></div>';
      });
      topicList.innerHTML = html;
    }
  }

  function renderGateBranchSelection() {
    var html = '<div class="gate-dashboard">';
    html += '<div class="gate-hero">';
    html += '<div class="gate-hero-badge">COMPETITIVE EXAM PREPARATION</div>';
    html += '<div class="gate-hero-title">GATE Exam <span class="gate-hero-accent">Module</span></div>';
    html += '<div class="gate-hero-sub">MCQ · NAT · MSQ practice. Mock tests. AI-powered strategies. Shortcut formulas. GATE traps exposed.</div>';
    html += '</div>';

    html += '<div class="gate-branch-grid">';
    Object.keys(GATE_BRANCHES).forEach(function (key) {
      var b = GATE_BRANCHES[key];
      html += '<div class="gate-branch-card" style="--branch-color:' + b.color + '" onclick="window.engModule.selectGateBranch(\'' + key + '\')">';
      html += '<div class="gate-branch-icon">' + b.icon + '</div>';
      html += '<div class="gate-branch-short">' + b.short + '</div>';
      html += '<div class="gate-branch-label">' + b.label + '</div>';
      html += '<div class="gate-branch-arrow">Select →</div>';
      html += '</div>';
    });
    html += '</div>';

    html += '<div class="gate-info-strip">';
    html += '<div class="gate-info-item"><span class="gate-info-num">5</span><span class="gate-info-label">Branches</span></div>';
    html += '<div class="gate-info-item"><span class="gate-info-num">7</span><span class="gate-info-label">Topics</span></div>';
    html += '<div class="gate-info-item"><span class="gate-info-num">50+</span><span class="gate-info-label">Formulas</span></div>';
    html += '<div class="gate-info-item"><span class="gate-info-num">20+</span><span class="gate-info-label">Traps</span></div>';
    html += '</div>';
    html += '</div>';
    setOutput(html);
  }

  function selectGateBranch(branch) {
    state.gateBranch = branch;
    renderGateSidebar();
    renderGateMainPanel();
  }

  function gateBackToBranches() {
    state.gateBranch = null;
    state.gateActiveTab = 'practice';
    renderGateSidebar();
    renderGateBranchSelection();
  }

  function switchGateTab(tab) {
    state.gateActiveTab = tab;
    document.querySelectorAll('[data-gate-tab]').forEach(function (btn) {
      btn.classList.toggle('active', btn.getAttribute('data-gate-tab') === tab);
    });
    renderGateMainPanel();
  }

  function renderGateMainPanel() {
    var branch = state.gateBranch;
    var tab    = state.gateActiveTab;
    var bLabel = branch ? GATE_BRANCHES[branch].label + ' (' + GATE_BRANCHES[branch].short + ')' : '';

    switch (tab) {
      case 'practice':       renderGatePractice(branch, bLabel);      break;
      case 'mock':           renderGateMock(branch, bLabel);           break;
      case 'strategy':       renderGateStrategy(branch, bLabel);       break;
      case 'formulas':       renderGateFormulas();                      break;
      case 'misconceptions': renderGateMisconceptions();                break;
      case 'syllabus':       renderGateSyllabusPanel(branch, bLabel); break;
      case 'analysis':       renderGateAnalysis();                      break;
      default:               renderGatePractice(branch, bLabel);
    }
  }

  // ── GATE PRACTICE ────────────────────────────────────────────
  function renderGatePractice(branch, branchLabel) {
    if (!branch) { renderGateBranchSelection(); return; }
    var b    = GATE_BRANCHES[branch];
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header">';
    html += '<div class="gate-panel-badge" style="--badge-color:' + b.color + '">' + b.icon + ' GATE ' + b.short + '</div>';
    html += '<div class="gate-panel-title">Practice Questions</div>';
    html += '<div class="gate-panel-sub">GATE-style MCQ, NAT & MSQ with full solutions</div>';
    html += '</div>';

    html += '<div class="gate-form-section"><div class="gate-form-label">Select Topic</div>';
    html += '<div class="gate-topic-chips" id="gate-practice-topics">';
    Object.keys(GATE_TOPICS).forEach(function (key) {
      var t = GATE_TOPICS[key];
      html += '<button class="gate-topic-chip' + (state.gateTopicKey === key ? ' active' : '') + '" onclick="window.engModule.selectGateTopic(\'' + key + '\')" data-topic="' + key + '">';
      html += '<span>' + t.icon + '</span> ' + t.label + '</button>';
    });
    html += '</div></div>';

    html += '<div class="gate-form-section"><div class="gate-form-label">Specific Subtopic</div>';
    html += '<input type="text" class="gate-input" id="gate-subtopic-input" placeholder="e.g. Eigenvalues, Cauchy-Riemann, Newton-Raphson…" value="' + (state.gateSubtopic || '') + '"></div>';

    html += '<div class="gate-form-row">';
    html += '<div class="gate-form-section gate-form-half"><div class="gate-form-label">Question Type</div>';
    html += '<select class="eng-select gate-select" id="gate-qtype-select">';
    html += '<option value="MCQ">MCQ</option><option value="NAT">NAT</option><option value="MSQ">MSQ</option></select></div>';
    html += '<div class="gate-form-section gate-form-half"><div class="gate-form-label">Difficulty</div>';
    html += '<select class="eng-select gate-select" id="gate-diff-select">';
    html += '<option value="easy">Easy (1 mark)</option><option value="medium" selected>Medium (2 marks)</option><option value="hard">Hard (tricky)</option></select></div>';
    html += '</div>';

    html += '<button class="gate-action-btn gate-action-primary" onclick="window.engModule.fetchGatePractice()">✍ Generate Practice Question</button>';
    html += '<div id="gate-practice-result"></div></div>';
    setOutput(html);
  }

  function selectGateTopic(key) {
    state.gateTopicKey = key;
    document.querySelectorAll('.gate-topic-chip').forEach(function (c) {
      c.classList.toggle('active', c.getAttribute('data-topic') === key);
    });
  }

  function fetchGatePractice() {
    var subtopicEl = document.getElementById('gate-subtopic-input');
    var subtopic   = subtopicEl ? subtopicEl.value.trim() : '';
    if (!subtopic && !state.gateTopicKey) { alert('Please select a topic or enter a subtopic'); return; }
    if (!subtopic) subtopic = GATE_TOPICS[state.gateTopicKey].label;

    var qtype = document.getElementById('gate-qtype-select').value;
    var diff  = document.getElementById('gate-diff-select').value;
    var result = document.getElementById('gate-practice-result');
    if (result) result.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Generating ' + qtype + ' on ' + subtopic + '…</span></div>';

    postToAPI('/eng/gate/practice', { subtopic: subtopic, branch: state.gateBranch, difficulty: diff, question_type: qtype }, function (data) {
      if (result) {
        result.innerHTML = '<div class="eng-response gate-response">' + renderContent(data.response || JSON.stringify(data)) + '</div>';
        typesetOutput();
      }
    });
  }

  // ── GATE MOCK ────────────────────────────────────────────────
  function renderGateMock(branch, bLabel) {
    if (!branch) { renderGateBranchSelection(); return; }
    var b    = GATE_BRANCHES[branch];
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header"><div class="gate-panel-badge" style="--badge-color:' + b.color + '">' + b.icon + ' GATE ' + b.short + '</div>';
    html += '<div class="gate-panel-title">Mock Test</div><div class="gate-panel-sub">Simulated GATE exam conditions</div></div>';
    html += '<div class="gate-form-row">';
    html += '<div class="gate-form-section gate-form-half"><div class="gate-form-label">Questions</div>';
    html += '<select class="eng-select gate-select" id="gate-mock-numq"><option value="5">5 (Quick)</option><option value="10" selected>10 (Standard)</option><option value="15">15</option><option value="25">25 (Full)</option></select></div>';
    html += '<div class="gate-form-section gate-form-half"><div class="gate-form-label">Time (min)</div>';
    html += '<select class="eng-select gate-select" id="gate-mock-time"><option value="15">15</option><option value="30" selected>30</option><option value="45">45</option><option value="60">60</option></select></div>';
    html += '</div>';
    html += '<button class="gate-action-btn gate-action-primary" onclick="window.engModule.fetchGateMock()">📝 Generate Mock Test</button>';
    html += '<div id="gate-mock-result"></div></div>';
    setOutput(html);
  }

  function fetchGateMock() {
    var numQ   = document.getElementById('gate-mock-numq').value;
    var time   = document.getElementById('gate-mock-time').value;
    var result = document.getElementById('gate-mock-result');
    if (result) result.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Generating ' + numQ + '-question mock test…</span></div>';
    postToAPI('/eng/gate/mock', { branch: state.gateBranch, num_questions: parseInt(numQ), time_minutes: parseInt(time) }, function (data) {
      if (result) { result.innerHTML = '<div class="eng-response gate-response">' + renderContent(data.response || JSON.stringify(data)) + '</div>'; typesetOutput(); }
    });
  }

  // ── GATE STRATEGY ────────────────────────────────────────────
  function renderGateStrategy(branch, bLabel) {
    if (!branch) { renderGateBranchSelection(); return; }
    var b    = GATE_BRANCHES[branch];
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header"><div class="gate-panel-badge" style="--badge-color:' + b.color + '">' + b.icon + ' GATE ' + b.short + '</div>';
    html += '<div class="gate-panel-title">Prep Strategy</div><div class="gate-panel-sub">AI-generated personalized preparation plan</div></div>';
    html += '<div class="gate-form-section"><div class="gate-form-label">Months until GATE</div>';
    html += '<select class="eng-select gate-select" id="gate-strategy-months" style="max-width:none;width:100%">';
    html += '<option value="1">1 Month (Crash)</option><option value="2">2 Months</option><option value="3" selected>3 Months</option><option value="6">6 Months</option><option value="12">12 Months</option></select></div>';
    html += '<button class="gate-action-btn gate-action-primary" onclick="window.engModule.fetchGateStrategy()">📈 Generate My Strategy</button>';
    html += '<div id="gate-strategy-result"></div></div>';
    setOutput(html);
  }

  function fetchGateStrategy() {
    var months = document.getElementById('gate-strategy-months').value;
    var result = document.getElementById('gate-strategy-result');
    if (result) result.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Crafting your ' + months + '-month strategy…</span></div>';
    postToAPI('/eng/gate/strategy', { branch: state.gateBranch, months: parseInt(months) }, function (data) {
      if (result) { result.innerHTML = '<div class="eng-response gate-response">' + renderContent(data.response || JSON.stringify(data)) + '</div>'; typesetOutput(); }
    });
  }

  // ── GATE FORMULAS ────────────────────────────────────────────
  function renderGateFormulas() {
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header"><div class="gate-panel-badge" style="--badge-color:#fbbf24">⚡ Shortcuts</div>';
    html += '<div class="gate-panel-title">Quick Formulas & Shortcuts</div><div class="gate-panel-sub">50+ shortcut formulas for instant GATE answers</div></div>';
    html += '<div class="gate-formula-grid">';
    Object.keys(GATE_FORMULA_CATS).forEach(function (key) {
      var cat = GATE_FORMULA_CATS[key];
      html += '<div class="gate-formula-card" onclick="window.engModule.fetchGateFormulas(\'' + key + '\')">';
      html += '<div class="gate-formula-icon">' + cat.icon + '</div>';
      html += '<div class="gate-formula-label">' + cat.label + '</div>';
      html += '<div class="gate-formula-arrow">View →</div></div>';
    });
    html += '</div><div id="gate-formula-result"></div></div>';
    setOutput(html);
  }

  function fetchGateFormulas(category) {
    var result = document.getElementById('gate-formula-result');
    if (result) result.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Loading…</span></div>';
    postToAPI('/eng/gate/formulas', { category: category }, function (data) {
      if (result) {
        if (data.formulas && Array.isArray(data.formulas)) {
          var html = '<div style="margin-top:16px">';
          data.formulas.forEach(function (f, i) {
            html += '<div class="eng-card" style="animation-delay:' + (i * .05) + 's">';
            html += '<div class="eng-card-header" style="background:rgba(251,191,36,.05);border-left:3px solid #fbbf24">';
            html += '<div style="flex:1;font-size:13px;font-weight:700;color:var(--e-t1)">' + (f.name || 'Formula ' + (i + 1)) + '</div></div>';
            html += '<div class="eng-card-body">';
            if (f.formula) html += '<div style="font-family:var(--e-mono);font-size:13px;color:var(--e-cyan);padding:10px;background:var(--e-bg3);border-radius:8px;border:1px solid var(--e-border);margin-bottom:8px">' + f.formula + '</div>';
            if (f.condition) html += '<div style="font-size:12px;color:var(--e-t2)"><strong style="color:var(--e-amber)">When:</strong> ' + f.condition + '</div>';
            html += '</div></div>';
          });
          result.innerHTML = html + '</div>';
        } else {
          result.innerHTML = '<div class="eng-response gate-response">' + renderContent(data.response || JSON.stringify(data)) + '</div>';
        }
        typesetOutput();
      }
    });
  }

  // ── GATE MISCONCEPTIONS ──────────────────────────────────────
  function renderGateMisconceptions() {
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header"><div class="gate-panel-badge" style="--badge-color:#f87171">⚠ Traps</div>';
    html += '<div class="gate-panel-title">Common Traps & Misconceptions</div><div class="gate-panel-sub">20+ traps GATE loves — understand them before the exam</div></div>';
    html += '<div class="gate-form-section"><div class="gate-form-label">Select Topic</div>';
    html += '<div class="gate-topic-chips">';
    Object.keys(GATE_TOPICS).forEach(function (key) {
      var t = GATE_TOPICS[key];
      html += '<button class="gate-topic-chip" onclick="window.engModule.fetchGateMisconceptions(\'' + key + '\')" data-topic="' + key + '">';
      html += '<span>' + t.icon + '</span> ' + t.label + '</button>';
    });
    html += '</div></div><div id="gate-misconception-result"></div></div>';
    setOutput(html);
  }

  function fetchGateMisconceptions(topic) {
    var result = document.getElementById('gate-misconception-result');
    if (result) result.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Loading traps…</span></div>';
    postToAPI('/eng/gate/misconceptions', { topic: topic }, function (data) {
      if (result) {
        if (data.misconceptions && Array.isArray(data.misconceptions)) {
          var html = '<div style="margin-top:16px">';
          data.misconceptions.forEach(function (m, i) {
            var d = m.danger || 'HIGH';
            var col = d === 'CRITICAL' ? '#dc2626' : d === 'HIGH' ? '#ef4444' : '#f59e0b';
            html += '<div class="eng-card" style="animation-delay:' + (i * .06) + 's">';
            html += '<div class="eng-card-header" style="background:rgba(239,68,68,.06);border-left:3px solid ' + col + '">';
            html += '<div style="flex:1;font-size:13px;font-weight:700;color:var(--e-t1)">' + (m.misconception || 'Trap ' + (i + 1)) + '</div>';
            html += '<div class="eng-card-tag" style="background:rgba(239,68,68,.08);color:' + col + ';border:1px solid rgba(239,68,68,.2)">' + d + '</div></div>';
            html += '<div class="eng-card-body">';
            if (m.truth) html += '<div style="font-size:12.5px;color:#4ade80;margin-bottom:8px"><strong>Truth:</strong> ' + m.truth + '</div>';
            if (m.trap_question) html += '<div style="font-size:12.5px;color:var(--e-t2);padding:10px;background:var(--e-bg3);border-radius:8px;border:1px solid var(--e-border)"><strong style="color:var(--e-amber)">Trap Q:</strong> ' + m.trap_question + '</div>';
            html += '</div></div>';
          });
          result.innerHTML = html + '</div>';
        } else {
          result.innerHTML = '<div class="eng-response">' + renderContent(data.response || JSON.stringify(data)) + '</div>';
        }
        typesetOutput();
      }
    });
  }

  // ── GATE SYLLABUS PANEL ──────────────────────────────────────
  function renderGateSyllabusPanel(branch, bLabel) {
    if (!branch) { renderGateBranchSelection(); return; }
    var b    = GATE_BRANCHES[branch];
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header"><div class="gate-panel-badge" style="--badge-color:' + b.color + '">' + b.icon + ' GATE ' + b.short + '</div>';
    html += '<div class="gate-panel-title">Branch Syllabus</div><div class="gate-panel-sub">' + bLabel + ' mathematics syllabus & weightage</div></div>';
    html += '<div id="gate-syllabus-result"><div class="eng-loading"><div class="eng-spinner"></div><span>Loading syllabus…</span></div></div></div>';
    setOutput(html);
    postToAPI('/eng/gate/syllabus', { branch: branch }, function (data) {
      var result = document.getElementById('gate-syllabus-result');
      if (result) {
        if (data.specific_syllabus && Array.isArray(data.specific_syllabus)) {
          var s = '<div class="eng-response" style="margin-top:0"><ul>';
          data.specific_syllabus.forEach(function (item) { s += '<li>' + item + '</li>'; });
          result.innerHTML = s + '</ul></div>';
        } else {
          result.innerHTML = '<div class="eng-response">' + renderContent(data.response || JSON.stringify(data)) + '</div>';
        }
        typesetOutput();
      }
    });
  }

  // ── GATE ANALYSIS ────────────────────────────────────────────
  function renderGateAnalysis() {
    var html = '<div class="gate-panel">';
    html += '<div class="gate-panel-header"><div class="gate-panel-badge" style="--badge-color:#a78bfa">🔍 Analysis</div>';
    html += '<div class="gate-panel-title">Topic-wise GATE Analysis</div><div class="gate-panel-sub">Frequency, traps, time strategy, scoring patterns</div></div>';
    html += '<div class="gate-form-section"><div class="gate-form-label">Select Topic</div>';
    html += '<div class="gate-topic-chips">';
    Object.keys(GATE_TOPICS).forEach(function (key) {
      var t = GATE_TOPICS[key];
      html += '<button class="gate-topic-chip" onclick="window.engModule.fetchGateAnalysis(\'' + key + '\')" data-topic="' + key + '">';
      html += '<span>' + t.icon + '</span> ' + t.label + '</button>';
    });
    html += '</div></div><div id="gate-analysis-result"></div></div>';
    setOutput(html);
  }

  function fetchGateAnalysis(topic) {
    var result = document.getElementById('gate-analysis-result');
    if (result) result.innerHTML = '<div class="eng-loading"><div class="eng-spinner"></div><span>Analysing ' + GATE_TOPICS[topic].label + '…</span></div>';
    postToAPI('/eng/gate/analysis', { topic: topic }, function (data) {
      if (result) {
        result.innerHTML = '<div class="eng-response gate-response">' + renderContent(data.response || (data.analysis ? JSON.stringify(data.analysis) : JSON.stringify(data))) + '</div>';
        typesetOutput();
      }
    });
  }

  // ── MISCONCEPTION MODULE (University) ────────────────────────
  function fetchMisconceptions() {
    if (!state.activeTopic) return;
    showLoading('Loading misconception questions…');
    postToAPI('/eng/misconceptions', { topic: state.activeTopic }, function (data) {
      if (data.questions && data.questions.length) renderMisconceptionQuestions(data.questions);
      else setOutput(buildWelcomeHTML('⚠', 'No questions yet', 'Try another topic.'));
    });
  }

  function renderMisconceptionQuestions(questions) {
    var html = '<div style="padding:4px 0">';
    html += '<div style="margin-bottom:20px">';
    html += '<div style="font-family:var(--e-mono);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#ef4444;margin-bottom:5px">⚠ Misconception Detector</div>';
    html += '<div style="font-size:19px;font-weight:800;color:var(--e-t1);letter-spacing:-.4px">' + getTopicLabel(state.activeTopic) + '</div>';
    html += '<div style="font-size:12.5px;color:var(--e-t3);margin-top:6px;line-height:1.7">Answer each question honestly. The AI will diagnose your thinking.</div></div>';

    questions.forEach(function (q, i) {
      html += '<div class="eng-card" style="animation-delay:' + (i * .07) + 's" id="mc-card-' + q.id + '">';
      html += '<div class="eng-card-header" style="background:rgba(239,68,68,.06);border-left:3px solid #ef4444">';
      html += '<div style="flex:1;font-size:13px;font-weight:700;color:var(--e-t1)">Q' + (i + 1) + '</div>';
      html += '<div class="eng-card-tag" style="background:rgba(239,68,68,.08);color:#ef4444;border:1px solid rgba(239,68,68,.2)">' + q.danger + ' risk</div></div>';
      html += '<div class="eng-card-body">';
      html += '<div style="font-size:13.5px;color:var(--e-t1);line-height:1.8;margin-bottom:12px">' + q.question + '</div>';
      html += '<textarea id="mc-answer-' + q.id + '" placeholder="Write your answer here…" style="width:100%;min-height:80px;background:var(--e-bg3);border:1px solid var(--e-border2);border-radius:10px;padding:10px 12px;color:var(--e-t1);font-size:14px;font-family:var(--e-sans);resize:vertical;outline:none;line-height:1.6;transition:border-color 200ms"></textarea>';
      html += '<button onclick="window.engModule.submitMisconception(\'' + q.id + '\')" style="margin-top:10px;padding:8px 18px;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.25);color:#ef4444;border-radius:8px;font-size:12px;font-weight:700;font-family:var(--e-sans);cursor:pointer;min-height:40px">Diagnose My Thinking</button>';
      html += '<div id="mc-result-' + q.id + '" style="margin-top:12px"></div>';
      html += '</div></div>';
    });
    setOutput(html + '</div>');
  }

  function submitMisconception(questionId) {
    var ta     = document.getElementById('mc-answer-' + questionId);
    var result = document.getElementById('mc-result-' + questionId);
    if (!ta) return;
    var answer = ta.value.trim();
    if (!answer) { ta.style.borderColor = '#ef4444'; return; }
    if (result) result.innerHTML = '<div style="display:flex;align-items:center;gap:10px;color:var(--e-t3);font-size:12px;font-family:var(--e-mono);padding:8px 0"><div class="eng-spinner"></div>Analysing…</div>';
    postToAPI('/eng/diagnose', { topic: state.activeTopic, question_id: questionId, answer: answer }, function (data) {
      if (result) {
        result.innerHTML = '<div style="background:var(--e-bg3);border:1px solid rgba(239,68,68,.15);border-left:3px solid #ef4444;border-radius:0 10px 10px 0;padding:14px 16px;font-size:13px;line-height:1.85;color:var(--e-t2)">' + renderContent(data.response) + '</div>';
        typesetOutput();
      }
    });
  }

  // ── NAVIGATION ───────────────────────────────────────────────
  function selectSem(sem, btn) {
    if (state.gateMode) return; // ignore in gate mode
    state.activeSem      = sem;
    state.activeTopic    = null;
    state.activeSubtopic = null;
    document.querySelectorAll('.eng-sem-pill').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    renderTopicList(sem);
    clearSubtopics();
    clearBars();
    var label = (state.syllabus && state.syllabus[sem]) ? state.syllabus[sem].label : sem;
    setOutput(buildWelcomeHTML('∫', label, 'Select a topic from the left panel.'));
    closeSidebar(); // auto-close on mobile after picking semester
  }

  function renderTopicList(sem) {
    var list = document.getElementById('eng-topic-list');
    if (!list || !state.syllabus || !state.syllabus[sem]) { if (list) list.innerHTML = ''; return; }
    var topics = state.syllabus[sem].topics;
    list.innerHTML = '';
    var idx = 0;
    Object.keys(topics).forEach(function (key) {
      var t   = topics[key];
      var btn = document.createElement('button');
      btn.className = 'eng-topic-btn' + (state.activeTopic === key ? ' active' : '');
      btn.setAttribute('data-topic', key);
      btn.textContent = t.label;
      btn.style.animation = 'e-in .25s var(--e-ease) ' + (idx * .04) + 's both';
      btn.addEventListener('click', function () { selectTopic(key, btn); });
      var g = document.createElement('div');
      g.className = 'eng-topic-group';
      g.appendChild(btn);
      list.appendChild(g);
      idx++;
    });
  }

  function selectTopic(topicKey, btn) {
    state.activeTopic    = topicKey;
    state.activeSubtopic = null;
    document.querySelectorAll('.eng-topic-btn').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    renderSubtopics(topicKey);
    clearBars();
    closeSidebar(); // auto-close drawer on mobile

    if (state.activeTab === 'misconception') { fetchMisconceptions(); return; }
    if (state.activeTab === 'connections')   { fetchConnections();    return; }
    setOutput(buildWelcomeHTML('{ }', btn.textContent, 'Select a subtopic above.'));
  }

  function renderSubtopics(topicKey) {
    var bar = document.getElementById('eng-subtopic-bar');
    if (!bar || !state.syllabus || !state.activeSem) { if (bar) bar.classList.add('hidden'); return; }
    var sem = state.syllabus[state.activeSem];
    if (!sem || !sem.topics[topicKey]) { bar.classList.add('hidden'); return; }
    if (state.activeTab === 'connections') { bar.classList.add('hidden'); return; }

    var subs = sem.topics[topicKey].subtopics;
    bar.innerHTML = '';
    subs.forEach(function (s, i) {
      var btn = document.createElement('button');
      btn.className = 'eng-chip';
      btn.setAttribute('data-sub', s);
      btn.textContent = s;
      btn.style.animation = 'e-in .2s var(--e-ease) ' + (i * .025) + 's both';
      btn.addEventListener('click', function () { selectSubtopic(s, btn); });
      bar.appendChild(btn);
    });
    bar.classList.remove('hidden');
  }

  function selectSubtopic(sub, btn) {
    state.activeSubtopic = sub;
    document.querySelectorAll('.eng-chip').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');

    clearBars();

    var tab = state.activeTab;
    if (tab === 'learn') {
      toggleEl('eng-section-bar', true);
      document.querySelectorAll('.eng-sec-btn').forEach(function (b) { b.classList.remove('active'); });
      document.querySelector('.eng-sec-btn[data-sec="definition"]').classList.add('active');
      state.activeSection = 'definition';
      fetchContent('learn');
    } else if (tab === 'revision')   { fetchContent('revision');   }
    else if (tab === 'formulabook')  { fetchFormulaBooklet();      }
    else if (tab === 'connections')  { fetchConnections();         }
    else if (tab === 'pyq')          { toggleEl('eng-pyq-filters', true); fetchPYQ(); }
    else if (tab === 'mocktest')     { toggleEl('eng-mock-config', true); }
    toggleEl('eng-ask-area', tab === 'ask');
  }

  function selectSection(sec, btn) {
    state.activeSection = sec;
    document.querySelectorAll('.eng-sec-btn').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active');
    if (state.activeSubtopic) fetchContent('learn');
  }

  // ── API CALLS ────────────────────────────────────────────────
  function fetchContent(mode) {
    if (!state.activeSubtopic) return;
    showLoading('Loading ' + (mode === 'learn' ? state.activeSection : 'revision') + ' for ' + state.activeSubtopic + '…');
    var payload = { topic: state.activeTopic, subtopic: state.activeSubtopic };
    if (mode === 'learn') payload.section = state.activeSection;
    var endpoint = mode === 'learn' ? '/eng/learn' : '/eng/revision';
    postToAPI(endpoint, payload, function (data) {
      renderResponse(data.response, data.source, data.references || [], data.prerequisites || []);
    });
  }

  function fetchFormulaBooklet() {
    if (!state.activeSubtopic) return;
    showLoading('Generating formula booklet…');
    postToAPI('/eng/formulabooklet', { topic: state.activeTopic, subtopic: state.activeSubtopic }, function (data) {
      renderResponse(data.response, data.source, data.references || []);
    });
  }

  function fetchConnections() {
    var display = state.activeSubtopic || (state.activeTopic ? getTopicLabel(state.activeTopic) : '');
    if (!state.activeTopic) return;
    showLoading('Mapping subject connections…');
    postToAPI('/eng/connections', { topic: state.activeTopic, subtopic: state.activeSubtopic || display }, function (data) {
      if (data.connections) renderConnectionsCard(data.connections, display, data.references || []);
      else renderResponse(data.response, data.source, data.references || []);
    });
  }

  function getTopicLabel(topicKey) {
    if (!state.syllabus || !state.activeSem) return topicKey;
    var sem = state.syllabus[state.activeSem];
    return (sem && sem.topics[topicKey]) ? sem.topics[topicKey].label : topicKey;
  }

  function renderConnectionsCard(connections, topicLabel, refs) {
    var palettes = [
      '#4f9cf7','#4ade80','#fbbf24','#f87171','#a78bfa','#22d3ee'
    ];
    var html = '<div>';
    html += '<div style="margin-bottom:20px"><div style="font-family:var(--e-mono);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:#22d3ee;margin-bottom:5px">↔ Subject Connections</div>';
    html += '<div style="font-size:19px;font-weight:800;color:var(--e-t1);letter-spacing:-.4px">' + topicLabel + '</div></div>';

    connections.forEach(function (c, i) {
      var col = palettes[i % palettes.length];
      html += '<div class="eng-card" style="animation-delay:' + (i * .07) + 's">';
      html += '<div class="eng-card-header" style="background:rgba(79,156,247,.05);border-left:3px solid ' + col + '">';
      html += '<div style="flex:1"><div style="font-size:14px;font-weight:700;color:' + col + '">' + c.subject + '</div><div style="font-size:10px;color:var(--e-t3);margin-top:2px;font-family:var(--e-mono)">' + c.semester + '</div></div></div>';
      html += '<div class="eng-card-body">';
      html += '<div style="font-size:12.5px;color:var(--e-t2);line-height:1.75;margin-bottom:10px">' + c.how + '</div>';
      html += '<div style="background:var(--e-bg3);border:1px solid var(--e-border);border-radius:8px;padding:10px 14px;font-family:var(--e-mono);font-size:12px;color:var(--e-t2)">';
      html += '<span style="font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:' + col + ';display:block;margin-bottom:6px">Example</span>' + c.example;
      html += '</div></div></div>';
    });
    html += '</div>';

    setOutput('<div class="eng-response">' + html + '</div>' + buildRefsHTML(refs));
    typesetOutput();
  }

  function fetchPYQ() {
    if (!state.activeSubtopic) return;
    showLoading('Fetching PYQs…');
    postToAPI('/eng/pyq', {
      topic: state.activeTopic, subtopic: state.activeSubtopic,
      university: document.getElementById('eng-univ-select').value,
      difficulty: document.getElementById('eng-diff-select').value
    }, function (data) { renderResponse(data.response, data.source, data.references || []); });
  }

  function fetchMockTest() {
    if (!state.activeSubtopic) return;
    showLoading('Generating mock test…');
    postToAPI('/eng/mocktest', {
      topic: state.activeTopic, subtopic: state.activeSubtopic,
      num_questions: document.getElementById('eng-numq-select').value,
      marks_each:    document.getElementById('eng-marks-select').value
    }, function (data) { renderResponse(data.response, data.source, []); });
  }

  function askAI() {
    var inp = document.getElementById('eng-ask-input');
    var q   = inp ? inp.value.trim() : '';
    if (!q) return;
    if (inp) { inp.value = ''; inp.style.height = 'auto'; }
    showLoading('Thinking…');
    postToAPI('/eng/ask', { question: q }, function (data) { renderResponse(data.response, data.source, []); });
  }

  function postToAPI(endpoint, payload, cb) {
    state.loading = true;
    fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        state.loading = false;
        if (data.error) {
          var errHTML = '<div class="eng-response"><p style="color:var(--e-rose)">Error: ' + data.error + '</p></div>';
          // Try to put error in the nearest result div first
          var rd = document.querySelector('[id$="-result"]');
          if (rd && state.gateMode) rd.innerHTML = errHTML;
          else setOutput(errHTML);
        } else { cb(data); }
      })
      .catch(function () {
        state.loading = false;
        setOutput('<div class="eng-response"><p style="color:var(--e-rose)">Network error. Please try again.</p></div>');
      });
  }

  // ── RENDERING ────────────────────────────────────────────────
  function showLoading(msg) {
    setOutput('<div class="eng-loading"><div class="eng-spinner"></div><span>' + (msg || 'Loading…') + '</span></div>');
  }

  function renderContent(text) {
    if (typeof renderMathContent === 'function') return renderMathContent(text);
    return '<p>' + String(text).replace(/\n{2,}/g, '</p><p>').replace(/\n/g, '<br>') + '</p>';
  }

  function renderResponse(text, source, refs, prereqs) {
    var prereqHtml = '';
    if (prereqs && prereqs.length) {
      prereqHtml = '<div class="eng-prereq-banner"><div class="eng-prereq-label">Prerequisites</div><div class="eng-prereq-pills">';
      prereqs.forEach(function (p) { prereqHtml += '<span class="eng-prereq-pill">' + p + '</span>'; });
      prereqHtml += '</div></div>';
    }
    var sourceHtml = source ? '<div style="margin-top:12px;font-size:10px;font-family:var(--e-mono);color:var(--e-t4)">● via ' + source + '</div>' : '';
    setOutput(prereqHtml + '<div class="eng-response">' + renderContent(text) + sourceHtml + '</div>' + buildRefsHTML(refs));
    typesetOutput();
  }

  function buildRefsHTML(refs) {
    if (!refs || !refs.length) return '';
    var links = refs.map(function (url) {
      var label = url.replace(/^https?:\/\/(?:www\.)?/, '').split('/')[0];
      return '<a href="' + url + '" target="_blank" rel="noopener">🔗 ' + label + '</a>';
    }).join('');
    return '<div class="eng-refs"><div class="eng-refs-title">References</div><div class="eng-refs-list">' + links + '</div></div>';
  }

  function typesetOutput() {
    var out = document.getElementById('eng-output');
    if (!out) return;
    if (typeof typesetEl === 'function') { typesetEl(out); return; }
    if (window.MathJax && window.MathJax.typesetPromise) {
      setTimeout(function () { window.MathJax.typesetPromise([out]).catch(function () {}); }, 60);
    }
  }

  function setOutput(html) {
    var out = document.getElementById('eng-output');
    if (out) { out.innerHTML = html; out.scrollTop = 0; }
  }

  // ── HELPERS ──────────────────────────────────────────────────
  function toggleEl(id, show) {
    var el = document.getElementById(id);
    if (!el) return;
    if (show) el.classList.remove('hidden');
    else      el.classList.add('hidden');
  }

  function clearSubtopics() {
    var bar = document.getElementById('eng-subtopic-bar');
    if (bar) { bar.innerHTML = ''; bar.classList.add('hidden'); }
  }

  function clearBars() {
    toggleEl('eng-section-bar', false);
    toggleEl('eng-pyq-filters', false);
    toggleEl('eng-mock-config', false);
    toggleEl('eng-ask-area', state.activeTab === 'ask');
  }

  // ── PUBLIC API ────────────────────────────────────────────────
  window.engModule = {
    chooseMode:              chooseMode,
    showLanding:             showLanding,
    switchTab:               switchTab,
    selectSem:               selectSem,
    selectTopic:             selectTopic,
    selectSubtopic:          selectSubtopic,
    selectSection:           selectSection,
    fetchPYQ:                fetchPYQ,
    fetchMockTest:           fetchMockTest,
    askAI:                   askAI,
    toggleSidebar:           toggleSidebar,
    submitMisconception:     submitMisconception,
    // GATE
    selectGateBranch:        selectGateBranch,
    gateBackToBranches:      gateBackToBranches,
    switchGateTab:           switchGateTab,
    selectGateTopic:         selectGateTopic,
    fetchGatePractice:       fetchGatePractice,
    fetchGateMock:           fetchGateMock,
    fetchGateStrategy:       fetchGateStrategy,
    fetchGateFormulas:       fetchGateFormulas,
    fetchGateMisconceptions: fetchGateMisconceptions,
    fetchGateAnalysis:       fetchGateAnalysis
  };

})();
