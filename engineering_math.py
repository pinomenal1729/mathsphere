from flask import Blueprint, jsonify, request
from groq import Groq
from google import genai
from dotenv import load_dotenv
import os, time

load_dotenv()

eng_bp = Blueprint('engineering', __name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GROQ_MODEL     = "llama-3.3-70b-versatile"
GEMINI_CASCADE = [("gemini-2.5-flash", "Gemini 2.5 Flash"), ("gemini-2.0-flash", "Gemini 2.0 Flash")]

# ══════════════════════════════════════════════════════════════
#  SYLLABUS DATA — IIT pattern (Bombay / Delhi / Madras)
#  Used to render semester → topic → subtopic navigation
# ══════════════════════════════════════════════════════════════
SYLLABUS = {
    "sem1": {
        "label": "Semester 1",
        "subtitle": "Calculus & Series",
        "topics": {
            "diff_calc": {
                "label": "Differential Calculus",
                "subtopics": [
                    "Limits and Continuity",
                    "Differentiability",
                    "Rolle's Theorem",
                    "Lagrange's Mean Value Theorem",
                    "Cauchy's Mean Value Theorem",
                    "L'Hôpital's Rule",
                    "Taylor's Theorem",
                    "Maclaurin Series",
                    "Indeterminate Forms",
                    "Curvature and Radius of Curvature"
                ]
            },
            "partial_diff": {
                "label": "Partial Differentiation",
                "subtopics": [
                    "Functions of Several Variables",
                    "Partial Derivatives",
                    "Euler's Theorem on Homogeneous Functions",
                    "Total Derivative",
                    "Jacobians",
                    "Maxima and Minima of Two Variables",
                    "Lagrange's Method of Multipliers"
                ]
            },
            "integral_calc": {
                "label": "Integral Calculus",
                "subtopics": [
                    "Reduction Formulae",
                    "Beta and Gamma Functions",
                    "Double Integrals",
                    "Change of Order of Integration",
                    "Triple Integrals",
                    "Applications: Area, Volume, Surface Area",
                    "Improper Integrals"
                ]
            },
            "infinite_series": {
                "label": "Infinite Series",
                "subtopics": [
                    "Convergence and Divergence",
                    "Comparison Test",
                    "Ratio Test (D'Alembert)",
                    "Root Test (Cauchy)",
                    "Integral Test",
                    "Alternating Series and Leibniz Test",
                    "Absolute and Conditional Convergence",
                    "Power Series and Radius of Convergence"
                ]
            }
        }
    },
    "sem2": {
        "label": "Semester 2",
        "subtitle": "Linear Algebra & ODEs",
        "topics": {
            "linear_algebra": {
                "label": "Linear Algebra",
                "subtopics": [
                    "Matrices and Types",
                    "Rank of a Matrix",
                    "Echelon Form and Normal Form",
                    "System of Linear Equations",
                    "Eigenvalues and Eigenvectors",
                    "Cayley-Hamilton Theorem",
                    "Diagonalization",
                    "Quadratic Forms",
                    "Positive Definite Matrices"
                ]
            },
            "ode_first": {
                "label": "First Order ODEs",
                "subtopics": [
                    "Formation of ODEs",
                    "Variables Separable",
                    "Homogeneous Equations",
                    "Exact Differential Equations",
                    "Integrating Factors",
                    "Linear First Order ODEs",
                    "Bernoulli's Equation",
                    "Orthogonal Trajectories",
                    "Applications: Growth and Decay"
                ]
            },
            "ode_higher": {
                "label": "Higher Order ODEs",
                "subtopics": [
                    "Linear ODEs with Constant Coefficients",
                    "Complementary Function",
                    "Particular Integral",
                    "Method of Undetermined Coefficients",
                    "Variation of Parameters",
                    "Euler-Cauchy Equation",
                    "Simultaneous Linear ODEs",
                    "Applications: Simple Harmonic Motion"
                ]
            },
            "laplace": {
                "label": "Laplace Transforms",
                "subtopics": [
                    "Definition and Existence",
                    "Laplace Transforms of Standard Functions",
                    "Properties: Linearity, Shifting",
                    "Inverse Laplace Transform",
                    "Partial Fractions Method",
                    "Convolution Theorem",
                    "Solution of ODEs using Laplace",
                    "Unit Step and Dirac Delta Functions"
                ]
            }
        }
    },
    "sem3": {
        "label": "Semester 3",
        "subtitle": "Vector Calculus & Complex Analysis",
        "topics": {
            "vector_calc": {
                "label": "Vector Calculus",
                "subtopics": [
                    "Scalar and Vector Fields",
                    "Gradient and Directional Derivative",
                    "Divergence and Curl",
                    "Vector Identities",
                    "Line Integrals",
                    "Surface Integrals",
                    "Volume Integrals",
                    "Green's Theorem in the Plane",
                    "Stokes' Theorem",
                    "Gauss Divergence Theorem"
                ]
            },
            "complex_analysis": {
                "label": "Complex Analysis",
                "subtopics": [
                    "Complex Numbers Review",
                    "Functions of a Complex Variable",
                    "Analytic Functions",
                    "Cauchy-Riemann Equations",
                    "Harmonic Functions",
                    "Elementary Complex Functions",
                    "Complex Integration",
                    "Cauchy's Integral Theorem",
                    "Cauchy's Integral Formula",
                    "Taylor and Laurent Series",
                    "Singularities and Poles",
                    "Residue Theorem",
                    "Contour Integration"
                ]
            },
            "fourier_series": {
                "label": "Fourier Series",
                "subtopics": [
                    "Periodic Functions",
                    "Dirichlet Conditions",
                    "Euler's Formulae",
                    "Fourier Series of Even and Odd Functions",
                    "Half-Range Sine and Cosine Series",
                    "Parseval's Identity",
                    "Complex Form of Fourier Series",
                    "Practical Harmonic Analysis"
                ]
            }
        }
    },
    "sem4": {
        "label": "Semester 4",
        "subtitle": "Probability, Statistics & Numerical Methods",
        "topics": {
            "probability": {
                "label": "Probability & Statistics",
                "subtopics": [
                    "Random Variables",
                    "Probability Distributions",
                    "Binomial Distribution",
                    "Poisson Distribution",
                    "Normal Distribution",
                    "Expectation and Variance",
                    "Joint Distributions",
                    "Correlation and Regression",
                    "Chi-Square Distribution",
                    "Hypothesis Testing",
                    "t-Test and F-Test",
                    "Sampling Theory"
                ]
            },
            "numerical": {
                "label": "Numerical Methods",
                "subtopics": [
                    "Errors and Approximations",
                    "Bisection Method",
                    "Regula-Falsi Method",
                    "Newton-Raphson Method",
                    "Newton's Forward Interpolation",
                    "Newton's Backward Interpolation",
                    "Lagrange Interpolation",
                    "Numerical Differentiation",
                    "Trapezoidal Rule",
                    "Simpson's 1/3 Rule",
                    "Simpson's 3/8 Rule",
                    "Euler's Method for ODEs",
                    "Runge-Kutta Method (RK4)"
                ]
            },
            "transforms": {
                "label": "Transform Theory",
                "subtopics": [
                    "Fourier Integral Theorem",
                    "Fourier Transform",
                    "Fourier Sine and Cosine Transforms",
                    "Convolution Theorem for Fourier",
                    "Z-Transform Definition",
                    "Z-Transform Properties",
                    "Inverse Z-Transform",
                    "Solution of Difference Equations"
                ]
            }
        }
    }
}

# ══════════════════════════════════════════════════════════════
#  HARDCODED REFERENCES — never AI-generated, never broken
# ══════════════════════════════════════════════════════════════
REFERENCES = {
    "diff_calc":       ["https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/","https://www.khanacademy.org/math/calculus-1","https://tutorial.math.lamar.edu/Classes/CalcI/CalcI.aspx","https://mathworld.wolfram.com/Calculus.html"],
    "partial_diff":    ["https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/","https://www.khanacademy.org/math/multivariable-calculus","https://tutorial.math.lamar.edu/Classes/CalcIII/CalcIII.aspx","https://mathworld.wolfram.com/PartialDerivative.html"],
    "integral_calc":   ["https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/","https://www.khanacademy.org/math/integral-calculus","https://tutorial.math.lamar.edu/Classes/CalcII/CalcII.aspx","https://mathworld.wolfram.com/Integral.html"],
    "infinite_series": ["https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/","https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new","https://tutorial.math.lamar.edu/Classes/CalcII/SeriesIntro.aspx","https://mathworld.wolfram.com/Series.html"],
    "linear_algebra":  ["https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/","https://www.khanacademy.org/math/linear-algebra","https://www.3blue1brown.com/topics/linear-algebra","https://mathworld.wolfram.com/LinearAlgebra.html"],
    "ode_first":       ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","https://www.khanacademy.org/math/differential-equations","https://tutorial.math.lamar.edu/Classes/DE/DE.aspx","https://mathworld.wolfram.com/OrdinaryDifferentialEquation.html"],
    "ode_higher":      ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","https://tutorial.math.lamar.edu/Classes/DE/SecondOrderConcepts.aspx","https://www.khanacademy.org/math/differential-equations","https://mathworld.wolfram.com/SecondOrderOrdinaryDifferentialEquation.html"],
    "laplace":         ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","https://tutorial.math.lamar.edu/Classes/DE/LaplaceIntro.aspx","https://www.khanacademy.org/math/differential-equations/laplace-transform","https://mathworld.wolfram.com/LaplaceTransform.html"],
    "vector_calc":     ["https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/","https://www.khanacademy.org/math/multivariable-calculus","https://tutorial.math.lamar.edu/Classes/CalcIII/VectorFields.aspx","https://mathworld.wolfram.com/VectorCalculus.html"],
    "complex_analysis":["https://ocw.mit.edu/courses/18-04-complex-variables-with-applications-spring-2018/","https://mathworld.wolfram.com/ComplexAnalysis.html","https://www.youtube.com/playlist?list=PLBh2i93oe2qvRGAtgkTszX7szZDVd6jh1","https://nptel.ac.in/courses/111/106/111106084/"],
    "fourier_series":  ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","https://www.khanacademy.org/science/electrical-engineering/ee-signals","https://mathworld.wolfram.com/FourierSeries.html","https://nptel.ac.in/courses/111/104/111104092/"],
    "probability":     ["https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/","https://www.khanacademy.org/math/statistics-probability","https://www.probabilitycourse.com/","https://mathworld.wolfram.com/Probability.html"],
    "numerical":       ["https://ocw.mit.edu/courses/18-330-introduction-to-numerical-analysis-spring-2012/","https://nptel.ac.in/courses/111/107/111107105/","https://mathworld.wolfram.com/NumericalAnalysis.html","https://tutorial.math.lamar.edu/Extras/AlgebraTrigReview/AlgebraTrigReview.aspx"],
    "transforms":      ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","https://www.khanacademy.org/science/electrical-engineering/ee-signals","https://mathworld.wolfram.com/FourierTransform.html","https://nptel.ac.in/courses/111/104/111104090/"]
}

# ══════════════════════════════════════════════════════════════
#  FORMAT RULES — engineering context
# ══════════════════════════════════════════════════════════════
ENG_FORMAT = """
OUTPUT FORMAT RULES — STRICTLY FOLLOW:
- Write inline math as $...$ and standalone equations on their own line as $$...$$
- NEVER put $...$ math on the same line as an ALL-CAPS section header
- Math always goes on a NEW LINE below the section header
- Use ALL-CAPS section headers followed by colon: SECTION NAME:
- Never use markdown: no **, *, #, __ ever
- Always end with REFERENCES: section (provided separately, do not fabricate URLs)
- College exam level only — no competition mathematics
- Include at least 2 fully worked numerical examples per response
- Every theorem must state: Name, Statement, Conditions, Proof sketch
"""

ENG_CONTEXT = """You are MathSphere Engineering by Anupam Nigam.
You are teaching B.Tech engineering students in India (IIT/NIT/Mumbai University/VTU/Anna University level).
Difficulty: College examination level — not JEE, not GATE, not competitive. Semester exam standard.
Style: Clear, precise, like a brilliant IIT professor explaining to first/second year students.
Always use engineering applications and examples where possible.
Never oversimplify — students are capable — but never go beyond syllabus scope.
"""

# ══════════════════════════════════════════════════════════════
#  TOPIC-SPECIFIC PROMPTS
# ══════════════════════════════════════════════════════════════
def build_learn_prompt(topic_key, subtopic, section):
    sections = {
        "definition": f"""Give the complete formal definition of {subtopic} for engineering mathematics.

DEFINITION:
[Precise mathematical definition. Every symbol explained.]

INTUITION:
[1-2 sentences: what this concept physically or geometrically means]

NOTATION:
[Standard notation used in Indian university examinations]

KEY CONDITIONS:
[When this definition applies. Edge cases and exceptions.]

SIMPLE EXAMPLE:
[One concrete numerical example illustrating the definition]
""",
        "theorem": f"""State and explain all major theorems related to {subtopic} in engineering mathematics.

For EACH theorem use this exact structure:

THEOREM NAME:
[Full name of the theorem]

STATEMENT:
[Precise mathematical statement]

CONDITIONS:
[Hypothesis — what must be true for the theorem to apply]

PROOF:
[Complete step-by-step proof. Every step on its own line. Every equation as $$...$$]

GEOMETRIC MEANING:
[What the theorem says visually or physically]

COROLLARY:
[Important results that follow directly]
""",
        "examples": f"""Provide 5 fully worked examples on {subtopic} at engineering university examination level.

For EACH example:

EXAMPLE [N] — [difficulty: Easy/Medium/Hard]:
[State the problem clearly]

SOLUTION:
[Complete step-by-step solution. Every equation as $$...$$. No steps skipped.]

FINAL ANSWER:
$$[answer]$$

KEY TECHNIQUE USED:
[Name the exact method applied]

COMMON MISTAKE TO AVOID:
[One typical error students make in this type of problem]

Cover: 2 easy, 2 medium, 1 hard example. Range from straightforward application to slightly tricky.
""",
        "practice": f"""Generate 8 practice problems on {subtopic} for engineering examination preparation.

Include:
- 3 short answer questions (2 marks each)
- 3 medium questions (4 marks each)  
- 2 long questions (6-8 marks each)

For each problem:

PROBLEM [N] ([marks] marks):
[Clear problem statement. All equations as $$...$$]

HINT:
[One line pointing in the right direction without giving the answer]

ANSWER:
$$[final answer only — no working]$$

Range from direct formula application to multi-step problems requiring synthesis.
University examination style — same pattern as Mumbai University / VTU / Anna University papers.
"""
    }
    return ENG_CONTEXT + "\n" + ENG_FORMAT + "\n\n" + sections.get(section, sections["definition"])

def build_revision_prompt(topic_key, subtopic):
    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Give a comprehensive quick revision summary of {subtopic} for engineering examination.
This is a revision sheet — bullet points only, no lengthy explanations.

KEY FORMULAS:
[Every important formula. Each on its own line as $$...$$]

IMPORTANT RESULTS:
- [Result 1]
- [Result 2]
- [Result 3 etc.]

STANDARD RESULTS TO MEMORISE:
[5-8 results that appear most frequently in university examinations]
$$[formula 1]$$
$$[formula 2]$$
[etc.]

QUICK TRICKS:
- [Trick 1 for fast solving]
- [Trick 2]
- [Trick 3]

COMMON MISTAKES:
- [Mistake 1]
- [Mistake 2]
- [Mistake 3]

EXAM TIPS:
- [What questions look like in university papers]
- [How to present solutions for full marks]
- [Time management tip]

MUST-KNOW THEOREMS:
[Name each theorem and its one-line statement. No proof needed here.]
"""

def build_pyq_prompt(topic_key, subtopic, university, difficulty):
    diff_map = {"easy": "2-4 mark straightforward application", "medium": "4-6 mark multi-step problems", "hard": "6-10 mark long answer questions requiring proof or derivation"}
    diff_desc = diff_map.get(difficulty, diff_map["medium"])

    univ_map = {
        "all": "various Indian universities (Mumbai University, VTU Bangalore, Anna University Chennai, AKTU Lucknow, Pune University, GTU Gujarat, JNTU Hyderabad)",
        "mumbai": "University of Mumbai (BE First Year)",
        "vtu": "Visvesvaraya Technological University (VTU) Bangalore",
        "anna": "Anna University Chennai (B.E/B.Tech)",
        "aktu": "AKTU (Dr. APJ Abdul Kalam Technical University) Lucknow",
        "abroad": "international universities (University of Cambridge, MIT OCW style, University of Toronto examination style)"
    }
    univ_desc = univ_map.get(university, univ_map["all"])

    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Provide 5 previous year examination questions on {subtopic} from {univ_desc}.
Difficulty level: {diff_desc}

For EACH question use this EXACT structure:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUESTION [N]:
[Exam] · [University] · [Approximate Year] · [[marks] Marks]

STATUS: CONFIRMED / REPRESENTATIVE
(CONFIRMED = you are certain this appeared; REPRESENTATIVE = typical exam-level question)

QUESTION TEXT:
[Full question. Every equation as $$...$$]

APPROACH:
[1-2 sentences: which technique/theorem to apply and why]

COMPLETE SOLUTION:
[Step-by-step. Every equation on its own line as $$...$$. No steps skipped.]

FINAL ANSWER:
$$[answer]$$

VERIFICATION:
[Show the check]

MARKS BREAKDOWN:
[How marks would typically be awarded: setup X marks, working Y marks, answer Z marks]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After all 5 questions:

TOPIC ANALYSIS:
[2-3 sentences: how frequently this topic appears, what types of questions are most common]

PREPARATION STRATEGY:
[3 bullet points: what to focus on for maximum marks]

⚠ Note: AI may occasionally reconstruct questions. Always cross-verify with official university question papers.
"""

def build_mocktest_prompt(topic_key, subtopic, num_q, marks_each):
    total = int(num_q) * int(marks_each)
    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Generate a complete mock test paper on {subtopic}.
Total questions: {num_q}
Marks per question: {marks_each}
Total marks: {total}
Time suggested: {int(num_q) * int(marks_each) * 2} minutes

Follow university examination paper format exactly.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MOCK TEST — {subtopic.upper()}
Total Marks: {total} | Time: {int(num_q) * int(marks_each) * 2} minutes
Instructions: Attempt ALL questions. Show complete working for full marks.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For EACH question:

QUESTION [N]: ({marks_each} Marks)
[Question with all equations as $$...$$]

Distribute difficulty as: 40% easy, 40% medium, 20% hard.
Mix: direct formula application, proof-based, application-based.

After all questions:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPLETE SOLUTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOLUTION [N]:
[Complete step-by-step working. Every equation as $$...$$]
FINAL ANSWER: $$[answer]$$
MARKS BREAKDOWN: [how {marks_each} marks are awarded]

At the end:
SELF-ASSESSMENT GUIDE:
[Score ranges and what they mean. What to revise if score is low.]
"""

def build_ask_prompt(question):
    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
A B.Tech engineering student asks: {question}

Answer at college examination level.
Show all working. Every equation on its own line as $$...$$
Include at least one worked example.
End with CONFIDENCE: HIGH / MEDIUM / LOW
"""

# ══════════════════════════════════════════════════════════════
#  API HELPERS
# ══════════════════════════════════════════════════════════════
def call_groq(prompt, system):
    client = Groq(api_key=GROQ_API_KEY)
    truncated = system[:3000] if len(system) > 3000 else system
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role":"system","content":truncated},{"role":"user","content":prompt}],
        max_tokens=4000,
        temperature=0.1
    )
    return resp.choices[0].message.content

