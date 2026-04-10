# ══════════════════════════════════════════════════════════════
#  MATHSPHERE ENGINEERING v3.0
#  By Anupam Nigam
#  100% FREE — Zero Rupees
#
#  Complete engineering mathematics + GATE/JAM/NET tutoring backend
#  For B.Tech students + Competitive exam aspirants
#  IIT/NIT/Mumbai University/VTU/Anna University + GATE/JAM/CSIR NET/NBHM
# ══════════════════════════════════════════════════════════════

from flask import Blueprint, jsonify, request
from groq import Groq
from google import genai
from dotenv import load_dotenv
import os, time, hashlib, threading, re, logging

load_dotenv()

# ══════════════════════════════════════════════════════════════
#  LOGGING SETUP
# ══════════════════════════════════════════════════════════════
logger = logging.getLogger("mathsphere.engineering")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)

# ══════════════════════════════════════════════════════════════
#  BLUEPRINT AND CONFIG
# ══════════════════════════════════════════════════════════════
eng_bp = Blueprint('engineering', __name__)

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
GROQ_MODEL      = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "8000"))
GEMINI_CASCADE  = [
    ("gemini-2.5-flash", "Gemini 2.5 Flash"),
    ("gemini-2.0-flash", "Gemini 2.0 Flash")
]

# ══════════════════════════════════════════════════════════════
#  MODULE-LEVEL CLIENTS — instantiated once, reused forever
# ══════════════════════════════════════════════════════════════
groq_client   = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ══════════════════════════════════════════════════════════════
#  THREAD-SAFE CACHE — saves API calls, zero cost
# ══════════════════════════════════════════════════════════════
_response_cache = {}
_cache_lock     = threading.Lock()
CACHE_MAX_SIZE  = 200
CACHE_TTL       = 86400  # 24 hours

def cache_key(prompt):
    return hashlib.sha256(prompt.encode()).hexdigest()

def get_cached(prompt):
    key = cache_key(prompt)
    with _cache_lock:
        if key in _response_cache:
            entry = _response_cache[key]
            age = time.time() - entry.get("created_at", 0)
            if age > CACHE_TTL:
                del _response_cache[key]
                logger.debug("Cache expired for key: %s", key[:12])
                return None, None
            entry["hits"] = entry.get("hits", 0) + 1
            return entry["response"], entry["source"] + " (cached)"
    return None, None

def set_cache(prompt, response, source):
    response_size = len(response.encode('utf-8'))
    if response_size > 100_000:
        logger.warning("Response too large to cache: %d bytes", response_size)
        return
    with _cache_lock:
        if len(_response_cache) >= CACHE_MAX_SIZE:
            # Evict least-used entry, but protect entries with age < 5 minutes
            now = time.time()
            eviction_candidates = {
                k: v for k, v in _response_cache.items()
                if now - v.get("created_at", 0) > 300
            }
            if eviction_candidates:
                min_key = min(eviction_candidates, key=lambda k: eviction_candidates[k].get("hits", 0))
            else:
                min_key = min(_response_cache, key=lambda k: _response_cache[k].get("hits", 0))
            del _response_cache[min_key]
        _response_cache[cache_key(prompt)] = {
            "response":   response,
            "source":     source,
            "hits":       0,
            "created_at": time.time()
        }

# ══════════════════════════════════════════════════════════════
#  THREAD-SAFE RATE LIMITER — protects free API quota
# ══════════════════════════════════════════════════════════════
_rate_data = {}
_rate_lock = threading.Lock()

def _get_client_ip():
    """Get client IP with proxy support"""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP", "")
    if real_ip:
        return real_ip.strip()
    return request.remote_addr or "unknown"

def check_rate_limit(max_per_minute=6):
    ip = _get_client_ip()
    now = time.time()
    with _rate_lock:
        if ip not in _rate_data:
            _rate_data[ip] = []
        _rate_data[ip] = [t for t in _rate_data[ip] if now - t < 60]
        if len(_rate_data) > 2000:
            oldest_ip = min(_rate_data, key=lambda k: max(_rate_data[k]) if _rate_data[k] else 0)
            if oldest_ip != ip:
                del _rate_data[oldest_ip]
        if len(_rate_data[ip]) >= max_per_minute:
            return False
        _rate_data[ip].append(now)
        return True

def rate_limit_response():
    return jsonify({
        "error": "Please wait a moment before trying again. This helps keep the service free for everyone."
    }), 429

# ══════════════════════════════════════════════════════════════
#  INPUT SANITIZATION — prevents prompt injection
# ══════════════════════════════════════════════════════════════
def sanitize_input(text, max_length=2000):
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if not text:
        return ""
    text = text[:max_length]
    bad_patterns = [
        r"ignore\s+(all\s+)?previous",
        r"disregard\s+(all\s+)?above",
        r"you\s+are\s+now",
        r"new\s+instructions",
        r"system\s*prompt",
        r"pretend\s+you\s+are",
        r"override\s+instructions",
        r"forget\s+(all\s+)?previous",
        r"<\|.*?\|>",
        r"$$INST$$.*?$$/INST$$",  # FIXED: was using $$ which means end-of-string
        r"$$SYSTEM$$.*?$$/SYSTEM$$",
        r"<system>.*?</system>",
    ]
    for pattern in bad_patterns:
        text = re.sub(pattern, "[removed]", text, flags=re.IGNORECASE | re.DOTALL)
    return text

# ══════════════════════════════════════════════════════════════
#  INPUT VALIDATION HELPERS
# ══════════════════════════════════════════════════════════════
def validate_json(*required_fields):
    data = request.get_json(force=True, silent=True)
    if not data:
        return None, jsonify({"error": "Request body must be valid JSON"}), 400
    missing = [f for f in required_fields if not str(data.get(f, "")).strip()]
    if missing:
        return None, jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    return data, None, None

def validate_positive_int(value, field_name, min_val=1, max_val=100, default=5):
    """Safely parse and validate integer input"""
    try:
        val = int(value)
        if val < min_val:
            return min_val
        if val > max_val:
            return max_val
        return val
    except (ValueError, TypeError):
        return default

def validate_topic_key(topic_key):
    """Check if topic_key exists in SYLLABUS"""
    for sem_data in SYLLABUS.values():
        if topic_key in sem_data["topics"]:
            return True
    return False

def get_topic_label(topic_key):
    """Get human-readable label for a topic key"""
    for sem_data in SYLLABUS.values():
        if topic_key in sem_data["topics"]:
            return sem_data["topics"][topic_key]["label"]
    return topic_key

# ══════════════════════════════════════════════════════════════
#  RESPONSE VALIDATION — don't cache garbage
# ══════════════════════════════════════════════════════════════
def is_valid_response(response):
    if not response or not isinstance(response, str):
        return False
    if len(response.strip()) < 100:
        return False
    bad_starts = [
        "i cannot", "i'm unable", "i don't", "as an ai",
        "error", "sorry, i", "i apologize"
    ]
    lower = response.strip().lower()
    for bad in bad_starts:
        if lower.startswith(bad):
            return False
    return True

# ══════════════════════════════════════════════════════════════
#  FORMULA KEY MAPPING — FIXED: maps SYLLABUS keys to FORMULA keys
# ══════════════════════════════════════════════════════════════
FORMULA_KEY_MAP = {
    "diff_calc":        "derivatives",
    "partial_diff":     "derivatives",
    "integral_calc":    "integrals",
    "infinite_series":  None,
    "linear_algebra":   None,
    "ode_first":        None,
    "ode_higher":       None,
    "laplace":          "laplace_transforms",
    "vector_calc":      "vector_identities",
    "complex_analysis": None,
    "fourier_series":   "fourier_series_formulas",
    "probability":      "probability_distributions",
    "numerical":        "numerical_formulas",
    "transforms":       "z_transforms",
}

def get_formula_count_for_topic(topic_key):
    """Get formula count using the mapping"""
    formula_key = FORMULA_KEY_MAP.get(topic_key)
    if formula_key and formula_key in QUICK_FORMULAS:
        return len(QUICK_FORMULAS[formula_key]["formulas"])
    return 0

# ══════════════════════════════════════════════════════════════
#  SYLLABUS DATA — IIT/NIT/Mumbai University/VTU pattern
# ══════════════════════════════════════════════════════════════
SYLLABUS = {
    "sem1": {
        "label": "Semester 1", "subtitle": "Calculus & Series",
        "topics": {
            "diff_calc": {
                "label": "Differential Calculus",
                "subtopics": [
                    "Limits: Definition and Basic Concepts",
                    "Algebra of Limits",
                    "Standard Limits",
                    "Left Hand and Right Hand Limits",
                    "Limits at Infinity",
                    "Sandwich Theorem",
                    "Continuity at a Point",
                    "Types of Discontinuities",
                    "Continuity on an Interval",
                    "Properties of Continuous Functions",
                    "Differentiability: First Principles",
                    "Differentiability vs Continuity",
                    "Rules of Differentiation",
                    "Chain Rule and Implicit Differentiation",
                    "Parametric Differentiation",
                    "Logarithmic Differentiation",
                    "Higher Order Derivatives",
                    "Rolle's Theorem: Statement and Verification",
                    "Lagrange's Mean Value Theorem",
                    "Cauchy's Mean Value Theorem",
                    "Geometric Interpretation of MVT",
                    "Indeterminate Form 0/0",
                    "Indeterminate Form inf/inf",
                    "Indeterminate Forms: 0 x inf, inf - inf",
                    "Indeterminate Forms: 1^inf, 0^0, inf^0",
                    "L'Hopital's Rule",
                    "Taylor's Theorem with Remainder",
                    "Maclaurin Series: sin x, cos x, e^x",
                    "Maclaurin Series: log(1+x), (1+x)^n",
                    "Applications of Taylor Series",
                    "Curvature: Definition and Formula",
                    "Radius of Curvature: Cartesian Form",
                    "Radius of Curvature: Parametric Form",
                    "Centre of Curvature and Evolute",
                ]
            },
            "partial_diff": {
                "label": "Partial Differentiation",
                "subtopics": [
                    "Functions of Two and Three Variables",
                    "Limits and Continuity for Functions of Two Variables",
                    "Partial Derivatives: First Order",
                    "Partial Derivatives: Second and Higher Order",
                    "Mixed Partial Derivatives and Clairaut's Theorem",
                    "Homogeneous Functions: Definition and Examples",
                    "Euler's Theorem on Homogeneous Functions",
                    "Extension of Euler's Theorem",
                    "Total Differential",
                    "Total Derivative: Chain Rule",
                    "Differentiation of Implicit Functions",
                    "Jacobian: Definition and Properties",
                    "Jacobian of Composite Functions",
                    "Jacobian: Change of Variables",
                    "Errors and Approximations using Differentials",
                    "Maxima and Minima: Critical Points",
                    "Second Derivative Test for Two Variables",
                    "Saddle Points",
                    "Maxima and Minima: Worked Examples",
                    "Lagrange's Method of Multipliers",
                    "Lagrange's Method: Applications",
                ]
            },
            "integral_calc": {
                "label": "Integral Calculus",
                "subtopics": [
                    "Reduction Formulae: sin^n x",
                    "Reduction Formulae: cos^n x",
                    "Reduction Formulae: sin^m x cos^n x",
                    "Wallis Formula",
                    "Gamma Function: Definition and Properties",
                    "Recurrence Relation of Gamma Function",
                    "Beta Function: Definition",
                    "Relation Between Beta and Gamma Functions",
                    "Beta and Gamma: Applications to Integrals",
                    "Double Integrals: Cartesian Coordinates",
                    "Double Integrals: Variable Limits",
                    "Change of Order of Integration",
                    "Double Integrals: Polar Coordinates",
                    "Area Using Double Integrals",
                    "Triple Integrals: Cartesian Coordinates",
                    "Triple Integrals: Cylindrical Coordinates",
                    "Triple Integrals: Spherical Coordinates",
                    "Volume Using Triple Integrals",
                    "Area Between Curves",
                    "Length of a Curve (Arc Length)",
                    "Surface Area of Revolution",
                    "Volume of Revolution: Disk and Shell Method",
                    "Centre of Mass and Moment of Inertia",
                    "Improper Integrals: Infinite Limits",
                    "Improper Integrals: Discontinuous Integrands",
                    "Convergence Tests for Improper Integrals",
                ]
            },
            "infinite_series": {
                "label": "Infinite Series",
                "subtopics": [
                    "Sequences: Convergence and Divergence",
                    "Series: Definition and Partial Sums",
                    "Geometric Series and its Sum",
                    "P-Series Test",
                    "Divergence Test (nth Term Test)",
                    "Comparison Test",
                    "Limit Comparison Test",
                    "Ratio Test (D'Alembert's Test)",
                    "Root Test (Cauchy's Test)",
                    "Integral Test",
                    "Alternating Series Test (Leibniz Test)",
                    "Absolute Convergence",
                    "Conditional Convergence",
                    "Power Series: Definition",
                    "Radius and Interval of Convergence",
                    "Operations on Power Series",
                    "Taylor Series as Power Series",
                ]
            }
        }
    },
    "sem2": {
        "label": "Semester 2", "subtitle": "Linear Algebra & ODEs",
        "topics": {
            "linear_algebra": {
                "label": "Linear Algebra",
                "subtopics": [
                    "Types of Matrices",
                    "Matrix Operations: Addition and Multiplication",
                    "Transpose, Symmetric and Skew-Symmetric Matrices",
                    "Determinants: Properties and Expansion",
                    "Determinants: Cramer's Rule",
                    "Inverse of a Matrix: Adjoint Method",
                    "Inverse of a Matrix: Row Reduction",
                    "Row Echelon Form",
                    "Reduced Row Echelon Form",
                    "Rank of a Matrix",
                    "Normal Form of a Matrix",
                    "System of Linear Equations: Types",
                    "Consistency of Linear Systems",
                    "Solution by Gauss Elimination",
                    "Solution by Gauss-Jordan Method",
                    "Homogeneous Systems",
                    "Non-Homogeneous Systems",
                    "Eigenvalues: Characteristic Equation",
                    "Eigenvectors: Finding and Properties",
                    "Properties of Eigenvalues",
                    "Cayley-Hamilton Theorem",
                    "Cayley-Hamilton: Finding Inverse and Powers",
                    "Diagonalization: Conditions and Process",
                    "Orthogonal Diagonalization",
                    "Quadratic Forms",
                    "Positive Definite and Indefinite Matrices",
                    "Index, Signature and Rank of Quadratic Form",
                ]
            },
            "ode_first": {
                "label": "First Order ODEs",
                "subtopics": [
                    "Formation of Differential Equations",
                    "Order and Degree of ODEs",
                    "Variables Separable Method",
                    "Equations Reducible to Variables Separable",
                    "Homogeneous Differential Equations",
                    "Equations Reducible to Homogeneous Form",
                    "Exact Differential Equations",
                    "Test for Exactness",
                    "Integrating Factor: Function of x Only",
                    "Integrating Factor: Function of y Only",
                    "Integrating Factor: By Inspection",
                    "Linear First Order ODE",
                    "Bernoulli's Equation",
                    "Clairaut's Equation",
                    "Orthogonal Trajectories: Cartesian",
                    "Orthogonal Trajectories: Polar",
                    "Application: Newton's Law of Cooling",
                    "Application: Growth and Decay",
                    "Application: Mixing Problems",
                    "Application: Electric Circuits (RL, RC)",
                ]
            },
            "ode_higher": {
                "label": "Higher Order ODEs",
                "subtopics": [
                    "Linear ODEs with Constant Coefficients",
                    "Auxiliary Equation: Real Distinct Roots",
                    "Auxiliary Equation: Real Repeated Roots",
                    "Auxiliary Equation: Complex Conjugate Roots",
                    "Complementary Function: All Cases",
                    "Particular Integral: e^(ax)",
                    "Particular Integral: sin(ax) and cos(ax)",
                    "Particular Integral: x^n (Polynomial)",
                    "Particular Integral: e^(ax) V(x)",
                    "Particular Integral: Failure Cases",
                    "Method of Undetermined Coefficients",
                    "Variation of Parameters",
                    "Wronskian and Linear Independence",
                    "Euler-Cauchy Equation",
                    "Legendre's Linear Equation",
                    "Simultaneous Linear ODEs",
                    "Application: Simple Harmonic Motion",
                    "Application: Damped Oscillations",
                    "Application: Forced Oscillations",
                    "Application: Beam Deflection",
                    "Application: RLC Circuits",
                ]
            },
            "laplace": {
                "label": "Laplace Transforms",
                "subtopics": [
                    "Definition of Laplace Transform",
                    "Existence Conditions",
                    "Laplace Transform of Standard Functions",
                    "First Shifting Theorem (s-shifting)",
                    "Second Shifting Theorem (t-shifting)",
                    "Laplace Transform of Derivatives",
                    "Laplace Transform of Integrals",
                    "Multiplication by t^n",
                    "Division by t",
                    "Inverse Laplace Transform: Definition",
                    "Inverse Laplace Transform: Standard Forms",
                    "Inverse by Partial Fractions",
                    "Inverse using First Shifting Theorem",
                    "Convolution Theorem",
                    "Convolution: Applications",
                    "Unit Step Function (Heaviside)",
                    "Laplace of Unit Step Function",
                    "Dirac Delta Function",
                    "Laplace of Dirac Delta",
                    "Periodic Functions: Laplace Transform",
                    "Solution of IVP using Laplace Transform",
                    "Solution of System of ODEs using Laplace",
                ]
            }
        }
    },
    "sem3": {
        "label": "Semester 3", "subtitle": "Vector Calculus & Complex Analysis",
        "topics": {
            "vector_calc": {
                "label": "Vector Calculus",
                "subtopics": [
                    "Scalar and Vector Fields",
                    "Vector Differentiation",
                    "Velocity and Acceleration Vectors",
                    "Gradient of a Scalar Field",
                    "Directional Derivative",
                    "Normal to a Surface",
                    "Maximum Rate of Change",
                    "Divergence of a Vector Field",
                    "Physical Meaning of Divergence",
                    "Curl of a Vector Field",
                    "Physical Meaning of Curl",
                    "Irrotational and Solenoidal Fields",
                    "Scalar Potential",
                    "Vector Identities: del Operator",
                    "Laplacian Operator",
                    "Line Integrals: Scalar Fields",
                    "Line Integrals: Vector Fields",
                    "Work Done by a Force",
                    "Conservative Fields and Path Independence",
                    "Surface Integrals: Scalar Fields",
                    "Surface Integrals: Vector Fields (Flux)",
                    "Volume Integrals",
                    "Green's Theorem in the Plane",
                    "Green's Theorem: Applications",
                    "Stokes' Theorem",
                    "Stokes' Theorem: Applications",
                    "Gauss Divergence Theorem",
                    "Gauss Theorem: Applications",
                    "Relationship Between Three Theorems",
                ]
            },
            "complex_analysis": {
                "label": "Complex Analysis",
                "subtopics": [
                    "Complex Numbers: Cartesian and Polar Form",
                    "De Moivre's Theorem",
                    "Roots of Complex Numbers",
                    "Geometry of Complex Numbers",
                    "Functions of a Complex Variable",
                    "Limits and Continuity in Complex Plane",
                    "Differentiability of Complex Functions",
                    "Cauchy-Riemann Equations: Cartesian Form",
                    "Cauchy-Riemann Equations: Polar Form",
                    "Analytic Functions",
                    "Harmonic Functions",
                    "Harmonic Conjugates",
                    "Construction of Analytic Functions",
                    "Complex Exponential Function",
                    "Complex Trigonometric Functions",
                    "Complex Hyperbolic Functions",
                    "Complex Logarithm",
                    "General Power Functions",
                    "Complex Integration: Line Integrals",
                    "Cauchy's Integral Theorem",
                    "Cauchy's Integral Formula",
                    "Derivatives Using Cauchy's Formula",
                    "Taylor Series in Complex Plane",
                    "Laurent Series",
                    "Removable Singularity",
                    "Poles: Simple and Higher Order",
                    "Essential Singularity",
                    "Residue: Definition and Calculation",
                    "Residue at Simple Pole",
                    "Residue at Pole of Order m",
                    "Residue Theorem",
                    "Contour Integration: Real Integrals",
                    "Contour Integration: Trigonometric Integrals",
                ]
            },
            "fourier_series": {
                "label": "Fourier Series",
                "subtopics": [
                    "Periodic Functions and Period",
                    "Trigonometric Series",
                    "Dirichlet Conditions",
                    "Euler's Formulae for Fourier Coefficients",
                    "Fourier Series of Continuous Functions",
                    "Fourier Series with Discontinuities",
                    "Convergence at Points of Discontinuity",
                    "Even Functions and Cosine Series",
                    "Odd Functions and Sine Series",
                    "Half-Range Cosine Series",
                    "Half-Range Sine Series",
                    "Parseval's Identity",
                    "Applications of Parseval's Identity",
                    "Change of Interval",
                    "Complex Form of Fourier Series",
                    "Exponential Form of Fourier Series",
                    "Practical Harmonic Analysis",
                    "Fourier Series in Engineering Problems",
                ]
            }
        }
    },
    "sem4": {
        "label": "Semester 4", "subtitle": "Probability, Statistics & Numerical Methods",
        "topics": {
            "probability": {
                "label": "Probability & Statistics",
                "subtopics": [
                    "Sample Space and Events",
                    "Classical and Axiomatic Probability",
                    "Conditional Probability",
                    "Multiplication Theorem",
                    "Independent Events",
                    "Bayes' Theorem",
                    "Discrete Random Variables",
                    "Probability Mass Function",
                    "Continuous Random Variables",
                    "Probability Density Function",
                    "Cumulative Distribution Function",
                    "Expectation and Mean",
                    "Variance and Standard Deviation",
                    "Moments and Moment Generating Function",
                    "Binomial Distribution",
                    "Binomial Distribution: Mean and Variance",
                    "Poisson Distribution",
                    "Poisson as Limit of Binomial",
                    "Poisson Distribution: Applications",
                    "Normal Distribution",
                    "Standard Normal Distribution",
                    "Normal Distribution: Applications",
                    "Exponential Distribution",
                    "Joint Probability Distributions",
                    "Marginal Distributions",
                    "Independent Random Variables",
                    "Covariance and Correlation Coefficient",
                    "Linear Regression: Method of Least Squares",
                    "Lines of Regression",
                    "Regression Coefficients",
                    "Curve Fitting",
                    "Sampling Distributions",
                    "Chi-Square Distribution",
                    "Chi-Square Test of Goodness of Fit",
                    "Chi-Square Test of Independence",
                    "t-Distribution and t-Test",
                    "F-Distribution and F-Test",
                    "Hypothesis Testing: Type I and Type II Errors",
                    "Large Sample Tests",
                ]
            },
            "numerical": {
                "label": "Numerical Methods",
                "subtopics": [
                    "Types of Errors in Numerical Methods",
                    "Absolute, Relative and Percentage Error",
                    "Round-off and Truncation Error",
                    "Propagation of Errors",
                    "Bisection Method",
                    "Bisection Method: Convergence",
                    "Regula-Falsi Method",
                    "Newton-Raphson Method",
                    "Newton-Raphson: Convergence and Failure",
                    "Secant Method",
                    "Fixed Point Iteration Method",
                    "Finite Differences: Forward Differences",
                    "Finite Differences: Backward Differences",
                    "Newton's Forward Difference Interpolation",
                    "Newton's Backward Difference Interpolation",
                    "Lagrange's Interpolation Formula",
                    "Divided Differences",
                    "Newton's Divided Difference Formula",
                    "Cubic Spline Interpolation",
                    "Numerical Differentiation: Forward Difference",
                    "Numerical Differentiation: Backward Difference",
                    "Trapezoidal Rule",
                    "Simpson's 1/3 Rule",
                    "Simpson's 3/8 Rule",
                    "Weddle's Rule",
                    "Gaussian Quadrature",
                    "Euler's Method for ODEs",
                    "Modified Euler's Method",
                    "Runge-Kutta Method: RK2",
                    "Runge-Kutta Method: RK4",
                    "Predictor-Corrector Methods",
                    "Gauss-Seidel Iterative Method",
                    "Jacobi Iterative Method",
                ]
            },
            "transforms": {
                "label": "Transform Theory",
                "subtopics": [
                    "Fourier Integral Theorem",
                    "Fourier Transform: Definition",
                    "Fourier Transform: Standard Pairs",
                    "Properties of Fourier Transform",
                    "Fourier Sine Transform",
                    "Fourier Cosine Transform",
                    "Convolution Theorem for Fourier Transform",
                    "Parseval's Identity for Fourier Transform",
                    "Inverse Fourier Transform",
                    "Applications of Fourier Transform",
                    "Z-Transform: Definition",
                    "Z-Transform of Standard Sequences",
                    "Region of Convergence (ROC)",
                    "Properties of Z-Transform",
                    "Initial Value Theorem",
                    "Final Value Theorem",
                    "Inverse Z-Transform: Partial Fractions",
                    "Inverse Z-Transform: Power Series",
                    "Inverse Z-Transform: Residue Method",
                    "Solution of Difference Equations using Z-Transform",
                    "Applications of Z-Transform",
                ]
            }
        }
    }
}

# ══════════════════════════════════════════════════════════════
#  PREREQUISITES
# ══════════════════════════════════════════════════════════════
PREREQUISITES = {
    "Limits and Continuity":              ["Basic functions and graphs", "Algebra of limits"],
    "Differentiability":                  ["Limits and Continuity"],
    "Rolle's Theorem":                    ["Differentiability", "Limits and Continuity"],
    "Lagrange's Mean Value Theorem":      ["Rolle's Theorem", "Differentiability"],
    "Cauchy's Mean Value Theorem":        ["Lagrange's Mean Value Theorem"],
    "L'Hopital's Rule":                   ["Limits and Continuity", "Differentiability", "Indeterminate Forms"],
    "Taylor's Theorem":                   ["Differentiability", "Maclaurin Series"],
    "Maclaurin Series":                   ["Differentiability", "Limits and Continuity"],
    "Indeterminate Forms":                ["Limits and Continuity", "L'Hopital's Rule"],
    "Curvature and Radius of Curvature":  ["Differentiability", "Parametric equations"],
    "Partial Derivatives":                ["Limits and Continuity", "Differentiability"],
    "Euler's Theorem on Homogeneous Functions": ["Partial Derivatives", "Functions of Several Variables"],
    "Total Derivative":                   ["Partial Derivatives", "Chain rule"],
    "Jacobians":                          ["Partial Derivatives", "Determinants"],
    "Maxima and Minima of Two Variables":  ["Partial Derivatives", "Jacobians"],
    "Lagrange's Method of Multipliers":   ["Partial Derivatives", "Maxima and Minima of Two Variables"],
    "Reduction Formulae":                 ["Integration techniques", "Trigonometric identities"],
    "Beta and Gamma Functions":           ["Reduction Formulae", "Improper Integrals"],
    "Double Integrals":                   ["Single variable integration", "Limits and Continuity"],
    "Change of Order of Integration":     ["Double Integrals"],
    "Triple Integrals":                   ["Double Integrals"],
    "Improper Integrals":                 ["Single variable integration", "Limits and Continuity"],
    "Convergence and Divergence":         ["Limits and Continuity", "Sequences"],
    "Ratio Test (D'Alembert)":            ["Convergence and Divergence"],
    "Root Test (Cauchy)":                 ["Convergence and Divergence"],
    "Power Series and Radius of Convergence": ["Convergence and Divergence", "Taylor's Theorem"],
    "Matrices and Types":                 ["Basic algebra"],
    "Rank of a Matrix":                   ["Matrices and Types", "Echelon Form and Normal Form"],
    "System of Linear Equations":         ["Rank of a Matrix", "Echelon Form and Normal Form"],
    "Eigenvalues and Eigenvectors":       ["Matrices and Types", "Determinants", "System of Linear Equations"],
    "Cayley-Hamilton Theorem":            ["Eigenvalues and Eigenvectors"],
    "Diagonalization":                    ["Eigenvalues and Eigenvectors", "Cayley-Hamilton Theorem"],
    "Quadratic Forms":                    ["Eigenvalues and Eigenvectors", "Diagonalization"],
    "Exact Differential Equations":       ["Variables Separable", "Partial Derivatives"],
    "Integrating Factors":                ["Exact Differential Equations"],
    "Bernoulli's Equation":               ["Linear First Order ODEs"],
    "Complementary Function":             ["Linear ODEs with Constant Coefficients", "Characteristic equation"],
    "Particular Integral":                ["Complementary Function"],
    "Variation of Parameters":            ["Complementary Function", "Particular Integral"],
    "Euler-Cauchy Equation":              ["Linear ODEs with Constant Coefficients"],
    "Laplace Transforms of Standard Functions": ["Definition and Existence", "Basic integration"],
    "Inverse Laplace Transform":          ["Laplace Transforms of Standard Functions", "Partial Fractions Method"],
    "Convolution Theorem":                ["Inverse Laplace Transform"],
    "Solution of ODEs using Laplace":     ["Inverse Laplace Transform", "Convolution Theorem"],
    "Unit Step and Dirac Delta Functions": ["Laplace Transforms of Standard Functions"],
    "Gradient and Directional Derivative": ["Partial Derivatives", "Scalar and Vector Fields"],
    "Divergence and Curl":                ["Gradient and Directional Derivative"],
    "Line Integrals":                     ["Vector Calculus basics", "Single variable integration"],
    "Surface Integrals":                  ["Line Integrals", "Double Integrals"],
    "Green's Theorem in the Plane":       ["Line Integrals", "Double Integrals"],
    "Stokes' Theorem":                    ["Surface Integrals", "Divergence and Curl"],
    "Gauss Divergence Theorem":           ["Surface Integrals", "Divergence and Curl"],
    "Analytic Functions":                 ["Complex Numbers Review", "Limits in complex plane"],
    "Cauchy-Riemann Equations":           ["Analytic Functions", "Partial Derivatives"],
    "Cauchy's Integral Theorem":          ["Complex Integration", "Analytic Functions"],
    "Cauchy's Integral Formula":          ["Cauchy's Integral Theorem"],
    "Taylor and Laurent Series":          ["Cauchy's Integral Formula", "Power Series"],
    "Residue Theorem":                    ["Taylor and Laurent Series", "Singularities and Poles"],
    "Contour Integration":                ["Residue Theorem"],
    "Fourier Series of Even and Odd Functions": ["Euler's Formulae", "Periodic Functions"],
    "Half-Range Sine and Cosine Series":  ["Fourier Series of Even and Odd Functions"],
    "Parseval's Identity":                ["Fourier Series of Even and Odd Functions"],
    "Binomial Distribution":              ["Random Variables", "Probability Distributions"],
    "Poisson Distribution":               ["Binomial Distribution"],
    "Normal Distribution":                ["Probability Distributions", "Expectation and Variance"],
    "Correlation and Regression":         ["Expectation and Variance", "Joint Distributions"],
    "Hypothesis Testing":                 ["Normal Distribution", "Sampling Theory"],
    "t-Test and F-Test":                  ["Hypothesis Testing", "Normal Distribution"],
    "Newton-Raphson Method":              ["Bisection Method", "Differentiability"],
    "Newton's Forward Interpolation":     ["Errors and Approximations", "Finite differences"],
    "Newton's Backward Interpolation":    ["Newton's Forward Interpolation"],
    "Lagrange Interpolation":             ["Newton's Forward Interpolation"],
    "Simpson's 1/3 Rule":                 ["Trapezoidal Rule", "Numerical Differentiation"],
    "Simpson's 3/8 Rule":                 ["Simpson's 1/3 Rule"],
    "Runge-Kutta Method (RK4)":           ["Euler's Method for ODEs", "Taylor's Theorem"],
    "Fourier Transform":                  ["Fourier Integral Theorem", "Fourier Series"],
    "Fourier Sine and Cosine Transforms": ["Fourier Transform"],
    "Convolution Theorem for Fourier":    ["Fourier Transform"],
    "Z-Transform Properties":             ["Z-Transform Definition"],
    "Inverse Z-Transform":                ["Z-Transform Properties", "Partial Fractions Method"],
    "Solution of Difference Equations":   ["Inverse Z-Transform"],
}

