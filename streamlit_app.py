import os
import time
from io import BytesIO
import streamlit as st
from PIL import Image

# Third-party imports for headless browsing
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


# -------------------------------------------------------------------
# Helper: Initialize Virtual Display & Headless Chrome
# -------------------------------------------------------------------
@st.cache_resource
def start_virtual_display():
    """Starts a virtual framebuffer (Xvfb) for headlessly hosting GUI browsers."""
    try:
        display = Display(visible=0, size=(1280, 720))
        display.start()
        return display
    except Exception as e:
        st.warning(f"Virtual display initialization notice: {e}")
        return None


def get_chrome_driver():
    """Configures and returns a headless Selenium Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,720")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )

    # Check common Linux chromium binary locations on Streamlit Cloud
    possible_paths = ["/usr/bin/chromium", "/usr/bin/chromium-browser"]
    for path in possible_paths:
        if os.path.exists(path):
            chrome_options.binary_location = path
            break

    driver = webdriver.Chrome(options=chrome_options)
    return driver


# -------------------------------------------------------------------
# Streamlit UI Configuration
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Headless Web Browser Host", page_icon="🌐", layout="wide"
)

st.title("🌐 Headless Browser & Application Runner")
st.caption(
    "Running inside Streamlit Cloud Linux Container with Virtual Display"
)

# Start virtual display session
start_virtual_display()

# Session state management for browser instance
if "driver" not in st.session_state:
    st.session_state.driver = None

if "last_screenshot" not in st.session_state:
    st.session_state.last_screenshot = None

# Sidebar controls
st.sidebar.header("🕹️ Browser Controls")

target_url = st.sidebar.text_input("Enter Target URL:", value="https://example.com")

col_nav1, col_nav2 = st.sidebar.columns(2)

with col_nav1:
    if st.button("🚀 Launch / Navigate", use_container_width=True):
        with st.spinner("Opening target site..."):
            try:
                if st.session_state.driver is None:
                    st.session_state.driver = get_chrome_driver()

                st.session_state.driver.get(target_url)
                time.sleep(2)  # Allow JS and page DOM to stabilize

                # Capture screenshot
                screenshot_bytes = (
                    st.session_state.driver.get_screenshot_as_png()
                )
                st.session_state.last_screenshot = Image.open(
                    BytesIO(screenshot_bytes)
                )
                st.success("Page loaded successfully!")
            except Exception as err:
                st.error(f"Failed to load page: {err}")

with col_nav2:
    if st.button("🔄 Refresh View", use_container_width=True):
        if st.session_state.driver:
            screenshot_bytes = st.session_state.driver.get_screenshot_as_png()
            st.session_state.last_screenshot = Image.open(
                BytesIO(screenshot_bytes)
            )
            st.rerun()
        else:
            st.warning("No active browser session.")

if st.sidebar.button("🛑 Stop Browser Session", use_container_width=True):
    if st.session_state.driver:
        st.session_state.driver.quit()
        st.session_state.driver = None
        st.session_state.last_screenshot = None
        st.info("Browser session closed.")

# -------------------------------------------------------------------
# Main Dashboard View
# -------------------------------------------------------------------
tab_preview, tab_source, tab_info = st.tabs(
    ["📸 Live Viewport", "📄 HTML Source", "ℹ️ System Info"]
)

with tab_preview:
    if st.session_state.last_screenshot:
        st.subheader("Current Browser Screen")
        st.image(
            st.session_state.last_screenshot,
            use_container_width=True,
            caption=f"Viewport: {target_url}",
        )
    else:
        st.info(
            "Click **Launch / Navigate** in the sidebar to start hosting the browser session."
        )

with tab_source:
    if st.session_state.driver:
        st.subheader("Page Source Code")
        st.code(st.session_state.driver.page_source[:5000], language="html")
    else:
        st.write("No active HTML source loaded.")

with tab_info:
    st.subheader("Container Environment Status")
    st.json(
        {
            "Python Streamlit": "Active",
            "Virtual Display": "Xvfb Enabled",
            "Headless Engine": "Chromium Driver",
            "Session Active": st.session_state.driver is not None,
        }
    )
