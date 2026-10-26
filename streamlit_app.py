import streamlit as st
import subprocess
import os
import urllib.request
import shutil

# --- SECTION 1: PORTABLE ENGINE SETUP ---
def setup_portable_node():
    """Downloads and extracts a portable Node.js runtime into the sandbox."""
    NODE_VERSION = "v20.11.0"
    NODE_URL = f"https://nodejs.org{NODE_VERSION}/node-{NODE_VERSION}-linux-x64.tar.xz"
    
    if not os.path.exists("node_runtime"):
        # Download the compressed binary archive from Node.js servers
        req = urllib.request.Request(NODE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            node_tar_data = response.read()
        
        with open("node.tar.xz", "wb") as f:
            f.write(node_tar_data)
        
        os.makedirs("node_runtime", exist_ok=True)
        # Extract files using built-in Linux tar tools
        subprocess.run(["tar", "-xf", "node.tar.xz", "-C", "node_runtime"], check=True)
        os.remove("node.tar.xz")

    # Locate the target directory containing the executable engine files
    runtime_folder = os.listdir("node_runtime")[0]
    node_bin_dir = os.path.abspath(os.path.join("node_runtime", runtime_folder, "bin"))
    return node_bin_dir

# --- SECTION 2: STREAMLIT APP ENGINE ---
st.title("⚡ Utopia Node.js Server Runner")
st.sidebar.header("System Status")

# Initialize and patch paths immediately on app startup
try:
    node_binary_path = setup_portable_node()
    if node_binary_path not in os.environ["PATH"]:
        os.environ["PATH"] = f"{node_binary_path}:{os.environ['PATH']}"
        
    node_version = subprocess.check_output(["node", "-v"], text=True).strip()
    npm_version = subprocess.check_output(["npm", "-v"], text=True).strip()
    st.sidebar.success(f"✅ Node {node_version} / NPM {npm_version}")
except Exception as e:
    st.sidebar.error("❌ Node Engine Error")
    st.error(f"Failed to load engine from storage folder: {e}")
    st.stop()

# --- SECTION 3: APP EXECUTION WORKFLOW ---
if st.button("🚀 Boot Utopia Server"):
    # Step 1: Install Javascript module dependencies locally
    with st.spinner("Running npm install..."):
        try:
            subprocess.run(["npm", "install"], check=True)
            st.sidebar.success("✅ Dependencies installed")
        except Exception as e:
            st.error(f"Failed to run npm install: {e}")
            st.stop()

    # Step 2: Dynamically discover and execute the entry script
    st.info("Booting backend server container...")
    try:
        entry_file = "index.js" if os.path.exists("index.js") else "index.mjs"
        
        # Open execution process pipe in the background
        process = subprocess.Popen(
            ["node", entry_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        st.success("🚀 Utopia server process is running locally in the background!")
        st.subheader("Live Terminal Logs:")
        log_placeholder = st.empty()
        
        # Read and display initial boot up lines
        logs = ""
        for _ in range(30):
            line = process.stdout.readline()
            if line:
                logs += line
                log_placeholder.code(logs)
                
    except Exception as e:
        st.error(f"Failed to execute application: {e}")
