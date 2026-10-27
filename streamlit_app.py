import io
import os
import urllib.parse
from PIL import Image
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

# -------------------------------------------------------------------
# Page Config & Layout
# -------------------------------------------------------------------
st.set_page_config(page_title="Chrome Browser", page_icon="🌐", layout="wide")

st.markdown(
    """
<style>
    .block-container {
        padding: 0.5rem !important;
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
# Driver Setup with Resource Caching
# -------------------------------------------------------------------
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")

    # Performance & memory optimization flags
    options.page_load_strategy = "eager"  # Does not wait for full page ads/trackers
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-animations")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    for binary_path in ["/usr/bin/chromium", "/usr/bin/chromium-browser"]:
        if os.path.exists(binary_path):
            options.binary_location = binary_path
            break

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(1)
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


def capture_viewport_fast(driver) -> Image.Image:
    """Fast direct image capture without redundant double-buffering."""
    raw_png = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(raw_png))
    return img.convert("RGB") if img.mode != "RGB" else img


# -------------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------------
if "current_url" not in st.session_state:
    st.session_state.current_url = driver.current_url

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
# Keyboard & Scroll Tools
# -------------------------------------------------------------------
with st.expander("⌨️ Keyboard & Scroll Tools"):
    k_col1, k_col2, k_col3, k_col4 = st.columns([4, 1, 1, 1])

    with k_col1:
        typed_text = st.text_input(
            "Type text into focused element:",
            key="type_box",
            placeholder="Click an element on screen, then type here...",
            label_visibility="collapsed",
        )

    with k_col2:
        if st.button("Send Keys", use_container_width=True):
            if typed_text:
                active_el = driver.switch_to.active_element
                active_el.send_keys(typed_text)
                active_el.send_keys(Keys.ENTER)
                st.session_state.current_url = driver.current_url
                st.rerun()

    with k_col3:
        if st.button("⬆️ Scroll Up", use_container_width=True):
            driver.execute_script("window.scrollBy(0, -400);")
            st.rerun()

    with k_col4:
        if st.button("⬇️ Scroll Down", use_container_width=True):
            driver.execute_script("window.scrollBy(0, 400);")
            st.rerun()


# -------------------------------------------------------------------
# Interactive Viewport
# -------------------------------------------------------------------
img = capture_viewport_fast(driver)

coords = streamlit_image_coordinates(
    img,
    key="full_screen_viewport",
)

if coords is not None and coords != st.session_state.last_click:
    st.session_state.last_click = coords
    x, y = coords["x"], coords["y"]

    js_click_code = f"""
    var elem = document.elementFromPoint({x}, {y});
    if (elem) {{
        elem.click();
        elem.focus();
    }}
    """
    driver.execute_script(js_click_code)
    st.session_state.current_url = driver.current_url
    st.rerun()
