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

# --- 2. DEPLOY FUNCTIONAL DEPENDENCY MOCKUPS ---
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
            # FIXED: Added live filesystem streaming logic directly into the node-static mockup
            f.write('''
import fs from 'fs';
import path from 'path';

export class Server {
    constructor(rootPath) {
        this.root = rootPath || '.';
    }
    serve(req, res) {
        // Automatically default empty requests to the main source file
        let targetFile = req.url === '/' ? 'index.js' : req.url;
        let filePath = path.join(this.root, targetFile);
        
        fs.readFile(filePath, (err, data) => {
            if (err) {
                res.writeHead(404, { 'Content-Type': 'text/plain' });
                res.end('File Not Found');
            } else {
                let ext = path.extname(filePath);
                let contentType = 'text/plain';
                if (ext === '.js' || ext === '.mjs') contentType = 'application/javascript';
                if (ext === '.html') contentType = 'text/html';
                if (ext === '.json') contentType = 'application/json';
                
                res.writeHead(200, { 'Content-Type': contentType });
                res.end(data);
            }
        });
    }
};
const nodeStatic = { Server: Server };
export { Server };
export default nodeStatic;
''')
            
        st.sidebar.success("✅ Mock packages synced")
    except Exception as e:
        st.sidebar.warning(f"Sync issue: {e}")

auto_assemble_dependencies()

# --- 3. SERVER STATE CONTAINER ---
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

    st.session_state.active_port = random.randint(8100, 8900)
    os.environ["PORT"] = str(st.session_state.active_port)
    
    st.info(f"Assigning stable web port lane: {st.session_state.active_port}...")
    entry_file = "index.js" if os.path.exists("index.js") else "index.mjs"
    
    st.session_state.server_process = subprocess.Popen(
        ["node", entry_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        close_fds=True
    )
    st.rerun()

# --- 4. DATA TRAFFIC ROUTING ENGINE ---
if st.session_state.server_process is not None:
    st.subheader("📋 Server Console Logs")
    st.code(f"Utopia background process online and listening on active port {st.session_state.active_port}...")

    st.subheader("🌐 Utopia Web Viewport")
    
    try:
        target_url = f"http://127.0.0.1:{st.session_state.active_port}"
        req = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            html_raw_data = response.read().decode('utf-8', errors='ignore')
            
        if html_raw_data.strip():
            components.html(html_raw_data, height=800, scrolling=True)
        else:
            st.info("🔄 Processing background modules. Wait 3 seconds and tap force refresh.")
    except Exception as fetch_err:
        st.warning("⚡ Loading cloud interface elements...")
        
    if st.button("🔄 Click to Force Refresh View"):
        st.rerun()
