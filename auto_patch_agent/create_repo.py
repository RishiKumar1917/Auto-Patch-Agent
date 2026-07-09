import os
import sys
import subprocess
import requests
from dotenv import load_dotenv

# load the env file
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_token_from_user():
    # if token is not found in env, we prompt the user to input it
    print("[*] GITHUB_TOKEN not found in .env file.")
    token = input("Please enter your GitHub Personal Access Token (PAT): ").strip()
    if not token:
        print("[!] Token cannot be empty. Exiting.")
        sys.exit(1)
        
    # write it back to .env so we save it for later
    with open(".env", "a") as f:
        f.write(f"\nGITHUB_TOKEN={token}\n")
    print("[+] GITHUB_TOKEN saved to .env file.")
    return token

def create_github_repo(token):
    # call github api to create a new repo
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # first get the username
    user_resp = requests.get("https://api.github.com/user", headers=headers)
    if user_resp.status_code != 200:
        print("[!] Failed to authenticate with GitHub. Check your token.")
        sys.exit(1)
        
    username = user_resp.json()["login"]
    print(f"[*] Authenticated successfully as {username}")
    
    repo_name = "auto-patch-agent"
    payload = {
        "name": repo_name,
        "description": "Autonomous AI-Agentic Security Triage and Patching Engine",
        "private": False,
        "auto_init": False
    }
    
    # try creating the repo
    print(f"[*] Creating new public repositry '{repo_name}' on GitHub...")
    create_resp = requests.post("https://api.github.com/user/repos", headers=headers, json=payload)
    
    if create_resp.status_code == 201:
        print(f"[+] Repository '{repo_name}' created successfully on GitHub!")
    elif create_resp.status_code == 422:
        print(f"[*] Repositry '{repo_name}' already exists on your GitHub account.")
    else:
        print(f"[!] Error creating repository: {create_resp.json().get('message')}")
        sys.exit(1)
        
    return username, repo_name

def initialize_and_push_git(username, repo_name, token):
    # run local commands to push this folder
    print("[*] Starting local git configuration...")
    
    # check if git is initialized
    if not os.path.exists(".git"):
        subprocess.run(["git", "init"], check=True)
        print("[+] Local git repository initialized.")
        
    # create gitignore to avoid uploading temp_clone or venv
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w") as f:
            f.write("venv/\ntemp_clone/\n__pycache__/\n*.pyc\n.env\n")
        print("[+] Created .gitignore file.")
        
    # stage and commit files
    subprocess.run(["git", "add", "."], check=True)
    
    # check if there's any commit already
    status = subprocess.run(["git", "status"], capture_output=True, text=True)
    if "nothing to commit" not in status.stdout:
        subprocess.run(["git", "commit", "-m", "chore: initial commit for Auto-Patch agent"], check=True)
        print("[+] Files commited.")
        
    subprocess.run(["git", "branch", "-M", "main"], check=True)
    
    # setup the remote URL with credentials
    remote_url = f"https://{token}@github.com/{username}/{repo_name}.git"
    
    # check if origin already exists
    remotes = subprocess.run(["git", "remote"], capture_output=True, text=True)
    if "origin" in remotes.stdout:
        subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)
    else:
        subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        
    # push the files to main branch
    print(f"[*] Pushing files to GitHub origin main...")
    push_status = subprocess.run(["git", "push", "-u", "origin", "main"])
    
    if push_status.returncode == 0:
        print(f"\n[🎉] Success! Project uploaded to: https://github.com/{username}/{repo_name}")
    else:
        print("[!] Push failed. Make sure you have git installed and configured on your path.")

if __name__ == "__main__":
    token = GITHUB_TOKEN if GITHUB_TOKEN else get_token_from_user()
    username, repo_name = create_github_repo(token)
    initialize_and_push_git(username, repo_name, token)
