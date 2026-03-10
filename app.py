from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
from groq import Groq
from dotenv import load_dotenv
import os, base64, re, time, hashlib
from PIL import Image
import io
from functools import lru_cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

# ── ENV VALIDATION AT STARTUP ──────────────────────────────────
def validate_env():
    missing = []
    if not os.getenv("GEMINI_API_KEY"):
        missing.append("GEMINI_API_KEY")
    if not os.getenv("GROQ_API_KEY"):
        missing.append("GROQ_API_KEY")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

validate_env()

app = Flask(__name__)

# ── RATE LIMITING ──────────────────────────────────────────────
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "20 per minute"]
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

MAX_MESSAGE_LENGTH = 5000
MAX_HISTORY_TURNS  = 10

# ── MODEL CASCADES ─────────────────────────────────────────────
HARD_MODEL_CASCADE = [
    ("gemini-2.5-pro",   "Gemini 2.5 Pro ✦"),
    ("gemini-2.5-flash", "Gemini 2.5 Flash ✦"),
    ("gemini-2.0-flash", "Gemini 2.0 Flash"),
]

MATH_MODEL_CASCADE = [
    ("gemini-2.5-pro",   "Gemini 2.5 Pro ✦"),
    ("gemini-2.5-flash", "Gemini 2.5 Flash ✦"),
    ("gemini-2.0-flash", "Gemini 2.0 Flash"),
]

# Separate cascade for verification to avoid self-verification bias
VERIFY_MODEL_CASCADE = [
    ("gemini-2.5-flash", "Gemini 2.5 Flash ✦"),
    ("gemini-2.0-flash", "Gemini 2.0 Flash"),
    ("gemini-2.5-pro",   "Gemini 2.5 Pro ✦"),
]

# ── FORMAT RULES ───────────────────────────────────────────────
FORMAT_RULES = """
OUTPUT FORMAT RULES:
- Write inline math as $...$ for symbols within text sentences.
- Write EVERY standalone equation on its OWN LINE as 
$$
...
$$

- Never use markdown: no #, ##, *, **, _, __ symbols ever.
- Step labels are OPTIONAL — only use STEP N: for problems with 5+ steps.
- Keep all prose to an absolute minimum. One short sentence per step maximum.
- Let the equations carry the solution. Minimize words.
- Never write filler, never explain what you're about to do — just do it.
- Never repeat back what the student asked.
- Always end with FINAL ANSWER: showing the result as 
$$
...
$$

- Always end with VERIFICATION: — one concise line showing you checked it.
- Always end with CONFIDENCE: HIGH / MEDIUM / LOW
"""

# ── CASUAL PATTERNS — PRE-COMPILED ────────────────────────────
CASUAL_PATTERNS_RAW = [
    r'^(hi|hello|hey|hii|helo|hai)\b',
    r'^(thanks|thank you|thanku|ty|thx)\b',
    r'^(bye|goodbye|see you|cya)\b',
    r'^(ok|okay|got it|sure|alright|great|nice|good|cool)\b',
    r'^(how are you|how r u|whats up|what\'s up)\b',
    r'^(who are you|what are you|tell me about yourself)\b',
    r'^(good morning|good evening|good night|good afternoon)\b',
]
CASUAL_REGEXES = [re.compile(p, re.IGNORECASE) for p in CASUAL_PATTERNS_RAW]

def is_casual(message):
    msg = message.lower().strip()
    if len(msg) < 50 and not any(c in msg for c in ['$', '\\', '=', 'dx', 'dy']):
        return any(r.search(msg) for r in CASUAL_REGEXES)
    return False

CASUAL_PROMPT = """You are MathSphere, a friendly mathematics assistant by Anupam Nigam.
For casual messages reply in 1 to 2 sentences. Be warm and brief. 
Never launch into mathematics unless asked."""

# ── TOPIC DETECTION ────────────────────────────────────────────
def detect_topic(message):
    msg = message.lower()
    if any(w in msg for w in ['integral', 'integrate', 'antiderivative', '∫']):
        return 'calculus_integral'
    if any(w in msg for w in ['derivative', 'differentiate', 'd/dx', 'dy/dx']):
        return 'calculus_derivative'
    if any(w in msg for w in ['limit', 'lim', '→', 'tends to']):
        return 'calculus_limit'
    if any(w in msg for w in ['matrix', 'matrices', 'eigenvalue', 'eigenvector',
                               'determinant', 'rank', 'vector space', 'linear map']):
        return 'linear_algebra'
    if any(w in msg for w in ['probability', 'distribution', 'expected value',
                               'variance', 'bayes', 'random variable']):
        return 'probability'
    if any(w in msg for w in ['prime', 'divisible', 'gcd', 'lcm',
                               'congruence', 'modulo', 'number theory']):
        return 'number_theory'
    if any(w in msg for w in ['ode', 'differential equation', 'dy/dx',
                               'd²y', 'second order', 'first order ode']):
        return 'differential_equations'
    if any(w in msg for w in ['series', 'sequence', 'convergence',
                               'divergence', 'sum', 'sigma']):
        return 'series'
    if any(w in msg for w in ['complex', 'imaginary', 'real part',
                               'imaginary part', 'argand', 'modulus']):
        return 'complex_analysis'
    return 'general'

