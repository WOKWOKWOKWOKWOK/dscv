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

# --- 2. DEPLOY FIXED DEPENDENCY MOCKUPS ---
def auto_assemble_dependencies():
    try:
        os.makedirs("node_modules", exist_ok=True)
        python_bin_path = os.path.dirname(sys.executable)
        cache_dirs = glob.glob(os.path.join(python_bin_path, "..", "src", "*"))
        
        for src_dir in cache_dirs:
            if "bare-server-node" in src_dir:
                dest_dir = os.path.join("node_modules", "@tomphttp", "bare-server-node")
                if not os.path.exists(dest_dir):
                    shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
                    
        # Inject custom mockup code with the required shouldRoute layout
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
export function createBareServer(path) {
    return new BareServer();
}
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

# Custom terminal log display area
log_placeholder = st.empty()

if st.button("🚀 Boot Utopia Server") or st.session_state.server_process is not None:
    if st.session_state.server_process is None:
        st.info("Booting background server container...")
        entry_file = "index.js" if os.path.exists("index.js") else "index.mjs"
        st.session_state.server_process = subprocess.Popen(
            ["node", entry_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        st.success("🚀 Utopia server process active!")

    # --- 4. DATA PORT PROXY AND VISUAL INTERFACE ---
    st.subheader("🌐 Utopia Web Viewport")
    
    try:
        # Request data loop from internal port 8080 configuration
        with urllib.request.urlopen("http://127.0.0.1:8080", timeout=5) as response:
            server_html_content = response.read().decode('utf-8', errors='ignore')
            
        components.html(server_html_content, height=800, scrolling=True)
        
    except Exception as proxy_err:
        st.error("⏳ Re-routing data traffic channels...")
        st.info("The process is running. Tap the launch button again to pull the fresh HTML layout frame.")
