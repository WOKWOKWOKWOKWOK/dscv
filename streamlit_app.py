import streamlit as st
import urllib.request
import zipfile
import io
import os
import subprocess
import sys
import shutil

st.title("⚡ Utopia Node.js Server Runner")

# 1. ENTER YOUR DETAILS HERE
REPO_OWNER = "UtopiaUnblocker"  # Replace with the actual repository owner name
REPO_NAME = "Utopia"    # Replace with the actual repository name
BRANCH = "main"            # Usually 'main' or 'master'

# 2. This line automatically constructs the secret GitHub background ZIP link
ZIP_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"

st.sidebar.header("System Status")

if st.button("🚀 Boot Utopia Server"):
    # Step 1: Download code from GitHub via the dynamic link
    with st.spinner("Downloading code files from GitHub..."):
        if os.path.exists("node_app"):
            shutil.rmtree("node_app")
            
        try:
            req = urllib.request.Request(ZIP_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                zip_data = response.read()
                
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
                zip_ref.extractall("node_app")
                
            # Find the nested main folder that GitHub auto-creates inside the ZIP
            nested_folder = os.listdir("node_app")[0]
            app_path = os.path.abspath(os.path.join("node_app", nested_folder))
            st.sidebar.success("✅ Code downloaded")
        except Exception as e:
            st.error(f"Failed to fetch code from GitHub: {e}")
            st.info("Check that REPO_OWNER and REPO_NAME are spelled exactly right.")
            st.stop()

    # Step 2: Extract a portable Node.js runtime inside the container
    with st.spinner("Setting up Node.js engine..."):
        try:
            NODE_VERSION = "v20.11.0"
            NODE_URL = f"https://nodejs.org{NODE_VERSION}/node-{NODE_VERSION}-linux-x64.tar.xz"
            
            if not os.path.exists("node_runtime"):
                req = urllib.request.Request(NODE_URL, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    node_tar_data = response.read()
                
                with open("node.tar.xz", "wb") as f:
                    f.write(node_tar_data)
                
                os.makedirs("node_runtime", exist_ok=True)
                subprocess.run(["tar", "-xf", "node.tar.xz", "-C", "node_runtime"], check=True)
                os.remove("node.tar.xz")
            
            runtime_folder = os.listdir("node_runtime")[0]
            node_bin_dir = os.path.abspath(os.path.join("node_runtime", runtime_folder, "bin"))
            
            os.environ["PATH"] = f"{node_bin_dir}:{os.environ['PATH']}"
            st.sidebar.success("✅ Node.js Engine Ready")
        except Exception as e:
            st.error(f"Failed to install Node.js engine: {e}")
            st.stop()

    # Step 3: Read package.json and download modules
    with st.spinner("Running npm install..."):
        try:
            subprocess.run(["npm", "install"], cwd=app_path, check=True)
            st.sidebar.success("✅ Dependencies installed")
        except Exception as e:
            st.error(f"Failed to run npm install: {e}")
            st.stop()

    # Step 4: Run the Utopia server file
    st.info("Booting background server container...")
    try:
        # Check if the main file is index.js or index.mjs based on your folder image
        entry_file = "index.js" if os.path.exists(os.path.join(app_path, "index.js")) else "index.mjs"
        
        process = subprocess.Popen(
            ["node", entry_file],
            cwd=app_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        st.success("🚀 Utopia server process is running in the background!")
        
        st.subheader("Live Terminal Logs:")
        log_placeholder = st.empty()
        
        logs = ""
        # Let's read out the logs to confirm the server booted successfully
        for _ in range(20):
            line = process.stdout.readline()
            if line:
                logs += line
                log_placeholder.code(logs)
                
    except Exception as e:
        st.error(f"Failed to execute application: {e}")
