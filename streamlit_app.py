import streamlit as st
import urllib.request
import zipfile
import io
import os
import subprocess
import sys
import shutil

st.title("⚡ Node.js App Runner inside Streamlit")

# 1. SET THE TARGET REPOSITORY DETAILS HERE
REPO_OWNER = "UtopiaUnblocker"
REPO_NAME = "Utopia"
BRANCH = "main"

ZIP_URL = f"https://github.com{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"

# Status trackers in Streamlit sidebar
st.sidebar.header("System Status")

if st.button("Download and Start Node.js Application"):
    # Step 1: Clean and download the repository code
    with st.spinner("Downloading repository source from GitHub..."):
        if os.path.exists("node_app"):
            shutil.rmtree("node_app")
            
        try:
            req = urllib.request.Request(ZIP_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                zip_data = response.read()
                
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
                zip_ref.extractall("node_app")
                
            # Handle the nested root directory GitHub creates
            nested_folder = os.listdir("node_app")[0]
            app_path = os.path.abspath(os.path.join("node_app", nested_folder))
            st.sidebar.success("✅ Code downloaded")
        except Exception as e:
            st.error(f"Failed to fetch code: {e}")
            st.stop()

    # Step 2: Install Node.js directly inside the Streamlit environment
    with st.spinner("Installing Node.js environment..."):
        try:
            # Streamlit Cloud runs on Linux (Ubuntu), so we download a portable Node.js binary package
            NODE_VERSION = "v20.11.0"
            NODE_URL = f"https://nodejs.org{NODE_VERSION}/node-{NODE_VERSION}-linux-x64.tar.xz"
            
            if not os.path.exists("node_runtime"):
                req = urllib.request.Request(NODE_URL, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    node_tar_data = response.read()
                
                with open("node.tar.xz", "wb") as f:
                    f.write(node_tar_data)
                
                # Unpack the portable Node binary package
                os.makedirs("node_runtime", exist_ok=True)
                subprocess.run(["tar", "-xf", "node.tar.xz", "-C", "node_runtime"], check=True)
                os.remove("node.tar.xz")
            
            # Find the path to the newly extracted node & npm binaries
            runtime_folder = os.listdir("node_runtime")[0]
            node_bin_dir = os.path.abspath(os.path.join("node_runtime", runtime_folder, "bin"))
            
            # Update the environment path so Python can find 'node' and 'npm'
            os.environ["PATH"] = f"{node_bin_dir}:{os.environ['PATH']}"
            st.sidebar.success("✅ Node.js Engine Ready")
        except Exception as e:
            st.error(f"Failed to install Node.js engine: {e}")
            st.stop()

    # Step 3: Install the application's dependencies (npm install)
    with st.spinner("Installing Node.js dependencies (npm install)..."):
        try:
            # Run npm install inside the target app folder
            subprocess.run(["npm", "install"], cwd=app_path, check=True)
            st.sidebar.success("✅ Dependencies installed")
        except Exception as e:
            st.error(f"Failed to run npm install: {e}")
            st.stop()

    # Step 4: Run the application
    st.info("Starting the background app container...")
    try:
        # Check if entry point is index.js or index.mjs
        entry_file = "index.js" if os.path.exists(os.path.join(app_path, "index.js")) else "index.mjs"
        
        # Launch the Node app as a background process so Streamlit doesn't freeze
        process = subprocess.Popen(
            ["node", entry_file],
            cwd=app_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        st.success(f"🚀 Node.js process started successfully using {entry_file}!")
        st.warning("Keep this Streamlit page open to keep the backend script running.")
        
        # Stream the initial terminal output log straight into the interface
        st.subheader("Console Output Logs:")
        log_placeholder = st.empty()
        
        # Read the first few lines of logs to ensure it booted correctly
        logs = ""
        for _ in range(15):
            line = process.stdout.readline()
            if line:
                logs += line
                log_placeholder.code(logs)
                
    except Exception as e:
        st.error(f"Failed to execute backend application: {e}")
