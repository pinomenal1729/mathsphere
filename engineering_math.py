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
# ══════════════════════════════════════════════════════════════
SYLLABUS = {
    "sem1": {
        "label": "Semester 1",
        "subtitle": "Calculus & Series",
        "topics": {
            "diff_calc": {
                "label": "Differential Calculus",
                "subtopics": [
                    "Limits and Continuity","Differentiability",
                    "Rolle's Theorem","Lagrange's Mean Value Theorem",
                    "Cauchy's Mean Value Theorem","L'Hopital's Rule",
                    "Taylor's Theorem","Maclaurin Series",
                    "Indeterminate Forms","Curvature and Radius of Curvature"
                ]
            },
            "partial_diff": {
                "label": "Partial Differentiation",
                "subtopics": [
                    "Functions of Several Variables","Partial Derivatives",
                    "Euler's Theorem on Homogeneous Functions","Total Derivative",
                    "Jacobians","Maxima and Minima of Two Variables",
                    "Lagrange's Method of Multipliers"
                ]
            },
            "integral_calc": {
                "label": "Integral Calculus",
                "subtopics": [
                    "Reduction Formulae","Beta and Gamma Functions",
                    "Double Integrals","Change of Order of Integration",
                    "Triple Integrals","Applications: Area, Volume, Surface Area",
                    "Improper Integrals"
                ]
            },
            "infinite_series": {
                "label": "Infinite Series",
                "subtopics": [
                    "Convergence and Divergence","Comparison Test",
                    "Ratio Test (D'Alembert)","Root Test (Cauchy)",
                    "Integral Test","Alternating Series and Leibniz Test",
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
                    "Matrices and Types","Rank of a Matrix",
                    "Echelon Form and Normal Form","System of Linear Equations",
                    "Eigenvalues and Eigenvectors","Cayley-Hamilton Theorem",
                    "Diagonalization","Quadratic Forms","Positive Definite Matrices"
                ]
            },
            "ode_first": {
                "label": "First Order ODEs",
                "subtopics": [
                    "Formation of ODEs","Variables Separable",
                    "Homogeneous Equations","Exact Differential Equations",
                    "Integrating Factors","Linear First Order ODEs",
                    "Bernoulli's Equation","Orthogonal Trajectories",
                    "Applications: Growth and Decay"
                ]
            },
            "ode_higher": {
                "label": "Higher Order ODEs",
                "subtopics": [
                    "Linear ODEs with Constant Coefficients","Complementary Function",
                    "Particular Integral","Method of Undetermined Coefficients",
                    "Variation of Parameters","Euler-Cauchy Equation",
                    "Simultaneous Linear ODEs","Applications: Simple Harmonic Motion"
                ]
            },
            "laplace": {
                "label": "Laplace Transforms",
                "subtopics": [
                    "Definition and Existence",
                    "Laplace Transforms of Standard Functions",
                    "Properties: Linearity, Shifting","Inverse Laplace Transform",
                    "Partial Fractions Method","Convolution Theorem",
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
                    "Scalar and Vector Fields","Gradient and Directional Derivative",
                    "Divergence and Curl","Vector Identities","Line Integrals",
                    "Surface Integrals","Volume Integrals",
                    "Green's Theorem in the Plane","Stokes' Theorem",
                    "Gauss Divergence Theorem"
                ]
            },
            "complex_analysis": {
                "label": "Complex Analysis",
                "subtopics": [
                    "Complex Numbers Review","Functions of a Complex Variable",
                    "Analytic Functions","Cauchy-Riemann Equations",
                    "Harmonic Functions","Elementary Complex Functions",
                    "Complex Integration","Cauchy's Integral Theorem",
                    "Cauchy's Integral Formula","Taylor and Laurent Series",
                    "Singularities and Poles","Residue Theorem","Contour Integration"
                ]
            },
            "fourier_series": {
                "label": "Fourier Series",
                "subtopics": [
                    "Periodic Functions","Dirichlet Conditions","Euler's Formulae",
                    "Fourier Series of Even and Odd Functions",
                    "Half-Range Sine and Cosine Series","Parseval's Identity",
                    "Complex Form of Fourier Series","Practical Harmonic Analysis"
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
                    "Random Variables","Probability Distributions",
                    "Binomial Distribution","Poisson Distribution",
                    "Normal Distribution","Expectation and Variance",
                    "Joint Distributions","Correlation and Regression",
                    "Chi-Square Distribution","Hypothesis Testing",
                    "t-Test and F-Test","Sampling Theory"
                ]
            },
            "numerical": {
                "label": "Numerical Methods",
                "subtopics": [
                    "Errors and Approximations","Bisection Method",
                    "Regula-Falsi Method","Newton-Raphson Method",
                    "Newton's Forward Interpolation","Newton's Backward Interpolation",
                    "Lagrange Interpolation","Numerical Differentiation",
                    "Trapezoidal Rule","Simpson's 1/3 Rule","Simpson's 3/8 Rule",
                    "Euler's Method for ODEs","Runge-Kutta Method (RK4)"
                ]
            },
            "transforms": {
                "label": "Transform Theory",
                "subtopics": [
                    "Fourier Integral Theorem","Fourier Transform",
                    "Fourier Sine and Cosine Transforms",
                    "Convolution Theorem for Fourier","Z-Transform Definition",
                    "Z-Transform Properties","Inverse Z-Transform",
                    "Solution of Difference Equations"
                ]
            }
        }
    }
}

