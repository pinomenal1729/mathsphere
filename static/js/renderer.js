// ══════════════════════════════════════════════════════════════
//  MATHSPHERE — VISUAL RENDERER  (Corrected)
// ══════════════════════════════════════════════════════════════

// ── SECTION ICON MAP ───────────────────────────────────────────
const SECTION_ICONS = {
    'CAREER LANDSCAPE'              : { icon: '🌍', color: 'teal'   },
    'CAREER NAME'                   : { icon: '💼', color: 'amber'  },
    'ROLE'                          : { icon: '🎯', color: 'teal'   },
    'MATHEMATICS USED'              : { icon: '📐', color: 'purple' },
    'INDUSTRIES'                    : { icon: '🏢', color: 'amber'  },
    'SALARY RANGE'                  : { icon: '💰', color: 'green'  },
    'DEMAND'                        : { icon: '📈', color: 'teal'   },
    'STEP BY STEP ROADMAP'          : { icon: '🗺️', color: 'amber'  },
    'YEAR BY YEAR PLAN'             : { icon: '📅', color: 'rose'   },
    'YEAR 1'                        : { icon: '🌱', color: 'teal'   },
    'YEAR 2'                        : { icon: '🌿', color: 'teal'   },
    'YEAR 3'                        : { icon: '🌳', color: 'amber'  },
    'YEAR 4+'                       : { icon: '🚀', color: 'rose'   },
    'ESSENTIAL SKILLS STACK'        : { icon: '🛠️', color: 'purple' },
    'MATHEMATICS'                   : { icon: '∑',  color: 'purple' },
    'TOOLS'                         : { icon: '⚙️', color: 'amber'  },
    'SOFT SKILLS'                   : { icon: '🤝', color: 'teal'   },
    'FREE RESOURCES TO START TODAY' : { icon: '📚', color: 'teal'   },
    'INSPIRING PEOPLE TO FOLLOW'    : { icon: '⭐', color: 'amber'  },
    'FIRST STEP THIS WEEK'          : { icon: '⚡', color: 'rose'   },
    'UNDERSTAND'                    : { icon: '🔍', color: 'teal'   },
    'APPROACH'                      : { icon: '💡', color: 'amber'  },
    'PROOF'                         : { icon: '📝', color: 'purple' },
    'VERIFY'                        : { icon: '✅', color: 'green'  },
    'VERIFICATION'                  : { icon: '✅', color: 'green'  },
    'ANSWER'                        : { icon: '🎯', color: 'amber'  },
    'FINAL ANSWER'                  : { icon: '🎯', color: 'amber'  },
    'CONFIDENCE'                    : { icon: '📊', color: 'teal'   },
    'KEY INSIGHT'                   : { icon: '💡', color: 'amber'  },
    'EDGE CASES'                    : { icon: '⚠️', color: 'rose'   },
    'THE STORY'                     : { icon: '📖', color: 'rose'   },
    'THE ANALOGY'                   : { icon: '🎯', color: 'amber'  },
    'WHAT YOUR BRAIN IS DOING'      : { icon: '🧠', color: 'purple' },
    'THE CORE IDEA IN ONE LINE'     : { icon: '💎', color: 'teal'   },
    'NOW THE MATHEMATICS'           : { icon: '∑',  color: 'purple' },
    'REAL WORLD RIGHT NOW'          : { icon: '🌍', color: 'teal'   },
    'INTUITION CHECK'               : { icon: '❓', color: 'rose'   },
    'THE PROBLEM THAT STARTED EVERYTHING' : { icon: '⚡', color: 'rose'   },
    'THE STRUGGLE'                  : { icon: '⚔️', color: 'amber'  },
    'THE BREAKTHROUGH'              : { icon: '💥', color: 'amber'  },
    'THE MATHEMATICS REVEALED'      : { icon: '∑',  color: 'purple' },
    'HOW IT CHANGED THE WORLD'      : { icon: '🌍', color: 'teal'   },
    'WHERE IT LIVES TODAY'          : { icon: '📱', color: 'teal'   },
    'THE OPEN MYSTERY'              : { icon: '🌌', color: 'purple' },
    'WHAT I NOTICE YOU\'RE THINKING'       : { icon: '👁️', color: 'teal'   },
    'THE QUESTION BENEATH YOUR QUESTION'   : { icon: '❓', color: 'purple' },
    'THINK ABOUT THIS FIRST'               : { icon: '🤔', color: 'amber'  },
    'A RELATED PATTERN TO NOTICE'          : { icon: '🔗', color: 'teal'   },
    'WHEN YOU\'VE WRESTLED WITH THAT'      : { icon: '💪', color: 'rose'   },
    'MATHEMATICAL THINKING HABIT THIS BUILDS': { icon: '🧠', color: 'purple' },
    'CENTRAL CONCEPT'               : { icon: '🎯', color: 'amber'  },
    'PREREQUISITE CONCEPTS'         : { icon: '⬅️', color: 'teal'   },
    'CORE SUB-CONCEPTS'             : { icon: '🔗', color: 'purple' },
    'CONNECTED TOPICS'              : { icon: '🕸️', color: 'rose'   },
    'REAL WORLD NODES'              : { icon: '🌍', color: 'teal'   },
    'THE BIG PICTURE'               : { icon: '🖼️', color: 'amber'  },
    'LEARNING PATHWAY'              : { icon: '🗺️', color: 'amber'  },
    'NAME'                          : { icon: '👤', color: 'amber'  },
    'EARLY LIFE'                    : { icon: '🌱', color: 'teal'   },
    'CONTRIBUTIONS'                 : { icon: '🏆', color: 'amber'  },
    'KEY THEOREMS'                  : { icon: '📜', color: 'purple' },
    'IMPACT'                        : { icon: '🌍', color: 'teal'   },
    'FAMOUS QUOTE'                  : { icon: '💬', color: 'rose'   },
    'WIKIPEDIA'                     : { icon: '🔗', color: 'teal'   },
    'WHAT WE\'RE PROVING'           : { icon: '📋', color: 'amber'  },
    'THE VISUAL SETUP'              : { icon: '🖼️', color: 'teal'   },
    'THE VISUAL ARGUMENT'           : { icon: '👁️', color: 'purple' },
    'THE MOMENT OF INSIGHT'         : { icon: '💥', color: 'amber'  },
    'WHY THIS IS A PROOF'           : { icon: '✅', color: 'green'  },
    'THE FORMULA EMERGES'           : { icon: '∑',  color: 'purple' },
    'OTHER WAYS TO SEE IT'          : { icon: '🔄', color: 'teal'   },
    'PUZZLE TITLE'                  : { icon: '🧩', color: 'amber'  },
    'THE OBSERVATION'               : { icon: '👁️', color: 'teal'   },
    'WHAT TO WONDER'                : { icon: '❓', color: 'purple' },
    'HINT'                          : { icon: '💡', color: 'amber'  },
    'THE BEAUTIFUL ANSWER'          : { icon: '✨', color: 'rose'   },
    'THE DEEPER MATHEMATICS'        : { icon: '∑',  color: 'purple' },
    'WHY MATHEMATICIANS LOVE THIS'  : { icon: '❤️', color: 'rose'   },
    'BUILD'                         : { icon: '🔨', color: 'amber'  },
    'APPLICATION'                   : { icon: '🌍', color: 'teal'   },
    'RESOURCE'                      : { icon: '🔗', color: 'teal'   },
    'QUESTION'                      : { icon: '📝', color: 'amber'  },
    'SOLUTION'                      : { icon: '📐', color: 'purple' },
    'KEY CONCEPT TESTED'            : { icon: '🔑', color: 'teal'   },
    'STATUS'                        : { icon: '📋', color: 'rose'   },
    'DOMAIN'                        : { icon: '📏', color: 'teal'   },
    'RANGE'                         : { icon: '📊', color: 'teal'   },
    'CRITICAL POINTS'               : { icon: '📍', color: 'rose'   },
    'INFLECTION POINTS'             : { icon: '🔄', color: 'amber'  },
    'INCREASING'                    : { icon: '📈', color: 'green'  },
    'DECREASING'                    : { icon: '📉', color: 'rose'   },
    'ASYMPTOTES'                    : { icon: '↔️', color: 'purple' },
    'INTERCEPTS'                    : { icon: '✕',  color: 'amber'  },
    'SYMMETRY'                      : { icon: '⚖️', color: 'teal'   },
    'CONCAVITY'                     : { icon: '〜', color: 'purple' },
    'FIELD'                         : { icon: '🏷️', color: 'purple' },
    'HOW IT WORKS'                  : { icon: '⚙️', color: 'teal'   },
    'EXAMPLE'                       : { icon: '💡', color: 'amber'  },
    'WHY IT MATTERS'                : { icon: '🌟', color: 'rose'   },
    'THE LEGEND IN ONE LINE'        : { icon: '⭐', color: 'amber'  },
    'THE PROBLEM THAT DEFINED THEM' : { icon: '❓', color: 'rose'   },
    'MATHEMATICAL LEGACY'           : { icon: '🏛️', color: 'purple' },
    'LEARN MORE'                    : { icon: '📚', color: 'teal'   },
    'INTERACTIVE RESOURCE'          : { icon: '🎮', color: 'teal'   },
    'EXPLORE FURTHER'               : { icon: '🔭', color: 'purple' },
    'KEY RESOURCE'                  : { icon: '📚', color: 'teal'   },
    'VISUAL FLOWCHART'              : { icon: '🗺️', color: 'amber'  },
    'VISUAL HINT'                   : { icon: '👁️', color: 'teal'   },
    'KEY CONCEPT'                   : { icon: '💎', color: 'amber'  },
    'VISUAL INSIGHT'                : { icon: '🖼️', color: 'purple' },
    'CAREER NAME'                   : { icon: '💼', color: 'amber'  },
    'TOP 5 CAREER PATHS'            : { icon: '🚀', color: 'teal'   },
    'HOW IT CHANGED THE WORLD'      : { icon: '🌍', color: 'teal'   },
    'FREE RESOURCES TO START TODAY' : { icon: '📚', color: 'teal'   },
    'WHY IT MATTERS'                : { icon: '🌟', color: 'rose'   },
    'APPROACH'                      : { icon: '🧭', color: 'teal'   },
    'QUESTION TEXT'                 : { icon: '📋', color: 'amber'  },
    'COMMON MISTAKES HERE'          : { icon: '⚠️', color: 'rose'   },
    'COMMON MISTAKES'               : { icon: '⚠️', color: 'rose'   },
    'EXAM STRATEGY'                 : { icon: '⚡', color: 'amber'  },
    'TOPIC SUMMARY'                 : { icon: '📖', color: 'purple' },
    'RECOMMENDED STUDY ORDER'       : { icon: '🗺️', color: 'teal'   },
    'OFFICIAL SOURCES'              : { icon: '🔗', color: 'teal'   },
    'DIFFICULTY AWARENESS'          : { icon: '📊', color: 'teal'   },
    'WHAT YOU DID RIGHT'            : { icon: '✅', color: 'green'  },
    'THE EXACT ERROR'               : { icon: '🔍', color: 'rose'   },
    'WHY IT IS WRONG'               : { icon: '⚠️', color: 'rose'   },
    'THE CORRECT APPROACH'          : { icon: '🔧', color: 'teal'   },
    'WHAT TO REMEMBER'              : { icon: '💎', color: 'amber'  },
    'SIMILAR MISTAKES TO WATCH FOR' : { icon: '👁️', color: 'purple' },
    'VERDICT'                       : { icon: '⚖️', color: 'amber'  },
    'YOUR ANSWER'                   : { icon: '📝', color: 'rose'   },
    'CORRECT ANSWER'                : { icon: '✅', color: 'green'  },
    'WHERE IT WENT WRONG'           : { icon: '🔍', color: 'rose'   },
    'THE CORRECT WORKING'           : { icon: '🔧', color: 'teal'   },
    'FORMULA NAME'                  : { icon: '📐', color: 'amber'  },
    'FORMULA'                       : { icon: '∑',  color: 'purple' },
    'CONDITIONS'                    : { icon: '⚠️', color: 'rose'   },
    'CORE FORMULAS'                 : { icon: '📐', color: 'purple' },
    'STANDARD RESULTS TO MEMORISE'  : { icon: '🧠', color: 'amber'  },
    'COMMON SUBSTITUTIONS'          : { icon: '🔄', color: 'teal'   },
    'CONNECTIONS TO OTHER TOPICS'   : { icon: '🔗', color: 'teal'   },
    'EXAM TIPS'                     : { icon: '⚡', color: 'rose'   },
    'MOCK TEST'                     : { icon: '✏️', color: 'rose'   },
    'SCORING'                       : { icon: '🏆', color: 'amber'  },
    'KEY CONCEPTS COVERED'          : { icon: '🔑', color: 'teal'   },
    'DEPTH 1'                       : { icon: '1️⃣', color: 'teal'   },
    'DEPTH 2'                       : { icon: '2️⃣', color: 'amber'  },
    'DEPTH 3'                       : { icon: '3️⃣', color: 'purple' },
    'CONNECTING THOUGHT'            : { icon: '🔗', color: 'rose'   },
    'WHICH DEPTH IS RIGHT FOR YOU'  : { icon: '🎯', color: 'teal'   },
    'THE BIG IDEA'                  : { icon: '💡', color: 'amber'  },
    'THE STORY'                     : { icon: '📖', color: 'rose'   },
    "WHY IT'S COOL"                : { icon: '🌟', color: 'teal'   },
    'THE GROWN-UP VERSION'          : { icon: '∑',  color: 'purple' },
    'REMEMBER IT LIKE THIS'         : { icon: '🧠', color: 'amber'  },
    'INSTRUCTIONS'                  : { icon: '📋', color: 'teal'   },
    'SOLUTIONS'                     : { icon: '📐', color: 'purple' },
    'VIDEO RESOURCES'               : { icon: '▶️', color: 'rose'   },
};

