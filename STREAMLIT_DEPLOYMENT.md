# Streamlit Cloud Deployment Guide
## Arc AI Agents - Hackathon Demo

---

## 🚀 Quick Deployment Options

### **OPTION A: Streamlit Cloud Only (Demo Mode)** ⭐ RECOMMENDED FOR HACKATHON
Deploy just the UI with demo data. Best for judging/showcase.

### **OPTION B: Full Stack on Railway**
Deploy backend API + Streamlit UI together. Best for full functionality.

---

## OPTION A: Streamlit Cloud (5 Minutes) ⭐

### Step 1: Prepare Repository

Ensure your GitHub repository is **public**:

```bash
# Check current visibility
git remote -v

# If private, go to GitHub:
# Settings → Danger Zone → Change visibility → Make Public
```

### Step 2: Add .gitignore

Ensure these are in `.gitignore`:
```
config/.env
.streamlit/secrets.toml
*.db
venv/
__pycache__/
*.pyc
.DS_Store
logs/*.log
```

### Step 3: Commit Configuration Files

```bash
git add .streamlit/config.toml
git add .streamlit/secrets.toml.example
git add requirements.txt
git commit -m "Add Streamlit Cloud configuration"
git push origin master
```

### Step 4: Deploy on Streamlit Cloud

1. **Go to**: https://share.streamlit.io/

2. **Sign in** with GitHub

3. **Click "New app"**

4. **Fill in:**
   - Repository: `your-username/arc-contest`
   - Branch: `master` or `main`
   - Main file path: `ui/streamlit_app.py`

5. **Add Secrets** (Click "Advanced settings" → "Secrets"):

Copy and paste from your `config/.env` with proper TOML format:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-..."

GOOGLE_API_KEY = "AIza..."

LANGSMITH_API_KEY = "lsv2_pt_..."
LANGSMITH_PROJECT = "pr-whispered-guideline-36"
LANGSMITH_TRACING = "false"

ARC_TESTNET_RPC_URL = "https://rpc.testnet.arc.network"
ARC_TESTNET_CHAIN_ID = "5042002"
ARC_TESTNET_EXPLORER_URL = "https://testnet.arcscan.app"

PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

INTENT_REGISTRY_ADDRESS = "0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82"
AUCTION_ESCROW_ADDRESS = "0x0B306BF915C4d645ff596e518fAf3F9669b97016"
PAYMENT_ROUTER_ADDRESS = "0x9A676e781A523b5d0C0e43731313A708CB607508"

PAYMENT_TOKEN_ADDRESS = "0x3600000000000000000000000000000000000000"
PAYMENT_NETWORK = "arc_testnet"
PAYMENT_RPC_URL = "https://rpc.testnet.arc.network"
PAYMENT_CHAIN_ID = "5042002"

API_BASE_URL = "http://localhost:8000"

DATABASE_URL = "sqlite:///./arc_coordination.db"
```

6. **Click "Deploy"**

7. **Wait 5-10 minutes** for deployment to complete

8. **Get your URL**: `https://[app-name]-[random].streamlit.app`

### Step 5: Test Deployed App

Visit your app URL and verify:
- [ ] UI loads without errors
- [ ] Can navigate between pages
- [ ] AI Demo page is accessible
- [ ] X402 Payment Demo works

---

## OPTION B: Full Stack on Railway (20 Minutes)

If you want the full backend API + frontend:

### Step 1: Sign Up for Railway

