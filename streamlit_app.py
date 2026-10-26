import io
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

def run_github_zip(zip_url, main_script="__main__.py"):
    # Create a temporary directory that self-deletes when the script ends
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Downloading ZIP from {zip_url}...")
        
        try:
            # Download the ZIP file over HTTPS
            with urllib.request.urlopen(zip_url) as response:
                zip_data = response.read()
        except Exception as e:
            print(f"Error downloading the file: {e}")
            return
        
        print("Extracting archive...")
        # Load the ZIP from memory and extract it to the temp directory
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Look for the main Streamlit file
        target_script = os.path.join(temp_dir, main_script)
        if not os.path.exists(target_script):
            print(f"Error: {main_script} not found in the ZIP root.")
            return

        print("Launching Streamlit...")
        # Start Streamlit targeting the extracted file
        subprocess.run(["streamlit", "run", target_script])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_github_zip.py <github_raw_zip_url>")
    else:
        run_github_zip(sys.argv[1])