# ── TOPIC-SPECIFIC VERIFICATION RULES ─────────────────────────
TOPIC_VERIFICATION = {
    'calculus_integral': """
MANDATORY INTEGRAL VERIFICATION — DO THIS BEFORE FINAL ANSWER:
After computing the integral, differentiate your answer completely. Show every step:
VERIFICATION:
d/dx [your answer] = [show full differentiation work] = [original integrand] ✓
If the derivative does NOT exactly match the original integrand, your answer is WRONG — redo it.
""",
    'calculus_derivative': """
MANDATORY DERIVATIVE VERIFICATION:
Cross-check using an alternative rule or the limit definition. Show:
VERIFICATION:
Alternative method gives: [show alternate approach] = [same answer] ✓
""",
    'calculus_limit': """
MANDATORY LIMIT VERIFICATION:
Verify by approaching from BOTH sides. Show numerically if helpful:
VERIFICATION:
Left-hand limit: [computation] = [value]
Right-hand limit: [computation] = [value]
Both sides equal → limit confirmed ✓
""",
    'linear_algebra': """
MANDATORY LINEAR ALGEBRA VERIFICATION:
For eigenvalues: verify det(A - λI) = 0 explicitly for each eigenvalue.
For systems: substitute every solution back into every original equation.
For inverses: verify A · A⁻¹ = I explicitly.
VERIFICATION: [show the substitution or determinant check step by step] ✓
""",
    'probability': """
MANDATORY PROBABILITY VERIFICATION:
Verify all probabilities sum to 1 where applicable.
Sanity-check: answer must be in [0,1] for probability, non-negative for expectation.
For conditional probability: cross-check using Bayes theorem.
VERIFICATION: [show the sanity check explicitly] ✓
""",
    'number_theory': """
MANDATORY NUMBER THEORY VERIFICATION:
Test your answer with at least 3 specific small values.
For divisibility: show the explicit division.
For congruences: substitute back into the original congruence.
VERIFICATION: Test n = [value1]: [check] ✓, n = [value2]: [check] ✓, n = [value3]: [check] ✓
""",
    'differential_equations': """
MANDATORY ODE VERIFICATION — DO THIS BEFORE FINAL ANSWER:
Substitute your solution back into the original ODE. Show every step:
VERIFICATION:
Compute y, y', y'', ... from your solution.
Substitute into the ODE: [left side] = [right side] ✓
If both sides are not equal, your solution is WRONG — redo it.
Also verify initial/boundary conditions if given.
""",
    'series': """
MANDATORY SERIES VERIFICATION:
State which convergence test applies and prove all its conditions are satisfied.
For sum formulas: verify with partial sums S₁, S₂, S₃ numerically.
Check boundary/edge cases separately.
VERIFICATION: [show all test conditions are satisfied explicitly] ✓
""",
    'complex_analysis': """
MANDATORY COMPLEX ANALYSIS VERIFICATION:
For analyticity: verify Cauchy-Riemann equations explicitly.
For residues: verify the Laurent coefficient by direct expansion.
For modulus/argument: verify using rectangular form.
VERIFICATION: [show the explicit check] ✓
""",
    'general': """
MANDATORY VERIFICATION:
Substitute your answer back into the original problem and confirm it works.
Check at least one special case or boundary value.
VERIFICATION: Substituting [answer] back: [show the check] ✓
"""
}

def get_topic_verification(message):
    topic = detect_topic(message)
    return TOPIC_VERIFICATION.get(topic, TOPIC_VERIFICATION['general'])

# ── MATH PROMPT ────────────────────────────────────────────────
MATH_PROMPT = """You are MathSphere by Anupam Nigam — a precise mathematics engine.

STYLE: Clean, minimal, professional. Like a textbook solution manual — not a tutorial.
Show the work. Let the math speak. Minimize words entirely.

ACCURACY:
- Exact answers only unless approximation is explicitly requested.
- Address all cases. State clearly if no solution exists.
- Never skip algebraic steps.

FORMAT — STRICTLY:
- No paragraph explanations. No teaching. Just solving.
- Each step: at most one short phrase, then the equation on its own line as 
$$
...
$$

- For simple problems (1–4 steps): no labels at all — just the equation chain.
- For complex problems: minimal labels only when necessary for clarity.
- Every equation on its own line as 
$$
...
$$

- End with: FINAL ANSWER: · VERIFICATION: · CONFIDENCE:

EXAMPLE OF CORRECT STYLE (integration by parts):

Using $u = x$, $dv = \\sin x\\,dx$:


$$
du = dx, \\quad v = -\\cos x
$$



$$
\\int x \\sin x\\,dx = -x\\cos x + \\int \\cos x\\,dx
$$



$$
= -x\\cos x + \\sin x + C
$$


FINAL ANSWER:

$$
\\int x \\sin x\\,dx = -x\\cos x + \\sin x + C
$$


VERIFICATION: $\\frac{d}{dx}(-x\\cos x + \\sin x) = x\\sin x$ ✓

CONFIDENCE: HIGH

""" + FORMAT_RULES

