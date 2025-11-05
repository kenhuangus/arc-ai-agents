# Arc Coordination System - UI Guide

## 🎨 Professional Streamlit Dashboard

A beautiful, full-featured web interface for the Arc Coordination System.

---

## Features

### 📊 **Dashboard**
- Real-time system metrics with gradient cards
- Interactive pie and bar charts using Plotly
- Recent activity feed for intents and matches
- Quick stats in sidebar

### ➕ **Create Intent**
- Intuitive form with validation
- Bid/Ask selection with smart defaults
- Real-time price and quantity inputs
- Success confirmations with balloons animation
- Comprehensive error handling

### 📋 **My Intents**
- Filter by active/matched status
- Expandable intent cards with full details
- One-click cancel functionality
- Summary metrics

### 🔄 **Matches**
- Status-based filtering (pending, funded, settled, etc.)
- Interactive match cards
- Fund escrow directly from UI
- Real-time status updates

### 📖 **Order Book**
- Live bid/ask order display
- Interactive depth charts
- Spread calculation and visualization
- Multi-asset support (USD, ETH, BTC, USDC)

### 💳 **Payments**
- Create Stripe payment intents
- Verify and anchor payments on-chain
- Full AP2 integration
- Transaction tracking

### 🔐 **Mandates**
- Register AP2 payment mandates
- Configurable scope and validity
- Success confirmations

### ⚙️ **System Info**
- Network configuration display
- Contract addresses
- API health check
- Account information

---

## Design Features

### 🎨 **Professional Styling**
- Gradient backgrounds on cards
- Color-coded status badges
- Smooth animations and transitions
- Responsive layout
- Custom CSS styling

### 📊 **Data Visualization**
- Plotly charts for interactive exploration
- Pie charts for status distribution
- Bar charts for match status
- Depth charts for order books
- Real-time metric updates

### 🎯 **User Experience**
- Loading spinners for async operations
- Success/error message boxes
- Expandable sections for details
- Tooltips and help text
- Refresh buttons on all pages
- Balloons animation for successes

### 🔄 **Real-Time Features**
- Auto-refresh capabilities
- Live data updates
- Instant status changes
- Background API calls

---

## How to Run

### Prerequisites
```bash
# Ensure services are running
# 1. Anvil node on port 8545
# 2. REST API on port 8000
```

### Start Streamlit
```bash
# Activate virtual environment
source venv/bin/activate

# Run Streamlit app
streamlit run ui/streamlit_app.py

# Or with custom port
streamlit run ui/streamlit_app.py --server.port 8501
```

### Access Dashboard
```
Open browser to: http://localhost:8501
```

---

## Page Walkthrough

### 1. Dashboard (📊)
**Purpose**: Overview of entire system

**Features**:
- 4 metric cards with gradients
- Intent status pie chart
- Match status bar chart
- Recent activity feed
- Quick stats in sidebar

**Actions**:
- View system health
- Navigate to other pages
- Monitor activity

---

### 2. Create Intent (➕)
**Purpose**: Submit new intents to the blockchain

**Workflow**:
1. Select intent type (bid/ask)
2. Enter price and quantity
3. Choose settlement asset
4. Set validity period
5. Provide AP2 mandate ID
6. Add description
7. Click "🚀 Submit Intent"

**Result**:
- Intent submitted to blockchain
- Transaction hash displayed
- Balloons animation
- Success confirmation box

---

### 3. My Intents (📋)
**Purpose**: View and manage your intents

**Features**:
- Filter by active/unmatched status
- Expandable intent cards
- Cancel active intents
- View full intent details
- Summary metrics

**Actions**:
- Cancel intents
- Refresh list
- View intent details

---

### 4. Matches (🔄)
**Purpose**: View and interact with matches

**Features**:
- Filter by status (pending, funded, settled, etc.)
- Interactive match cards
- Fund escrow functionality
- Status badges
- Party information

**Actions**:
- Fund escrow
- View match details
- Monitor settlement status

---

### 5. Order Book (📖)
**Purpose**: View live order book

**Features**:
- Separate bid/ask displays
- Interactive depth charts
- Spread calculation
- Multi-asset support
- Data tables

**Visualization**:
- Green bars for bids
- Red bars for asks
- Spread percentage
- Price/quantity data

---

### 6. Payments (💳)
**Purpose**: Manage payment intents

**Features**:
- Two tabs: Create / Verify
- Stripe integration
- On-chain anchoring
- Transaction tracking

