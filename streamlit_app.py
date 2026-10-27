import io
import os
import urllib.parse
from PIL import Image
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from playwright.sync_api import sync_playwright

# -------------------------------------------------------------------
# Page Config & Layout
# -------------------------------------------------------------------
st.set_page_config(page_title="Playwright Browser", page_icon="🌐", layout="wide")

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
# Fast Playwright Engine Setup
# -------------------------------------------------------------------
@st.cache_resource
def get_browser_context():
    p = sync_playwright().start()

    # Use Linux system Chromium installed via packages.txt
    binary_path = "/usr/bin/chromium"
    if not os.path.exists(binary_path):
        binary_path = "/usr/bin/chromium-browser"

    browser = p.chromium.launch(
        executable_path=binary_path if os.path.exists(binary_path) else None,
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1024,576",
        ],
    )

    context = browser.new_context(viewport={"width": 1024, "height": 576})
    page = context.new_page()

    # Block heavy fonts, media files, and background bloat
    page.route(
        "**/*.{woff,woff2,ttf,mp4,webm,m3u8}", lambda route: route.abort()
    )
    page.goto("https://www.google.com")
    return page


page = get_browser_context()


def sanitize_url(raw_url: str) -> str:
    url = raw_url.strip()
    if not url:
        return "https://www.google.com"
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
    return url


def capture_viewport(page) -> Image.Image:
    """Low-latency native Playwright JPEG screenshot."""
    screenshot_bytes = page.screenshot(type="jpeg", quality=45)
    return Image.open(io.BytesIO(screenshot_bytes))


# -------------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------------
if "current_url" not in st.session_state:
    st.session_state.current_url = page.url

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
        page.go_back()
        st.session_state.current_url = page.url
        st.rerun()

with nav_fwd:
    if st.button("▶", help="Forward", use_container_width=True):
        page.go_forward()
        st.session_state.current_url = page.url
        st.rerun()

with nav_ref:
    if st.button("🔄", help="Reload", use_container_width=True):
        page.reload()
        st.rerun()

with nav_home:
    if st.button("🏠", help="Home", use_container_width=True):
        page.goto("https://www.google.com")
        st.session_state.current_url = page.url
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
        page.goto(clean_url)
        st.session_state.current_url = page.url
        st.rerun()


# -------------------------------------------------------------------
# Direct Typing Handler (Triggers instantly on Enter)
# -------------------------------------------------------------------
def send_text_to_page():
    typed_value = st.session_state.get("direct_type_input", "")
    if typed_value:
        page.keyboard.type(typed_value)
        page.keyboard.press("Enter")
        st.session_state["direct_type_input"] = ""
        st.session_state.current_url = page.url


st.text_input(
    "⌨️ Direct Type Bar",
    key="direct_type_input",
    placeholder="Click any input field on the screen below, type here, and hit Enter...",
    on_change=send_text_to_page,
    label_visibility="collapsed",
)


# -------------------------------------------------------------------
# Interactive Viewport
# -------------------------------------------------------------------
@st.fragment
def render_viewport():
    img = capture_viewport(page)

    coords = streamlit_image_coordinates(
        img,
        key="full_screen_viewport",
    )

    if coords is not None and coords != st.session_state.last_click:
        st.session_state.last_click = coords
        x, y = coords["x"], coords["y"]

        # Native Playwright click at exact pixel coordinates
        page.mouse.click(x, y)
        st.session_state.current_url = page.url
        st.rerun()


render_viewport()