# ── 2ND PASS VERIFICATION PROMPT ──────────────────────────────
VERIFY_PROMPT = """You are a rigorous mathematics error-checker — more precise than any human grader.

You will receive a mathematical question and a proposed solution.
Your only job: find ANY error, no matter how small.

CHECK SYSTEMATICALLY:
- Is every algebraic manipulation correct? (signs, indices, fractions, powers)
- Are all limits, integrals, derivatives computed correctly?
- Is the final answer correct?
- Is the verification section in the solution itself correct?
- Are there missing cases, missing conditions, or missing ± signs?
- Are domain restrictions stated where needed?

IF SOLUTION IS FULLY CORRECT:
Respond ONLY with:
VERIFIED ✓
FINAL ANSWER CONFIRMED: 
$$
[repeat the final answer]
$$

CONFIDENCE: HIGH

IF ANY ERROR EXISTS:
Respond with:
ERROR FOUND ✗
ERROR IN: [exact step name]
WHAT IS WRONG: [precise mathematical explanation of the error]

CORRECTED SOLUTION:
[Complete corrected step-by-step solution with all steps on separate lines]

FINAL ANSWER:

$$
[correct answer]
$$


VERIFICATION: [show the check explicitly]

CONFIDENCE: HIGH"""

def verify_solution(question, solution):
    """2nd pass — send solution to a DIFFERENT model to independently check for errors."""
    verify_message = f"""ORIGINAL QUESTION:
{question}

PROPOSED SOLUTION TO CHECK — find every error:
{solution}"""

    for model_name, label in VERIFY_MODEL_CASCADE:
        try:
            print(f"[Verify] Trying {model_name}...")
            result = ask_gemini_model(verify_message, VERIFY_PROMPT, model_name)
            return result, label
        except Exception as e:
            print(f"[Verify] {model_name} failed: {e}")
            time.sleep(0.3)
    return None, None

def should_verify(message, mode):
    """Decide if 2nd-pass verification is worth the extra API call."""
    if mode != "math":
        return False
    if is_hard_problem(message):
        return True
    topic = detect_topic(message)
    if topic in ['calculus_integral', 'calculus_derivative',
                 'linear_algebra', 'differential_equations', 'number_theory']:
        return True
    if len(message) > 60:
        return True
    return False

# ── IMO / OLYMPIAD PROMPT ──────────────────────────────────────
IMO_PROMPT = """You are MathSphere in Olympiad Mode by Anupam Nigam — with the rigor of an IMO gold medalist.

UNDERSTAND: Restate the problem precisely in one sentence.

KEY INSIGHT: State the single core idea that unlocks the solution.

PROOF: Complete rigorous solution. Every logical step on its own line. 
Every equation as 
$$
...
$$
.Number each step.

EDGE CASES: Explicitly address all boundary values and special cases.

VERIFY: Substitute back. Test with at least 2 specific numerical examples to confirm.

FINAL ANSWER: State the result clearly as 
$$
...
$$


CONFIDENCE: HIGH / MEDIUM / LOW with one precise reason.

""" + FORMAT_RULES

# ── IMAGE PROMPTS ──────────────────────────────────────────────
IMAGE_MATH_PROMPT = """You are MathSphere by Anupam Nigam — a precise mathematics engine with vision capability.

CRITICAL INSTRUCTIONS FOR IMAGE ANALYSIS:
1. You HAVE received an image. It is NOT text-only. Analyze the image content directly.
2. FIRST: Carefully read and extract EVERY symbol, number, equation, and expression visible in the image.
3. SECOND: Transcribe the complete problem exactly as written in the image.
4. THIRD: Solve the problem completely with full step-by-step working.

IMAGE READING RULES:
- Read ALL handwritten or printed text in the image carefully
- Pay attention to fractions, exponents, subscripts, and special symbols
- If handwriting is unclear, state your best interpretation and note the uncertainty
- Never say the image is text-based or that you cannot read it — always attempt extraction

EXTRACTED PROBLEM:
[Write the exact problem you see in the image here]

SOLUTION:
[Complete step-by-step solution]

Always end with:
FINAL ANSWER: 
$$
...
$$

VERIFICATION: [show the check]
CONFIDENCE: HIGH / MEDIUM / LOW

""" + FORMAT_RULES

