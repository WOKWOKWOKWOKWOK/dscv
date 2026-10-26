import streamlit as st
import urllib.request
import zipfile
import io
import os
import shutil
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🌐 Live Non-Python Repo Host")

# 1. SET THE TARGET REPOSITORY INFORMATION
REPO_OWNER = "UtopiaUnblocker"
REPO_NAME = "Utopia"
BRANCH = "main" 

ZIP_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"

if st.button("Boot and Host Web Files"):
    with st.spinner("Pulling files from GitHub..."):
        try:
            # Clean up older builds
            if os.path.exists("hosted_site"):
                shutil.rmtree("hosted_site")
                
            # Download the repo as a zip file behind the scenes
            req = urllib.request.Request(ZIP_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                zip_data = response.read()
                
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
                zip_ref.extractall("hosted_site")
            
            # Find the folder GitHub wrapped everything inside
            folders = os.listdir("hosted_site")
            root_dir = os.path.join("hosted_site", folders[0])
            
            # Look for their main webpage file
            html_file = os.path.join(root_dir, "index.html")
            
            if os.path.exists(html_file):
                st.success("Successfully hosting repository!")
                # Read and render the HTML directly into Streamlit
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()
                
                # Render the site (adjust height as needed)
                components.html(html_content, height=800, scrolling=True)
            else:
                st.error("Could not find an index.html file in their repository.")
                st.write("Files found inside the repo:", os.listdir(root_dir))
                
        except Exception as e:
            st.error(f"Error loading files: {e}")
