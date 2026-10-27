import base64
import io
import os
import urllib.parse
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# -------------------------------------------------------------------
# Page Config & Styling
# -------------------------------------------------------------------
st.set_page_config(page_title="Chrome Browser", page_icon="🌐", layout="wide")

st.markdown(
    """
<style>
    .block-container {
        padding: 0.4rem !important;
        max-width: 100% !important;
    }
    header, footer {visibility: hidden;}
    .stApp {
        background-color: #202124;
        color: #e8eaed;
    }
    div[data-testid="stTextInput"] > div > div > input {
        background-color: #35363a !important;
        color: #ffffff !important;
        border-radius: 20px !important;
        border: 1px solid #5f6368 !important;
        padding-left: 15px !important;
    }
    .stButton > button {
        border-radius: 8px !important;
        background-color: #3c4043 !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #5f6368 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# -------------------------------------------------------------------
# Self-Creating Custom Component (Direct Keyboard Listener)
# -------------------------------------------------------------------
COMPONENT_DIR = os.path.join(os.path.dirname(__file__), "viewport_component")
os.makedirs(COMPONENT_DIR, exist_ok=True)
INDEX_HTML = os.path.join(COMPONENT_DIR, "index.html")

# Generates custom client-side HTML/JS component with real-time physical keyboard listeners
HTML_CONTENT = """<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@1.4.0/dist/streamlit-component-lib.js"></script>
  <style>
    body { margin: 0; padding: 0; background: #202124; overflow: hidden; font-family: sans-serif; }
    #container { position: relative; display: inline-block; cursor: crosshair; width: 100%; }
    #viewport { display: block; width: 100%; height: auto; user-select: none; }
    #hidden-input {
      position: absolute;
      top: 0; left: 0;
      opacity: 0;
      width: 1px; height: 1px;
      border: none; outline: none;
    }
  </style>
</head>
<body>
  <div id="container" tabindex="0">
    <img id="viewport" src="" />
    <input type="text" id="hidden-input" autocomplete="off" autocorrect="off" capitalize="off" spellcheck="false" />
  </div>
  <script>
    const img = document.getElementById('viewport');
    const container = document.getElementById('container');
    const hiddenInput = document.getElementById('hidden-input');

    function onRender(event) {
      const data = event.detail.args;
      if (data.image) {
        img.src = "data:image/jpeg;base64," + data.image;
      }
      Streamlit.setFrameHeight(container.offsetHeight || 576);
    }

    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
    Streamlit.setComponentReady();

    // Click handler: Captures X/Y coordinates and activates physical keyboard listener
    img.addEventListener('click', (e) => {
      const rect = img.getBoundingClientRect();
      const scaleX = 1024 / rect.width;
      const scaleY = 576 / rect.height;
      const x = Math.round((e.clientX - rect.left) * scaleX);
      const y = Math.round((e.clientY - rect.top) * scaleY);

      hiddenInput.value = '';
      hiddenInput.focus();

      Streamlit.setComponentValue({ type: 'click', x: x, y: y, ts: Date.now() });
    });

    // Keyboard listener: Intercepts physical typing and Enter keys directly on the image
    hiddenInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const textVal = hiddenInput.value;
        hiddenInput.value = '';
        Streamlit.setComponentValue({ type: 'type', text: textVal, key: 'Enter', ts: Date.now() });
      }
    });
  </script>