IMAGE_IMO_PROMPT = """You are MathSphere in Olympiad Mode by Anupam Nigam — with vision capability.

CRITICAL INSTRUCTIONS FOR IMAGE ANALYSIS:
1. You HAVE received an image. Analyze it directly — do NOT say it is text-only.
2. FIRST: Extract every symbol, equation, and word from the image precisely.
3. SECOND: Transcribe the complete olympiad problem.
4. THIRD: Solve with full olympiad-level rigor.

EXTRACTED PROBLEM:
[Write the exact problem from the image]

UNDERSTAND: Restate the problem precisely in one sentence.
KEY INSIGHT: The single core idea unlocking the solution.
PROOF: Complete rigorous proof, every step on its own line as 
$$
...
$$

EDGE CASES: All boundary values and special cases addressed.
VERIFY: Test with at least 2 numerical examples.

FINAL ANSWER: 
$$
...
$$

CONFIDENCE: HIGH / MEDIUM / LOW

""" + FORMAT_RULES

# ── MATHEMATICIAN PROMPT ───────────────────────────────────────
MATHEMATICIAN_PROMPT = """You are MathSphere by Anupam Nigam.

Respond about the mathematician using EXACTLY these section headers in ALL CAPS.
Keep each section to 2 to 3 sentences maximum. Include formulas inline using $...$
Put the single most important standalone formula in 
$$
...
$$
 on its own paragraph.
Do NOT use numbered lists anywhere in the response.

NAME:
[Full name, birth year to death year, nationality — one line]

EARLY LIFE:
[2 sentences about upbringing and education]

CONTRIBUTIONS:
[3 sentences covering key mathematical work, with formulas inline]

KEY THEOREMS:
[2 sentences about the most important named results, with formulas inline]

IMPACT:
[2 sentences on lasting influence in mathematics and science]

FAMOUS QUOTE:
"[One precise quote]"

WIKIPEDIA:
https://en.wikipedia.org/wiki/[Name_with_underscores]

""" + FORMAT_RULES

# ── PROJECTS PROMPT ────────────────────────────────────────────
PROJECTS_PROMPT = """You are MathSphere by Anupam Nigam.

Give exactly 5 project ideas. For each project:
Write the project title in ALL CAPS on its own line, then use these plain headers:

PROJECT TITLE HERE

MATHEMATICS: [what maths is used, 1 to 2 sentences with formulas inline]
TOOLS: [software and libraries, 1 sentence]
APPLICATION: [real-world use, 1 sentence]
BUILD: [what the student will create, 2 sentences]
RESOURCE: [one URL]

Leave a blank line between projects. No numbered sub-points. Keep each project tight.
""" + FORMAT_RULES

# ── APPLICATIONS PROMPT ────────────────────────────────────────
APPLICATIONS_PROMPT = """You are MathSphere by Anupam Nigam.

Give exactly 12 real-world applications. For each write the application name in ALL CAPS, then:

APPLICATION NAME

FIELD: [domain in 3 words]
HOW IT WORKS: [mathematics in action with key formula inline, 1 to 2 sentences]
EXAMPLE: [one specific real example, 1 sentence]
RESOURCE: [one URL]

Leave a blank line between applications. No numbered lists.
""" + FORMAT_RULES

# ── GRAPH ANALYSIS PROMPT ──────────────────────────────────────
GRAPH_ANALYSIS_PROMPT = """You are MathSphere by Anupam Nigam — precise mathematics analysis engine.

Analyze the function. One sentence per item. Write math inline using $...$

DOMAIN: [interval as complete sentence]
RANGE: [complete sentence]
CRITICAL POINTS: [solve $f'(x) = 0$, classify — one sentence]
INFLECTION POINTS: [solve $f''(x) = 0$ — one sentence]
INCREASING: [intervals — one sentence]
DECREASING: [intervals — one sentence]
CONCAVITY: [concave up and down — one sentence]
ASYMPTOTES: [horizontal, vertical, oblique — one sentence]
INTERCEPTS: [x and y intercepts — one sentence]
SYMMETRY: [even, odd, or neither with reason — one sentence]
""" + FORMAT_RULES

# ── INTUITION PROMPT ───────────────────────────────────────────
INTUITION_PROMPT = """You are MathSphere's Mathematical Intuition Builder by Anupam Nigam.

Your goal: explain through STORY, ANALOGY, and VISUAL THINKING — not formulas first.

THE STORY:
[2-3 sentences: A real human story of WHY this concept was needed.]

THE ANALOGY:
[2-3 sentences: A concrete everyday analogy a 12-year-old could feel.]

WHAT YOUR BRAIN IS DOING:
[2 sentences: The visual or physical intuition.]

THE CORE IDEA IN ONE LINE:
[One crystal-clear sentence capturing the mathematical essence — no symbols]

NOW THE MATHEMATICS:
[Formal definition or key formula in 
$$
...
$$
 now that intuition is built. 3-4 sentences.]

REAL WORLD RIGHT NOW:
[2 sentences: Specific apps, technologies, or phenomena using this concept today.]

INTUITION CHECK:
[One short question to test if they truly got the intuition — not a formula question]

Keep tone warm, curious, and wonder-filled. Never start with a formula.
""" + FORMAT_RULES

