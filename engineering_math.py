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
#  SYLLABUS DATA
# ══════════════════════════════════════════════════════════════
SYLLABUS = {
    "sem1": {
        "label": "Semester 1", "subtitle": "Calculus & Series",
        "topics": {
            "diff_calc": {
                "label": "Differential Calculus",
                "subtopics": ["Limits and Continuity","Differentiability",
                    "Rolle's Theorem","Lagrange's Mean Value Theorem",
                    "Cauchy's Mean Value Theorem","L'Hopital's Rule",
                    "Taylor's Theorem","Maclaurin Series",
                    "Indeterminate Forms","Curvature and Radius of Curvature"]
            },
            "partial_diff": {
                "label": "Partial Differentiation",
                "subtopics": ["Functions of Several Variables","Partial Derivatives",
                    "Euler's Theorem on Homogeneous Functions","Total Derivative",
                    "Jacobians","Maxima and Minima of Two Variables",
                    "Lagrange's Method of Multipliers"]
            },
            "integral_calc": {
                "label": "Integral Calculus",
                "subtopics": ["Reduction Formulae","Beta and Gamma Functions",
                    "Double Integrals","Change of Order of Integration",
                    "Triple Integrals","Applications: Area, Volume, Surface Area",
                    "Improper Integrals"]
            },
            "infinite_series": {
                "label": "Infinite Series",
                "subtopics": ["Convergence and Divergence","Comparison Test",
                    "Ratio Test (D'Alembert)","Root Test (Cauchy)",
                    "Integral Test","Alternating Series and Leibniz Test",
                    "Absolute and Conditional Convergence",
                    "Power Series and Radius of Convergence"]
            }
        }
    },
    "sem2": {
        "label": "Semester 2", "subtitle": "Linear Algebra & ODEs",
        "topics": {
            "linear_algebra": {
                "label": "Linear Algebra",
                "subtopics": ["Matrices and Types","Rank of a Matrix",
                    "Echelon Form and Normal Form","System of Linear Equations",
                    "Eigenvalues and Eigenvectors","Cayley-Hamilton Theorem",
                    "Diagonalization","Quadratic Forms","Positive Definite Matrices"]
            },
            "ode_first": {
                "label": "First Order ODEs",
                "subtopics": ["Formation of ODEs","Variables Separable",
                    "Homogeneous Equations","Exact Differential Equations",
                    "Integrating Factors","Linear First Order ODEs",
                    "Bernoulli's Equation","Orthogonal Trajectories",
                    "Applications: Growth and Decay"]
            },
            "ode_higher": {
                "label": "Higher Order ODEs",
                "subtopics": ["Linear ODEs with Constant Coefficients",
                    "Complementary Function","Particular Integral",
                    "Method of Undetermined Coefficients","Variation of Parameters",
                    "Euler-Cauchy Equation","Simultaneous Linear ODEs",
                    "Applications: Simple Harmonic Motion"]
            },
            "laplace": {
                "label": "Laplace Transforms",
                "subtopics": ["Definition and Existence",
                    "Laplace Transforms of Standard Functions",
                    "Properties: Linearity, Shifting","Inverse Laplace Transform",
                    "Partial Fractions Method","Convolution Theorem",
                    "Solution of ODEs using Laplace",
                    "Unit Step and Dirac Delta Functions"]
            }
        }
    },
    "sem3": {
        "label": "Semester 3", "subtitle": "Vector Calculus & Complex Analysis",
        "topics": {
            "vector_calc": {
                "label": "Vector Calculus",
                "subtopics": ["Scalar and Vector Fields",
                    "Gradient and Directional Derivative","Divergence and Curl",
                    "Vector Identities","Line Integrals","Surface Integrals",
                    "Volume Integrals","Green's Theorem in the Plane",
                    "Stokes' Theorem","Gauss Divergence Theorem"]
            },
            "complex_analysis": {
                "label": "Complex Analysis",
                "subtopics": ["Complex Numbers Review",
                    "Functions of a Complex Variable","Analytic Functions",
                    "Cauchy-Riemann Equations","Harmonic Functions",
                    "Elementary Complex Functions","Complex Integration",
                    "Cauchy's Integral Theorem","Cauchy's Integral Formula",
                    "Taylor and Laurent Series","Singularities and Poles",
                    "Residue Theorem","Contour Integration"]
            },
            "fourier_series": {
                "label": "Fourier Series",
                "subtopics": ["Periodic Functions","Dirichlet Conditions",
                    "Euler's Formulae",
                    "Fourier Series of Even and Odd Functions",
                    "Half-Range Sine and Cosine Series","Parseval's Identity",
                    "Complex Form of Fourier Series","Practical Harmonic Analysis"]
            }
        }
    },
    "sem4": {
        "label": "Semester 4", "subtitle": "Probability, Statistics & Numerical Methods",
        "topics": {
            "probability": {
                "label": "Probability & Statistics",
                "subtopics": ["Random Variables","Probability Distributions",
                    "Binomial Distribution","Poisson Distribution",
                    "Normal Distribution","Expectation and Variance",
                    "Joint Distributions","Correlation and Regression",
                    "Chi-Square Distribution","Hypothesis Testing",
                    "t-Test and F-Test","Sampling Theory"]
            },
            "numerical": {
                "label": "Numerical Methods",
                "subtopics": ["Errors and Approximations","Bisection Method",
                    "Regula-Falsi Method","Newton-Raphson Method",
                    "Newton's Forward Interpolation","Newton's Backward Interpolation",
                    "Lagrange Interpolation","Numerical Differentiation",
                    "Trapezoidal Rule","Simpson's 1/3 Rule","Simpson's 3/8 Rule",
                    "Euler's Method for ODEs","Runge-Kutta Method (RK4)"]
            },
            "transforms": {
                "label": "Transform Theory",
                "subtopics": ["Fourier Integral Theorem","Fourier Transform",
                    "Fourier Sine and Cosine Transforms",
                    "Convolution Theorem for Fourier","Z-Transform Definition",
                    "Z-Transform Properties","Inverse Z-Transform",
                    "Solution of Difference Equations"]
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
- Write inline math as $...$ and standalone equations on their own line as $$...$$
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
[Complete step-by-step proof. Every equation on its own line as $$...$$]

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
[Problem statement with specific numbers. Every equation as $$...$$]

SOLUTION:
[Step-by-step. Every equation on its own line as $$...$$. No steps skipped.]
[Label each step clearly]

MARKS BREAKDOWN:
[Step 1: what it earns. Step 2: what it earns. Etc. Total must add to stated marks.]

FINAL ANSWER:
$$[answer]$$

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
[Problem statement. All equations as $$...$$]

HINT:
[One line pointing in the right direction without giving it away]

MARKS BREAKDOWN:
[How marks are distributed across steps]

ANSWER:
$$[final answer — no working]$$
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
[Every important formula on its own line as $$...$$]
[Label each formula with its name]

STANDARD RESULTS TO MEMORISE:
[5-8 results that appear most in university papers. Each as $$...$$]

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
[Full question. Every equation on its own line as $$...$$]

APPROACH:
[1-2 sentences: exact technique or theorem to apply and why]

COMPLETE SOLUTION:
[Step-by-step solution. Every equation on its own line as $$...$$. No steps skipped.]

MARKS BREAKDOWN — STEP BY STEP:
[Step 1 — [description]: [N] mark(s)]
[Step 2 — [description]: [N] mark(s)]
[Step 3 — [description]: [N] mark(s)]
[... continue until total marks accounted for]

FINAL ANSWER:
$$[answer]$$

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
[Question with all equations as $$...$$]

Difficulty distribution: 40% straightforward, 40% multi-step, 20% proof or derivation.
Question types: mix direct formula application, proof-based, application to engineering context.

After ALL questions add:

COMPLETE SOLUTIONS

SOLUTION [N]:
[Complete step-by-step working. Every equation as $$...$$]

MARKS BREAKDOWN:
[Step 1 — description: N mark(s)]
[Step 2 — description: N mark(s)]
[Continue until {marks_each} marks accounted for]

FINAL ANSWER:
$$[answer]$$

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
$$[the complete formula — every symbol defined]$$

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
[All key results together — each as $$...$$]

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
Show all working. Every equation on its own line as $$...$$
Include at least one worked numerical example with specific numbers.
If relevant, mention which engineering subject uses this concept and how.
End with CONFIDENCE: HIGH / MEDIUM / LOW
"""


# ══════════════════════════════════════════════════════════════
#  API HELPERS
# ══════════════════════════════════════════════════════════════
def call_groq(prompt, system=""):
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
        return call_groq(full_prompt), "Groq"
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
        prereqs  = PREREQUISITES.get(subtopic, [])
        prompt   = build_learn_prompt(topic, subtopic, section)
        response, source = get_eng_response(prompt)
        return jsonify({
            "response":     response,
            "source":       source,
            "references":   REFERENCES.get(topic, []),
            "prerequisites": prereqs
        })
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
        return jsonify({"response": response, "source": source, "references": REFERENCES.get(topic, [])})
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
        return jsonify({"response": response, "source": source, "references": REFERENCES.get(topic, [])})
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

@eng_bp.route("/eng/formulabooklet", methods=["POST"])
def formula_booklet():
    try:
        data     = request.json
        topic    = data.get("topic","")
        subtopic = data.get("subtopic","")
        prompt   = build_formula_booklet_prompt(topic, subtopic)
        response, source = get_eng_response(prompt)
        return jsonify({"response": response, "source": source, "references": REFERENCES.get(topic, [])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@eng_bp.route("/eng/connections", methods=["POST"])
def connections():
    try:
        data     = request.json
        topic    = data.get("topic","")
        subtopic = data.get("subtopic","")
        topic_connections = SUBJECT_CONNECTIONS.get(topic)
        if topic_connections:
            return jsonify({
                "connections": topic_connections["connections"],
                "source":      "MathSphere Engineering",
                "references":  REFERENCES.get(topic, [])
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
$$[actual formula from this topic used in this subject]$$
EXAMPLE:
[One specific engineering problem using this]

Cover at least 5 different engineering subjects. Be specific.
"""
        response, source = get_eng_response(prompt)
        return jsonify({"response": response, "source": source, "references": REFERENCES.get(topic, [])})
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