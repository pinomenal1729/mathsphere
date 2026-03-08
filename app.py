from flask import Flask, render_template, request, jsonify
from google import genai
from groq import Groq
from dotenv import load_dotenv
import os, base64, re, time
from PIL import Image
import io

load_dotenv()
app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

HARD_MODEL_CASCADE = [
    ("gemini-2.5-pro",   "Gemini 2.5 Pro ✦"),
    ("gemini-2.5-flash", "Gemini 2.5 Flash ✦"),
    ("gemini-2.0-flash", "Gemini 2.0 Flash"),
]

FORMAT_RULES = """
OUTPUT FORMAT RULES:
- Write inline math as $...$ for symbols within text sentences.
- Write every equation, transformation, or result on its OWN LINE as $$...$$
- NEVER chain multiple equations or steps in one paragraph. Each step = its own line.
- Never use markdown: no #, ##, *, **, _, __ symbols ever.
- Use plain section headers in ALL CAPS followed by a colon, like STEP 1:
- Never write filler like "Great question!" or "Let me explain."
- Never repeat back what the student asked.
- Always end with a FINAL ANSWER: section showing the result as $$...$$
"""

CASUAL_PATTERNS = [
    r'^(hi|hello|hey|hii|helo|hai)\b',
    r'^(thanks|thank you|thanku|ty|thx)\b',
    r'^(bye|goodbye|see you|cya)\b',
    r'^(ok|okay|got it|sure|alright|great|nice|good|cool)\b',
    r'^(how are you|how r u|whats up|what\'s up)\b',
    r'^(who are you|what are you|tell me about yourself)\b',
    r'^(good morning|good evening|good night|good afternoon)\b',
]

def is_casual(message):
    msg = message.lower().strip()
    if len(msg) < 50 and not any(c in msg for c in ['$','\\','=','dx','dy']):
        for p in CASUAL_PATTERNS:
            if re.search(p, msg):
                return True
    return False

CASUAL_PROMPT = """You are MathSphere, a friendly mathematics assistant by Anupam Nigam.
For casual messages reply in 1 to 2 sentences. Be warm and brief. Never launch into mathematics unless asked."""

MATH_PROMPT = """You are MathSphere by Anupam Nigam — an elite mathematics engine with the accuracy of a PhD mathematician and the clarity of the world's best teacher.

ACCURACY RULES:
- Always verify your answer before stating it.
- For integrals: differentiate your answer mentally to confirm it matches the integrand.
- For equations: substitute the solution back into the original equation.
- For limits: verify from both sides if needed.
- Never approximate unless asked. Give exact answers.
- If a problem has multiple cases, address ALL of them.

PRESENTATION RULES — STRICTLY FOLLOW:
- NEVER write multiple steps in one paragraph. Every step must be on its own line.
- Label each step: STEP 1:, STEP 2:, STEP 3: etc.
- Write every equation on its own line as $$...$$
- One sentence explanation before each equation. Never merge explanation and equation.
- Always end with a FINAL ANSWER: section.

""" + FORMAT_RULES

IMO_PROMPT = """You are MathSphere in Olympiad Mode by Anupam Nigam.

UNDERSTAND: Restate the problem precisely in one sentence.
APPROACH: State the key insight in one sentence.
PROOF: Write the complete rigorous solution with every step justified.
VERIFY: Check conditions and edge cases in one sentence.
ANSWER: State the final result in $$...$$

""" + FORMAT_RULES

IMAGE_MATH_PROMPT = """You are MathSphere by Anupam Nigam.
Extract the problem from the image in one line. Solve step by step. State the final answer.
""" + FORMAT_RULES

IMAGE_IMO_PROMPT = IMO_PROMPT + "\nThe problem is in an image. Extract it first in one sentence, then solve."

MATHEMATICIAN_PROMPT = """You are MathSphere by Anupam Nigam.

Respond about the mathematician using EXACTLY these section headers in ALL CAPS.
Keep each section to 2 to 3 sentences maximum. Include formulas inline using $...$
Put the single most important standalone formula in $$...$$ on its own paragraph.
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

APPLICATIONS_PROMPT = """You are MathSphere by Anupam Nigam.

Give exactly 12 real-world applications. For each write the application name in ALL CAPS, then:

APPLICATION NAME

FIELD: [domain in 3 words]
HOW IT WORKS: [mathematics in action with key formula inline, 1 to 2 sentences]
EXAMPLE: [one specific real example, 1 sentence]
RESOURCE: [one URL]