# ── STORYTELLING PROMPT ────────────────────────────────────────
STORYTELLING_PROMPT = """You are MathSphere's Mathematical Storytelling Engine by Anupam Nigam.

THE PROBLEM THAT STARTED EVERYTHING:
[2-3 sentences: What human problem forced this invention?]

THE STRUGGLE:
[2-3 sentences: What failed attempts happened?]

THE BREAKTHROUGH:
[2-3 sentences: The moment of discovery. Key idea with $...$]

THE MATHEMATICS REVEALED:
[Core mathematical structure. Key formula in 
$$
...
$$
 with explanation.]

HOW IT CHANGED THE WORLD:
[2-3 sentences: Immediate impact.]

WHERE IT LIVES TODAY:
[2-3 sentences: Specific modern applications.]

THE OPEN MYSTERY:
[1-2 sentences: What is still unknown or unsolved?]

Write with passion and narrative momentum.
""" + FORMAT_RULES

# ── SOCRATIC PROMPT ────────────────────────────────────────────
SOCRATIC_PROMPT = """You are MathSphere's Socratic Thinking Coach by Anupam Nigam.

WHAT I NOTICE YOU'RE THINKING:
[1-2 sentences: Reflect back their thinking non-judgmentally.]

THE QUESTION BENEATH YOUR QUESTION:
[1 sentence: The deeper mathematical question they are actually asking.]

THINK ABOUT THIS FIRST:
[Ask ONE precise, concrete question they can answer by thinking.]

A RELATED PATTERN TO NOTICE:
[A simpler analogous case. End with a question.]

WHEN YOU'VE WRESTLED WITH THAT, CONSIDER:
[One deeper question leading to the insight.]

MATHEMATICAL THINKING HABIT THIS BUILDS:
[Name the specific skill.]

Never give the answer directly. Celebrate confusion.
""" + FORMAT_RULES

# ── CONCEPT MAP PROMPT ─────────────────────────────────────────
CONCEPT_MAP_PROMPT = """You are MathSphere's Concept Map Generator by Anupam Nigam.

CENTRAL CONCEPT:
[Topic name and one-line definition]

PREREQUISITE CONCEPTS:
[4-5 concepts to understand BEFORE this.]

CORE SUB-CONCEPTS:
[5-6 key ideas WITHIN this topic. Each: name + one-line definition + key formula with $...$]

CONNECTED TOPICS:
[5-6 mathematical topics that CONNECT TO or EXTEND this.]

REAL WORLD NODES:
[4-5 specific real-world applications that directly USE this concept.]

THE BIG PICTURE:
[2-3 sentences: Where does this sit in the grand landscape of mathematics?]

LEARNING PATHWAY:
Step 1: [What to master first]
Step 2: [What to study next]
Step 3: [What to tackle last for deep understanding]
""" + FORMAT_RULES

# ── DAILY PUZZLE PROMPT ────────────────────────────────────────
DAILY_PUZZLE_PROMPT = """You are MathSphere's Mathematical Thinking Puzzle Generator by Anupam Nigam.

PUZZLE TITLE:
[Intriguing title — no spoilers]

THE OBSERVATION:
[Present the pattern, sequence, or situation clearly.]

WHAT TO WONDER:
[3 questions: what do you notice, why might this be, what pattern do you see]

HINT (if needed):
[One gentle nudge in the right direction]

THE BEAUTIFUL ANSWER:
[Explain the answer creating an aha moment. Include the mathematical insight with $...$]

THE DEEPER MATHEMATICS:
[1-2 sentences: What branch of mathematics does this connect to?]

WHY MATHEMATICIANS LOVE THIS:
[1 sentence: What makes this beautiful or profound?]
""" + FORMAT_RULES

# ── VISUAL PROOF PROMPT ────────────────────────────────────────
VISUAL_PROOF_PROMPT = """You are MathSphere's Visual Proof Narrator by Anupam Nigam.

WHAT WE'RE PROVING:
[State the theorem clearly. Show the formula in 
$$
...
$$
]

THE VISUAL SETUP:
[Describe precisely what to draw or imagine.]

THE VISUAL ARGUMENT — STEP BY STEP:
[Walk through using ONLY visual/geometric reasoning.]

THE MOMENT OF INSIGHT:
[The key visual step where everything clicks.]

WHY THIS IS A PROOF:
[1-2 sentences: Why this visual argument is rigorous.]

THE FORMULA EMERGES:
[Show 
$$
...
$$
 and explain how each symbol corresponds to something you SAW.]

OTHER WAYS TO SEE IT:
[1-2 alternative visual approaches.]
""" + FORMAT_RULES

