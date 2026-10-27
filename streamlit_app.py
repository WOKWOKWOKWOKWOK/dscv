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
# Page Config & Custom Styling
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
# Driver Setup
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


def capture_compressed_viewport(driver) -> Image.Image:
    raw_png = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(raw_png)).convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=45, optimize=True)
    buffer.seek(0)
    return Image.open(buffer)


# -------------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------------
if "current_url" not in st.session_state:
    try:
        st.session_state.current_url = driver.current_url
    except Exception:
        st.session_state.current_url = "https://www.google.com"

if "last_click" not in st.session_state:
    st.session_state.last_click = None

if "last_coords" not in st.session_state:
    st.session_state.last_coords = None


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
# Reliable Text Typing Handler
# -------------------------------------------------------------------
def send_text_to_page():
    typed_value = st.session_state.get("direct_type_input", "")
    if typed_value:
        try:
            # Re-focus the target element using stored click coordinates if active element lost focus
            if st.session_state.last_coords:
                lx, ly = st.session_state.last_coords
                re_focus_js = f"""
                var elem = document.elementFromPoint({lx}, {ly});
                if (elem) {{
                    var target = elem;
                    while (target && typeof target.focus !== 'function') {{
                        target = target.parentElement;
                    }}
                    if (target) {{
                        target.focus();
                        if (typeof target.click === 'function') target.click();
                    }}
                }}
                """
                driver.execute_script(re_focus_js)

            active_el = driver.switch_to.active_element
            active_el.send_keys(typed_value)
            active_el.send_keys(Keys.ENTER)
        except Exception:
            pass
        st.session_state["direct_type_input"] = ""
        st.session_state.current_url = driver.current_url


st.text_input(
    "⌨️ Instant Type Bar",
    key="direct_type_input",
    placeholder="Click an input box below, type here, and hit Enter...",
    on_change=send_text_to_page,
    label_visibility="collapsed",
)


# -------------------------------------------------------------------
# Viewport Fragment (Safe Click Handler)
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
        x, y = coords["x"], coords["y"]
        st.session_state.last_coords = (x, y)

        # Safe element resolution prevents 'elem.click is not a function' on SVGs/Text Nodes
        safe_click_js = f"""
        var elem = document.elementFromPoint({x}, {y});
        if (elem) {{
            var target = elem;
            while (target && typeof target.click !== 'function') {{
                target = target.parentElement;
            }}
            if (target) {{
                target.click();
                if (typeof target.focus === 'function') target.focus();
            }} else {{
                elem.dispatchEvent(new MouseEvent('click', {{bubbles: true, cancelable: true, clientX: {x}, clientY: {y}}}));
            }}
        }}
        """
        driver.execute_script(safe_click_js)
        st.session_state.current_url = driver.current_url
        st.rerun()


render_viewport()
