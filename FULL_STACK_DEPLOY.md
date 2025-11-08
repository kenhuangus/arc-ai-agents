# Full Stack Deployment Guide
## Deploy Arc AI Agents with Complete Functionality

This guide will help you deploy both backend (API + AI Agents) and frontend (Streamlit UI) so the full system works.

---

## 🎯 **Goal: Show Full Functionality**

After deployment:
- ✅ AI Agents actually process intents
- ✅ Intent creation works
- ✅ Live matching with Claude & Gemini
- ✅ Real-time agent visualization
- ✅ All features functional

---

## 🚀 **OPTION A: Railway.app (Recommended - 20 min)**

Railway provides free tier and is perfect for hackathons.

### **Step 1: Sign Up for Railway**

1. Go to: **https://railway.app**
2. Click **"Start a New Project"**
3. Sign in with GitHub
4. Verify your account (may need to add payment method for free tier, $5 credit)

### **Step 2: Deploy Backend API**

1. **Click "New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose **"kenhuangus/arc-ai-agents"**
4. Railway will detect your Python app

### **Step 3: Configure Environment Variables**

In Railway dashboard, go to **Variables** tab and add:

```bash
# AI/LLM API Keys (use your actual keys from config/.env)
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY_HERE
GOOGLE_API_KEY=AIzaYOUR_KEY_HERE
LANGSMITH_API_KEY=lsv2_pt_YOUR_KEY_HERE
LANGSMITH_PROJECT=pr-whispered-guideline-36
LANGSMITH_TRACING=false

# Arc Network
ARC_TESTNET_RPC_URL=https://rpc.testnet.arc.network
ARC_TESTNET_CHAIN_ID=5042002
ARC_TESTNET_EXPLORER_URL=https://testnet.arcscan.app

# Deployment Keys
PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
PAYMENT_PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

# Contract Addresses
INTENT_REGISTRY_ADDRESS=0x0DCd1Bf9A1b36cE34237eEaFef220932846BCD82
AUCTION_ESCROW_ADDRESS=0x0B306BF915C4d645ff596e518fAf3F9669b97016
PAYMENT_ROUTER_ADDRESS=0x9A676e781A523b5d0C0e43731313A708CB607508

# Payment Config
PAYMENT_TOKEN_ADDRESS=0x3600000000000000000000000000000000000000
PAYMENT_NETWORK=arc_testnet
PAYMENT_RPC_URL=https://rpc.testnet.arc.network
PAYMENT_CHAIN_ID=5042002

# Database (Railway will provide)
DATABASE_URL=sqlite:///./arc_coordination.db

# API Config
API_HOST=0.0.0.0
API_PORT=$PORT
```

**IMPORTANT:** Railway will auto-assign `$PORT` - don't change it!

### **Step 4: Deploy**

1. Railway will automatically start building
2. Wait 5-10 minutes for deployment
3. Once deployed, you'll see a URL like:
   ```
   https://arc-ai-agents-production.up.railway.app
   ```
4. **Copy this URL!**

### **Step 5: Test Backend API**

Visit your Railway URL:
```
https://your-app.railway.app/health
```

Should return:
```json
{"status": "healthy", "timestamp": "..."}
```

Also check:
```
https://your-app.railway.app/docs
```

Should show FastAPI Swagger docs!

### **Step 6: Update Streamlit Cloud**

1. Go to: https://share.streamlit.io
2. Click your app → Settings → Secrets
3. **Update this line:**
   ```toml
   API_BASE_URL = "https://your-app.railway.app"
   ```
   (Replace with your actual Railway URL)
4. Save
5. Wait 2 minutes for Streamlit to redeploy

### **Step 7: Test Full Functionality**

Visit your Streamlit app:
1. **Try creating an intent** - should work now!
2. **Click "AI Agents Demo"** - agents will actually process!
3. **Watch real-time** - Claude & Gemini analyze in real-time!

---

## 🚀 **OPTION B: Render.com (Alternative - 25 min)**

### **Step 1: Sign Up**
1. Go to: https://render.com
2. Sign up with GitHub

### **Step 2: Create Web Service**
1. Click **"New +"** → **"Web Service"**
2. Connect to **kenhuangus/arc-ai-agents**
3. Configure:
   - **Name:** arc-ai-agents-api
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn services.api:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

