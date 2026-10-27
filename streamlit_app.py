import io
import os
import time
import urllib.parse
from PIL import Image
import streamlit as st

# Selenium and Headless Display Imports
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# -------------------------------------------------------------------
# Page Config & Chrome Theme Styling
# -------------------------------------------------------------------
st.set_page_config(page_title="Chrome Browser", page_icon="🌐", layout="wide")

st.markdown(
    """
<style>
    /* Chrome Dark UI Styling */
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
# Driver & Display Helpers
# -------------------------------------------------------------------
@st.cache_resource
def start_virtual_display():
    """Starts virtual frame buffer for headless Linux execution."""
    try:
        display = Display(visible=0, size=(1280, 720))
        display.start()
        return display
    except Exception:
        return None


def init_chrome_driver():
    """Initializes Selenium Chrome WebDriver."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    for binary_path in ["/usr/bin/chromium", "/usr/bin/chromium-browser"]:
        if os.path.exists(binary_path):
            options.binary_location = binary_path
            break

    return webdriver.Chrome(options=options)


def sanitize_url(raw_url: str) -> str:
    """Formats string inputs to prevent Selenium invalid argument errors."""
    url = raw_url.strip()
    if not url:
        return "https://www.google.com"
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
    return url


def capture_viewport(driver) -> Image.Image:
    """Captures screenshot from Selenium driver memory."""
    raw_png = driver.get_screenshot_as_png()
    return Image.open(io.BytesIO(raw_png))


# -------------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------------
start_virtual_display()

if "driver" not in st.session_state or st.session_state.driver is None:
    st.session_state.driver = init_chrome_driver()
    st.session_state.driver.get("https://www.google.com")

if "current_url" not in st.session_state:
    st.session_state.current_url = "https://www.google.com"

if "last_screenshot" not in st.session_state:
    st.session_state.last_screenshot = capture_viewport(
        st.session_state.driver
    )

driver = st.session_state.driver


# -------------------------------------------------------------------
# Top Chrome Navigation Bar
# -------------------------------------------------------------------
nav_back, nav_fwd, nav_ref, nav_home, nav_url, nav_go = st.columns(
    [0.4, 0.4, 0.4, 0.4, 6.5, 0.8]
)

with nav_back:
    if st.button("◀", help="Back", use_container_width=True):
        try:
            driver.back()
            time.sleep(1)
            st.session_state.current_url = driver.current_url
            st.session_state.last_screenshot = capture_viewport(driver)
            st.rerun()
        except Exception as err:
            st.error(f"Navigation error: {err}")

with nav_fwd:
    if st.button("▶", help="Forward", use_container_width=True):
        try:
            driver.forward()
            time.sleep(1)
            st.session_state.current_url = driver.current_url
            st.session_state.last_screenshot = capture_viewport(driver)
            st.rerun()
        except Exception as err:
            st.error(f"Navigation error: {err}")

with nav_ref:
    if st.button("🔄", help="Reload", use_container_width=True):
        try:
            driver.refresh()
            time.sleep(1)
            st.session_state.last_screenshot = capture_viewport(driver)
            st.rerun()
        except Exception as err:
            st.error(f"Reload error: {err}")

with nav_home:
    if st.button("🏠", help="Home", use_container_width=True):
        try:
            driver.get("https://www.google.com")
            time.sleep(1)
            st.session_state.current_url = driver.current_url
            st.session_state.last_screenshot = capture_viewport(driver)
            st.rerun()
        except Exception as err:
            st.error(f"Home navigation error: {err}")

with nav_url:
    target_url_input = st.text_input(
        "Omnibox",
        value=st.session_state.current_url,
        label_visibility="collapsed",
        placeholder="Search Google or type a URL",
    )

with nav_go:
    if st.button("Go ↵", use_container_width=True):
        clean_url = sanitize_url(target_url_input)
        try:
            driver.get(clean_url)
            time.sleep(2)
            st.session_state.current_url = driver.current_url
            st.session_state.last_screenshot = capture_viewport(driver)
            st.rerun()
        except Exception as err:
            st.error(f"Failed to navigate: {err}")


# -------------------------------------------------------------------
# Interactive Sidebar & Viewport Layout
# -------------------------------------------------------------------
col_tools, col_view = st.columns([1, 3.2])

with col_tools:
    st.subheader("🖱️ Interact")

    # 1. Coordinate Clicker
    st.markdown("**Click Coordinates**")
    click_x = st.number_input(
        "X Pos (px):", min_value=0, max_value=1280, value=640, step=10
    )
    click_y = st.number_input(
        "Y Pos (px):", min_value=0, max_value=720, value=360, step=10
    )

    if st.button("🎯 Click Viewport", use_container_width=True):
        try:
            # Inject click into the DOM element at specified coordinates
            js_click = f"""
            var el = document.elementFromPoint({click_x}, {click_y});
            if (el) {{
                el.click();
                el.focus();
            }}
            """
            driver.execute_script(js_click)
            time.sleep(1.5)
            st.session_state.current_url = driver.current_url
            st.session_state.last_screenshot = capture_viewport(driver)
            st.rerun()
        except Exception as err:
            st.error(f"Click error: {err}")

    st.divider()

    # 2. Text Input
    st.markdown("**Type Text**")
    text_input_val = st.text_input(
        "Text to send:", placeholder="Type search query or text..."
    )
    send_enter_key = st.checkbox("Press Enter key", value=True)

    if st.button("⌨️ Send Keys", use_container_width=True):
        try:
            active_element = driver.switch_to.active_element
            active_element.send_keys(text_input_val)
            if send_enter_key:
                active_element.send_keys(Keys.ENTER)
            time.sleep(1.5)
            st.session_state.current_url = driver.current_url
            st.session_state.last_screenshot = capture_viewport(driver)
            st.rerun()
        except Exception as err:
            st.error(f"Typing error: {err}")

    st.divider()

    # 3. Scroll Page
    st.markdown("**Scroll Viewport**")
    col_sc1, col_sc2 = st.columns(2)
    with col_sc1:
        if st.button("⬆️ Scroll Up", use_container_width=True):
            driver.execute_script("window.scrollBy(0, -400);")
            time.sleep(0.5)
            st.session_state.last_screenshot = capture_viewport(driver)
            st.rerun()
    with col_sc2:
        if st.button("⬇️ Scroll Down", use_container_width=True):
            driver.execute_script("window.scrollBy(0, 400);")
            time.sleep(0.5)
            st.session_state.last_screenshot = capture_viewport(driver)
            st.rerun()

with col_view:
    if st.session_state.last_screenshot:
        st.image(
            st.session_state.last_screenshot,
            caption=f"Selenium Active Viewport: {driver.current_url}",
            use_container_width=True,
        )