1. Go to https://railway.app
2. Sign in with GitHub
3. Verify your account (may need credit card for free tier, but won't be charged)

### Step 2: Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose `arc-contest` repository

### Step 3: Add Services

Railway will detect multiple services. Add:

**Service 1: API (Backend)**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn services.api:app --host 0.0.0.0 --port $PORT`
- Port: 8000

**Service 2: Streamlit (Frontend)**
- Build Command: `pip install -r requirements.txt`
- Start Command: `streamlit run ui/streamlit_app.py --server.port $PORT --server.headless true`
- Port: 8501

### Step 4: Set Environment Variables

For **both services**, add all variables from `config/.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
GOOGLE_API_KEY=AIza...
ARC_TESTNET_RPC_URL=https://rpc.testnet.arc.network
# ... (copy all from config/.env)
```

**Important:** Update `API_BASE_URL` in Streamlit service to point to your Railway API URL:
```
API_BASE_URL=https://[your-api-service].railway.app
```

### Step 5: Deploy

1. Click "Deploy" for both services
2. Wait for build to complete
3. Railway will give you URLs for both services

### Step 6: Test

- API: `https://[api-service].railway.app/health`
- UI: `https://[ui-service].railway.app`

---

## OPTION C: Replit (Alternative, 10 Minutes)

### Step 1: Import from GitHub

1. Go to https://replit.com
2. Click "Create Repl" → "Import from GitHub"
3. Paste your repo URL

### Step 2: Configure .replit

Create `.replit` file:
```toml
language = "python3"
run = "streamlit run ui/streamlit_app.py --server.port 8080 --server.headless true"

[nix]
channel = "stable-21_11"

[deployment]
run = ["sh", "-c", "streamlit run ui/streamlit_app.py --server.port 8080 --server.headless true"]
```

### Step 3: Add Secrets

In Replit:
1. Click "Secrets" (🔒 icon)
2. Add each environment variable from `config/.env`

### Step 4: Run

Click "Run" button. Replit will:
- Install dependencies from requirements.txt
- Start Streamlit
- Give you a public URL

---

## 🔧 Troubleshooting

### Issue: Module Import Errors

**Error:** `ModuleNotFoundError: No module named 'services'`

**Fix:** Create `packages.txt` (for Streamlit Cloud):
```
python3-dev
build-essential
```

And ensure `requirements.txt` has all dependencies.

---

### Issue: Database Connection Errors

**Error:** `Database file not found`

**Fix:** For demo purposes, create an in-memory database or use SQLite with proper path:

Update in your Streamlit app:
```python
# Check if database exists, if not use demo mode
if not os.path.exists("arc_coordination.db"):
    st.warning("Running in demo mode - no database connection")
    # Use demo data instead
```

---

### Issue: API Connection Timeout

**Error:** `Connection to localhost:8000 failed`

**Fix:** Two options:

1. **Demo Mode:** Modify UI to work without API:
```python
try:
    sdk = ArcSDK(...)
except Exception:
    st.info("Running in demo mode without backend API")
    # Use mock data
```

2. **Deploy API:** Use Railway/Render to deploy API and update `API_BASE_URL`

---

### Issue: Secrets Not Loading

**Error:** `KeyError: 'ANTHROPIC_API_KEY'`

**Fix:** In Streamlit Cloud, secrets are accessed via `st.secrets`:

```python
import streamlit as st

# Instead of os.getenv()
api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
```

Update your app to check for Streamlit secrets first:
```python
def get_env_var(key, default=""):
    # Try Streamlit secrets first (for cloud deployment)
    if hasattr(st, 'secrets') and key in st.secrets:
        return st.secrets[key]
    # Fall back to environment variables (for local)
    return os.getenv(key, default)
```

---

## 📋 Pre-Deployment Checklist

- [ ] GitHub repository is **public**
- [ ] `.gitignore` excludes secrets and sensitive files
- [ ] `requirements.txt` is complete and up-to-date
- [ ] `.streamlit/config.toml` is committed
- [ ] `.streamlit/secrets.toml.example` is committed (NOT secrets.toml!)
- [ ] `README.md` has setup instructions
- [ ] Tested locally with `streamlit run ui/streamlit_app.py`
- [ ] All API keys are ready to copy into secrets

---

## 🎯 Recommended for Hackathon Submission

**Best Option:** Streamlit Cloud (Option A)

**Why:**
- ✅ Free tier is generous
- ✅ Deploys in 5 minutes
- ✅ Automatic HTTPS
- ✅ Good performance
- ✅ Easy to update (just push to GitHub)

**Preparation Time:**
- Initial setup: 10 minutes
- Testing: 5 minutes
- Total: **15 minutes**

**Your Submission URL:**
```
Demo: https://arc-ai-agents-[random].streamlit.app
GitHub: https://github.com/[username]/arc-contest
```

---

## 📞 Support

If deployment fails:
- Check Streamlit Community: https://discuss.streamlit.io
- Railway Discord: https://discord.gg/railway
- Replit Support: https://replit.com/support

**Common Solutions:**
- Clear cache and redeploy
- Check logs for specific errors
- Verify all secrets are properly formatted (no quotes issues)
- Ensure Python version compatibility (3.11+ required)

---

## 🚀 After Deployment

1. **Test thoroughly:**
   - Navigate to each page
   - Try submitting an intent
   - Check AI Demo page
   - Verify no console errors

2. **Get feedback:**
   - Share with a friend
   - Test on mobile
   - Check loading speed

3. **Update README:**
   - Add deployed URL to README.md
   - Update "Quick Start" section

4. **Take screenshots:**
   - Homepage
   - AI agents in action
   - Results display
   - For your presentation/video

Good luck with your deployment! 🎉
