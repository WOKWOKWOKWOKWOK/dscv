import streamlit as st
import subprocess
import os
import urllib.request

st.title("⚡ Utopia Node.js Server Runner")
st.sidebar.header("System Status")

# Create a local 'bin' directory if it doesn't exist
local_bin_path = os.path.abspath("bin")
os.makedirs(local_bin_path, exist_ok=True)

# Add the directory to the path environment variable
if local_bin_path not in os.environ["PATH"]:
    os.environ["PATH"] = f"{local_bin_path}:{os.environ['PATH']}"

# Direct URL to the compiled Linux binary file
NODE_BINARY_URL = "https://github.com"
node_file_path = os.path.join(local_bin_path, "node")

# Download the file directly inside the Streamlit instance container
if not os.path.exists(node_file_path):
    with st.spinner("Downloading Linux Node binary from storage mirror..."):
        try:
            req = urllib.request.Request(NODE_BINARY_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                binary_content = response.read()
            with open(node_file_path, "wb") as f:
                f.write(binary_content)
        except Exception as e:
            st.error(f"Download failed: {e}")
            st.stop()

# Set execution rights and verify
try:
    if os.path.exists(node_file_path):
        os.chmod(node_file_path, 0o755)
        
    node_version = subprocess.check_output(["node", "-v"], text=True).strip()
    st.sidebar.success(f"✅ Node Engine Ready ({node_version})")
except Exception as e:
    st.sidebar.error("❌ Node Engine Missing")
    st.error(f"Execution check failed: {e}")
    st.stop()

if st.button("🚀 Boot Utopia Server"):
    st.info("Running npm install...")
    try:
        subprocess.run(["npm", "install"], check=True)
        st.sidebar.success("✅ Dependencies installed")
    except Exception as e:
        st.error(f"Failed to run npm install: {e}")
        st.stop()

    st.info("Booting background server container...")
    try:
        entry_file = "index.js" if os.path.exists("index.js") else "index.mjs"
        
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
        for _ in range(30):
            line = process.stdout.readline()
            if line:
                logs += line
                log_placeholder.code(logs)
                
    except Exception as e:
        st.error(f"Failed to execute application: {e}")