### **Step 3: Add Environment Variables**
Same as Railway (see above)

### **Step 4: Deploy**
Wait 10-15 minutes for first deploy

Your URL will be:
```
https://arc-ai-agents-api.onrender.com
```

### **Step 5: Update Streamlit**
Same as Railway Step 6

---

## 🚀 **OPTION C: Fly.io (Advanced - 30 min)**

Requires Dockerfile and fly.toml configuration.

### **Quick Setup:**

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Launch app
flyctl launch

# Set secrets
flyctl secrets set ANTHROPIC_API_KEY="..." GOOGLE_API_KEY="..."

# Deploy
flyctl deploy
```

---

## 📊 **Comparison Table**

| Platform | Setup Time | Free Tier | Auto-Deploy | Ease |
|----------|------------|-----------|-------------|------|
| **Railway** | 20 min | $5 credit | ✅ Yes | ⭐⭐⭐⭐⭐ |
| **Render** | 25 min | 750 hrs/mo | ✅ Yes | ⭐⭐⭐⭐ |
| **Fly.io** | 30 min | Limited | ⚠️ Manual | ⭐⭐⭐ |

**Recommendation:** Use Railway.app for fastest deployment!

---

## ✅ **Verification Checklist**

After deployment:

- [ ] Backend API URL is accessible
- [ ] `/health` endpoint returns healthy
- [ ] `/docs` shows Swagger UI
- [ ] Streamlit `API_BASE_URL` updated
- [ ] Streamlit app redeployed
- [ ] Intent creation works
- [ ] AI agents process in real-time
- [ ] No connection errors in logs

---

## 🎬 **For Your Demo Video**

Once deployed, you can show:

1. **Create Intent** - Actually submit and see it work!
2. **AI Agents Processing** - Watch Claude & Gemini analyze live
3. **Match Finding** - See real matching with confidence scores
4. **Fraud Detection** - Show risk scores being calculated
5. **API Documentation** - Show /docs page
6. **Full Stack** - Frontend ↔ Backend ↔ Blockchain

---

## 🆘 **Troubleshooting**

### **Issue: Railway build fails**
**Fix:** Check logs for missing dependencies. Make sure requirements.txt is complete.

### **Issue: App starts but crashes**
**Fix:** Check environment variables are set correctly. View Railway logs.

### **Issue: Streamlit can't connect to API**
**Fix:**
- Verify Railway URL is correct
- Check CORS is enabled (already configured in api.py)
- Ensure API_BASE_URL in Streamlit secrets matches Railway URL exactly

### **Issue: AI agents timeout**
**Fix:** Claude/Gemini API calls may take time. This is normal for first request.

---

## 💰 **Cost Estimate**

**Railway:**
- Free tier: $5 credit (enough for hackathon)
- After free tier: ~$5-10/month

**Render:**
- Free tier: 750 hours/month (plenty for demo)
- Spins down after 15 min inactivity

**For Hackathon:** Both are FREE! ✅

---

## 🔄 **Auto-Deploy Setup**

Once configured, every push to GitHub will auto-deploy:

```bash
git add .
git commit -m "Update feature"
git push origin master
# Railway/Render auto-deploys in 2-3 minutes!
```

---

## 📝 **Important Notes**

1. **Database:** SQLite works for demo. For production, upgrade to PostgreSQL.
2. **API Keys:** Keep secure! Never commit to git.
3. **Rate Limits:** Claude/Gemini have rate limits. Be mindful during demo.
4. **Cold Starts:** First request may be slow. Keep app warm during demo.

---

## 🎯 **Next Steps After Deployment**

1. **Test thoroughly** - Try all features
2. **Take screenshots** - Capture working features
3. **Record video** - Show full functionality
4. **Update README** - Add deployment URLs
5. **Submit to hackathon** - You're ready!

---

## 🏆 **You'll Be Able to Show:**

✅ Full multi-agent AI system working live
✅ Real-time Claude + Gemini processing
✅ Intent creation and matching
✅ Fraud detection with confidence scores
✅ Complete end-to-end workflow
✅ Production-ready deployment

**This is WAY more impressive than demo mode!** 🚀

Good luck!