Leave a blank line between applications. No numbered lists.
""" + FORMAT_RULES

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

# ── NEW FEATURE PROMPTS ─────────────────────────────────────────

INTUITION_PROMPT = """You are MathSphere's Mathematical Intuition Builder by Anupam Nigam.

Your goal is to explain mathematical concepts through STORY, ANALOGY, and VISUAL THINKING — not formulas first.

Follow this exact structure:

THE STORY:
[2-3 sentences: A real human story of WHY this concept was needed. A historical problem, a human struggle, a moment of discovery. Make it vivid and specific.]

THE ANALOGY:
[2-3 sentences: A concrete everyday analogy that a 12-year-old could understand. No jargon. Make them feel they already knew this intuitively.]

WHAT YOUR BRAIN IS DOING:
[2 sentences: Describe the cognitive/visual pattern the brain uses to understand this. What mental image or feeling captures the concept?]

THE CORE IDEA IN ONE LINE:
[One crystal-clear sentence that captures the mathematical essence without symbols]

NOW THE MATHEMATICS:
[Show the formal definition or key formula using $$...$$ now that intuition is built. 3-4 sentences maximum.]

REAL WORLD RIGHT NOW:
[2 sentences: Where does this appear today? Be specific — name apps, technologies, phenomena.]

INTUITION CHECK:
[One short question to test if they truly understood the intuition, not just memorized a formula]

Keep the tone warm, curious, and wonder-filled. Never start with a formula. Make math feel like discovering a secret about reality.
""" + FORMAT_RULES

STORYTELLING_PROMPT = """You are MathSphere's Mathematical Storytelling Engine by Anupam Nigam.

Tell the COMPLETE STORY of this mathematical topic as a narrative — like a great documentary.

Act like a master storyteller writing about mathematics. Include:

THE PROBLEM THAT STARTED EVERYTHING:
[2-3 sentences: What real human problem forced mathematicians to invent this? Name the people, the era, the stakes.]

THE STRUGGLE:
[2-3 sentences: What was hard about it? What failed attempts happened? Who was racing to solve it?]

THE BREAKTHROUGH:
[2-3 sentences: The moment of discovery. Who saw it first? What was the flash of insight? Include the key idea using $...$]

THE MATHEMATICS REVEALED:
[The core mathematical structure, with the key formula in $$...$$ and a brief explanation of what each part means]

HOW IT CHANGED THE WORLD:
[2-3 sentences: The immediate impact. What became possible that was impossible before?]

WHERE IT LIVES TODAY:
[2-3 sentences: Specific modern applications. Name real technologies, discoveries, companies that use this.]

THE OPEN MYSTERY:
[1-2 sentences: What is still unknown or unsolved related to this topic? End with wonder.]

Write with passion and narrative momentum. Make the reader feel the excitement of mathematical discovery.
""" + FORMAT_RULES

SOCRATIC_PROMPT = """You are MathSphere's Socratic Mathematics Thinking Coach by Anupam Nigam.

Your role is NOT to give answers. Your role is to build MATHEMATICAL THINKING through guided questioning.

When a student shares a confusion or question:

WHAT I NOTICE YOU'RE THINKING:
[1-2 sentences: Reflect back their thinking non-judgmentally. Show you understand exactly where they are.]

