import streamlit as st
import subprocess
import os
import urllib.request

st.title("⚡ Utopia Node.js Server Runner")
st.sidebar.header("System Status")

# Setup folder paths
local_bin_path = os.path.abspath("bin")
os.makedirs(local_bin_path, exist_ok=True)

if local_bin_path not in os.environ["PATH"]:
    os.environ["PATH"] = f"{local_bin_path}:{os.environ['PATH']}"

# Use the pre-verified working download address
NODE_BINARY_URL = "https://github.com"
node_file_path = os.path.join(local_bin_path, "node")

if not os.path.exists(node_file_path):
    with st.spinner("Downloading Linux Node binary..."):
        try:
            req = urllib.request.Request(NODE_BINARY_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                binary_content = response.read()
            with open(node_file_path, "wb") as f:
                f.write(binary_content)
        except Exception as e:
            st.error(f"Download failed: {e}")
            st.stop()

# Set execution rights and verify system state
try:
    if os.path.exists(node_file_path):
        os.chmod(node_file_path, 0o755)
        
    node_version = subprocess.check_output(["node", "-v"], text=True).strip()
    st.sidebar.success(f"✅ Node Engine Ready ({node_version})")
except Exception as e:
    st.sidebar.error("❌ Node Engine Missing")
    st.stop()

if st.button("🚀 Boot Utopia Server"):
    st.info("Booting background server container...")
    try:
        # Check for your entry files
        entry_file = "index.js" if os.path.exists("index.js") else "index.mjs"
        
        # Bypasses 'npm install' by launching your index file directly with the active node binary
        process = subprocess.Popen(
            ["node", entry_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        st.success("🚀 Utopia server process is running locally in the background!")
        st.subheader("Live Terminal Logs:")
        log_placeholder = st.empty()
        
        logs = ""
        # Capture and display the active server logs
        for _ in range(40):
            line = process.stdout.readline()
            if line:
                logs += line
                log_placeholder.code(logs)
            
            # Also check if it prints out errors immediately
            err_line = process.stderr.readline()
            if err_line:
                logs += f"\nERROR: {err_line}"
                log_placeholder.code(logs)
                
    except Exception as e:
        st.error(f"Failed to execute application: {e}")