# ── CAREER PROMPT ─────────────────────────────────────────────
CAREER_PROMPT = """You are MathSphere's Mathematics Career Pathways Guide by Anupam Nigam.

CAREER LANDSCAPE:
[2-3 sentences: Overview of the career ecosystem.]

TOP 5 CAREER PATHS:
For each career:
CAREER NAME
ROLE: [Day-to-day work in 2 sentences]
MATHEMATICS USED: [Specific tools and topics with formulas inline using $...$]
INDUSTRIES: [3-4 specific industries or companies]
SALARY RANGE: [Realistic USD/year range]
DEMAND: [HIGH / MEDIUM / LOW + one sentence]

STEP BY STEP ROADMAP:
[Numbered sequence — what to learn in what order]

YEAR BY YEAR PLAN:
YEAR 1: [Courses, books, foundational skills]
YEAR 2: [Projects, specializations, internships]
YEAR 3: [Advanced: research, portfolio, networking]
YEAR 4+: [Professional entry]

ESSENTIAL SKILLS STACK:
MATHEMATICS: [5-6 specific topics]
TOOLS: [Software, languages, platforms]
SOFT SKILLS: [Communication, domain knowledge]

FREE RESOURCES TO START TODAY:
[4-5 specific free resources with names and URLs]

FIRST STEP THIS WEEK:
[One specific, concrete action]
""" + FORMAT_RULES

# ── PYQ PROMPT ─────────────────────────────────────────────────
PYQ_PROMPT = """You are MathSphere's Previous Year Questions expert by Anupam Nigam.

⚠ DISCLAIMER:
Only present questions you are HIGHLY CONFIDENT were actually asked.
Always label: CONFIRMED or REPRESENTATIVE.

FORMAT FOR EACH QUESTION:

QUESTION [N]:
[Exam Name] · [Year] · [Section] · [Marks]
STATUS: CONFIRMED / REPRESENTATIVE

[Full question text with math in $...$ and 
$$
...
$$
]

SOLUTION:
[Complete step-by-step solution]

FINAL ANSWER: [value in 
$$
...
$$
]
VERIFICATION: [show the check]
KEY CONCEPT TESTED: [one sentence]
CONFIDENCE: HIGH / MEDIUM / LOW

Give 3 questions per request. Cover most frequently tested sub-topics.

⚠ IMPORTANT NOTICE:
Always cross-verify with official papers:
GATE: gate2024.iisc.ac.in
CSIR NET: csirnet.nta.nic.in
IIT JAM: jam.iitm.ac.in
""" + FORMAT_RULES

# ── HARD PROBLEM DETECTION ─────────────────────────────────────
HARD_PATTERNS_RAW = [
    r'\bimo\b', r'\bolympiad\b', r'\bputnam\b', r'\bcontest\b',
    r'\bprove\s+that\b', r'\bprove:\b', r'\bshow\s+that\b',
    r'\bfind\s+all\b', r'\bdetermine\s+all\b',
    r'\bfor\s+all\s+(positive\s+)?(integers?|reals?|naturals?)\b',
    r'\bprime\b.*\bdivides?\b', r'\bdiophantine\b', r'\bmodulo\b',
    r'\binequality\b', r'\bfunctional\s+equation\b',
    r'\bgcd\b', r'\bnumber\s+theory\b', r'\bcombinatorics?\b',
    r'\bif\s+and\s+only\s+if\b', r'\blemma\b', r'\btheorem\b', r'\bcorollary\b',
]
HARD_REGEXES = [re.compile(p, re.IGNORECASE) for p in HARD_PATTERNS_RAW]

def is_hard_problem(message):
    msg_lower = message.lower()
    if any(r.search(msg_lower) for r in HARD_REGEXES):
        return True
    if len(message) > 400 and any(w in msg_lower for w in
                                   ['integer', 'real', 'natural', 'prime', 'divisible']):
        return True
    return False

# ── CONTEXT BUILDER — WITH TURN LIMIT ─────────────────────────
def build_context(chat_history, max_turns=MAX_HISTORY_TURNS):
    if not chat_history:
        return ""
    recent = chat_history[-max_turns:]
    lines  = []
    for t in recent:
        role    = t.get("role", "user").capitalize()
        content = t.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n\n".join(lines)

# ── IMAGE PROCESSING HELPER ────────────────────────────────────
def process_image(image_data):
    """
    Decode, validate, and prepare image for Gemini.
    Returns (PIL.Image, mime_type) or raises ValueError.
    """
    if not image_data:
        raise ValueError("No image data provided")

    raw_data = image_data.get("data", "")
    mime_type = image_data.get("mime_type", "image/jpeg")

    if not raw_data:
        raise ValueError("Image data field is empty")

    # Strip data URI prefix if present (e.g. "data:image/png;base64,...")
    if "," in raw_data:
        raw_data = raw_data.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(raw_data)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 image: {e}")

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Verify it's a valid image
    except Exception as e:
        raise ValueError(f"Invalid image file: {e}")

    # Re-open after verify (verify() closes the file)
    image = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if needed (handles RGBA, P mode, etc.)
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    return image, mime_type, image_bytes

