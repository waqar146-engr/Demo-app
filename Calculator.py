"""
Scientific Calculator — Streamlit GUI
-------------------------------------
Keyboard + mouse input.
Run with:   streamlit run calculator.py
"""

import html
import inspect
import math
import re

import streamlit as st
import streamlit.components.v1 as components

# ============================================================================
# 1. PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Welcome to my Scientific Calculator",
    page_icon="🧮",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# 2. STYLING  (LCD screen + calculator keypad)
# ============================================================================
st.markdown(
    """
    <style>
        .block-container { max-width: 640px; padding-top: 2.2rem; }

        /* ---------- Title ---------- */
        .calc-title {
            text-align: center;
            font-family: "Segoe UI", sans-serif;
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: .5px;
            color: #1f2937;
            margin-top: .4rem;
            margin-bottom: 1rem;
            line-height: 1.3;
        }
        .calc-title .by {
            display: block;
            font-size: 0.98rem;
            font-weight: 500;
            color: #7fb894;
            margin-top: 6px;
            letter-spacing: 1.4px;
            text-transform: uppercase;
        }

        /* ---------- LCD SCREEN ---------- */
        .lcd {
            background: radial-gradient(circle at 25% 0%, #123425 0%, #08130d 70%);
            border: 3px solid #24402f;
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 18px;
            font-family: "Courier New", ui-monospace, monospace;
            text-align: right;
            overflow: hidden;
            box-shadow: inset 0 0 22px rgba(0, 255, 140, .10),
                        0 8px 22px rgba(0, 0, 0, .50);
        }
        .lcd .expr {
            color: #6fe0a4;
            font-size: 1.05rem;
            min-height: 1.5em;
            opacity: .80;
            word-wrap: break-word;
            word-break: break-all;
        }
        .lcd .result {
            color: #c6ffdd;
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1.25;
            min-height: 1.3em;
            word-wrap: break-word;
            word-break: break-all;
            text-shadow: 0 0 12px rgba(0, 255, 140, .55);
        }

        /* ---------- BUTTONS ---------- */
        .stButton > button {
            width: 100%;
            height: 54px;
            border-radius: 12px;
            font-size: 1.02rem;
            font-weight: 600;
            color: #e6edf3;
            background: linear-gradient(180deg, #1b2733 0%, #141d26 100%);
            border: 1px solid #2b3d4d;
            box-shadow: 0 2px 0 #0d141b, 0 3px 8px rgba(0, 0, 0, .35);
            transition: all .10s ease;
        }
        .stButton > button:hover {
            background: linear-gradient(180deg, #24374a 0%, #1a2632 100%);
            border-color: #3f6b8f;
            color: #ffffff;
        }
        .stButton > button:active { transform: translateY(1px) scale(.98); }
        .stButton > button:focus:not(:active) {
            color: #e6edf3; border-color: #3f6b8f;
        }

        /* "=" key */
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(180deg, #1f9d63 0%, #147a4a 100%);
            border-color: #27c07a;
            color: #ffffff;
        }
        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="stBaseButton-primary"]:hover {
            background: linear-gradient(180deg, #25b873 0%, #178a54 100%);
        }

        /* tighter keypad grid */
        div[data-testid="stHorizontalBlock"] { gap: .45rem; }
        div[data-testid="stVerticalBlock"]  { gap: .45rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# 3. HEADING
# ============================================================================
st.markdown(
    '<div class="calc-title">🧮 Scientific Calculator'
    '<span class="by">by Waqar Ahmed</span></div>',
    unsafe_allow_html=True,
)

# ============================================================================
# 4. KEYBOARD SUPPORT
#    Injects a listener into the parent Streamlit document.
#    When a key is pressed, it clicks the matching on-screen button.
# ============================================================================
components.html(
    """
    <script>
    (function () {
        const parentWin = window.parent;
        if (parentWin.__calcKeyboardAttached) return;   // attach only once
        parentWin.__calcKeyboardAttached = true;

        // key  ->  exact label of the button to click
        const KEY_MAP = {
            "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
            "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
            ".": ".",  ",": ".",
            "+": "+",  "-": "−",  "*": "×",  "x": "×",  "/": "÷",
            "(": "(",  ")": ")",
            "^": "xʸ", "!": "n!",
            "=": "=",  "Enter": "=",
            "Backspace": "DEL",
            "Escape": "AC",  "Delete": "AC",
            "p": "π"
        };

        parentWin.document.addEventListener("keydown", function (e) {
            // Do not hijack typing inside real inputs / textareas
            const t = e.target;
            if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA"
                      || t.isContentEditable)) return;
            // Ignore when modifier keys are held (Ctrl+C, Cmd+R, etc.)
            if (e.ctrlKey || e.metaKey || e.altKey) return;

            const label = KEY_MAP[e.key];
            if (!label) return;

            const buttons = parentWin.document.querySelectorAll("button");
            for (const btn of buttons) {
                const text = (btn.innerText || "").trim();
                if (text === label) {
                    e.preventDefault();
                    btn.click();
                    return;
                }
            }
        });
    })();
    </script>
    """,
    height=0,
)

# ============================================================================
# 5. SESSION STATE
# ============================================================================
_DEFAULTS = {"expr": "", "result": "0", "angle": "DEG", "fresh": False}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ============================================================================
# 6. MATH ENGINE  (safe evaluation of the typed expression)
# ============================================================================
_IMPLICIT_MUL = re.compile(
    r"(?<=[\d\)])(?=(?:pi|sqrt|sin|cos|tan|asin|acos|atan|ln|log|exp|abs|fact|e|\())"
)


def _make_namespace(degrees: bool) -> dict:
    """Build the whitelist of names the expression is allowed to use."""
    to_rad = math.radians if degrees else (lambda x: x)
    from_rad = math.degrees if degrees else (lambda x: x)

    def _fact(n):
        n = float(n)
        if n < 0 or n != int(n) or n > 170:
            raise ValueError("invalid factorial")
        return math.factorial(int(n))

    return {
        "__builtins__": {},                     # <-- no builtins = no file/system access
        "pi": math.pi,
        "e": math.e,
        "sqrt": math.sqrt,
        "abs": abs,
        "exp": math.exp,
        "ln": math.log,                         # natural log
        "log": math.log10,                      # base-10 log
        "sin": lambda x: math.sin(to_rad(x)),
        "cos": lambda x: math.cos(to_rad(x)),
        "tan": lambda x: math.tan(to_rad(x)),
        "asin": lambda x: from_rad(math.asin(x)),
        "acos": lambda x: from_rad(math.acos(x)),
        "atan": lambda x: from_rad(math.atan(x)),
        "fact": _fact,
        "pow": pow,
    }


def _expand_factorials(s: str) -> str:
    """Turn  '5!'  ->  'fact(5)'  and  '(2+3)!'  ->  'fact((2+3))'."""
    while "!" in s:
        i = s.index("!")
        j = i - 1
        if j < 0:
            raise ValueError("dangling '!'")

        if s[j] == ")":                                   # walk back to the matching "("
            depth = 0
            while j >= 0:
                if s[j] == ")":
                    depth += 1
                elif s[j] == "(":
                    depth -= 1
                    if depth == 0:
                        break
                j -= 1
            if j < 0:
                raise ValueError("unbalanced parentheses")
            k = j - 1                                     # include a leading function name
            while k >= 0 and s[k].isalpha():
                k -= 1
            j = k + 1
        else:                                             # plain number
            while j >= 0 and (s[j].isdigit() or s[j] == "."):
                j -= 1
            j += 1
            if j == i:
                raise ValueError("dangling '!'")

        s = s[:j] + "fact(" + s[j:i] + ")" + s[i + 1:]
    return s


def _to_python(expr: str) -> str:
    """Translate the pretty display syntax into valid Python."""
    s = expr
    s = s.replace("×", "*").replace("÷", "/")
    s = s.replace("−", "-").replace("–", "-")     # U+2212 / en-dash
    s = s.replace("π", "pi").replace("√", "sqrt")
    s = s.replace("^", "**")
    s = _expand_factorials(s)
    s = _IMPLICIT_MUL.sub("*", s)                 # 2π -> 2*pi , 3(4) -> 3*(4)
    return s


def _format(value) -> str:
    """Human-friendly number formatting."""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return "Error"
        if value.is_integer() and abs(value) < 1e15:
            return str(int(value))
        if value != 0 and (abs(value) >= 1e15 or abs(value) < 1e-9):
            return f"{value:.8e}"
        return f"{value:.10g}"
    if isinstance(value, complex):
        return f"{value.real:.10g}{value.imag:+.10g}j"
    return str(value)


def evaluate(expr: str) -> str:
    """Evaluate a display expression and return a display string."""
    if not expr.strip():
        return "0"
    if "_" in expr:                       # block dunder / attribute tricks
        return "Error"
    try:
        py_expr = _to_python(expr)
        value = eval(py_expr, _make_namespace(st.session_state.angle == "DEG"))  # noqa: S307
    except Exception:
        return "Error"
    try:
        return _format(value)
    except Exception:
        return "Error"




# ============================================================================
# 7. KEY HANDLERS
# ============================================================================
def on_press(label: str) -> None:
    """Single callback used by every key on the pad."""
    ss = st.session_state

    # --- control keys -------------------------------------------------------
    if label == "AC":
        ss.expr, ss.result, ss.fresh = "", "0", False
        return

    if label == "DEL":
        ss.expr = ss.expr[:-1]
        ss.fresh = False
        return

    if label == "=":
        if ss.expr.strip():
            ss.result = evaluate(ss.expr)
            ss.fresh = True
        return

    # --- any other key starts a brand-new calculation after "=" ------------
    if ss.fresh:
        ss.expr, ss.fresh = "", False

    # --- special keys -------------------------------------------------------
    if label == "x²":
        ss.expr += "^2"
    elif label == "xʸ":
        ss.expr += "^"
    elif label == "√":
        ss.expr += "√("
    elif label == "1/x":
        ss.expr = f"1/({ss.expr})" if ss.expr else "1/("
    elif label == "n!":
        ss.expr += "!"
    elif label == "±":
        if ss.expr.startswith(("−", "-")):
            ss.expr = ss.expr[1:]
        else:
            ss.expr = "−" + ss.expr
    elif label in ("exp", "abs", "sin", "cos", "tan", "ln", "log"):
        ss.expr += label + "("
    else:                                    # digits, ".", "(", ")", + − × ÷
        ss.expr += label


# ============================================================================
# 8. ANGLE MODE
# ============================================================================
st.radio(
    "Angle mode",
    ["DEG", "RAD"],
    key="angle",
    horizontal=True,
    label_visibility="collapsed",
)

# ============================================================================
# 9. LIVE PREVIEW + LCD RENDER
# ============================================================================
if not st.session_state.fresh:
    _live = evaluate(st.session_state.expr) if st.session_state.expr.strip() else "0"
    if _live != "Error":                 # keep the last good value while typing
        st.session_state.result = _live

_display_expr = html.escape(st.session_state.expr) if st.session_state.expr else "&nbsp;"
_display_res = html.escape(str(st.session_state.result))

st.markdown(
    f"""
    <div class="lcd">
        <div class="expr">{_display_expr}</div>
        <div class="result">{_display_res}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# 10. KEYPAD
