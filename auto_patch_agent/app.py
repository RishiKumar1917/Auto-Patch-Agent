import streamlit as st
import os
import difflib
from dotenv import load_dotenv

# Import our custom modules
from scanner import scan_code
from patcher import patch_vulnerability
from verifier import verify_code_syntax

# Load environment variables if present
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Auto-Patch | AI DevSecOps Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Sleek CSS for Dark-Mode Premium Aesthetics
st.markdown("""
<style>
    .main {
        background-color: #0f111a;
        color: #e6edf3;
    }
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    .vuln-card {
        padding: 15px;
        border-radius: 8px;
        background-color: #1e1e2e;
        border-left: 5px solid #ef4444;
        margin-bottom: 10px;
    }
    .success-card {
        padding: 15px;
        border-radius: 8px;
        background-color: #1b2e1b;
        border-left: 5px solid #22c55e;
        margin-bottom: 10px;
    }
    .badge {
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .badge-critical { background-color: #ef4444; color: white; }
    .badge-high { background-color: #f97316; color: white; }
    .badge-medium { background-color: #eab308; color: black; }
</style>
""", unsafe_allow_index=True)

# App Header
st.title("🛡️ Auto-Patch: AI-Agentic DevSecOps Triage Engine")
st.markdown("*Autonomous Vulnerability Identification, Verification, and Remediation Harness*")
st.write("---")

# Sidebar Configuration
st.sidebar.header("🤖 Agent Settings")

# Select LLM Engine
engine = st.sidebar.selectbox(
    "Select LLM Engine",
    ["Ollama (Local)", "Groq (Cloud)"]
)

# API Keys and Models setup
groq_api_key = os.getenv("GROQ_API_KEY", "")
ollama_model = "qwen2.5"
groq_model = "llama-3.3-70b-specdec"

if engine == "Ollama (Local)":
    st.sidebar.info("Using local Ollama. Make sure Ollama is running (`ollama run qwen2.5`).")
    ollama_model = st.sidebar.text_input("Ollama Model Name", value="qwen2.5")
else:
    # Look for GROQ_API_KEY in env, or let user input it
    user_groq_key = st.sidebar.text_input("Groq API Key", value=groq_api_key, type="password")
    if user_groq_key:
        groq_api_key = user_groq_key
    else:
        st.sidebar.warning("Please enter a Groq API Key.")
    
    groq_model = st.sidebar.selectbox(
        "Groq Model",
        ["llama-3.3-70b-specdec", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]
    )

# Main columns
col_editor, col_results = st.columns([3, 2])

# Left column: Code Editor
with col_editor:
    st.subheader("📝 Source Code Analysis")
    
    # Preset Demo Button
    if st.button("🔌 Load Vulnerable Demo Code"):
        try:
            with open("demo_vulnerable.py", "r") as f:
                code_content = f.read()
            st.session_state["code_input"] = code_content
        except FileNotFoundError:
            st.error("demo_vulnerable.py file not found.")
            
    # TextInput Area
    code_input = st.text_area(
        "Paste your Python code here:",
        value=st.session_state.get("code_input", ""),
        height=350,
        key="code_area"
    )
    
    if code_input:
        st.session_state["code_input"] = code_input

