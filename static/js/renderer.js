// ══════════════════════════════════════════════════════════════
//  MATHSPHERE — VISUAL RENDERER
//  Rich visual output: cards, flowcharts, formula boxes,
//  step ladders, icon sections, career timelines, etc.
// ══════════════════════════════════════════════════════════════

// ── SECTION ICON MAP ───────────────────────────────────────────
const SECTION_ICONS = {
    // Career
    'CAREER LANDSCAPE'    : { icon:'🌍', color:'teal'   },
    'CAREER NAME'         : { icon:'💼', color:'amber'  },
    'ROLE'                : { icon:'🎯', color:'teal'   },
    'MATHEMATICS USED'    : { icon:'📐', color:'purple' },
    'INDUSTRIES'          : { icon:'🏢', color:'amber'  },
    'SALARY RANGE'        : { icon:'💰', color:'green'  },
    'DEMAND'              : { icon:'📈', color:'teal'   },
    'STEP BY STEP ROADMAP': { icon:'🗺️', color:'amber'  },
    'YEAR BY YEAR PLAN'   : { icon:'📅', color:'rose'   },
    'YEAR 1'              : { icon:'🌱', color:'teal'   },
    'YEAR 2'              : { icon:'🌿', color:'teal'   },
    'YEAR 3'              : { icon:'🌳', color:'amber'  },
    'YEAR 4+'             : { icon:'🚀', color:'rose'   },
    'ESSENTIAL SKILLS STACK':{ icon:'🛠️', color:'purple'},
    'MATHEMATICS'         : { icon:'∑',  color:'purple' },
    'TOOLS'               : { icon:'⚙️', color:'amber'  },
    'SOFT SKILLS'         : { icon:'🤝', color:'teal'   },
    'FREE RESOURCES TO START TODAY':{ icon:'📚', color:'teal' },
    'INSPIRING PEOPLE TO FOLLOW'   :{ icon:'⭐', color:'amber'},
    'FIRST STEP THIS WEEK': { icon:'⚡', color:'rose'   },
    // Math
    'UNDERSTAND'          : { icon:'🔍', color:'teal'   },
    'APPROACH'            : { icon:'💡', color:'amber'  },
    'PROOF'               : { icon:'📝', color:'purple' },
    'VERIFY'              : { icon:'✅', color:'green'  },
    'ANSWER'              : { icon:'🎯', color:'amber'  },
    // Intuition
    'THE STORY'           : { icon:'📖', color:'rose'   },
    'THE ANALOGY'         : { icon:'🎯', color:'amber'  },
    'WHAT YOUR BRAIN IS DOING':{ icon:'🧠', color:'purple'},
    'THE CORE IDEA IN ONE LINE':{ icon:'💎', color:'teal'},
    'NOW THE MATHEMATICS' : { icon:'∑',  color:'purple' },
    'REAL WORLD RIGHT NOW': { icon:'🌍', color:'teal'   },
    'INTUITION CHECK'     : { icon:'❓', color:'rose'   },
    // Story
    'THE PROBLEM THAT STARTED EVERYTHING':{ icon:'⚡', color:'rose'  },
    'THE STRUGGLE'        : { icon:'⚔️', color:'amber'  },
    'THE BREAKTHROUGH'    : { icon:'💥', color:'amber'  },
    'THE MATHEMATICS REVEALED':{ icon:'∑', color:'purple'},
    'HOW IT CHANGED THE WORLD':{ icon:'🌍', color:'teal'},
    'WHERE IT LIVES TODAY': { icon:'📱', color:'teal'   },
    'THE OPEN MYSTERY'    : { icon:'🌌', color:'purple' },
    // Concept map
    'CENTRAL CONCEPT'     : { icon:'🎯', color:'amber'  },
    'PREREQUISITE CONCEPTS': { icon:'⬅️', color:'teal' },
    'CORE SUB-CONCEPTS'   : { icon:'🔗', color:'purple' },
    'CONNECTED TOPICS'    : { icon:'🕸️', color:'rose'   },
    'REAL WORLD NODES'    : { icon:'🌍', color:'teal'   },
    'THE BIG PICTURE'     : { icon:'🖼️', color:'amber'  },
    'LEARNING PATHWAY'    : { icon:'🗺️', color:'amber'  },
    // Mathematician
    'NAME'                : { icon:'👤', color:'amber'  },
    'EARLY LIFE'          : { icon:'🌱', color:'teal'   },
    'CONTRIBUTIONS'       : { icon:'🏆', color:'amber'  },
    'KEY THEOREMS'        : { icon:'📜', color:'purple' },
    'IMPACT'              : { icon:'🌍', color:'teal'   },
    'FAMOUS QUOTE'        : { icon:'💬', color:'rose'   },
    'WIKIPEDIA'           : { icon:'🔗', color:'teal'   },
    // Visual proof
    'WHAT WE\'RE PROVING' : { icon:'📋', color:'amber'  },
    'THE VISUAL SETUP'    : { icon:'🖼️', color:'teal'   },
    'THE VISUAL ARGUMENT' : { icon:'👁️', color:'purple' },
    'THE MOMENT OF INSIGHT':{ icon:'💥', color:'amber'  },
    'WHY THIS IS A PROOF' : { icon:'✅', color:'green'  },
    'THE FORMULA EMERGES' : { icon:'∑',  color:'purple' },
    // Puzzle
    'PUZZLE TITLE'        : { icon:'🧩', color:'amber'  },
    'THE OBSERVATION'     : { icon:'👁️', color:'teal'   },
    'WHAT TO WONDER'      : { icon:'❓', color:'purple' },
    'HINT'                : { icon:'💡', color:'amber'  },
    'THE BEAUTIFUL ANSWER': { icon:'✨', color:'rose'   },
    'THE DEEPER MATHEMATICS':{ icon:'∑', color:'purple' },
    'WHY MATHEMATICIANS LOVE THIS':{ icon:'❤️', color:'rose'},
    // Projects
    'BUILD'               : { icon:'🔨', color:'amber'  },
    'APPLICATION'         : { icon:'🌍', color:'teal'   },
    'RESOURCE'            : { icon:'🔗', color:'teal'   },
    // Generic
    'DOMAIN'              : { icon:'📏', color:'teal'   },
    'RANGE'               : { icon:'📊', color:'teal'   },
    'CRITICAL POINTS'     : { icon:'📍', color:'rose'   },
    'INFLECTION POINTS'   : { icon:'🔄', color:'amber'  },
    'INCREASING'          : { icon:'📈', color:'green'  },
    'DECREASING'          : { icon:'📉', color:'rose'   },
    'ASYMPTOTES'          : { icon:'↔️', color:'purple' },
    'INTERCEPTS'          : { icon:'✕',  color:'amber'  },
    'SYMMETRY'            : { icon:'⚖️', color:'teal'   },
    'FIELD'               : { icon:'🏷️', color:'purple' },
    'HOW IT WORKS'        : { icon:'⚙️', color:'teal'   },
    'EXAMPLE'             : { icon:'💡', color:'amber'  },
};

