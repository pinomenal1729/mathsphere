from flask import Blueprint, jsonify, request
from groq import Groq
from google import genai
from dotenv import load_dotenv
import os, time, hashlib

load_dotenv()

eng_bp = Blueprint('engineering', __name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GROQ_MODEL     = "llama-3.3-70b-versatile"
GROQ_MAX_TOKENS = 8000
GEMINI_CASCADE = [("gemini-2.5-flash", "Gemini 2.5 Flash"), ("gemini-2.0-flash", "Gemini 2.0 Flash")]

# ══════════════════════════════════════════════════════════════
#  MODULE-LEVEL CLIENTS — instantiated once, reused forever
# ══════════════════════════════════════════════════════════════
groq_client   = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ══════════════════════════════════════════════════════════════
#  SIMPLE RESPONSE CACHE — saves API calls, zero cost
# ══════════════════════════════════════════════════════════════
_response_cache = {}
CACHE_MAX_SIZE  = 200  # prevent memory bloat

def cache_key(prompt):
    return hashlib.sha256(prompt.encode()).hexdigest()

def get_cached(prompt):
    key = cache_key(prompt)
    if key in _response_cache:
        entry = _response_cache[key]
        entry["hits"] = entry.get("hits", 0) + 1
        return entry["response"], entry["source"] + " (cached)"
    return None, None

def set_cache(prompt, response, source):
    if len(_response_cache) >= CACHE_MAX_SIZE:
        # evict least-hit entry
        min_key = min(_response_cache, key=lambda k: _response_cache[k].get("hits", 0))
        del _response_cache[min_key]
    _response_cache[cache_key(prompt)] = {
        "response": response,
        "source":   source,
        "hits":     0
    }


# ══════════════════════════════════════════════════════════════
#  SYLLABUS DATA — IIT/NIT/Mumbai University/VTU pattern
#  Fully expanded — every exam question type covered
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
#  PREREQUISITES — hardcoded, zero AI calls
# ══════════════════════════════════════════════════════════════
PREREQUISITES = {
    "Limits and Continuity":              ["Basic functions and graphs","Algebra of limits"],
    "Differentiability":                  ["Limits and Continuity"],
    "Rolle's Theorem":                    ["Differentiability","Limits and Continuity"],
    "Lagrange's Mean Value Theorem":      ["Rolle's Theorem","Differentiability"],
    "Cauchy's Mean Value Theorem":        ["Lagrange's Mean Value Theorem"],
    "L'Hopital's Rule":                   ["Limits and Continuity","Differentiability","Indeterminate Forms"],
    "Taylor's Theorem":                   ["Differentiability","Maclaurin Series"],
    "Maclaurin Series":                   ["Differentiability","Limits and Continuity"],
    "Indeterminate Forms":                ["Limits and Continuity","L'Hopital's Rule"],
    "Curvature and Radius of Curvature":  ["Differentiability","Parametric equations"],
    "Partial Derivatives":                ["Limits and Continuity","Differentiability"],
    "Euler's Theorem on Homogeneous Functions": ["Partial Derivatives","Functions of Several Variables"],
    "Total Derivative":                   ["Partial Derivatives","Chain rule"],
    "Jacobians":                          ["Partial Derivatives","Determinants"],
    "Maxima and Minima of Two Variables": ["Partial Derivatives","Jacobians"],
    "Lagrange's Method of Multipliers":   ["Partial Derivatives","Maxima and Minima of Two Variables"],
    "Reduction Formulae":                 ["Integration techniques","Trigonometric identities"],
    "Beta and Gamma Functions":           ["Reduction Formulae","Improper Integrals"],
    "Double Integrals":                   ["Single variable integration","Limits and Continuity"],
    "Change of Order of Integration":     ["Double Integrals"],
    "Triple Integrals":                   ["Double Integrals"],
    "Improper Integrals":                 ["Single variable integration","Limits and Continuity"],
    "Convergence and Divergence":         ["Limits and Continuity","Sequences"],
    "Ratio Test (D'Alembert)":            ["Convergence and Divergence"],
    "Root Test (Cauchy)":                 ["Convergence and Divergence"],
    "Power Series and Radius of Convergence": ["Convergence and Divergence","Taylor's Theorem"],
    "Matrices and Types":                 ["Basic algebra"],
    "Rank of a Matrix":                   ["Matrices and Types","Echelon Form and Normal Form"],
    "System of Linear Equations":         ["Rank of a Matrix","Echelon Form and Normal Form"],
    "Eigenvalues and Eigenvectors":        ["Matrices and Types","Determinants","System of Linear Equations"],
    "Cayley-Hamilton Theorem":            ["Eigenvalues and Eigenvectors"],
    "Diagonalization":                    ["Eigenvalues and Eigenvectors","Cayley-Hamilton Theorem"],
    "Quadratic Forms":                    ["Eigenvalues and Eigenvectors","Diagonalization"],
    "Exact Differential Equations":       ["Variables Separable","Partial Derivatives"],
    "Integrating Factors":                ["Exact Differential Equations"],
    "Bernoulli's Equation":               ["Linear First Order ODEs"],
    "Complementary Function":             ["Linear ODEs with Constant Coefficients","Characteristic equation"],
    "Particular Integral":                ["Complementary Function"],
    "Variation of Parameters":            ["Complementary Function","Particular Integral"],
    "Euler-Cauchy Equation":              ["Linear ODEs with Constant Coefficients"],
    "Laplace Transforms of Standard Functions": ["Definition and Existence","Basic integration"],
    "Inverse Laplace Transform":          ["Laplace Transforms of Standard Functions","Partial Fractions Method"],
    "Convolution Theorem":                ["Inverse Laplace Transform"],
    "Solution of ODEs using Laplace":     ["Inverse Laplace Transform","Convolution Theorem"],
    "Unit Step and Dirac Delta Functions": ["Laplace Transforms of Standard Functions"],
    "Gradient and Directional Derivative": ["Partial Derivatives","Scalar and Vector Fields"],
    "Divergence and Curl":                ["Gradient and Directional Derivative"],
    "Line Integrals":                     ["Vector Calculus basics","Single variable integration"],
    "Surface Integrals":                  ["Line Integrals","Double Integrals"],
    "Green's Theorem in the Plane":       ["Line Integrals","Double Integrals"],
    "Stokes' Theorem":                    ["Surface Integrals","Divergence and Curl"],
    "Gauss Divergence Theorem":           ["Surface Integrals","Divergence and Curl"],
    "Analytic Functions":                 ["Complex Numbers Review","Limits in complex plane"],
    "Cauchy-Riemann Equations":           ["Analytic Functions","Partial Derivatives"],
    "Cauchy's Integral Theorem":          ["Complex Integration","Analytic Functions"],
    "Cauchy's Integral Formula":          ["Cauchy's Integral Theorem"],
    "Taylor and Laurent Series":          ["Cauchy's Integral Formula","Power Series"],
    "Residue Theorem":                    ["Taylor and Laurent Series","Singularities and Poles"],
    "Contour Integration":                ["Residue Theorem"],
    "Fourier Series of Even and Odd Functions": ["Euler's Formulae","Periodic Functions"],
    "Half-Range Sine and Cosine Series":  ["Fourier Series of Even and Odd Functions"],
    "Parseval's Identity":                ["Fourier Series of Even and Odd Functions"],
    "Binomial Distribution":              ["Random Variables","Probability Distributions"],
    "Poisson Distribution":               ["Binomial Distribution"],
    "Normal Distribution":                ["Probability Distributions","Expectation and Variance"],
    "Correlation and Regression":         ["Expectation and Variance","Joint Distributions"],
    "Hypothesis Testing":                 ["Normal Distribution","Sampling Theory"],
    "t-Test and F-Test":                  ["Hypothesis Testing","Normal Distribution"],
    "Newton-Raphson Method":              ["Bisection Method","Differentiability"],
    "Newton's Forward Interpolation":     ["Errors and Approximations","Finite differences"],
    "Newton's Backward Interpolation":    ["Newton's Forward Interpolation"],
    "Lagrange Interpolation":             ["Newton's Forward Interpolation"],
    "Simpson's 1/3 Rule":                 ["Trapezoidal Rule","Numerical Differentiation"],
    "Simpson's 3/8 Rule":                 ["Simpson's 1/3 Rule"],
    "Runge-Kutta Method (RK4)":           ["Euler's Method for ODEs","Taylor's Theorem"],
    "Fourier Transform":                  ["Fourier Integral Theorem","Fourier Series"],
    "Fourier Sine and Cosine Transforms": ["Fourier Transform"],
    "Convolution Theorem for Fourier":    ["Fourier Transform"],
    "Z-Transform Properties":            ["Z-Transform Definition"],
    "Inverse Z-Transform":               ["Z-Transform Properties","Partial Fractions Method"],
    "Solution of Difference Equations":  ["Inverse Z-Transform"],
}

# ══════════════════════════════════════════════════════════════
#  SUBTOPIC GUIDANCE — tells AI exactly what to cover per subtopic
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
#  REFERENCES
# ══════════════════════════════════════════════════════════════
REFERENCES = {
    "diff_calc":        ["https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/","https://www.khanacademy.org/math/calculus-1","https://tutorial.math.lamar.edu/Classes/CalcI/CalcI.aspx","https://mathworld.wolfram.com/Calculus.html"],
    "partial_diff":     ["https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/","https://www.khanacademy.org/math/multivariable-calculus","https://tutorial.math.lamar.edu/Classes/CalcIII/CalcIII.aspx","https://mathworld.wolfram.com/PartialDerivative.html"],
    "integral_calc":    ["https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/","https://www.khanacademy.org/math/integral-calculus","https://tutorial.math.lamar.edu/Classes/CalcII/CalcII.aspx","https://mathworld.wolfram.com/Integral.html"],
    "infinite_series":  ["https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/","https://www.khanacademy.org/math/ap-calculus-bc/bc-series-new","https://tutorial.math.lamar.edu/Classes/CalcII/SeriesIntro.aspx","https://mathworld.wolfram.com/Series.html"],
    "linear_algebra":   ["https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/","https://www.khanacademy.org/math/linear-algebra","https://www.3blue1brown.com/topics/linear-algebra","https://mathworld.wolfram.com/LinearAlgebra.html"],
    "ode_first":        ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","https://www.khanacademy.org/math/differential-equations","https://tutorial.math.lamar.edu/Classes/DE/DE.aspx","https://mathworld.wolfram.com/OrdinaryDifferentialEquation.html"],
    "ode_higher":       ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","https://tutorial.math.lamar.edu/Classes/DE/SecondOrderConcepts.aspx","https://www.khanacademy.org/math/differential-equations","https://mathworld.wolfram.com/SecondOrderOrdinaryDifferentialEquation.html"],
    "laplace":          ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","https://tutorial.math.lamar.edu/Classes/DE/LaplaceIntro.aspx","https://www.khanacademy.org/math/differential-equations/laplace-transform","https://mathworld.wolfram.com/LaplaceTransform.html"],
    "vector_calc":      ["https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/","https://www.khanacademy.org/math/multivariable-calculus","https://tutorial.math.lamar.edu/Classes/CalcIII/VectorFields.aspx","https://mathworld.wolfram.com/VectorCalculus.html"],
    "complex_analysis": ["https://ocw.mit.edu/courses/18-04-complex-variables-with-applications-spring-2018/","https://mathworld.wolfram.com/ComplexAnalysis.html","https://www.youtube.com/playlist?list=PLBh2i93oe2qvRGAtgkTszX7szZDVd6jh1","https://nptel.ac.in/courses/111/106/111106084/"],
    "fourier_series":   ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","https://www.khanacademy.org/science/electrical-engineering/ee-signals","https://mathworld.wolfram.com/FourierSeries.html","https://nptel.ac.in/courses/111/104/111104092/"],
    "probability":      ["https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/","https://www.khanacademy.org/math/statistics-probability","https://www.probabilitycourse.com/","https://mathworld.wolfram.com/Probability.html"],
    "numerical":        ["https://ocw.mit.edu/courses/18-330-introduction-to-numerical-analysis-spring-2012/","https://nptel.ac.in/courses/111/107/111107105/","https://mathworld.wolfram.com/NumericalAnalysis.html","https://tutorial.math.lamar.edu/Extras/AlgebraTrigReview/AlgebraTrigReview.aspx"],
    "transforms":       ["https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/","https://www.khanacademy.org/science/electrical-engineering/ee-signals","https://mathworld.wolfram.com/FourierTransform.html","https://nptel.ac.in/courses/111/104/111104090/"]
}

# ══════════════════════════════════════════════════════════════
#  SUBJECT CONNECTIONS MAP
# ══════════════════════════════════════════════════════════════
SUBJECT_CONNECTIONS = {
    "diff_calc": {"connections": [
        {"subject": "Engineering Mechanics", "semester": "Sem 1-2", "how": "Velocity and acceleration as derivatives of displacement. Newton's second law in differential form.", "example": "Finding maximum range of a projectile using $dR/d\\theta = 0$"},
        {"subject": "Thermodynamics", "semester": "Sem 2-3", "how": "Rate of change of temperature, pressure, and entropy. Partial derivatives for thermodynamic potentials.", "example": "Joule-Thomson coefficient $\\mu_{JT} = (\\partial T/\\partial P)_H$"},
        {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "Instantaneous current as derivative of charge. Voltage across inductor.", "example": "Transient analysis: finding $di/dt$ at $t=0^+$ when switch closes"},
        {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Velocity gradient, strain rate, and viscosity. Bernoulli equation derivation.", "example": "Shear stress $\\tau = \\mu\\,du/dy$ in viscous flow"},
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": "Transfer function derivation. Sensitivity analysis using derivatives.", "example": "Gain margin and phase margin calculations"}
    ]},
    "partial_diff": {"connections": [
        {"subject": "Heat Transfer", "semester": "Sem 3-4", "how": "Heat equation with partial derivatives in temperature.", "example": "Steady-state temperature in a 2D plate"},
        {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Continuity equation, Navier-Stokes equations are PDEs.", "example": "Incompressibility $\\partial u/\\partial x + \\partial v/\\partial y = 0$"},
        {"subject": "Electromagnetics", "semester": "Sem 3-4", "how": "Maxwell equations are PDEs in fields.", "example": "Wave equation $\\nabla^2 E = \\mu\\epsilon\\,\\partial^2 E/\\partial t^2$"},
        {"subject": "Thermodynamics", "semester": "Sem 2-3", "how": "Maxwell relations use mixed partial derivatives.", "example": "$(\\partial S/\\partial V)_T = (\\partial P/\\partial T)_V$"},
        {"subject": "Structural Analysis", "semester": "Sem 3-4", "how": "Beam and plate bending equations involve higher partial derivatives.", "example": "Plate bending: $\\partial^4 w/\\partial x^4 = q/D$"}
    ]},
    "integral_calc": {"connections": [
        {"subject": "Engineering Mechanics", "semester": "Sem 1-2", "how": "Centre of mass, moment of inertia, work done by variable force.", "example": "Moment of inertia $I = \\int r^2\\,dm$"},
        {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "Energy stored, RMS value of AC signals.", "example": "Charge $q = \\int_0^T i(t)\\,dt$"},
        {"subject": "Signals and Systems", "semester": "Sem 3-4", "how": "Convolution integral, energy and power of signals.", "example": "Output $y(t) = \\int x(\\tau)h(t-\\tau)\\,d\\tau$"},
        {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Flow rate, pressure force, buoyancy.", "example": "Volume flow rate $Q = \\iint \\vec{v}\\cdot d\\vec{A}$"},
        {"subject": "Heat Transfer", "semester": "Sem 3-4", "how": "Total heat transfer by integrating heat equation.", "example": "Total heat $Q = \\int_0^L kA\\,(dT/dx)\\,dx$"}
    ]},
    "infinite_series": {"connections": [
        {"subject": "Signals and Systems", "semester": "Sem 3-4", "how": "Fourier series expresses periodic signals as infinite series.", "example": "Square wave: $\\sum (1/n)\\sin(n\\omega_0 t)$"},
        {"subject": "Numerical Methods", "semester": "Sem 4", "how": "Taylor series is basis of every numerical approximation.", "example": "Newton-Raphson uses $f(x+h) \\approx f(x) + hf'(x)$"},
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": "Bode plot approximations and stability use series.", "example": "Gain approximation near corner frequency"},
        {"subject": "Digital Communications", "semester": "Sem 5-6", "how": "Shannon entropy as series, channel capacity.", "example": "$H = -\\sum p_i\\log p_i$"}
    ]},
    "linear_algebra": {"connections": [
        {"subject": "Structural Analysis", "semester": "Sem 3-4", "how": "Stiffness matrix method: entire analysis is $[K]\\{u\\} = \\{F\\}$.", "example": "Truss analysis: 20 unknown forces solved by matrix methods"},
        {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "Mesh and node analysis give systems of linear equations.", "example": "KVL gives $[Z][I] = [V]$ solved by matrix inverse"},
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": "State-space $\\dot{x} = Ax + Bu$. Eigenvalues determine stability.", "example": "System stable iff all eigenvalues of $A$ have negative real parts"},
        {"subject": "Machine Learning", "semester": "Sem 6+", "how": "Linear regression, PCA, neural networks built on linear algebra.", "example": "Principal components are eigenvectors of covariance matrix"},
        {"subject": "Image Processing", "semester": "Sem 5-6", "how": "Transformations, filtering, compression using matrix operations.", "example": "SVD compression: $A = U\\Sigma V^T$"}
    ]},
    "ode_first": {"connections": [
        {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "RC and RL circuits give first-order ODEs.", "example": "RC circuit: $R\\,dq/dt + q/C = V(t)$"},
        {"subject": "Engineering Mechanics", "semester": "Sem 1-2", "how": "Newton second law with variable force.", "example": "Projectile with drag: $m\\,dv/dt = mg - kv$"},
        {"subject": "Chemical Engineering", "semester": "Sem 3-4", "how": "Reaction kinetics, mixing problems.", "example": "First-order reaction: $dC/dt = -kC$"},
        {"subject": "Biomedical Engineering", "semester": "Sem 4+", "how": "Drug concentration, population models.", "example": "Drug decay: $dC/dt = -\\lambda C$"}
    ]},
    "ode_higher": {"connections": [
        {"subject": "Electrical Circuits", "semester": "Sem 2-3", "how": "RLC circuits give second-order ODEs.", "example": "Series RLC: $L\\,d^2q/dt^2 + R\\,dq/dt + q/C = V(t)$"},
        {"subject": "Mechanical Vibrations", "semester": "Sem 3-4", "how": "Every vibrating system is a second-order ODE.", "example": "Mass-spring-damper: $m\\ddot{x} + c\\dot{x} + kx = F(t)$"},
        {"subject": "Structural Analysis", "semester": "Sem 3-4", "how": "Beam deflection is a fourth-order ODE.", "example": "Euler-Bernoulli: $EI\\,d^4y/dx^4 = w(x)$"},
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": "Second-order system response: overshoot, settling time.", "example": "$\\ddot{y} + 2\\zeta\\omega_n\\dot{y} + \\omega_n^2 y = \\omega_n^2 u$"}
    ]},
    "laplace": {"connections": [
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": "Transfer function $G(s) = Y(s)/U(s)$. Entire design in s-domain.", "example": "PID controller: $C(s) = K_p + K_i/s + K_d s$"},
        {"subject": "Electrical Circuits", "semester": "Sem 3", "how": "Impedance in s-domain makes circuit analysis algebraic.", "example": "Voltage divider in s-domain: no differential equations"},
        {"subject": "Signals and Systems", "semester": "Sem 3-4", "how": "System analysis using poles and zeros.", "example": "Stable iff all poles in left half s-plane"},
        {"subject": "Digital Signal Processing", "semester": "Sem 5", "how": "Z-transform is discrete-time equivalent.", "example": "Relationship $z = e^{sT}$"},
        {"subject": "Communications", "semester": "Sem 4-5", "how": "Modulation, filtering, channel analysis.", "example": "Bandwidth of AM signal from Laplace transform"}
    ]},
    "vector_calc": {"connections": [
        {"subject": "Electromagnetics", "semester": "Sem 3-4", "how": "Maxwell equations in vector calculus form.", "example": "Gauss law: $\\nabla\\cdot\\vec{E} = \\rho/\\epsilon_0$"},
        {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Velocity field, vorticity, continuity equation.", "example": "Irrotational: $\\nabla\\times\\vec{v} = 0$"},
        {"subject": "Heat Transfer", "semester": "Sem 3-4", "how": "Heat flux vector, Fourier law.", "example": "$\\vec{q} = -k\\nabla T$"},
        {"subject": "Structural Mechanics", "semester": "Sem 3-4", "how": "Stress tensors, displacement fields.", "example": "Strain energy $U = \\iiint \\sigma_{ij}\\epsilon_{ij}\\,dV$"}
    ]},
    "complex_analysis": {"connections": [
        {"subject": "Electrical Circuits", "semester": "Sem 2-3", "how": "Phasors are complex numbers. Impedance $Z = R + jX$.", "example": "AC analysis: $V = IZ$ with complex quantities"},
        {"subject": "Control Systems", "semester": "Sem 4-5", "how": "Nyquist plot, root locus in complex s-plane.", "example": "Nyquist stability uses contour integration"},
        {"subject": "Signals and Systems", "semester": "Sem 3-4", "how": "Frequency response $H(j\\omega)$ is complex.", "example": "Bode plot: magnitude $|H(j\\omega)|$ and phase"},
        {"subject": "Electromagnetics", "semester": "Sem 3-4", "how": "Complex permittivity, wave propagation.", "example": "Skin depth from imaginary part of propagation constant"}
    ]},
    "fourier_series": {"connections": [
        {"subject": "Signals and Systems", "semester": "Sem 3-4", "how": "Every periodic signal is a Fourier series.", "example": "Square wave: $\\sum_{n=odd} (4/n\\pi)\\sin(n\\omega_0 t)$"},
        {"subject": "Communications", "semester": "Sem 4-5", "how": "Modulation analysis, channel bandwidth.", "example": "AM signal spectrum analysis"},
        {"subject": "Digital Signal Processing", "semester": "Sem 5", "how": "DFT and FFT are discrete Fourier series.", "example": "FFT: $O(N\\log N)$ vs $O(N^2)$"},
        {"subject": "Mechanical Vibrations", "semester": "Sem 3-4", "how": "Periodic forcing expanded as Fourier series.", "example": "Engine vibration at harmonics of rotation frequency"}
    ]},
    "probability": {"connections": [
        {"subject": "Communications", "semester": "Sem 4-5", "how": "Bit error rate, noise analysis, channel capacity.", "example": "BER for BPSK: $P_e = Q(\\sqrt{2E_b/N_0})$"},
        {"subject": "Reliability Engineering", "semester": "Sem 5-6", "how": "Failure probability, MTTF, reliability function.", "example": "Exponential failure: $R(t) = e^{-\\lambda t}$"},
        {"subject": "Control Systems", "semester": "Sem 5", "how": "Stochastic control, Kalman filter.", "example": "Kalman gain minimises mean square error"},
        {"subject": "Machine Learning", "semester": "Sem 6+", "how": "Bayesian inference, probabilistic models.", "example": "Bayes classifier: $P(C|x) \\propto P(x|C)P(C)$"},
        {"subject": "Quality Control", "semester": "Sem 5-6", "how": "Statistical process control, Six Sigma.", "example": "Control limits at $\\mu \\pm 3\\sigma$"}
    ]},
    "numerical": {"connections": [
        {"subject": "Computer Science", "semester": "Sem 2+", "how": "Every numerical method implemented as algorithm.", "example": "scipy.integrate.odeint implements RK4"},
        {"subject": "Structural Analysis", "semester": "Sem 3-4", "how": "Finite Element Method uses numerical integration.", "example": "FEM stiffness matrix assembled by numerical integration"},
        {"subject": "Fluid Mechanics", "semester": "Sem 4-5", "how": "CFD solves Navier-Stokes numerically.", "example": "Finite difference: $\\partial u/\\partial t + u\\,\\partial u/\\partial x = 0$"},
        {"subject": "Heat Transfer", "semester": "Sem 4", "how": "Numerical solution when analytical impossible.", "example": "Crank-Nicolson scheme for transient conduction"}
    ]},
    "transforms": {"connections": [
        {"subject": "Digital Signal Processing", "semester": "Sem 5", "how": "Z-transform fundamental to DSP. Filter design.", "example": "Digital filter $H(z) = Y(z)/X(z)$ — poles inside unit circle"},
        {"subject": "Communications", "semester": "Sem 4-5", "how": "Fourier transform gives frequency spectrum.", "example": "Bandwidth of sinc pulse $= 1/T$ Hz"},
        {"subject": "Control Systems", "semester": "Sem 5", "how": "Discrete-time control uses Z-transform.", "example": "Digital PID designed in z-domain"},
        {"subject": "Image Processing", "semester": "Sem 5-6", "how": "2D Fourier transform for filtering, compression.", "example": "JPEG uses Discrete Cosine Transform"}
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
- Never use markdown: no **, *, #, __ ever
- College exam level only — semester exam standard, not competitive
- Include at least 2 fully worked numerical examples per response
- Every theorem must state: Name, Statement, Conditions, Proof sketch
"""

ENG_CONTEXT = """You are MathSphere Engineering by Anupam Nigam.
You are teaching B.Tech engineering students in India (IIT/NIT/Mumbai University/VTU/Anna University level).
Difficulty: College examination level — semester exam standard only.
Style: Clear, precise, like a brilliant IIT professor explaining to first/second year students.
Always use engineering applications and examples where possible.
"""

# ══════════════════════════════════════════════════════════════
#  PROMPT BUILDERS
# ══════════════════════════════════════════════════════════════
def get_subtopic_guidance(subtopic):
    return SUBTOPIC_GUIDANCE.get(subtopic, "")

def build_learn_prompt(topic_key, subtopic, section):
    guidance = get_subtopic_guidance(subtopic)
    guidance_block = f"\nSPECIFIC GUIDANCE FOR THIS SUBTOPIC:\n{guidance}\n" if guidance else ""

    sections = {
        "definition": f"""Give the complete formal definition of {subtopic} for engineering mathematics.
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
""",
        "practice": f"""Generate 8 practice problems on {subtopic} in university examination style.
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

""",
        "intuition": f"""You are explaining {subtopic} to a B.Tech engineering student who is confused
and wants to understand what is actually happening — not just formulas.

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

    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Generate a complete Quick Revision sheet for {subtopic}.
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

For EACH question use this EXACT structure:

QUESTION [N]: [Exam Name] · [University] · [Approximate Year] · [[marks] Marks]

STATUS: CONFIRMED / REPRESENTATIVE
(CONFIRMED = you are certain it appeared. REPRESENTATIVE = typical exam-level question.)

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
[Step 3 — [description]: [N] mark(s)]
[... continue until total marks accounted for]

FINAL ANSWER:

$$
[answer]
$$


VERIFICATION:
[Show the check explicitly]

COMMON MISTAKE ON THIS PROBLEM:
[The specific error students most often make on this exact type]

EXAM STRATEGY:
[One sentence: how to approach this type quickly under exam pressure]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After all 5 questions add:

TOPIC ANALYSIS:
[How frequently this appears, which sub-types are most common, trend across years]

PREPARATION STRATEGY:
- [Most important concept to master for this topic]
- [Most common question type to practice]
- [One thing that separates 8/10 from 10/10 on this topic]

OFFICIAL SOURCES:
Mumbai University: https://mu.ac.in
VTU: https://vtu.ac.in
Anna University: https://www.annauniv.edu
AKTU: https://aktu.ac.in

Note: Always cross-verify questions with official university question papers.
"""


def build_mocktest_prompt(topic_key, subtopic, num_q, marks_each):
    total = int(num_q) * int(marks_each)
    time_min = int(num_q) * int(marks_each) * 2
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
Instructions: Attempt ALL questions. Show complete working. Each step must be clearly presented.

For EACH question:

QUESTION [N]: ({marks_each} Marks)
[Question with all equations as 
$$
...
$$
]

Difficulty distribution: 40% straightforward, 40% multi-step, 20% proof or derivation.
Question types: mix direct formula application, proof-based, application to engineering context.

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
[{total*8//10}+ marks: Excellent — ready for exam]
[{total*6//10}-{total*8//10-1} marks: Good — review weak areas]
[{total*4//10}-{total*6//10-1} marks: Fair — needs more practice]
[Below {total*4//10} marks: Revise fundamentals first]

KEY CONCEPTS TESTED:
[List the specific subtopics and theorems covered in this paper]
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
[One sentence: what this formula computes in engineering terms. Name the physical quantity and its units.]

WHEN TO USE:
[Specific conditions under which this formula applies]

DO NOT USE WHEN:
[Common mistake — when students incorrectly apply this formula]

QUICK EXAMPLE:
[One specific numerical example: given values → substitution → answer in 3-4 lines]

After all formulas add:

STANDARD RESULTS TABLE:
[All key results together — each as 
$$
...
$$
]

DERIVATION CONNECTIONS:
[How these formulas relate to each other]

ENGINEERING SUBJECTS USING THIS:
[List subjects with one specific use-case each]

EXAM QUICK REFERENCE:
- Most frequently asked: [formula name]
- Most commonly forgotten: [what students forget]
- Most commonly misapplied: [the typical error]

Generate minimum 8 formulas. Be complete — this is a reference document.
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
End with CONFIDENCE: HIGH / MEDIUM / LOW
"""


# ══════════════════════════════════════════════════════════════
#  NEW FEATURE: STEP-BY-STEP SOLVER
#  Students paste a problem, get detailed solution
# ══════════════════════════════════════════════════════════════
def build_solve_prompt(problem, topic_key=""):
    guidance = ""
    if topic_key:
        guidance = f"\nThis problem is from the topic area: {topic_key}\n"

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
"""


# ══════════════════════════════════════════════════════════════
#  NEW FEATURE: COMPARE METHODS
#  When multiple methods exist, show all with comparison
# ══════════════════════════════════════════════════════════════
def build_compare_prompt(subtopic1, subtopic2, topic_key=""):
    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Compare and contrast these two mathematical methods/concepts for engineering students:

METHOD A: {subtopic1}
METHOD B: {subtopic2}

Use this EXACT structure:

METHOD A — {subtopic1.upper()}:
[2-3 sentence description]
[Key formula as 
$$
...
$$
]
[When to use: specific conditions]

METHOD B — {subtopic2.upper()}:
[2-3 sentence description]
[Key formula as 
$$
...
$$
]
[When to use: specific conditions]

HEAD-TO-HEAD COMPARISON:

FEATURE                  | METHOD A              | METHOD B
Accuracy                 | [comparison]          | [comparison]
Speed in exam            | [comparison]          | [comparison]
Ease of application      | [comparison]          | [comparison]
When it fails            | [specific condition]  | [specific condition]
Exam frequency           | [how often asked]     | [how often asked]
Typical marks            | [marks range]         | [marks range]

SAME PROBLEM, BOTH METHODS:
[Choose one specific numerical problem and solve it using BOTH methods side by side]

Problem:

$$
[problem statement]
$$


Solution by Method A:
[Complete step-by-step]

Solution by Method B:
[Complete step-by-step]

WHICH TO USE WHEN:
[Decision flowchart in words — if [condition] then use Method A, if [condition] then use Method B]

EXAM STRATEGY:
[Which method to default to under time pressure and why]

ENGINEERING CONTEXT:
[Where each method appears in engineering subjects]
"""


# ══════════════════════════════════════════════════════════════
#  NEW FEATURE: EXAM STRATEGY GENERATOR
#  Topic-wise exam preparation plan
# ══════════════════════════════════════════════════════════════
def build_exam_strategy_prompt(topic_key, hours_available):
    topic_label = ""
    for sem_data in SYLLABUS.values():
        for tk, td in sem_data["topics"].items():
            if tk == topic_key:
                topic_label = td["label"]
                break

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
[List 3-5 question types that appear almost every year with the exact approach]

QUICK WINS (easy marks with minimal preparation):
[3-4 subtopics where memorising one formula gives guaranteed marks]

DANGER ZONES (where students commonly lose marks):
[3-4 specific mistakes to avoid]

FORMULA SHEET TO MEMORISE:
[The 10-15 most critical formulas for this topic — each as 
$$
...
$$
]

LAST-MINUTE CHECKLIST:
- [ ] [Item 1 to verify before entering exam hall]
- [ ] [Item 2]
- [ ] [Item 3]
- [ ] [Item 4]
- [ ] [Item 5]

EXAM HALL STRATEGY:
- Time per mark: [recommendation]
- Which question to attempt first: [advice]
- How to present for maximum marks: [specific tips]
"""


# ══════════════════════════════════════════════════════════════
#  NEW FEATURE: DOUBT SOLVER WITH CONTEXT
#  Student describes confusion, AI diagnoses and explains
# ══════════════════════════════════════════════════════════════
def build_doubt_prompt(doubt, topic_key="", subtopic=""):
    context = ""
    if topic_key:
        context += f"Topic area: {topic_key}\n"
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
[Identify the precise point of confusion — not the whole topic, the EXACT misunderstanding]

THE SOURCE OF CONFUSION:
[Why this is confusing — what two things is the student mixing up, or what step are they missing?]

THE CLEAR EXPLANATION:
[Explain the correct understanding step by step. Use simple language first, then formal mathematics.]
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
[One analogy from engineering or daily life that captures the essence]

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


CONFIDENCE THAT I ADDRESSED YOUR DOUBT: HIGH / MEDIUM / LOW
[If MEDIUM or LOW, suggest what additional information would help]
"""


# ══════════════════════════════════════════════════════════════
#  NEW FEATURE: TOPIC ROADMAP
#  Visual learning path for a complete topic
# ══════════════════════════════════════════════════════════════
def build_roadmap(topic_key):
    """Generate a structured learning roadmap — no AI call needed"""
    for sem_key, sem_data in SYLLABUS.items():
        if topic_key in sem_data["topics"]:
            topic_data = sem_data["topics"][topic_key]
            subtopics = topic_data["subtopics"]
            total = len(subtopics)

            # Build phases
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
                    "phase":       i + 1,
                    "name":        name,
                    "description": desc,
                    "subtopics":   phase_subtopics,
                    "estimated_hours": max(1, len(phase_subtopics) * 2)
                })

            # Collect prerequisites for this topic
            topic_prereqs = {}
            for st in subtopics:
                for key, val in PREREQUISITES.items():
                    if key.lower() in st.lower() or st.lower() in key.lower():
                        topic_prereqs[key] = val

            return {
                "topic":          topic_data["label"],
                "total_subtopics": total,
                "estimated_hours": total * 2,
                "phases":         phases,
                "prerequisites":  topic_prereqs,
                "references":     REFERENCES.get(topic_key, [])
            }

    return None


# ══════════════════════════════════════════════════════════════
#  NEW FEATURE: STUDY PROGRESS TRACKER
#  Tracks what students have studied (in-memory, per session)
# ══════════════════════════════════════════════════════════════
_student_progress = {}

def get_progress(student_id):
    if student_id not in _student_progress:
        _student_progress[student_id] = {
            "completed_subtopics":  [],
            "weak_areas":           [],
            "strong_areas":         [],
            "misconceptions_found": [],
            "mock_tests_taken":     0,
            "total_study_time":     0,
            "last_active":          None
        }
    return _student_progress[student_id]

def update_progress(student_id, action, data):
    progress = get_progress(student_id)
    progress["last_active"] = time.strftime("%Y-%m-%d %H:%M:%S")

    if action == "complete_subtopic":
        subtopic = data.get("subtopic", "")
        if subtopic and subtopic not in progress["completed_subtopics"]:
            progress["completed_subtopics"].append(subtopic)

    elif action == "mark_weak":
        subtopic = data.get("subtopic", "")
        if subtopic and subtopic not in progress["weak_areas"]:
            progress["weak_areas"].append(subtopic)
        if subtopic in progress["strong_areas"]:
            progress["strong_areas"].remove(subtopic)

    elif action == "mark_strong":
        subtopic = data.get("subtopic", "")
        if subtopic and subtopic not in progress["strong_areas"]:
            progress["strong_areas"].append(subtopic)
        if subtopic in progress["weak_areas"]:
            progress["weak_areas"].remove(subtopic)

    elif action == "misconception_found":
        misconception_id = data.get("misconception_id", "")
        if misconception_id and misconception_id not in progress["misconceptions_found"]:
            progress["misconceptions_found"].append(misconception_id)

    elif action == "mock_test":
        progress["mock_tests_taken"] += 1

    elif action == "study_time":
        minutes = data.get("minutes", 0)
        progress["total_study_time"] += minutes

    return progress


# ══════════════════════════════════════════════════════════════
#  API HELPERS — with caching and proper error handling
# ══════════════════════════════════════════════════════════════
def call_groq(prompt, system=""):
    if not groq_client:
        raise RuntimeError("Groq API key not configured")
    truncated_system = system[:4000] if len(system) > 4000 else system
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

def call_gemini(prompt, model_name):
    if not gemini_client:
        raise RuntimeError("Gemini API key not configured")
    resp = gemini_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config={"temperature": 0.1}
    )
    return resp.text

def get_eng_response(full_prompt):
    # Check cache first
    cached_resp, cached_source = get_cached(full_prompt)
    if cached_resp:
        return cached_resp, cached_source

    system_msg = ENG_CONTEXT + "\n" + ENG_FORMAT

    # Try Groq first
    try:
        response = call_groq(full_prompt, system=system_msg)
        set_cache(full_prompt, response, "Groq")
        return response, "Groq"
    except Exception as e:
        print(f"[Eng] Groq failed: {e}")

    # Cascade through Gemini models
    for model_name, label in GEMINI_CASCADE:
        try:
            response = call_gemini(full_prompt, model_name)
            set_cache(full_prompt, response, label)
            return response, label
        except Exception as e:
            print(f"[Eng] {model_name} failed: {e}")
            time.sleep(0.2)

    return "Service temporarily unavailable. Please try again.", "None"


# ══════════════════════════════════════════════════════════════
#  INPUT VALIDATION HELPER
# ══════════════════════════════════════════════════════════════
def validate_json(*required_fields):
    """Validate request has JSON body and required fields"""
    data = request.get_json(force=True, silent=True)
    if not data:
        return None, jsonify({"error": "Request body must be valid JSON"}), 400
    missing = [f for f in required_fields if not data.get(f, "").strip()]
    if missing:
        return None, jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    return data, None, None


# ══════════════════════════════════════════════════════════════
#  ROUTES — Original (with validation added)
# ══════════════════════════════════════════════════════════════
@eng_bp.route("/eng/syllabus")
def get_syllabus():
    return jsonify(SYLLABUS)

@eng_bp.route("/eng/learn", methods=["POST"])
def learn():
    try:
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic    = data.get("topic", "")
        subtopic = data.get("subtopic", "")
        section  = data.get("section", "definition")
        prereqs  = PREREQUISITES.get(subtopic, [])
        prompt   = build_learn_prompt(topic, subtopic, section)
        response, source = get_eng_response(prompt)
        return jsonify({
            "response":      response,
            "source":        source,
            "references":    REFERENCES.get(topic, []),
            "prerequisites": prereqs
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/revision", methods=["POST"])
def revision():
    try:
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic    = data.get("topic", "")
        subtopic = data.get("subtopic", "")
        prompt   = build_revision_prompt(topic, subtopic)
        response, source = get_eng_response(prompt)
        return jsonify({"response": response, "source": source, "references": REFERENCES.get(topic, [])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/pyq", methods=["POST"])
def pyq():
    try:
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic      = data.get("topic", "")
        subtopic   = data.get("subtopic", "")
        university = data.get("university", "all")
        difficulty = data.get("difficulty", "medium")
        prompt     = build_pyq_prompt(topic, subtopic, university, difficulty)
        response, source = get_eng_response(prompt)
        return jsonify({"response": response, "source": source, "references": REFERENCES.get(topic, [])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/mocktest", methods=["POST"])
def mocktest():
    try:
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic      = data.get("topic", "")
        subtopic   = data.get("subtopic", "")
        num_q      = data.get("num_questions", "5")
        marks_each = data.get("marks_each", "5")
        prompt     = build_mocktest_prompt(topic, subtopic, num_q, marks_each)
        response, source = get_eng_response(prompt)
        return jsonify({"response": response, "source": source})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/formulabooklet", methods=["POST"])
def formula_booklet():
    try:
        data, err, code = validate_json("subtopic")
        if err:
            return err, code
        topic    = data.get("topic", "")
        subtopic = data.get("subtopic", "")
        prompt   = build_formula_booklet_prompt(topic, subtopic)
        response, source = get_eng_response(prompt)
        return jsonify({"response": response, "source": source, "references": REFERENCES.get(topic, [])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/connections", methods=["POST"])
def connections():
    try:
        data, err, code = validate_json("topic")
        if err:
            return err, code
        topic    = data.get("topic", "")
        subtopic = data.get("subtopic", "")
        topic_connections = SUBJECT_CONNECTIONS.get(topic)
        if topic_connections:
            return jsonify({
                "connections": topic_connections["connections"],
                "source":     "MathSphere Engineering",
                "references": REFERENCES.get(topic, []),
                "type":       "structured"
            })
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
"""
        response, source = get_eng_response(prompt)
        return jsonify({
            "response":   response,
            "source":     source,
            "references": REFERENCES.get(topic, []),
            "type":       "generated"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/ask", methods=["POST"])
def ask_eng():
    try:
        data, err, code = validate_json("question")
        if err:
            return err, code
        question = data.get("question", "")
        prompt   = build_ask_prompt(question)
        response, source = get_eng_response(prompt)
        return jsonify({"response": response, "source": source})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  MISCONCEPTION DATABASE — COMPLETE
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
            "question": "Can you apply L'Hopital's Rule to find lim(x→2) (x²-4)/(x-2)? What must you check first?",
            "correct": "L'Hopital's Rule applies ONLY when the limit gives an indeterminate form 0/0 or ∞/∞. The limit (x²-4)/(x-2) at x=2 gives 0/0 — so L'Hopital applies. But you must ALWAYS verify the indeterminate form first. Applying it to non-indeterminate forms gives wrong answers.",
            "why_students_believe_it": "Students see L'Hopital as a shortcut and apply it without checking conditions."
        },
        {
            "id": "DC03",
            "misconception": "A function can have at most one tangent line at any point",
            "danger": "MEDIUM",
            "question": "If f'(c) = 0 at some point c, what does the tangent line look like? Does the function have to have a maximum or minimum at c?",
            "correct": "f'(c) = 0 means a horizontal tangent — but this could be a maximum, minimum, OR a point of inflection (like f(x)=x³ at x=0). Students must check the second derivative or sign change of f' to classify critical points.",
            "why_students_believe_it": "Students memorise 'set derivative to zero to find maxima/minima' without understanding that f'(c)=0 is necessary but not sufficient."
        },
        {
            "id": "DC04",
            "misconception": "Taylor series always converges to the function",
            "danger": "HIGH",
            "question": "If I write the Taylor series of f(x) around x=0 and sum infinitely many terms, do I always get f(x)?",
            "correct": "No. A function must be analytic for its Taylor series to converge to it. The Taylor series may converge to a different function or diverge entirely outside the radius of convergence. Always state the interval of convergence.",
            "why_students_believe_it": "Students work only with standard functions (sin, cos, e^x) whose Taylor series converge everywhere, never seeing a counterexample."
        },
        {
            "id": "DC05",
            "misconception": "The derivative of a product is the product of derivatives",
            "danger": "CRITICAL",
            "question": "What is the derivative of f(x) = x² · sin(x)? Write your first instinct, then verify.",
            "correct": "d/dx(uv) = u·(dv/dx) + v·(du/dx). NOT d/dx(uv) = (du/dx)·(dv/dx). This is the product rule. The correct answer is x²·cos(x) + 2x·sin(x). Students who believe the misconception write 2x·cos(x) and lose full marks.",
            "why_students_believe_it": "Analogy with exponent rules: (uv)^n = u^n·v^n. Students incorrectly extend this pattern to derivatives."
        }
    ],
    "partial_diff": [
        {
            "id": "PD01",
            "misconception": "Mixed partial derivatives are always equal",
            "danger": "MEDIUM",
            "question": "Is it always true that ∂²f/∂x∂y = ∂²f/∂y∂x for any function f(x,y)?",
            "correct": "Clairaut's theorem states mixed partials are equal ONLY if both mixed partials are continuous in a neighbourhood of the point. This condition is satisfied for most functions in engineering, but it is NOT universally true. Students must state the continuity condition in exams.",
            "why_students_believe_it": "Clairaut's theorem is taught without emphasis on its conditions."
        },
        {
            "id": "PD02",
            "misconception": "If both partial derivatives exist, the function is differentiable",
            "danger": "HIGH",
            "question": "If ∂f/∂x and ∂f/∂y both exist at a point, does that guarantee f is differentiable there?",
            "correct": "No. Existence of partial derivatives does NOT imply differentiability. A function can have both partial derivatives existing at a point while being discontinuous there. Differentiability requires the partial derivatives to be continuous.",
            "why_students_believe_it": "Single-variable analogy: if f'(x) exists, f is differentiable. This does not extend to multiple variables."
        },
        {
            "id": "PD03",
            "misconception": "Euler's theorem applies to all functions of two variables",
            "danger": "HIGH",
            "question": "Can you apply Euler's theorem to f(x,y) = x² + y² + 1? Why or why not?",
            "correct": "Euler's theorem x·∂f/∂x + y·∂f/∂y = n·f applies ONLY to homogeneous functions of degree n. f(x,y) = x²+y²+1 is NOT homogeneous because of the constant term. Always verify homogeneity first.",
            "why_students_believe_it": "Students apply Euler's theorem mechanically without checking the homogeneity condition."
        }
    ],
    "integral_calc": [
        {
            "id": "IC01",
            "misconception": "If the integral of f from a to b is zero, then f must be zero",
            "danger": "HIGH",
            "question": "If ∫₀^π sin(x) dx = 0... wait, does it? Calculate it. What does a zero integral actually mean geometrically?",
            "correct": "∫₀^π sin(x) dx = 2, not zero. But ∫₀^{2π} sin(x) dx = 0 even though sin(x) is never identically zero. A zero integral means the positive and negative areas cancel — not that the function is zero.",
            "why_students_believe_it": "Students think of integration as measuring 'total function value' rather than signed area."
        },
        {
            "id": "IC02",
            "misconception": "Integration and differentiation always undo each other perfectly",
            "danger": "MEDIUM",
            "question": "If F(x) = ∫₀ˣ f(t)dt, is it always true that F'(x) = f(x)?",
            "correct": "Yes — but only when f is continuous. The Fundamental Theorem of Calculus requires continuity of f. Also: d/dx[∫f(x)dx] = f(x) but ∫[d/dx f(x)]dx = f(x) + C. The constant of integration is critical.",
            "why_students_believe_it": "The relationship is taught as absolute without stating continuity requirements."
        },
        {
            "id": "IC03",
            "misconception": "The order of integration in double integrals can always be swapped without changing limits",
            "danger": "CRITICAL",
            "question": "To change the order of ∫₀¹∫ₓ¹ f(x,y) dy dx, can you just write ∫₀¹∫₀¹ f(x,y) dx dy?",
            "correct": "No — changing the order of integration ALWAYS requires rewriting the limits by sketching the region. The original integral integrates y from x to 1, and x from 0 to 1. After changing order: y goes from 0 to 1, and x goes from 0 to y.",
            "why_students_believe_it": "Students think of double integrals as two independent single integrals."
        },
        {
            "id": "IC04",
            "misconception": "Beta function B(m,n) = B(n,m) means the integral limits are symmetric",
            "danger": "MEDIUM",
            "question": "Why is B(m,n) = B(n,m)? Is it because the limits of integration are symmetric?",
            "correct": "B(m,n) = ∫₀¹ x^(m-1)(1-x)^(n-1)dx. The symmetry B(m,n)=B(n,m) comes from the substitution x→(1-x), not from symmetric limits.",
            "why_students_believe_it": "Students see the result is symmetric and assume the reason is symmetry of limits."
        }
    ],
    "infinite_series": [
        {
            "id": "IS01",
            "misconception": "If the nth term goes to zero, the series converges",
            "danger": "CRITICAL",
            "question": "The harmonic series has terms 1/n → 0. Does it converge?",
            "correct": "No — the harmonic series Σ(1/n) diverges even though 1/n → 0. The nth term going to zero is NECESSARY but NOT SUFFICIENT for convergence. The divergence test only works one way: if aₙ does NOT go to zero, the series definitely diverges. If aₙ → 0, you need another test.",
            "why_students_believe_it": "The divergence test is taught as the first test, and students incorrectly apply its contrapositive."
        },
        {
            "id": "IS02",
            "misconception": "Absolute convergence and conditional convergence give the same sum",
            "danger": "HIGH",
            "question": "The alternating harmonic series Σ(-1)^(n+1)/n converges to ln(2). If we rearrange its terms, do we still get ln(2)?",
            "correct": "No — by the Riemann rearrangement theorem, a conditionally convergent series can be rearranged to converge to ANY real number, or to diverge. Only absolutely convergent series are immune to rearrangement.",
            "why_students_believe_it": "Students assume addition is commutative for infinite sums, just as it is for finite sums."
        },
        {
            "id": "IS03",
            "misconception": "The ratio test always gives a conclusive answer",
            "danger": "MEDIUM",
            "question": "Apply the ratio test to Σ(1/n²). What happens? Does it converge or diverge?",
            "correct": "The ratio test gives L = lim(n→∞) (n/(n+1))² = 1 — INCONCLUSIVE. When L=1, the ratio test fails and you must use another test (here the p-series test with p=2>1 confirms convergence).",
            "why_students_believe_it": "Students learn the ratio test as the 'universal' test and don't know what to do when it fails."
        }
    ],
    "linear_algebra": [
        {
            "id": "LA01",
            "misconception": "Eigenvalues are always real numbers",
            "danger": "HIGH",
            "question": "Find the eigenvalues of the matrix [[0, -1], [1, 0]]. Are they real?",
            "correct": "The characteristic equation is λ²+1=0, giving λ=±i — complex eigenvalues. Real eigenvalues are guaranteed ONLY for symmetric matrices (by the spectral theorem).",
            "why_students_believe_it": "Most textbook examples use symmetric matrices which always have real eigenvalues."
        },
        {
            "id": "LA02",
            "misconception": "If AB = 0 then A = 0 or B = 0",
            "danger": "CRITICAL",
            "question": "Give an example of two non-zero matrices A and B where AB = 0.",
            "correct": "A = [[1,0],[0,0]] and B = [[0,0],[0,1]] gives AB = 0 with neither A nor B being zero. This is called zero divisors. The cancellation law of real numbers does NOT apply to matrices.",
            "why_students_believe_it": "Direct analogy from real numbers where ab=0 implies a=0 or b=0."
        },
        {
            "id": "LA03",
            "misconception": "Rank of a matrix equals the number of non-zero rows",
            "danger": "HIGH",
            "question": "What is the rank of the matrix [[1,2,3],[2,4,6],[0,0,0]]?",
            "correct": "Rank = 1, not 2. Row 2 is twice row 1, so after row reduction it becomes zero. Rank is the number of non-zero rows in ROW ECHELON FORM — not in the original matrix.",
            "why_students_believe_it": "Students confuse 'non-zero rows in the original matrix' with 'non-zero rows after row reduction'."
        },
        {
            "id": "LA04",
            "misconception": "A matrix with all non-zero entries is always invertible",
            "danger": "HIGH",
            "question": "Is the matrix [[1,2],[2,4]] invertible? All its entries are non-zero.",
            "correct": "No — det([[1,2],[2,4]]) = 4-4 = 0, so it is singular. A matrix is invertible if and only if its determinant is non-zero.",
            "why_students_believe_it": "Students confuse 'non-zero matrix' with 'invertible matrix'."
        },
        {
            "id": "LA05",
            "misconception": "Cayley-Hamilton theorem means a matrix satisfies its own characteristic equation as a number would",
            "danger": "MEDIUM",
            "question": "If the characteristic equation of A is λ²-3λ+2=0, what does Cayley-Hamilton say? Write the matrix equation.",
            "correct": "Cayley-Hamilton says A²-3A+2I=0 where I is the identity matrix. Students often write A²-3A+2=0 without the identity matrix, which is meaningless.",
            "why_students_believe_it": "Students substitute A into the scalar equation without converting scalar terms to matrix form."
        }
    ],
    "ode_first": [
        {
            "id": "OF01",
            "misconception": "Every first order ODE can be solved by separating variables",
            "danger": "HIGH",
            "question": "Identify which method applies: dy/dx = (x+y)/(x-y). Can you separate variables here?",
            "correct": "No — this equation cannot be separated. It is a homogeneous equation, solved by substitution y=vx. Always identify the type first.",
            "why_students_believe_it": "Variables separable is taught first and students default to it for every ODE."
        },
        {
            "id": "OF02",
            "misconception": "The integrating factor for a linear ODE is always e^(∫P dx)",
            "danger": "MEDIUM",
            "question": "The standard form is dy/dx + P(x)y = Q(x). What if the equation is dx/dy + P(y)x = Q(y)?",
            "correct": "When x is the dependent variable (dx/dy form), the integrating factor is e^(∫P(y)dy) — not e^(∫P dx). Students must first identify which variable is dependent.",
            "why_students_believe_it": "Students memorise the formula for dy/dx form and apply it blindly to all linear ODEs."
        },
        {
            "id": "OF03",
            "misconception": "An exact equation M dx + N dy = 0 has solution F where ∂F/∂x = N",
            "danger": "CRITICAL",
            "question": "For the exact equation M dx + N dy = 0, is ∂F/∂x = M or ∂F/∂x = N?",
            "correct": "∂F/∂x = M and ∂F/∂y = N. Many students swap M and N when integrating to find F.",
            "why_students_believe_it": "Confusion between the test condition (∂M/∂y = ∂N/∂x) and the integration conditions."
        }
    ],
    "ode_higher": [
        {
            "id": "OH01",
            "misconception": "Particular integral for e^(ax) fails only when a is a root of the auxiliary equation",
            "danger": "HIGH",
            "question": "Find PI for y'' - 2y' + y = e^x. What is the auxiliary equation? Is the PI formula e^x/f(1)?",
            "correct": "The auxiliary equation is (D-1)²=0, so D=1 is a repeated root. For a repeated root of multiplicity r, PI = x^r·e^(ax)/f^(r)(a). Students only remember the simple root case.",
            "why_students_believe_it": "Textbooks often show the simple failure case without emphasising the repeated root case."
        },
        {
            "id": "OH02",
            "misconception": "The general solution is just the particular integral",
            "danger": "CRITICAL",
            "question": "You found that y = x²e^x satisfies y'' - 2y' + y = 2e^x. Is this the complete general solution?",
            "correct": "No — the complete general solution is y = CF + PI = (c₁ + c₂x)e^x + x²e^x. Missing the complementary function loses all marks.",
            "why_students_believe_it": "Students focus on finding the particular integral and forget to add the complementary function."
        },
        {
            "id": "OH03",
            "misconception": "Wronskian being zero at one point means the functions are linearly dependent",
            "danger": "HIGH",
            "question": "If W(f,g)(x₀) = 0 at a single point x₀, does that mean f and g are linearly dependent?",
            "correct": "No. For solutions of a linear ODE, the Wronskian is either identically zero everywhere (dependent) or never zero (independent). This is Abel's theorem.",
            "why_students_believe_it": "Students check the Wronskian at one convenient point rather than understanding its behaviour."
        }
    ],
    "laplace": [
        {
            "id": "LT01",
            "misconception": "Laplace transform of a product is the product of Laplace transforms",
            "danger": "CRITICAL",
            "question": "Is L{t·sin(t)} = L{t} · L{sin(t)} = (1/s²)·(1/(s²+1))?",
            "correct": "No — L{f·g} ≠ L{f}·L{g}. The correct result uses L{tⁿf(t)} = (-1)ⁿ dⁿ/dsⁿ [F(s)]. Product of transforms gives convolution, not product.",
            "why_students_believe_it": "Analogy with linearity: L{f+g} = L{f}+L{g} makes students think multiplication also distributes."
        },
        {
            "id": "LT02",
            "misconception": "Initial conditions are applied after finding the general solution",
            "danger": "HIGH",
            "question": "When solving an IVP using Laplace transforms, when exactly do the initial conditions appear?",
            "correct": "Initial conditions appear DURING the transformation step: L{y''} = s²Y(s) - sy(0) - y'(0). Not at the end.",
            "why_students_believe_it": "Classical method habit: solve ODE first, apply initial conditions last."
        },
        {
            "id": "LT03",
            "misconception": "Inverse Laplace transform of F(s)·G(s) is f(t)·g(t)",
            "danger": "CRITICAL",
            "question": "Find L⁻¹{1/(s(s+1))} — is it L⁻¹{1/s} · L⁻¹{1/(s+1)} = 1·e^(-t)?",
            "correct": "No — L⁻¹{F(s)·G(s)} = f(t)*g(t) (convolution), not the product. Use partial fractions: 1/(s(s+1)) = 1/s - 1/(s+1), giving L⁻¹ = 1 - e^(-t).",
            "why_students_believe_it": "Students reverse the wrong 'rule' L{f·g} = L{f}·L{g}."
        }
    ],
    "vector_calc": [
        {
            "id": "VC01",
            "misconception": "div(curl F) = curl(div F)",
            "danger": "HIGH",
            "question": "What is div(curl F)? What is curl(div F)? Are they the same?",
            "correct": "div(curl F) = 0 always (identity). curl(div F) is meaningless — div F is a scalar, curl needs a vector input.",
            "why_students_believe_it": "Students treat div and curl as interchangeable operators."
        },
        {
            "id": "VC02",
            "misconception": "A vector field with zero curl is always conservative",
            "danger": "HIGH",
            "question": "If curl F = 0 everywhere, is F necessarily conservative?",
            "correct": "Only if the domain is simply connected. In multiply connected domains, curl F = 0 does not imply conservative.",
            "why_students_believe_it": "The theorem is taught without the simply-connected condition."
        },
        {
            "id": "VC03",
            "misconception": "Green's, Stokes' and Gauss's theorems are three separate unrelated results",
            "danger": "MEDIUM",
            "question": "How are Green's theorem, Stokes' theorem, and Gauss's divergence theorem related?",
            "correct": "All three are special cases of the Generalised Stokes' theorem. Green's is 2D, Stokes relates surface to boundary line, Gauss relates volume to boundary surface.",
            "why_students_believe_it": "They are taught as three separate named theorems."
        }
        ],
    "complex_analysis": [
        {
            "id": "CA01",
            "misconception": "An analytic function is just a function you can write a formula for",
            "danger": "HIGH",
            "question": "Is f(z) = z̄ (complex conjugate) analytic? It has a simple formula.",
            "correct": "No — f(z) = z̄ = x - iy fails the Cauchy-Riemann equations: u=x, v=-y gives ∂u/∂x=1 but ∂v/∂y=-1, so CR is violated everywhere. Analytic means the derivative exists in the complex sense — much stronger than having a formula.",
            "why_students_believe_it": "Analogy with real analysis where differentiable ≈ has a formula."
        },
        {
            "id": "CA02",
            "misconception": "Cauchy's theorem means every complex integral around a closed curve is zero",
            "danger": "CRITICAL",
            "question": "Is ∮_C dz/z = 0 for C being the unit circle? Apply Cauchy's theorem.",
            "correct": "No — ∮_C dz/z = 2πi. Cauchy's theorem requires the function to be ANALYTIC INSIDE AND ON the contour. f(z)=1/z has a singularity at z=0 inside the unit circle.",
            "why_students_believe_it": "Students apply Cauchy's theorem without checking whether singularities lie inside the contour."
        },
        {
            "id": "CA03",
            "misconception": "The residue at a pole is always the numerator divided by the derivative of the denominator",
            "danger": "HIGH",
            "question": "Find the residue of f(z) = 1/(z²(z-1)) at z=0. Is it 1/2z|_{z=0}?",
            "correct": "z=0 is a pole of order 2, not a simple pole. The simple pole formula only works for simple poles. For pole of order m, use the higher order formula.",
            "why_students_believe_it": "The simple pole formula is taught first and most prominently."
        }
    ],
    "fourier_series": [
        {
            "id": "FS01",
            "misconception": "Fourier series always converges to f(x) at every point",
            "danger": "HIGH",
            "question": "At a point of discontinuity x₀, what value does the Fourier series converge to?",
            "correct": "At a discontinuity, Fourier series converges to the AVERAGE of left and right limits: [f(x₀⁺) + f(x₀⁻)]/2. This is the Dirichlet condition.",
            "why_students_believe_it": "The series is called 'of f(x)' suggesting it equals f(x) everywhere."
        },
        {
            "id": "FS02",
            "misconception": "Any function can be represented by a Fourier series",
            "danger": "MEDIUM",
            "question": "What conditions must f(x) satisfy for its Fourier series to exist and converge?",
            "correct": "Dirichlet conditions: (1) periodic, (2) bounded, (3) finite number of maxima, minima, and discontinuities in one period.",
            "why_students_believe_it": "Textbooks jump straight to computing without emphasising validity conditions."
        },
        {
            "id": "FS03",
            "misconception": "For an odd function, a₀ = 0 because the average is zero",
            "danger": "MEDIUM",
            "question": "Why is a₀ = 0 for an odd function f(x) on [-L, L]?",
            "correct": "a₀ = (1/L)∫₋ₗᴸ f(x)dx. For odd function f(-x)=-f(x), integral over symmetric interval is zero. ALL cosine coefficients aₙ = 0 for odd functions.",
            "why_students_believe_it": "Students memorise the result but cannot explain the reasoning."
        }
    ],
    "probability": [
        {
            "id": "PR01",
            "misconception": "P(A∩B) = P(A)·P(B) always",
            "danger": "CRITICAL",
            "question": "A card is drawn from a deck. A = 'red', B = 'king'. Are A and B independent? Calculate P(A∩B) both ways.",
            "correct": "P(A∩B) = P(A)·P(B) is the DEFINITION of independence, not a general rule. For dependent events, use P(A∩B) = P(A)·P(B|A).",
            "why_students_believe_it": "Students see multiplication rule in independent examples and generalise incorrectly."
        },
        {
            "id": "PR02",
            "misconception": "The mean of a normal distribution is always 0",
            "danger": "HIGH",
            "question": "If X ~ N(μ, σ²), what are the mean and variance? When is the mean zero?",
            "correct": "Mean = μ, Variance = σ². Mean is zero only for STANDARD normal N(0,1). Always convert using Z = (X-μ)/σ.",
            "why_students_believe_it": "Z-tables use standard normal and students confuse standard with general form."
        },
        {
            "id": "PR03",
            "misconception": "Variance can be negative if the data has more negative values",
            "danger": "HIGH",
            "question": "Can Var(X) ever be negative? What is Var(X) if X always takes the same value?",
            "correct": "Variance is ALWAYS non-negative. Var(X) = E[(X-μ)²] ≥ 0 because it is expectation of a squared quantity. If constant, Var(X) = 0.",
            "why_students_believe_it": "Students confuse variance with deviations (X-μ) which can be negative."
        }
    ],
    "numerical": [
        {
            "id": "NM01",
            "misconception": "Newton-Raphson always converges to the correct root",
            "danger": "HIGH",
            "question": "Can Newton-Raphson method fail to converge? Give a condition when it might diverge.",
            "correct": "Newton-Raphson can FAIL if: (1) f'(xₙ)=0, (2) initial guess too far, (3) multiple roots nearby. Not globally convergent.",
            "why_students_believe_it": "Textbook examples are chosen to always converge."
        },
        {
            "id": "NM02",
            "misconception": "Simpson's 1/3 rule can be applied for any number of subintervals",
            "danger": "CRITICAL",
            "question": "You want to apply Simpson's 1/3 rule with 5 subintervals. Can you?",
            "correct": "Simpson's 1/3 rule REQUIRES an EVEN number of subintervals. With 5 subintervals you CANNOT apply it.",
            "why_students_believe_it": "Students memorise the formula without remembering the constraint on n."
        },
        {
            "id": "NM03",
            "misconception": "More iterations always means more accuracy in Newton-Raphson",
            "danger": "MEDIUM",
            "question": "After convergence to 1.4142135, should you do more iterations?",
            "correct": "Stop when |xₙ₊₁ - xₙ| < ε. More iterations past convergence just repeat digits.",
            "why_students_believe_it": "Students think more iterations = more accurate without understanding convergence criteria."
        }
    ],
    "transforms": [
        {
            "id": "TR01",
            "misconception": "Z-transform and Laplace transform are just different names for the same thing",
            "danger": "HIGH",
            "question": "What is the fundamental difference between Z-transform and Laplace transform?",
            "correct": "Laplace is for continuous-time: F(s) = ∫₀^∞ f(t)e^(-st)dt. Z-transform is for discrete-time: X(z) = Σₙ x[n]z^(-n). Connected by z = e^(sT).",
            "why_students_believe_it": "Both convert time-domain to algebraic — students see similarity but miss the fundamental difference."
        },
        {
            "id": "TR02",
            "misconception": "Region of Convergence (ROC) is always the entire z-plane",
            "danger": "HIGH",
            "question": "What is the ROC of X(z) = z/(z-0.5) for a causal sequence?",
            "correct": "ROC = {|z| > 0.5}. For causal sequences ROC is exterior to a circle. ROC MUST be stated with every Z-transform answer.",
            "why_students_believe_it": "Students compute the transform correctly but treat ROC as an afterthought."
        }
    ]
}

# ══════════════════════════════════════════════════════════════
#  MISCONCEPTION DETECTOR PROMPT
# ══════════════════════════════════════════════════════════════
def build_misconception_prompt(topic_key, student_answer, question_id):
    """Evaluate student's free-text answer against known misconceptions"""
    topic_misconceptions = MISCONCEPTIONS.get(topic_key, [])
    question_data = None
    for m in topic_misconceptions:
        if m["id"] == question_id:
            question_data = m
            break

    if not question_data:
        return None

    return f"""You are MathSphere's Misconception Detector — a specialist in mathematics education.

You have asked a diagnostic question to probe a specific misconception.

MISCONCEPTION BEING PROBED: {question_data['misconception']}
DANGER LEVEL: {question_data['danger']}

DIAGNOSTIC QUESTION ASKED:
{question_data['question']}

STUDENT'S ANSWER:
{student_answer}

CORRECT UNDERSTANDING:
{question_data['correct']}

WHY STUDENTS HOLD THIS MISCONCEPTION:
{question_data['why_students_believe_it']}

YOUR TASK — analyse the student's answer carefully:

DIAGNOSIS:
[State clearly: does the student's answer reveal the misconception, a partial misconception, or correct understanding?
Quote the specific phrase in their answer that reveals this.]

WHAT THIS TELLS US:
[Explain precisely what mental model the student has]

THE CORRECT UNDERSTANDING:
[Explain the correct understanding clearly and gently]

THE COUNTEREXAMPLE THAT BREAKS THE MISCONCEPTION:
[Give one specific numerical counterexample that makes the misconception obviously wrong]

HOW THIS AFFECTS EXAM PERFORMANCE:
[Describe exactly which exam questions this misconception will cause errors in]

HOW TO FIX THIS PERMANENTLY:
[One specific mental reframe or visual image that replaces the wrong belief]

CONFIDENCE IN DIAGNOSIS: HIGH / MEDIUM / LOW

Tone: Warm, non-judgmental, encouraging. Never say "wrong" — say "this is a very common belief, and here is what is actually happening."
"""


# ══════════════════════════════════════════════════════════════
#  MISCONCEPTION ROUTES
# ══════════════════════════════════════════════════════════════
@eng_bp.route("/eng/misconceptions", methods=["POST"])
def get_misconceptions():
    """Return diagnostic questions for a topic"""
    try:
        data, err, code = validate_json("topic")
        if err:
            return err, code
        topic = data.get("topic", "")
        topic_misconceptions = MISCONCEPTIONS.get(topic, [])
        questions = [{
            "id":            m["id"],
            "question":      m["question"],
            "danger":        m["danger"],
            "misconception": m["misconception"]
        } for m in topic_misconceptions]
        return jsonify({"questions": questions, "topic": topic})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/diagnose", methods=["POST"])
def diagnose():
    """Evaluate student answer and provide misconception diagnosis"""
    try:
        data, err, code = validate_json("topic", "question_id", "answer")
        if err:
            return err, code
        topic          = data.get("topic", "")
        question_id    = data.get("question_id", "")
        student_answer = data.get("answer", "")
        prompt = build_misconception_prompt(topic, student_answer, question_id)
        if not prompt:
            return jsonify({"error": "Question not found"}), 404
        response, source = get_eng_response(prompt)

        # Track misconception in progress
        student_id = data.get("student_id", "anonymous")
        update_progress(student_id, "misconception_found", {"misconception_id": question_id})

        return jsonify({"response": response, "source": source})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  NEW ROUTES — Step-by-Step Solver
# ══════════════════════════════════════════════════════════════
@eng_bp.route("/eng/solve", methods=["POST"])
def solve():
    """Solve any engineering math problem step by step"""
    try:
        data, err, code = validate_json("problem")
        if err:
            return err, code
        problem   = data.get("problem", "")
        topic_key = data.get("topic", "")
        prompt    = build_solve_prompt(problem, topic_key)
        response, source = get_eng_response(prompt)
        return jsonify({
            "response":   response,
            "source":     source,
            "references": REFERENCES.get(topic_key, [])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  NEW ROUTES — Compare Methods
# ══════════════════════════════════════════════════════════════
@eng_bp.route("/eng/compare", methods=["POST"])
def compare():
    """Compare two methods or concepts side by side"""
    try:
        data, err, code = validate_json("method1", "method2")
        if err:
            return err, code
        method1   = data.get("method1", "")
        method2   = data.get("method2", "")
        topic_key = data.get("topic", "")
        prompt    = build_compare_prompt(method1, method2, topic_key)
        response, source = get_eng_response(prompt)
        return jsonify({
            "response":   response,
            "source":     source,
            "references": REFERENCES.get(topic_key, [])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  NEW ROUTES — Exam Strategy
# ══════════════════════════════════════════════════════════════
@eng_bp.route("/eng/examstrategy", methods=["POST"])
def exam_strategy():
    """Generate topic-wise exam preparation plan"""
    try:
        data, err, code = validate_json("topic")
        if err:
            return err, code
        topic_key       = data.get("topic", "")
        hours_available = data.get("hours", "8")
        prompt = build_exam_strategy_prompt(topic_key, hours_available)
        response, source = get_eng_response(prompt)
        return jsonify({"response": response, "source": source})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  NEW ROUTES — Doubt Solver
# ══════════════════════════════════════════════════════════════
@eng_bp.route("/eng/doubt", methods=["POST"])
def doubt():
    """Diagnose and resolve a specific doubt"""
    try:
        data, err, code = validate_json("doubt")
        if err:
            return err, code
        doubt_text = data.get("doubt", "")
        topic_key  = data.get("topic", "")
        subtopic   = data.get("subtopic", "")
        prompt     = build_doubt_prompt(doubt_text, topic_key, subtopic)
        response, source = get_eng_response(prompt)
        return jsonify({
            "response":   response,
            "source":     source,
            "references": REFERENCES.get(topic_key, [])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  NEW ROUTES — Topic Roadmap (no AI call)
# ══════════════════════════════════════════════════════════════
@eng_bp.route("/eng/roadmap", methods=["POST"])
def roadmap():
    """Get structured learning roadmap for a topic"""
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


# ══════════════════════════════════════════════════════════════
#  NEW ROUTES — Progress Tracking
# ══════════════════════════════════════════════════════════════
@eng_bp.route("/eng/progress", methods=["GET"])
def get_student_progress():
    """Get progress for a student"""
    try:
        student_id = request.args.get("student_id", "anonymous")
        progress = get_progress(student_id)

        # Calculate completion percentage per topic
        total_subtopics = 0
        for sem_data in SYLLABUS.values():
            for topic_data in sem_data["topics"].values():
                total_subtopics += len(topic_data["subtopics"])

        completed = len(progress["completed_subtopics"])
        percentage = round((completed / total_subtopics) * 100, 1) if total_subtopics > 0 else 0

        return jsonify({
            "progress":              progress,
            "total_subtopics":       total_subtopics,
            "completed_count":       completed,
            "completion_percentage": percentage
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/progress/update", methods=["POST"])
def update_student_progress():
    """Update progress for a student"""
    try:
        data, err, code = validate_json("action")
        if err:
            return err, code
        student_id = data.get("student_id", "anonymous")
        action     = data.get("action", "")
        valid_actions = [
            "complete_subtopic", "mark_weak", "mark_strong",
            "misconception_found", "mock_test", "study_time"
        ]
        if action not in valid_actions:
            return jsonify({"error": f"Invalid action. Valid: {', '.join(valid_actions)}"}), 400

        progress = update_progress(student_id, action, data)
        return jsonify({"progress": progress, "message": f"Progress updated: {action}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════
#  NEW ROUTES — Quick Method Selector (no AI call)
#  Student describes their ODE/integral/equation type,
#  gets instant method recommendation
# ══════════════════════════════════════════════════════════════
METHOD_SELECTOR = {
    "ode_first_order": {
        "label": "First Order ODE Method Selector",
        "decision_tree": [
            {"check": "Can you write it as f(x)dx = g(y)dy?", "yes": "Variables Separable Method", "no": "Continue below"},
            {"check": "Is it of the form dy/dx = f(y/x)?", "yes": "Homogeneous ODE — substitute y = vx", "no": "Continue below"},
            {"check": "Is it of the form dy/dx + P(x)y = Q(x)?", "yes": "Linear ODE — IF = e^(∫P dx)", "no": "Continue below"},
            {"check": "Is it of the form dy/dx + P(x)y = Q(x)yⁿ?", "yes": "Bernoulli — substitute v = y^(1-n)", "no": "Continue below"},
            {"check": "Is M dx + N dy = 0 with ∂M/∂y = ∂N/∂x?", "yes": "Exact Equation", "no": "Continue below"},
            {"check": "Is (∂M/∂y - ∂N/∂x)/N a function of x only?", "yes": "Integrating Factor μ(x)", "no": "Continue below"},
            {"check": "Is (∂N/∂x - ∂M/∂y)/M a function of y only?", "yes": "Integrating Factor μ(y)", "no": "Continue below"},
            {"check": "Is it y = px + f(p) where p = dy/dx?", "yes": "Clairaut's Equation", "no": "Try substitution or numerical method"}
        ]
    },
    "convergence_tests": {
        "label": "Series Convergence Test Selector",
        "decision_tree": [
            {"check": "Does aₙ → 0 as n → ∞?", "yes": "Continue testing (necessary but not sufficient)", "no": "DIVERGES by Divergence Test"},
            {"check": "Is it a geometric series Σarⁿ?", "yes": "Converges if |r| < 1, diverges if |r| ≥ 1", "no": "Continue below"},
            {"check": "Is it a p-series Σ1/nᵖ?", "yes": "Converges if p > 1, diverges if p ≤ 1", "no": "Continue below"},
            {"check": "Can you compute lim |aₙ₊₁/aₙ|?", "yes": "Ratio Test: L<1 converges, L>1 diverges, L=1 inconclusive", "no": "Continue below"},
            {"check": "Can you compute lim |aₙ|^(1/n)?", "yes": "Root Test: L<1 converges, L>1 diverges, L=1 inconclusive", "no": "Continue below"},
            {"check": "Is aₙ ≥ bₙ ≥ 0 with Σbₙ known?", "yes": "Comparison Test", "no": "Continue below"},
            {"check": "Is it alternating: Σ(-1)ⁿbₙ with bₙ decreasing to 0?", "yes": "Alternating Series Test — converges", "no": "Continue below"},
            {"check": "Can you integrate f(x) where f(n) = aₙ?", "yes": "Integral Test", "no": "Try Limit Comparison Test"}
        ]
    },
    "integration_methods": {
        "label": "Integration Method Selector",
        "decision_tree": [
            {"check": "Is it a standard form from formula tables?", "yes": "Direct formula application", "no": "Continue below"},
            {"check": "Is it ∫f(g(x))g'(x)dx?", "yes": "Substitution: let u = g(x)", "no": "Continue below"},
            {"check": "Is it ∫u·dv form (product of two functions)?", "yes": "Integration by Parts: ∫u dv = uv - ∫v du", "no": "Continue below"},
            {"check": "Is it a rational function P(x)/Q(x)?", "yes": "Partial Fractions (if degree P < degree Q)", "no": "Continue below"},
            {"check": "Does it contain √(a²-x²), √(a²+x²), or √(x²-a²)?", "yes": "Trigonometric Substitution", "no": "Continue below"},
            {"check": "Is it sinᵐx·cosⁿx?", "yes": "Reduction Formula or Wallis Formula", "no": "Continue below"},
            {"check": "Is it an improper integral?", "yes": "Check convergence first, then evaluate limit", "no": "Try combination of methods"}
        ]
    },
    "laplace_inverse": {
        "label": "Inverse Laplace Transform Method Selector",
        "decision_tree": [
            {"check": "Is F(s) in the standard table?", "yes": "Direct lookup", "no": "Continue below"},
            {"check": "Is F(s) a rational function?", "yes": "Partial Fractions → lookup each term", "no": "Continue below"},
            {"check": "Does F(s) have the form F(s-a)?", "yes": "First Shifting: e^(at)·L⁻¹{F(s)}", "no": "Continue below"},
            {"check": "Does F(s) contain e^(-as)?", "yes": "Second Shifting: u(t-a)·f(t-a)", "no": "Continue below"},
            {"check": "Is F(s) = F₁(s)·F₂(s)?", "yes": "Convolution: f₁(t) * f₂(t) = ∫₀ᵗ f₁(τ)f₂(t-τ)dτ", "no": "Try series expansion or contour integration"}
        ]
    },
    "numerical_integration": {
        "label": "Numerical Integration Method Selector",
        "decision_tree": [
            {"check": "How many data points do you have?", "yes": "If n+1 points, you have n subintervals", "no": "Count your data first"},
            {"check": "Is n (number of subintervals) even?", "yes": "Simpson's 1/3 Rule (most accurate for even n)", "no": "Continue below"},
            {"check": "Is n divisible by 3?", "yes": "Simpson's 3/8 Rule", "no": "Continue below"},
            {"check": "Is n divisible by 6?", "yes": "Weddle's Rule (most accurate)", "no": "Continue below"},
            {"check": "None of the above?", "yes": "Trapezoidal Rule (works for any n)", "no": "Trapezoidal Rule"}
        ]
    }
}

@eng_bp.route("/eng/methodselector", methods=["POST"])
def method_selector():
    """Return decision tree for method selection"""
    try:
        data, err, code = validate_json("category")
        if err:
            return err, code
        category = data.get("category", "")
        selector = METHOD_SELECTOR.get(category)
        if not selector:
            return jsonify({
                "error": f"Category '{category}' not found",
                "available": list(METHOD_SELECTOR.keys())
            }), 404
        return jsonify(selector)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/methodselector/all")
def all_method_selectors():
    """Return all available method selectors"""
    return jsonify({
        "selectors": {k: v["label"] for k, v in METHOD_SELECTOR.items()}
    })


# ══════════════════════════════════════════════════════════════
#  NEW ROUTES — Quick Formula Lookup (no AI call)
#  Instant formula retrieval — no API cost
# ══════════════════════════════════════════════════════════════
QUICK_FORMULAS = {
    "derivatives": {
        "label": "Standard Derivatives",
        "formulas": [
            {"name": "Power Rule", "formula": "d/dx(xⁿ) = nxⁿ⁻¹", "condition": "n is any real number"},
            {"name": "Exponential", "formula": "d/dx(eˣ) = eˣ", "condition": "Always valid"},
            {"name": "General Exponential", "formula": "d/dx(aˣ) = aˣ ln(a)", "condition": "a > 0, a ≠ 1"},
            {"name": "Natural Log", "formula": "d/dx(ln x) = 1/x", "condition": "x > 0"},
            {"name": "Sine", "formula": "d/dx(sin x) = cos x", "condition": "x in radians"},
            {"name": "Cosine", "formula": "d/dx(cos x) = -sin x", "condition": "x in radians"},
            {"name": "Tangent", "formula": "d/dx(tan x) = sec²x", "condition": "x ≠ (2n+1)π/2"},
            {"name": "Inverse Sine", "formula": "d/dx(sin⁻¹x) = 1/√(1-x²)", "condition": "|x| < 1"},
            {"name": "Inverse Tangent", "formula": "d/dx(tan⁻¹x) = 1/(1+x²)", "condition": "All x"},
            {"name": "Product Rule", "formula": "d/dx(uv) = u(dv/dx) + v(du/dx)", "condition": "u, v differentiable"},
            {"name": "Quotient Rule", "formula": "d/dx(u/v) = [v(du/dx) - u(dv/dx)]/v²", "condition": "v ≠ 0"},
            {"name": "Chain Rule", "formula": "d/dx(f(g(x))) = f'(g(x))·g'(x)", "condition": "Both differentiable"},
        ]
    },
    "integrals": {
        "label": "Standard Integrals",
        "formulas": [
            {"name": "Power Rule", "formula": "∫xⁿ dx = xⁿ⁺¹/(n+1) + C", "condition": "n ≠ -1"},
            {"name": "Reciprocal", "formula": "∫(1/x) dx = ln|x| + C", "condition": "x ≠ 0"},
            {"name": "Exponential", "formula": "∫eˣ dx = eˣ + C", "condition": "Always valid"},
            {"name": "Sine", "formula": "∫sin x dx = -cos x + C", "condition": "x in radians"},
            {"name": "Cosine", "formula": "∫cos x dx = sin x + C", "condition": "x in radians"},
            {"name": "Secant Squared", "formula": "∫sec²x dx = tan x + C", "condition": "x ≠ (2n+1)π/2"},
            {"name": "Form 1/(a²+x²)", "formula": "∫dx/(a²+x²) = (1/a)tan⁻¹(x/a) + C", "condition": "a ≠ 0"},
            {"name": "Form 1/√(a²-x²)", "formula": "∫dx/√(a²-x²) = sin⁻¹(x/a) + C", "condition": "|x| < a"},
            {"name": "Form 1/(x²-a²)", "formula": "∫dx/(x²-a²) = (1/2a)ln|(x-a)/(x+a)| + C", "condition": "x ≠ ±a"},
        ]
    },
    "laplace_transforms": {
        "label": "Standard Laplace Transforms",
        "formulas": [
            {"name": "Constant", "formula": "L{1} = 1/s", "condition": "s > 0"},
            {"name": "Power", "formula": "L{tⁿ} = n!/sⁿ⁺¹", "condition": "s > 0, n = 0,1,2,..."},
            {"name": "Exponential", "formula": "L{eᵃᵗ} = 1/(s-a)", "condition": "s > a"},
            {"name": "Sine", "formula": "L{sin(at)} = a/(s²+a²)", "condition": "s > 0"},
            {"name": "Cosine", "formula": "L{cos(at)} = s/(s²+a²)", "condition": "s > 0"},
            {"name": "t·sin(at)", "formula": "L{t·sin(at)} = 2as/(s²+a²)²", "condition": "s > 0"},
            {"name": "t·cos(at)", "formula": "L{t·cos(at)} = (s²-a²)/(s²+a²)²", "condition": "s > 0"},
            {"name": "eᵃᵗ·sin(bt)", "formula": "L{eᵃᵗ·sin(bt)} = b/((s-a)²+b²)", "condition": "s > a"},
            {"name": "eᵃᵗ·cos(bt)", "formula": "L{eᵃᵗ·cos(bt)} = (s-a)/((s-a)²+b²)", "condition": "s > a"},
            {"name": "Unit Step", "formula": "L{u(t-a)} = e⁻ᵃˢ/s", "condition": "s > 0, a ≥ 0"},
            {"name": "Dirac Delta", "formula": "L{δ(t-a)} = e⁻ᵃˢ", "condition": "a ≥ 0"},
            {"name": "First Shifting", "formula": "L{eᵃᵗf(t)} = F(s-a)", "condition": "s > a"},
            {"name": "Second Shifting", "formula": "L{f(t-a)u(t-a)} = e⁻ᵃˢF(s)", "condition": "a ≥ 0"},
            {"name": "Derivative", "formula": "L{f'(t)} = sF(s) - f(0)", "condition": "f continuous"},
            {"name": "Second Derivative", "formula": "L{f''(t)} = s²F(s) - sf(0) - f'(0)", "condition": "f' continuous"},
            {"name": "Multiplication by t", "formula": "L{tf(t)} = -d/ds[F(s)]", "condition": "F differentiable"},
            {"name": "Division by t", "formula": "L{f(t)/t} = ∫ₛ^∞ F(u) du", "condition": "Integral exists"},
            {"name": "Convolution", "formula": "L{f*g} = F(s)·G(s)", "condition": "Both transforms exist"},
        ]
    },
    "z_transforms": {
        "label": "Standard Z-Transforms",
        "formulas": [
            {"name": "Unit Step", "formula": "Z{u[n]} = z/(z-1)", "condition": "|z| > 1"},
            {"name": "Unit Ramp", "formula": "Z{n·u[n]} = z/(z-1)²", "condition": "|z| > 1"},
            {"name": "Exponential", "formula": "Z{aⁿu[n]} = z/(z-a)", "condition": "|z| > |a|"},
            {"name": "n·aⁿ", "formula": "Z{n·aⁿu[n]} = az/(z-a)²", "condition": "|z| > |a|"},
            {"name": "Cosine", "formula": "Z{cos(nω)u[n]} = z(z-cosω)/(z²-2z·cosω+1)", "condition": "|z| > 1"},
            {"name": "Sine", "formula": "Z{sin(nω)u[n]} = z·sinω/(z²-2z·cosω+1)", "condition": "|z| > 1"},
        ]
    },
    "fourier_series_formulas": {
        "label": "Fourier Series Formulas",
        "formulas": [
            {"name": "Fourier Coefficients a₀", "formula": "a₀ = (1/L)∫₋ₗᴸ f(x) dx", "condition": "f satisfies Dirichlet conditions"},
            {"name": "Fourier Coefficients aₙ", "formula": "aₙ = (1/L)∫₋ₗᴸ f(x)cos(nπx/L) dx", "condition": "n = 1,2,3,..."},
            {"name": "Fourier Coefficients bₙ", "formula": "bₙ = (1/L)∫₋ₗᴸ f(x)sin(nπx/L) dx", "condition": "n = 1,2,3,..."},
            {"name": "Fourier Series", "formula": "f(x) = a₀/2 + Σ[aₙcos(nπx/L) + bₙsin(nπx/L)]", "condition": "Period = 2L"},
            {"name": "Parseval's Identity", "formula": "(1/L)∫₋ₗᴸ [f(x)]² dx = a₀²/2 + Σ(aₙ² + bₙ²)", "condition": "f² integrable"},
            {"name": "Even Function", "formula": "bₙ = 0, aₙ = (2/L)∫₀ᴸ f(x)cos(nπx/L) dx", "condition": "f(-x) = f(x)"},
            {"name": "Odd Function", "formula": "a₀ = aₙ = 0, bₙ = (2/L)∫₀ᴸ f(x)sin(nπx/L) dx", "condition": "f(-x) = -f(x)"},
        ]
    },
    "vector_identities": {
        "label": "Vector Calculus Identities",
        "formulas": [
            {"name": "Gradient", "formula": "∇f = (∂f/∂x)î + (∂f/∂y)ĵ + (∂f/∂z)k̂", "condition": "f is scalar field"},
            {"name": "Divergence", "formula": "∇·F = ∂F₁/∂x + ∂F₂/∂y + ∂F₃/∂z", "condition": "F is vector field"},
            {"name": "Curl", "formula": "∇×F = |î ĵ k̂; ∂/∂x ∂/∂y ∂/∂z; F₁ F₂ F₃|", "condition": "F is vector field"},
            {"name": "Laplacian", "formula": "∇²f = ∂²f/∂x² + ∂²f/∂y² + ∂²f/∂z²", "condition": "f twice differentiable"},
            {"name": "curl(grad f)", "formula": "∇×(∇f) = 0", "condition": "Always (identity)"},
            {"name": "div(curl F)", "formula": "∇·(∇×F) = 0", "condition": "Always (identity)"},
            {"name": "Green's Theorem", "formula": "∮(M dx + N dy) = ∬(∂N/∂x - ∂M/∂y) dA", "condition": "Simply connected, C positive orientation"},
            {"name": "Stokes' Theorem", "formula": "∬(∇×F)·dS = ∮F·dr", "condition": "Oriented surface with boundary"},
            {"name": "Gauss Divergence", "formula": "∭(∇·F) dV = ∬F·dS", "condition": "Closed surface, outward normal"},
        ]
    },
    "probability_distributions": {
        "label": "Probability Distribution Formulas",
        "formulas": [
            {"name": "Binomial PMF", "formula": "P(X=r) = ⁿCᵣ pʳ qⁿ⁻ʳ", "condition": "n trials, p = success prob, q = 1-p"},
            {"name": "Binomial Mean/Var", "formula": "E(X) = np, Var(X) = npq", "condition": "X ~ Bin(n,p)"},
            {"name": "Poisson PMF", "formula": "P(X=r) = e⁻λ λʳ/r!", "condition": "λ = mean rate"},
            {"name": "Poisson Mean/Var", "formula": "E(X) = Var(X) = λ", "condition": "X ~ Poi(λ)"},
            {"name": "Normal PDF", "formula": "f(x) = (1/σ√2π)e^(-(x-μ)²/2σ²)", "condition": "-∞ < x < ∞"},
            {"name": "Standard Normal", "formula": "Z = (X-μ)/σ ~ N(0,1)", "condition": "X ~ N(μ,σ²)"},
            {"name": "Exponential PDF", "formula": "f(x) = λe⁻λˣ, x ≥ 0", "condition": "λ > 0"},
            {"name": "Exponential Mean/Var", "formula": "E(X) = 1/λ, Var(X) = 1/λ²", "condition": "X ~ Exp(λ)"},
        ]
    },
    "numerical_formulas": {
        "label": "Numerical Methods Formulas",
        "formulas": [
            {"name": "Newton-Raphson", "formula": "xₙ₊₁ = xₙ - f(xₙ)/f'(xₙ)", "condition": "f'(xₙ) ≠ 0"},
            {"name": "Bisection", "formula": "c = (a+b)/2, check sign of f(c)", "condition": "f(a)·f(b) < 0"},
            {"name": "Trapezoidal Rule", "formula": "∫ ≈ (h/2)[y₀ + 2(y₁+...+yₙ₋₁) + yₙ]", "condition": "Any n"},
            {"name": "Simpson's 1/3", "formula": "∫ ≈ (h/3)[y₀ + 4(y₁+y₃+...) + 2(y₂+y₄+...) + yₙ]", "condition": "n MUST be even"},
            {"name": "Simpson's 3/8", "formula": "∫ ≈ (3h/8)[y₀ + 3(y₁+y₂) + 2y₃ + 3(y₄+y₅) + ...]", "condition": "n divisible by 3"},
            {"name": "RK4 k₁", "formula": "k₁ = hf(xₙ, yₙ)", "condition": ""},
            {"name": "RK4 k₂", "formula": "k₂ = hf(xₙ + h/2, yₙ + k₁/2)", "condition": ""},
            {"name": "RK4 k₃", "formula": "k₃ = hf(xₙ + h/2, yₙ + k₂/2)", "condition": ""},
            {"name": "RK4 k₄", "formula": "k₄ = hf(xₙ + h, yₙ + k₃)", "condition": ""},
            {"name": "RK4 Update", "formula": "yₙ₊₁ = yₙ + (k₁ + 2k₂ + 2k₃ + k₄)/6", "condition": ""},
            {"name": "Newton Forward", "formula": "y = y₀ + s·Δy₀ + s(s-1)/2!·Δ²y₀ + ...", "condition": "s = (x-x₀)/h, equally spaced"},
            {"name": "Lagrange", "formula": "P(x) = Σ yₖ · Πⱼ≠ₖ (x-xⱼ)/(xₖ-xⱼ)", "condition": "Any spacing"},
        ]
    }
}

@eng_bp.route("/eng/formulas", methods=["POST"])
def quick_formulas():
    """Get instant formula lookup — zero API cost"""
    try:
        data, err, code = validate_json("category")
        if err:
            return err, code
        category = data.get("category", "")
        formulas = QUICK_FORMULAS.get(category)
        if not formulas:
            return jsonify({
                "error":     f"Category '{category}' not found",
                "available": {k: v["label"] for k, v in QUICK_FORMULAS.items()}
            }), 404
        return jsonify(formulas)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/formulas/all")
def all_formula_categories():
    """List all available formula categories"""
    return jsonify({
        "categories": {k: {"label": v["label"], "count": len(v["formulas"])} for k, v in QUICK_FORMULAS.items()}
    })

@eng_bp.route("/eng/formulas/search")
def search_formulas():
    """Search across all formula categories"""
    query = request.args.get("q", "").lower().strip()
    if not query or len(query) < 2:
        return jsonify({"error": "Search query must be at least 2 characters", "results": []}), 400

    results = []
    for category, data in QUICK_FORMULAS.items():
        for formula in data["formulas"]:
            if (query in formula["name"].lower() or
                query in formula["formula"].lower() or
                query in formula.get("condition", "").lower()):
                results.append({
                    "category":  category,
                    "category_label": data["label"],
                    "name":      formula["name"],
                    "formula":   formula["formula"],
                    "condition": formula.get("condition", "")
                })

    return jsonify({
        "query":   query,
        "count":   len(results),
        "results": results
    })


# ══════════════════════════════════════════════════════════════
#  HEALTH CHECK AND STATS
# ══════════════════════════════════════════════════════════════
@eng_bp.route("/eng/health")
def health():
    """Health check and application stats"""
    total_subtopics = 0
    total_topics = 0
    for sem_data in SYLLABUS.values():
        for topic_data in sem_data["topics"].values():
            total_topics += 1
            total_subtopics += len(topic_data["subtopics"])

    total_misconceptions = sum(len(v) for v in MISCONCEPTIONS.values())
    total_formulas = sum(len(v["formulas"]) for v in QUICK_FORMULAS.values())
    total_method_selectors = sum(len(v["decision_tree"]) for v in METHOD_SELECTOR.values())

    return jsonify({
        "status":  "healthy",
        "app":     "MathSphere Engineering by Anupam Nigam",
        "version": "2.0",
        "stats": {
            "semesters":         len(SYLLABUS),
            "topics":            total_topics,
            "subtopics":         total_subtopics,
            "prerequisites":     len(PREREQUISITES),
            "misconceptions":    total_misconceptions,
            "quick_formulas":    total_formulas,
            "method_selectors":  total_method_selectors,
            "subject_connections": sum(len(v["connections"]) for v in SUBJECT_CONNECTIONS.values()),
            "references":        sum(len(v) for v in REFERENCES.values()),
            "cached_responses":  len(_response_cache),
            "active_students":   len(_student_progress)
        },
        "providers": {
            "groq":   "configured" if GROQ_API_KEY else "missing",
            "gemini": "configured" if GEMINI_API_KEY else "missing"
        },
        "routes": {
            "no_ai_cost": [
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
                "POST /eng/misconceptions"
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
                "POST /eng/doubt"
            ]
        }
    })