# ══════════════════════════════════════════════════════════════
#  SUBTOPIC GUIDANCE
# ══════════════════════════════════════════════════════════════
SUBTOPIC_GUIDANCE = {
    "Limits and Continuity": "Cover epsilon-delta definition, left and right hand limits, algebra of limits, sandwich theorem. Show discontinuity types. Numerical example: find limit of (x^2-1)/(x-1) as x→1. Examiner expects: state type of discontinuity explicitly.",
    "Differentiability": "Cover definition via first principles, relation between continuity and differentiability. Show a function continuous but not differentiable at a point. Numerical example using |x| at x=0.",
    "Rolle's Theorem": "State all THREE conditions explicitly — continuous on [a,b], differentiable on (a,b), f(a)=f(b). Show a 2-mark statement question and a 4-mark verification problem. Examiner expects: all three conditions stated before applying.",
    "Lagrange's Mean Value Theorem": "State conditions, geometric interpretation as parallel tangent. Show verification with f(x)=x^2 on [1,3]. Examiner expects: find c explicitly in every problem.",
    "Cauchy's Mean Value Theorem": "Show it as generalisation of LMVT. Typical exam problem: apply to f(x)=x^2, g(x)=x^3. Examiner expects: verify both functions satisfy conditions.",
    "L'Hopital's Rule": "Cover 0/0 and inf/inf forms. Show repeated application. Numerical: lim(x→0) sinx/x, lim(x→∞) x/e^x. Examiner expects: state the indeterminate form before applying the rule.",
    "Taylor's Theorem": "Show expansion with Lagrange remainder. Cover expansion of sin, cos, e^x, log(1+x) about x=0. Examiner expects: write first 4-5 terms explicitly.",
    "Maclaurin Series": "Special case of Taylor at x=0. Standard expansions: e^x, sin x, cos x, log(1+x), (1+x)^n. Examiner expects: range of validity for each series.",
    "Indeterminate Forms": "Cover 0/0, inf/inf, 0×inf, inf-inf, 1^inf, 0^0, inf^0. Show conversion strategy. Numerical: lim(x→0) x^x.",
    "Curvature and Radius of Curvature": "Formula kappa = |y''|/(1+y'^2)^(3/2). Show for circle, parabola, catenary. Examiner expects: units and geometric meaning stated.",
    "Partial Derivatives": "Show clairaut theorem (symmetry of mixed partials). Numerical: find all second partials of f(x,y)=x^2y+xy^3. Examiner expects: verify f_xy = f_yx.",
    "Euler's Theorem on Homogeneous Functions": "State theorem: x*df/dx + y*df/dy = n*f. Show verification. Examiner expects: first verify function is homogeneous of degree n, then apply theorem.",
    "Total Derivative": "Show df = (df/dx)dx + (df/dy)dy. Chain rule for composite functions. Numerical: if z=x^2+y^2, x=t, y=t^2, find dz/dt.",
    "Jacobians": "J = d(u,v)/d(x,y) as 2x2 determinant. Show J*J_inverse=1. Examiner expects: change of variables in double integrals requires Jacobian.",
    "Maxima and Minima of Two Variables": "Second derivative test: D = f_xx*f_yy - (f_xy)^2. Show saddle point case. Numerical: find extrema of f(x,y)=x^2+y^2-2x-4y+8.",
    "Lagrange's Method of Multipliers": "Constrained optimisation: grad(f) = lambda*grad(g). Show for maximising x+y subject to x^2+y^2=1. Examiner expects: solve the system of equations systematically.",
    "Reduction Formulae": "Derive I_n for sin^n x, cos^n x. Show Wallis formula. Numerical: evaluate integral of sin^5 x dx using reduction. Examiner expects: start from scratch with integration by parts.",
    "Beta and Gamma Functions": "B(m,n) = integral_0^1 x^(m-1)(1-x)^(n-1)dx. Gamma(n+1)=n*Gamma(n). Relation B(m,n)=Gamma(m)Gamma(n)/Gamma(m+n). Numerical: evaluate integral_0^inf x^4 e^-x dx = Gamma(5) = 24.",
    "Double Integrals": "Evaluate by iterated integration. Change order when limits are variable. Polar coordinates: dA = r dr dtheta. Numerical: area of circle x^2+y^2=a^2 using double integral.",
    "Change of Order of Integration": "Draw the region, identify new limits carefully. Numerical: change order in integral_0^1 integral_x^1 f(x,y) dy dx. Examiner expects: always draw the region first.",
    "Triple Integrals": "Volume element dV = dx dy dz. Cylindrical: r dr dtheta dz. Numerical: volume of sphere using triple integral.",
    "Eigenvalues and Eigenvectors": "Characteristic equation det(A-lambdaI)=0. For each eigenvalue solve (A-lambdaI)x=0. Show for 3x3 matrix. Examiner expects: characteristic polynomial written in full, roots found, eigenvectors found by row reduction.",
    "Cayley-Hamilton Theorem": "Every matrix satisfies its own characteristic equation. Show verification for 2x2 and 3x3. Use to find A^-1 and higher powers. Examiner expects: state theorem, find characteristic equation, verify A satisfies it.",
    "Diagonalization": "A = PDP^-1 where D is diagonal eigenvalue matrix. Conditions: n linearly independent eigenvectors. Numerical: diagonalize 2x2 matrix fully. Examiner expects: show eigenvectors are linearly independent.",
    "Exact Differential Equations": "Test: dM/dy = dN/dx. Show finding integrating factor mu=mu(x) when (dM/dy-dN/dx)/N is function of x only. Numerical: solve (2xy+y^2)dx + (x^2+2xy)dy=0.",
    "Bernoulli's Equation": "dy/dx + P(x)y = Q(x)y^n. Substitution v=y^(1-n). Numerical: solve dy/dx - y = xy^2. Examiner expects: clearly show the substitution step.",
    "Complementary Function": "Auxiliary equation method. Roots: real distinct, real repeated, complex conjugate — three separate cases. Examiner expects: write the three cases and identify which applies.",
    "Particular Integral": "Operator method D=d/dx. Cases: e^ax, sin(ax), cos(ax), x^n, x^n*e^ax. Show failure case when D=a is a root. Examiner expects: check if failure case applies before computing.",
    "Variation of Parameters": "Wronskian W. Particular integral yp = -y1*integral(y2*f/W) + y2*integral(y1*f/W). Numerical: solve y'' + y = sec x. Examiner expects: compute W first, then the two integrals.",
    "Laplace Transforms of Standard Functions": "Table: L{1}=1/s, L{t^n}=n!/s^(n+1), L{e^at}=1/(s-a), L{sin at}=a/(s^2+a^2), L{cos at}=s/(s^2+a^2). First shifting theorem. Examiner expects: state the formula before applying.",
    "Inverse Laplace Transform": "Partial fractions for rational functions. Cover all three types of denominator factors. Convolution for products. Examiner expects: always write partial fraction form before finding coefficients.",
    "Solution of ODEs using Laplace": "Take Laplace of both sides, apply initial conditions, find Y(s), take inverse. Numerical: solve y'' + 3y' + 2y = e^-t, y(0)=1, y'(0)=0. Examiner expects: show each step of taking the Laplace transform.",
    "Gradient and Directional Derivative": "grad f = (df/dx)i + (df/dy)j + (df/dz)k. Directional derivative = grad f dot unit vector. Maximum rate of change = |grad f|. Numerical: find directional derivative of f=x^2+y^2+z^2 at (1,1,1) in direction (1,1,1).",
    "Divergence and Curl": "div F = dF1/dx + dF2/dy + dF3/dz (scalar). curl F = del cross F (vector). Irrotational if curl=0, solenoidal if div=0. Examiner expects: classify the field after computing.",
    "Green's Theorem in the Plane": "Line integral around closed curve = double integral of (dN/dx - dM/dy) dA. Used for area calculation. Numerical: verify for F=(y,x) around unit circle. Examiner expects: state the orientation convention.",
    "Stokes' Theorem": "Surface integral of curl F = line integral of F. Choose orientation consistently. Numerical: verify for F=(y,-x,0) over hemisphere. Examiner expects: state the right-hand rule for orientation.",
    "Gauss Divergence Theorem": "Volume integral of div F = surface integral of F dot n. Outward normal. Numerical: verify for F=(x,y,z) over unit cube. Examiner expects: confirm outward normal direction.",
    "Cauchy-Riemann Equations": "df/dx = dv/dy and du/dy = -dv/dx in Cartesian. Polar form also. If CR satisfied and partials continuous then analytic. Numerical: check if f(z)=z^2 is analytic. Examiner expects: check CR equations explicitly, then state the conclusion.",
    "Cauchy's Integral Theorem": "Integral of f(z) around simple closed curve = 0 if f is analytic inside. Simply connected domain required. Show deformation of contour. Examiner expects: verify function is analytic in the region before applying.",
    "Cauchy's Integral Formula": "f(z0) = (1/2pi i) integral f(z)/(z-z0) dz. Extension for derivatives. Numerical: evaluate integral of e^z/(z-1) around |z|=2. Examiner expects: identify z0 and verify it lies inside the contour.",
    "Taylor and Laurent Series": "Taylor inside circle of convergence. Laurent has negative powers — valid in annular region. Residue = coefficient of 1/(z-z0) in Laurent series. Numerical: expand f(z)=1/((z-1)(z-2)) in different annular regions.",
    "Residue Theorem": "Integral = 2pi i * sum of residues inside contour. Three types of singularities: removable, pole, essential. Residue at simple pole = lim(z→z0)(z-z0)f(z). Examiner expects: classify each singularity before computing residue.",
    "Fourier Series of Even and Odd Functions": "Even: bn=0, only cosine terms. Odd: a0=an=0, only sine terms. Examiner expects: check symmetry BEFORE computing — saves half the calculation.",
    "Half-Range Sine and Cosine Series": "Extend function as odd or even. Sine series: all bn. Cosine series: all an. Numerical: expand f(x)=x on [0,L] as both sine and cosine series. Examiner expects: state the extension type clearly.",
    "Parseval's Identity": "Sum of squares of Fourier coefficients = integral of f^2. Used to evaluate infinite series. Numerical: use Parseval on f(x)=x to find sum 1/n^2 = pi^2/6.",
    "Binomial Distribution": "P(X=r) = nCr p^r q^(n-r). Mean=np, Variance=npq. Conditions: fixed n, independent trials, constant p. Numerical: 6 coins tossed, find P(exactly 4 heads). Examiner expects: verify all conditions before applying.",
    "Poisson Distribution": "P(X=r) = e^(-lambda) lambda^r / r!. Mean = Variance = lambda. Approximation to binomial when n large, p small. Numerical: average 3 calls/minute, find P(exactly 5 calls).",
    "Normal Distribution": "Standard normal Z=(X-mu)/sigma. Use Z-tables. 68-95-99.7 rule. Numerical: X~N(50,100), find P(X>60). Examiner expects: always convert to Z, state symmetry when used.",
    "Newton-Raphson Method": "x_{n+1} = x_n - f(x_n)/f'(x_n). Converges quadratically. Show iteration table with 3-4 iterations. Examiner expects: present as a table with columns: n, x_n, f(x_n), f'(x_n), x_{n+1}.",
    "Newton's Forward Interpolation": "Delta operator. Forward difference table. Formula: y = y0 + s*Delta(y0) + s(s-1)/2! * Delta^2(y0) + ... where s=(x-x0)/h. Examiner expects: always construct full forward difference table first.",
    "Lagrange Interpolation": "No equal spacing required. L_k(x) formula. Used when data points unequally spaced. Numerical: find f(2) given f(1)=1, f(3)=9, f(4)=16. Examiner expects: write full L_k expressions before substituting.",
    "Trapezoidal Rule": "h/2[y0 + 2(y1+...+y_{n-1}) + yn]. Error O(h^2). Numerical: integrate sin x from 0 to pi with n=6. Examiner expects: clear table of x and y values before applying formula.",
    "Simpson's 1/3 Rule": "h/3[y0 + 4(y1+y3+...) + 2(y2+y4+...) + yn]. n must be EVEN. Error O(h^4). More accurate than trapezoidal. Examiner expects: verify n is even, then label odd and even interior points clearly.",
    "Runge-Kutta Method (RK4)": "Four slopes k1,k2,k3,k4. y_{n+1} = y_n + (k1+2k2+2k3+k4)/6. Show one complete step with all four k values. Examiner expects: calculate each k value separately and clearly labelled.",
    "Fourier Transform": "F(omega) = integral f(t) e^(-j omega t) dt. Inverse: f(t) = (1/2pi) integral F(omega) e^(j omega t) d omega. Standard pairs: rect, sinc, Gaussian. Examiner expects: state both transform and inverse transform pair.",
    "Z-Transform Definition": "Z{x(n)} = sum_{n=-inf}^{inf} x(n) z^(-n). Region of convergence crucial. Standard pairs: Z{a^n u(n)} = z/(z-a) for |z|>|a|. Examiner expects: always state the ROC.",
    "Inverse Z-Transform": "Partial fraction method. Divide by z first, apply partial fractions, multiply back by z. Numerical: find inverse Z of z/((z-1)(z-2)). Examiner expects: use z/X(z) method for cleaner partial fractions.",
}

# ══════════════════════════════════════════════════════════════
#  SUBTOPIC GUIDANCE LOOKUP — fuzzy matching
# ══════════════════════════════════════════════════════════════
def get_subtopic_guidance(subtopic):
    """Get guidance with exact match first, then fuzzy match"""
    if subtopic in SUBTOPIC_GUIDANCE:
        return SUBTOPIC_GUIDANCE[subtopic]

    subtopic_lower = subtopic.lower()
    for key, value in SUBTOPIC_GUIDANCE.items():
        key_lower = key.lower()
        if key_lower in subtopic_lower or subtopic_lower in key_lower:
            return value

    for key, value in SUBTOPIC_GUIDANCE.items():
        key_words = set(key.lower().split())
        subtopic_words = set(subtopic_lower.split())
        overlap = key_words & subtopic_words
        if len(overlap) >= 2:
            return value

    return ""

# ══════════════════════════════════════════════════════════════
#  REFERENCES
# ══════════════════════════════════════════════════════════════
REFERENCES = {
    "diff_calc":        ["https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/", "https://www.khanacademy.org/math/calculus-1", "https://tutorial.math.lamar.edu/Classes/CalcI/CalcI.aspx", "https://mathworld.wolfram.com/Calculus.html"],
    "partial_diff":     ["https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/", "https://www.khanacademy.org/math/multivariable-calculus", "https://tutorial.math.lamar.edu/Classes/CalcIII/CalcIII.aspx", "https://mathworld.wolfram.com/PartialDerivative.html"],
    "integral_calc":    ["https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/", "https://www.khanacademy.org/math/integral-calculus", "https://tutorial.math.lamar.edu/Classes/CalcII/CalcII.aspx", "https://mathworld.wolfram.com/Integral.html"],
    "infinite_series":  ["https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/", "https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new", "https://tutorial.math.lamar.edu/Classes/CalcII/SeriesIntro.aspx", "https://mathworld.wolfram.com/Series.html"],
    "linear_algebra":   ["https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/", "https://www.khanacademy.org/math/linear-algebra", "https://www.3blue1brown.com/topics/linear-algebra", "https://mathworld.wolfram.com/LinearAlgebra.html"],
    "ode_first":        ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/", "https://www.khanacademy.org/math/differential-equations", "https://tutorial.math.lamar.edu/Classes/DE/DE.aspx", "https://mathworld.wolfram.com/OrdinaryDifferentialEquation.html"],
    "ode_higher":       ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/", "https://tutorial.math.lamar.edu/Classes/DE/SecondOrderConcepts.aspx", "https://www.khanacademy.org/math/differential-equations", "https://mathworld.wolfram.com/SecondOrderOrdinaryDifferentialEquation.html"],
    "laplace":          ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/", "https://tutorial.math.lamar.edu/Classes/DE/LaplaceIntro.aspx", "https://www.khanacademy.org/math/differential-equations/laplace-transform", "https://mathworld.wolfram.com/LaplaceTransform.html"],
    "vector_calc":      ["https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/", "https://www.khanacademy.org/math/multivariable-calculus", "https://tutorial.math.lamar.edu/Classes/CalcIII/VectorFields.aspx", "https://mathworld.wolfram.com/VectorCalculus.html"],
    "complex_analysis": ["https://ocw.mit.edu/courses/18-04-complex-variables-with-applications-spring-2018/", "https://mathworld.wolfram.com/ComplexAnalysis.html", "https://www.youtube.com/playlist?list=PLBh2i93oe2qvRGAtgkTszX7szZDVd6jh1", "https://nptel.ac.in/courses/111/106/111106084/"],
    "fourier_series":   ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/", "https://www.khanacademy.org/science/electrical-engineering/ee-signals", "https://mathworld.wolfram.com/FourierSeries.html", "https://nptel.ac.in/courses/111/104/111104092/"],
    "probability":      ["https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/", "https://www.khanacademy.org/math/statistics-probability", "https://www.probabilitycourse.com/", "https://mathworld.wolfram.com/Probability.html"],
    "numerical":        ["https://ocw.mit.edu/courses/18-330-introduction-to-numerical-analysis-spring-2012/", "https://nptel.ac.in/courses/111/107/111107105/", "https://mathworld.wolfram.com/NumericalAnalysis.html", "https://tutorial.math.lamar.edu/Extras/AlgebraTrigReview/AlgebraTrigReview.aspx"],
    "transforms":       ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/", "https://www.khanacademy.org/science/electrical-engineering/ee-signals", "https://mathworld.wolfram.com/FourierTransform.html", "https://nptel.ac.in/courses/111/104/111104090/"],
    "gate":             ["https://gate.iitk.ac.in/", "https://nptel.ac.in/", "https://www.madeeasy.in/", "https://byjusexamprep.com/gate"],
    "iit_jam":          ["https://jam.iitb.ac.in/", "https://nptel.ac.in/", "https://www.mathcity.org/"],
    "csir_net":         ["https://csirhrdg.res.in/", "https://nptel.ac.in/", "https://www.shaalaa.com/"],
}