def call_gemini(prompt, model_name):
    client = genai.Client(api_key=GEMINI_API_KEY)
    resp = client.models.generate_content(model=model_name, contents=prompt)
    return resp.text

def get_eng_response(full_prompt):
    try:
        return call_groq(full_prompt, ""), "Groq"
    except Exception as e:
        print(f"[Eng] Groq failed: {e}")
    for model_name, label in GEMINI_CASCADE:
        try:
            return call_gemini(full_prompt, model_name), label
        except Exception as e:
            print(f"[Eng] {model_name} failed: {e}")
            time.sleep(0.2)
    return "Service temporarily unavailable. Please try again.", "None"

# ══════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════
@eng_bp.route("/eng/syllabus")
def get_syllabus():
    return jsonify(SYLLABUS)

@eng_bp.route("/eng/learn", methods=["POST"])
def learn():
    try:
        data     = request.json
        topic    = data.get("topic","")
        subtopic = data.get("subtopic","")
        section  = data.get("section","definition")
        prompt   = build_learn_prompt(topic, subtopic, section)
        response, source = get_eng_response(prompt)
        refs = REFERENCES.get(topic, [])
        return jsonify({"response": response, "source": source, "references": refs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/revision", methods=["POST"])
def revision():
    try:
        data     = request.json
        topic    = data.get("topic","")
        subtopic = data.get("subtopic","")
        prompt   = build_revision_prompt(topic, subtopic)
        response, source = get_eng_response(prompt)
        refs = REFERENCES.get(topic, [])
        return jsonify({"response": response, "source": source, "references": refs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/pyq", methods=["POST"])
def pyq():
    try:
        data       = request.json
        topic      = data.get("topic","")
        subtopic   = data.get("subtopic","")
        university = data.get("university","all")
        difficulty = data.get("difficulty","medium")
        prompt     = build_pyq_prompt(topic, subtopic, university, difficulty)
        response, source = get_eng_response(prompt)
        refs = REFERENCES.get(topic, [])
        return jsonify({"response": response, "source": source, "references": refs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/mocktest", methods=["POST"])
def mocktest():
    try:
        data       = request.json
        topic      = data.get("topic","")
        subtopic   = data.get("subtopic","")
        num_q      = data.get("num_questions","5")
        marks_each = data.get("marks_each","5")
        prompt     = build_mocktest_prompt(topic, subtopic, num_q, marks_each)
        response, source = get_eng_response(prompt)
        return jsonify({"response": response, "source": source})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/ask", methods=["POST"])
def ask_eng():
    try:
        data     = request.json
        question = data.get("question","")
        prompt   = build_ask_prompt(question)
        response, source = get_eng_response(prompt)
        return jsonify({"response": response, "source": source})
    except Exception as e:
        return jsonify({"error": str(e)}), 500