**Workflow (Create)**:
1. Enter amount and currency
2. Specify payer and payee
3. Provide mandate ID
4. Create payment intent
5. Receive client secret

**Workflow (Verify)**:
1. Enter payment intent ID
2. Click verify
3. Payment verified on Stripe
4. Proof anchored on-chain

---

### 7. Mandates (🔐)
**Purpose**: Register AP2 mandates

**Features**:
- Registration form
- Scope configuration
- Validity period setting
- Success confirmations

**Workflow**:
1. Generate or enter mandate ID
2. Set issuer address
3. Specify subject (payer)
4. Define scope
5. Set validity period
6. Register mandate

---

### 8. System Info (⚙️)
**Purpose**: View system configuration

**Features**:
- Network configuration
- Contract addresses
- Account information
- API health status
- Documentation links

---

## Keyboard Shortcuts

- `R` - Refresh current page (Streamlit default)
- `C` - Clear cache (Streamlit default)
- `F5` - Full page refresh (browser)

---

## Customization

### Change Colors
Edit `ui/streamlit_app.py` CSS section:
```python
--primary-color: #1f77b4;
--secondary-color: #ff7f0e;
--success-color: #2ca02c;
```

### Modify Metrics
Edit individual page functions:
```python
def show_dashboard(sdk: ArcSDK):
    # Add custom metrics here
    pass
```

### Add New Pages
1. Create page function
2. Add to navigation radio
3. Add to main routing

---

## Troubleshooting

### UI Won't Load
```bash
# Check if API is running
curl http://localhost:8000/health

# Check if Streamlit is installed
pip list | grep streamlit

# Restart Streamlit
pkill -f streamlit
streamlit run ui/streamlit_app.py
```

### SDK Errors
```bash
# Verify environment variables
cat config/.env

# Check contract addresses are set
echo $INTENT_REGISTRY_ADDRESS
```

### Slow Loading
```bash
# Clear Streamlit cache
streamlit cache clear

# Reduce data fetch frequency
# Edit page refresh intervals in code
```

---

## Advanced Features

### Real-Time Updates
The UI includes manual refresh buttons. For auto-refresh:
```python
# Add to any page function
import time
st_autorefresh = st.experimental_rerun
time.sleep(5)  # 5 second interval
st_autorefresh()
```

### Export Data
Add export functionality:
```python
# In any page
import pandas as pd
df = pd.DataFrame(intents)
csv = df.to_csv().encode('utf-8')
st.download_button("Download CSV", csv, "intents.csv")
```

### Custom Themes
Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor="#1f77b4"
backgroundColor="#ffffff"
secondaryBackgroundColor="#f0f2f6"
textColor="#262730"
font="sans serif"
```

---

## Production Deployment

### Using Streamlit Cloud
```bash
# 1. Push to GitHub
git add .
git commit -m "Add Streamlit UI"
git push

# 2. Deploy on streamlit.io
# - Connect GitHub repo
# - Set environment variables
# - Deploy!
```

### Using Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8501"]
```

### Environment Variables
Set these in production:
```bash
API_BASE_URL=https://your-api.com
ARC_TESTNET_RPC_URL=https://rpc.arc.network
INTENT_REGISTRY_ADDRESS=0x...
AUCTION_ESCROW_ADDRESS=0x...
PAYMENT_ROUTER_ADDRESS=0x...
PRIVATE_KEY=0x...
```

---

## Performance Tips

1. **Use st.cache_data for API calls**
```python
@st.cache_data(ttl=10)  # Cache for 10 seconds
def fetch_intents():
    return run_async(sdk.list_intents())
```

2. **Lazy load data**
```python
# Only fetch when tab is selected
if selected_tab == "My Intents":
    intents = fetch_intents()
```

3. **Paginate large lists**
```python
page_size = 10
page = st.number_input("Page", 1, len(items)//page_size)
display_items = items[(page-1)*page_size:page*page_size]
```

---

## Screenshots

### Dashboard
![Dashboard with metrics and charts]

### Create Intent
![Intent creation form with validation]

### Order Book
![Live order book with depth charts]

---

## Credits

**Built with**:
- Streamlit - Web framework
- Plotly - Interactive charts
- Pandas - Data manipulation
- Arc SDK - Blockchain interaction

**Design inspired by**:
- Modern fintech dashboards
- DeFi applications
- Enterprise admin panels

---

## Support

For issues or questions:
- Check TESTING_REPORT.md
- Review API documentation
- Test with integration_test.py

---

**Enjoy the professional Arc Coordination UI! 🎉**