// ── YEAR COLORS for timeline ───────────────────────────────────
const YEAR_COLORS = ['teal','amber','rose','purple'];

// ── CAREER CARD DETECTION ──────────────────────────────────────
// Detects if the whole response is career-mode (has salary, demand, etc.)
function isCareerResponse(raw) {
    return /SALARY RANGE|YEAR BY YEAR|FIRST STEP THIS WEEK/i.test(raw);
}

// ── FORMULA BOX ────────────────────────────────────────────────
function formulaBox(content) {
    return `<div class="vr-formula-box">${content}</div>`;
}

// ── SECTION ICON LOOKUP ────────────────────────────────────────
function getSectionMeta(label) {
    const upper = label.toUpperCase().trim();
    // Exact match
    if (SECTION_ICONS[upper]) return SECTION_ICONS[upper];
    // Partial match
    for (const key of Object.keys(SECTION_ICONS)) {
        if (upper.includes(key) || key.includes(upper)) return SECTION_ICONS[key];
    }
    return { icon: '◆', color: 'teal' };
}

// ── STEP NUMBER CARD ───────────────────────────────────────────
let _stepCounter = 0;
function resetStepCounter() { _stepCounter = 0; }
function stepCard(content) {
    _stepCounter++;
    const colors = ['amber','teal','rose','purple','green'];
    const color = colors[(_stepCounter - 1) % colors.length];
    return `<div class="vr-step-card vr-step-${color}">
        <div class="vr-step-num">${_stepCounter}</div>
        <div class="vr-step-body">${content}</div>
    </div>`;
}