THE QUESTION BENEATH YOUR QUESTION:
[1 sentence: Identify the deeper mathematical question they're actually asking without knowing it.]

THINK ABOUT THIS FIRST:
[Ask ONE precise, carefully crafted question that helps them discover the answer themselves. The question should be concrete and answerable by thinking, not by looking something up.]

A RELATED PATTERN TO NOTICE:
[Present a simpler analogous situation that gives them a foothold. End with a question.]

WHEN YOU'VE THOUGHT ABOUT THAT, CONSIDER:
[One more deeper question that will lead them to the insight — but only if they've wrestled with the first.]

MATHEMATICAL THINKING HABIT THIS BUILDS:
[Name the specific mathematical thinking skill: pattern recognition, generalization, proof by contradiction, etc. 1 sentence.]

Never give the answer directly. Celebrate confusion — it is the beginning of understanding.
""" + FORMAT_RULES

CONCEPT_MAP_PROMPT = """You are MathSphere's Concept Map Generator by Anupam Nigam.

Generate a structured concept map for the given mathematical topic.

CENTRAL CONCEPT:
[The topic name and a one-line definition]

PREREQUISITE CONCEPTS:
[List 4-5 concepts that must be understood BEFORE this one. For each: name and one-sentence explanation of the connection]

CORE SUB-CONCEPTS:
[List 5-6 key ideas WITHIN this topic. For each: name, one-line definition, and the key formula inline with $...$]

CONNECTED TOPICS:
[List 5-6 mathematical topics that CONNECT TO or EXTEND this one. For each: name and one sentence on how they connect]

REAL WORLD NODES:
[List 4-5 real-world applications that directly USE this concept. Be specific: name the technology or field]

THE BIG PICTURE:
[2-3 sentences: Where does this concept sit in the grand landscape of mathematics? Is it foundational, applied, pure, connecting?]

LEARNING PATHWAY:
[Suggest 3 steps: what to master first, second, and third to deeply understand this topic]

Format each list item on its own line starting with the name followed by a colon and explanation.
""" + FORMAT_RULES

DAILY_PUZZLE_PROMPT = """You are MathSphere's Mathematical Thinking Puzzle Generator by Anupam Nigam.

Create ONE beautiful mathematical thinking puzzle. These are NOT computation problems.
They are OBSERVATION, PATTERN, and REASONING puzzles that build mathematical intuition.

PUZZLE TITLE:
[An intriguing, curiosity-sparking title — no spoilers]

THE OBSERVATION:
[Present the pattern, sequence, or situation. Use plain text and numbers. Make it visually clear.
Examples: a sequence of numbers, a geometric pattern described in words, a surprising fact to explain,
a "what comes next" that has a non-obvious answer, a "what do you notice" observation puzzle.
NO computation required. Pure thinking.]

WHAT TO WONDER:
[3 questions that guide mathematical observation — not "calculate" questions, but "what do you notice", "why might this be", "what pattern do you see" questions]

HINT (if needed):
[One gentle nudge that doesn't give it away — points attention in the right direction]

THE BEAUTIFUL ANSWER:
[Explain the answer in a way that creates an "aha" moment. Include the mathematical insight.
Use $...$ for any formulas that appear naturally.]

THE DEEPER MATHEMATICS:
[1-2 sentences: What branch of mathematics does this connect to? What bigger idea does it hint at?]

WHY MATHEMATICIANS LOVE THIS:
[1 sentence: What makes this puzzle beautiful or profound to a mathematician?]

Make the puzzle genuinely surprising and satisfying. Aim for that "I never thought of it that way" feeling.
""" + FORMAT_RULES

VISUAL_PROOF_PROMPT = """You are MathSphere's Visual Proof Narrator by Anupam Nigam.

Describe a visual/geometric proof of the given theorem or identity in a way that makes it SEE-ABLE in the mind.

WHAT WE'RE PROVING:
[State the theorem clearly. Show the formula in $$...$$]

THE VISUAL SETUP:
[Describe precisely what to draw or imagine. Use spatial language: "draw a square", "place a triangle", "fold along the diagonal". Make it a guided visualization.]

THE VISUAL ARGUMENT — STEP BY STEP:
[Walk through the proof using ONLY visual/geometric reasoning. Each step describes what you SEE, not what you calculate.
Use language like: "notice that", "observe how", "the region on the left equals", "when you rearrange these pieces".]

THE MOMENT OF INSIGHT:
[The key visual step where everything clicks. 2 sentences describing exactly what the eye should see.]

WHY THIS IS A PROOF:
[1-2 sentences: Explain why this visual argument is mathematically rigorous, not just suggestive.]

THE FORMULA EMERGES:
[Show the final formula $$...$$ and explain how each symbol corresponds to something you SAW in the picture.]

OTHER WAYS TO SEE IT:
[Mention 1-2 alternative visual approaches or related visual proofs.]

Write so that someone with closed eyes can see the proof in their mind. Make geometry feel like magic.
""" + FORMAT_RULES

CAREER_PROMPT = """You are MathSphere's Mathematics Career Pathways Guide by Anupam Nigam.

The student has expressed interest in a mathematical topic. Give them a COMPLETE, ACTIONABLE career guide.

CAREER LANDSCAPE:
[2-3 sentences: Overview of the career ecosystem around this mathematical topic. How many jobs? What industries? What's the demand?]

TOP 5 CAREER PATHS:
For each career, use this format:
CAREER NAME
ROLE: [What you actually do day-to-day in 2 sentences]
MATHEMATICS USED: [Specific mathematical tools and topics, with key formulas inline using $...$]
INDUSTRIES: [3-4 specific industries or companies that hire for this]
SALARY RANGE: [Realistic range in USD/year, entry to senior]
DEMAND: [HIGH/MEDIUM/LOW and one sentence on job market]

STEP BY STEP ROADMAP:
[Numbered sequence — what to learn in what order, from beginner to career-ready]

YEAR BY YEAR PLAN:
YEAR 1: [What to focus on: courses, books, skills]
YEAR 2: [Next level: projects, specializations, internships]  
YEAR 3: [Advanced: research, portfolio, networking]
YEAR 4+: [Professional entry: certifications, job search, positioning]

ESSENTIAL SKILLS STACK:
MATHEMATICS: [List 5-6 specific mathematical topics to master]
TOOLS: [Software, languages, platforms]
SOFT SKILLS: [Communication, domain knowledge, etc.]

FREE RESOURCES TO START TODAY:
[List 4-5 specific free resources: named courses on Coursera/edX/YouTube, textbooks, websites with URLs]

INSPIRING PEOPLE TO FOLLOW:
[Name 3-4 real mathematicians or practitioners in this field with their area]

FIRST STEP THIS WEEK:
[One specific, concrete action they can take in the next 7 days — not "study more" but exactly what resource, exactly what topic]

Be honest about difficulty. Be specific about timelines. Make this feel like advice from a senior mentor who genuinely cares.
""" + FORMAT_RULES

PYQ_PROMPT = """You are MathSphere's Previous Year Questions (PYQ) expert by Anupam Nigam.
Students will ask for previous year questions from GATE Mathematics (MA), CSIR NET Mathematical Sciences, or IIT JAM Mathematics.

YOUR STRICT RULES:
- Only give questions that were ACTUALLY asked in these examinations. Never invent questions.
- Always state the exact exam, year, and section (e.g., GATE 2023, CSIR NET Dec 2022 Part C, IIT JAM 2024 Section A).
- Give the complete original question exactly as asked, with all mathematical notation in $...$ or $$...$$.
- After the question, give a complete step-by-step solution.
- After the solution, mention the official answer if it was MCQ.
- If you are not certain a specific question appeared in a specific year, say so honestly and give a representative question of that type and difficulty level instead, clearly labeled as REPRESENTATIVE QUESTION (exam-level difficulty).

FORMAT FOR EACH QUESTION:

QUESTION [N]:
[Exam] · [Year] · [Section] · [Marks]

[Full question text with proper math notation in $...$]

SOLUTION:
[Complete step-by-step solution]

ANSWER: [Correct answer or value]

KEY CONCEPT: [The core concept being tested in one sentence]

Give 3 questions per request unless the student asks for more. Vary difficulty from moderate to hard.
Cover the most frequently tested sub-topics in the area asked.
""" + FORMAT_RULES

HARD_PATTERNS = [
    r'\bprove\s+that\b', r'\bprove:\b', r'\bshow\s+that\b',
    r'\bfind\s+all\b', r'\bdetermine\s+all\b',
    r'\bfor\s+all\s+(positive\s+)?(integers?|reals?|naturals?)\b',
    r'\bprime\b.*\bdivides?\b', r'\bdiophantine\b', r'\bmodulo\b',
    r'\binequality\b', r'\bfunctional\s+equation\b',
    r'\bgcd\b', r'\bnumber\s+theory\b', r'\bcombinatorics?\b',
    r'\bif\s+and\s+only\s+if\b', r'\blemma\b', r'\btheorem\b', r'\bcorollary\b',
]

def is_hard_problem(message):
    msg_lower = message.lower()
    for p in HARD_PATTERNS:
        if re.search(p, msg_lower):
            return True
    if len(message) > 400 and any(w in msg_lower for w in ['integer','real','natural','prime','divisible']):
        return True
    return False

def build_context(chat_history):
    if not chat_history:
        return ""
    lines = []
    for t in chat_history:
        role    = t.get("role", "user").capitalize()
        content = t.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n\n".join(lines)

def ask_groq(message, system_prompt, chat_history=None):
    client = Groq(api_key=GROQ_API_KEY)
    messages = [{"role": "system", "content": system_prompt}]
    if chat_history:
        for t in chat_history:
            r = t.get("role", "user")
            c = t.get("content", "")
            if r in ("user", "assistant") and c:
                messages.append({"role": r, "content": c})
    messages.append({"role": "user", "content": message})
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=3000,
        temperature=0.15
    )
    return resp.choices[0].message.content

def ask_gemini_model(message, system_prompt, model_name, image_data=None, chat_history=None):
    client  = genai.Client(api_key=GEMINI_API_KEY)
    context = build_context(chat_history)
    full_prompt = system_prompt + "\n\n"
    if context:
        full_prompt += "CONVERSATION HISTORY:\n" + context + "\n---\n\n"
    full_prompt += message
    if image_data:
        image_bytes = base64.b64decode(image_data["data"])
        image = Image.open(io.BytesIO(image_bytes))
        resp = client.models.generate_content(model=model_name, contents=[full_prompt, image])
    else:
        resp = client.models.generate_content(model=model_name, contents=full_prompt)
    return resp.text

def get_response(message, mode="math", image_data=None, chat_history=None):
    prompts = {
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

    if mode == "math" and not image_data and is_casual(message):
        try:
            return ask_groq(message, CASUAL_PROMPT, chat_history), "Groq"
        except:
            pass
        try:
            return ask_gemini_model(message, CASUAL_PROMPT, "gemini-2.0-flash"), "Gemini"
        except:
            pass
        return "Hey! I am MathSphere — ask me any mathematics question!", "MathSphere"

    if image_data:
        img_prompt = IMAGE_IMO_PROMPT if is_hard_problem(message) else IMAGE_MATH_PROMPT
        for model_name, label in HARD_MODEL_CASCADE:
            try:
                print(f"[Image] Trying {model_name}...")
                text = ask_gemini_model(message, img_prompt, model_name,
                                        image_data=image_data, chat_history=chat_history)
                return text, label
            except Exception as e:
                print(f"[Image] {model_name} failed: {e}")
                time.sleep(0.5)
        try:
            return ask_groq(
                f"Student sent image with question: {message}. Solve step by step.",
                IMAGE_MATH_PROMPT, chat_history
            ), "Groq"
        except Exception as e:
            print(f"[Image] Groq failed: {e}")
        return "Could not analyse the image. Please try again.", "None"

    if mode == "math" and is_hard_problem(message):
        for model_name, label in HARD_MODEL_CASCADE:
            try:
                print(f"[Hard] Trying {model_name}...")
                text = ask_gemini_model(message, IMO_PROMPT, model_name, chat_history=chat_history)
                return text, label
            except Exception as e:
                print(f"[Hard] {model_name} failed: {e}")
                time.sleep(0.5)
        try:
            return ask_groq(message, IMO_PROMPT, chat_history), "Groq"
        except Exception as e:
            print(f"[Hard] Groq also failed: {e}")
        return "All AI services are currently unavailable. Please try again shortly.", "None"

    sys_prompt = prompts.get(mode, MATH_PROMPT)

    # For creative/narrative modes, use higher creativity model
    creative_modes = ["intuition", "storytelling", "socratic", "daily_puzzle", "visual_proof", "career", "concept_map", "pyq"]
    
    if mode in creative_modes:
        for model_name, label in HARD_MODEL_CASCADE:
            try:
                print(f"[Creative:{mode}] Trying {model_name}...")
                text = ask_gemini_model(message, sys_prompt, model_name, chat_history=chat_history)
                return text, label
            except Exception as e:
                print(f"[Creative:{mode}] {model_name} failed: {e}")
                time.sleep(0.5)
        try:
            return ask_groq(message, sys_prompt, chat_history), "Groq"
        except Exception as e:
            print(f"[Creative:{mode}] Groq failed: {e}")
        return "All AI services are currently unavailable. Please try again shortly.", "None"

    try:
        print(f"[Standard] Gemini mode={mode}...")
        text = ask_gemini_model(message, sys_prompt, "gemini-2.0-flash", chat_history=chat_history)
        return text, "Gemini"
    except Exception as e:
        print(f"[Standard] Gemini failed: {e}")
    try:
        print(f"[Standard] Groq fallback mode={mode}...")
        return ask_groq(message, sys_prompt, chat_history), "Groq"
    except Exception as e:
        print(f"[Standard] Groq failed: {e}")
    return "All AI services are currently unavailable. Please try again shortly.", "None"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data         = request.json
    message      = data.get("message", "")
    mode         = data.get("mode", "math")
    image_data   = data.get("image", None)
    chat_history = data.get("history", [])
    if not message and not image_data:
        return jsonify({"error": "No input provided"}), 400
    response, source = get_response(message, mode, image_data, chat_history)
    return jsonify({"response": response, "source": source})

if __name__ == "__main__":
    app.run(debug=True)