# ══════════════════════════════════════════════════════════════
#  HARDCODED REFERENCES
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
#  SUBJECT CONNECTIONS MAP — hardcoded, never AI-generated
#  Shows exactly which engineering subjects use each math topic
# ══════════════════════════════════════════════════════════════
SUBJECT_CONNECTIONS = {
    "diff_calc": {
        "connections": [
            {"subject": "Engineering Mechanics", "semester": "Sem 1–2", "how": "Velocity and acceleration as derivatives of displacement. Newton's second law in differential form.", "example": "Finding maximum range of a projectile using $dR/d\\theta = 0$"},
            {"subject": "Thermodynamics", "semester": "Sem 2–3", "how": "Rate of change of temperature, pressure, and entropy. Partial derivatives for thermodynamic potentials.", "example": "Joule-Thomson coefficient $\\mu_{JT} = (\\partial T/\\partial P)_H$"},
            {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "Instantaneous current as derivative of charge. Voltage across inductor $v = L\\,di/dt$.", "example": "Transient analysis: finding $di/dt$ at $t=0^+$ when switch closes"},
            {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Velocity gradient, strain rate, and viscosity. Bernoulli's equation derivation.", "example": "Shear stress $\\tau = \\mu\\,du/dy$ in viscous flow"},
            {"subject": "Control Systems", "semester": "Sem 4–5", "how": "Transfer function derivation. Sensitivity analysis using derivatives.", "example": "Gain margin and phase margin calculations"}
        ]
    },
    "partial_diff": {
        "connections": [
            {"subject": "Heat Transfer", "semester": "Sem 3–4", "how": "Heat equation $\\partial T/\\partial t = \\alpha\\,\\nabla^2 T$ is a PDE in temperature.", "example": "Steady-state temperature in a 2D plate"},
            {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Continuity equation, Navier-Stokes equations — all PDEs with partial derivatives.", "example": "Velocity field $u(x,y,t)$ satisfying incompressibility $\\partial u/\\partial x + \\partial v/\\partial y = 0$"},
            {"subject": "Electromagnetics", "semester": "Sem 3–4", "how": "Maxwell's equations are PDEs. Electric and magnetic fields described by partial derivatives.", "example": "Wave equation $\\nabla^2 E = \\mu\\epsilon\\,\\partial^2 E/\\partial t^2$"},
            {"subject": "Thermodynamics", "semester": "Sem 2–3", "how": "Maxwell relations use mixed partial derivatives of thermodynamic potentials.", "example": "$(\\partial S/\\partial V)_T = (\\partial P/\\partial T)_V$"},
            {"subject": "Structural Analysis", "semester": "Sem 3–4", "how": "Beam deflection equations. Stress-strain relationships in 2D.", "example": "Plate bending equation involves $\\partial^4 w/\\partial x^4$"}
        ]
    },
    "integral_calc": {
        "connections": [
            {"subject": "Engineering Mechanics", "semester": "Sem 1–2", "how": "Centre of mass, moment of inertia, work done by variable force — all integrals.", "example": "Moment of inertia $I = \\int r^2\\,dm$ for rotating bodies"},
            {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "Energy stored in capacitor $E = \\int v\\,i\\,dt$. RMS value of AC signals.", "example": "Charge $q = \\int_0^T i(t)\\,dt$ on a capacitor"},
            {"subject": "Signals and Systems", "semester": "Sem 3–4", "how": "Convolution integral, energy and power of signals, area under waveforms.", "example": "Output $y(t) = \\int_{-\\infty}^{\\infty} x(\\tau)h(t-\\tau)\\,d\\tau$"},
            {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Flow rate, pressure force on surfaces, buoyancy — all surface and volume integrals.", "example": "Volume flow rate $Q = \\int\\int \\vec{v}\\cdot d\\vec{A}$"},
            {"subject": "Heat Transfer", "semester": "Sem 3–4", "how": "Total heat transfer, temperature distribution by integrating heat equation.", "example": "Total heat $Q = \\int_0^L kA\\,(dT/dx)\\,dx$"}
        ]
    },
    "infinite_series": {
        "connections": [
            {"subject": "Signals and Systems", "semester": "Sem 3–4", "how": "Fourier series expresses periodic signals as infinite trigonometric series.", "example": "Square wave decomposed into $\\sum (1/n)\\sin(n\\omega_0 t)$"},
            {"subject": "Numerical Methods", "semester": "Sem 4", "how": "Taylor series is the basis of every numerical approximation — Euler method, RK4, Newton-Raphson.", "example": "Newton-Raphson uses $f(x+h) \\approx f(x) + hf'(x)$"},
            {"subject": "Digital Communications", "semester": "Sem 5–6", "how": "Channel capacity and coding theory use series expansions.", "example": "Shannon entropy as a series $H = -\\sum p_i\\log p_i$"},
            {"subject": "Control Systems", "semester": "Sem 4–5", "how": "Bode plot approximations use series. Stability analysis uses Laurent series.", "example": "Gain approximation near corner frequency"}
        ]
    },
    "linear_algebra": {
        "connections": [
            {"subject": "Structural Analysis", "semester": "Sem 3–4", "how": "Stiffness matrix method — entire analysis is a system of linear equations $[K]\\{u\\} = \\{F\\}$.", "example": "Truss analysis: solving for 20 unknown forces using matrix methods"},
            {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "Mesh analysis and node analysis give systems of linear equations. Network matrices.", "example": "KVL gives $[Z][I] = [V]$ — solved using matrix inverse"},
            {"subject": "Control Systems", "semester": "Sem 4–5", "how": "State-space representation $\\dot{x} = Ax + Bu$. Eigenvalues determine system stability.", "example": "System stable iff all eigenvalues of $A$ have negative real parts"},
            {"subject": "Machine Learning", "semester": "Sem 6+", "how": "Linear regression, PCA, neural networks — all built on linear algebra.", "example": "Principal components are eigenvectors of the covariance matrix"},
            {"subject": "Image Processing", "semester": "Sem 5–6", "how": "Image transformations, filtering, compression using matrix operations.", "example": "SVD used for image compression: $A = U\\Sigma V^T$"},
            {"subject": "Quantum Mechanics", "semester": "Sem 5+", "how": "Quantum states are vectors, observables are matrices, measurements are eigenvalues.", "example": "Energy levels from eigenvalues of Hamiltonian matrix $H\\psi = E\\psi$"}
        ]
    },
    "ode_first": {
        "connections": [
            {"subject": "Electrical Circuits", "semester": "Sem 2", "how": "RC and RL circuits give first-order ODEs. Natural and forced response.", "example": "RC circuit: $R\\,dq/dt + q/C = V(t)$"},
            {"subject": "Engineering Mechanics", "semester": "Sem 1–2", "how": "Newton's second law for variable forces gives first-order ODEs.", "example": "Projectile with air resistance: $m\\,dv/dt = mg - kv$"},
            {"subject": "Chemical Engineering", "semester": "Sem 3–4", "how": "Reaction kinetics, mixing problems, chemical reactor design.", "example": "First-order reaction: $dC/dt = -kC$"},
            {"subject": "Biomedical Engineering", "semester": "Sem 4+", "how": "Drug concentration in blood, population models, epidemic spread.", "example": "Drug decay: $dC/dt = -\\lambda C$ giving exponential washout"}
        ]
    },
    "ode_higher": {
        "connections": [
            {"subject": "Electrical Circuits", "semester": "Sem 2–3", "how": "RLC circuits give second-order ODEs. Natural frequency, damping ratio.", "example": "Series RLC: $L\\,d^2q/dt^2 + R\\,dq/dt + q/C = V(t)$"},
            {"subject": "Mechanical Vibrations", "semester": "Sem 3–4", "how": "Every vibrating system is a second-order ODE. Free, forced, damped vibrations.", "example": "Mass-spring-damper: $m\\ddot{x} + c\\dot{x} + kx = F(t)$"},
            {"subject": "Structural Analysis", "semester": "Sem 3–4", "how": "Beam deflection equation is a fourth-order ODE.", "example": "Euler-Bernoulli beam: $EI\\,d^4y/dx^4 = w(x)$"},
            {"subject": "Control Systems", "semester": "Sem 4–5", "how": "System response described by ODEs. Second-order system response — overshoot, settling time.", "example": "Standard second-order: $\\ddot{y} + 2\\zeta\\omega_n\\dot{y} + \\omega_n^2 y = \\omega_n^2 u$"}
        ]
    },
    "laplace": {
        "connections": [
            {"subject": "Control Systems", "semester": "Sem 4–5", "how": "Transfer function $G(s) = Y(s)/U(s)$ is the Laplace transform of the impulse response. Entire control design works in s-domain.", "example": "PID controller design: $C(s) = K_p + K_i/s + K_d s$"},
            {"subject": "Electrical Circuits", "semester": "Sem 3", "how": "Impedance in s-domain: $Z_L = sL$, $Z_C = 1/(sC)$. Circuit analysis becomes algebra.", "example": "Voltage divider in s-domain: no differential equations needed"},
            {"subject": "Signals and Systems", "semester": "Sem 3–4", "how": "System analysis using poles and zeros. Stability from pole locations.", "example": "System stable iff all poles have negative real parts (left half s-plane)"},
            {"subject": "Digital Signal Processing", "semester": "Sem 5", "how": "Z-transform is the discrete-time equivalent of Laplace transform.", "example": "Relationship $z = e^{sT}$ connects s-domain to z-domain"},
            {"subject": "Communications", "semester": "Sem 4–5", "how": "Modulation, filtering, channel analysis all use Laplace and Fourier transforms.", "example": "Bandwidth of AM signal computed from Laplace transform of pulse"}
        ]
    },
    "vector_calc": {
        "connections": [
            {"subject": "Electromagnetics", "semester": "Sem 3–4", "how": "Maxwell's equations written entirely in vector calculus: $\\nabla\\cdot\\vec{E} = \\rho/\\epsilon_0$, $\\nabla\\times\\vec{B} = \\mu_0\\vec{J}$.", "example": "Gauss's law in differential form $\\nabla\\cdot\\vec{E} = \\rho/\\epsilon_0$"},
            {"subject": "Fluid Mechanics", "semester": "Sem 3", "how": "Velocity field, vorticity $\\vec{\\omega} = \\nabla\\times\\vec{v}$, continuity equation $\\nabla\\cdot\\vec{v} = 0$.", "example": "Irrotational flow: $\\nabla\\times\\vec{v} = 0$ implies potential function exists"},
            {"subject": "Heat Transfer", "semester": "Sem 3–4", "how": "Heat flux vector, Fourier's law $\\vec{q} = -k\\nabla T$, divergence theorem for energy balance.", "example": "Heat equation derived from $\\nabla\\cdot\\vec{q} = -\\rho c_p\\,\\partial T/\\partial t$"},
            {"subject": "Structural Mechanics", "semester": "Sem 3–4", "how": "Stress and strain tensors, displacement fields, virtual work principle.", "example": "Strain energy $U = \\int\\int\\int \\sigma_{ij}\\epsilon_{ij}\\,dV$"}
        ]
    },
    "complex_analysis": {
        "connections": [
            {"subject": "Electrical Circuits", "semester": "Sem 2–3", "how": "Phasors are complex numbers. Impedance $Z = R + jX$. Power factor.", "example": "AC analysis: $V = IZ$ where all quantities are complex"},
            {"subject": "Control Systems", "semester": "Sem 4–5", "how": "Nyquist plot uses complex frequency response. Root locus in complex s-plane.", "example": "Nyquist stability criterion uses contour integration in s-plane"},
            {"subject": "Signals and Systems", "semester": "Sem 3–4", "how": "Frequency response $H(j\\omega)$ is complex. Magnitude and phase from complex analysis.", "example": "Bode plot: magnitude $|H(j\\omega)|$ and phase $\\angle H(j\\omega)$"},
            {"subject": "Electromagnetics", "semester": "Sem 3–4", "how": "Complex permittivity, wave propagation with complex wave number.", "example": "Skin depth from imaginary part of complex propagation constant"}
        ]
    },
    "fourier_series": {
        "connections": [
            {"subject": "Signals and Systems", "semester": "Sem 3–4", "how": "Every periodic signal is a Fourier series. Frequency spectrum, harmonics, bandwidth.", "example": "Square wave: $x(t) = \\sum_{n=odd} (4/n\\pi)\\sin(n\\omega_0 t)$"},
            {"subject": "Communications", "semester": "Sem 4–5", "how": "Modulation analysis, channel bandwidth, frequency division multiplexing.", "example": "AM signal spectrum analysis using Fourier series"},
            {"subject": "Digital Signal Processing", "semester": "Sem 5", "how": "DFT and FFT are the discrete versions of Fourier series. Spectral analysis.", "example": "FFT computes N-point DFT in $O(N\\log N)$ instead of $O(N^2)$"},
            {"subject": "Mechanical Vibrations", "semester": "Sem 3–4", "how": "Periodic forcing functions expanded as Fourier series. Resonance at harmonics.", "example": "Engine vibration: response at each harmonic of rotation frequency"}
        ]
    },
    "probability": {
        "connections": [
            {"subject": "Communications", "semester": "Sem 4–5", "how": "Bit error rate, noise analysis, channel capacity — all probability.", "example": "BER for BPSK: $P_e = Q(\\sqrt{2E_b/N_0})$"},
            {"subject": "Reliability Engineering", "semester": "Sem 5–6", "how": "Failure probability, MTTF, reliability function, hazard rate.", "example": "Exponential failure: $R(t) = e^{-\\lambda t}$"},
            {"subject": "Control Systems", "semester": "Sem 5", "how": "Stochastic control, Kalman filter uses probability and statistics.", "example": "Kalman filter optimal gain minimises mean square error"},
            {"subject": "Machine Learning", "semester": "Sem 6+", "how": "Bayesian inference, naive Bayes classifier, probabilistic graphical models.", "example": "Bayes classifier: $P(C|x) \\propto P(x|C)P(C)$"},
            {"subject": "Quality Control", "semester": "Sem 5–6", "how": "Statistical process control, acceptance sampling, Six Sigma.", "example": "Control chart limits set at $\\mu \\pm 3\\sigma$"}
        ]
    },
    "numerical": {
        "connections": [
            {"subject": "Computer Science / Programming", "semester": "Sem 2+", "how": "Every numerical method is implemented as an algorithm. Root finding, interpolation, ODE solvers in Python/MATLAB.", "example": "scipy.integrate.odeint implements RK4 for ODEs"},
            {"subject": "Structural Analysis", "semester": "Sem 3–4", "how": "Finite Element Method is numerical integration and matrix assembly.", "example": "FEM mesh: each element uses numerical integration for stiffness matrix"},
            {"subject": "Fluid Mechanics", "semester": "Sem 4–5", "how": "Computational Fluid Dynamics solves Navier-Stokes numerically.", "example": "Finite difference discretisation of $\\partial u/\\partial t + u\\,\\partial u/\\partial x = 0$"},
            {"subject": "Heat Transfer", "semester": "Sem 4", "how": "Numerical solution of heat equation when analytical solution is impossible.", "example": "Crank-Nicolson scheme for transient heat conduction"}
        ]
    },
    "transforms": {
        "connections": [
            {"subject": "Digital Signal Processing", "semester": "Sem 5", "how": "Z-transform is fundamental to DSP. Filter design, stability analysis of digital filters.", "example": "Digital filter $H(z) = Y(z)/X(z)$ — poles must be inside unit circle"},
            {"subject": "Communications", "semester": "Sem 4–5", "how": "Fourier transform gives frequency spectrum of non-periodic signals. Bandwidth calculation.", "example": "Bandwidth of sinc pulse $= 1/T$ Hz from its Fourier transform"},
            {"subject": "Control Systems", "semester": "Sem 5", "how": "Discrete-time control uses Z-transform exactly as continuous uses Laplace.", "example": "Digital PID controller designed in z-domain"},
            {"subject": "Image Processing", "semester": "Sem 5–6", "how": "2D Fourier transform for image filtering, edge detection, compression.", "example": "JPEG compression uses Discrete Cosine Transform (variant of Fourier)"}
        ]
    }
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
- College exam level only — not JEE, not GATE, not competitive. Semester exam standard.
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
#  PROMPTS
# ══════════════════════════════════════════════════════════════
def build_learn_prompt(topic_key, subtopic, section):
    sections = {
        "definition": f"""Give the complete formal definition of {subtopic} for engineering mathematics.

DEFINITION:
[Precise mathematical definition. Every symbol explained.]

INTUITION:
[1-2 sentences: what this concept physically or geometrically means to an engineer]

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
[Full name]

STATEMENT:
[Precise mathematical statement]

CONDITIONS:
[Hypothesis — what must be true]

PROOF:
[Complete step-by-step proof. Every equation on its own line as $$...$$]

GEOMETRIC MEANING:
[What the theorem says visually or physically]

COROLLARY:
[Important results that follow]
""",
        "examples": f"""Provide 5 fully worked examples on {subtopic} at engineering university examination level.

For EACH example:

EXAMPLE [N] — [Easy/Medium/Hard]:
[State the problem clearly]

SOLUTION:
[Complete step-by-step. Every equation as $$...$$. No steps skipped.]

FINAL ANSWER:
$$[answer]$$

KEY TECHNIQUE USED:
[Name the exact method]

COMMON MISTAKE TO AVOID:
[One typical error students make]

Cover: 2 easy, 2 medium, 1 hard.
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
[One line pointing in the right direction]

ANSWER:
$$[final answer only]$$

University examination style — Mumbai University / VTU / Anna University pattern.
"""
    }
    return ENG_CONTEXT + "\n" + ENG_FORMAT + "\n\n" + sections.get(section, sections["definition"])

def build_revision_prompt(topic_key, subtopic):
    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Give a comprehensive quick revision summary of {subtopic} for engineering examination.
Bullet points only — no lengthy explanations.

KEY FORMULAS:
[Every important formula. Each on its own line as $$...$$]

IMPORTANT RESULTS:
- [Result 1]
- [Result 2]
- [Result 3]

STANDARD RESULTS TO MEMORISE:
[5-8 results that appear most frequently in university examinations]
$$[formula 1]$$
$$[formula 2]$$

QUICK TRICKS:
- [Trick 1]
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
[Name each theorem and its one-line statement.]
"""

def build_pyq_prompt(topic_key, subtopic, university, difficulty):
    diff_map = {
        "easy":   "2-4 mark straightforward application",
        "medium": "4-6 mark multi-step problems",
        "hard":   "6-10 mark long answer requiring proof or derivation"
    }
    univ_map = {
        "all":    "various Indian universities (Mumbai University, VTU Bangalore, Anna University Chennai, AKTU Lucknow, Pune University, GTU Gujarat, JNTU Hyderabad)",
        "mumbai": "University of Mumbai (BE First Year)",
        "vtu":    "Visvesvaraya Technological University (VTU) Bangalore",
        "anna":   "Anna University Chennai (B.E/B.Tech)",
        "aktu":   "AKTU (Dr. APJ Abdul Kalam Technical University) Lucknow",
        "abroad": "international universities (Cambridge, MIT OCW style, University of Toronto examination style)"
    }
    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Provide 5 previous year examination questions on {subtopic} from {univ_map.get(university, univ_map['all'])}.
Difficulty: {diff_map.get(difficulty, diff_map['medium'])}

For EACH question:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUESTION [N]:
[Exam] · [University] · [Approximate Year] · [[marks] Marks]

STATUS: CONFIRMED / REPRESENTATIVE

QUESTION TEXT:
[Full question. Every equation as $$...$$]

APPROACH:
[1-2 sentences: which technique to apply and why]

COMPLETE SOLUTION:
[Step-by-step. Every equation on its own line as $$...$$. No steps skipped.]

FINAL ANSWER:
$$[answer]$$

VERIFICATION:
[Show the check]

MARKS BREAKDOWN:
[How marks are awarded]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After all 5 questions:

TOPIC ANALYSIS:
[How frequently this appears, what types are most common]

PREPARATION STRATEGY:
- [Focus point 1]
- [Focus point 2]
- [Focus point 3]

OFFICIAL SOURCES:
Mumbai University: https://mu.ac.in
VTU: https://vtu.ac.in
Anna University: https://www.annauniv.edu
AKTU: https://aktu.ac.in

⚠ Always cross-verify with official university question papers.
"""

def build_mocktest_prompt(topic_key, subtopic, num_q, marks_each):
    total = int(num_q) * int(marks_each)
    time_min = int(num_q) * int(marks_each) * 2
    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Generate a complete mock test paper on {subtopic}.
Total questions: {num_q} | Marks per question: {marks_each} | Total: {total} marks
Time suggested: {time_min} minutes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MOCK TEST — {subtopic.upper()}
Total Marks: {total} | Time: {time_min} minutes
Instructions: Attempt ALL questions. Show complete working for full marks.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For EACH question:

QUESTION [N]: ({marks_each} Marks)
[Question with all equations as $$...$$]

Distribute difficulty: 40% easy, 40% medium, 20% hard.
Mix: direct formula application, proof-based, application-based.

After all questions:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPLETE SOLUTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SOLUTION [N]:
[Complete step-by-step. Every equation as $$...$$]
FINAL ANSWER:
$$[answer]$$
MARKS BREAKDOWN: [how {marks_each} marks are awarded]

SELF-ASSESSMENT GUIDE:
[Score ranges and what to revise if score is low.]
"""

def build_formula_booklet_prompt(topic_key, subtopic):
    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
Generate a complete, exam-ready Formula Booklet entry for {subtopic} in engineering mathematics.
This is a reference booklet — precise, complete, and exam-focused.
Format exactly as a university formula sheet.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMULA BOOKLET — {subtopic.upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For EACH formula use this EXACT structure:

FORMULA [N]: [Formula Name]

FORMULA:
$$[the complete formula]$$

PHYSICAL MEANING:
[What this formula describes in engineering — one sentence. Name the physical quantity.]

SI UNITS:
[Units of each symbol in the formula]

CONDITIONS:
[When this formula applies. Any restrictions.]

QUICK EXAMPLE:
[One numerical example showing formula in use — specific numbers, specific answer]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After all individual formulas:

STANDARD RESULTS TABLE:
[All key results in one place — each on its own line as $$...$$]

CONNECTIONS TO OTHER FORMULAS:
[How these formulas relate to each other and to other topics]

WHICH SUBJECT USES THIS:
[List engineering subjects that directly use these formulas with one example each]

EXAM QUICK REFERENCE:
- [Most frequently asked formula in exams]
- [Formula students most often forget]
- [Formula most commonly applied incorrectly]

Generate at least 8 formulas. Be complete — this is a reference document, not a summary.
"""

def build_ask_prompt(question):
    return ENG_CONTEXT + "\n" + ENG_FORMAT + f"""
A B.Tech engineering student asks: {question}

Answer at college examination level.
Show all working. Every equation on its own line as $$...$$
Include at least one worked example.
If relevant, mention which engineering subject uses this concept.
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
        return jsonify({"response": response, "source": source, "references": REFERENCES.get(topic, [])})
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
        # Return hardcoded connections for the topic
        topic_connections = SUBJECT_CONNECTIONS.get(topic, None)
        if topic_connections:
            return jsonify({
                "connections": topic_connections["connections"],
                "source": "MathSphere Engineering",
                "references": REFERENCES.get(topic, [])
            })
        # If subtopic-level connection requested, use AI
        prompt = ENG_CONTEXT + f"""
For the engineering mathematics topic: {subtopic}

Show EXACTLY how this mathematics topic is used across different engineering subjects.
For EACH connection:

SUBJECT NAME: [Engineering subject name]
SEMESTER: [Which semester this appears]
HOW IT IS USED:
[2-3 sentences explaining the direct mathematical connection. Be specific.]
KEY FORMULA USED:
$$[the actual formula from this math topic that appears in this subject]$$
CONCRETE EXAMPLE:
[One specific problem or application from that engineering subject]

Cover at least 5 different engineering subjects.
Be specific — name actual equations, actual applications, actual engineering scenarios.
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