// ── CAREER TIMELINE NODE ───────────────────────────────────────
function yearCard(year, content, idx) {
    const color = YEAR_COLORS[idx % YEAR_COLORS.length];
    const icons = ['🌱','🌿','🌳','🚀'];
    const icon  = icons[idx % icons.length];
    return `<div class="vr-year-card vr-year-${color}">
        <div class="vr-year-badge">${icon} ${year}</div>
        <div class="vr-year-body">${content}</div>
    </div>`;
}

// ── CAREER PATH CARD ───────────────────────────────────────────
let _careerIdx = 0;
function careerCard(title, fields) {
    _careerIdx++;
    const colors = ['teal','amber','rose','purple'];
    const color = colors[(_careerIdx - 1) % colors.length];
    let rows = '';
    for (const [k, v] of Object.entries(fields)) {
        const meta = getSectionMeta(k);
        rows += `<div class="vr-career-row">
            <span class="vr-career-row-icon">${meta.icon}</span>
            <span class="vr-career-row-label">${k}</span>
            <span class="vr-career-row-val">${linkify(esc(v))}</span>
        </div>`;
    }
    return `<div class="vr-career-card vr-career-${color}">
        <div class="vr-career-title">
            <span class="vr-career-num">${_careerIdx}</span>
            ${esc(title)}
        </div>
        <div class="vr-career-rows">${rows}</div>
    </div>`;
}

// ── ROADMAP FLOWCHART ──────────────────────────────────────────
function roadmapFlow(steps) {
    const colors = ['teal','amber','rose','purple','green','teal','amber'];
    return `<div class="vr-roadmap">` +
        steps.map((s, i) => `
            <div class="vr-roadmap-step vr-rm-${colors[i % colors.length]}">
                <div class="vr-rm-num">${i + 1}</div>
                <div class="vr-rm-text">${linkify(esc(s))}</div>
            </div>
            ${i < steps.length - 1 ? '<div class="vr-roadmap-arrow">↓</div>' : ''}
        `).join('') +
    `</div>`;
}

// ── SKILL STACK PILLS ──────────────────────────────────────────
function skillPills(items, color) {
    return `<div class="vr-skill-pills">` +
        items.map(it => `<span class="vr-pill vr-pill-${color}">${esc(it.trim())}</span>`).join('') +
    `</div>`;
}

// ── HIGHLIGHT BOX ──────────────────────────────────────────────
function highlightBox(icon, label, content, color) {
    return `<div class="vr-highlight vr-hl-${color}">
        <div class="vr-hl-header"><span>${icon}</span> <strong>${esc(label)}</strong></div>
        <div class="vr-hl-body">${linkify(esc(content))}</div>
    </div>`;
}

