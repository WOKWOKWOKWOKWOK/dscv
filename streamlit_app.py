import streamlit as st
import subprocess
import os
import urllib.request
import sys
import shutil
import glob
import random
import fcntl

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

# --- 3. CONTAINER MANAGEMENT ---
if "server_process" not in st.session_state:
    st.session_state.server_process = None
if "active_port" not in st.session_state:
    st.session_state.active_port = 8080
if "terminal_logs" not in st.session_state:
    st.session_state.terminal_logs = "System awaiting initialization...\n"

boot_button = st.button("🚀 Start/Restart Utopia Server Instance")

if boot_button:
    if st.session_state.server_process is not None:
        try:
            st.session_state.server_process.terminate()
        except Exception:
            pass
        st.session_state.server_process = None

    st.session_state.active_port = random.randint(8100, 8900)
    os.environ["PORT"] = str(st.session_state.active_port)
    st.session_state.terminal_logs = f"--- Booting instance on port {st.session_state.active_port} ---\n"
    
    entry_file = "index.js" if os.path.exists("index.js") else "index.mjs"
    
    st.session_state.server_process = subprocess.Popen(
        ["node", entry_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Configure the background streams to be non-blocking so they never freeze the page layout
    for stream in [st.session_state.server_process.stdout, st.session_state.server_process.stderr]:
        fd = stream.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
    st.rerun()

# --- 4. REAL-TIME TERMINAL DISPLAY LAYER ---
if st.session_state.server_process is not None:
    st.subheader("🖥️ Utopia Live Server Console")
    
    # Scan standard pipe vectors for runtime feedback strings
    try:
        stdout_data = st.session_state.server_process.stdout.read()
        if stdout_data:
            st.session_state.terminal_logs += stdout_data
    except Exception:
        pass

    try:
        stderr_data = st.session_state.server_process.stderr.read()
        if stderr_data:
            st.session_state.terminal_logs += f"\nERROR DETAILS: {stderr_data}"
    except Exception:
        pass

    # Print the aggregated terminal text straight out to the container panel layout
    st.code(st.session_state.terminal_logs, language="bash")
    
    # Auto refresh trigger button
    if st.button("🔄 Sync Live Stream Outputs"):
        st.rerun()
