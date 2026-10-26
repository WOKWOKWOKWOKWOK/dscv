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

# --- 2. DEPLOY DEPENDENCY MOCKUPS ---
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
                    
        static_dest = os.path.join("node_modules", "node-static")
        os.makedirs(static_dest, exist_ok=True)
        with open(os.path.join(static_dest, "package.json"), "w") as f:
            f.write('{"name":"node-static","version":"0.7.11","main":"./lib/node-static.js","type":"module"}')
        os.makedirs(os.path.join(static_dest, "lib"), exist_ok=True)
        with open(os.path.join(static_dest, "lib", "node-static.js"), "w") as f:
            f.write('class Server { constructor() {} serve() {} }; const nodeStatic = { Server: Server }; export { Server }; export default nodeStatic;')
    except Exception:
        pass

auto_assemble_dependencies()

# --- 3. SERVER STATE MANAGEMENT ---
if "server_process" not in st.session_state:
    st.session_state.server_process = None
if "server_logs" not in st.session_state:
    st.session_state.server_logs = ""

if st.button("🚀 Boot Utopia Server") or st.session_state.server_process is not None:
    if st.session_state.server_process is None:
        st.info("Booting background server container...")
        entry_file = "index.js" if os.path.exists("index.js") else "index.mjs"
        
        # Start the process and route output logs so Python can read them
        st.session_state.server_process = subprocess.Popen(
            ["node", entry_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        st.success("🚀 Utopia server process triggered!")

    # Check for new logs from the server process
    try:
        # Read available lines from stdout without blocking
        import select
        process = st.session_state.server_process
        
        # Read stdout logs
        while rlist := select.select([process.stdout], [], [], 0.1)[0]:
            line = process.stdout.readline()
            if not line:
                break
            st.session_state.server_logs += line

        # Read stderr logs (errors)
        while rlist := select.select([process.stderr], [], [], 0.1)[0]:
            line = process.stderr.readline()
            if not line:
                break
            st.session_state.server_logs += f"ERROR: {line}"
    except Exception as log_err:
        pass

    # Display the logs on the page so we can see what the server is doing
    st.subheader("📋 Server Console Logs")
    if st.session_state.server_logs:
        st.code(st.session_state.server_logs)
    else:
        st.write("No log output generated yet. Click the button again to refresh logs.")

    # --- 4. PYTHON REVERSE PROXY CONNECTION ---
    st.subheader("🌐 Utopia Web Viewport")
    
    # Try multiple common ports to check where it's listening
    ports_to_try = [8080, 8000, 3000, 5000]
    connected = False
    
    for port in ports_to_try:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=2) as response:
                server_html_content = response.read().decode('utf-8', errors='ignore')
            
            st.success(f"Connected successfully on port {port}!")
            components.html(server_html_content, height=800, scrolling=True)
            connected = True
            break
        except Exception:
            continue
            
    if not connected:
        st.error("⏳ Waiting for server interface to stabilize...")
        st.info("Review the Server Console Logs above to check for errors or to see if a custom port is required.")