# Right column: Scan Results
with col_results:
    st.subheader("🔍 Scan & Vulnerability Reports")
    
    scan_triggered = st.button("🚀 Run Security Scan")
    
    if "vulnerabilities" not in st.session_state:
        st.session_state["vulnerabilities"] = []
        
    if scan_triggered and code_input:
        with st.spinner("Analyzing code for security flaws..."):
            vulns = scan_code(code_input)
            st.session_state["vulnerabilities"] = vulns
            
        if not vulns:
            st.success("✅ No vulnerabilities detected! Code matches baseline security requirements.")
        else:
            st.warning(f"⚠️ Detected {len(vulns)} vulnerability findings.")
            
    # Display vulnerabilities
    for idx, vuln in enumerate(st.session_state["vulnerabilities"]):
        badge_style = "badge-critical" if vuln["severity"] == "CRITICAL" else "badge-high"
        
        st.markdown(f"""
        <div class="vuln-card">
            <span class="badge {badge_style}">{vuln['severity']}</span>
            <strong>Line {vuln['line']}: {vuln['id']}</strong>
            <p style="margin: 5px 0;">{vuln['description']}</p>
            <code style="background-color: #2e2e3e; padding: 2px 4px; border-radius: 4px; color: #f43f5e;">{vuln['code']}</code>
        </div>
        """, unsafe_allow_index=True)
        
        # Patching triggers
        patch_btn_key = f"patch_{idx}_{vuln['line']}"
        if st.button(f"🛠️ Auto-Patch Issue #{idx+1}", key=patch_btn_key):
            with st.spinner(f"Agent generating secure fix for Line {vuln['line']}..."):
                try:
                    # Determine LLM Engine and Call
                    engine_name = "Ollama" if "Local" in engine else "Groq"
                    patched_code = patch_vulnerability(
                        code_snippet=code_input,
                        vulnerability=vuln,
                        engine=engine_name,
                        ollama_model=ollama_model,
                        groq_key=groq_api_key,
                        groq_model=groq_model
                    )
                    
                    # Verify syntax
                    is_valid, error_msg = verify_code_syntax(patched_code)
                    
                    if is_valid:
                        st.success("🎉 Secure patch generated and verified successfully!")
                        st.session_state[f"patch_result_{idx}"] = patched_code
                    else:
                        st.error(f"❌ Verification Failed. Patched code contains syntax errors:\n{error_msg}")
                        st.text_area("Faulty generated code:", value=patched_code, height=150)
                except Exception as e:
                    st.error(f"Error during patching: {str(e)}")

# Bottom section: Code Diff & Applier
if any(f"patch_result_{i}" in st.session_state for i in range(len(st.session_state["vulnerabilities"]))):
    st.write("---")
    st.subheader("🔄 Automated Patch Verification & Code Diff")
    
    # Gather patches
    for idx, vuln in enumerate(st.session_state["vulnerabilities"]):
        patch_key = f"patch_result_{idx}"
        if patch_key in st.session_state:
            original_code = code_input.splitlines(keepends=True)
            patched_code_lines = st.session_state[patch_key].splitlines(keepends=True)
            
            # Compute diff
            diff = difflib.unified_diff(
                original_code,
                patched_code_lines,
                fromfile="original.py",
                tofile="patched.py",
                n=3
            )
            diff_text = "".join(diff)
            
            col_diff, col_patched_file = st.columns(2)
            
            with col_diff:
                st.markdown(f"**Vulnerability Fix Diff (Issue #{idx+1})**")
                if diff_text:
                    st.code(diff_text, language="diff")
                else:
                    st.info("No modifications were detected between original and patched code. The LLM decided no changes were necessary.")
                    
            with col_patched_file:
                st.markdown("**Patched Output Code**")
                st.code(st.session_state[patch_key], language="python")
                
                # Apply button
                if st.button("💾 Apply & Update Source Code", key=f"apply_{idx}"):
                    st.session_state["code_input"] = st.session_state[patch_key]
                    st.session_state["vulnerabilities"] = [] # Clear reports after updating
                    st.rerun()

# Explainer / How it works
st.write("---")
with st.expander("ℹ️ How it works (AI SecOps Agent Workflow)"):
    st.markdown("""
    1. **Static Analysis:** The application runs a rule-based AST/regex scan on your input code to extract details of vulnerabilities (e.g., Line, severity, context).
    2. **Contextual Prompting:** The agent formats the code and scan report, requesting the selected LLM to act as a Security Engineer and refactor the vulnerability.
    3. **Syntax Verification:** The generated code is compiled programmatically (`ast.parse`) to verify it is free of syntax errors.
    4. **Code Differencing:** A unified diff is computed so the developer can review the proposed changes before committing.
    """)
