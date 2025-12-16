import os
import subprocess

# Repo URL
repo_url = "https://github.com/WilJones-Red/app_challenge_fa25"

# Target folder on your Windows machine
target_dir = r"C:\Users\wmj1f\OneDrive\Documents\A-Education\Challenge\Assets"

# Ensure the folder exists
os.makedirs(target_dir, exist_ok=True)

# Repo folder name
repo_name = "DS350_FA25_Jones_Wil"
repo_path = os.path.join(target_dir, repo_name)

try:
    if os.path.exists(repo_path):
        print(f"Repo already exists at {repo_path}, pulling latest changes...")
        subprocess.run(["git", "-C", repo_path, "pull", "origin", "main"], check=True)
    else:
        print(f"Cloning repo into {repo_path}...")
        subprocess.run(["git", "clone", repo_url, repo_path], check=True)

    print("✅ Repo is ready at:", repo_path)

except subprocess.CalledProcessError as e:
    print("❌ Git command failed:", e)
except FileNotFoundError:
    print("❌ Git is not installed or not found in PATH. Install Git and try again.")