// ── RESOURCE LINK ──────────────────────────────────────────────
function resourceLink(url) {
    const clean = url.replace(/^https?:\/\//, '').replace(/\/$/, '');
    return `<a href="${url}" target="_blank" rel="noopener" class="vr-resource-link">
        <span>🔗</span> ${clean}
    </a>`;
}

// ── MAIN ESCAPE / LINKIFY ──────────────────────────────────────
function esc(str) {
    return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function linkify(text) {
    return String(text).replace(/(https?:\/\/[^\s<>"&]+)/g,
        url => `<a href="${url}" target="_blank" rel="noopener" class="vr-resource-link"><span>🔗</span> ${url.replace(/^https?:\/\//,'').replace(/\/$/,'')}</a>`
    );
}

// ══════════════════════════════════════════════════════════════
//  CORE RENDER PIPELINE
// ══════════════════════════════════════════════════════════════

function renderMathContent(raw, mode) {
    if (!raw) return '';

    resetStepCounter();
    _careerIdx = 0;

    // ── Protect math ──────────────────────────────────────────
    let text = raw
        .replace(/\\\[/g, '$$').replace(/\\\]/g, '$$')
        .replace(/\\\(/g, '$').replace(/\\\)/g, '$');

    const dispBlocks = [];
    text = text.replace(/\$\$([\s\S]*?)\$\$/g, m => {
        dispBlocks.push(m); return `\x00D${dispBlocks.length-1}\x00`;
    });
    const inlineBlocks = [];
    text = text.replace(/\$([^$\n]{1,200}?)\$/g, m => {
        inlineBlocks.push(m); return `\x00I${inlineBlocks.length-1}\x00`;
    });

    // ── Split into paragraphs ──────────────────────────────────
    const rawParas = text.split(/\n{2,}/);

    // ── Restore helpers ───────────────────────────────────────
    function restoreInline(s) {
        inlineBlocks.forEach((b,i) => s = s.replace(`\x00I${i}\x00`, b));
        dispBlocks.forEach((b,i)   => s = s.replace(`\x00D${i}\x00`, b));
        return s;
    }

    // ── Career block grouping ─────────────────────────────────
    // Collect consecutive career fields into a card
    let careerBuffer = null;
    let careerTitle  = '';
    const outputBlocks = [];

    function flushCareer() {
        if (careerBuffer && Object.keys(careerBuffer).length) {
            outputBlocks.push({ type:'career-card', title: careerTitle, fields: careerBuffer });
        }
        careerBuffer = null;
        careerTitle  = '';
    }

    // Detect year cards
    let yearIdx = 0;

    // Track roadmap steps (numbered)
    let roadmapSteps = [];
    let inRoadmap = false;

    function flushRoadmap() {
        if (roadmapSteps.length) {
            outputBlocks.push({ type:'roadmap', steps: roadmapSteps });
            roadmapSteps = [];
        }
        inRoadmap = false;
    }

    for (let para of rawParas) {
        para = para.trim();
        if (!para) continue;

        const restored = restoreInline(para);

        // ── Display math ──────────────────────────────────────
        if (restored.startsWith('$$') && restored.endsWith('$$')) {
            flushCareer(); flushRoadmap();
            outputBlocks.push({ type:'formula', content: restored });
            continue;
        }

        // ── ALL-CAPS section header (standalone) ──────────────
        const headerOnlyMatch = para.match(/^([A-Z][A-Z\s\/\'\-]{2,60}):\s*$/);
        if (headerOnlyMatch) {
            const label = headerOnlyMatch[1].trim();

            // Detect YEAR headers → timeline
            const yearMatch = label.match(/^YEAR\s+(\d+\+?)/i);
            if (yearMatch) {
                flushCareer(); flushRoadmap();
                outputBlocks.push({ type:'year-header', label, idx: yearIdx++ });
                continue;
            }

            // Detect STEP BY STEP ROADMAP → switch mode
            if (/STEP BY STEP|ROADMAP|LEARNING PATHWAY/i.test(label)) {
                flushCareer(); flushRoadmap();
                outputBlocks.push({ type:'section-header', label });
                inRoadmap = true;
                continue;
            }

            // Detect CAREER NAME / TOP 5 CAREER PATHS — flush old career card, start new
            if (/^TOP \d+ CAREER|CAREER PATH/i.test(label)) {
                flushCareer(); flushRoadmap();
                outputBlocks.push({ type:'section-header', label });
                continue;
            }

            // Generic section header
            flushCareer(); flushRoadmap();
            outputBlocks.push({ type:'section-header', label });
            continue;
        }

        // ── ALL-CAPS header + content on same line ────────────
        const inlineHeaderMatch = para.match(/^([A-Z][A-Z\s\/\'\-]{2,50}):\s+(.+)$/s);
        if (inlineHeaderMatch && !para.includes('\n')) {
            const label   = inlineHeaderMatch[1].trim();
            const content = inlineHeaderMatch[2].trim();

            // YEAR 1/2/3/4: content → year card inline
            const yearMatch = label.match(/^YEAR\s+(\d+\+?)/i);
            if (yearMatch) {
                flushCareer(); flushRoadmap();
                outputBlocks.push({ type:'year-card', label, content: restoreInline(content), idx: yearIdx++ });
                continue;
            }

            // Career sub-fields: ROLE, SALARY RANGE, DEMAND, INDUSTRIES, MATHEMATICS USED
            const careerFields = ['ROLE','SALARY RANGE','DEMAND','INDUSTRIES','MATHEMATICS USED','TOOLS'];
            if (careerFields.includes(label)) {
                if (!careerBuffer) careerBuffer = {};
                careerBuffer[label] = restoreInline(content);
                continue;
            }

            // CAREER NAME → start a new career card
            if (label === 'CAREER NAME' || /^CAREER\s+\d/.test(label)) {
                flushCareer(); flushRoadmap();
                careerTitle  = restoreInline(content);
                careerBuffer = {};
                continue;
            }

            // FIRST STEP THIS WEEK → special highlight
            if (/FIRST STEP/i.test(label)) {
                flushCareer(); flushRoadmap();
                outputBlocks.push({ type:'first-step', content: restoreInline(content) });
                continue;
            }

            // SALARY / DEMAND → handled inside career card above
            // Generic inline section
            flushCareer();
            outputBlocks.push({ type:'inline-section', label, content: restoreInline(content) });
            continue;
        }

        // ── Numbered list items → step cards or roadmap ───────
        const lines = para.split('\n').map(l => l.trim()).filter(Boolean);
        if (lines.length >= 1 && lines.every(l => /^\d+[.)]\s/.test(l))) {
            const items = lines.map(l => restoreInline(l.replace(/^\d+[.)]\s+/, '')));
            flushCareer();
            if (inRoadmap) {
                // accumulate roadmap
                roadmapSteps.push(...items);
            } else {
                outputBlocks.push({ type:'numbered', items });
            }
            continue;
        }

        // ── Step N — header ───────────────────────────────────
        if (/^(Step|Stage)\s+\d+\s*[—–:\-]/i.test(para)) {
            flushCareer(); flushRoadmap();
            outputBlocks.push({ type:'step-header', content: restoreInline(para) });
            continue;
        }

        // ── Standalone career card title (ALL CAPS, no colon) ─
        // e.g. "DATA SCIENTIST" on its own line
        if (/^[A-Z][A-Z\s\/&]{4,50}$/.test(para) && para === para.toUpperCase()) {
            flushCareer(); flushRoadmap();
            careerTitle  = para;
            careerBuffer = {};
            continue;
        }

        // ── Regular paragraph ─────────────────────────────────
        flushCareer();
        if (inRoadmap) { flushRoadmap(); }
        outputBlocks.push({ type:'paragraph', content: restoreInline(para) });
    }

    flushCareer();
    flushRoadmap();

    // ── RENDER BLOCKS TO HTML ─────────────────────────────────
    let html = '';
    let yearBuffer = []; // collect year cards for timeline wrapper

    function flushYears() {
        if (!yearBuffer.length) return;
        html += `<div class="vr-timeline">` + yearBuffer.join('') + `</div>`;
        yearBuffer = [];
    }

    for (const block of outputBlocks) {
        if (block.type !== 'year-card' && block.type !== 'year-header') flushYears();

        switch (block.type) {

            case 'formula':
                html += `<div class="vr-formula-box">${esc(block.content)}</div>`;
                break;

            case 'section-header': {
                const meta = getSectionMeta(block.label);
                html += `<div class="vr-section-header vr-sh-${meta.color}">
                    <span class="vr-sh-icon">${meta.icon}</span>
                    <span class="vr-sh-text">${esc(block.label)}</span>
                </div>`;
                break;
            }

            case 'inline-section': {
                const meta = getSectionMeta(block.label);
                // Special: WIKIPEDIA → resource link
                if (block.label === 'WIKIPEDIA' || /^RESOURCE/i.test(block.label)) {
                    const urlMatch = block.content.match(/https?:\/\/[^\s]+/);
                    html += `<div class="vr-inline-section vr-is-${meta.color}">
                        <span class="vr-is-icon">${meta.icon}</span>
                        <span class="vr-is-label">${esc(block.label)}</span>
                        ${urlMatch ? resourceLink(urlMatch[0]) : linkify(esc(block.content))}
                    </div>`;
                }
                // SALARY → pill
                else if (/SALARY/i.test(block.label)) {
                    html += `<div class="vr-inline-section vr-is-green">
                        <span class="vr-is-icon">💰</span>
                        <span class="vr-is-label">${esc(block.label)}</span>
                        <span class="vr-salary-badge">${esc(block.content)}</span>
                    </div>`;
                }
                // DEMAND → badge
                else if (/DEMAND/i.test(block.label)) {
                    const level = /HIGH/i.test(block.content) ? 'high' : /LOW/i.test(block.content) ? 'low' : 'med';
                    html += `<div class="vr-inline-section vr-is-${meta.color}">
                        <span class="vr-is-icon">${meta.icon}</span>
                        <span class="vr-is-label">${esc(block.label)}</span>
                        <span class="vr-demand-badge vr-demand-${level}">${esc(block.content)}</span>
                    </div>`;
                }
                else {
                    html += `<div class="vr-inline-section vr-is-${meta.color}">
                        <span class="vr-is-icon">${meta.icon}</span>
                        <span class="vr-is-label">${esc(block.label)}</span>
                        <span class="vr-is-val">${linkify(esc(block.content))}</span>
                    </div>`;
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
                const meta = getSectionMeta(block.label);
                yearBuffer.push(`<div class="vr-year-card vr-year-${YEAR_COLORS[block.idx % 4]}">
                    <div class="vr-year-badge">${meta.icon} ${esc(block.label)}</div>
                </div>`);
                break;
            }

            case 'year-card':
                yearBuffer.push(yearCard(block.label, block.content, block.idx));
                break;

            case 'numbered':
                html += `<div class="vr-steps-list">` +
                    block.items.map(item => {
                        resetStepCounter();
                        return stepCard(linkify(esc(item)));
                    }).join('') +
                `</div>`;
                // re-init counter properly for the whole list
                html = html; // already set
                break;

            case 'step-header':
                html += `<div class="vr-step-header-line">${esc(block.content)}</div>`;
                break;

            case 'first-step':
                html += `<div class="vr-first-step">
                    <div class="vr-fs-label">⚡ FIRST STEP THIS WEEK</div>
                    <div class="vr-fs-body">${linkify(esc(block.content))}</div>
                </div>`;
                break;

            case 'paragraph':
            default:
                html += `<p class="vr-para">${linkify(esc(block.content))}</p>`;
                break;
        }
    }

    flushYears();

    // ── Post-process: MathJax delimiters survive ──────────────
    // They were protected as \x00 tokens — now they're in escaped HTML,
    // so we need to un-escape the math tokens back to real math
    // (they were restored via restoreInline already above)

    return html;
}

// ── Numbered steps — fix counter for whole list ────────────────
// Override the stepCard to use a closure counter per list
function renderNumberedList(items) {
    return `<div class="vr-steps-list">` +
        items.map((item, i) => {
            const colors = ['amber','teal','rose','purple','green'];
            const color  = colors[i % colors.length];
            return `<div class="vr-step-card vr-step-${color}">
                <div class="vr-step-num">${i + 1}</div>
                <div class="vr-step-body">${item}</div>
            </div>`;
        }).join('') +
    `</div>`;
}

function typesetEl(el) {
    if (window.MathJax?.typesetPromise) {
        setTimeout(() => MathJax.typesetPromise([el]).catch(console.warn), 30);
    }
}

function isQuotaError(text) {
    if (!text) return false;
    const t = text.toLowerCase();
    return t.includes('all ai services') || t.includes('rate limit') ||
           t.includes('quota') || t.includes('unavailable');
}

function renderErrorMessage(text) {
    return `<div class="error-title">⚠ Service Temporarily Unavailable</div>
<div class="error-body">${esc(text)}</div>
<div class="error-fix">Wait a moment and try again. The free API quota may be exhausted for today.</div>`;
}