const YEAR_COLORS = ['teal', 'amber', 'rose', 'purple'];

// ── HELPERS ────────────────────────────────────────────────────
function esc(str) {
    return String(str)
        .replace(/&/g,  '&amp;')
        .replace(/</g,  '&lt;')
        .replace(/>/g,  '&gt;')
        .replace(/"/g,  '&quot;');
}

function linkify(text) {
    return String(text).replace(
        /(https?:\/\/[^\s<>"&]+)/g,
        function(url) {
            var clean = url.replace(/^https?:\/\/(?:www\.)?/, '').replace(/\/$/, '');
            // Truncate very long URLs for display
            var display = clean.length > 60 ? clean.substring(0, 57) + '...' : clean;
            return '<a href="' + url +
                '" target="_blank" rel="noopener" class="vr-resource-link">' +
                '<span>🔗</span> ' + display + '</a>';
        }
    );
}

function isQuotaError(text) {
    if (!text) return false;
    var t = text.toLowerCase();
    return t.includes('all ai services') ||
           t.includes('rate limit')      ||
           t.includes('quota')           ||
           t.includes('429')             ||
           t.includes('unavailable');
}

function renderErrorMessage(text) {
    if (!text) return '';
    var t = text.toLowerCase();
    if (t.includes('rate limit') || t.includes('429')) {
        return '<div class="error-bubble rate-limit-error">' +
            '<div class="error-title">⏳ Rate Limit Reached</div>' +
            '<div class="error-body">You are sending messages too quickly. ' +
            'Please wait a moment and try again.</div></div>';
    }
    if (t.includes('quota') || t.includes('all ai services')) {
        return '<div class="error-bubble quota-error">' +
            '<div class="error-title">⚠ Service Temporarily Unavailable</div>' +
            '<div class="error-body">' + esc(text) + '</div>' +
            '<div class="error-fix">The free API quota may be exhausted. ' +
            'Please try again later.</div></div>';
    }
    return '<div class="error-bubble">' +
        '<div class="error-title">⚠ Error</div>' +
        '<div class="error-body">' + esc(text) + '</div></div>';
}

function getSectionMeta(label) {
    var upper = label.toUpperCase().trim();
    if (SECTION_ICONS[upper]) return SECTION_ICONS[upper];
    var keys = Object.keys(SECTION_ICONS);
    for (var i = 0; i < keys.length; i++) {
        if (upper.includes(keys[i]) || keys[i].includes(upper)) {
            return SECTION_ICONS[keys[i]];
        }
    }
    return { icon: '◆', color: 'teal' };
}

function resourceLink(url) {
    var clean = url.replace(/^https?:\/\//, '').replace(/\/$/, '');
    return '<a href="' + url +
        '" target="_blank" rel="noopener" class="vr-resource-link">' +
        '<span>🔗</span> ' + clean + '</a>';
}

// ── CAREER CARD ────────────────────────────────────────────────
var _careerIdx = 0;

function careerCard(title, fields) {
    _careerIdx++;
    var colors = ['teal', 'amber', 'rose', 'purple'];
    var color  = colors[(_careerIdx - 1) % colors.length];
    var rows   = '';
    var keys   = Object.keys(fields);
    for (var i = 0; i < keys.length; i++) {
        var k    = keys[i];
        var v    = fields[k];
        var meta = getSectionMeta(k);
        rows += '<div class="vr-career-row">' +
            '<span class="vr-career-row-icon">' + meta.icon + '</span>' +
            '<span class="vr-career-row-label">' + esc(k) + '</span>' +
            '<span class="vr-career-row-val">' + linkify(esc(v)) + '</span>' +
            '</div>';
    }
    return '<div class="vr-career-card vr-career-' + color + '">' +
        '<div class="vr-career-title">' +
        '<span class="vr-career-num">' + _careerIdx + '</span>' +
        esc(title) + '</div>' +
        '<div class="vr-career-rows">' + rows + '</div>' +
        '</div>';
}

function roadmapFlow(steps) {
    var colors = ['teal', 'amber', 'rose', 'purple', 'green', 'teal', 'amber'];
    var html   = '<div class="vr-roadmap">';
    for (var i = 0; i < steps.length; i++) {
        var color = colors[i % colors.length];
        html += '<div class="vr-roadmap-step vr-rm-' + color + '">' +
            '<div class="vr-rm-num">' + (i + 1) + '</div>' +
            '<div class="vr-rm-text">' + linkify(esc(steps[i])) + '</div>' +
            '</div>';
        if (i < steps.length - 1) html += '<div class="vr-roadmap-arrow">↓</div>';
    }
    return html + '</div>';
}

function renderNumberedList(items) {
    var colors = ['amber', 'teal', 'rose', 'purple', 'green'];
    var html   = '<div class="vr-steps-list">';
    for (var i = 0; i < items.length; i++) {
        var color = colors[i % colors.length];
        html += '<div class="vr-step-card vr-step-' + color + '">' +
            '<div class="vr-step-num">' + (i + 1) + '</div>' +
            '<div class="vr-step-body">' + items[i] + '</div>' +
            '</div>';
    }
    return html + '</div>';
}

function yearCard(label, content, idx) {
    var color = YEAR_COLORS[idx % YEAR_COLORS.length];
    var icons = ['🌱', '🌿', '🌳', '🚀'];
    var icon  = icons[idx % icons.length];
    return '<div class="vr-year-card vr-year-' + color + '">' +
        '<div class="vr-year-badge">' + icon + ' ' + esc(label) + '</div>' +
        '<div class="vr-year-body">' + linkify(esc(content)) + '</div>' +
        '</div>';
}

// ══════════════════════════════════════════════════════════════
//  CORE RENDER PIPELINE
// ══════════════════════════════════════════════════════════════
function renderMathContent(raw) {
    if (!raw) return '';

    _careerIdx = 0;

    // ── Step 1: Normalise LaTeX delimiters ─────────────────────
    // FIX: correct regex for \[...\] and \(...\)
    var text = raw
        .replace(/\\\[/g, '$$').replace(/\\\]/g, '$$')
        .replace(/\\\(/g, '$' ).replace(/\\\)/g, '$' );

    // ── Step 2: Protect math with tokens ──────────────────────
    var dispBlocks   = [];
    var inlineBlocks = [];

    text = text.replace(/\$\$([\s\S]*?)\$\$/g, function(m) {
        dispBlocks.push(m);
        return '\x00D' + (dispBlocks.length - 1) + '\x00';
    });
    text = text.replace(/\$([^$\n]{1,300}?)\$/g, function(m) {
        inlineBlocks.push(m);
        return '\x00I' + (inlineBlocks.length - 1) + '\x00';
    });

    function restoreInline(s) {
        for (var i = 0; i < inlineBlocks.length; i++) {
            s = s.split('\x00I' + i + '\x00').join(inlineBlocks[i]);
        }
        for (var j = 0; j < dispBlocks.length; j++) {
            s = s.split('\x00D' + j + '\x00').join(dispBlocks[j]);
        }
        return s;
    }

    // ── Step 3: Pre-process — normalise so every section header gets its own paragraph ──
    // AI often returns sections separated by single \n — force double \n before ALL-CAPS headers
    text = text
        .replace(/([^\n])\n([A-Z][A-Z0-9 \/\'\-·—]{2,70}:)/g, '$1\n\n$2')
        .replace(/([^\n])\n(\d+[.)] )/g, '$1\n\n$2')
        .replace(/([^\n])\n([-•·▸] )/g, '$1\n\n$2');

    // ── Step 3: Split into paragraphs ─────────────────────────
    var rawParas = text.split(/\n{2,}/);

    var outputBlocks = [];
    var careerBuffer = null;
    var careerTitle  = '';
    var yearIdx      = 0;
    var roadmapSteps = [];
    var inRoadmap    = false;

    function flushCareer() {
        if (careerBuffer && Object.keys(careerBuffer).length) {
            outputBlocks.push({ type: 'career-card', title: careerTitle, fields: careerBuffer });
        }
        careerBuffer = null;
        careerTitle  = '';
    }

    function flushRoadmap() {
        if (roadmapSteps.length) {
            outputBlocks.push({ type: 'roadmap', steps: roadmapSteps });
            roadmapSteps = [];
        }
        inRoadmap = false;
    }

    // ── Step 4: Parse each paragraph ──────────────────────────
    for (var pi = 0; pi < rawParas.length; pi++) {
        var para     = rawParas[pi].trim();
        if (!para) continue;

        var restored = restoreInline(para);

        // ── Display math block ────────────────────────────────
        // FIX: check tokenised form \x00D or restored $$
        if (/^\x00D\d+\x00$/.test(para.trim())) {
            flushCareer(); flushRoadmap();
            outputBlocks.push({ type: 'formula', content: restored });
            continue;
        }
        // Also catch restored $$ blocks that come through as paragraphs
        var trimR = restored.trim();
        if (trimR.startsWith('$$') && trimR.endsWith('$$') && trimR.length > 4) {
            flushCareer(); flushRoadmap();
            outputBlocks.push({ type: 'formula', content: restored });
            continue;
        }

        // ── ALL-CAPS header only (no content) ─────────────────
        var headerOnlyMatch = para.match(/^([A-Z][A-Z0-9\s\/\'\-·—]{2,80}):\s*$/);
        if (headerOnlyMatch) {
            var labelH = headerOnlyMatch[1].trim();
            if (/^YEAR\s+(\d+\+?)/i.test(labelH)) {
                flushCareer(); flushRoadmap();
                outputBlocks.push({ type: 'year-header', label: labelH, idx: yearIdx++ });
                continue;
            }
            if (/STEP BY STEP|ROADMAP|LEARNING PATHWAY/i.test(labelH)) {
                flushCareer(); flushRoadmap();
                outputBlocks.push({ type: 'section-header', label: labelH });
                inRoadmap = true;
                continue;
            }
            flushCareer(); flushRoadmap();
            outputBlocks.push({ type: 'section-header', label: labelH });
            continue;
        }

        // ── ALL-CAPS header + content on same line ─────────────
        var inlineHeaderMatch = para.match(/^([A-Z][A-Z0-9\s\/\'\-·—]{2,70}):\s+([\s\S]+)$/);
        if (inlineHeaderMatch && para.indexOf('\n') === -1) {
            var labelI   = inlineHeaderMatch[1].trim();
            var contentI = inlineHeaderMatch[2].trim();

            if (/^YEAR\s+(\d+\+?)/i.test(labelI)) {
                flushCareer(); flushRoadmap();
                outputBlocks.push({ type: 'year-card', label: labelI, content: restoreInline(contentI), idx: yearIdx++ });
                continue;
            }

            var careerFields = ['ROLE', 'SALARY RANGE', 'DEMAND', 'INDUSTRIES', 'MATHEMATICS USED', 'TOOLS', 'WHY IT MATTERS', 'EXAM STRATEGY', 'KEY CONCEPT TESTED'];
            if (careerFields.indexOf(labelI) !== -1) {
                if (!careerBuffer) careerBuffer = {};
                careerBuffer[labelI] = restoreInline(contentI);
                continue;
            }

            if (labelI === 'CAREER NAME' || /^CAREER\s+\d/.test(labelI)) {
                flushCareer(); flushRoadmap();
                careerTitle  = restoreInline(contentI);
                careerBuffer = {};
                continue;
            }

            if (/FIRST STEP/i.test(labelI)) {
                flushCareer(); flushRoadmap();
                outputBlocks.push({ type: 'first-step', content: restoreInline(contentI) });
                continue;
            }

            flushCareer();
            outputBlocks.push({ type: 'inline-section', label: labelI, content: restoreInline(contentI) });
            continue;
        }

        // ── Numbered list ──────────────────────────────────────
        var lines = para.split('\n').map(function(l) { return l.trim(); }).filter(function(l) { return l.length > 0; });
        if (lines.length >= 1 && lines.every(function(l) { return /^\d+[.)]\s/.test(l); })) {
            var items = lines.map(function(l) { return restoreInline(l.replace(/^\d+[.)]\s+/, '')); });
            flushCareer();
            if (inRoadmap) {
                for (var ri = 0; ri < items.length; ri++) roadmapSteps.push(items[ri]);
            } else {
                outputBlocks.push({ type: 'numbered', items: items });
            }
            continue;
        }

        // ── Step N header ──────────────────────────────────────
        if (/^(Step|Stage|STEP)\s+\d+\s*[—–:\-]/i.test(para)) {
            flushCareer(); flushRoadmap();
            outputBlocks.push({ type: 'step-header', content: restoreInline(para) });
            continue;
        }

        // ── Standalone ALL-CAPS career title ───────────────────
        if (/^[A-Z][A-Z\s\/&·]{4,50}$/.test(para) && para === para.toUpperCase() && !para.includes(':')) {
            flushCareer(); flushRoadmap();
            careerTitle  = para;
            careerBuffer = {};
            continue;
        }

        // ── Bullet list ────────────────────────────────────────
        var bulletLines = para.split('\n').map(function(l) { return l.trim(); }).filter(function(l) { return l.length > 0; });
        if (bulletLines.length > 1 && bulletLines.every(function(l) { return /^[-•·▸▹→]/.test(l); })) {
            flushCareer();
            var bulletItems = bulletLines.map(function(l) { return restoreInline(l.replace(/^[-•·▸▹→]\s*/, '')); });
            outputBlocks.push({ type: 'bullets', items: bulletItems });
            continue;
        }

        // ── Regular paragraph ──────────────────────────────────
        flushCareer();
        if (inRoadmap) flushRoadmap();
        outputBlocks.push({ type: 'paragraph', content: restoreInline(para) });
    }

    flushCareer();
    flushRoadmap();

    // ── Step 5: Render blocks to HTML ─────────────────────────
    var html       = '';
    var yearBuffer = [];

    function flushYears() {
        if (!yearBuffer.length) return;
        html += '<div class="vr-timeline">' + yearBuffer.join('') + '</div>';
        yearBuffer = [];
    }

    for (var bi = 0; bi < outputBlocks.length; bi++) {
        var block = outputBlocks[bi];

        if (block.type !== 'year-card' && block.type !== 'year-header') flushYears();

        switch (block.type) {

            case 'formula':
                html += '<div class="vr-formula-box">' + block.content + '</div>';
                break;

            case 'section-header': {
                var metaSH = getSectionMeta(block.label);
                html += '<div class="vr-section-header vr-sh-' + metaSH.color + '">' +
                    '<span class="vr-sh-icon">' + metaSH.icon + '</span>' +
                    '<span class="vr-sh-text">' + esc(block.label) + '</span>' +
                    '</div>';
                break;
            }

            case 'inline-section': {
                var metaIS = getSectionMeta(block.label);

                if (block.label === 'WIKIPEDIA' || /^RESOURCE/i.test(block.label)) {
                    var urlMatch = block.content.match(/https?:\/\/[^\s]+/);
                    html += '<div class="vr-inline-section vr-is-' + metaIS.color + '">' +
                        '<span class="vr-is-icon">' + metaIS.icon + '</span>' +
                        '<span class="vr-is-label">' + esc(block.label) + '</span>' +
                        (urlMatch ? resourceLink(urlMatch[0]) : linkify(esc(block.content))) +
                        '</div>';
                } else if (/SALARY/i.test(block.label)) {
                    html += '<div class="vr-inline-section vr-is-green">' +
                        '<span class="vr-is-icon">💰</span>' +
                        '<span class="vr-is-label">' + esc(block.label) + '</span>' +
                        '<span class="vr-salary-badge">' + esc(block.content) + '</span>' +
                        '</div>';
                } else if (/DEMAND/i.test(block.label)) {
                    var demandLvl = /HIGH/i.test(block.content) ? 'high' : /LOW/i.test(block.content) ? 'low' : 'med';
                    html += '<div class="vr-inline-section vr-is-' + metaIS.color + '">' +
                        '<span class="vr-is-icon">' + metaIS.icon + '</span>' +
                        '<span class="vr-is-label">' + esc(block.label) + '</span>' +
                        '<span class="vr-demand-badge vr-demand-' + demandLvl + '">' + esc(block.content) + '</span>' +
                        '</div>';
                } else if (/CONFIDENCE/i.test(block.label)) {
                    var confLvl   = /HIGH/i.test(block.content) ? 'high' : /MEDIUM/i.test(block.content) ? 'med' : 'low';
                    var confColor = confLvl === 'high' ? '#22c55e' : confLvl === 'med' ? '#f5a623' : '#ef4444';
                    html += '<div class="vr-inline-section vr-is-teal">' +
                        '<span class="vr-is-icon">📊</span>' +
                        '<span class="vr-is-label">CONFIDENCE</span>' +
                        '<span class="vr-confidence-badge" style="color:' + confColor + ';font-weight:700;">' +
                        esc(block.content) + '</span>' +
                        '</div>';
                } else if (/VERIFICATION/i.test(block.label)) {
                    html += '<div class="vr-inline-section vr-is-green">' +
                        '<span class="vr-is-icon">✅</span>' +
                        '<span class="vr-is-label">VERIFICATION</span>' +
                        '<span class="vr-is-val">' + linkify(esc(block.content)) + '</span>' +
                        '</div>';
                } else {
                    html += '<div class="vr-inline-section vr-is-' + metaIS.color + '">' +
                        '<span class="vr-is-icon">' + metaIS.icon + '</span>' +
                        '<span class="vr-is-label">' + esc(block.label) + '</span>' +
                        '<span class="vr-is-val">' + linkify(esc(block.content)) + '</span>' +
                        '</div>';
                }
                break;
            }

            case 'career-card':
                html += careerCard(block.title, block.fields);
                break;

            case 'roadmap':
                html += roadmapFlow(block.steps);
                break;

            case 'year-header': {
                var metaYH = getSectionMeta(block.label);
                yearBuffer.push('<div class="vr-year-card vr-year-' + YEAR_COLORS[block.idx % 4] + '">' +
                    '<div class="vr-year-badge">' + metaYH.icon + ' ' + esc(block.label) + '</div></div>');
                break;
            }

            case 'year-card':
                yearBuffer.push(yearCard(block.label, block.content, block.idx));
                break;

            case 'numbered':
                html += renderNumberedList(block.items.map(function(item) { return linkify(esc(item)); }));
                break;

            case 'bullets':
                html += '<ul class="vr-bullet-list">';
                for (var bui = 0; bui < block.items.length; bui++) {
                    html += '<li>' + linkify(esc(block.items[bui])) + '</li>';
                }
                html += '</ul>';
                break;

            case 'step-header':
                html += '<div class="vr-step-header-line">' + esc(block.content) + '</div>';
                break;

            case 'first-step':
                html += '<div class="vr-first-step">' +
                    '<div class="vr-fs-label">⚡ FIRST STEP THIS WEEK</div>' +
                    '<div class="vr-fs-body">' + linkify(esc(block.content)) + '</div>' +
                    '</div>';
                break;

            case 'paragraph':
            default:
                // FIX: Don't check for $$ here — math is already tokenised and restored.
                // Just render as paragraph. MathJax will handle $$ inside the text.
                html += '<p class="vr-para">' + linkify(esc(block.content)) + '</p>';
                break;
        }
    }

    flushYears();
    return html;
}

// ── MATHJAX TYPESET ────────────────────────────────────────────
function typesetEl(el) {
    if (window.MathJax && window.MathJax.typesetPromise) {
        setTimeout(function() {
            window.MathJax.typesetPromise([el]).catch(function(err) {
                console.warn('MathJax typeset error:', err);
            });
        }, 30);
    }
}