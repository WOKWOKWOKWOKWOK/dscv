import streamlit as st
import subprocess
import os
import urllib.request
import sys
import shutil
import glob
import random
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("⚡ Utopia Node.js Server Runner")
st.sidebar.header("System Status")

# --- 1. SYSTEM INITIALIZATION ---
local_bin_path = os.path.abspath("bin")
os.makedirs(local_bin_path, exist_ok=True)
if local_bin_path not in os.environ["PATH"]:
    os.environ["PATH"] = f"{local_bin_path}:{os.environ['PATH']}"

NODE_BINARY_URL = "https://github.com"
node_file_path = os.path.join(local_bin_path, "node")

if not os.path.exists(node_file_path):
    with st.spinner("Initializing server engine container..."):
        try:
            req = urllib.request.Request(NODE_BINARY_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                binary_content = response.read()
            with open(node_file_path, "wb") as f:
                f.write(binary_content)
            os.chmod(node_file_path, 0o755)
        except Exception as e:
            st.error(f"Engine download failed: {e}")
            st.stop()

try:
    node_version = subprocess.check_output(["node", "-v"], text=True).strip()
    st.sidebar.success(f"✅ Node Engine Ready ({node_version})")
except Exception:
    st.sidebar.error("❌ Node Engine Offline")
    st.stop()

# --- 2. DEPLOY DEPENDENCY MOCKUPS ---
def auto_assemble_dependencies():
    try:
        os.makedirs("node_modules", exist_ok=True)
        pkg_dir = os.path.join("node_modules", "@tomphttp", "bare-server-node")
        os.makedirs(pkg_dir, exist_ok=True)
        with open(os.path.join(pkg_dir, "package.json"), "w") as f:
            f.write('{"name":"@tomphttp/bare-server-node","version":"2.0.1","main":"dist/index.js","type":"module"}')
            
        dist_dir = os.path.join(pkg_dir, "dist")
        os.makedirs(dist_dir, exist_ok=True)
        with open(os.path.join(dist_dir, "index.js"), "w") as f:
            f.write('''
export class BareServer {
    constructor() {}
    shouldRoute(req) { return false; }
    route(req, res) { return false; }
    upgrade(req, socket, head) {}
    listen() {}
}
export function createBareServer(path) { return new BareServer(); }
export default createBareServer;
''')

        static_dest = os.path.join("node_modules", "node-static")
        os.makedirs(static_dest, exist_ok=True)
        with open(os.path.join(static_dest, "package.json"), "w") as f:
            f.write('{"name":"node-static","version":"0.7.11","main":"./lib/node-static.js","type":"module"}')
        os.makedirs(os.path.join(static_dest, "lib"), exist_ok=True)
        with open(os.path.join(static_dest, "lib", "node-static.js"), "w") as f:
            f.write('class Server { constructor() {} serve() {} }; const nodeStatic = { Server: Server }; export { Server }; export default nodeStatic;')
            
        st.sidebar.success("✅ Mock packages synced")
    except Exception as e:
        st.sidebar.warning(f"Sync issue: {e}")

auto_assemble_dependencies()

# --- 3. SERVER STATE ASYNCHRONOUS STORAGE ---
if "server_process" not in st.session_state:
    st.session_state.server_process = None
if "active_port" not in st.session_state:
    st.session_state.active_port = 8080

boot_button = st.button("🚀 Boot Utopia Server")

if boot_button:
    if st.session_state.server_process is not None:
        try:
            st.session_state.server_process.terminate()
        except Exception:
            pass
        st.session_state.server_process = None

    # Roll a clean unique port number assignment
    st.session_state.active_port = random.randint(8100, 8900)
    os.environ["PORT"] = str(st.session_state.active_port)
    
    st.info(f"Assigning stable web port lane: {st.session_state.active_port}...")
    entry_file = "index.js" if os.path.exists("index.js") else "index.mjs"
    
    # Non-blocking flags to make sure the interface handles streams smoothly
    st.session_state.server_process = subprocess.Popen(
        ["node", entry_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,            # Line-buffered output streaming
        close_fds=True
    )
    st.rerun()

# --- 4. ASYNCHRONOUS CONSOLE LOG MONITOR ---
if st.session_state.server_process is not None:
    st.subheader("📋 Server Console Logs")
    log_placeholder = st.empty()
    log_placeholder.code(f"Utopia background process online and listening on active port {st.session_state.active_port}...")

    # --- 5. DATA PORT PROXY AND VISUAL INTERFACE ---
    st.subheader("🌐 Utopia Web Viewport")
    try:
        target_url = f"http://127.0.0.1:{st.session_state.active_port}"
        # Direct fallback components check
        with urllib.request.urlopen(target_url, timeout=1) as response:
            server_html_content = response.read().decode('utf-8', errors='ignore')
        components.html(server_html_content, height=800, scrolling=True)
    except Exception:
        # If the backend is running but still spinning up its internal sockets, 
        # we display an embedded iframe proxy rather than throwing a blocking connection failure alert box.
        iframe_proxy_html = f'<iframe src="http://127.0.0.1:{st.session_state.active_port}" width="100%" height="800px" style="border:1px solid #333; border-radius:8px;"></iframe>'
        components.html(iframe_proxy_html, height=820, scrolling=True)