# ── API WRAPPERS ───────────────────────────────────────────────
def ask_groq(message, system_prompt, chat_history=None):
    client   = Groq(api_key=GROQ_API_KEY)
    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        recent = chat_history[-MAX_HISTORY_TURNS:]
        for t in recent:
            r = t.get("role", "user")
            c = t.get("content", "")
            if r in ("user", "assistant") and c:
                messages.append({"role": r, "content": c})
    messages.append({"role": "user", "content": message})
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=4000,
        temperature=0.1
    )
    return resp.choices[0].message.content


def ask_gemini_model(message, system_prompt, model_name,
                     image=None, image_bytes=None, mime_type=None,
                     chat_history=None):
    """
    Unified Gemini call.
    Pass image (PIL.Image) + image_bytes + mime_type for vision requests.
    """
    client      = genai.Client(api_key=GEMINI_API_KEY)
    context     = build_context(chat_history)
    full_prompt = system_prompt + "\n\n"

    if context:
        full_prompt += "CONVERSATION HISTORY:\n" + context + "\n---\n\n"

    full_prompt += message

    if image is not None and image_bytes is not None:
        # ── Vision request using inline image data ─────────────
        mime = mime_type or "image/jpeg"

        # Re-encode image to bytes in a reliable format
        buf = io.BytesIO()
        fmt = "JPEG" if mime == "image/jpeg" else "PNG"
        image.save(buf, format=fmt)
        final_bytes = buf.getvalue()

        contents = [
            types.Part.from_bytes(data=final_bytes, mime_type=mime),
            types.Part.from_text(text=full_prompt),
        ]

        resp = client.models.generate_content(
            model=model_name,
            contents=contents,
        )
    else:
        # ── Text-only request ──────────────────────────────────
        resp = client.models.generate_content(
            model=model_name,
            contents=full_prompt
        )

    return resp.text