# ============================================================================
LAYOUT = [
    ["AC",  "DEL", "(",   ")",   "÷"],
    ["sin", "cos", "tan", "ln",  "log"],
    ["√",   "x²",  "xʸ",  "π",   "e"],
    ["7",   "8",   "9",   "×",   "1/x"],
    ["4",   "5",   "6",   "−",   "n!"],
    ["1",   "2",   "3",   "+",   "±"],
    ["0",   ".",   "exp", "abs", "="],
]


def _button_kwargs() -> dict:
    """Stay compatible with both old and new Streamlit button APIs."""
    try:
        params = inspect.signature(st.button).parameters
    except (TypeError, ValueError):
        return {}
    if "width" in params:
        return {"width": "stretch"}
    if "use_container_width" in params:
        return {"use_container_width": True}
    return {}


_BTN_KW = _button_kwargs()

for row in LAYOUT:
    cols = st.columns(5, gap="small")
    for col, label in zip(cols, row):
        with col:
            extra = {"type": "primary"} if label == "=" else {}
            st.button(
                label,
                key=f"btn_{label}",
                on_click=on_press,
                args=(label,),
                **_BTN_KW,
                **extra,
            )

# ============================================================================
# 11. FOOTER
# ============================================================================
st.caption(
    "⌨️ **Keyboard shortcuts:** digits `0-9`, operators `+ - * /`, "
    "`^` power, `!` factorial, `(` `)` parentheses, `p` for π, "
    "`Enter` = equals, `Backspace` = delete, `Esc` = clear (AC).  \n"
    "**DEG/RAD** switches the trig unit · **xʸ** = power · **n!** = factorial · "
    "**1/x** = reciprocal · **±** = sign flip · implicit multiplication "
    "(`2π`, `3(4)`) is supported."
)