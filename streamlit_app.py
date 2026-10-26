import streamlit as st
import subprocess
import os
import urllib.request
import sys
import shutil
import glob
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

# Verify node binary state
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

# --- 3. SERVER STATE CONTAINER ---
if "server_process" not in st.session_state:
    st.session_state.server_process = None

boot_button = st.button("🚀 Boot/Restart Utopia Server")

# If button is pressed or if process has crashed, handle fresh initialization
if boot_button or (st.session_state.server_process is not None and st.session_state.server_process.poll() is not None):
    # Kill dead reference if it crashed out
    if st.session_state.server_process is not None:
        st.session_state.server_process.kill()
        st.session_state.server_process = None
        
    st.info("Starting fresh background server container instance...")
    entry_file = "index.js" if os.path.exists("index.js") else "index.mjs"
    st.session_state.server_process = subprocess.Popen(
        ["node", entry_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

# --- 4. LIVE CONSOLE LOG MONITOR ---
if st.session_state.server_process is not None:
    st.subheader("📋 Server Console Logs")
    log_placeholder = st.empty()
    
    # Check current process logs non-blocking
    logs = ""
    try:
        # Read available console outputs
        for _ in range(15):
            # Check standard out
            line = st.session_state.server_process.stdout.readline()
            if line:
                logs += f"LOG: {line}"
            # Check error line stream
            err_line = st.session_state.server_process.stderr.readline()
            if err_line:
                logs += f"ERROR: {err_line}"
        
        if logs:
            log_placeholder.code(logs)
        else:
            log_placeholder.code("Server process is listening silently...")
    except Exception as log_err:
        log_placeholder.code(f"Awaiting logs: {log_err}")

    # --- 5. DATA PORT PROXY AND VISUAL INTERFACE ---
    st.subheader("🌐 Utopia Web Viewport")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080", timeout=2) as response:
            server_html_content = response.read().decode('utf-8', errors='ignore')
        components.html(server_html_content, height=800, scrolling=True)
    except Exception as proxy_err:
        st.error("⏳ Interface not rendering yet.")
        st.info("Review the Server Console Logs above to check for errors or to see if a custom port is required.")
