// ══════════════════════════════════════════════════════════════
//  MATHSPHERE ENGINEERING — engineering.js
//  Mode switcher + full engineering interface
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
        var saved = localStorage.getItem('msMode');
        if (saved === 'engineering') activateEngineering();
        else if (saved === 'general') activateGeneral();
        else showLanding();
    });
    
    // ══════════════════════════════════════════════════════════════
    //  LANDING OVERLAY
    // ══════════════════════════════════════════════════════════════
    function injectLanding() {
        var el = document.createElement('div');
        el.id = 'mode-landing';
        el.className = 'hidden';
        el.innerHTML = [
            '<div class="landing-logo">',
            '  <div class="landing-logo-mark">M</div>',
            '  <div>',
            '    <div style="font-size:16px;font-weight:700;letter-spacing:-.3px">MathSphere</div>',
            '    <div class="landing-tagline">Learn Maths with Anupam</div>',
            '  </div>',
            '</div>',
            '<div class="landing-title">Choose your learning path</div>',
            '<div class="landing-sub">Select General Mathematics for broad topics,<br>or Engineering Mathematics for B.Tech Semester 1-4.</div>',
            '<div class="landing-cards">',
            '  <div class="landing-card landing-card--general" onclick="window.engModule.chooseMode(\'general\')">',
            '    <div class="landing-card-icon">&#x2211;</div>',
            '    <div class="landing-card-title">General Mathematics</div>',
            '    <div class="landing-card-desc">Ask Anupam, Intuition Builder, Story Mode, PYQ Practice, Graph Plotter, Mock Tests and more for all levels from Class 11 to research.</div>',
            '    <span class="landing-card-badge">All levels</span>',
            '  </div>',
            '  <div class="landing-card landing-card--engineering" onclick="window.engModule.chooseMode(\'engineering\')">',
            '    <div class="landing-card-icon" style="font-family:var(--font-mono);font-size:16px;color:#3b82f6">&#x222B;&#x2207;</div>',
            '    <div class="landing-card-title">Engineering Mathematics</div>',
            '    <div class="landing-card-desc">Structured Semester 1-4 content based on IIT/NIT syllabus. Definitions, theorems, proofs, PYQs from universities across India, Formula Booklet, and Subject Connections.</div>',
            '    <span class="landing-card-badge">B.Tech Sem 1-4</span>',
            '  </div>',
            '</div>',
            '<div class="landing-footer">Your choice is remembered - switch anytime using the button in the header.</div>'
        ].join('');
        document.body.appendChild(el);
    }
    
    // ══════════════════════════════════════════════════════════════
    //  ENGINEERING APP
    // ══════════════════════════════════════════════════════════════
    function injectEngApp() {
        var el = document.createElement('div');
        el.id = 'eng-app';
        el.innerHTML = [
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
            '    <button class="eng-tab active" data-tab="learn"       onclick="window.engModule.switchTab(\'learn\',this)">Learn</button>',
            '    <button class="eng-tab"        data-tab="revision"    onclick="window.engModule.switchTab(\'revision\',this)">Quick Revision</button>',
            '    <button class="eng-tab"        data-tab="formulabook" onclick="window.engModule.switchTab(\'formulabook\',this)">Formula Booklet</button>',
            '    <button class="eng-tab"        data-tab="connections" onclick="window.engModule.switchTab(\'connections\',this)">Subject Connections</button>',
            '    <button class="eng-tab"        data-tab="pyq"         onclick="window.engModule.switchTab(\'pyq\',this)">PYQ Bank</button>',
            '    <button class="eng-tab"        data-tab="mocktest"    onclick="window.engModule.switchTab(\'mocktest\',this)">Mock Test</button>',
            '    <button class="eng-tab"        data-tab="ask"         onclick="window.engModule.switchTab(\'ask\',this)">Ask AI</button>',
            '  </div>',
            '  <div class="eng-header-right">',
            '    <button class="mode-switch-btn" onclick="window.engModule.showLanding()">&#x21C4; Switch Mode</button>',
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
            '        <div class="eng-welcome-sub">Select a semester, choose a topic, then pick a subtopic to begin. Seven tabs — Learn, Revision, Formula Booklet, Subject Connections, PYQ Bank, Mock Test, and Ask AI.</div>',
            '      </div>',
            '    </div>',
    
            // Ask AI input
            '    <div class="eng-ask-area hidden" id="eng-ask-area">',
            '      <div class="eng-input-box">',
            '        <textarea id="eng-ask-input" rows="1" placeholder="Ask any engineering mathematics question..." oninput="this.style.height=\'auto\';this.style.height=this.scrollHeight+\'px\'" onkeydown="if(event.key===\'Enter\'&&!event.shiftKey){event.preventDefault();window.engModule.askAI()}"></textarea>',
            '        <button class="eng-send" onclick="window.engModule.askAI()">',
            '          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
            '        </button>',
            '      </div>',
            '    </div>',
    
            '  </div>',
            '</div>'
        ].join('');
        document.body.appendChild(el);
    
        // Mobile overlay — tapping it closes the sidebar drawer
        var overlay = document.createElement('div');
        overlay.id = 'eng-mobile-overlay';
        overlay.className = 'eng-mobile-overlay';
        overlay.addEventListener('click', function() { closeSidebar(); });
        document.body.appendChild(overlay);
    }
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
        toggleEl('eng-subtopic-bar', tab !== 'ask' && state.activeTopic);
    
        if (state.activeSubtopic) {
            if (tab === 'revision')    fetchContent('revision');
            if (tab === 'formulabook') fetchFormulaBooklet();
            if (tab === 'connections') fetchConnections();
        }
    
        if (tab === 'ask') {
            setOutput('<div class="eng-welcome"><div class="eng-welcome-symbol" style="font-size:36px">?</div><div class="eng-welcome-title">Ask Engineering AI</div><div class="eng-welcome-sub">Ask any B.Tech mathematics question. I know you are studying for semester exams and will answer at exactly that level.</div></div>');
        }
    
        if (tab === 'connections' && !state.activeSubtopic) {
            setOutput(buildConnectionsWelcome());
        }
    
        if (tab === 'formulabook' && !state.activeSubtopic) {
            setOutput('<div class="eng-welcome"><div class="eng-welcome-symbol" style="font-size:36px;font-family:var(--font-mono)">F(x)</div><div class="eng-welcome-title">Formula Booklet</div><div class="eng-welcome-sub">Select a semester, topic, and subtopic to generate a complete formula reference with physical meanings, units, and examples.</div></div>');
        }
    }
    
    function buildConnectionsWelcome() {
        return [
            '<div class="eng-welcome">',
            '<div class="eng-welcome-symbol" style="font-size:36px">&#x2194;</div>',
            '<div class="eng-welcome-title">Subject Connections Map</div>',
            '<div class="eng-welcome-sub">Discover exactly where your mathematics appears in Circuits, Mechanics, Control Systems, Signals, and more. Select a topic to see its real engineering applications.</div>',
            '</div>'
        ].join('');
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
        setOutput('<div class="eng-welcome"><div class="eng-welcome-symbol">&#x222B;</div><div class="eng-welcome-title">' + label + '</div><div class="eng-welcome-sub">Select a topic from the left to begin.</div></div>');
    }
    
    function renderTopicList(sem) {
        var list = document.getElementById('eng-topic-list');
        if (!list || !state.syllabus || !state.syllabus[sem]) { if(list) list.innerHTML = ''; return; }
        var topics = state.syllabus[sem].topics;
        list.innerHTML = '';
        Object.keys(topics).forEach(function(key) {
            var t = topics[key];
            var btn = document.createElement('button');
            btn.className = 'eng-topic-btn';
            btn.setAttribute('data-topic', key);
            btn.textContent = t.label;
            btn.addEventListener('click', function() {
                selectTopic(key, btn);
            });
            var group = document.createElement('div');
            group.className = 'eng-topic-group';
            group.appendChild(btn);
            list.appendChild(group);
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
        closeSidebar(); // close drawer on mobile after topic selected
    
        // For Subject Connections tab — show topic-level connections immediately
        if (state.activeTab === 'connections') {
            fetchConnections();
            return;
        }
        setOutput('<div class="eng-welcome"><div class="eng-welcome-symbol" style="font-size:36px;font-family:var(--font-mono)">{ }</div><div class="eng-welcome-title">' + btn.textContent + '</div><div class="eng-welcome-sub">Select a subtopic above to load content.</div></div>');
    }
    
    function renderSubtopics(topicKey) {
        var bar = document.getElementById('eng-subtopic-bar');
        if (!bar || !state.syllabus || !state.activeSem) { if(bar) bar.classList.add('hidden'); return; }
        var sem = state.syllabus[state.activeSem];
        if (!sem || !sem.topics[topicKey]) { bar.classList.add('hidden'); return; }
    
        if (state.activeTab === 'connections') { bar.classList.add('hidden'); return; }
    
        var subs = sem.topics[topicKey].subtopics;
        bar.innerHTML = '';
        subs.forEach(function(s) {
            var btn = document.createElement('button');
            btn.className = 'eng-chip';
            btn.setAttribute('data-sub', s);
            btn.textContent = s;
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
        showLoading('Loading Subject Connections for ' + displayName + '...');
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
        var colors = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4'];
        var html = '<div style="padding:4px 0">';
        html += '<div style="margin-bottom:20px;">';
        html += '<div style="font-family:var(--font-mono);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#3b82f6;margin-bottom:4px;">Subject Connections Map</div>';
        html += '<div style="font-size:18px;font-weight:700;color:var(--text-primary);letter-spacing:-.3px;">' + topicLabel + '</div>';
        html += '<div style="font-size:12px;color:var(--text-tertiary);margin-top:4px;">Where this mathematics appears in your engineering degree</div>';
        html += '</div>';
    
        connections.forEach(function(c, i) {
            var color = colors[i % colors.length];
            html += '<div style="margin-bottom:16px;border-radius:10px;overflow:hidden;border:1px solid rgba(255,255,255,0.06);">';
            // Header
            html += '<div style="background:' + color + '18;border-left:3px solid ' + color + ';padding:12px 16px;display:flex;align-items:center;gap:12px;">';
            html += '<div style="flex:1;">';
            html += '<div style="font-size:14px;font-weight:700;color:' + color + ';letter-spacing:-.2px;">' + c.subject + '</div>';
            html += '<div style="font-size:11px;color:var(--text-tertiary);margin-top:2px;font-family:var(--font-mono);">' + c.semester + '</div>';
            html += '</div>';
            html += '<div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;padding:3px 10px;border-radius:9999px;background:' + color + '22;color:' + color + ';border:1px solid ' + color + '44;">Engineering</div>';
            html += '</div>';
            // Body
            html += '<div style="background:var(--bg-surface);padding:12px 16px;">';
            html += '<div style="font-size:12.5px;color:var(--text-secondary);line-height:1.7;margin-bottom:10px;">' + c.how + '</div>';
            html += '<div style="background:var(--bg-raised);border:1px solid rgba(255,255,255,0.06);border-radius:6px;padding:10px 14px;font-family:var(--font-mono);font-size:12px;color:var(--text-secondary);">';
            html += '<span style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:' + color + ';display:block;margin-bottom:6px;">Example</span>';
            html += c.example;
            html += '</div>';
            html += '</div>';
            html += '</div>';
        });
    
        html += '</div>';
    
        // References
        var refsHtml = '';
        if (refs && refs.length) {
            var links = refs.map(function(url) {
                var label = url.replace(/^https?:\/\/(?:www\.)?/, '').split('/')[0];
                return '<a href="' + url + '" target="_blank" rel="noopener" class="eng-refs-list" style="display:inline-flex;align-items:center;gap:6px;background:var(--bg-surface);border:1px solid rgba(59,130,246,0.2);color:#3b82f6;text-decoration:none;padding:5px 12px;border-radius:6px;font-size:11px;font-family:var(--font-mono);margin:3px;">&#x1F517; ' + label + '</a>';
            }).join('');
            refsHtml = '<div style="margin-top:16px;padding:14px 16px;background:var(--bg-raised);border:1px solid rgba(255,255,255,0.06);border-left:2px solid #3b82f6;border-radius:0 8px 8px 0;">';
            refsHtml += '<div style="font-family:var(--font-mono);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#3b82f6;margin-bottom:10px;">References</div>';
            refsHtml += '<div style="display:flex;flex-wrap:wrap;gap:4px;">' + links + '</div>';
            refsHtml += '</div>';
        }
    
        setOutput('<div class="eng-response">' + html + '</div>' + refsHtml);
    
        // Typeset math in the connections
        var out = document.getElementById('eng-output');
        if (out && typeof typesetEl === 'function') typesetEl(out);
        else if (window.MathJax && window.MathJax.typesetPromise) {
            setTimeout(function() { window.MathJax.typesetPromise([out]).catch(function(){}); }, 50);
        }
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
        showLoading('Generating ' + numQ + '-question mock test on ' + state.activeSubtopic + '...');
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
                setOutput('<div class="eng-response"><p style="color:#f87171">Error: ' + data.error + '</p></div>');
            } else {
                cb(data);
            }
        })
        .catch(function(e){
            state.loading = false;
            setOutput('<div class="eng-response"><p style="color:#f87171">Network error. Please try again.</p></div>');
        });
    }
    
    // ══════════════════════════════════════════════════════════════
    //  RENDERING
    // ══════════════════════════════════════════════════════════════
    function showLoading(msg) {
        setOutput('<div class="eng-loading"><div class="eng-spinner"></div>' + (msg || 'Loading...') + '</div>');
    }
    
    function renderResponse(text, source, refs, prereqs) {
        var rendered = '';
        if (typeof renderMathContent === 'function') {
            rendered = renderMathContent(text);
        } else {
            rendered = '<p class="vr-para">' + text.replace(/\n{2,}/g, '</p><p class="vr-para">').replace(/\n/g, '<br>') + '</p>';
        }
    
        // Prerequisites banner
        var prereqHtml = '';
        if (prereqs && prereqs.length) {
            var pills = prereqs.map(function(p) {
                return '<span style="display:inline-block;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);color:#3b82f6;padding:3px 10px;border-radius:9999px;font-size:11px;font-family:var(--font-mono);margin:2px;">' + p + '</span>';
            }).join('');
            prereqHtml = '<div style="margin-bottom:16px;padding:12px 16px;background:rgba(59,130,246,0.04);border:1px solid rgba(59,130,246,0.15);border-left:3px solid #3b82f6;border-radius:0 8px 8px 0;">';
            prereqHtml += '<div style="font-family:var(--font-mono);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#3b82f6;margin-bottom:8px;">Prerequisites for this topic</div>';
            prereqHtml += '<div style="display:flex;flex-wrap:wrap;gap:4px;">' + pills + '</div>';
            prereqHtml += '</div>';
        }
    
        var sourceHtml = source ? '<div style="margin-top:12px;font-size:10px;font-family:var(--font-mono);color:var(--text-disabled)">Source: ' + source + '</div>' : '';
        var refsHtml = '';
        if (refs && refs.length) {
            var links = refs.map(function(url) {
                var label = url.replace(/^https?:\/\/(?:www\.)?/, '').split('/')[0];
                return '<a href="' + url + '" target="_blank" rel="noopener">&#x1F517; ' + label + '</a>';
            }).join('');
            refsHtml = '<div class="eng-refs"><div class="eng-refs-title">References &amp; Further Reading</div><div class="eng-refs-list">' + links + '</div></div>';
        }
        setOutput(prereqHtml + '<div class="eng-response">' + rendered + sourceHtml + '</div>' + refsHtml);
        var out = document.getElementById('eng-output');
        if (out && typeof typesetEl === 'function') typesetEl(out);
        else if (window.MathJax && window.MathJax.typesetPromise) {
            setTimeout(function() { window.MathJax.typesetPromise([out]).catch(function(){}); }, 50);
        }
    }
    
    function setOutput(html) {
        var out = document.getElementById('eng-output');
        if (out) out.innerHTML = html;
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
        chooseMode:      chooseMode,
        showLanding:     showLanding,
        switchTab:       switchTab,
        selectSem:       selectSem,
        selectTopic:     selectTopic,
        selectSubtopic:  selectSubtopic,
        selectSection:   selectSection,
        fetchPYQ:        fetchPYQ,
        fetchMockTest:   fetchMockTest,
        askAI:           askAI,
        toggleSidebar:   toggleSidebar
    };
    
    })();