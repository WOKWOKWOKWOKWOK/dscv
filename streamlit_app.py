import io
import os
import urllib.parse
from PIL import Image
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# -------------------------------------------------------------------
# Page Config & Strict Fullscreen Layout (No Page Scrollbars)
# -------------------------------------------------------------------
st.set_page_config(page_title="Chrome Browser", page_icon="🌐", layout="wide")

st.markdown(
    """
<style>
    /* Lock root view to 100vh and hide window scrollbars */
    html, body, [data-testid="stAppViewContainer"], .main {
        height: 100vh !important;
        overflow: hidden !important;
    }
    .block-container {
        padding: 0.2rem 0.4rem 0rem 0.4rem !important;
        max-width: 100% !important;
        height: 100vh !important;
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
        height: 38px !important;
    }
    .stButton > button {
        border-radius: 8px !important;
        background-color: #3c4043 !important;
        color: #ffffff !important;
        border: none !important;
        height: 38px !important;
    }
    .stButton > button:hover {
        background-color: #5f6368 !important;
    }
    /* Restrain image element to viewport budget */
    div[data-testid="stImage"] img {
        width: 100% !important;
        max-height: 78vh !important;
        object-fit: contain !important;
        border-radius: 4px;
    }
</style>
""",
    unsafe_allow_html=True,
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
# Driver Setup (Fixed 1280x720 Canvas Resolution)
# -------------------------------------------------------------------
CHROME_WIDTH = 1280
CHROME_HEIGHT = 720


@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={CHROME_WIDTH},{CHROME_HEIGHT}")

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


def capture_compressed_viewport(driver) -> Image.Image:
    raw_png = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(raw_png)).convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=50, optimize=True)
    buffer.seek(0)
    return Image.open(buffer)


# -------------------------------------------------------------------
# Session State
# -------------------------------------------------------------------
if "current_url" not in st.session_state:
    try:
        st.session_state.current_url = driver.current_url
    except Exception:
        st.session_state.current_url = "https://www.google.com"

if "last_click" not in st.session_state:
    st.session_state.last_click = None


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
# Typing Input Handler
# -------------------------------------------------------------------
def handle_typing():
    typed_text = st.session_state.get("type_input_value", "")
    if typed_text:
        cdp_type_text(driver, typed_text)
        cdp_press_enter(driver)
        st.session_state["type_input_value"] = ""
        st.session_state.current_url = driver.current_url


st.text_input(
    "Typing Bar",
    key="type_input_value",
    placeholder="1. Click search box in image below  →  2. Type here  →  3. Press Enter",
    on_change=handle_typing,
    label_visibility="collapsed",
)


# -------------------------------------------------------------------
# Viewport Fragment with Dynamic Coordinate Scaling
# -------------------------------------------------------------------
@st.fragment
def render_viewport():
    img = capture_compressed_viewport(driver)

    coords = streamlit_image_coordinates(
        img,
        key="full_screen_viewport",
    )

    if coords is not None and coords != st.session_state.last_click:
        st.session_state.last_click = coords

        # Dynamic Coordinate Scaling: Converts display click position to internal Chrome coordinates
        rendered_width = coords.get("width", CHROME_WIDTH)
        rendered_height = coords.get("height", CHROME_HEIGHT)

        scale_x = CHROME_WIDTH / rendered_width
        scale_y = CHROME_HEIGHT / rendered_height

        real_x = int(coords["x"] * scale_x)
        real_y = int(coords["y"] * scale_y)

        cdp_click(driver, real_x, real_y)
        st.session_state.current_url = driver.current_url
        st.rerun()


render_viewport()
