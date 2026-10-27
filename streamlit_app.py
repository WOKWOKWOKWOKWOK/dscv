import io
import os
import time
import urllib.parse
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components

# Third-party headless browser dependencies
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


# -------------------------------------------------------------------
# Helper: Format & Sanitize User Input URLs
# -------------------------------------------------------------------
def sanitize_url(raw_url: str) -> str:
    """Ensures input strings have a valid scheme to prevent 'invalid argument' Selenium errors."""
    url = raw_url.strip()
    if not url:
        return "https://example.com"

    # Add https protocol if missing scheme
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"

    return url


# -------------------------------------------------------------------
# Helper: Display & Driver Initialization
# -------------------------------------------------------------------
@st.cache_resource
def start_virtual_display():
    """Initializes a virtual framebuffer (Xvfb) on Streamlit Cloud Linux servers."""
    try:
        display = Display(visible=0, size=(1280, 720))
        display.start()
        return display
    except Exception as exc:
        st.caption(f"Virtual display notice: {exc}")
        return None


def init_chrome_driver():
    """Configures a robust headless Chrome WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,720")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Locate Chromium binary on Linux container
    for binary_path in ["/usr/bin/chromium", "/usr/bin/chromium-browser"]:
        if os.path.exists(binary_path):
            chrome_options.binary_location = binary_path
            break

    return webdriver.Chrome(options=chrome_options)


# -------------------------------------------------------------------
# Page Config & Session State Initialization
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Streamlit Web Runner",
    page_icon="🖥️",
    layout="wide",
)

# Start virtual display session once
start_virtual_display()

if "driver" not in st.session_state:
    st.session_state.driver = None

if "last_screenshot" not in st.session_state:
    st.session_state.last_screenshot = None


# -------------------------------------------------------------------
# Dashboard UI Layout
# -------------------------------------------------------------------
st.title("🖥️ Streamlit Web Runner & Embedded Viewer")

mode = st.radio(
    "Select Operating Mode:",
    ["Headless Browser (Selenium)", "Embedded App Viewer (iFrame)"],
    horizontal=True,
)

if mode == "Headless Browser (Selenium)":
    st.subheader("Headless Browser Session")

    # Controls
    col_input, col_btn1, col_btn2 = st.columns([3, 1, 1])

    with col_input:
        raw_target = st.text_input(
            "Enter Web Address:",
            value="example.com",
            placeholder="e.g. google.com or https://example.com",
        )

    # Automatically format URL to prevent Selenium 'invalid argument' exceptions
    clean_url = sanitize_url(raw_target)

    with col_btn1:
        st.write(" ")  # Alignment spacer
        launch_clicked = st.button("🚀 Load Page", use_container_width=True)

    with col_btn2:
        st.write(" ")  # Alignment spacer
        stop_clicked = st.button("🛑 Stop Driver", use_container_width=True)

    # Browser Execution Logic
    if launch_clicked:
        with st.spinner(f"Navigating to {clean_url}..."):
            try:
                if st.session_state.driver is None:
                    st.session_state.driver = init_chrome_driver()

                # Execute navigation on sanitized URL
                st.session_state.driver.get(clean_url)
                time.sleep(2)  # Wait for rendering

                # Capture viewport image
                raw_png = st.session_state.driver.get_screenshot_as_png()
                st.session_state.last_screenshot = Image.open(
                    io.BytesIO(raw_png)
                )
                st.success("Loaded successfully!")
            except Exception as err:
                st.error(f"Failed to navigate: {err}")

    if stop_clicked:
        if st.session_state.driver:
            st.session_state.driver.quit()
            st.session_state.driver = None
            st.session_state.last_screenshot = None
            st.info("Browser session closed.")

    # Viewport Output
    st.divider()
    if st.session_state.last_screenshot:
        st.image(
            st.session_state.last_screenshot,
            caption=f"Active URL: {clean_url}",
            use_container_width=True,
        )
    else:
        st.info("Enter a web address and click **Load Page** to render.")

else:
    st.subheader("Embedded Application Frame")
    st.caption("Embed externally hosted services or web applications.")

    iframe_url_input = st.text_input(
        "Enter Hosted App URL:",
        value="https://example.com",
        help="Paste the external HTTPS link of your hosted app.",
    )

    clean_iframe_url = sanitize_url(iframe_url_input)

    st.write(f"**Rendering:** `{clean_iframe_url}`")
    components.iframe(clean_iframe_url, height=750, scrolling=True)
