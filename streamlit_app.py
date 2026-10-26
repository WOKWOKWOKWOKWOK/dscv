import streamlit as st
import urllib.request
import zipfile
import io
import os
import subprocess
import shutil

st.title("⚡ Utopia Node.js Server Runner")

# 1. ENTER YOUR DETAILS HERE
REPO_OWNER = "UtopiaUnblocker"  # Replace with the actual repository owner name
REPO_NAME = "Utopia"    # Replace with the actual repository name
BRANCH = "main"            # Usually 'main' or 'master'

ZIP_URL = f"https://github.com{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"

st.sidebar.header("System Status")

if st.button("🚀 Boot Utopia Server"):
    # Step 1: Download code from GitHub
    with st.spinner("Downloading code files from GitHub..."):
        if os.path.exists("node_app"):
            shutil.rmtree("node_app")
            
        try:
            req = urllib.request.Request(ZIP_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                zip_data = response.read()
                
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
                zip_ref.extractall("node_app")
                
            nested_folder = os.listdir("node_app")[0]
            app_path = os.path.abspath(os.path.join("node_app", nested_folder))
            st.sidebar.success("✅ Code downloaded")
        except Exception as e:
            st.error(f"Failed to fetch code from GitHub: {e}")
            st.stop()

    # Step 2: Check Pre-installed Node Environment
    with st.spinner("Verifying system Node.js installation..."):
        try:
            node_version = subprocess.check_output(["node", "-v"], text=True).strip()
            npm_version = subprocess.check_output(["npm", "-v"], text=True).strip()
            st.sidebar.success(f"✅ Node {node_version} / NPM {npm_version} Detected")
        except Exception as e:
            st.error("Node.js was not detected on the system container.")
            st.info("Make sure you created a 'packages.txt' file in your GitHub repo with the text 'nodejs' inside it.")
            st.stop()

    # Step 3: Download dependencies
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
        # Keep reading lines to stream logs live to your Streamlit UI
        for _ in range(30):
            line = process.stdout.readline()
            if line:
                logs += line
                log_placeholder.code(logs)
                
    except Exception as e:
        st.error(f"Failed to execute application: {e}")
