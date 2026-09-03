import streamlit as st
import yfinance as yf
import pandas as pd

# Set up page configurations
st.set_page_config(page_title="FIN304 Valuation Dashboard", layout="wide")

# ==============================================================================
# 1. SIDEBAR NAVIGATION & TICKER INPUT
# ==============================================================================
st.sidebar.header("📊 Dashboard Settings")
ticker_symbol = st.sidebar.text_input("Enter Stock Ticker Symbol:", value="AAPL").upper().strip()

# ==============================================================================
# 2. DATA EXTRACTION FUNCTION (CACHED FOR INSTANT PERFORMANCE)
# ==============================================================================
@st.cache_data(ttl=3600)  # Caches results for 1 hour to keep UI lightning fast
def fetch_company_financials(symbol):
    """
    Safely connects to yfinance and builds a normalized data structure.
    If the API call fails or metrics are missing, it falls back to safe default fields.
    """
    fallback_data = {
        "long_name": symbol, "sector": "N/A", "industry": "N/A",
        "eps": None, "peg_ratio": None, "beta": None, "stock_price": 0.0,
        "net_profits": None, "sales": None, "total_equity": None,
        "total_current_assets": None, "total_current_liabilities": None,
        "shares_outstanding": None
    }
    
    try:
        ticker_data = yf.Ticker(symbol)
        info = ticker_data.info
        
        if not info:
            return fallback_data
            
        return {
            "long_name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "eps": info.get("trailingEps"),
            "peg_ratio": info.get("pegRatio"),
            "beta": info.get("beta"),  # <-- Extracted cleanly here
            "stock_price": info.get("currentPrice", 0.0),
            "net_profits": info.get("netIncomeToCommon"),
            "sales": info.get("totalRevenue"),
            "total_equity": info.get("totalStockholderEquity"),
            "total_current_assets": info.get("totalCurrentAssets"),
            "total_current_liabilities": info.get("totalCurrentLiabilities"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio")
        }
    except Exception as e:
        st.sidebar.error(f"Error gathering data for {symbol}: {e}")
        return fallback_data

# ==============================================================================
# 3. INITIALIZE VARIABLES & CALCULATIONS
# ==============================================================================
data = fetch_company_financials(ticker_symbol)

# Calculate financial ratios derived from raw metrics
pe_ratio = (data["stock_price"] / data["eps"]) if (data["eps"] and data["eps"] != 0) else None

book_value_per_share = (data["total_equity"] / data["shares_outstanding"]) if (data["total_equity"] and data["shares_outstanding"]) else None
pb_ratio = (data["stock_price"] / book_value_per_share) if (data["stock_price"] and book_value_per_share) else None

net_profit_margin = (data["net_profits"] / data["sales"] * 100) if (data["net_profits"] and data["sales"]) else 0.0
div_y_raw = data.get("dividend_yield")
dividend_yield = div_y_raw * 100 if div_y_raw < 1.0 else div_y_raw * 1
div_p_raw = data.get("payout_ratio")
dividend_payout = (div_p_raw * 100) if div_p_raw is not None else None

# ==============================================================================
# 4. RENDER WEB UI LAYOUT
# ==============================================================================
st.subheader(f"🏢 Company Profile: {data['long_name']}")
st.write(f"**Sector:** {data['sector']} | **Industry:** {data['industry']}")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📈 Earnings & Valuation")
    st.metric("Earnings Per Share (EPS)", f"${data['eps']:.2f}" if data['eps'] else "N/A")
    st.metric("Price-to-Earnings (P/E) Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
    st.metric("Price-to-Book (P/B) Ratio", f"{pb_ratio:.2f}" if pb_ratio else "N/A")
    st.metric("PEG Ratio", f"{data['peg_ratio']:.2f}" if data['peg_ratio'] else "N/A")
    
    # Brand new Drop-In Beta Component:
    st.metric(
        label="Beta (Volatility)", 
        value=f"{data['beta']:.2f}" if data['beta'] is not None else "N/A",
        help="Measures volatility relative to the market. Beta > 1.0 is more volatile; Beta < 1.0 is less volatile."
    )

with col2:
    st.markdown("### 💡 Efficiency & Returns")
    st.metric("Net Profit Margin", f"{net_profit_margin:.2f}%")
    st.metric("Book Value Per Share", f"${book_value_per_share:.2f}" if book_value_per_share else "N/A")

with col3:
    st.markdown("### 💸 Dividends & Capital Allocation")
    st.metric("Dividend Yield", f"{dividend_yield:.2f}%" if dividend_yield is not None else "N/A")
    st.metric("Dividend Payout Ratio", f"{dividend_payout:.2f}%" if dividend_payout is not None else "N/A")
    st.metric("Current Market Price", f"${data['stock_price']:.2f}")

# ==============================================================================
# 5. DETAILED DATA TABLE
# ==============================================================================
st.markdown("---")
st.markdown("### 🗒️ Raw Financial Data Inputs (in Thousands)")

net_profits_k = (data["net_profits"] / 1000) if data["net_profits"] else 0.0
sales_k = (data["sales"] / 1000) if data["sales"] else 0.0
equity_k = (data["total_equity"] / 1000) if data["total_equity"] else 0.0
assets_k = (data["total_current_assets"] / 1000) if data["total_current_assets"] else 0.0
liab_k = (data["total_current_liabilities"] / 1000) if data["total_current_liabilities"] else 0.0

raw_data = {
    "Financial Metric": [
        "Net Profits to Common", 
        "Total Revenue (Sales)", 
        "Total Stockholders Equity", 
        "Total Current Assets", 
        "Total Current Liabilities", 
        "Total Shares Outstanding"
    ],
    "Value": [
        f"${net_profits_k:,.2f}K" if net_profits_k else "N/A",
        f"${sales_k:,.2f}K" if sales_k else "N/A",
        f"${equity_k:,.2f}K" if equity_k else "N/A",
        f"${assets_k:,.2f}K" if assets_k else "N/A",
        f"${liab_k:,.2f}K" if liab_k else "N/A",
        f"{data['shares_outstanding']:,.0f}" if data['shares_outstanding'] else "N/A"
    ]
}

st.table(pd.DataFrame(raw_data))
