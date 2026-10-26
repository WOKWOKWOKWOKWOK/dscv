import streamlit as st
import subprocess
import os

st.title("⚡ Utopia Node.js Server Runner")

st.sidebar.header("System Status")

# Verify that packages.txt worked and Node.js is ready natively
try:
    node_version = subprocess.check_output(["node", "-v"], text=True).strip()
    npm_version = subprocess.check_output(["npm", "-v"], text=True).strip()
    st.sidebar.success(f"✅ Node {node_version} / NPM {npm_version}")
except Exception:
    st.sidebar.error("❌ Node.js missing")
    st.error("Please ensure 'packages.txt' is in your repo with the word 'nodejs' written inside.")
    st.stop()

if st.button("🚀 Boot Utopia Server"):
    # Step 1: Install dependencies locally
    with st.spinner("Running npm install..."):
        try:
            subprocess.run(["npm", "install"], check=True)
            st.sidebar.success("✅ Dependencies installed")
        except Exception as e:
            st.error(f"Failed to run npm install: {e}")
            st.stop()

    # Step 2: Run the local server file
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