# ══════════════════════════════════════════════════════════════
#  SUBJECT CONNECTIONS MAP
# ══════════════════════════════════════════════════════════════
SUBJECT_CONNECTIONS = {
    "diff_calc": {"connections": [
        {"subject": "Engineering Mechanics", "semester": "Sem 1-2", "how": "Velocity and acceleration as derivatives of displacement. Newton's second law in differential form.", "example": r"Finding maximum range of a projectile using $dR/d\theta = 0$"},
        {"subject": "Thermodynamics", "semester": "Sem 2-3", "how": "Rate of change of temperature, pressure, and entropy. Partial derivatives for thermodynamic potentials.", "example": r"Joule-Thomson coefficient $\mu_{JT} = (\partial T/\partial P)_H$"},
        {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "Instantaneous current as derivative of charge. Voltage across inductor.", "example": r"Transient analysis: finding $di/dt$ at $t=0^+$ when switch closes"},
        {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Velocity gradient, strain rate, and viscosity. Bernoulli equation derivation.", "example": r"Shear stress $\tau = \mu\,du/dy$ in viscous flow"},
                {"subject": "Control Systems", "semester": "Sem 4-5", "how": "Transfer function derivation. Sensitivity analysis using derivatives.", "example": r"Gain margin and phase margin calculations"}
    ]},
    "partial_diff": {"connections": [
        {"subject": "Heat Transfer", "semester": "Sem 3-4", "how": "Heat equation with partial derivatives in temperature.", "example": r"Steady-state temperature in a 2D plate"},
        {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Continuity equation, Navier-Stokes equations are PDEs.", "example": r"Incompressibility $\partial u/\partial x + \partial v/\partial y = 0$"},
        {"subject": "Electromagnetics", "semester": "Sem 3-4", "how": "Maxwell equations are PDEs in fields.", "example": r"Wave equation $\nabla^2 E = \mu\epsilon\,\partial^2 E/\partial t^2$"},
        {"subject": "Thermodynamics", "semester": "Sem 2-3", "how": "Maxwell relations use mixed partial derivatives.", "example": r"$(\partial S/\partial V)_T = (\partial P/\partial T)_V$"},
        {"subject": "Structural Analysis", "semester": "Sem 3-4", "how": "Beam and plate bending equations involve higher partial derivatives.", "example": r"Plate bending: $\partial^4 w/\partial x^4 = q/D$"}
    ]},
    "integral_calc": {"connections": [
        {"subject": "Engineering Mechanics", "semester": "Sem 1-2", "how": "Centre of mass, moment of inertia, work done by variable force.", "example": r"Moment of inertia $I = \int r^2\,dm$"},
        {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "Energy stored, RMS value of AC signals.", "example": r"Charge $q = \int_0^T i(t)\,dt$"},
        {"subject": "Signals and Systems", "semester": "Sem 3-4", "how": "Convolution integral, energy and power of signals.", "example": r"Output $y(t) = \int x(\tau)h(t-\tau)\,d\tau$"},
        {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Flow rate, pressure force, buoyancy.", "example": r"Volume flow rate $Q = \iint \vec{v}\cdot d\vec{A}$"},
        {"subject": "Heat Transfer", "semester": "Sem 3-4", "how": "Total heat transfer by integrating heat equation.", "example": r"Total heat $Q = \int_0^L kA\,(dT/dx)\,dx$"}
    ]},
    "infinite_series": {"connections": [
        {"subject": "Signals and Systems", "semester": "Sem 3-4", "how": "Fourier series expresses periodic signals as infinite series.", "example": r"Square wave: $\sum (1/n)\sin(n\omega_0 t)$"},
        {"subject": "Numerical Methods", "semester": "Sem 4", "how": "Taylor series is basis of every numerical approximation.", "example": r"Newton-Raphson uses $f(x+h) \approx f(x) + hf'(x)$"},
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": "Bode plot approximations and stability use series.", "example": r"Gain approximation near corner frequency"},
        {"subject": "Digital Communications", "semester": "Sem 5-6", "how": "Shannon entropy as series, channel capacity.", "example": r"$H = -\sum p_i\log p_i$"}
    ]},
    "linear_algebra": {"connections": [
        {"subject": "Structural Analysis", "semester": "Sem 3-4", "how": "Stiffness matrix method: entire analysis is [K]{u} = {F}.", "example": r"Truss analysis: 20 unknown forces solved by matrix methods"},
        {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "Mesh and node analysis give systems of linear equations.", "example": r"KVL gives $[Z][I] = [V]$ solved by matrix inverse"},
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": r"State-space $\dot{x} = Ax + Bu$. Eigenvalues determine stability.", "example": r"System stable iff all eigenvalues of $A$ have negative real parts"},
        {"subject": "Machine Learning", "semester": "Sem 6+", "how": "Linear regression, PCA, neural networks built on linear algebra.", "example": r"Principal components are eigenvectors of covariance matrix"},
        {"subject": "Image Processing", "semester": "Sem 5-6", "how": "Transformations, filtering, compression using matrix operations.", "example": r"SVD compression: $A = U\Sigma V^T$"}
    ]},
    "ode_first": {"connections": [
        {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "RC and RL circuits give first-order ODEs.", "example": r"RC circuit: $R\,dq/dt + q/C = V(t)$"},
        {"subject": "Engineering Mechanics", "semester": "Sem 1-2", "how": "Newton second law with variable force.", "example": r"Projectile with drag: $m\,dv/dt = mg - kv$"},
        {"subject": "Chemical Engineering", "semester": "Sem 3-4", "how": "Reaction kinetics, mixing problems.", "example": r"First-order reaction: $dC/dt = -kC$"},
        {"subject": "Biomedical Engineering", "semester": "Sem 4+", "how": "Drug concentration, population models.", "example": r"Drug decay: $dC/dt = -\lambda C$"}
    ]},
    "ode_higher": {"connections": [
        {"subject": "Electrical Circuits", "semester": "Sem 2-3", "how": "RLC circuits give second-order ODEs.", "example": r"Series RLC: $L\,d^2q/dt^2 + R\,dq/dt + q/C = V(t)$"},
        {"subject": "Mechanical Vibrations", "semester": "Sem 3-4", "how": "Every vibrating system is a second-order ODE.", "example": r"Mass-spring-damper: $m\ddot{x} + c\dot{x} + kx = F(t)$"},
        {"subject": "Structural Analysis", "semester": "Sem 3-4", "how": "Beam deflection is a fourth-order ODE.", "example": r"Euler-Bernoulli: $EI\,d^4y/dx^4 = w(x)$"},
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": "Second-order system response: overshoot, settling time.", "example": r"$\ddot{y} + 2\zeta\omega_n\dot{y} + \omega_n^2 y = \omega_n^2 u$"}
    ]},
    "laplace": {"connections": [
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": "Transfer function G(s) = Y(s)/U(s). Entire design in s-domain.", "example": r"PID controller: $C(s) = K_p + K_i/s + K_d s$"},
        {"subject": "Electrical Circuits", "semester": "Sem 3", "how": "Impedance in s-domain makes circuit analysis algebraic.", "example": r"Voltage divider in s-domain: no differential equations"},
        {"subject": "Signals and Systems", "semester": "Sem 3-4", "how": "System analysis using poles and zeros.", "example": r"Stable iff all poles in left half s-plane"},
        {"subject": "Digital Signal Processing", "semester": "Sem 5", "how": "Z-transform is discrete-time equivalent.", "example": r"Relationship $z = e^{sT}$"},
        {"subject": "Communications", "semester": "Sem 4-5", "how": "Modulation, filtering, channel analysis.", "example": r"Bandwidth of AM signal from Laplace transform"}
    ]},
    "vector_calc": {"connections": [
        {"subject": "Electromagnetics", "semester": "Sem 3-4", "how": "Maxwell equations in vector calculus form.", "example": r"Gauss law: $\nabla\cdot\vec{E} = \rho/\epsilon_0$"},
        {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Velocity field, vorticity, continuity equation.", "example": r"Irrotational: $\nabla\times\vec{v} = 0$"},
        {"subject": "Heat Transfer", "semester": "Sem 3-4", "how": "Heat flux vector, Fourier law.", "example": r"$\vec{q} = -k\nabla T$"},
        {"subject": "Structural Mechanics", "semester": "Sem 3-4", "how": "Stress tensors, displacement fields.", "example": r"Strain energy $U = \iiint \sigma_{ij}\epsilon_{ij}\,dV$"}
    ]},
    "complex_analysis": {"connections": [
        {"subject": "Electrical Circuits", "semester": "Sem 2-3", "how": "Phasors are complex numbers. Impedance Z = R + jX.", "example": r"AC analysis: $V = IZ$ with complex quantities"},
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": "Nyquist plot, root locus in complex s-plane.", "example": r"Nyquist stability uses contour integration"},
        {"subject": "Signals and Systems", "semester": "Sem 3-4", "how": r"Frequency response $H(j\omega)$ is complex.", "example": r"Bode plot: magnitude $|H(j\omega)|$ and phase"},
        {"subject": "Electromagnetics", "semester": "Sem 3-4", "how": "Complex permittivity, wave propagation.", "example": r"Skin depth from imaginary part of propagation constant"}
    ]},
    "fourier_series": {"connections": [
        {"subject": "Signals and Systems", "semester": "Sem 3-4", "how": "Every periodic signal is a Fourier series.", "example": r"Square wave: $\sum_{n=odd} (4/n\pi)\sin(n\omega_0 t)$"},
        {"subject": "Communications", "semester": "Sem 4-5", "how": "Modulation analysis, channel bandwidth.", "example": r"AM signal spectrum analysis"},
        {"subject": "Digital Signal Processing", "semester": "Sem 5", "how": "DFT and FFT are discrete Fourier series.", "example": r"FFT: $O(N\log N)$ vs $O(N^2)$"},
        {"subject": "Mechanical Vibrations", "semester": "Sem 3-4", "how": "Periodic forcing expanded as Fourier series.", "example": r"Engine vibration at harmonics of rotation frequency"}
    ]},
    "probability": {"connections": [
        {"subject": "Communications", "semester": "Sem 4-5", "how": "Bit error rate, noise analysis, channel capacity.", "example": r"BER for BPSK: $P_e = Q(\sqrt{2E_b/N_0})$"},
        {"subject": "Reliability Engineering", "semester": "Sem 5-6", "how": "Failure probability, MTTF, reliability function.", "example": r"Exponential failure: $R(t) = e^{-\lambda t}$"},
        {"subject": "Control Systems", "semester": "Sem 5", "how": "Stochastic control, Kalman filter.", "example": r"Kalman gain minimises mean square error"},
        {"subject": "Machine Learning", "semester": "Sem 6+", "how": "Bayesian inference, probabilistic models.", "example": r"Bayes classifier: $P(C|x) \propto P(x|C)P(C)$"},
        {"subject": "Quality Control", "semester": "Sem 5-6", "how": "Statistical process control, Six Sigma.", "example": r"Control limits at $\mu \pm 3\sigma$"}
    ]},
    "numerical": {"connections": [
        {"subject": "Computer Science", "semester": "Sem 2+", "how": "Every numerical method implemented as algorithm.", "example": r"scipy.integrate.odeint implements RK4"},
        {"subject": "Structural Analysis", "semester": "Sem 3-4", "how": "Finite Element Method uses numerical integration.", "example": r"FEM stiffness matrix assembled by numerical integration"},
        {"subject": "Fluid Mechanics", "semester": "Sem 4-5", "how": "CFD solves Navier-Stokes numerically.", "example": r"Finite difference: $\partial u/\partial t + u\,\partial u/\partial x = 0$"},
        {"subject": "Heat Transfer", "semester": "Sem 4", "how": "Numerical solution when analytical impossible.", "example": r"Crank-Nicolson scheme for transient conduction"}
    ]},
    "transforms": {"connections": [
        {"subject": "Digital Signal Processing", "semester": "Sem 5", "how": "Z-transform fundamental to DSP. Filter design.", "example": r"Digital filter $H(z) = Y(z)/X(z)$ — poles inside unit circle"},
        {"subject": "Communications", "semester": "Sem 4-5", "how": "Fourier transform gives frequency spectrum.", "example": r"Bandwidth of sinc pulse $= 1/T$ Hz"},
        {"subject": "Control Systems", "semester": "Sem 5", "how": "Discrete-time control uses Z-transform.", "example": r"Digital PID designed in z-domain"},
        {"subject": "Image Processing", "semester": "Sem 5-6", "how": "2D Fourier transform for filtering, compression.", "example": r"JPEG uses Discrete Cosine Transform"}
    ]}
}

# ══════════════════════════════════════════════════════════════
#  FORMAT RULES
# ══════════════════════════════════════════════════════════════
ENG_FORMAT = """
OUTPUT FORMAT RULES — STRICTLY FOLLOW:
- Write inline math as $...$ and standalone equations on their own line as


$$
...
$$


- NEVER put $...$ math on the same line as an ALL-CAPS section header
- Math always goes on a NEW LINE below the section header
- Use ALL-CAPS section headers followed by colon: SECTION NAME:
- Never use markdown headers: no #, ##, ### ever
- Never use bold/italic markers: no **, *, __ ever
- College exam level only — semester exam standard, not competitive
- Include at least 2 fully worked numerical examples per response
- Every theorem must state: Name, Statement, Conditions, Proof sketch
- Every step must be mathematically rigorous and verifiable
- Double-check all numerical calculations before presenting
"""

GATE_FORMAT = """
OUTPUT FORMAT RULES — STRICTLY FOLLOW:
- Write inline math as $...$ and standalone equations on their own line as


$$
...
$$


- NEVER put $...$ math on the same line as an ALL-CAPS section header
- Math always goes on a NEW LINE below the section header
- Use ALL-CAPS section headers followed by colon: SECTION NAME:
- Never use markdown headers: no #, ##, ### ever
- Never use bold/italic markers: no **, *, __ ever
- GATE exam level — conceptual depth with time pressure awareness
- Every answer must be mathematically rigorous and verifiable
- For MCQ: explain why EACH wrong option is wrong
- For NAT: show exact numerical answer with units
- Double-check all calculations — accuracy is paramount
- Time estimate for each problem
"""

ENG_CONTEXT = """You are MathSphere Engineering by Anupam Nigam.
You are teaching B.Tech engineering students in India (IIT/NIT/Mumbai University/VTU/Anna University level).
Difficulty: College examination level — semester exam standard only.
Style: Clear, precise, like a brilliant IIT professor explaining to first/second year students.
Always use engineering applications and examples where possible.
ACCURACY IS PARAMOUNT: Double-check every calculation. Every formula must be correct.
If you are unsure about any fact, say so explicitly rather than guessing.
"""

GATE_CONTEXT = """You are MathSphere GATE Preparation by Anupam Nigam.
You are preparing students for GATE, IIT JAM, CSIR NET, and NBHM examinations.
Difficulty: Competitive exam level — conceptual depth with tricky applications.
Style: Precise, efficient, focused on problem-solving speed and accuracy.
Every answer must be mathematically rigorous. No hand-waving.
ACCURACY IS PARAMOUNT: Double-check every calculation. Every formula must be correct.
If you are unsure about any fact, say so explicitly rather than guessing.
Focus on:
- Common traps and distractors in MCQ options
- Quick methods that save time in competitive exams
- Conceptual understanding that catches trick questions
- Negative marking awareness
"""

# ══════════════════════════════════════════════════════════════
#  PROMPT BUILDERS — University Level
# ══════════════════════════════════════════════════════════════
def build_learn_prompt(topic_key, subtopic, section):
    guidance = get_subtopic_guidance(subtopic)
    guidance_block = f"\nSPECIFIC GUIDANCE FOR THIS SUBTOPIC:\n{guidance}\n" if guidance else ""
    topic_label = get_topic_label(topic_key) if topic_key else "Engineering Mathematics"

    sections = {
        "definition": f"""Give the complete formal definition of {subtopic} for engineering mathematics.
Topic area: {topic_label}
{guidance_block}
DEFINITION:
[Precise mathematical definition. Every symbol explained. Use standard Indian university notation.]

INTUITION:
[1-2 sentences: physical or geometric meaning for an engineering student]

NOTATION:
[Standard notation used in Mumbai University / VTU / Anna University examinations]

KEY CONDITIONS:
[When this definition applies. All exceptions and edge cases.]

SIMPLE EXAMPLE:
[One concrete numerical example with specific numbers — not abstract letters]

ENGINEERING APPLICATION:
[One sentence: where exactly this appears in an engineering subject]
""",
        "theorem": f"""State and explain all major theorems related to {subtopic}.
Topic area: {topic_label}
{guidance_block}
For EACH theorem use this EXACT structure:

THEOREM NAME:
[Full official name]

EXAM WEIGHT:
[Typical marks in university exam: e.g. "2 marks for statement, 8 marks for proof"]

STATEMENT:
[Precise mathematical statement — every condition spelled out]

CONDITIONS:
[List every hypothesis that must be satisfied — examiners deduct marks if these are skipped]

PROOF:
[Complete step-by-step proof. Every equation on its own line as


$$
...
$$


]

GEOMETRIC MEANING:
[Visual or physical interpretation]

EXAMINER EXPECTS:
[Specific phrases, notation, or steps the examiner wants to see]

COROLLARY:
[Important results that follow directly]
""",
        "examples": f"""Provide 5 fully worked examples on {subtopic} at engineering university examination level.
Topic area: {topic_label}
{guidance_block}
For EACH example use this EXACT structure:

EXAMPLE [N] — [2 marks / 4 marks / 6 marks]:
[Problem statement with specific numbers. Every equation as


$$
...
$$


]

SOLUTION:
[Step-by-step. Every equation on its own line as


$$
...
$$


. No steps skipped.]
[Label each step clearly]

MARKS BREAKDOWN:
[Step 1: what it earns. Step 2: what it earns. Etc. Total must add to stated marks.]

FINAL ANSWER:


$$
[answer]
$$



COMMON MISTAKE:
[One specific error students make on this type]

Cover: 2 problems at 2 marks, 2 problems at 4 marks, 1 problem at 6-8 marks.
VERIFY EVERY CALCULATION before presenting. Accuracy is non-negotiable.
""",
        "practice": f"""Generate 8 practice problems on {subtopic} in university examination style.
Topic area: {topic_label}
{guidance_block}
Include:
- 3 short answer problems (2 marks each) — direct formula application
- 3 medium problems (4 marks each) — multi-step with some analysis
- 2 long problems (6-8 marks each) — proof or extended application

For each problem:

PROBLEM [N] ([marks] Marks) — [Mumbai University / VTU / Anna University style]:
[Problem statement. All equations as


$$
...
$$


]

HINT:
[One line pointing in the right direction without giving it away]

MARKS BREAKDOWN:
[How marks are distributed across steps]

ANSWER:


$$
[final answer — no working]
$$


VERIFY every answer is correct before presenting.
""",
        "intuition": f"""You are explaining {subtopic} to a B.Tech engineering student who is confused
and wants to understand what is actually happening — not just formulas.
Topic area: {topic_label}

Your goal: build the picture in their mind BEFORE showing any formula.
Write like 3Blue1Brown — warm, visual, story-driven, wonder-filled.
Every analogy must use something an engineering student already knows physically.

THE STORY:
[2-3 sentences: the real human problem or physical situation that made this concept necessary.
Name a real engineer, scientist, or physical phenomenon. Make it feel like history, not a textbook.]

THE PHYSICAL ANALOGY:
[3-4 sentences: connect this concept to something the student has physically experienced.
Use: springs, circuits, water flow, rotating shafts, signals, heat, bridges — things engineering students know.
No abstract mathematics yet. Just the feeling of what is happening.]

WHAT YOUR BRAIN IS ACTUALLY DOING:
[2-3 sentences: describe the mental image or geometric picture.
"Picture this..." or "Imagine you are..." — make them see it with eyes closed.]

THE KEY INSIGHT IN ONE LINE:
[One sentence capturing the entire concept without a single symbol.
This is the sentence they will remember 10 years from now.]

NOW THE MATHEMATICS:
[Now introduce the formula — but explain every symbol as something from the analogy above.
Each symbol should map to something physical they just visualised.]


$$
[the key formula]
$$



WHY EACH PART OF THE FORMULA MAKES SENSE:
[Go through each term: "The [symbol] represents [physical thing from the analogy]..."]

THE MOMENT IT CLICKS:
[Describe the exact moment of understanding — the "aha" — using the analogy.
What changes when you truly understand this? What can you now see that you could not before?]

ENGINEERING CONNECTION:
[2-3 sentences: exactly where this appears in their engineering degree.
Name the specific subject, the specific equation, the specific application.
"In your 3rd semester Control Systems course, this concept appears as..."]

WHAT HAPPENS WITHOUT THIS CONCEPT:
[1-2 sentences: what engineering problems become impossible to solve without this mathematics.
Make them feel why this matters — not just that it does.]

INTUITION CHECK:
[One question they can answer purely from the picture — no formula needed.
If they can answer it, they truly understood. If not, re-read the analogy.]

VISUAL RESOURCE:
[One real URL — prefer 3Blue1Brown, NPTEL, or MIT OCW video for this exact topic]

TONE: Warm, curious, enthusiastic. Like a brilliant professor who genuinely loves this topic
and cannot wait to show you why it is beautiful. Never condescending. Never dry.
Start with the story — never with a formula.
"""
    }
    return ENG_CONTEXT + "\n" + ENG_FORMAT + "\n\n" + sections.get(section, sections["definition"])


def build_revision_prompt(topic_key, subtopic):
    guidance = get_subtopic_guidance(subtopic)
    guidance_block = f"\nKEY FOCUS FOR THIS SUBTOPIC: {guidance}\n" if guidance else ""
    topic_label = get_topic_label(topic_key) if topic_key else "Engineering Mathematics"

    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Generate a complete Quick Revision sheet for {subtopic}.
Topic area: {topic_label}
{guidance_block}
This is for a student revising the night before an examination.
Bullet points only — no lengthy explanations.

KEY FORMULAS:
[Every important formula on its own line as


$$
...
$$


]
[Label each formula with its name]

STANDARD RESULTS TO MEMORISE:
[5-8 results that appear most in university papers. Each as


$$
...
$$


]

CONDITIONS TO STATE:
[List every condition/hypothesis the examiner expects to see written — skipping these loses marks]

QUICK TRICKS:
- [Trick 1 that saves time in exam]
- [Trick 2]
- [Trick 3]

COMMON MISTAKES:
- [Mistake 1 with why it is wrong]
- [Mistake 2]
- [Mistake 3]

EXAMINER EXPECTS:
[3-4 specific things examiners look for in this topic — exact phrases, notation, steps that earn marks]
[This is what separates full marks from partial marks]

MUST-KNOW THEOREMS:
[Each theorem: Name — one line statement — exam marks typically awarded]

EXAM TIPS:
- [How questions on this topic typically appear in university papers]
- [Time allocation: how many minutes per mark]
- [Presentation tip for full marks]

VERIFY all formulas are mathematically correct before presenting.
"""


def build_pyq_prompt(topic_key, subtopic, university, difficulty):
    diff_map = {
        "easy":   "2-4 mark straightforward application questions",
        "medium": "4-6 mark multi-step problems requiring method selection",
        "hard":   "6-10 mark long answer questions requiring proof or derivation"
    }
    univ_map = {
        "all":    "various Indian universities (Mumbai University, VTU Bangalore, Anna University Chennai, AKTU Lucknow, Pune University, GTU Gujarat, JNTU Hyderabad)",
        "mumbai": "University of Mumbai (BE First Year Engineering)",
        "vtu":    "Visvesvaraya Technological University (VTU) Bangalore",
        "anna":   "Anna University Chennai (B.E/B.Tech First Year)",
        "aktu":   "AKTU Dr. APJ Abdul Kalam Technical University Lucknow",
        "abroad": "international universities (Cambridge Engineering Tripos, MIT OpenCourseWare style, University of Toronto)"
    }
    guidance = get_subtopic_guidance(subtopic)
    guidance_block = f"\nKEY CONTENT FOR THIS SUBTOPIC: {guidance}\n" if guidance else ""

    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Provide 5 previous year examination questions on {subtopic} from {univ_map.get(university, univ_map['all'])}.
Difficulty: {diff_map.get(difficulty, diff_map['medium'])}
{guidance_block}

IMPORTANT: Mark every question as REPRESENTATIVE (typical exam-level question in the style of this university).
Do NOT claim a question appeared in a specific year unless you are 100% certain.

For EACH question use this EXACT structure:

QUESTION [N]: [University Style] · [[marks] Marks]

STATUS: REPRESENTATIVE
(These are typical exam-level questions in the style of this university's papers.)

QUESTION TEXT:
[Full question. Every equation on its own line as


$$
...
$$


]

APPROACH:
[1-2 sentences: exact technique or theorem to apply and why]

COMPLETE SOLUTION:
[Step-by-step solution. Every equation on its own line as


$$
...
$$


. No steps skipped.]

MARKS BREAKDOWN — STEP BY STEP:
[Step 1 — [description]: [N] mark(s)]
[Step 2 — [description]: [N] mark(s)]
[Total marks accounted for]

FINAL ANSWER:


$$
[answer]
$$



VERIFICATION:
[Show the check explicitly — substitute back or use alternative method]

COMMON MISTAKE ON THIS PROBLEM:
[The specific error students most often make]

EXAM STRATEGY:
[One sentence: how to approach this type quickly under exam pressure]

After all 5 questions add:

TOPIC ANALYSIS:
[How frequently this appears, which sub-types are most common]

PREPARATION STRATEGY:
- [Most important concept to master]
- [Most common question type to practice]
- [One thing that separates full marks from partial marks]

VERIFY every solution is mathematically correct. Double-check all calculations.
"""


def build_mocktest_prompt(topic_key, subtopic, num_q, marks_each):
    total = num_q * marks_each
    time_min = num_q * marks_each * 2
    guidance = get_subtopic_guidance(subtopic)
    guidance_block = f"\nCONTENT GUIDANCE: {guidance}\n" if guidance else ""

    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Generate a complete mock examination paper on {subtopic}.
{guidance_block}
Total questions: {num_q} | Marks per question: {marks_each} | Total marks: {total}
Time allowed: {time_min} minutes

Format exactly like a university examination paper.

MOCK TEST — {subtopic.upper()}
Total Marks: {total} | Time: {time_min} minutes
Instructions: Attempt ALL questions. Show complete working.

For EACH question:

QUESTION [N]: ({marks_each} Marks)
[Question with all equations as


$$
...
$$


]

Difficulty distribution: 40% straightforward, 40% multi-step, 20% proof or derivation.

After ALL questions add:

COMPLETE SOLUTIONS

SOLUTION [N]:
[Complete step-by-step working. Every equation as


$$
...
$$


]

MARKS BREAKDOWN:
[Step 1 — description: N mark(s)]
[Step 2 — description: N mark(s)]
[Continue until {marks_each} marks accounted for]

FINAL ANSWER:


$$
[answer]
$$



End with:

SELF-ASSESSMENT GUIDE:
[{total*8//10}+ marks: Excellent]
[{total*6//10}-{total*8//10-1} marks: Good]
[{total*4//10}-{total*6//10-1} marks: Fair]
[Below {total*4//10} marks: Revise fundamentals first]

VERIFY every solution is mathematically correct. Double-check all calculations.
"""


def build_formula_booklet_prompt(topic_key, subtopic):
    guidance = get_subtopic_guidance(subtopic)
    guidance_block = f"\nESSENTIAL CONTENT: {guidance}\n" if guidance else ""

    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Generate a complete exam-ready Formula Booklet entry for {subtopic}.
{guidance_block}
Format exactly as a university formula sheet — precise, complete, exam-focused.

FORMULA BOOKLET — {subtopic.upper()}

For EACH formula use this EXACT structure:

FORMULA [N]: [Official Formula Name]

FORMULA:


$$
[the complete formula — every symbol defined]
$$



PHYSICAL MEANING:
[One sentence: what this formula computes]

WHEN TO USE:
[Specific conditions under which this formula applies]

DO NOT USE WHEN:
[Common mistake — when students incorrectly apply this formula]

QUICK EXAMPLE:
[One specific numerical example: given values to answer in 3-4 lines]

After all formulas add:

STANDARD RESULTS TABLE:
[All key results together — each as


$$
...
$$


]

ENGINEERING SUBJECTS USING THIS:
[List subjects with one specific use-case each]

Generate minimum 8 formulas. Be complete.
VERIFY every formula is mathematically correct.
"""


def build_ask_prompt(question):
    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
A B.Tech engineering student asks: {question}

Answer at college examination level — semester exam standard.
Show all working. Every equation on its own line as


$$
...
$$


Include at least one worked numerical example with specific numbers.
If relevant, mention which engineering subject uses this concept and how.

VERIFY all calculations are correct before presenting.
End with CONFIDENCE: HIGH / MEDIUM / LOW
"""


def build_solve_prompt(problem, topic_key=""):
    guidance = ""
    if topic_key:
        topic_label = get_topic_label(topic_key)
        guidance = f"\nThis problem is from the topic area: {topic_label}\n"

    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
A B.Tech engineering student needs a complete step-by-step solution.
{guidance}

PROBLEM:
{problem}

Solve this COMPLETELY using this EXACT structure:

PROBLEM CLASSIFICATION:
[Topic → Subtopic → Exact method/theorem to use]
[Why this method: one sentence explaining why this approach works]

PREREQUISITES CHECK:
[List 2-3 concepts the student must know before attempting this]

STEP-BY-STEP SOLUTION:

STEP 1: [Clear description of what we are doing]
[Working with every equation on its own line as


$$
...
$$


]
[Explain WHY we do this step — not just HOW]

STEP 2: [Clear description]
[Working...]

[Continue for ALL steps — skip NOTHING]

FINAL ANSWER:


$$
[boxed answer]
$$



VERIFICATION:
[Substitute back or use alternative method to confirm the answer is correct]

MARKS BREAKDOWN (if this were an exam question):
[Step 1: N marks — description]
[Step 2: N marks — description]
[Total: N marks]

COMMON MISTAKES ON THIS TYPE:
- [Mistake 1: what students do wrong and why]
- [Mistake 2]

SIMILAR PROBLEMS TO PRACTICE:
[List 2 similar problems with slightly different numbers]

TIME ESTIMATE:
[How many minutes this should take in an exam]

VERIFY every step is mathematically correct. Double-check the final answer.
"""


def build_compare_prompt(method1, method2, topic_key=""):
    topic_context = ""
    if topic_key:
        topic_label = get_topic_label(topic_key)
        topic_context = f"\nTopic area: {topic_label}\n"

    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Compare and contrast these two mathematical methods/concepts for engineering students:
{topic_context}
METHOD A: {method1}
METHOD B: {method2}

Use this EXACT structure:

METHOD A — {method1.upper()}:
[2-3 sentence description]
[Key formula as


$$
...
$$


]
[When to use: specific conditions]

METHOD B — {method2.upper()}:
[2-3 sentence description]
[Key formula as


$$
...
$$


]
[When to use: specific conditions]

HEAD-TO-HEAD COMPARISON:

Accuracy: Method A [comparison] vs Method B [comparison]
Speed in exam: Method A [comparison] vs Method B [comparison]
Ease of application: Method A [comparison] vs Method B [comparison]
When it fails: Method A [condition] vs Method B [condition]
Exam frequency: Method A [how often] vs Method B [how often]
Typical marks: Method A [range] vs Method B [range]

SAME PROBLEM, BOTH METHODS:
[Choose one specific numerical problem and solve it using BOTH methods]

Problem:


$$
[problem statement]
$$



Solution by Method A:
[Complete step-by-step]

Solution by Method B:
[Complete step-by-step]

WHICH TO USE WHEN:
[Decision guide in words]

EXAM STRATEGY:
[Which method to default to under time pressure and why]

ENGINEERING CONTEXT:
[Where each method appears in engineering subjects]

VERIFY all solutions are mathematically correct.
"""


def build_exam_strategy_prompt(topic_key, hours_available):
    topic_label = get_topic_label(topic_key)
    if not topic_label or topic_label == topic_key:
        topic_label = topic_key

    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Generate a complete exam preparation strategy for {topic_label}.
The student has {hours_available} hours before the exam.

EXAM STRATEGY — {topic_label.upper()}
Available Time: {hours_available} hours

PRIORITY MATRIX:
[Classify every subtopic into:]

MUST DO (will definitely be asked — 80% exam papers):
- [Subtopic 1]: [typical marks] — [time needed]
- [Subtopic 2]: [typical marks] — [time needed]

SHOULD DO (frequently asked — 60% papers):
- [Subtopic 1]: [typical marks] — [time needed]

GOOD TO DO (occasionally asked — 30% papers):
- [Subtopic 1]: [typical marks] — [time needed]

SKIP IF SHORT ON TIME (rarely asked alone):
- [Subtopic 1]: [why it can be skipped]

HOUR-BY-HOUR PLAN:
[Break the available {hours_available} hours into specific blocks]

Hour 1: [Exact topic + what to do]
Hour 2: [Exact topic + what to do]
[Continue for all hours]
Last 30 minutes: [What to revise in the final half hour]

GUARANTEED QUESTIONS (appear in 90%+ papers):
[List 3-5 question types that appear almost every year]

QUICK WINS (easy marks with minimal preparation):
[3-4 subtopics where memorising one formula gives guaranteed marks]

DANGER ZONES (where students commonly lose marks):
[3-4 specific mistakes to avoid]

FORMULA SHEET TO MEMORISE:
[The 10-15 most critical formulas — each as


$$
...
$$


]

LAST-MINUTE CHECKLIST:
- [ ] [Item 1]
- [ ] [Item 2]
- [ ] [Item 3]
- [ ] [Item 4]
- [ ] [Item 5]

EXAM HALL STRATEGY:
- Time per mark: [recommendation]
- Which question to attempt first: [advice]
- How to present for maximum marks: [specific tips]
"""


def build_doubt_prompt(doubt, topic_key="", subtopic=""):
    context = ""
    if topic_key:
        topic_label = get_topic_label(topic_key)
        context += f"Topic area: {topic_label}\n"
    if subtopic:
        context += f"Subtopic: {subtopic}\n"
        guidance = get_subtopic_guidance(subtopic)
        if guidance:
            context += f"Key content: {guidance}\n"

    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
A B.Tech engineering student has a doubt. They are confused and need help.
{context}

STUDENT'S DOUBT:
{doubt}

Your job: figure out EXACTLY where the confusion is and fix it.

WHAT I THINK YOU ARE CONFUSED ABOUT:
[Identify the precise point of confusion]

THE SOURCE OF CONFUSION:
[Why this is confusing — what two things is the student mixing up?]

THE CLEAR EXPLANATION:
[Explain the correct understanding step by step.]
[Every equation on its own line as


$$
...
$$


]

THE KEY DISTINCTION:
[If the confusion involves two similar things, make a clear comparison]

CONCRETE EXAMPLE:
[One specific numerical example that makes the concept crystal clear]
[Full working shown]

VISUAL/PHYSICAL ANALOGY:
[One analogy from engineering or daily life]

HOW TO REMEMBER THIS:
[One memory trick or one-liner that prevents this confusion from recurring]

RELATED EXAM QUESTION:
[One exam-style question that tests exactly this understanding]


$$
[question]
$$



ANSWER:


$$
[answer with key steps]
$$



VERIFY all explanations and calculations are correct.

CONFIDENCE THAT I ADDRESSED YOUR DOUBT: HIGH / MEDIUM / LOW
"""


# ══════════════════════════════════════════════════════════════
#
#  GATE / IIT JAM / CSIR NET / NBHM — COMPETITIVE EXAM MODULE
#
# ══════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────
#  GATE EXAM DATA — Verified from official GATE syllabus
# ──────────────────────────────────────────────
GATE_DATA = {
    "exam_info": {
        "name": "Graduate Aptitude Test in Engineering",
        "conducting_body": "IIT (rotates annually)",
        "official_website": "https://gate.iitk.ac.in/",
        "math_weightage": "13% of total marks (approximately 15 marks out of 100)",
        "question_types": {
            "MCQ": {
                "marks": [1, 2],
                "negative_marking": "1/3 for 1-mark, 2/3 for 2-mark",
                "description": "Multiple Choice Questions with 4 options"
            },
            "NAT": {
                "marks": [1, 2],
                "negative_marking": "None",
                "description": "Numerical Answer Type — enter a number"
            },
            "MSQ": {
                "marks": [1, 2],
                "negative_marking": "None",
                "description": "Multiple Select Questions — one or more correct (GATE 2024+)"
            }
        },
        "total_questions_math": "8-10 questions",
        "time_recommendation": "25-30 minutes for math section",
        "time_per_question": {
            "1_mark": "1.5-2 minutes",
            "2_mark": "3-4 minutes"
        }
    },
    "branches": {
        "cs": {
            "label": "Computer Science & IT (CS/IT)",
            "code": "GATE CS",
            "math_topics": {
                "linear_algebra":   {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "calculus":         {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "probability":      {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "combinatorics":    {"weight": "MEDIUM", "questions_per_year": "1-2", "must_do": True},
                "graph_theory":     {"weight": "MEDIUM", "questions_per_year": "1",   "must_do": False}
            },
            "specific_syllabus": [
                "Propositional and first-order logic",
                "Sets, relations, functions, partial orders, lattices",
                "Combinatorics, counting arguments",
                "Graph theory: connectivity, matching, colouring",
                "Group theory (basics)",
                "Linear algebra: matrices, determinants, systems, eigenvalues",
                "Calculus: limits, continuity, differentiation, maxima/minima, mean value theorem, integration",
                "Probability: conditional probability, Bayes theorem, distributions, uniform, normal, exponential, Poisson"
            ]
        },
        "ec": {
            "label": "Electronics & Communication (EC)",
            "code": "GATE EC",
            "math_topics": {
                "linear_algebra":   {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "calculus":         {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "diff_equations":   {"weight": "MEDIUM", "questions_per_year": "1-2", "must_do": True},
                "complex_analysis": {"weight": "MEDIUM", "questions_per_year": "1",   "must_do": True},
                "probability":      {"weight": "HIGH",   "questions_per_year": "1-2", "must_do": True},
                "numerical_methods":{"weight": "LOW",    "questions_per_year": "0-1", "must_do": False},
                "transforms":       {"weight": "MEDIUM", "questions_per_year": "1",   "must_do": True}
            },
            "specific_syllabus": [
                "Linear algebra: matrix algebra, systems, eigenvalues/eigenvectors",
                "Calculus: mean value theorems, theorems of integral calculus, partial derivatives, maxima/minima, multiple integrals, Fourier series",
                "Vector analysis: gradient, divergence, curl, Green's, Stokes', Gauss theorems",
                "Differential equations: first order, higher order with constant coefficients, Cauchy-Euler equations, initial and boundary value problems",
                "Complex analysis: analytic functions, Cauchy integral theorem/formula, Taylor/Laurent series, residue theorem",
                "Probability and statistics: sampling theorems, conditional probability, mean, median, mode, standard deviation, random variables, uniform, normal, exponential, Poisson, binomial distributions"
            ]
        },
        "me": {
            "label": "Mechanical Engineering (ME)",
            "code": "GATE ME",
            "math_topics": {
                "linear_algebra":   {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "calculus":         {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "diff_equations":   {"weight": "HIGH",   "questions_per_year": "1-2", "must_do": True},
                "complex_analysis": {"weight": "MEDIUM", "questions_per_year": "1",   "must_do": True},
                "probability":      {"weight": "MEDIUM", "questions_per_year": "1-2", "must_do": True},
                "numerical_methods":{"weight": "MEDIUM", "questions_per_year": "1",   "must_do": True}
            },
            "specific_syllabus": [
                "Linear algebra: matrix algebra, systems, eigenvalues/eigenvectors",
                "Calculus: functions of single variable, limit, continuity, differentiability, mean value theorems, theorems of integral calculus, evaluation of definite/improper integrals",
                "Partial derivatives, total derivative, maxima/minima, gradient, divergence, curl, directional derivatives, line/surface/volume integrals",
                "Stokes, Gauss, Green's theorems",
                "Differential equations: first order (linear/nonlinear), higher order with constant coefficients, Cauchy-Euler equations, initial/boundary value problems, Laplace transforms",
                "Complex variables: analytic functions, Cauchy integral theorem/formula, Taylor/Laurent series, residue theorem",
                "Probability and statistics: definitions, conditional probability, Bayes theorem, mean, median, mode, standard deviation, random variables, Poisson, normal, binomial distributions",
                "Numerical methods: numerical solutions of linear/nonlinear algebraic equations, integration (trapezoidal/Simpson's), single/multi-step methods for differential equations"
            ]
        },
        "ce": {
            "label": "Civil Engineering (CE)",
            "code": "GATE CE",
            "math_topics": {
                "linear_algebra":   {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "calculus":         {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "diff_equations":   {"weight": "MEDIUM", "questions_per_year": "1-2", "must_do": True},
                "probability":      {"weight": "HIGH",   "questions_per_year": "1-2", "must_do": True},
                "numerical_methods":{"weight": "MEDIUM", "questions_per_year": "1",   "must_do": True}
            },
            "specific_syllabus": [
                "Linear algebra: matrix algebra, systems, eigenvalues/eigenvectors",
                "Calculus: functions of single variable, limit, continuity, differentiability, mean value theorems, definite/improper integrals",
                "Partial derivatives, total derivative, maxima/minima, gradient, divergence, curl",
                "Differential equations: first order, higher order with constant coefficients",
                "Probability and statistics: conditional probability, Bayes theorem, distributions",
                "Numerical methods: numerical solutions of linear/nonlinear equations, integration, differential equations"
            ]
        },
        "ee": {
            "label": "Electrical Engineering (EE)",
            "code": "GATE EE",
            "math_topics": {
                "linear_algebra":   {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "calculus":         {"weight": "HIGH",   "questions_per_year": "2-3", "must_do": True},
                "diff_equations":   {"weight": "HIGH",   "questions_per_year": "1-2", "must_do": True},
                "complex_analysis": {"weight": "MEDIUM", "questions_per_year": "1",   "must_do": True},
                "probability":      {"weight": "MEDIUM", "questions_per_year": "1-2", "must_do": True},
                "numerical_methods":{"weight": "LOW",    "questions_per_year": "0-1", "must_do": False},
                "transforms":       {"weight": "MEDIUM", "questions_per_year": "1",   "must_do": True}
            },
            "specific_syllabus": [
                "Linear algebra: matrix algebra, systems, eigenvalues/eigenvectors",
                "Calculus: mean value theorems, theorems of integral calculus, partial derivatives, maxima/minima, multiple integrals",
                "Vector analysis: gradient, divergence, curl, Green's, Stokes', Gauss theorems",
                "Differential equations: first order, higher order with constant coefficients, Laplace transforms",
                "Complex analysis: analytic functions, Cauchy integral theorem/formula, residue theorem",
                "Probability and statistics: conditional probability, Bayes theorem, mean, median, mode, standard deviation, distributions",
                "Numerical methods: solutions of nonlinear equations, single/multi-step methods"
            ]
        }
    },
    "topic_mapping": {
        "linear_algebra":   ["linear_algebra"],
        "calculus":         ["diff_calc", "partial_diff", "integral_calc"],
        "diff_equations":   ["ode_first", "ode_higher", "laplace"],
        "complex_analysis": ["complex_analysis"],
        "probability":      ["probability"],
        "numerical_methods":["numerical"],
        "transforms":       ["transforms", "laplace"],
        "vector_analysis":  ["vector_calc"],
        "fourier":          ["fourier_series", "transforms"],
        "combinatorics":    [],
        "graph_theory":     []
    }
}

# ──────────────────────────────────────────────
#  IIT JAM DATA
# ──────────────────────────────────────────────
JAM_DATA = {
    "exam_info": {
        "name": "IIT Joint Admission Test for M.Sc.",
        "conducting_body": "IIT (rotates annually)",
        "official_website": "https://jam.iitb.ac.in/",
        "papers": {
            "mathematics": {
                "code": "MA",
                "total_marks": 100,
                "duration": "3 hours",
                "sections": {
                    "Section A": "MCQ — 30 questions (10x1 + 10x2 = 30 marks) — negative marking",
                    "Section B": "MSQ — 10 questions (10x2 = 20 marks) — no negative marking",
                    "Section C": "NAT — 20 questions (10x1 + 10x2 = 30 marks) — no negative marking"
                }
            },
            "mathematical_statistics": {
                "code": "MS",
                "total_marks": 100,
                "duration": "3 hours",
                "sections": {
                    "Section A": "MCQ — 30 questions",
                    "Section B": "MSQ — 10 questions",
                    "Section C": "NAT — 20 questions"
                }
            }
        }
    },
    "syllabus_ma": {
        "real_analysis": [
            "Sequences and series of real numbers",
            "Convergent and divergent sequences, bounded and monotone sequences",
            "Convergence criteria for sequences of real numbers",
            "Cauchy sequences",
            "Absolute and conditional convergence",
            "Tests of convergence for series — ratio test, root test, integral test, comparison test",
            "Power series — radius and interval of convergence",
            "Taylor series",
            "Limits, continuity, differentiability of functions of one variable",
            "Mean value theorems (Rolle's, Lagrange's, Cauchy's)",
            "L'Hopital's rule",
            "Maxima and minima",
            "Riemann integration — definition, properties, fundamental theorem of calculus",
            "Improper integrals",
            "Uniform continuity",
            "Sequences and series of functions — uniform convergence"
        ],
        "multivariable_calculus": [
            "Functions of several variables — limit, continuity, differentiability",
            "Partial derivatives, total derivative",
            "Maxima and minima — method of Lagrange multipliers",
            "Double and triple integrals — change of order, change of variables",
            "Line integrals, surface integrals",
            "Green's theorem, Stokes' theorem, Gauss divergence theorem"
        ],
        "linear_algebra": [
            "Finite-dimensional vector spaces",
            "Linear transformations and their matrix representations",
            "Rank, nullity, rank-nullity theorem",
            "Systems of linear equations",
            "Eigenvalues and eigenvectors",
            "Cayley-Hamilton theorem",
            "Diagonalisation",
            "Inner product spaces, orthogonality, Gram-Schmidt process",
            "Symmetric, skew-symmetric, Hermitian, skew-Hermitian, orthogonal, unitary matrices"
        ],
        "ode": [
            "First order ODEs — exact, linear, Bernoulli, substitution methods",
            "Second order linear ODEs with constant coefficients",
            "Method of variation of parameters",
            "Cauchy-Euler equations",
            "Series solutions (Frobenius method)",
            "Legendre polynomials, Bessel functions — basics",
            "Systems of first order ODEs",
            "Power series methods"
        ],
        "abstract_algebra": [
            "Groups — definition, examples, subgroups, cyclic groups",
            "Normal subgroups, quotient groups",
            "Lagrange's theorem, Cayley's theorem",
            "Group homomorphisms, isomorphisms",
            "Permutation groups",
            "Rings — definition, examples, integral domains, fields",
            "Ring homomorphisms, ideals, quotient rings",
            "Polynomial rings, irreducibility criteria"
        ]
    },
    "syllabus_ms": {
        "mathematics_component": [
            "Sequences and series, differential calculus, integral calculus",
            "Matrices and linear algebra",
            "Differential equations"
        ],
        "statistics_component": [
            "Probability axioms, conditional probability, Bayes' theorem",
            "Random variables — discrete and continuous",
            "Standard distributions: Binomial, Poisson, Normal, Uniform, Exponential, Gamma, Beta",
            "Joint distributions, marginal and conditional distributions",
            "Expectation, variance, covariance, correlation",
            "Moment generating functions and characteristic functions",
            "Chebyshev's inequality, law of large numbers, central limit theorem",
            "Sampling distributions: chi-square, t, F",
            "Estimation: point estimation, unbiasedness, consistency, efficiency, sufficiency",
            "Methods of estimation: maximum likelihood, method of moments",
            "Testing of hypotheses: Neyman-Pearson lemma, UMP tests",
            "Confidence intervals",
            "Regression analysis — simple linear regression"
        ]
    }
}

# ──────────────────────────────────────────────
#  CSIR NET DATA
# ──────────────────────────────────────────────
CSIR_NET_DATA = {
    "exam_info": {
        "name": "CSIR UGC NET for JRF and Lectureship",
        "conducting_body": "CSIR-HRDG / NTA",
        "official_website": "https://csirhrdg.res.in/",
        "subject": "Mathematical Sciences",
        "total_marks": 200,
        "duration": "3 hours",
        "sections": {
            "Part A": {"marks": 30, "questions": "15 out of 20", "level": "General aptitude, logical reasoning, quantitative"},
            "Part B": {"marks": 70, "questions": "25 out of 40", "level": "Core mathematics — must score well here"},
            "Part C": {"marks": 100, "questions": "20 out of 60", "level": "Advanced mathematics — differentiator"}
        },
        "negative_marking": "25% for wrong answer in Part A and B, no negative in Part C"
    },
    "syllabus": {
        "analysis": [
            "Elementary set theory, finite/countable/uncountable sets, real number system",
            "Sequences and series, convergence, limsup, liminf",
            "Bolzano-Weierstrass theorem, Heine-Borel theorem",
            "Continuity, uniform continuity, differentiability, mean value theorem",
            "Sequences and series of functions, uniform convergence",
            "Riemann sums and Riemann integral",
            "Improper integrals, monotone and dominated convergence",
            "Functions of several variables, directional derivative, partial derivative",
            "Metric spaces: completeness, compactness, connectedness",
            "Normed linear spaces, Banach spaces (intro)",
            "Inner product spaces, Hilbert spaces (intro)",
            "Lebesgue measure and integration (basics)"
        ],
        "linear_algebra": [
            "Vector spaces, subspaces, linear dependence, basis, dimension",
            "Linear transformations, rank-nullity",
            "Matrices: canonical forms, diagonal forms, triangular forms",
            "Inner product spaces, orthonormal basis, Gram-Schmidt",
            "Eigenvalues: algebraic and geometric multiplicity",
            "Cayley-Hamilton theorem, minimal polynomial",
            "Jordan canonical form",
            "Symmetric, skew-symmetric, Hermitian, skew-Hermitian, unitary, normal matrices",
            "Positive definite matrices, quadratic forms"
        ],
        "abstract_algebra": [
            "Groups: subgroups, normal subgroups, quotient groups, homomorphisms, isomorphisms",
            "Cyclic groups, permutation groups, Cayley's theorem, class equations",
            "Sylow theorems, direct products, finitely generated abelian groups",
            "Rings: ideals, prime and maximal ideals, quotient rings, unique factorization domains",
            "Principal ideal domains, Euclidean domains",
            "Polynomial rings, irreducibility criteria",
            "Fields: finite fields, field extensions"
        ],
        "complex_analysis": [
            "Analytic functions, Cauchy-Riemann equations",
            "Power series, radius of convergence",
            "Cauchy's theorem, Cauchy integral formula",
            "Liouville's theorem, maximum modulus principle",
            "Taylor series, Laurent series",
            "Singularities: classification",
            "Residue theorem, contour integration",
            "Conformal mappings, Mobius transformations"
        ],
        "ode_pde": [
            "Existence and uniqueness of solutions of IVPs",
            "Singular solutions, p-clairaut equations",
            "Linear ODEs: Wronskian, variation of parameters",
            "Sturm-Liouville problems, Green's functions",
            "First order PDE: method of characteristics",
            "Heat equation, wave equation, Laplace equation",
            "Separation of variables",
            "D'Alembert formula"
        ],
        "topology": [
            "Topological spaces: basis, subspace, product, quotient topologies",
            "Connectedness, compactness",
            "Countability and separation axioms",
            "Urysohn lemma, Tietze extension theorem",
            "Metrization theorems (intro)"
        ]
    }
}

# ──────────────────────────────────────────────
#  NBHM DATA
# ──────────────────────────────────────────────
NBHM_DATA = {
    "exam_info": {
        "name": "National Board for Higher Mathematics Scholarship",
        "conducting_body": "DAE-NBHM",
        "official_website": "http://www.nbhm.dae.gov.in/",
        "nature": "Proof-heavy, tests mathematical maturity",
        "duration": "3 hours",
        "total_marks": 40,
        "description": "30 questions, answer as many as possible. Partial marking. Proofs required."
    },
    "topics": [
        "Real Analysis: sequences, series, continuity, differentiability, Riemann integration",
        "Linear Algebra: vector spaces, linear transformations, eigenvalues, canonical forms",
        "Abstract Algebra: groups (up to Sylow theorems), rings, fields",
        "Complex Analysis: analytic functions, contour integration, residues",
        "Topology: metric spaces, compactness, connectedness",
        "Combinatorics: counting, pigeonhole principle, generating functions",
        "Number Theory: divisibility, congruences, primes, quadratic residues",
        "Ordinary Differential Equations: existence theorems, linear systems"
    ]
}

# ──────────────────────────────────────────────
#  COMPETITIVE EXAM TOPIC WEIGHTAGE — verified from 10+ years analysis
# ──────────────────────────────────────────────
GATE_TOPIC_ANALYSIS = {
    "linear_algebra": {
        "frequency": "Every year without exception",
        "typical_questions": 2,
        "typical_marks": "3-4 marks",
        "most_asked": [
            "Eigenvalues and eigenvectors (90% years)",
            "Rank of a matrix (80% years)",
            "System of linear equations — consistency (75% years)",
            "Cayley-Hamilton theorem (60% years)",
            "Diagonalization (50% years)",
            "Determinant properties (50% years)"
        ],
        "question_style": "Usually NAT — compute eigenvalue, find rank, solve system",
        "common_traps": [
            "Eigenvalues of A^2 are squares of eigenvalues of A — but eigenvectors may differ",
            "Rank(AB) <= min(Rank A, Rank B) — students forget this bound",
            "det(A) = 0 does NOT mean A = 0",
            "Eigenvalues of triangular matrix are diagonal elements — but students miss this shortcut"
        ],
        "time_strategy": "Eigenvalue questions: use trace and determinant shortcut for 2x2. For 3x3: find one eigenvalue by inspection, then use trace/det for others."
    },
    "calculus": {
        "frequency": "Every year without exception",
        "typical_questions": 2,
        "typical_marks": "3-4 marks",
        "most_asked": [
            "Maxima and minima (85% years)",
            "Mean value theorems — Rolle's, LMVT (70% years)",
            "Double/triple integrals (65% years)",
            "Continuity and differentiability (60% years)",
            "Gradient, divergence, curl (55% years)",
            "Green's/Stokes'/Gauss theorem (50% years)"
        ],
        "question_style": "MCQ for conceptual, NAT for computational",
        "common_traps": [
            "Differentiable everywhere does NOT mean derivative is continuous",
                        "f(x,y) continuous in x and y separately does NOT imply jointly continuous",
            "Change of order of integration — MUST draw the region first",
            "Directional derivative maximum is |grad f|, NOT grad f itself",
            "Stokes theorem needs consistent orientation — right hand rule"
        ],
        "time_strategy": "For maxima/minima: compute critical points, check second derivative test. For integrals: always check if polar/cylindrical coordinates simplify. For MVT: verify conditions first."
    },
    "probability": {
        "frequency": "Every year without exception",
        "typical_questions": 2,
        "typical_marks": "3-4 marks",
        "most_asked": [
            "Bayes theorem (80% years)",
            "Normal distribution — Z conversion (75% years)",
            "Expectation and variance (70% years)",
            "Conditional probability (65% years)",
            "Poisson distribution (50% years)",
            "Binomial distribution (45% years)"
        ],
        "question_style": "NAT for computation, MCQ for conceptual",
        "common_traps": [
            "P(A union B) != P(A) + P(B) unless mutually exclusive",
            "P(A intersect B) = P(A)P(B) ONLY if independent",
            "Variance is ALWAYS non-negative",
            "For Poisson: mean = variance = lambda — students confuse parameters",
            "Normal distribution: P(X > mu) = 0.5 — students forget symmetry"
        ],
        "time_strategy": "Bayes theorem: draw tree diagram mentally. Normal: always convert to Z first. For discrete distributions: check if problem fits Binomial/Poisson pattern."
    },
    "diff_equations": {
        "frequency": "Most years (85%+)",
        "typical_questions": 1,
        "typical_marks": "2 marks",
        "most_asked": [
            "Second order ODE with constant coefficients (75% years)",
            "First order linear ODE (60% years)",
            "Laplace transform to solve IVP (50% years)",
            "Exact equations (40% years)",
            "Euler-Cauchy equation (35% years)"
        ],
        "question_style": "Usually NAT — solve and find y(specific value)",
        "common_traps": [
            "PI failure case — when e^ax and a is root of auxiliary equation",
            "Laplace of derivative: L{y'} = sY(s) - y(0) — initial conditions appear during transform, not after",
            "Euler-Cauchy: substitute y = x^m, NOT e^mx",
            "Integrating factor: check if equation is in standard form FIRST"
        ],
        "time_strategy": "Identify type in 10 seconds. For constant coefficient: write auxiliary equation immediately. For Laplace: take transform of both sides, plug in ICs, solve algebraically."
    },
    "complex_analysis": {
        "frequency": "Most years for EC/EE/ME (70%+)",
        "typical_questions": 1,
        "typical_marks": "2 marks",
        "most_asked": [
            "Residue computation (70% years)",
            "Cauchy-Riemann equations — analyticity check (60% years)",
            "Contour integration using residue theorem (55% years)",
            "Laurent series expansion (40% years)",
            "Singularity classification (35% years)"
        ],
        "question_style": "NAT for residue values, MCQ for analyticity",
        "common_traps": [
            "z-bar (conjugate) is NOT analytic — most common GATE trap",
            "Residue formula differs for simple pole vs higher order pole",
            "Laurent series depends on the annular region — different regions give different series",
            "Cauchy theorem applies only in simply connected domains"
        ],
        "time_strategy": "Residue at simple pole: use limit formula directly. For analyticity: check CR equations — if one fails, immediately mark not analytic."
    },
    "numerical_methods": {
        "frequency": "60-70% years",
        "typical_questions": 1,
        "typical_marks": "2 marks",
        "most_asked": [
            "Newton-Raphson iteration (60% years)",
            "Trapezoidal/Simpson's rule (55% years)",
            "Bisection method (30% years)",
            "Runge-Kutta (25% years)"
        ],
        "question_style": "NAT — compute next iteration or integral value",
        "common_traps": [
            "Newton-Raphson can diverge — check f'(x) != 0",
            "Simpson's 1/3 needs EVEN number of subintervals",
            "Trapezoidal rule error is O(h^2), Simpson's is O(h^4) — students confuse",
            "In bisection: always check that f(a)*f(b) < 0"
        ],
        "time_strategy": "For N-R: one iteration is usually enough for GATE. For integration: apply formula directly — no derivation needed."
    },
    "transforms": {
        "frequency": "50-60% years for EC/EE",
        "typical_questions": 1,
        "typical_marks": "2 marks",
        "most_asked": [
            "Laplace transform pairs (60% years)",
            "Z-transform ROC (40% years)",
            "Fourier series coefficients (35% years)",
            "Inverse Laplace using partial fractions (30% years)"
        ],
        "question_style": "NAT for computation, MCQ for ROC/convergence",
        "common_traps": [
            "L{f*g} = F(s).G(s) — product of transforms is convolution, NOT product of functions",
            "Z-transform: ALWAYS state ROC",
            "Fourier series: check even/odd BEFORE computing — saves half the work",
            "Shifting theorems: first shifting is in s-domain, second is in t-domain"
        ],
        "time_strategy": "Memorize standard Laplace/Z pairs. For inverse Laplace: partial fractions then table lookup."
    }
}

# ──────────────────────────────────────────────
#  GATE-SPECIFIC MISCONCEPTIONS
# ──────────────────────────────────────────────
GATE_MISCONCEPTIONS = {
    "linear_algebra": [
        {
            "id": "G_LA01",
            "misconception": "If eigenvalues of A are lambda_1, lambda_2, then eigenvalues of A+kI are lambda_1+k, lambda_2+k",
            "truth": "TRUE — this is correct! Eigenvalues of A+kI are indeed lambda_i + k. Students sometimes doubt this correct fact.",
            "gate_relevance": "Frequently used as a shortcut in GATE. If you know eigenvalues of A, you immediately know eigenvalues of A+kI, kA, A^n, A^(-1).",
            "danger": "MEDIUM",
            "trap_question": "If eigenvalues of A are 2 and 5, what are eigenvalues of A^2 - 3A + 2I?",
            "answer": "For lambda=2: 4-6+2=0. For lambda=5: 25-15+2=12. Answer: 0 and 12.",
            "shortcut": "For any polynomial p(A), eigenvalues are p(lambda_i). This saves enormous time in GATE."
        },
        {
            "id": "G_LA02",
            "misconception": "A matrix with rank r always has exactly r non-zero eigenvalues",
            "truth": "FALSE — rank equals number of non-zero eigenvalues only for diagonalizable matrices. For non-diagonalizable, the relationship is rank >= number of non-zero eigenvalues.",
            "gate_relevance": "GATE sometimes gives a nilpotent matrix (all eigenvalues 0) with non-zero rank.",
            "danger": "HIGH",
            "trap_question": "A = [[0,1],[0,0]]. Find rank and eigenvalues.",
            "answer": "Rank = 1 (non-zero row in REF). Eigenvalues: both 0 (characteristic equation lambda^2 = 0). So rank=1 but no non-zero eigenvalues.",
            "shortcut": "Rank = n - nullity. For eigenvalue 0: geometric multiplicity = nullity of A."
        },
        {
            "id": "G_LA03",
            "misconception": "If det(A) = 0, then all eigenvalues are 0",
            "truth": "FALSE — det(A) = product of all eigenvalues. If det=0, at least ONE eigenvalue is 0, not all.",
            "gate_relevance": "Direct GATE trap. They give det=0 and ask how many eigenvalues are zero.",
            "danger": "HIGH",
            "trap_question": "A 3x3 matrix has eigenvalues 0, 2, 5. What is det(A)?",
            "answer": "det(A) = 0 x 2 x 5 = 0. Conversely if det=0, only one eigenvalue needs to be 0.",
            "shortcut": "det(A) = product of eigenvalues. trace(A) = sum of eigenvalues. Two equations, very powerful for 2x2."
        },
        {
            "id": "G_LA04",
            "misconception": "Eigenvectors of distinct eigenvalues are always orthogonal",
            "truth": "FALSE — eigenvectors of distinct eigenvalues are LINEARLY INDEPENDENT but orthogonal only for SYMMETRIC matrices.",
            "gate_relevance": "GATE tests this distinction. They ask: 'A has distinct eigenvalues. Are eigenvectors orthogonal?' Answer: not necessarily.",
            "danger": "CRITICAL",
            "trap_question": "A = [[2,1],[0,3]]. Find eigenvectors. Are they orthogonal?",
            "answer": "Lambda=2: v1=(1,0). Lambda=3: v2=(-1,1). v1.v2 = -1 != 0. NOT orthogonal. They would be orthogonal only if A were symmetric.",
            "shortcut": "Symmetric matrix => orthogonal eigenvectors. Non-symmetric => only linearly independent."
        }
    ],
    "calculus": [
        {
            "id": "G_CA01",
            "misconception": "If f is differentiable everywhere, f' must be continuous",
            "truth": "FALSE — Darboux's theorem says f' has intermediate value property, but f' can be discontinuous. Classic example: f(x) = x^2 sin(1/x) for x!=0, f(0)=0.",
            "gate_relevance": "GATE loves this conceptual trap. They ask: true or false — differentiable implies derivative is continuous.",
            "danger": "CRITICAL",
            "trap_question": "f(x) = x^2 sin(1/x) for x!=0, f(0)=0. Is f differentiable at x=0? Is f' continuous at x=0?",
            "answer": "f'(0) = lim h->0 [h^2 sin(1/h)]/h = lim h sin(1/h) = 0. So f'(0) exists. But f'(x) = 2x sin(1/x) - cos(1/x) for x!=0. As x->0, cos(1/x) oscillates. So f' is NOT continuous at 0.",
            "shortcut": "Differentiable everywhere: YES. Derivative continuous: NOT necessarily. Continuously differentiable (C^1) is a STRONGER condition."
        },
        {
            "id": "G_CA02",
            "misconception": "If partial derivatives exist at a point, the function is differentiable there",
            "truth": "FALSE — for f(x,y), existence of partial derivatives does NOT imply differentiability. Need partial derivatives to be CONTINUOUS for differentiability.",
            "gate_relevance": "GATE ME/EC frequently tests this. Standard example: f(x,y) = xy/(x^2+y^2) for (x,y)!=(0,0), f(0,0)=0.",
            "danger": "CRITICAL",
            "trap_question": "f(x,y) = xy/sqrt(x^2+y^2) for (x,y)!=(0,0), f(0,0)=0. Do partial derivatives exist at origin? Is f differentiable at origin?",
            "answer": "f_x(0,0) = lim h->0 f(h,0)/h = 0. f_y(0,0) = 0. Both exist. But check along y=x: f(x,x) = x^2/(x*sqrt(2)) = x/sqrt(2). Not differentiable at origin because limit of [f(h,k) - f(0,0) - 0*h - 0*k]/sqrt(h^2+k^2) depends on direction.",
            "shortcut": "Partial derivatives exist + continuous => differentiable. Partial derivatives exist alone is NOT enough in 2+ variables."
        },
        {
            "id": "G_CA03",
            "misconception": "Double integral always equals iterated integral",
            "truth": "TRUE only when function is continuous (or satisfies Fubini conditions). For discontinuous functions, Fubini may fail.",
            "gate_relevance": "GATE asks: when can you interchange order of integration? Answer: Fubini's theorem conditions.",
            "danger": "HIGH",
            "trap_question": "When is it valid to write integral integral f(x,y) dA = integral(integral f(x,y) dx) dy?",
            "answer": "Valid when: (1) f is continuous on the region, or (2) f is measurable and integral of |f| is finite (Fubini-Tonelli). For GATE: assume continuous unless told otherwise.",
            "shortcut": "Continuous function on bounded closed region: always safe to interchange. Otherwise: check absolute integrability."
        }
    ],
    "probability": [
        {
            "id": "G_PR01",
            "misconception": "For normal distribution, P(X = a) is found from the PDF",
            "truth": "FALSE — for continuous distributions, P(X = a) = 0 for any specific value a. Only P(a < X < b) makes sense.",
            "gate_relevance": "GATE sometimes asks P(X = 5) for X ~ N(mu, sigma^2). Answer is ALWAYS 0.",
            "danger": "HIGH",
            "trap_question": "X ~ N(0,1). Find P(X = 0).",
            "answer": "P(X = 0) = 0. For continuous random variable, probability at any single point is 0. Only P(a < X < b) = integral_a^b f(x) dx makes sense.",
            "shortcut": "Continuous RV: point probability = 0. Only interval probabilities matter."
        },
        {
            "id": "G_PR02",
            "misconception": "Uncorrelated random variables are independent",
            "truth": "FALSE — uncorrelated means Cov(X,Y) = 0 which means E[XY] = E[X]E[Y]. Independence is a STRONGER condition. Uncorrelated + jointly normal => independent.",
            "gate_relevance": "Classic GATE conceptual question. Standard counterexample: X ~ N(0,1), Y = X^2. Then Cov(X,Y) = E[X^3] = 0 but clearly dependent.",
            "danger": "CRITICAL",
            "trap_question": "X ~ N(0,1), Y = X^2. Are X and Y uncorrelated? Are they independent?",
            "answer": "Cov(X,Y) = E[XY] - E[X]E[Y] = E[X^3] - 0 = 0 (since X^3 is odd function, symmetric distribution). So uncorrelated: YES. Independent: NO (Y is completely determined by X).",
            "shortcut": "Independent => uncorrelated (always). Uncorrelated => independent (ONLY if jointly normal)."
        },
        {
            "id": "G_PR03",
            "misconception": "E[g(X)] = g(E[X]) for any function g",
            "truth": "FALSE — this is Jensen's inequality territory. E[g(X)] = g(E[X]) only if g is linear (affine). For convex g: E[g(X)] >= g(E[X]). For concave g: reversed.",
            "gate_relevance": "GATE trap: E[X^2] != (E[X])^2. In fact E[X^2] = Var(X) + (E[X])^2 >= (E[X])^2.",
            "danger": "CRITICAL",
            "trap_question": "X ~ Uniform(0,1). Find E[X^2] and (E[X])^2. Are they equal?",
            "answer": "E[X] = 1/2, so (E[X])^2 = 1/4. E[X^2] = integral_0^1 x^2 dx = 1/3. They are NOT equal. Difference = Var(X) = 1/3 - 1/4 = 1/12.",
            "shortcut": "E[X^2] >= (E[X])^2 always. Equality only when Var(X) = 0 (constant)."
        }
    ],
    "diff_equations": [
        {
            "id": "G_DE01",
            "misconception": "The general solution of a second order ODE always has exactly 2 arbitrary constants",
            "truth": "TRUE for linear ODEs. But for nonlinear ODEs, singular solutions may exist that cannot be obtained from the general solution for any value of constants.",
            "gate_relevance": "GATE asks: 'How many arbitrary constants in the general solution of a 2nd order ODE?' Answer: 2 (for linear). But watch for singular solutions in nonlinear.",
            "danger": "MEDIUM",
            "trap_question": "y = cx + c^2 is the general solution of a first order ODE. Can you find ALL solutions?",
            "answer": "General solution: y = cx + c^2 (one-parameter family). But there may be a singular solution: eliminate c from y = cx + c^2 and dy/dx = c. This gives the envelope y = -x^2/4, which is a solution not obtainable from any value of c.",
            "shortcut": "Linear ODE: general solution is complete. Nonlinear: check for singular solutions using p-discriminant method."
        },
        {
            "id": "G_DE02",
            "misconception": "Laplace transform can solve any ODE",
            "truth": "FALSE — Laplace transform works best for LINEAR ODEs with CONSTANT coefficients and given INITIAL conditions. For variable coefficients or boundary value problems, other methods are needed.",
            "gate_relevance": "GATE sometimes gives a variable coefficient ODE and asks which method to use. Laplace is NOT the answer.",
            "danger": "MEDIUM",
            "trap_question": "Which method works for: x^2 y'' + xy' + (x^2 - n^2)y = 0?",
            "answer": "This is Bessel's equation — a variable coefficient ODE. Laplace transform is NOT suitable. Use Frobenius (series) method. Solution: J_n(x) and Y_n(x).",
            "shortcut": "Constant coefficients + IVP => Laplace. Variable coefficients => power series/Frobenius. Boundary value => Sturm-Liouville."
        }
    ],
    "complex_analysis": [
        {
            "id": "G_CX01",
            "misconception": "If f(z) is differentiable as a real function of two variables, it is analytic",
            "truth": "FALSE — analytic means COMPLEX differentiable, which requires Cauchy-Riemann equations to be satisfied. Real differentiability is weaker.",
            "gate_relevance": "GATE's favourite question: Is f(z) = |z|^2 analytic? Answer: f = x^2+y^2. u=x^2+y^2, v=0. CR: u_x=2x should equal v_y=0. Only at origin. So analytic NOWHERE (not even at origin because analytic requires open set).",
            "danger": "CRITICAL",
            "trap_question": "Where is f(z) = |z|^2 analytic?",
            "answer": "NOWHERE. u = x^2+y^2, v = 0. CR equations: u_x = 2x = v_y = 0 => x=0. u_y = 2y = -v_x = 0 => y=0. CR satisfied only at (0,0). But analytic requires CR in a neighbourhood, not just a point. So f is differentiable at z=0 but analytic NOWHERE.",
            "shortcut": "Analytic = CR equations satisfied in an OPEN SET. Single point is not enough."
        },
        {
            "id": "G_CX02",
            "misconception": "Residue at a pole can always be found by the formula lim(z->z0) (z-z0)f(z)",
            "truth": "FALSE — this formula works only for SIMPLE poles (order 1). For pole of order m, use the general formula involving (m-1)th derivative.",
            "gate_relevance": "GATE gives poles of order 2 or 3 and tests whether students know the general formula.",
            "danger": "HIGH",
            "trap_question": "Find residue of f(z) = 1/(z-1)^3 at z=1.",
            "answer": "Pole of order 3. Residue = (1/2!) lim(z->1) d^2/dz^2 [(z-1)^3 * 1/(z-1)^3] = (1/2) lim d^2/dz^2 [1] = 0.",
            "shortcut": "Simple pole: Res = lim (z-z0)f(z). Order m pole: Res = (1/(m-1)!) lim d^(m-1)/dz^(m-1) [(z-z0)^m f(z)]. For Laurent series: residue = coefficient of (z-z0)^(-1)."
        }
    ]
}

# ──────────────────────────────────────────────
#  GATE QUICK FORMULAS — One-page cheat sheet
# ──────────────────────────────────────────────
GATE_QUICK_FORMULAS = {
    "linear_algebra_shortcuts": {
        "label": "Linear Algebra — GATE Shortcuts",
        "formulas": [
            {"name": "Eigenvalue of kA", "formula": "If Ax = λx, then (kA)x = kλx", "condition": "k is scalar"},
            {"name": "Eigenvalue of A^n", "formula": "If Ax = λx, then A^n x = λ^n x", "condition": "n positive integer"},
            {"name": "Eigenvalue of A^(-1)", "formula": "If Ax = λx and λ≠0, then A^(-1)x = (1/λ)x", "condition": "A invertible"},
            {"name": "Eigenvalue of A+kI", "formula": "If Ax = λx, then (A+kI)x = (λ+k)x", "condition": "k is scalar"},
            {"name": "Eigenvalue of p(A)", "formula": "If Ax = λx, then p(A)x = p(λ)x", "condition": "p is polynomial"},
            {"name": "Trace-Det shortcut for 2x2", "formula": "λ² - (trace)λ + det = 0", "condition": "2x2 matrix only"},
            {"name": "3x3 characteristic equation", "formula": "λ³ - (trace)λ² + (sum of cofactors of diagonal)λ - det = 0", "condition": "3x3 matrix"},
            {"name": "Rank-Nullity", "formula": "Rank(A) + Nullity(A) = n (number of columns)", "condition": "Always"},
            {"name": "Cayley-Hamilton shortcut", "formula": "A satisfies its own characteristic equation — use to find A^(-1) and higher powers", "condition": "Every square matrix"},
            {"name": "Symmetric eigenvalues", "formula": "Symmetric matrix always has REAL eigenvalues and ORTHOGONAL eigenvectors", "condition": "A = A^T"},
        ]
    },
    "calculus_shortcuts": {
        "label": "Calculus — GATE Shortcuts",
        "formulas": [
            {"name": "Rolle's conditions", "formula": "f continuous on [a,b], differentiable on (a,b), f(a)=f(b) => exists c: f'(c)=0", "condition": "All three conditions required"},
            {"name": "LMVT", "formula": "[f(b)-f(a)]/(b-a) = f'(c) for some c in (a,b)", "condition": "f continuous on [a,b], differentiable on (a,b)"},
            {"name": "Maxima test (2 variables)", "formula": "D = f_xx·f_yy - (f_xy)² > 0 and f_xx < 0 => maximum", "condition": "At critical point"},
            {"name": "Minima test (2 variables)", "formula": "D = f_xx·f_yy - (f_xy)² > 0 and f_xx > 0 => minimum", "condition": "At critical point"},
            {"name": "Saddle point test", "formula": "D = f_xx·f_yy - (f_xy)² < 0 => saddle point", "condition": "At critical point"},
            {"name": "Directional derivative", "formula": "D_u f = ∇f · û = |∇f| cos θ", "condition": "û is unit vector"},
            {"name": "Max directional derivative", "formula": "Maximum rate of change = |∇f| in direction of ∇f", "condition": "At given point"},
            {"name": "Green's theorem", "formula": "∮(M dx + N dy) = ∬(∂N/∂x - ∂M/∂y) dA", "condition": "C positive (counterclockwise)"},
            {"name": "Stokes' theorem", "formula": "∬(∇×F)·dS = ∮ F·dr", "condition": "Right-hand rule for orientation"},
            {"name": "Gauss theorem", "formula": "∭(∇·F) dV = ∯ F·dS", "condition": "Outward normal"},
        ]
    },
    "probability_shortcuts": {
        "label": "Probability — GATE Shortcuts",
        "formulas": [
            {"name": "Bayes theorem", "formula": "P(A|B) = P(B|A)P(A) / P(B)", "condition": "P(B) > 0"},
            {"name": "Total probability", "formula": "P(B) = Σ P(B|Aᵢ)P(Aᵢ)", "condition": "Aᵢ partition sample space"},
            {"name": "Binomial mean/var", "formula": "E(X) = np, Var(X) = npq", "condition": "X ~ Bin(n,p), q=1-p"},
            {"name": "Poisson mean/var", "formula": "E(X) = Var(X) = λ", "condition": "X ~ Poi(λ)"},
            {"name": "Normal standardization", "formula": "Z = (X-μ)/σ ~ N(0,1)", "condition": "X ~ N(μ,σ²)"},
            {"name": "Exponential memoryless", "formula": "P(X > s+t | X > s) = P(X > t)", "condition": "X ~ Exp(λ)"},
            {"name": "Variance formula", "formula": "Var(X) = E(X²) - [E(X)]²", "condition": "Always"},
            {"name": "Covariance formula", "formula": "Cov(X,Y) = E(XY) - E(X)E(Y)", "condition": "Always"},
            {"name": "Var of sum", "formula": "Var(aX+bY) = a²Var(X) + b²Var(Y) + 2ab·Cov(X,Y)", "condition": "Always"},
            {"name": "Independent => uncorrelated", "formula": "Independent => Cov(X,Y) = 0, but NOT converse", "condition": "Converse true only if jointly normal"},
        ]
    },
    "de_shortcuts": {
        "label": "Differential Equations — GATE Shortcuts",
        "formulas": [
            {"name": "CF: distinct real roots", "formula": "y = c₁e^(m₁x) + c₂e^(m₂x)", "condition": "Auxiliary eq has distinct real roots m₁, m₂"},
            {"name": "CF: repeated roots", "formula": "y = (c₁ + c₂x)e^(mx)", "condition": "Auxiliary eq has repeated root m"},
            {"name": "CF: complex roots", "formula": "y = e^(αx)(c₁cos βx + c₂sin βx)", "condition": "Roots α ± iβ"},
            {"name": "PI: e^(ax)", "formula": "PI = e^(ax)/f(a), if f(a)≠0", "condition": "f(D) is characteristic polynomial"},
            {"name": "PI: e^(ax) failure", "formula": "If f(a)=0, PI = x·e^(ax)/f'(a). If f'(a)=0, PI = x²·e^(ax)/f''(a)", "condition": "a is root of auxiliary eq"},
            {"name": "PI: sin(ax) or cos(ax)", "formula": "Replace D² with -a² in f(D)", "condition": "f(D) contains only even powers of D"},
            {"name": "Laplace of derivative", "formula": "L{y'} = sY(s) - y(0)", "condition": "Y(s) = L{y}"},
            {"name": "Laplace of 2nd derivative", "formula": "L{y''} = s²Y(s) - sy(0) - y'(0)", "condition": "Initial conditions plug in here"},
            {"name": "Euler-Cauchy substitution", "formula": "x = e^t converts x²y'' + xy' + y = 0 to constant coefficient", "condition": "Equation has x^n·y^(n) pattern"},
            {"name": "Convolution", "formula": "L⁻¹{F(s)G(s)} = f*g = ∫₀ᵗ f(τ)g(t-τ)dτ", "condition": "Use when F(s)G(s) appears"},
        ]
    },
    "complex_shortcuts": {
        "label": "Complex Analysis — GATE Shortcuts",
        "formulas": [
            {"name": "CR equations (Cartesian)", "formula": "u_x = v_y and u_y = -v_x", "condition": "f = u + iv is analytic"},
            {"name": "Residue at simple pole", "formula": "Res(f, z₀) = lim(z→z₀) (z-z₀)f(z)", "condition": "z₀ is simple pole"},
            {"name": "Residue at simple pole (ratio)", "formula": "Res(p/q, z₀) = p(z₀)/q'(z₀)", "condition": "q(z₀)=0, q'(z₀)≠0"},
            {"name": "Residue at pole of order m", "formula": "Res = (1/(m-1)!) lim d^(m-1)/dz^(m-1) [(z-z₀)^m f(z)]", "condition": "z₀ is pole of order m"},
            {"name": "Residue theorem", "formula": "∮_C f(z)dz = 2πi × Σ(residues inside C)", "condition": "C is positively oriented"},
            {"name": "Cauchy integral formula", "formula": "f(z₀) = (1/2πi) ∮ f(z)/(z-z₀) dz", "condition": "f analytic inside C, z₀ inside C"},
            {"name": "nth derivative formula", "formula": "f^(n)(z₀) = (n!/2πi) ∮ f(z)/(z-z₀)^(n+1) dz", "condition": "f analytic inside C"},
            {"name": "Liouville's theorem", "formula": "Bounded entire function is constant", "condition": "f analytic everywhere and |f| bounded"},
        ]
    }
}

# ══════════════════════════════════════════════════════════════
#  GATE PROMPT BUILDERS
# ══════════════════════════════════════════════════════════════

def build_gate_practice_prompt(topic_key, subtopic, branch, difficulty, question_type):
    branch_info = GATE_DATA["branches"].get(branch, GATE_DATA["branches"]["cs"])
    branch_label = branch_info["label"]
    topic_analysis = GATE_TOPIC_ANALYSIS.get(topic_key, {})

    traps = ""
    if topic_analysis and "common_traps" in topic_analysis:
        traps = "\nCOMMON GATE TRAPS FOR THIS TOPIC:\n" + "\n".join(f"- {t}" for t in topic_analysis["common_traps"])

    type_instruction = {
        "mcq": """Generate MCQ with exactly 4 options (A, B, C, D).
Exactly ONE option is correct.
Design distractors based on common calculation errors and misconceptions.
After the solution, explain WHY each wrong option is wrong — what specific error leads to it.""",
        "nat": """Generate NAT (Numerical Answer Type) question.
Student must compute exact numerical answer.
Answer should be an integer or decimal (up to 2 decimal places).
Show complete computation in solution.""",
        "msq": """Generate MSQ (Multiple Select Question) with exactly 4 options.
ONE or MORE options may be correct.
Student must select ALL correct options for full marks.
After solution, clearly state which options are correct and why each."""
    }

    diff_instruction = {
        "easy": "1-mark level — direct formula application, solvable in 1-2 minutes",
        "medium": "2-mark level — requires 2-3 step reasoning, solvable in 3-4 minutes",
        "hard": "2-mark tricky — requires deep conceptual understanding or clever shortcut, designed to trap unprepared students"
    }

    return GATE_CONTEXT + "\n" + GATE_FORMAT + f"""
Generate 5 GATE-style practice questions on {subtopic} for {branch_label}.
Difficulty: {diff_instruction.get(difficulty, diff_instruction['medium'])}
Question type: {type_instruction.get(question_type, type_instruction['mcq'])}
{traps}

For EACH question use this EXACT structure:

QUESTION [N]: GATE {branch.upper()} Style · {question_type.upper()} · [1 mark / 2 marks]

QUESTION:
[Complete question text. Every equation as


$$
...
$$


]

[For MCQ/MSQ: List options A, B, C, D]

SOLUTION:
[Complete step-by-step solution]
[Every equation on its own line]
[Show the FASTEST method — GATE is time-pressured]

CORRECT ANSWER: [answer]

[For MCQ: WHY EACH WRONG OPTION IS WRONG:
Option A: [if wrong — what error leads here]
Option B: [if wrong — what error leads here]
etc.]

TIME TO SOLVE: [minutes]

GATE SHORTCUT:
[If there is a faster method than the standard approach, show it here]

TRAP ALERT:
[What specific mistake GATE expects students to make on this type]

After all 5 questions:

TOPIC PATTERN ANALYSIS:
[How this subtopic typically appears in GATE {branch.upper()}]
[Which years it appeared and in what form]

PREPARATION PRIORITY:
[How important this subtopic is for GATE {branch.upper()} — HIGH/MEDIUM/LOW]
[Recommended practice: how many questions to solve before exam]

VERIFY every answer is mathematically correct. Double-check all calculations.
GATE answers must be EXACT — no approximation errors allowed.
"""


def build_gate_mock_prompt(branch, num_questions, time_minutes):
    branch_info = GATE_DATA["branches"].get(branch, GATE_DATA["branches"]["cs"])
    branch_label = branch_info["label"]
    syllabus_points = branch_info.get("specific_syllabus", [])
    syllabus_text = "\n".join(f"- {s}" for s in syllabus_points)

    return GATE_CONTEXT + "\n" + GATE_FORMAT + f"""
Generate a COMPLETE GATE Mathematics mock test for {branch_label}.

GATE MATH MOCK TEST — {branch_label.upper()}
Questions: {num_questions} | Time: {time_minutes} minutes
Pattern: Mix of MCQ, NAT, and MSQ

Syllabus covered:
{syllabus_text}

Distribution:
- 1-mark questions: {num_questions // 2} questions (MCQ + NAT mix)
- 2-mark questions: {num_questions - num_questions // 2} questions (MCQ + NAT + MSQ mix)

IMPORTANT RULES:
- MCQ: 4 options, exactly one correct. Negative marking: -1/3 for 1-mark, -2/3 for 2-mark.
- NAT: Numerical answer. No negative marking.
- MSQ: 4 options, one or more correct. No negative marking.

For EACH question:

Q[N]. ([1/2] mark) [MCQ/NAT/MSQ]
[Question text with equations as


$$
...
$$


]
[For MCQ/MSQ: (A) ... (B) ... (C) ... (D) ...]

After ALL questions:

ANSWER KEY:
Q1: [answer] | Q2: [answer] | ...

DETAILED SOLUTIONS:

Solution Q[N]:
[Complete solution with every step]
[For MCQ: explain why wrong options are wrong]
[For NAT: show complete computation]
[Time estimate: X minutes]

SCORING GUIDE:
{num_questions * 15 // (num_questions)}+ marks: Excellent — GATE ready
{num_questions * 10 // (num_questions)}-{num_questions * 15 // (num_questions) - 1} marks: Good — focus on weak areas
Below {num_questions * 10 // (num_questions)} marks: Needs significant practice

TOPIC-WISE ANALYSIS:
[Which topics each question covers — helps identify weak areas]

VERIFY every answer is mathematically correct. GATE-level accuracy required.
"""


def build_gate_strategy_prompt(branch, months_remaining):
    branch_info = GATE_DATA["branches"].get(branch, GATE_DATA["branches"]["cs"])
    branch_label = branch_info["label"]
    math_topics = branch_info.get("math_topics", {})

    topic_list = "\n".join(
        f"- {topic}: Weight {info['weight']}, ~{info['questions_per_year']} questions/year, Must do: {'YES' if info['must_do'] else 'Optional'}"
        for topic, info in math_topics.items()
    )

    return GATE_CONTEXT + "\n" + GATE_FORMAT + f"""
Generate a COMPLETE GATE Mathematics preparation strategy for {branch_label}.
Time remaining: {months_remaining} months.

BRANCH-SPECIFIC TOPIC ANALYSIS:
{topic_list}

GATE MATH PREPARATION STRATEGY — {branch_label.upper()}
Time: {months_remaining} months remaining

PRIORITY ORDER (study these in this exact sequence):
[Rank every math topic by importance for this specific branch]
[For each: expected marks, typical question types, preparation time needed]

MONTH-BY-MONTH PLAN:
[Break {months_remaining} months into specific study blocks]

Month 1: [Topics + what to cover + resources]
Month 2: [Topics + what to cover + resources]
[Continue for all months]
Last week: [Revision strategy]
Exam day: [Time management plan]

GUARANTEED MARKS (appear EVERY year in GATE {branch.upper()}):
[List 3-5 question types that appear every year with exact approach]
[These alone can give 6-8 marks — never skip these]

HIGH-ROI SHORTCUTS:
[5-7 shortcuts that save time in GATE math section]
[Each with example of how it is used]

NEGATIVE MARKING STRATEGY:
[When to attempt MCQ vs when to skip]
[NAT questions: always attempt (no negative marking)]
[Risk-reward analysis for guessing]

COMMON GATE TRAPS FOR {branch.upper()}:
[5-6 specific traps that GATE setters use for this branch]
[How to identify and avoid each trap]

TOPIC-WISE QUESTION BANK:
[For each topic: how many practice questions to solve before exam]
[Recommended sources]

REVISION FORMULA SHEET:
[The 20 most important formulas for GATE {branch.upper()} math]
[Each as


$$
...
$$


]

EXAM DAY STRATEGY:
- Time allocation: [how to split 180 minutes]
- Which section to attempt first: [recommendation]
- When to leave a question: [time limit per question]
- Last 15 minutes: [what to do]

CUTOFF CONTEXT:
[Approximate math marks needed for different GATE ranks]
[Scoring 12+ out of 15 in math can significantly boost overall rank]
"""


def build_jam_practice_prompt(subtopic, paper_code, difficulty):
    paper_info = "IIT JAM Mathematics (MA)" if paper_code == "ma" else "IIT JAM Mathematical Statistics (MS)"

    diff_instruction = {
        "easy": "Section A style — MCQ, 1-2 marks, direct application",
        "medium": "Section B style — MSQ, 2 marks, requires careful analysis",
        "hard": "Section C style — NAT, 1-2 marks, requires deep understanding or computation"
    }

    return GATE_CONTEXT + "\n" + GATE_FORMAT + f"""
Generate 5 IIT JAM style practice questions on {subtopic} for {paper_info}.
Difficulty: {diff_instruction.get(difficulty, diff_instruction['medium'])}

IIT JAM tests CONCEPTUAL DEPTH more than GATE.
Questions should test understanding, not just formula application.

For EACH question:

QUESTION [N]: JAM {paper_code.upper()} Style · [Section A/B/C] · [1/2 marks]

QUESTION:
[Complete question. Equations as


$$
...
$$


]
[Options if MCQ/MSQ]

SOLUTION:
[Complete solution]
[Focus on conceptual reasoning, not just computation]

CORRECT ANSWER: [answer]

CONCEPT TESTED:
[What specific concept this question probes]

JAM TIP:
[How JAM questions on this topic differ from GATE]

After all questions:

JAM vs GATE COMPARISON:
[How this topic is tested differently in JAM vs GATE]

VERIFY every answer. JAM requires mathematical precision.
"""


def build_csir_net_practice_prompt(subtopic, part, difficulty):
    part_info = {
        "a": "Part A — General aptitude, logical reasoning (2 marks each, negative marking)",
        "b": "Part B — Core mathematics (3.5-5 marks, negative marking)",
        "c": "Part C — Advanced mathematics (5 marks each, NO negative marking)"
    }

    return GATE_CONTEXT + "\n" + GATE_FORMAT + f"""
Generate 5 CSIR NET Mathematical Sciences style questions on {subtopic}.
Section: {part_info.get(part, part_info['b'])}
Difficulty: {difficulty}

CSIR NET tests MATHEMATICAL MATURITY and PROOF ABILITY.
Part B tests core concepts rigorously.
Part C tests advanced topics — no negative marking encourages attempting.

For EACH question:

QUESTION [N]: CSIR NET Style · {part_info.get(part, 'Part B')} · [marks]

QUESTION:
[Complete question. For Part B/C: may involve proofs, counterexamples, or deep reasoning]

SOLUTION:
[Complete solution with rigorous justification]
[For proofs: every logical step must be justified]

KEY CONCEPT:
[What mathematical concept this tests]

NET TIP:
[How to approach this type efficiently in CSIR NET]

After all questions:

PART B vs PART C STRATEGY:
[How to decide which questions to attempt in each part]
[Time allocation between parts]

VERIFY mathematical rigor of every proof and solution.
"""


# ══════════════════════════════════════════════════════════════
#  MISCONCEPTION DATABASE — University Level (Original)
# ══════════════════════════════════════════════════════════════
MISCONCEPTIONS = {
    "diff_calc": [
        {
            "id": "DC01",
            "misconception": "If a function is continuous at a point, it must be differentiable there",
            "danger": "HIGH",
            "question": "The function f(x) = |x| is continuous at x = 0. Is it differentiable at x = 0? Explain why or why not in your own words.",
            "correct": "Continuity does NOT imply differentiability. f(x)=|x| is continuous at x=0 but has a sharp corner — the left derivative is -1 and the right derivative is +1, so the derivative does not exist. Differentiability implies continuity but not the other way around.",
            "why_students_believe_it": "Students confuse the theorem 'differentiable implies continuous' with its converse, which is false."
        },
        {
            "id": "DC02",
            "misconception": "L'Hopital's Rule can be applied to any limit",
            "danger": "HIGH",
            "question": "Can you apply L'Hopital's Rule to find lim(x->2) (x^2-4)/(x-2)? What must you check first?",
            "correct": "L'Hopital's Rule applies ONLY when the limit gives an indeterminate form 0/0 or inf/inf. The limit (x^2-4)/(x-2) at x=2 gives 0/0 — so L'Hopital applies. But you must ALWAYS verify the indeterminate form first.",
            "why_students_believe_it": "Students see L'Hopital as a shortcut and apply it without checking conditions."
        },
        {
            "id": "DC03",
            "misconception": "A function can have at most one tangent line at any point",
            "danger": "MEDIUM",
            "question": "If f'(c) = 0 at some point c, what does the tangent line look like? Does the function have to have a maximum or minimum at c?",
            "correct": "f'(c) = 0 means a horizontal tangent — but this could be a maximum, minimum, OR a point of inflection (like f(x)=x^3 at x=0). Students must check the second derivative or sign change of f' to classify critical points.",
            "why_students_believe_it": "Students memorise 'set derivative to zero to find maxima/minima' without understanding that f'(c)=0 is necessary but not sufficient."
        },
        {
            "id": "DC04",
            "misconception": "Taylor series always converges to the function",
            "danger": "HIGH",
            "question": "If I write the Taylor series of f(x) around x=0 and sum infinitely many terms, do I always get f(x)?",
            "correct": "No. A function must be analytic for its Taylor series to converge to it. The Taylor series may converge to a different function or diverge entirely outside the radius of convergence.",
            "why_students_believe_it": "Students work only with standard functions (sin, cos, e^x) whose Taylor series converge everywhere."
        },
        {
            "id": "DC05",
            "misconception": "The derivative of a product is the product of derivatives",
            "danger": "CRITICAL",
            "question": "What is the derivative of f(x) = x^2 * sin(x)? Write your first instinct, then verify.",
            "correct": "d/dx(uv) = u*(dv/dx) + v*(du/dx). NOT d/dx(uv) = (du/dx)*(dv/dx). The correct answer is x^2*cos(x) + 2x*sin(x).",
            "why_students_believe_it": "Analogy with exponent rules: (uv)^n = u^n*v^n. Students incorrectly extend this pattern to derivatives."
        }
    ],
    "partial_diff": [
        {
            "id": "PD01",
            "misconception": "Mixed partial derivatives are always equal",
            "danger": "MEDIUM",
            "question": "Is it always true that d^2f/dxdy = d^2f/dydx for any function f(x,y)?",
            "correct": "Clairaut's theorem states mixed partials are equal ONLY if both mixed partials are continuous in a neighbourhood of the point.",
            "why_students_believe_it": "Clairaut's theorem is taught without emphasis on its conditions."
        },
        {
            "id": "PD02",
            "misconception": "If both partial derivatives exist, the function is differentiable",
            "danger": "HIGH",
            "question": "If df/dx and df/dy both exist at a point, does that guarantee f is differentiable there?",
            "correct": "No. Existence of partial derivatives does NOT imply differentiability. A function can have both partial derivatives existing at a point while being discontinuous there.",
            "why_students_believe_it": "Single-variable analogy: if f'(x) exists, f is differentiable. This does not extend to multiple variables."
        },
        {
            "id": "PD03",
            "misconception": "Euler's theorem applies to all functions of two variables",
            "danger": "HIGH",
            "question": "Can you apply Euler's theorem to f(x,y) = x^2 + y^2 + 1? Why or why not?",
            "correct": "Euler's theorem applies ONLY to homogeneous functions of degree n. f(x,y) = x^2+y^2+1 is NOT homogeneous because of the constant term.",
            "why_students_believe_it": "Students apply Euler's theorem mechanically without checking the homogeneity condition."
        }
    ],
    "integral_calc": [
        {
            "id": "IC01",
            "misconception": "If the integral of f from a to b is zero, then f must be zero",
            "danger": "HIGH",
            "question": "If integral from 0 to pi of sin(x) dx = 0... wait, does it? Calculate it. What does a zero integral actually mean geometrically?",
            "correct": "Integral from 0 to pi of sin(x) dx = 2, not zero. But integral from 0 to 2pi of sin(x) dx = 0 even though sin(x) is never identically zero. A zero integral means positive and negative areas cancel.",
            "why_students_believe_it": "Students think of integration as measuring 'total function value' rather than signed area."
        },
        {
            "id": "IC02",
            "misconception": "Integration and differentiation always undo each other perfectly",
            "danger": "MEDIUM",
            "question": "If F(x) = integral from 0 to x of f(t)dt, is it always true that F'(x) = f(x)?",
            "correct": "Yes — but only when f is continuous. The Fundamental Theorem of Calculus requires continuity of f. Also the constant of integration is critical.",
            "why_students_believe_it": "The relationship is taught as absolute without stating continuity requirements."
        },
        {
            "id": "IC03",
            "misconception": "The order of integration in double integrals can always be swapped without changing limits",
            "danger": "CRITICAL",
            "question": "To change the order of integral_0^1 integral_x^1 f(x,y) dy dx, can you just write integral_0^1 integral_0^1 f(x,y) dx dy?",
            "correct": "No — changing the order of integration ALWAYS requires rewriting the limits by sketching the region.",
            "why_students_believe_it": "Students think of double integrals as two independent single integrals."
        },
        {
            "id": "IC04",
            "misconception": "Beta function B(m,n) = B(n,m) means the integral limits are symmetric",
            "danger": "MEDIUM",
            "question": "Why is B(m,n) = B(n,m)? Is it because the limits of integration are symmetric?",
            "correct": "The symmetry B(m,n)=B(n,m) comes from the substitution x->(1-x), not from symmetric limits.",
            "why_students_believe_it": "Students see the result is symmetric and assume the reason is symmetry of limits."
        }
    ],
    "infinite_series": [
        {
            "id": "IS01",
            "misconception": "If the nth term goes to zero, the series converges",
            "danger": "CRITICAL",
            "question": "The harmonic series has terms 1/n -> 0. Does it converge?",
            "correct": "No — the harmonic series sum(1/n) diverges even though 1/n -> 0. The nth term going to zero is NECESSARY but NOT SUFFICIENT for convergence.",
            "why_students_believe_it": "The divergence test is taught as the first test, and students incorrectly apply its contrapositive."
        },
        {
            "id": "IS02",
            "misconception": "Absolute convergence and conditional convergence give the same sum",
            "danger": "HIGH",
            "question": "The alternating harmonic series sum((-1)^(n+1)/n) converges to ln(2). If we rearrange its terms, do we still get ln(2)?",
            "correct": "No — by the Riemann rearrangement theorem, a conditionally convergent series can be rearranged to converge to ANY real number.",
            "why_students_believe_it": "Students assume addition is commutative for infinite sums, just as it is for finite sums."
        },
        {
            "id": "IS03",
            "misconception": "The ratio test always gives a conclusive answer",
            "danger": "MEDIUM",
            "question": "Apply the ratio test to sum(1/n^2). What happens?",
            "correct": "The ratio test gives L = 1 — INCONCLUSIVE. When L=1, you must use another test.",
            "why_students_believe_it": "Students learn the ratio test as the 'universal' test and don't know what to do when it fails."
        }
    ],
    "linear_algebra": [
        {
            "id": "LA01",
            "misconception": "Eigenvalues are always real numbers",
            "danger": "HIGH",
            "question": "Find the eigenvalues of the matrix [[0, -1], [1, 0]]. Are they real?",
            "correct": "The characteristic equation is lambda^2+1=0, giving lambda=+/-i — complex eigenvalues. Real eigenvalues are guaranteed ONLY for symmetric matrices.",
            "why_students_believe_it": "Most textbook examples use symmetric matrices which always have real eigenvalues."
        },
        {
            "id": "LA02",
            "misconception": "If AB = 0 then A = 0 or B = 0",
            "danger": "CRITICAL",
            "question": "Give an example of two non-zero matrices A and B where AB = 0.",
            "correct": "A = [[1,0],[0,0]] and B = [[0,0],[0,1]] gives AB = 0 with neither being zero. The cancellation law does NOT apply to matrices.",
            "why_students_believe_it": "Direct analogy from real numbers where ab=0 implies a=0 or b=0."
        },
        {
            "id": "LA03",
            "misconception": "Rank of a matrix equals the number of non-zero rows",
            "danger": "HIGH",
            "question": "What is the rank of [[1,2,3],[2,4,6],[0,0,0]]?",
            "correct": "Rank = 1, not 2. Row 2 is twice row 1. Rank is non-zero rows in ROW ECHELON FORM.",
            "why_students_believe_it": "Students confuse non-zero rows in original matrix with non-zero rows after row reduction."
        },
        {
            "id": "LA04",
            "misconception": "A matrix with all non-zero entries is always invertible",
            "danger": "HIGH",
            "question": "Is [[1,2],[2,4]] invertible? All its entries are non-zero.",
            "correct": "No — det = 4-4 = 0, so it is singular. Invertible iff determinant is non-zero.",
            "why_students_believe_it": "Students confuse 'non-zero matrix' with 'invertible matrix'."
        },
        {
            "id": "LA05",
            "misconception": "Cayley-Hamilton means a matrix satisfies its characteristic equation as a number would",
            "danger": "MEDIUM",
            "question": "If characteristic equation is lambda^2-3*lambda+2=0, write the matrix equation.",
            "correct": "A^2-3A+2I=0 where I is identity. Students often write A^2-3A+2=0 without the identity matrix.",
            "why_students_believe_it": "Students substitute A into scalar equation without converting scalar terms to matrix form."
        }
    ],
    "ode_first": [
        {
            "id": "OF01",
            "misconception": "Every first order ODE can be solved by separating variables",
            "danger": "HIGH",
            "question": "Identify which method applies: dy/dx = (x+y)/(x-y). Can you separate variables here?",
            "correct": "No — this is a homogeneous equation, solved by substitution y=vx. Always identify the type first.",
            "why_students_believe_it": "Variables separable is taught first and students default to it."
        },
        {
            "id": "OF02",
            "misconception": "The integrating factor for a linear ODE is always e^(integral P dx)",
            "danger": "MEDIUM",
            "question": "The standard form is dy/dx + P(x)y = Q(x). What if the equation is dx/dy + P(y)x = Q(y)?",
            "correct": "When x is dependent (dx/dy form), the integrating factor is e^(integral P(y)dy). Students must identify which variable is dependent.",
            "why_students_believe_it": "Students memorise the dy/dx form and apply it blindly."
        },
        {
            "id": "OF03",
            "misconception": "An exact equation M dx + N dy = 0 has solution F where dF/dx = N",
            "danger": "CRITICAL",
            "question": "For exact equation M dx + N dy = 0, is dF/dx = M or dF/dx = N?",
            "correct": "dF/dx = M and dF/dy = N. Many students swap M and N.",
            "why_students_believe_it": "Confusion between the test condition and the integration conditions."
        }
    ],
    "ode_higher": [
        {
            "id": "OH01",
            "misconception": "PI for e^(ax) fails only when a is a root of the auxiliary equation",
            "danger": "HIGH",
            "question": "Find PI for y'' - 2y' + y = e^x. Is D=1 a simple or repeated root?",
            "correct": "D=1 is a repeated root (multiplicity 2). For repeated root of multiplicity r, PI = x^r*e^(ax)/f^(r)(a).",
            "why_students_believe_it": "Textbooks often show simple failure case without emphasising repeated root case."
        },
        {
            "id": "OH02",
            "misconception": "The general solution is just the particular integral",
            "danger": "CRITICAL",
            "question": "You found PI = x^2*e^x for y'' - 2y' + y = 2e^x. Is this the complete solution?",
            "correct": "No — complete solution is y = CF + PI = (c1 + c2*x)e^x + x^2*e^x.",
            "why_students_believe_it": "Students focus on PI and forget to add CF."
        },
        {
            "id": "OH03",
            "misconception": "Wronskian being zero at one point means functions are linearly dependent",
            "danger": "HIGH",
            "question": "If W(f,g)(x0) = 0 at a single point, are f and g linearly dependent?",
            "correct": "For solutions of a linear ODE, Wronskian is either identically zero or never zero (Abel's theorem).",
            "why_students_believe_it": "Students check Wronskian at one convenient point rather than understanding its behaviour."
        }
    ],
    "laplace": [
        {
            "id": "LT01",
            "misconception": "Laplace transform of a product is the product of Laplace transforms",
            "danger": "CRITICAL",
            "question": "Is L{t*sin(t)} = L{t} * L{sin(t)}?",
            "correct": "No — L{f*g} != L{f}*L{g}. Use L{t^n*f(t)} = (-1)^n d^n/ds^n [F(s)]. Product of transforms gives convolution.",
            "why_students_believe_it": "Analogy with linearity L{f+g} = L{f}+L{g}."
        },
        {
            "id": "LT02",
            "misconception": "Initial conditions are applied after finding the general solution",
            "danger": "HIGH",
            "question": "When solving an IVP using Laplace, when do initial conditions appear?",
            "correct": "Initial conditions appear DURING transformation: L{y''} = s^2*Y(s) - s*y(0) - y'(0).",
            "why_students_believe_it": "Classical method habit: solve first, apply ICs last."
        },
        {
            "id": "LT03",
            "misconception": "Inverse Laplace of F(s)*G(s) is f(t)*g(t)",
            "danger": "CRITICAL",
            "question": "Find L^(-1){1/(s(s+1))} — is it 1*e^(-t)?",
            "correct": "No — use partial fractions: 1/(s(s+1)) = 1/s - 1/(s+1), giving L^(-1) = 1 - e^(-t).",
            "why_students_believe_it": "Students reverse the wrong rule."
        }
    ],
    "vector_calc": [
        {
            "id": "VC01",
            "misconception": "div(curl F) = curl(div F)",
            "danger": "HIGH",
            "question": "What is div(curl F)? What is curl(div F)?",
            "correct": "div(curl F) = 0 always (identity). curl(div F) is meaningless — div F is scalar, curl needs vector.",
            "why_students_believe_it": "Students treat div and curl as interchangeable operators."
        },
        {
            "id": "VC02",
            "misconception": "A vector field with zero curl is always conservative",
            "danger": "HIGH",
                        "question": "If curl F = 0 everywhere, is F necessarily conservative?",
            "correct": "Only if the domain is simply connected.",
            "why_students_believe_it": "The theorem is taught without the simply-connected condition."
        },
        {
            "id": "VC03",
            "misconception": "Green's, Stokes' and Gauss's theorems are three separate unrelated results",
            "danger": "MEDIUM",
            "question": "How are these three theorems related?",
            "correct": "All three are special cases of the Generalised Stokes' theorem.",
            "why_students_believe_it": "They are taught as three separate named theorems."
        }
    ],
    "complex_analysis": [
        {
            "id": "CA01",
            "misconception": "An analytic function is just a function you can write a formula for",
            "danger": "HIGH",
            "question": "Is f(z) = z-bar (complex conjugate) analytic?",
            "correct": "No — f(z) = z-bar fails Cauchy-Riemann equations. Analytic means complex-differentiable.",
            "why_students_believe_it": "Analogy with real analysis where differentiable means has a formula."
        },
        {
            "id": "CA02",
            "misconception": "Cauchy's theorem means every complex integral around a closed curve is zero",
            "danger": "CRITICAL",
            "question": "Is contour integral of dz/z = 0 for C being the unit circle?",
            "correct": "No — contour integral of dz/z = 2*pi*i. f(z)=1/z has singularity at z=0 inside the contour.",
            "why_students_believe_it": "Students apply Cauchy's theorem without checking for singularities."
        },
        {
            "id": "CA03",
            "misconception": "The residue at a pole is always numerator/derivative of denominator",
            "danger": "HIGH",
            "question": "Find residue of 1/(z^2*(z-1)) at z=0.",
            "correct": "z=0 is pole of order 2. Simple pole formula only works for simple poles.",
            "why_students_believe_it": "Simple pole formula is taught first and most prominently."
        }
    ],
    "fourier_series": [
        {
            "id": "FS01",
            "misconception": "Fourier series always converges to f(x) at every point",
            "danger": "HIGH",
            "question": "At a discontinuity x0, what does the Fourier series converge to?",
            "correct": "At discontinuity, converges to AVERAGE of left and right limits: [f(x0+) + f(x0-)]/2.",
            "why_students_believe_it": "The series is called 'of f(x)' suggesting it equals f(x) everywhere."
        },
        {
            "id": "FS02",
            "misconception": "Any function can be represented by a Fourier series",
            "danger": "MEDIUM",
            "question": "What conditions must f(x) satisfy?",
            "correct": "Dirichlet conditions: periodic, bounded, finite number of maxima/minima/discontinuities.",
            "why_students_believe_it": "Textbooks jump straight to computing without emphasising conditions."
        },
        {
            "id": "FS03",
            "misconception": "For an odd function, a0 = 0 because the average is zero",
            "danger": "MEDIUM",
            "question": "Why is a0 = 0 for an odd function?",
            "correct": "For odd function f(-x)=-f(x), integral over symmetric interval is zero. ALL an = 0.",
            "why_students_believe_it": "Students memorise the result but cannot explain the reasoning."
        }
    ],
    "probability": [
        {
            "id": "PR01",
            "misconception": "P(A intersect B) = P(A)*P(B) always",
            "danger": "CRITICAL",
            "question": "A card is drawn. A='red', B='king'. Are they independent?",
            "correct": "P(A intersect B) = P(A)*P(B) is the DEFINITION of independence. For dependent events use P(A intersect B) = P(A)*P(B|A).",
            "why_students_believe_it": "Students see multiplication rule in independent examples and generalise."
        },
        {
            "id": "PR02",
            "misconception": "The mean of a normal distribution is always 0",
            "danger": "HIGH",
            "question": "If X ~ N(mu, sigma^2), when is the mean zero?",
            "correct": "Mean = mu. Zero only for STANDARD normal N(0,1). Always convert using Z = (X-mu)/sigma.",
            "why_students_believe_it": "Z-tables use standard normal and students confuse standard with general."
        },
        {
            "id": "PR03",
            "misconception": "Variance can be negative",
            "danger": "HIGH",
            "question": "Can Var(X) ever be negative?",
            "correct": "Variance is ALWAYS >= 0. Var(X) = E[(X-mu)^2] >= 0 because it is expectation of squared quantity.",
            "why_students_believe_it": "Students confuse variance with deviations (X-mu) which can be negative."
        }
    ],
    "numerical": [
        {
            "id": "NM01",
            "misconception": "Newton-Raphson always converges",
            "danger": "HIGH",
            "question": "Can Newton-Raphson fail to converge?",
            "correct": "Yes — fails if f'(xn)=0, initial guess too far, or multiple roots nearby.",
            "why_students_believe_it": "Textbook examples are chosen to always converge."
        },
        {
            "id": "NM02",
            "misconception": "Simpson's 1/3 rule works for any number of subintervals",
            "danger": "CRITICAL",
            "question": "Apply Simpson's 1/3 with 5 subintervals. Can you?",
            "correct": "No — requires EVEN number of subintervals.",
            "why_students_believe_it": "Students memorise formula without remembering constraint."
        },
        {
            "id": "NM03",
            "misconception": "More iterations always means more accuracy in Newton-Raphson",
            "danger": "MEDIUM",
            "question": "After converging to 1.4142135, should you do more iterations?",
            "correct": "Stop when |x(n+1) - x(n)| < epsilon. More iterations past convergence just repeat digits.",
            "why_students_believe_it": "Students think more = better without understanding convergence."
        }
    ],
    "transforms": [
        {
            "id": "TR01",
            "misconception": "Z-transform and Laplace transform are the same thing",
            "danger": "HIGH",
            "question": "What is the fundamental difference?",
            "correct": "Laplace is continuous-time. Z-transform is discrete-time. Connected by z = e^(sT).",
            "why_students_believe_it": "Both convert time-domain to algebraic."
        },
        {
            "id": "TR02",
            "misconception": "ROC is always the entire z-plane",
            "danger": "HIGH",
            "question": "What is the ROC of z/(z-0.5) for causal sequence?",
            "correct": "ROC = {|z| > 0.5}. ROC MUST be stated with every Z-transform.",
            "why_students_believe_it": "Students treat ROC as afterthought."
        }
    ]
}


# ══════════════════════════════════════════════════════════════
#  MISCONCEPTION DETECTOR PROMPT
# ══════════════════════════════════════════════════════════════
def build_misconception_prompt(topic_key, student_answer, question_id):
    """Build misconception diagnosis prompt — works for both university and GATE misconceptions"""
    # Search in university misconceptions
    topic_misconceptions = MISCONCEPTIONS.get(topic_key, [])
    question_data = None
    for m in topic_misconceptions:
        if m["id"] == question_id:
            question_data = m
            break

    # Search in GATE misconceptions if not found
    if not question_data:
        gate_misconceptions = GATE_MISCONCEPTIONS.get(topic_key, [])
        for m in gate_misconceptions:
            if m["id"] == question_id:
                question_data = m
                break

    if not question_data:
        return None

    # Determine if this is a GATE-level misconception
    is_gate = question_id.startswith("G_")
    context = GATE_CONTEXT if is_gate else ENG_CONTEXT
    format_rules = GATE_FORMAT if is_gate else ENG_FORMAT

    truth_or_correct = question_data.get("truth", question_data.get("correct", ""))

    return context + "\n" + format_rules + f"""
You are MathSphere's Misconception Detector — a specialist in mathematics education.

MISCONCEPTION BEING PROBED: {question_data['misconception']}
DANGER LEVEL: {question_data.get('danger', 'HIGH')}

DIAGNOSTIC QUESTION ASKED:
{question_data.get('question', question_data.get('trap_question', ''))}

STUDENT'S ANSWER:
{student_answer}

CORRECT UNDERSTANDING:
{truth_or_correct}

WHY STUDENTS HOLD THIS MISCONCEPTION:
{question_data.get('why_students_believe_it', question_data.get('gate_relevance', ''))}

DIAGNOSIS:
[Does the student's answer reveal the misconception, partial misconception, or correct understanding?]
[Be specific — quote the exact part of their answer that reveals their thinking]

WHAT THIS TELLS US:
[What mental model the student has — where exactly their understanding breaks down]

THE CORRECT UNDERSTANDING:
[Explain correctly and gently — build from what they DO understand]
[Every equation on its own line as


$$
...
$$


]

THE COUNTEREXAMPLE THAT BREAKS THE MISCONCEPTION:
[One specific numerical counterexample that the student can verify themselves]

HOW THIS AFFECTS EXAM PERFORMANCE:
[Which exam questions this causes errors in — be specific about question types]

HOW TO FIX THIS PERMANENTLY:
[One mental reframe or visual image that prevents this error from recurring]
[The goal: they should never make this mistake again after reading this]

FOLLOW-UP QUESTION:
[One question that tests whether the student has truly fixed the misconception]


$$
[follow-up question]
$$



EXPECTED ANSWER:


$$
[correct answer to follow-up]
$$



CONFIDENCE IN DIAGNOSIS: HIGH / MEDIUM / LOW
[If MEDIUM or LOW, explain what additional information would help]

Tone: Warm, non-judgmental, encouraging. Never make the student feel stupid.
"""


# ══════════════════════════════════════════════════════════════
#  TOPIC ROADMAP BUILDER (no AI call)
# ══════════════════════════════════════════════════════════════
def build_roadmap(topic_key):
    for sem_key, sem_data in SYLLABUS.items():
        if topic_key in sem_data["topics"]:
            topic_data = sem_data["topics"][topic_key]
            subtopics = topic_data["subtopics"]
            total = len(subtopics)

            phases = []
            chunk_size = max(1, total // 4)
            phase_names = ["Foundation", "Core Concepts", "Advanced Methods", "Exam Mastery"]
            phase_descriptions = [
                "Build the basics — definitions, notation, simple examples",
                "Master the main theorems and standard problems",
                "Tackle harder problems, proofs, and special cases",
                "Practice exam-style problems and revision"
            ]

            for i, (name, desc) in enumerate(zip(phase_names, phase_descriptions)):
                start = i * chunk_size
                end = start + chunk_size if i < 3 else total
                phase_subtopics = subtopics[start:end] if start < total else []
                phases.append({
                    "phase":           i + 1,
                    "name":            name,
                    "description":     desc,
                    "subtopics":       phase_subtopics,
                    "estimated_hours": max(1, len(phase_subtopics) * 2)
                })

            # Fuzzy prerequisite matching
            topic_prereqs = {}
            for st in subtopics:
                st_lower = st.lower()
                for key, val in PREREQUISITES.items():
                    key_lower = key.lower()
                    if key_lower in st_lower or st_lower in key_lower:
                        topic_prereqs[key] = val
                    else:
                        key_words = set(key_lower.split())
                        st_words = set(st_lower.split())
                        if len(key_words & st_words) >= 2:
                            topic_prereqs[key] = val

            return {
                "topic":           topic_data["label"],
                "total_subtopics": total,
                "estimated_hours": total * 2,
                "phases":          phases,
                "prerequisites":   topic_prereqs,
                "references":      REFERENCES.get(topic_key, []),
                "difficulty":      TOPIC_DIFFICULTY.get(topic_key, {}),
                "gate_relevance":  GATE_TOPIC_ANALYSIS.get(topic_key, {})
            }
    return None


# ══════════════════════════════════════════════════════════════
#  STUDENT PROGRESS TRACKER — FIXED (RLock, no deadlock)
# ══════════════════════════════════════════════════════════════
_student_progress = {}
_progress_lock    = threading.RLock()  # FIXED: RLock instead of Lock
PROGRESS_MAX_STUDENTS = 500
PROGRESS_MAX_LIST     = 200

def _get_progress_unlocked(student_id):
    """Internal — caller MUST hold _progress_lock"""
    if student_id not in _student_progress and len(_student_progress) >= PROGRESS_MAX_STUDENTS:
        oldest = min(
            _student_progress,
            key=lambda k: _student_progress[k].get("last_active") or "0000-00-00"
        )
        logger.info("Evicting inactive student: %s", oldest)
        del _student_progress[oldest]

    if student_id not in _student_progress:
        _student_progress[student_id] = {
            "completed_subtopics":  [],
            "weak_areas":           [],
            "strong_areas":         [],
            "misconceptions_found": [],
            "mock_tests_taken":     0,
            "mock_test_scores":     [],
            "total_study_time":     0,
            "last_active":          time.strftime("%Y-%m-%d %H:%M:%S"),
            "created_at":           time.strftime("%Y-%m-%d %H:%M:%S"),
            "gate_progress": {
                "questions_attempted": 0,
                "questions_correct":   0,
                "topic_scores":        {},
                "mock_tests":          [],
                "weak_gate_topics":    [],
                "strong_gate_topics":  []
            }
        }
    return _student_progress[student_id]

def get_progress(student_id):
    with _progress_lock:
        return _get_progress_unlocked(student_id)

def update_progress(student_id, action, data):
    with _progress_lock:
        progress = _get_progress_unlocked(student_id)
        progress["last_active"] = time.strftime("%Y-%m-%d %H:%M:%S")

        if action == "complete_subtopic":
            subtopic = data.get("subtopic", "")
            if subtopic and subtopic not in progress["completed_subtopics"]:
                if len(progress["completed_subtopics"]) < PROGRESS_MAX_LIST:
                    progress["completed_subtopics"].append(subtopic)

        elif action == "mark_weak":
            subtopic = data.get("subtopic", "")
            if subtopic and subtopic not in progress["weak_areas"]:
                if len(progress["weak_areas"]) < PROGRESS_MAX_LIST:
                    progress["weak_areas"].append(subtopic)
            if subtopic in progress["strong_areas"]:
                progress["strong_areas"].remove(subtopic)

        elif action == "mark_strong":
            subtopic = data.get("subtopic", "")
            if subtopic and subtopic not in progress["strong_areas"]:
                if len(progress["strong_areas"]) < PROGRESS_MAX_LIST:
                    progress["strong_areas"].append(subtopic)
            if subtopic in progress["weak_areas"]:
                progress["weak_areas"].remove(subtopic)

        elif action == "misconception_found":
            misconception_id = data.get("misconception_id", "")
            if misconception_id and misconception_id not in progress["misconceptions_found"]:
                if len(progress["misconceptions_found"]) < PROGRESS_MAX_LIST:
                    progress["misconceptions_found"].append(misconception_id)

        elif action == "mock_test":
            progress["mock_tests_taken"] += 1
            score = data.get("score")
            if score is not None:
                if len(progress["mock_test_scores"]) < PROGRESS_MAX_LIST:
                    progress["mock_test_scores"].append({
                        "score": score,
                        "total": data.get("total", 0),
                        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "type": data.get("type", "university")
                    })

        elif action == "study_time":
            minutes = validate_positive_int(data.get("minutes", 0), "minutes", min_val=0, max_val=1440, default=0)
            progress["total_study_time"] += minutes

        elif action == "gate_question":
            gp = progress["gate_progress"]
            gp["questions_attempted"] += 1
            if data.get("correct", False):
                gp["questions_correct"] += 1
            topic = data.get("topic", "")
            if topic:
                if topic not in gp["topic_scores"]:
                    gp["topic_scores"][topic] = {"attempted": 0, "correct": 0}
                gp["topic_scores"][topic]["attempted"] += 1
                if data.get("correct", False):
                    gp["topic_scores"][topic]["correct"] += 1

        elif action == "gate_mock":
            gp = progress["gate_progress"]
            if len(gp["mock_tests"]) < PROGRESS_MAX_LIST:
                gp["mock_tests"].append({
                    "score": data.get("score", 0),
                    "total": data.get("total", 0),
                    "branch": data.get("branch", ""),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S")
                })

        elif action == "gate_mark_weak":
            topic = data.get("topic", "")
            gp = progress["gate_progress"]
            if topic and topic not in gp["weak_gate_topics"]:
                if len(gp["weak_gate_topics"]) < PROGRESS_MAX_LIST:
                    gp["weak_gate_topics"].append(topic)
            if topic in gp["strong_gate_topics"]:
                gp["strong_gate_topics"].remove(topic)

        elif action == "gate_mark_strong":
            topic = data.get("topic", "")
            gp = progress["gate_progress"]
            if topic and topic not in gp["strong_gate_topics"]:
                if len(gp["strong_gate_topics"]) < PROGRESS_MAX_LIST:
                    gp["strong_gate_topics"].append(topic)
            if topic in gp["weak_gate_topics"]:
                gp["weak_gate_topics"].remove(topic)

        return progress


# ══════════════════════════════════════════════════════════════
#  METHOD SELECTOR (no AI call) — FIXED ordering
# ══════════════════════════════════════════════════════════════
METHOD_SELECTOR = {
    "ode_first_order": {
        "label": "First Order ODE Method Selector",
        "decision_tree": [
            {"check": "Can you write it as f(x)dx = g(y)dy?", "yes": "Variables Separable Method", "no": "Continue below"},
            {"check": "Is it of the form dy/dx = f(y/x)?", "yes": "Homogeneous ODE — substitute y = vx", "no": "Continue below"},
            {"check": "Is it of the form dy/dx + P(x)y = Q(x)?", "yes": "Linear ODE — IF = e^(integral P dx)", "no": "Continue below"},
            {"check": "Is it of the form dy/dx + P(x)y = Q(x)y^n?", "yes": "Bernoulli — substitute v = y^(1-n)", "no": "Continue below"},
            {"check": "Is M dx + N dy = 0 with dM/dy = dN/dx?", "yes": "Exact Equation", "no": "Continue below"},
            {"check": "Is (dM/dy - dN/dx)/N a function of x only?", "yes": "Integrating Factor mu(x)", "no": "Continue below"},
            {"check": "Is (dN/dx - dM/dy)/M a function of y only?", "yes": "Integrating Factor mu(y)", "no": "Continue below"},
            {"check": "Is it y = px + f(p) where p = dy/dx?", "yes": "Clairaut's Equation", "no": "Try substitution or numerical method"}
        ]
    },
    "convergence_tests": {
        "label": "Series Convergence Test Selector",
        "decision_tree": [
            {"check": "Does an -> 0 as n -> infinity?", "yes": "Continue testing (necessary but not sufficient)", "no": "DIVERGES by Divergence Test"},
            {"check": "Is it a geometric series sum(ar^n)?", "yes": "Converges if |r| < 1, diverges if |r| >= 1", "no": "Continue below"},
            {"check": "Is it a p-series sum(1/n^p)?", "yes": "Converges if p > 1, diverges if p <= 1", "no": "Continue below"},
            {"check": "Can you compute lim |a(n+1)/a(n)|?", "yes": "Ratio Test: L<1 converges, L>1 diverges, L=1 inconclusive", "no": "Continue below"},
            {"check": "Can you compute lim |an|^(1/n)?", "yes": "Root Test: L<1 converges, L>1 diverges, L=1 inconclusive", "no": "Continue below"},
            {"check": "Is an >= bn >= 0 with sum(bn) known?", "yes": "Comparison Test", "no": "Continue below"},
            {"check": "Is it alternating: sum((-1)^n bn) with bn decreasing to 0?", "yes": "Alternating Series Test — converges", "no": "Continue below"},
            {"check": "Can you integrate f(x) where f(n) = an?", "yes": "Integral Test", "no": "Try Limit Comparison Test"}
        ]
    },
    "integration_methods": {
        "label": "Integration Method Selector",
        "decision_tree": [
            {"check": "Is it a standard form from formula tables?", "yes": "Direct formula application", "no": "Continue below"},
            {"check": "Is it integral f(g(x))g'(x)dx?", "yes": "Substitution: let u = g(x)", "no": "Continue below"},
            {"check": "Is it integral u*dv form (product of two functions)?", "yes": "Integration by Parts: integral u dv = uv - integral v du", "no": "Continue below"},
            {"check": "Is it a rational function P(x)/Q(x)?", "yes": "Partial Fractions (if degree P < degree Q)", "no": "Continue below"},
            {"check": "Does it contain sqrt(a^2-x^2), sqrt(a^2+x^2), or sqrt(x^2-a^2)?", "yes": "Trigonometric Substitution", "no": "Continue below"},
            {"check": "Is it sin^m(x)*cos^n(x)?", "yes": "Reduction Formula or Wallis Formula", "no": "Continue below"},
            {"check": "Is it an improper integral?", "yes": "Check convergence first, then evaluate limit", "no": "Try combination of methods"}
        ]
    },
    "laplace_inverse": {
        "label": "Inverse Laplace Transform Method Selector",
        "decision_tree": [
            {"check": "Is F(s) in the standard table?", "yes": "Direct lookup", "no": "Continue below"},
            {"check": "Is F(s) a rational function?", "yes": "Partial Fractions then lookup each term", "no": "Continue below"},
            {"check": "Does F(s) have the form F(s-a)?", "yes": "First Shifting: e^(at)*L^(-1){F(s)}", "no": "Continue below"},
            {"check": "Does F(s) contain e^(-as)?", "yes": "Second Shifting: u(t-a)*f(t-a)", "no": "Continue below"},
            {"check": "Is F(s) = F1(s)*F2(s)?", "yes": "Convolution: f1(t) * f2(t)", "no": "Try series expansion or contour integration"}
        ]
    },
    "numerical_integration": {
        "label": "Numerical Integration Method Selector",
        "decision_tree": [
            # FIXED: Most specific first, then least specific
            {"check": "Is n (subintervals) divisible by 6?", "yes": "Weddle's Rule (most accurate)", "no": "Continue below"},
            {"check": "Is n divisible by 3 (but not 6)?", "yes": "Simpson's 3/8 Rule", "no": "Continue below"},
            {"check": "Is n even (but not divisible by 6)?", "yes": "Simpson's 1/3 Rule (most common)", "no": "Continue below"},
            {"check": "Is n odd and not divisible by 3?", "yes": "Trapezoidal Rule (works for any n)", "no": "Trapezoidal Rule"},
        ]
    },
    "gate_method_selector": {
        "label": "GATE Mathematics — Which Topic First?",
        "decision_tree": [
            {"check": "Is the question about eigenvalues, rank, or determinant?", "yes": "Linear Algebra — use trace/det shortcuts", "no": "Continue below"},
            {"check": "Is the question about maxima/minima, limits, or continuity?", "yes": "Calculus — check conditions carefully", "no": "Continue below"},
            {"check": "Is the question about probability, distribution, or Bayes?", "yes": "Probability — convert to standard form", "no": "Continue below"},
            {"check": "Is the question about solving a differential equation?", "yes": "ODE — identify type first, then method", "no": "Continue below"},
            {"check": "Is the question about residues, analyticity, or contour integral?", "yes": "Complex Analysis — check CR equations or use residue theorem", "no": "Continue below"},
            {"check": "Is the question about numerical computation (iteration, integration)?", "yes": "Numerical Methods — apply formula directly", "no": "Continue below"},
            {"check": "Is the question about Laplace/Z/Fourier transforms?", "yes": "Transforms — use table lookup first", "no": "Read question again — classify before solving"}
        ]
    }
}

# ══════════════════════════════════════════════════════════════
#  QUICK FORMULAS (no AI call)
# ══════════════════════════════════════════════════════════════
QUICK_FORMULAS = {
    "derivatives": {
        "label": "Standard Derivatives",
        "formulas": [
            {"name": "Power Rule", "formula": "d/dx(x^n) = nx^(n-1)", "condition": "n is any real number"},
            {"name": "Exponential", "formula": "d/dx(e^x) = e^x", "condition": "Always valid"},
            {"name": "General Exponential", "formula": "d/dx(a^x) = a^x ln(a)", "condition": "a > 0, a != 1"},
            {"name": "Natural Log", "formula": "d/dx(ln x) = 1/x", "condition": "x > 0"},
            {"name": "Sine", "formula": "d/dx(sin x) = cos x", "condition": "x in radians"},
            {"name": "Cosine", "formula": "d/dx(cos x) = -sin x", "condition": "x in radians"},
            {"name": "Tangent", "formula": "d/dx(tan x) = sec^2(x)", "condition": "x != (2n+1)pi/2"},
            {"name": "Inverse Sine", "formula": "d/dx(sin^(-1) x) = 1/sqrt(1-x^2)", "condition": "|x| < 1"},
            {"name": "Inverse Tangent", "formula": "d/dx(tan^(-1) x) = 1/(1+x^2)", "condition": "All x"},
            {"name": "Product Rule", "formula": "d/dx(uv) = u(dv/dx) + v(du/dx)", "condition": "u, v differentiable"},
            {"name": "Quotient Rule", "formula": "d/dx(u/v) = [v(du/dx) - u(dv/dx)]/v^2", "condition": "v != 0"},
            {"name": "Chain Rule", "formula": "d/dx(f(g(x))) = f'(g(x))*g'(x)", "condition": "Both differentiable"},
        ]
    },
    "integrals": {
        "label": "Standard Integrals",
        "formulas": [
            {"name": "Power Rule", "formula": "integral x^n dx = x^(n+1)/(n+1) + C", "condition": "n != -1"},
            {"name": "Reciprocal", "formula": "integral (1/x) dx = ln|x| + C", "condition": "x != 0"},
            {"name": "Exponential", "formula": "integral e^x dx = e^x + C", "condition": "Always valid"},
            {"name": "Sine", "formula": "integral sin x dx = -cos x + C", "condition": "x in radians"},
            {"name": "Cosine", "formula": "integral cos x dx = sin x + C", "condition": "x in radians"},
            {"name": "Secant Squared", "formula": "integral sec^2(x) dx = tan x + C", "condition": "x != (2n+1)pi/2"},
            {"name": "Form 1/(a^2+x^2)", "formula": "integral dx/(a^2+x^2) = (1/a)tan^(-1)(x/a) + C", "condition": "a != 0"},
            {"name": "Form 1/sqrt(a^2-x^2)", "formula": "integral dx/sqrt(a^2-x^2) = sin^(-1)(x/a) + C", "condition": "|x| < a"},
            {"name": "Form 1/(x^2-a^2)", "formula": "integral dx/(x^2-a^2) = (1/2a)ln|(x-a)/(x+a)| + C", "condition": "x != +/-a"},
            {"name": "Secant", "formula": "integral sec x dx = ln|sec x + tan x| + C", "condition": "x != (2n+1)pi/2"},
            {"name": "e^(ax)sin(bx)", "formula": "integral e^(ax)sin(bx) dx = e^(ax)[a*sin(bx) - b*cos(bx)]/(a^2+b^2) + C", "condition": "a^2+b^2 != 0"},
        ]
    },
    "laplace_transforms": {
        "label": "Standard Laplace Transforms",
        "formulas": [
            {"name": "Constant", "formula": "L{1} = 1/s", "condition": "s > 0"},
            {"name": "Power", "formula": "L{t^n} = n!/s^(n+1)", "condition": "s > 0, n = 0,1,2,..."},
            {"name": "Exponential", "formula": "L{e^(at)} = 1/(s-a)", "condition": "s > a"},
            {"name": "Sine", "formula": "L{sin(at)} = a/(s^2+a^2)", "condition": "s > 0"},
            {"name": "Cosine", "formula": "L{cos(at)} = s/(s^2+a^2)", "condition": "s > 0"},
            {"name": "t*sin(at)", "formula": "L{t*sin(at)} = 2as/(s^2+a^2)^2", "condition": "s > 0"},
            {"name": "t*cos(at)", "formula": "L{t*cos(at)} = (s^2-a^2)/(s^2+a^2)^2", "condition": "s > 0"},
            {"name": "e^(at)*sin(bt)", "formula": "L{e^(at)*sin(bt)} = b/((s-a)^2+b^2)", "condition": "s > a"},
            {"name": "e^(at)*cos(bt)", "formula": "L{e^(at)*cos(bt)} = (s-a)/((s-a)^2+b^2)", "condition": "s > a"},
            {"name": "Unit Step", "formula": "L{u(t-a)} = e^(-as)/s", "condition": "s > 0, a >= 0"},
            {"name": "Dirac Delta", "formula": "L{delta(t-a)} = e^(-as)", "condition": "a >= 0"},
            {"name": "First Shifting", "formula": "L{e^(at)f(t)} = F(s-a)", "condition": "s > a"},
            {"name": "Second Shifting", "formula": "L{f(t-a)u(t-a)} = e^(-as)F(s)", "condition": "a >= 0"},
            {"name": "Derivative", "formula": "L{f'(t)} = sF(s) - f(0)", "condition": "f continuous"},
            {"name": "Second Derivative", "formula": "L{f''(t)} = s^2 F(s) - sf(0) - f'(0)", "condition": "f' continuous"},
            {"name": "Multiplication by t", "formula": "L{tf(t)} = -d/ds[F(s)]", "condition": "F differentiable"},
            {"name": "Division by t", "formula": "L{f(t)/t} = integral_s^inf F(u) du", "condition": "Integral exists"},
            {"name": "Convolution", "formula": "L{f*g} = F(s)*G(s)", "condition": "Both transforms exist"},
        ]
    },
    "z_transforms": {
        "label": "Standard Z-Transforms",
        "formulas": [
            {"name": "Unit Step", "formula": "Z{u[n]} = z/(z-1)", "condition": "|z| > 1"},
            {"name": "Unit Ramp", "formula": "Z{n*u[n]} = z/(z-1)^2", "condition": "|z| > 1"},
            {"name": "Exponential", "formula": "Z{a^n u[n]} = z/(z-a)", "condition": "|z| > |a|"},
            {"name": "n*a^n", "formula": "Z{n*a^n u[n]} = az/(z-a)^2", "condition": "|z| > |a|"},
            {"name": "Cosine", "formula": "Z{cos(nw)u[n]} = z(z-cos w)/(z^2-2z*cos w+1)", "condition": "|z| > 1"},
            {"name": "Sine", "formula": "Z{sin(nw)u[n]} = z*sin w/(z^2-2z*cos w+1)", "condition": "|z| > 1"},
        ]
    },
    "fourier_series_formulas": {
        "label": "Fourier Series Formulas",
        "formulas": [
            {"name": "Fourier Coefficients a0", "formula": "a0 = (1/L) integral(-L to L) f(x) dx", "condition": "f satisfies Dirichlet conditions"},
            {"name": "Fourier Coefficients an", "formula": "an = (1/L) integral(-L to L) f(x)cos(n*pi*x/L) dx", "condition": "n = 1,2,3,..."},
            {"name": "Fourier Coefficients bn", "formula": "bn = (1/L) integral(-L to L) f(x)sin(n*pi*x/L) dx", "condition": "n = 1,2,3,..."},
            {"name": "Fourier Series", "formula": "f(x) = a0/2 + sum[an*cos(n*pi*x/L) + bn*sin(n*pi*x/L)]", "condition": "Period = 2L"},
            {"name": "Parseval's Identity", "formula": "(1/L) integral(-L to L) [f(x)]^2 dx = a0^2/2 + sum(an^2 + bn^2)", "condition": "f^2 integrable"},
            {"name": "Even Function", "formula": "bn = 0, an = (2/L) integral(0 to L) f(x)cos(n*pi*x/L) dx", "condition": "f(-x) = f(x)"},
            {"name": "Odd Function", "formula": "a0 = an = 0, bn = (2/L) integral(0 to L) f(x)sin(n*pi*x/L) dx", "condition": "f(-x) = -f(x)"},
        ]
    },
    "vector_identities": {
        "label": "Vector Calculus Identities",
        "formulas": [
            {"name": "Gradient", "formula": "grad f = (df/dx)i + (df/dy)j + (df/dz)k", "condition": "f is scalar field"},
            {"name": "Divergence", "formula": "div F = dF1/dx + dF2/dy + dF3/dz", "condition": "F is vector field"},
            {"name": "Curl", "formula": "curl F = |i j k; d/dx d/dy d/dz; F1 F2 F3|", "condition": "F is vector field"},
            {"name": "Laplacian", "formula": "laplacian f = d^2f/dx^2 + d^2f/dy^2 + d^2f/dz^2", "condition": "f twice differentiable"},
            {"name": "curl(grad f)", "formula": "curl(grad f) = 0", "condition": "Always (identity)"},
            {"name": "div(curl F)", "formula": "div(curl F) = 0", "condition": "Always (identity)"},
            {"name": "Green's Theorem", "formula": "contour_integral(M dx + N dy) = double_integral(dN/dx - dM/dy) dA", "condition": "Simply connected, C positive orientation"},
            {"name": "Stokes' Theorem", "formula": "double_integral(curl F)*dS = contour_integral F*dr", "condition": "Oriented surface with boundary"},
            {"name": "Gauss Divergence", "formula": "triple_integral(div F) dV = surface_integral F*dS", "condition": "Closed surface, outward normal"},
        ]
    },
    "probability_distributions": {
        "label": "Probability Distribution Formulas",
        "formulas": [
            {"name": "Binomial PMF", "formula": "P(X=r) = nCr * p^r * q^(n-r)", "condition": "n trials, p = success prob, q = 1-p"},
            {"name": "Binomial Mean/Var", "formula": "E(X) = np, Var(X) = npq", "condition": "X ~ Bin(n,p)"},
            {"name": "Poisson PMF", "formula": "P(X=r) = e^(-lambda) * lambda^r / r!", "condition": "lambda = mean rate"},
            {"name": "Poisson Mean/Var", "formula": "E(X) = Var(X) = lambda", "condition": "X ~ Poi(lambda)"},
            {"name": "Normal PDF", "formula": "f(x) = (1/(sigma*sqrt(2*pi))) * e^(-(x-mu)^2/(2*sigma^2))", "condition": "-inf < x < inf"},
            {"name": "Standard Normal", "formula": "Z = (X-mu)/sigma ~ N(0,1)", "condition": "X ~ N(mu, sigma^2)"},
            {"name": "Exponential PDF", "formula": "f(x) = lambda * e^(-lambda*x), x >= 0", "condition": "lambda > 0"},
            {"name": "Exponential Mean/Var", "formula": "E(X) = 1/lambda, Var(X) = 1/lambda^2", "condition": "X ~ Exp(lambda)"},
            {"name": "Uniform PDF", "formula": "f(x) = 1/(b-a) for a <= x <= b", "condition": "a < b"},
            {"name": "Uniform Mean/Var", "formula": "E(X) = (a+b)/2, Var(X) = (b-a)^2/12", "condition": "X ~ U(a,b)"},
        ]
    },
    "numerical_formulas": {
        "label": "Numerical Methods Formulas",
        "formulas": [
            {"name": "Newton-Raphson", "formula": "x(n+1) = x(n) - f(x(n))/f'(x(n))", "condition": "f'(x(n)) != 0"},
            {"name": "Bisection", "formula": "c = (a+b)/2, check sign of f(c)", "condition": "f(a)*f(b) < 0"},
            {"name": "Regula-Falsi", "formula": "c = (a*f(b) - b*f(a))/(f(b) - f(a))", "condition": "f(a)*f(b) < 0"},
            {"name": "Trapezoidal Rule", "formula": "integral approx (h/2)[y0 + 2(y1+...+y(n-1)) + yn]", "condition": "Any n"},
            {"name": "Simpson's 1/3", "formula": "integral approx (h/3)[y0 + 4(y1+y3+...) + 2(y2+y4+...) + yn]", "condition": "n MUST be even"},
            {"name": "Simpson's 3/8", "formula": "integral approx (3h/8)[y0 + 3(y1+y2) + 2y3 + 3(y4+y5) + ...]", "condition": "n divisible by 3"},
            {"name": "RK4 k1", "formula": "k1 = h*f(xn, yn)", "condition": ""},
            {"name": "RK4 k2", "formula": "k2 = h*f(xn + h/2, yn + k1/2)", "condition": ""},
            {"name": "RK4 k3", "formula": "k3 = h*f(xn + h/2, yn + k2/2)", "condition": ""},
            {"name": "RK4 k4", "formula": "k4 = h*f(xn + h, yn + k3)", "condition": ""},
            {"name": "RK4 Update", "formula": "y(n+1) = yn + (k1 + 2k2 + 2k3 + k4)/6", "condition": ""},
            {"name": "Newton Forward", "formula": "y = y0 + s*Delta(y0) + s(s-1)/2!*Delta^2(y0) + ...", "condition": "s = (x-x0)/h, equally spaced"},
            {"name": "Lagrange", "formula": "P(x) = sum yk * product(j!=k) (x-xj)/(xk-xj)", "condition": "Any spacing"},
        ]
    }
}

# ══════════════════════════════════════════════════════════════
#  TOPIC DIFFICULTY RATINGS (no AI call)
# ══════════════════════════════════════════════════════════════
TOPIC_DIFFICULTY = {
    "diff_calc":        {"difficulty": 6, "exam_weight": "15-20%", "tip": "Focus on MVT and Taylor series — appear every year"},
    "partial_diff":     {"difficulty": 7, "exam_weight": "15-20%", "tip": "Euler theorem and Lagrange multipliers are guaranteed questions"},
    "integral_calc":    {"difficulty": 7, "exam_weight": "20-25%", "tip": "Beta-Gamma and change of order — practice at least 5 problems each"},
    "infinite_series":  {"difficulty": 5, "exam_weight": "10-15%", "tip": "Master ratio test and root test — they solve 80% of problems"},
    "linear_algebra":   {"difficulty": 6, "exam_weight": "25-30%", "tip": "Eigenvalues and Cayley-Hamilton — never skip these"},
    "ode_first":        {"difficulty": 5, "exam_weight": "15-20%", "tip": "Identify the type first — then the method is automatic"},
    "ode_higher":       {"difficulty": 7, "exam_weight": "20-25%", "tip": "CF + PI method — practice all PI cases especially failure case"},
    "laplace":          {"difficulty": 6, "exam_weight": "20-25%", "tip": "Memorize the table — 50% of marks come from standard transforms"},
    "vector_calc":      {"difficulty": 8, "exam_weight": "25-30%", "tip": "Green, Stokes, Gauss — one will definitely be asked"},
    "complex_analysis": {"difficulty": 8, "exam_weight": "25-30%", "tip": "Residue theorem is the king — master it"},
    "fourier_series":   {"difficulty": 6, "exam_weight": "15-20%", "tip": "Even/odd check saves half the calculation — always do it first"},
    "probability":      {"difficulty": 5, "exam_weight": "25-30%", "tip": "Normal distribution + Bayes theorem — most asked"},
    "numerical":        {"difficulty": 4, "exam_weight": "20-25%", "tip": "Formula-based — easiest marks if you memorize the formulas"},
    "transforms":       {"difficulty": 7, "exam_weight": "20-25%", "tip": "Z-transform ROC is where students lose marks — always state it"}
}


# ══════════════════════════════════════════════════════════════
#  API HELPERS — with caching, validation, error handling
# ══════════════════════════════════════════════════════════════
def call_groq(prompt, system=""):
    if not groq_client:
        raise RuntimeError("AI service temporarily unavailable")
    try:
        truncated_system = system[:4000] if len(system) > 4000 else system
        if len(prompt) > 30000:
            logger.warning("Truncating Groq prompt from %d to 30000 chars", len(prompt))
            prompt = prompt[:30000]
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": truncated_system},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=GROQ_MAX_TOKENS,
            temperature=0.1
        )
        return resp.choices[0].message.content
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg or "auth" in error_msg:
            raise RuntimeError("Authentication error with AI provider")
        elif "rate limit" in error_msg or "429" in error_msg:
            raise RuntimeError("AI provider rate limit reached — please wait a moment")
        elif "timeout" in error_msg:
            raise RuntimeError("AI provider timeout — please try again")
        else:
            logger.warning("Groq error: %s", e)
            raise RuntimeError("AI provider temporarily unavailable")

def call_gemini(prompt, model_name, system=""):
    if not gemini_client:
        raise RuntimeError("AI service temporarily unavailable")
    try:
        if len(prompt) > 30000:
            logger.warning("Truncating Gemini prompt from %d to 30000 chars", len(prompt))
            prompt = prompt[:30000]
        # FIXED: Include system message in Gemini call
        full_prompt = system + "\n\n" + prompt if system else prompt
        resp = gemini_client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config={"temperature": 0.1}
        )
        if not resp.text:
            raise RuntimeError(f"{model_name} returned empty response")
        return resp.text
    except Exception as e:
        error_msg = str(e).lower()
        if "api key" in error_msg or "auth" in error_msg:
            raise RuntimeError("Authentication error with AI provider")
        elif "rate limit" in error_msg or "429" in error_msg:
            raise RuntimeError("AI provider rate limit reached — please wait a moment")
        else:
            logger.warning("Gemini %s error: %s", model_name, e)
            raise RuntimeError("AI provider temporarily unavailable")

def get_eng_response(full_prompt, prefer_provider=None, context_type="university"):
    """Get AI response with caching, validation, and smart provider routing"""
    cached_resp, cached_source = get_cached(full_prompt)
    if cached_resp:
        return cached_resp, cached_source

    system_msg = (GATE_CONTEXT + "\n" + GATE_FORMAT) if context_type == "gate" else (ENG_CONTEXT + "\n" + ENG_FORMAT)
    start_time = time.time()
    timeout = 30
    prompt_length = len(full_prompt)

    if prefer_provider == "gemini" or prompt_length > 15000:
        provider_order = [
            ("gemini", GEMINI_CASCADE),
            ("groq", [(GROQ_MODEL, "Groq")])
        ]
    else:
        provider_order = [
            ("groq", [(GROQ_MODEL, "Groq")]),
            ("gemini", GEMINI_CASCADE)
        ]

    for provider_type, models in provider_order:
        for model_info in models:
            if time.time() - start_time > timeout:
                break
            try:
                if provider_type == "groq":
                    response = call_groq(full_prompt, system=system_msg)
                    label = "Groq"
                else:
                    model_name, label = model_info
                    response = call_gemini(full_prompt, model_name, system=system_msg)

                if is_valid_response(response):
                    set_cache(full_prompt, response, label)
                    return response, label
                else:
                    logger.warning("%s returned invalid response, trying next", label)
            except Exception as e:
                logger.warning("%s failed: %s", provider_type, e)
                time.sleep(0.2)

    return "All AI services are temporarily busy. Please try again in a moment. This service is 100% free — thank you for your patience.", "None"


# ══════════════════════════════════════════════════════════════
#  STANDARDIZED RESPONSE WRAPPER
# ══════════════════════════════════════════════════════════════
def make_response(response, source, topic_key="", **extra):
    result = {
        "response":  response,
        "source":    source,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cached":    "(cached)" in source if isinstance(source, str) else False,
    }
    if topic_key:
        result["references"] = REFERENCES.get(topic_key, [])
    result.update(extra)
    return jsonify(result)


# ══════════════════════════════════════════════════════════════
#
#                    R O U T E S
#
# ══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
#  ZERO COST ROUTES (No AI Call)
# ─────────────────────────────────────────────

@eng_bp.route("/eng/syllabus")
def get_syllabus():
    return jsonify(SYLLABUS)

@eng_bp.route("/eng/health")
def health():
    total_subtopics = 0
    total_topics = 0
    for sem_data in SYLLABUS.values():
        for topic_data in sem_data["topics"].values():
            total_topics += 1
            total_subtopics += len(topic_data["subtopics"])

    total_gate_misconceptions = sum(len(v) for v in GATE_MISCONCEPTIONS.values())
    total_gate_formulas = sum(len(v["formulas"]) for v in GATE_QUICK_FORMULAS.values())

    return jsonify({
        "status":  "healthy",
        "app":     "MathSphere Engineering by Anupam Nigam",
        "version": "3.0",
        "cost":    "100% FREE — zero rupees",
        "stats": {
            "semesters":              len(SYLLABUS),
            "topics":                 total_topics,
            "subtopics":              total_subtopics,
            "prerequisites":          len(PREREQUISITES),
            "misconceptions":         sum(len(v) for v in MISCONCEPTIONS.values()),
            "gate_misconceptions":    total_gate_misconceptions,
            "quick_formulas":         sum(len(v["formulas"]) for v in QUICK_FORMULAS.values()),
            "gate_formulas":          total_gate_formulas,
            "method_selectors":       sum(len(v["decision_tree"]) for v in METHOD_SELECTOR.values()),
            "subject_connections":    sum(len(v["connections"]) for v in SUBJECT_CONNECTIONS.values()),
            "cached_responses":       len(_response_cache),
            "active_students":        len(_student_progress),
            "gate_branches":          len(GATE_DATA["branches"]),
            "competitive_exams":      4
        },
        "competitive_exams": ["GATE", "IIT JAM", "CSIR NET", "NBHM"],
        "free_providers": {
            "groq":   {"status": "configured" if GROQ_API_KEY else "missing", "tier": "FREE", "limit": "30 req/min"},
            "gemini": {"status": "configured" if GEMINI_API_KEY else "missing", "tier": "FREE", "limit": "15 req/min"}
        },
        "routes": {
            "zero_cost": [
                "GET  /eng/syllabus",
                "GET  /eng/health",
                "GET  /eng/formulas/all",
                "GET  /eng/formulas/search?q=...",
                "POST /eng/formulas",
                "POST /eng/methodselector",
                "GET  /eng/methodselector/all",
                "POST /eng/roadmap",
                "GET  /eng/progress",
                "POST /eng/progress/update",
                "POST /eng/misconceptions",
                "POST /eng/selftest",
                "POST /eng/selftest/answer",
                "POST /eng/examplan",
                "POST /eng/difficulty",
                "POST /eng/prerequisites",
                "GET  /eng/export/syllabus",
                "POST /eng/export/formulas",
                "POST /eng/export/misconceptions",
                "POST /eng/export/methods",
                "GET  /eng/gate/info",
                "POST /eng/gate/syllabus",
                "POST /eng/gate/analysis",
                "POST /eng/gate/formulas",
                "POST /eng/gate/misconceptions",
                "GET  /eng/jam/info",
                "GET  /eng/csir/info",
                "GET  /eng/nbhm/info",
                "GET  /eng/competitive/exams"
            ],
            "ai_powered": [
                "POST /eng/learn",
                "POST /eng/revision",
                "POST /eng/pyq",
                "POST /eng/mocktest",
                "POST /eng/formulabooklet",
                "POST /eng/connections",
                "POST /eng/ask",
                "POST /eng/diagnose",
                "POST /eng/solve",
                "POST /eng/compare",
                "POST /eng/examstrategy",
                "POST /eng/doubt",
                "POST /eng/gate/practice",
                "POST /eng/gate/mock",
                "POST /eng/gate/strategy",
                "POST /eng/jam/practice",
                "POST /eng/csir/practice"
            ]
        }
    })

@eng_bp.route("/eng/formulas/all")
def all_formula_categories():
    categories = {k: {"label": v["label"], "count": len(v["formulas"])} for k, v in QUICK_FORMULAS.items()}
    gate_categories = {f"gate_{k}": {"label": v["label"], "count": len(v["formulas"])} for k, v in GATE_QUICK_FORMULAS.items()}
    categories.update(gate_categories)
    return jsonify({"categories": categories})

@eng_bp.route("/eng/formulas/search")
def search_formulas():
    query = request.args.get("q", "").lower().strip()
    if not query or len(query) < 2:
        return jsonify({"error": "Search query must be at least 2 characters", "results": []}), 400
    results = []
    # Search university formulas
    for category, data in QUICK_FORMULAS.items():
        for formula in data["formulas"]:
            if (query in formula["name"].lower() or
                query in formula["formula"].lower() or
                query in formula.get("condition", "").lower()):
                results.append({
                    "category":       category,
                    "category_label": data["label"],
                    "name":           formula["name"],
                    "formula":        formula["formula"],
                    "condition":      formula.get("condition", ""),
                    "level":          "university"
                })
    # Search GATE formulas
    for category, data in GATE_QUICK_FORMULAS.items():
        for formula in data["formulas"]:
            if (query in formula["name"].lower() or
                query in formula["formula"].lower() or
                query in formula.get("condition", "").lower()):
                results.append({
                    "category":       f"gate_{category}",
                    "category_label": data["label"],
                    "name":           formula["name"],
                    "formula":        formula["formula"],
                    "condition":      formula.get("condition", ""),
                    "level":          "gate"
                })
    return jsonify({"query": query, "count": len(results), "results": results})

@eng_bp.route("/eng/formulas", methods=["POST"])
def quick_formulas_route():
    try:
        data, err, code = validate_json("category")
        if err:
            return err, code
        category = data.get("category", "")
        # Check university formulas
        formulas = QUICK_FORMULAS.get(category)
        if not formulas:
            # Check GATE formulas
            gate_key = category.replace("gate_", "") if category.startswith("gate_") else category
            formulas = GATE_QUICK_FORMULAS.get(gate_key)
        if not formulas:
            all_categories = list(QUICK_FORMULAS.keys()) + [f"gate_{k}" for k in GATE_QUICK_FORMULAS.keys()]
            return jsonify({
                "error":     f"Category '{category}' not found",
                "available": all_categories
            }), 404
        return jsonify(formulas)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/methodselector/all")
def all_method_selectors():
    return jsonify({"selectors": {k: v["label"] for k, v in METHOD_SELECTOR.items()}})

@eng_bp.route("/eng/methodselector", methods=["POST"])
def method_selector_route():
    try:
        data, err, code = validate_json("category")
        if err:
            return err, code
        category = data.get("category", "")
        selector = METHOD_SELECTOR.get(category)
        if not selector:
            return jsonify({
                "error":     f"Category '{category}' not found",
                "available": list(METHOD_SELECTOR.keys())
            }), 404
        return jsonify(selector)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/roadmap", methods=["POST"])
def roadmap():
    try:
        data, err, code = validate_json("topic")
        if err:
            return err, code
        topic_key = data.get("topic", "")
        roadmap_data = build_roadmap(topic_key)
        if not roadmap_data:
            return jsonify({"error": f"Topic '{topic_key}' not found"}), 404
        return jsonify(roadmap_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/progress", methods=["GET"])
def get_student_progress():
    try:
        student_id = request.args.get("student_id", "anonymous")
        progress = get_progress(student_id)
        total_subtopics = 0
        for sem_data in SYLLABUS.values():
            for topic_data in sem_data["topics"].values():
                total_subtopics += len(topic_data["subtopics"])
        completed = len(progress["completed_subtopics"])
        percentage = round((completed / total_subtopics) * 100, 1) if total_subtopics > 0 else 0

        gate_stats = progress.get("gate_progress", {})
        gate_accuracy = 0
        if gate_stats.get("questions_attempted", 0) > 0:
            gate_accuracy = round(
                (gate_stats["questions_correct"] / gate_stats["questions_attempted"]) * 100, 1
            )

        return jsonify({
            "progress":              progress,
            "total_subtopics":       total_subtopics,
            "completed_count":       completed,
            "completion_percentage": percentage,
            "gate_stats": {
                "questions_attempted": gate_stats.get("questions_attempted", 0),
                "questions_correct":   gate_stats.get("questions_correct", 0),
                "accuracy":            gate_accuracy,
                "mock_tests_taken":    len(gate_stats.get("mock_tests", [])),
                "weak_topics":         gate_stats.get("weak_gate_topics", []),
                "strong_topics":       gate_stats.get("strong_gate_topics", [])
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/progress/update", methods=["POST"])
def update_student_progress():
    try:
        data, err, code = validate_json("action")
        if err:
            return err, code
        student_id = data.get("student_id", "anonymous")
        action = data.get("action", "")
        valid_actions = [
            "complete_subtopic", "mark_weak", "mark_strong",
            "misconception_found", "mock_test", "study_time",
            "gate_question", "gate_mock", "gate_mark_weak", "gate_mark_strong"
        ]
        if action not in valid_actions:
            return jsonify({"error": f"Invalid action. Valid: {', '.join(valid_actions)}"}), 400
        progress = update_progress(student_id, action, data)
        return jsonify({"progress": progress, "message": f"Progress updated: {action}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/misconceptions", methods=["POST"])
def get_misconceptions():
    try:
        data, err, code = validate_json("topic")
        if err:
            return err, code
        topic = data.get("topic", "")
        level = data.get("level", "university")

        if level == "gate":
            topic_misconceptions = GATE_MISCONCEPTIONS.get(topic, [])
            questions = [{
                "id":            m["id"],
                "question":      m.get("trap_question", ""),
                "danger":        m.get("danger", "HIGH"),
                "misconception": m["misconception"],
                "gate_relevance": m.get("gate_relevance", ""),
                "shortcut":      m.get("shortcut", "")
            } for m in topic_misconceptions]
        else:
            topic_misconceptions = MISCONCEPTIONS.get(topic, [])
            questions = [{
                "id":            m["id"],
                "question":      m["question"],
                "danger":        m["danger"],
                "misconception": m["misconception"]
            } for m in topic_misconceptions]

        return jsonify({"questions": questions, "topic": topic, "level": level})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/prerequisites", methods=["POST"])
def prerequisites_route():
    try:
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        subtopic = data.get("subtopic", "")
        prereqs = {}
        if subtopic in PREREQUISITES:
            prereqs[subtopic] = PREREQUISITES[subtopic]
        subtopic_lower = subtopic.lower()
        for key, val in PREREQUISITES.items():
            key_lower = key.lower()
            if key_lower in subtopic_lower or subtopic_lower in key_lower:
                prereqs[key] = val
            else:
                key_words = set(key_lower.split())
                subtopic_words = set(subtopic_lower.split())
                if len(key_words & subtopic_words) >= 2:
                    prereqs[key] = val
        return jsonify({"subtopic": subtopic, "prerequisites": prereqs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/difficulty", methods=["POST"])
def topic_difficulty():
    try:
        data = request.get_json(force=True, silent=True) or {}
        topics = data.get("topics", list(TOPIC_DIFFICULTY.keys()))
        result = {}
        for topic in topics:
            if topic in TOPIC_DIFFICULTY:
                info = TOPIC_DIFFICULTY[topic]
                label = get_topic_label(topic)
                result[topic] = {
                    "label":            label,
                    "difficulty":       info["difficulty"],
                    "difficulty_label": "Easy" if info["difficulty"] <= 4 else "Medium" if info["difficulty"] <= 6 else "Hard" if info["difficulty"] <= 8 else "Very Hard",
                    "exam_weight":      info["exam_weight"],
                    "tip":              info["tip"],
                    "misconceptions":   len(MISCONCEPTIONS.get(topic, [])),
                    "gate_misconceptions": len(GATE_MISCONCEPTIONS.get(topic, [])),
                    "formulas":         get_formula_count_for_topic(topic),  # FIXED: uses mapping
                    "gate_analysis":    GATE_TOPIC_ANALYSIS.get(topic, {}).get("frequency", "N/A")
                }
        return jsonify({"difficulty_scale": "1 (easiest) to 10 (hardest)", "topics": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/selftest", methods=["POST"])
def self_test():
    try:
        data = request.get_json(force=True, silent=True) or {}
        topics = data.get("topics", list(MISCONCEPTIONS.keys()))
        level = data.get("level", "university")
        num_questions = min(validate_positive_int(data.get("num_questions", 10), "num_questions", 1, 30, 10), 30)

        all_questions = []
        source_db = GATE_MISCONCEPTIONS if level == "gate" else MISCONCEPTIONS

        for topic in topics:
            if topic in source_db:
                for m in source_db[topic]:
                    q_text = m.get("trap_question", m.get("question", ""))
                    all_questions.append({
                        "id":            m["id"],
                        "topic":         topic,
                        "question":      q_text,
                        "danger":        m.get("danger", "MEDIUM"),
                        "misconception": m["misconception"],
                        "level":         level
                    })

        danger_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
        all_questions.sort(key=lambda q: danger_order.get(q["danger"], 3))
        selected = all_questions[:num_questions]

        return jsonify({
            "test_name":     f"MathSphere {'GATE' if level == 'gate' else 'University'} Self-Assessment",
            "num_questions": len(selected),
            "level":         level,
            "instructions":  "Answer each question IN YOUR OWN WORDS before looking at the answer. Be honest — this is for YOUR learning.",
            "questions":     selected,
            "tip":           "After answering, use /eng/diagnose to check your understanding with AI analysis."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/selftest/answer", methods=["POST"])
def self_test_answer():
    try:
        data, err, code = validate_json("question_id")
        if err:
            return err, code
        question_id = data.get("question_id", "")

        # Search university misconceptions
        for topic, misconceptions in MISCONCEPTIONS.items():
            for m in misconceptions:
                if m["id"] == question_id:
                    return jsonify({
                        "id":                      m["id"],
                        "question":                m["question"],
                        "correct_understanding":   m["correct"],
                        "common_misconception":    m["misconception"],
                        "why_students_believe_it": m["why_students_believe_it"],
                        "danger_level":            m["danger"],
                        "topic":                   topic,
                        "level":                   "university",
                        "tip": "If you got this wrong, don't worry! Now you know the truth — use it in your exam."
                    })

        # Search GATE misconceptions
        for topic, misconceptions in GATE_MISCONCEPTIONS.items():
            for m in misconceptions:
                if m["id"] == question_id:
                    return jsonify({
                        "id":                    m["id"],
                        "trap_question":         m.get("trap_question", ""),
                        "truth":                 m.get("truth", ""),
                        "answer":                m.get("answer", ""),
                        "misconception":         m["misconception"],
                        "gate_relevance":        m.get("gate_relevance", ""),
                        "shortcut":              m.get("shortcut", ""),
                        "danger_level":          m.get("danger", "HIGH"),
                        "topic":                 topic,
                        "level":                 "gate",
                        "tip": "This is a common GATE trap. Understanding WHY the misconception is wrong will save you marks."
                    })

        return jsonify({"error": "Question not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/examplan", methods=["POST"])
def exam_plan():
    try:
        data = request.get_json(force=True, silent=True) or {}
        hours_available = validate_positive_int(data.get("hours", 24), "hours", 1, 720, 24)
        topics_to_cover = data.get("topics", [])

        all_topic_keys = []
        for sem_data in SYLLABUS.values():
            all_topic_keys.extend(sem_data["topics"].keys())

        if not topics_to_cover:
            return jsonify({
                "error":     "Provide list of topic keys in 'topics' field",
                "available": all_topic_keys
            }), 400

        plan = {
            "title":           f"Study Plan — {hours_available} Hours Remaining",
            "total_hours":     hours_available,
            "strategy":        [],
            "phase1_formulas": [],
            "phase2_practice": [],
            "phase3_revision": []
        }

        formula_hours  = round(hours_available * 0.3, 1)
        practice_hours = round(hours_available * 0.5, 1)
        revision_hours = round(hours_available * 0.2, 1)
        hours_per_topic = round(hours_available / len(topics_to_cover), 1) if topics_to_cover else 0

        for topic_key in topics_to_cover:
            topic_label = get_topic_label(topic_key)
            subtopic_list = []
            for sem_data in SYLLABUS.values():
                if topic_key in sem_data["topics"]:
                    subtopic_list = sem_data["topics"][topic_key]["subtopics"]
                    break

            total_subtopics = len(subtopic_list)
            must_do = subtopic_list[:total_subtopics // 2]
            good_to_do = subtopic_list[total_subtopics // 2:]

            plan["strategy"].append({
                "topic":               topic_label,
                "hours_allocated":     hours_per_topic,
                "must_do_subtopics":   must_do[:8],
                "if_time_permits":     good_to_do[:5],
                "misconception_count": len(MISCONCEPTIONS.get(topic_key, [])),
                "gate_relevance":      GATE_TOPIC_ANALYSIS.get(topic_key, {}).get("frequency", "N/A")
            })

            formula_key = FORMULA_KEY_MAP.get(topic_key)
            if formula_key and formula_key in QUICK_FORMULAS:
                plan["phase1_formulas"].append({
                    "topic":         topic_label,
                    "formula_count": len(QUICK_FORMULAS[formula_key]["formulas"]),
                    "endpoint":      f"/eng/formulas with category={formula_key}"
                })

        plan["timeline"] = [
            {"phase": "Phase 1: Formulas",  "hours": formula_hours,  "what": "Memorize key formulas using /eng/formulas"},
            {"phase": "Phase 2: Practice",  "hours": practice_hours, "what": "Solve problems using /eng/learn (examples section)"},
            {"phase": "Phase 3: Revision",  "hours": revision_hours, "what": "Quick revision + self-test using /eng/selftest"},
            {"phase": "Last 30 Minutes",    "hours": 0.5,           "what": "Review misconceptions using /eng/misconceptions"}
        ]

        plan["motivation"] = f"You have {hours_available} hours. That is enough. Focus on {len(topics_to_cover)} topics. Do formulas first, then practice, then revise. You've got this."

        return jsonify(plan)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
#  COMPETITIVE EXAM ROUTES (Zero Cost)
# ─────────────────────────────────────────────

@eng_bp.route("/eng/competitive/exams")
def competitive_exams():
    return jsonify({
        "exams": {
            "gate": {
                "name": GATE_DATA["exam_info"]["name"],
                "website": GATE_DATA["exam_info"]["official_website"],
                "math_weightage": GATE_DATA["exam_info"]["math_weightage"],
                "branches": list(GATE_DATA["branches"].keys()),
                "endpoints": ["/eng/gate/info", "/eng/gate/syllabus", "/eng/gate/analysis",
                            "/eng/gate/formulas", "/eng/gate/misconceptions",
                            "/eng/gate/practice", "/eng/gate/mock", "/eng/gate/strategy"]
            },
            "iit_jam": {
                "name": JAM_DATA["exam_info"]["name"],
                "website": JAM_DATA["exam_info"]["official_website"],
                "papers": list(JAM_DATA["exam_info"]["papers"].keys()),
                "endpoints": ["/eng/jam/info", "/eng/jam/practice"]
            },
            "csir_net": {
                "name": CSIR_NET_DATA["exam_info"]["name"],
                "website": CSIR_NET_DATA["exam_info"]["official_website"],
                "endpoints": ["/eng/csir/info", "/eng/csir/practice"]
            },
            "nbhm": {
                "name": NBHM_DATA["exam_info"]["name"],
                "website": NBHM_DATA["exam_info"]["official_website"],
                "endpoints": ["/eng/nbhm/info"]
            }
        }
    })

@eng_bp.route("/eng/gate/info")
def gate_info():
    return jsonify(GATE_DATA["exam_info"])

@eng_bp.route("/eng/gate/syllabus", methods=["POST"])
def gate_syllabus():
    try:
        data = request.get_json(force=True, silent=True) or {}
        branch = data.get("branch", "cs")
        branch_data = GATE_DATA["branches"].get(branch)
        if not branch_data:
            return jsonify({
                "error": f"Branch '{branch}' not found",
                "available": list(GATE_DATA["branches"].keys())
            }), 404
        return jsonify({
            "branch": branch_data["label"],
            "code": branch_data["code"],
            "math_topics": branch_data["math_topics"],
            "specific_syllabus": branch_data["specific_syllabus"],
            "topic_mapping": GATE_DATA["topic_mapping"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/gate/analysis", methods=["POST"])
def gate_analysis():
    try:
        data = request.get_json(force=True, silent=True) or {}
        topic = data.get("topic", "")
        if topic:
            analysis = GATE_TOPIC_ANALYSIS.get(topic)
            if not analysis:
                return jsonify({
                    "error": f"No analysis for topic '{topic}'",
                    "available": list(GATE_TOPIC_ANALYSIS.keys())
                }), 404
            return jsonify({"topic": topic, "analysis": analysis})
        else:
            return jsonify({"all_topics": GATE_TOPIC_ANALYSIS})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/gate/formulas", methods=["POST"])
def gate_formulas():
    try:
        data = request.get_json(force=True, silent=True) or {}
        category = data.get("category", "")
        if category:
            formulas = GATE_QUICK_FORMULAS.get(category)
            if not formulas:
                return jsonify({
                    "error": f"Category '{category}' not found",
                    "available": list(GATE_QUICK_FORMULAS.keys())
                }), 404
            return jsonify(formulas)
        else:
            return jsonify({
                "categories": {k: {"label": v["label"], "count": len(v["formulas"])}
                             for k, v in GATE_QUICK_FORMULAS.items()}
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/gate/misconceptions", methods=["POST"])
def gate_misconceptions_route():
    try:
        data = request.get_json(force=True, silent=True) or {}
        topic = data.get("topic", "")
        if topic:
            misconceptions = GATE_MISCONCEPTIONS.get(topic, [])
            return jsonify({"topic": topic, "misconceptions": misconceptions})
        else:
            summary = {}
            for topic_key, items in GATE_MISCONCEPTIONS.items():
                summary[topic_key] = {
                    "count": len(items),
                    "ids": [m["id"] for m in items],
                    "dangers": [m.get("danger", "HIGH") for m in items]
                }
            return jsonify({"all_topics": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/jam/info")
def jam_info():
    return jsonify(JAM_DATA)

@eng_bp.route("/eng/csir/info")
def csir_info():
    return jsonify(CSIR_NET_DATA)

@eng_bp.route("/eng/nbhm/info")
def nbhm_info():
    return jsonify(NBHM_DATA)


# ─────────────────────────────────────────────
#  EXPORT ROUTES (No AI Call — Offline Study)
# ─────────────────────────────────────────────

@eng_bp.route("/eng/export/syllabus")
def export_syllabus():
    return jsonify({
        "title":         "MathSphere — Complete Engineering Math Syllabus",
        "author":        "MathSphere Engineering by Anupam Nigam",
        "version":       "3.0",
        "generated":     time.strftime("%Y-%m-%d %H:%M:%S"),
        "syllabus":      SYLLABUS,
        "prerequisites": PREREQUISITES,
        "references":    REFERENCES,
        "gate_syllabus": {b: d["specific_syllabus"] for b, d in GATE_DATA["branches"].items()}
    })

@eng_bp.route("/eng/export/formulas", methods=["POST"])
def export_formulas():
    try:
        data = request.get_json(force=True, silent=True) or {}
        categories = data.get("categories", list(QUICK_FORMULAS.keys()))
        include_gate = data.get("include_gate", True)
        export = {
            "title":     "MathSphere Engineering — Formula Booklet",
            "author":    "MathSphere Engineering by Anupam Nigam",
            "version":   "3.0",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "university_formulas":  {},
            "gate_formulas":        {}
        }
        for cat in categories:
            if cat in QUICK_FORMULAS:
                export["university_formulas"][cat] = QUICK_FORMULAS[cat]
        if include_gate:
            for cat, data_cat in GATE_QUICK_FORMULAS.items():
                export["gate_formulas"][cat] = data_cat
        return jsonify(export)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/export/misconceptions", methods=["POST"])
def export_misconceptions():
    try:
        data = request.get_json(force=True, silent=True) or {}
        topics = data.get("topics", list(MISCONCEPTIONS.keys()))
        include_gate = data.get("include_gate", True)
        export = {
            "title":     "MathSphere — Common Misconceptions Guide",
            "author":    "MathSphere Engineering by Anupam Nigam",
            "version":   "3.0",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "purpose":   "Read before exam to avoid common mistakes",
            "university_misconceptions": {},
            "gate_misconceptions":       {}
        }
        for topic in topics:
            if topic in MISCONCEPTIONS:
                export["university_misconceptions"][topic] = MISCONCEPTIONS[topic]
        if include_gate:
            for topic in topics:
                if topic in GATE_MISCONCEPTIONS:
                    export["gate_misconceptions"][topic] = GATE_MISCONCEPTIONS[topic]
        return jsonify(export)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/export/methods", methods=["POST"])
def export_methods():
    return jsonify({
        "title":     "MathSphere — Method Selection Guide",
        "author":    "MathSphere Engineering by Anupam Nigam",
        "version":   "3.0",
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "selectors": METHOD_SELECTOR
    })


# ─────────────────────────────────────────────
#  AI-POWERED ROUTES — University Level
# ─────────────────────────────────────────────

@eng_bp.route("/eng/learn", methods=["POST"])
def learn():
    try:
        if not check_rate_limit(6):
            return rate_limit_response()
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic    = sanitize_input(data.get("topic", ""))
        subtopic = sanitize_input(data.get("subtopic", ""))
        section  = data.get("section", "definition")
        if section not in ("definition", "theorem", "examples", "practice", "intuition"):
            return jsonify({"error": "Invalid section. Choose: definition, theorem, examples, practice, intuition"}), 400
        prereqs  = PREREQUISITES.get(subtopic, [])
        prompt   = build_learn_prompt(topic, subtopic, section)
        response, source = get_eng_response(prompt)
        return make_response(response, source, topic_key=topic, prerequisites=prereqs, section=section)
    except Exception as e:
        logger.error("Learn error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/revision", methods=["POST"])
def revision():
    try:
        if not check_rate_limit(6):
            return rate_limit_response()
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic    = sanitize_input(data.get("topic", ""))
        subtopic = sanitize_input(data.get("subtopic", ""))
        prompt   = build_revision_prompt(topic, subtopic)
        response, source = get_eng_response(prompt)
        return make_response(response, source, topic_key=topic)
    except Exception as e:
        logger.error("Revision error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/pyq", methods=["POST"])
def pyq():
    try:
        if not check_rate_limit(4):
            return rate_limit_response()
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic      = sanitize_input(data.get("topic", ""))
        subtopic   = sanitize_input(data.get("subtopic", ""))
        university = data.get("university", "all")
        difficulty = data.get("difficulty", "medium")
        prompt     = build_pyq_prompt(topic, subtopic, university, difficulty)
        response, source = get_eng_response(prompt, prefer_provider="gemini")
        return make_response(response, source, topic_key=topic)
    except Exception as e:
        logger.error("PYQ error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/mocktest", methods=["POST"])
def mocktest():
    try:
        if not check_rate_limit(2):
            return rate_limit_response()
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic      = sanitize_input(data.get("topic", ""))
        subtopic   = sanitize_input(data.get("subtopic", ""))
        num_q      = validate_positive_int(data.get("num_questions", 5), "num_questions", 1, 20, 5)
        marks_each = validate_positive_int(data.get("marks_each", 5), "marks_each", 1, 10, 5)
        prompt     = build_mocktest_prompt(topic, subtopic, num_q, marks_each)
        response, source = get_eng_response(prompt, prefer_provider="gemini")

        student_id = data.get("student_id", "anonymous")
        update_progress(student_id, "mock_test", {"type": "university"})

        return make_response(response, source)
    except Exception as e:
        logger.error("Mocktest error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/formulabooklet", methods=["POST"])
def formula_booklet():
    try:
        if not check_rate_limit(4):
            return rate_limit_response()
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic    = sanitize_input(data.get("topic", ""))
        subtopic = sanitize_input(data.get("subtopic", ""))
        prompt   = build_formula_booklet_prompt(topic, subtopic)
        response, source = get_eng_response(prompt)
        return make_response(response, source, topic_key=topic)
    except Exception as e:
        logger.error("Formula booklet error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/connections", methods=["POST"])
def connections():
    try:
        data, err, code = validate_json("topic")
        if err:
            return err, code
        topic    = sanitize_input(data.get("topic", ""))
        subtopic = sanitize_input(data.get("subtopic", ""))

        topic_connections = SUBJECT_CONNECTIONS.get(topic)
        if topic_connections:
            return jsonify({
                "connections": topic_connections["connections"],
                "source":     "MathSphere Engineering",
                "references": REFERENCES.get(topic, []),
                "type":       "structured"
            })

        if not check_rate_limit(4):
            return rate_limit_response()

        prompt = ENG_CONTEXT + f"""
For the engineering mathematics topic: {subtopic}
Show exactly how this appears in different engineering subjects.

For EACH engineering subject:

SUBJECT NAME: [name]
SEMESTER: [which semester]
HOW IT IS USED:
[2-3 sentences with specific mathematical connection]
KEY FORMULA:


$$
[actual formula from this topic used in this subject]
$$


EXAMPLE:
[One specific engineering problem using this]

Cover at least 5 different engineering subjects. Be specific.
VERIFY all formulas and connections are accurate.
"""
        response, source = get_eng_response(prompt)
        return jsonify({
            "response":   response,
            "source":     source,
            "references": REFERENCES.get(topic, []),
            "type":       "generated"
        })
    except Exception as e:
        logger.error("Connections error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/ask", methods=["POST"])
def ask_eng():
    try:
        if not check_rate_limit(6):
            return rate_limit_response()
        data, err, code = validate_json("question")
        if err:
            return err, code
        question = sanitize_input(data.get("question", ""))
        if len(question) < 3:
            return jsonify({"error": "Question too short. Please ask a complete question."}), 400
        prompt   = build_ask_prompt(question)
        response, source = get_eng_response(prompt)
        return make_response(response, source)
    except Exception as e:
        logger.error("Ask error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/diagnose", methods=["POST"])
def diagnose():
    try:
        if not check_rate_limit(4):
            return rate_limit_response()
        data, err, code = validate_json("topic", "question_id", "answer")
        if err:
            return err, code
        topic          = sanitize_input(data.get("topic", ""))
        question_id    = data.get("question_id", "")
        student_answer = sanitize_input(data.get("answer", ""))

        prompt = build_misconception_prompt(topic, student_answer, question_id)
        if not prompt:
            return jsonify({"error": "Question not found"}), 404

        context_type = "gate" if question_id.startswith("G_") else "university"
        response, source = get_eng_response(prompt, context_type=context_type)

        student_id = data.get("student_id", "anonymous")
        update_progress(student_id, "misconception_found", {"misconception_id": question_id})

        return make_response(response, source)
    except Exception as e:
        logger.error("Diagnose error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/solve", methods=["POST"])
def solve():
    try:
        if not check_rate_limit(4):
            return rate_limit_response()
        data, err, code = validate_json("problem")
        if err:
            return err, code
        problem   = sanitize_input(data.get("problem", ""), max_length=3000)
        topic_key = sanitize_input(data.get("topic", ""))
        if len(problem) < 5:
            return jsonify({"error": "Problem statement too short. Please provide a complete problem."}), 400
        prompt    = build_solve_prompt(problem, topic_key)
        response, source = get_eng_response(prompt, prefer_provider="gemini")
        return make_response(response, source, topic_key=topic_key)
    except Exception as e:
        logger.error("Solve error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/compare", methods=["POST"])
def compare():
    try:
        if not check_rate_limit(4):
            return rate_limit_response()
        data, err, code = validate_json("method1", "method2")
        if err:
            return err, code
        method1   = sanitize_input(data.get("method1", ""))
        method2   = sanitize_input(data.get("method2", ""))
        topic_key = sanitize_input(data.get("topic", ""))
        prompt    = build_compare_prompt(method1, method2, topic_key)
        response, source = get_eng_response(prompt)
        return make_response(response, source, topic_key=topic_key)
    except Exception as e:
        logger.error("Compare error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/examstrategy", methods=["POST"])
def exam_strategy():
    try:
        if not check_rate_limit(3):
            return rate_limit_response()
        data, err, code = validate_json("topic")
        if err:
            return err, code
        topic_key = sanitize_input(data.get("topic", ""))
        hours_available = validate_positive_int(data.get("hours", 8), "hours", 1, 168, 8)

        if not validate_topic_key(topic_key):
            return jsonify({"error": f"Topic '{topic_key}' not found in syllabus"}), 404

        prompt = build_exam_strategy_prompt(topic_key, hours_available)
        response, source = get_eng_response(prompt, prefer_provider="gemini")
        return make_response(response, source)
    except Exception as e:
        logger.error("Exam strategy error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/doubt", methods=["POST"])
def doubt():
    try:
        if not check_rate_limit(6):
            return rate_limit_response()
        data, err, code = validate_json("doubt")
        if err:
            return err, code
        doubt_text = sanitize_input(data.get("doubt", ""))
        topic_key  = sanitize_input(data.get("topic", ""))
        subtopic   = sanitize_input(data.get("subtopic", ""))
        if len(doubt_text) < 5:
            return jsonify({"error": "Please describe your doubt in more detail."}), 400
        prompt     = build_doubt_prompt(doubt_text, topic_key, subtopic)
        response, source = get_eng_response(prompt)
        return make_response(response, source, topic_key=topic_key)
    except Exception as e:
        logger.error("Doubt error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500


# ─────────────────────────────────────────────
#  AI-POWERED ROUTES — Competitive Exams
# ─────────────────────────────────────────────

@eng_bp.route("/eng/gate/practice", methods=["POST"])
def gate_practice():
    try:
        if not check_rate_limit(4):
            return rate_limit_response()
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic_key     = sanitize_input(data.get("topic", ""))
        subtopic      = sanitize_input(data.get("subtopic", ""))
        branch        = data.get("branch", "cs")
        difficulty    = data.get("difficulty", "medium")
        question_type = data.get("question_type", "mcq")

        if branch not in GATE_DATA["branches"]:
            return jsonify({
                "error": f"Branch '{branch}' not found",
                "available": list(GATE_DATA["branches"].keys())
            }), 404

        if difficulty not in ("easy", "medium", "hard"):
            return jsonify({"error": "Difficulty must be: easy, medium, hard"}), 400

        if question_type not in ("mcq", "nat", "msq"):
            return jsonify({"error": "Question type must be: mcq, nat, msq"}), 400

        prompt = build_gate_practice_prompt(topic_key, subtopic, branch, difficulty, question_type)
        response, source = get_eng_response(prompt, prefer_provider="gemini", context_type="gate")

        student_id = data.get("student_id", "anonymous")
        update_progress(student_id, "gate_question", {"topic": topic_key})

        return make_response(response, source, topic_key=topic_key,
                           exam="GATE", branch=branch, difficulty=difficulty,
                           question_type=question_type,
                           references=REFERENCES.get("gate", []))
    except Exception as e:
        logger.error("GATE practice error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/gate/mock", methods=["POST"])
def gate_mock():
    try:
        if not check_rate_limit(2):
            return rate_limit_response()
        data = request.get_json(force=True, silent=True) or {}
        branch        = data.get("branch", "cs")
        num_questions = validate_positive_int(data.get("num_questions", 10), "num_questions", 5, 20, 10)
        time_minutes  = validate_positive_int(data.get("time_minutes", 30), "time_minutes", 10, 60, 30)

        if branch not in GATE_DATA["branches"]:
            return jsonify({
                "error": f"Branch '{branch}' not found",
                "available": list(GATE_DATA["branches"].keys())
            }), 404

        prompt = build_gate_mock_prompt(branch, num_questions, time_minutes)
        response, source = get_eng_response(prompt, prefer_provider="gemini", context_type="gate")

        student_id = data.get("student_id", "anonymous")
        update_progress(student_id, "gate_mock", {
            "branch": branch,
            "total": num_questions
        })

        return make_response(response, source,
                           exam="GATE", branch=branch,
                           num_questions=num_questions,
                           time_minutes=time_minutes,
                           references=REFERENCES.get("gate", []))
    except Exception as e:
        logger.error("GATE mock error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/gate/strategy", methods=["POST"])
def gate_strategy():
    try:
        if not check_rate_limit(3):
            return rate_limit_response()
        data = request.get_json(force=True, silent=True) or {}
        branch           = data.get("branch", "cs")
        months_remaining = validate_positive_int(data.get("months", 6), "months", 1, 24, 6)

        if branch not in GATE_DATA["branches"]:
            return jsonify({
                "error": f"Branch '{branch}' not found",
                "available": list(GATE_DATA["branches"].keys())
            }), 404

        prompt = build_gate_strategy_prompt(branch, months_remaining)
        response, source = get_eng_response(prompt, prefer_provider="gemini", context_type="gate")

        return make_response(response, source,
                           exam="GATE", branch=branch,
                           months_remaining=months_remaining,
                           references=REFERENCES.get("gate", []))
    except Exception as e:
        logger.error("GATE strategy error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/jam/practice", methods=["POST"])
def jam_practice():
    try:
        if not check_rate_limit(4):
            return rate_limit_response()
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        subtopic   = sanitize_input(data.get("subtopic", ""))
        paper_code = data.get("paper", "ma")
        difficulty = data.get("difficulty", "medium")

        if paper_code not in ("ma", "ms"):
            return jsonify({"error": "Paper code must be: ma (Mathematics) or ms (Mathematical Statistics)"}), 400

        if difficulty not in ("easy", "medium", "hard"):
            return jsonify({"error": "Difficulty must be: easy, medium, hard"}), 400

        prompt = build_jam_practice_prompt(subtopic, paper_code, difficulty)
        response, source = get_eng_response(prompt, prefer_provider="gemini", context_type="gate")

        return make_response(response, source,
                           exam="IIT JAM", paper=paper_code,
                           difficulty=difficulty,
                           references=REFERENCES.get("iit_jam", []))
    except Exception as e:
        logger.error("JAM practice error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500

@eng_bp.route("/eng/csir/practice", methods=["POST"])
def csir_practice():
    try:
        if not check_rate_limit(4):
            return rate_limit_response()
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        subtopic   = sanitize_input(data.get("subtopic", ""))
        part       = data.get("part", "b")
        difficulty = data.get("difficulty", "medium")

        if part not in ("a", "b", "c"):
            return jsonify({"error": "Part must be: a (aptitude), b (core), c (advanced)"}), 400

        if difficulty not in ("easy", "medium", "hard"):
            return jsonify({"error": "Difficulty must be: easy, medium, hard"}), 400

        prompt = build_csir_net_practice_prompt(subtopic, part, difficulty)
        response, source = get_eng_response(prompt, prefer_provider="gemini", context_type="gate")

        return make_response(response, source,
                           exam="CSIR NET", part=part,
                           difficulty=difficulty,
                           references=REFERENCES.get("csir_net", []))
    except Exception as e:
        logger.error("CSIR practice error: %s", e)
        return jsonify({"error": "Something went wrong. Please try again."}), 500


# ─────────────────────────────────────────────
#  ADMIN ROUTES
# ─────────────────────────────────────────────

@eng_bp.route("/eng/admin/cache/stats")
def cache_stats():
    with _cache_lock:
        total_entries = len(_response_cache)
        total_hits = sum(v.get("hits", 0) for v in _response_cache.values())
        oldest = min((v.get("created_at", 0) for v in _response_cache.values()), default=0)
        newest = max((v.get("created_at", 0) for v in _response_cache.values()), default=0)
    return jsonify({
        "total_entries":   total_entries,
        "max_entries":     CACHE_MAX_SIZE,
        "total_hits":      total_hits,
        "ttl_seconds":     CACHE_TTL,
        "oldest_entry":    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(oldest)) if oldest else "none",
        "newest_entry":    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(newest)) if newest else "none",
        "utilization":     f"{round(total_entries/CACHE_MAX_SIZE*100, 1)}%"
    })

@eng_bp.route("/eng/admin/cache/cleanup", methods=["POST"])
def admin_cache_cleanup():
    now = time.time()
    removed = 0
    with _cache_lock:
        expired_keys = [k for k, v in _response_cache.items() if now - v.get("created_at", 0) > CACHE_TTL]
        for k in expired_keys:
            del _response_cache[k]
            removed += 1
    logger.info("Cache cleanup: removed %d expired entries", removed)
    return jsonify({
        "message":   f"Removed {removed} expired entries",
        "remaining": len(_response_cache)
    })

@eng_bp.route("/eng/admin/rate/stats")
def rate_stats():
    with _rate_lock:
        now = time.time()
        active_ips = 0
        total_requests = 0
        for ip, timestamps in _rate_data.items():
            recent = [t for t in timestamps if now - t < 60]
            if recent:
                active_ips += 1
                total_requests += len(recent)
    return jsonify({
        "active_ips_last_minute":    active_ips,
        "total_requests_last_minute": total_requests,
        "tracked_ips":               len(_rate_data)
    })

@eng_bp.route("/eng/admin/progress/stats")
def progress_stats():
    with _progress_lock:
        total_students = len(_student_progress)
        total_completed = sum(len(p.get("completed_subtopics", [])) for p in _student_progress.values())
        total_misconceptions = sum(len(p.get("misconceptions_found", [])) for p in _student_progress.values())
        total_gate_questions = sum(p.get("gate_progress", {}).get("questions_attempted", 0) for p in _student_progress.values())
        total_gate_correct = sum(p.get("gate_progress", {}).get("questions_correct", 0) for p in _student_progress.values())

    gate_accuracy = round((total_gate_correct / total_gate_questions * 100), 1) if total_gate_questions > 0 else 0

    return jsonify({
        "total_students":            total_students,
        "max_students":              PROGRESS_MAX_STUDENTS,
        "total_subtopics_completed": total_completed,
        "total_misconceptions_found": total_misconceptions,
        "gate_stats": {
            "total_questions_attempted": total_gate_questions,
            "total_questions_correct":   total_gate_correct,
            "overall_accuracy":          gate_accuracy
        }
    })


# ══════════════════════════════════════════════════════════════
#  END OF FILE
#
#  MathSphere Engineering v3.0
#  By Anupam Nigam
#  100% FREE — Zero Rupees
#
#  Total Routes: 45+
#    Zero Cost Routes: 28+ (no AI calls)
#    AI-Powered Routes: 17+ (free Groq + Gemini)
#
#  Features:
#    UNIVERSITY LEVEL:
#    - 4 semesters, 14 topics, 250+ subtopics
#    - 40+ misconception diagnostics
#    - 100+ instant formulas
#    - 5 method selector decision trees
#    - 60+ subject connections
#    - Student progress tracking
#    - Offline export for students with limited internet
#
#    COMPETITIVE EXAMS:
#    - GATE: 5 branches (CS/EC/ME/CE/EE), topic analysis, shortcuts, traps
#    - IIT JAM: MA and MS papers, full syllabus
#    - CSIR NET: Part A/B/C, full syllabus
#    - NBHM: Exam info and topics
#    - 20+ GATE-specific misconceptions with trap questions
#    - 50+ GATE shortcut formulas
#    - GATE mock test generator
#    - Branch-specific preparation strategies
#
#    INFRASTRUCTURE:
#    - Thread-safe caching with improved eviction
#    - Rate limiting with proxy support
#    - Input sanitization (fixed regex patterns)
#    - Input validation (positive int, topic key validation)
#    - Deadlock-free progress tracker (RLock)
#    - Formula key mapping (fixed mismatch bug)
#    - Fuzzy subtopic guidance matching
#    - Smart provider routing with system message for both providers
#    - Admin dashboard with progress stats
#
#  BUGS FIXED IN v3.0:
#    1. Deadlock in progress tracker (Lock -> RLock + separated internal function)
#    2. Formula key mismatch (FORMULA_KEY_MAP added)
#    3. Regex for prompt injection ([INST] pattern fixed)
#    4. Input validation for mocktest/examstrategy (validate_positive_int)
#    5. Gemini system message (now included in call)
#    6. Nested loop break in exam_strategy_prompt (added topic validation)
#    7. New student eviction (last_active set on creation)
#    8. Rate limiter IP detection (X-Forwarded-For support)
#    9. Numerical integration decision tree ordering (most specific first)
#    10. PYQ prompt honesty (removed CONFIRMED, all REPRESENTATIVE)
#    11. Cache eviction (grace period for new entries)
#
#  Free Providers Used:
#    - Groq (Llama 3.3 70B) — 30 req/min free
#    - Google Gemini (2.5 Flash, 2.0 Flash) — 15 req/min free
#
# ══════════════════════════════════════════════════════════════
