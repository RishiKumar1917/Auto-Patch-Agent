import os
import sys
import shutil
from github import Github
from git import Repo
from dotenv import load_dotenv

# import our custom files here
from scanner import scan_code
from patcher import patch_vulnerability
from verifier import verify_code_syntax

# load the env varibles
load_dotenv()

# setup the config settings
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OLLAMA_MODEL = "qwen2.5"

if not GITHUB_TOKEN:
    print("[!] Warning: GITHUB_TOKEN not found in environment. Please add it to your .env file.")

def run_github_patch_flow(target_repo_name, engine="Ollama"):
    """
    Automates the entire open source contribution flow:
    1. Forks the target repository to your GitHub account.
    2. Clones your fork locally.
    3. Scans the codebase for vulnerabilities.
    4. Patches vulnerabilities using LLM.
    5. Verifies code syntax.
    6. Commits, pushes, and opens a Pull Request to the original repository.
    """
    if not GITHUB_TOKEN:
        raise ValueError("GitHub Personal Access Token (GITHUB_TOKEN) is required in the .env file.")
        
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    
    print(f"[*] Authenticated as GitHub user: {user.login}")
    
    # first we fork the origional repo to our github
    print(f"[*] Fetching target repository: {target_repo_name}...")
    original_repo = g.get_repo(target_repo_name)
    
    print(f"[*] Forking {target_repo_name} to your account ({user.login})...")
    forked_repo = user.create_fork(original_repo)
    print(f"[+] Fork created successfully: {forked_repo.html_url}")
    
    # now clone the fork locallly
    local_dir = os.path.join(os.getcwd(), "temp_clone")
    if os.path.exists(local_dir):
        print(f"[*] Cleaning up old temporary directory: {local_dir}")
        shutil.rmtree(local_dir)
        
    # inject token in url for auth
    clone_url = forked_repo.clone_url.replace("https://", f"https://{GITHUB_TOKEN}@")
    print(f"[*] Cloning fork to local directory: {local_dir}...")
    repo = Repo.clone_from(clone_url, local_dir)
    print("[+] Clone complete.")
    
    # scan all python files in cloned dir
    print("[*] Scanning repository for security vulnerabilities...")
    findings = []
    for root, dirs, files in os.walk(local_dir):
        # skip venv and git folders to save time
        if any(ignored in root for ignored in ["venv", ".git", "__pycache__", "egg-info"]):
            continue
            
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    vulns = scan_code(content)
                    if vulns:
                        print(f"[!] Found {len(vulns)} issues in: {os.path.relpath(file_path, local_dir)}")
                        findings.append({
                            "file_path": file_path,
                            "relative_path": os.path.relpath(file_path, local_dir),
                            "content": content,
                            "vulnerabilities": vulns
                        })
                except Exception as e:
                    print(f"[!] Error scanning {file}: {str(e)}")
                    
    if not findings:
        print("[+] No vulnerabilities detected in the repository. Cleanup complete.")
        shutil.rmtree(local_dir)
        return
        
    # create new branch for the security patch
    branch_name = "security/patch-vulnerabilities"
    print(f"[*] Creating new git branch: {branch_name}")
    new_branch = repo.create_head(branch_name)
    new_branch.checkout()
    
    # patch files
    patched_files_count = 0
    patch_details_summary = ""
    
    for finding in findings:
        file_path = finding["file_path"]
        relative_path = finding["relative_path"]
        current_content = finding["content"]
        
        # apply patch for each vuln found
        patched_content = current_content
        for vuln in finding["vulnerabilities"]:
            print(f"[*] Patching vulnerability at line {vuln['line']} in {relative_path}...")
            
            try:
                # call the patcher file to run llm
                engine_choice = "Ollama" if engine == "Ollama" else "Groq"
                patched_content = patch_vulnerability(
                    code_snippet=patched_content,
                    vulnerability=vuln,
                    engine=engine_choice,
                    ollama_model=OLLAMA_MODEL,
                    groq_key=GROQ_API_KEY
                )
                
                # verify that code compiles correctly
                is_valid, err = verify_code_syntax(patched_content)
                if is_valid:
                    print(f"[+] Patch verified successfully for line {vuln['line']}.")
                    patch_details_summary += f"- Fixed {vuln['id']} on line {vuln['line']} in `{relative_path}`: {vuln['description']}\n"
                else:
                    print(f"[!] Warning: patch syntax invalid, skipping this patch. Error: {err}")
                    patched_content = current_content # Roll back
            except Exception as e:
                print(f"[!] Error generating patch: {str(e)}")
                
        # if successfully patched then write back to file and git add it
        if patched_content != current_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(patched_content)
            repo.index.add([file_path])
            patched_files_count += 1
            
    if patched_files_count == 0:
        print("[-] No patches were successfully applied or verified. Exiting.")
        shutil.rmtree(local_dir)
        return
        
    # commit changes and push to our fork repo
    print("[*] Committing changes...")
    repo.index.commit("chore(security): fix detected vulnerabilities automatically using AI SecOps Agent")
    
    print(f"[*] Pushing branch {branch_name} to your fork on GitHub...")
    origin = repo.remote(name="origin")
    origin.push(branch_name)
    print("[+] Push complete.")
    
    # create the actual PR to the origional repository
    pr_title = "security(patch): fix vulnerabilities identified by automated SecOps Agent"
    pr_body = (
        "### 🛡️ Automated Security Patch Report\n\n"
        "This Pull Request was generated by **Auto-Patch**, an agentic security automation tool. "
        "The following vulnerabilities were detected and resolved:\n\n"
        f"{patch_details_summary}\n"
        "**Note:** Please review and run local tests before merging."
    )
    
    print(f"[*] Opening Pull Request from {user.login}:{branch_name} to {original_repo.owner.login}:master/main...")
    try:
        pr = original_repo.create_pull(
            title=pr_title,
            body=pr_body,
            base=original_repo.default_branch,
            head=f"{user.login}:{branch_name}"
        )
        print(f"[🎉] Pull Request created successfully! View it here: {pr.html_url}")
    except Exception as e:
        print(f"[!] Error creating Pull Request (you may already have a pending PR): {str(e)}")
        
    # clean up the temp files
    print("[*] Cleaning up temporary clone directory...")
    shutil.rmtree(local_dir)
    print("[+] Finished flow.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python github_agent.py <owner/repo> [engine: Ollama/Groq]")
        sys.exit(1)
        
    repo_target = sys.argv[1]
    engine_choice = sys.argv[2] if len(sys.argv) > 2 else "Ollama"
    run_github_patch_flow(repo_target, engine_choice)