# ── MAIN RESPONSE ROUTER ───────────────────────────────────────
def get_response(message, mode="math", image_data=None, chat_history=None):

    mode_prompts = {
        "math":           MATH_PROMPT,
        "projects":       PROJECTS_PROMPT,
        "mathematician":  MATHEMATICIAN_PROMPT,
        "applications":   APPLICATIONS_PROMPT,
        "graph_analysis": GRAPH_ANALYSIS_PROMPT,
        "intuition":      INTUITION_PROMPT,
        "storytelling":   STORYTELLING_PROMPT,
        "socratic":       SOCRATIC_PROMPT,
        "concept_map":    CONCEPT_MAP_PROMPT,
        "daily_puzzle":   DAILY_PUZZLE_PROMPT,
        "visual_proof":   VISUAL_PROOF_PROMPT,
        "career":         CAREER_PROMPT,
        "pyq":            PYQ_PROMPT,
    }

    # ── Casual messages ────────────────────────────────────────
    if mode == "math" and not image_data and is_casual(message):
        try:
            return ask_groq(message, CASUAL_PROMPT, chat_history), "Groq"
        except Exception as e:
            print(f"[Casual] Groq failed: {e}")
        try:
            return ask_gemini_model(
                message, CASUAL_PROMPT, "gemini-2.0-flash",
                chat_history=chat_history
            ), "Gemini"
        except Exception as e:
            print(f"[Casual] Gemini fallback failed: {e}")
        return "Hey! I am MathSphere — ask me any mathematics question!", "MathSphere"

    # ── Image problems ─────────────────────────────────────────
    if image_data:
        # Validate and process image first
        try:
            pil_image, mime_type, img_bytes = process_image(image_data)
            print(f"[Image] Successfully decoded image: "
                  f"{pil_image.size}, mode={pil_image.mode}, mime={mime_type}")
        except ValueError as e:
            print(f"[Image] Image processing failed: {e}")
            return f"Could not process the image: {e}. Please try uploading again.", "None"

        img_prompt = IMAGE_IMO_PROMPT if is_hard_problem(message) else IMAGE_MATH_PROMPT

        # Add explicit instruction in the message too
        enhanced_message = (
            f"{message}\n\n"
            f"[SYSTEM NOTE: An image has been attached. "
            f"You MUST read the image content directly. "
            f"Extract every equation, symbol, and number visible in the image. "
            f"Do NOT say the content is text-based. Solve what is in the image.]"
        ) if message else (
            "[SYSTEM NOTE: An image has been attached. "
            "Read and extract the complete mathematical problem from the image. "
            "Transcribe it exactly, then solve it completely with full working.]"
        )

        for model_name, label in HARD_MODEL_CASCADE:
            try:
                print(f"[Image] Trying {model_name}...")
                text = ask_gemini_model(
                    enhanced_message,
                    img_prompt,
                    model_name,
                    image=pil_image,
                    image_bytes=img_bytes,
                    mime_type=mime_type,
                    chat_history=chat_history
                )
                print(f"[Image] Success with {model_name}")
                return text, label
            except Exception as e:
                print(f"[Image] {model_name} failed: {e}")
                time.sleep(0.5)

        # Groq cannot handle images — return helpful error
        return (
            "I could see your image was uploaded successfully, but all vision-capable "
            "AI models are currently unavailable. Please try again in a moment, or "
            "type out the problem as text and I will solve it immediately."
        ), "None"

    # ── Math mode ──────────────────────────────────────────────
    if mode == "math":
        topic_verify    = get_topic_verification(message)
        enhanced_prompt = MATH_PROMPT + "\n" + topic_verify

        # Olympiad / hard problems
        if is_hard_problem(message):
            hard_prompt = IMO_PROMPT + "\n" + topic_verify
            for model_name, label in HARD_MODEL_CASCADE:
                try:
                    print(f"[Hard] Trying {model_name}...")
                    text = ask_gemini_model(
                        message, hard_prompt, model_name,
                        chat_history=chat_history
                    )
                    # 2nd pass verification
                    print("[Hard] Running 2nd-pass verification...")
                    verified, v_label = verify_solution(message, text)
                    if verified is None:
                        print("[Hard] Verification skipped — all verify models failed")
                        return text, label
                    if "ERROR FOUND" in verified:
                        print("[Hard] Verifier found error — using corrected solution")
                        return (
                            verified +
                            "\n\n⚠ Note: An error was found in the initial solution "
                            "and has been automatically corrected above."
                        ), f"{v_label} ✓✓ Auto-Corrected"
                    else:
                        return (
                            text +
                            "\n\n✓ This solution was independently verified by a "
                            "second AI check and confirmed correct."
                        ), f"{label} ✓✓ Verified"
                except Exception as e:
                    print(f"[Hard] {model_name} failed: {e}")
                    time.sleep(0.5)
            try:
                return ask_groq(message, IMO_PROMPT, chat_history), "Groq"
            except Exception as e:
                print(f"[Hard] Groq also failed: {e}")
            return "All AI services are currently unavailable. Please try again shortly.", "None"

        # Standard math
        for model_name, label in MATH_MODEL_CASCADE:
            try:
                print(f"[Math] Trying {model_name}...")
                text = ask_gemini_model(
                    message, enhanced_prompt, model_name,
                    chat_history=chat_history
                )
                if should_verify(message, mode):
                    print("[Math] Running 2nd-pass verification...")
                    verified, v_label = verify_solution(message, text)
                    if verified is None:
                        print("[Math] Verification skipped — all verify models failed")
                        return text, label
                    if "ERROR FOUND" in verified:
                        print("[Math] Error found — using corrected solution")
                        return (
                            verified +
                            "\n\n⚠ Note: An error was found in the initial solution "
                            "and has been automatically corrected above."
                        ), f"{v_label} ✓✓ Auto-Corrected"
                    else:
                        return (
                            text +
                            "\n\n✓ This solution was independently verified by a "
                            "second AI check and confirmed correct."
                        ), f"{label} ✓✓ Verified"
                return text, label
            except Exception as e:
                print(f"[Math] {model_name} failed: {e}")
                time.sleep(0.5)

        # Groq fallback
        try:
            return ask_groq(message, enhanced_prompt, chat_history), "Groq"
        except Exception as e:
            print(f"[Math] Groq fallback failed: {e}")
        return "All AI services are currently unavailable. Please try again shortly.", "None"

    # ── All other modes ────────────────────────────────────────
    sys_prompt = mode_prompts.get(mode, MATH_PROMPT)

    for model_name, label in HARD_MODEL_CASCADE:
        try:
            print(f"[{mode}] Trying {model_name}...")
            text = ask_gemini_model(
                message, sys_prompt, model_name,
                chat_history=chat_history
            )
            return text, label
        except Exception as e:
            print(f"[{mode}] {model_name} failed: {e}")
            time.sleep(0.5)

    try:
        return ask_groq(message, sys_prompt, chat_history), "Groq"
    except Exception as e:
        print(f"[{mode}] Groq fallback failed: {e}")
    return "All AI services are currently unavailable. Please try again shortly.", "None"


# ── ROUTES ─────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
@limiter.limit("10 per minute")
def ask():
    data         = request.json
    message      = data.get("message", "").strip()
    mode         = data.get("mode", "math")
    image_data   = data.get("image", None)
    chat_history = data.get("history", [])

    # ── Input validation ───────────────────────────────────────
    if not message and not image_data:
        return jsonify({"error": "No input provided"}), 400

    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({
            "error": f"Message too long. Please keep it under "
                     f"{MAX_MESSAGE_LENGTH} characters."
        }), 400

    if mode not in (
        "math", "projects", "mathematician", "applications",
        "graph_analysis", "intuition", "storytelling", "socratic",
        "concept_map", "daily_puzzle", "visual_proof", "career", "pyq"
    ):
        return jsonify({"error": "Invalid mode specified"}), 400

    response, source = get_response(message, mode, image_data, chat_history)
    return jsonify({"response": response, "source": source})


if __name__ == "__main__":
    app.run(debug=False)