</body>
</html>
"""

with open(INDEX_HTML, "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)

interactive_viewport = components.declare_component(
    "interactive_viewport", path=COMPONENT_DIR
)


# -------------------------------------------------------------------
# CDP Hardware Input Dispatchers
# -------------------------------------------------------------------
def cdp_click(driver, x: int, y: int):
    driver.execute_cdp_cmd(
        "Input.dispatchMouseEvent",
        {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1},
    )
    driver.execute_cdp_cmd(
        "Input.dispatchMouseEvent",
        {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1},
    )


def cdp_type_text(driver, text: str):
    for char in text:
        driver.execute_cdp_cmd(
            "Input.dispatchKeyEvent",
            {"type": "keyDown", "text": char, "unmodifiedText": char},
        )
        driver.execute_cdp_cmd(
            "Input.dispatchKeyEvent",
            {"type": "keyUp", "text": char, "unmodifiedText": char},
        )


def cdp_press_enter(driver):
    driver.execute_cdp_cmd(
        "Input.dispatchKeyEvent",
        {
            "type": "keyDown",
            "key": "Enter",
            "code": "Enter",
            "windowsVirtualKeyCode": 13,
            "nativeVirtualKeyCode": 13,
            "text": "\r",
        },
    )
    driver.execute_cdp_cmd(
        "Input.dispatchKeyEvent",
        {
            "type": "keyUp",
            "key": "Enter",
            "code": "Enter",
            "windowsVirtualKeyCode": 13,
            "nativeVirtualKeyCode": 13,
        },
    )


# -------------------------------------------------------------------
# Browser Setup
# -------------------------------------------------------------------
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1024,576")

    options.page_load_strategy = "eager"
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-domain-reliability")
    options.add_argument("--disable-sync")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--disable-default-apps")
    options.add_argument("--mute-audio")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-notifications")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    for binary_path in ["/usr/bin/chromium", "/usr/bin/chromium-browser"]:
        if os.path.exists(binary_path):
            options.binary_location = binary_path
            break

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0.2)

    try:
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd(
            "Network.setBlockedURLs",
            {
                "urls": [
                    "*.woff2", "*.woff", "*.ttf",
                    "*.mp4", "*.webm", "*.avi", "*.m3u8",
                    "*doubleclick.net*", "*google-analytics.com*",
                    "*googlesyndication.com*", "*facebook.net*"
                ]
            },
        )
    except Exception:
        pass

    driver.get("https://www.google.com")
    return driver


driver = get_driver()


def sanitize_url(raw_url: str) -> str:
    url = raw_url.strip()
    if not url:
        return "https://www.google.com"
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
    return url


def capture_compressed_viewport_b64(driver) -> str:
    raw_png = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(raw_png)).convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=45, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# -------------------------------------------------------------------
# Session State
# -------------------------------------------------------------------
if "current_url" not in st.session_state:
    try:
        st.session_state.current_url = driver.current_url
    except Exception:
        st.session_state.current_url = "https://www.google.com"

if "last_event_ts" not in st.session_state:
    st.session_state.last_event_ts = None


# -------------------------------------------------------------------
# Top Navigation Bar
# -------------------------------------------------------------------
nav_back, nav_fwd, nav_ref, nav_home, nav_url, nav_go = st.columns(
    [0.3, 0.3, 0.3, 0.3, 7.5, 0.6]
)

with nav_back:
    if st.button("◀", help="Back", use_container_width=True):
        driver.back()
        st.session_state.current_url = driver.current_url
        st.rerun()

with nav_fwd:
    if st.button("▶", help="Forward", use_container_width=True):
        driver.forward()
        st.session_state.current_url = driver.current_url
        st.rerun()

with nav_ref:
    if st.button("🔄", help="Reload", use_container_width=True):
        driver.refresh()
        st.rerun()

with nav_home:
    if st.button("🏠", help="Home", use_container_width=True):
        driver.get("https://www.google.com")
        st.session_state.current_url = driver.current_url
        st.rerun()

with nav_url:
    target_url_input = st.text_input(
        "Omnibox",
        value=st.session_state.current_url,
        label_visibility="collapsed",
        placeholder="Search or enter URL",
    )

with nav_go:
    if st.button("Go ↵", use_container_width=True):
        clean_url = sanitize_url(target_url_input)
        driver.get(clean_url)
        st.session_state.current_url = driver.current_url
        st.rerun()


# -------------------------------------------------------------------
# Direct Interactive Viewport (Handles Clicks + Keyboard Input)
# -------------------------------------------------------------------
b64_image = capture_compressed_viewport_b64(driver)

event = interactive_viewport(image=b64_image, key="direct_screen_viewport")

if event and event.get("ts") != st.session_state.last_event_ts:
    st.session_state.last_event_ts = event.get("ts")
    event_type = event.get("type")

    if event_type == "click":
        cdp_click(driver, event["x"], event["y"])
        st.session_state.current_url = driver.current_url
        st.rerun()

    elif event_type == "type":
        text_to_send = event.get("text", "")
        if text_to_send:
            cdp_type_text(driver, text_to_send)
        if event.get("key") == "Enter":
            cdp_press_enter(driver)
        st.session_state.current_url = driver.current_url
        st.rerun()
