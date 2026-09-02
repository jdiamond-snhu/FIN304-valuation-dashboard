import streamlit as st
import yfinance as yf
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="Equity Valuation Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Fundamental Equity Valuation Dashboard")
st.caption("""Designed by Jeff Diamond, 2026""")
st.write("""
**Directions:** Input any public ticker symbol 
to instantly pull real-time market metrics and financial statement data.
""")

# --- SIDEBAR INPUTS ---
st.sidebar.header("🛠️ Dashboard Controls")
ticker_symbol = st.sidebar.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT, F):", value="AAPL").upper()

# --- OPTIMIZED CACHED DATA FETCHING ENGINE ---
# This saves the stock metrics in memory for 20 minutes (1200 seconds) so Yahoo doesn't block you!
@st.cache_data(ttl=1200)
def fetch_financial_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Extract Core Income Statement Data
    sales = info.get("totalRevenue") or info.get("grossProfits") or 0.0
    shares_outstanding = info.get("sharesOutstanding")
    stock_price = info.get("currentPrice") or info.get("previousClose") or 0.0
    net_profits = info.get("netIncomeToCommon") or info.get("netIncome")
    
    # Calculate or extract EPS safely
    if shares_outstanding and net_profits:
        eps = net_profits / shares_outstanding
    else:
        eps = info.get("trailingEps") or info.get("forwardEps") or 0.0
        if eps and shares_outstanding and not net_profits:
            net_profits = eps * shares_outstanding
            
    # Extract Balance Sheet Metrics safely
    total_equity = info.get("totalShareholdersEquity") or info.get("bookValue", 0.0) * (shares_outstanding or 1)
    
    total_current_assets = None
    total_current_liabilities = None
    
    try:
        q_bs = stock.quarterly_balance_sheet
        if not q_bs.empty:
            latest_col = q_bs.columns
            if 'Current Assets' in q_bs.index:
                val_assets = q_bs.loc['Current Assets', latest_col]
                total_current_assets = float(val_assets.iloc if isinstance(val_assets, pd.Series) else val_assets)
            if 'Current Liabilities' in q_bs.index:
                val_liab = q_bs.loc['Current Liabilities', latest_col]
                total_current_liabilities = float(val_liab.iloc if isinstance(val_liab, pd.Series) else val_liab)
    except Exception:
        pass
        
    if total_current_assets is None:
        total_current_assets = info.get("totalCurrentAssets") or 0.0
    if total_current_liabilities is None:
        total_current_liabilities = info.get("totalCurrentLiabilities") or 0.0
    
    dividend_per_share = info.get("dividendRate") or info.get("trailingAnnualDividendRate") or 0.0
    if not dividend_per_share and info.get("dividendYield"):
        dividend_per_share = info.get("dividendYield") * stock_price
        
    peg_ratio = info.get("pegRatio")
    long_name = info.get('longName', ticker)
    sector = info.get('sector', 'N/A')
    industry = info.get('industry', 'N/A')
    payout_ratio_fallback = info.get("payoutRatio", 0.0)
    profit_margin_fallback = info.get("profitMargins", 0.0)
    book_value_fallback = info.get("bookValue") or 0.0
    pb_fallback = info.get("priceToBook") or 0.0
    pe_fallback = info.get("trailingPE") or info.get("forwardPE") or 0.0
    div_yield_fallback = info.get("dividendYield", 0.0)

    # Bundle all pulled metrics into a safe dictionary payload
    return {
        "sales": sales, "shares_outstanding": shares_outstanding, "stock_price": stock_price,
        "net_profits": net_profits, "eps": eps, "total_equity": total_equity,
        "total_current_assets": total_current_assets, "total_current_liabilities": total_current_liabilities,
        "dividend_per_share": dividend_per_share, "peg_ratio": peg_ratio, "long_name": long_name,
        "sector": sector, "industry": industry, "payout_ratio_fallback": payout_ratio_fallback,
        "profit_margin_fallback": profit_margin_fallback, "book_value_fallback": book_value_fallback,
        "pb_fallback": pb_fallback, "pe_fallback": pe_fallback, "div_yield_fallback": div_yield_fallback
    }

# --- APPLICATION ENGINE RUN ---
if ticker_symbol:
    try:
        # Call our new safely cached framework function
        data = fetch_financial_data(ticker_symbol)
        
        if not data["shares_outstanding"] or data["stock_price"] == 0.0:
            st.error(f"Ticker symbol '{ticker_symbol}' is valid, but Yahoo Finance does not have complete public share configurations for it.")
        else:
            # --- CALCULATE INTERMEDIATE SCREENER RATIOS ---
            if data["total_equity"] and data["shares_outstanding"]:
                book_value_per_share = data["total_equity"] / data["shares_outstanding"]
            else:
                book_value_per_share = data["book_value_fallback"]
                
            if data["stock_price"] and book_value_per_share:
                pb_ratio = data["stock_price"] / book_value_per_share
            else:
                pb_ratio = data["pb_fallback"]
                
            if data["stock_price"] and data["eps"] and data["eps"] > 0:
                pe_ratio = data["stock_price"] / data["eps"]
            else:
                pe_ratio = data["pe_fallback"]
                
            net_profit_margin = ((data["net_profits"] / data["sales"]) * 100) if data["sales"] and data["net_profits"] else (data["profit_margin_fallback"] * 100)
            current_ratio = (data["total_current_assets"] / data["total_current_liabilities"]) if data["total_current_assets"] and data["total_current_liabilities"] else 0.0
            
            dividend_yield = (data["dividend_per_share"] / data["stock_price"]) * 100 if data["stock_price"] else (data["div_yield_fallback"] * 100)
            if data["eps"] and data["eps"] > 0:
                dividend_payout = (data["dividend_per_share"] / data["eps"]) * 100
            else:
                dividend_payout = (data["payout_ratio_fallback"] * 100)
try:
    ticker_data = yf.Ticker(ticker_symbol)
    # ... details or mapping logic
except Exception as e:
    st.error(f"Error loading ticker data: {e}")
    st.stop()  # Keeps the app from trying to render the rest of the layout with missing data

# Line 129 will now run perfectly:
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
    
    # Extract beta safely from your yfinance data dictionary
    beta = data.get("beta")
    st.metric(
        label="Beta (Volatility)", 
        value=f"{beta:.2f}" if beta is not None else "N/A",
        help="Measures volatility relative to the market. > 1.0 is more volatile; < 1.0 is less volatile."
    )

with col2:
    st.markdown("### 💡 Efficiency & Returns")
    st.metric("Net Profit Margin", f"{net_profit_margin:.2f}%")
    st.metric("Book Value Per Share", f"${book_value_per_share:.2f}" if book_value_per_share else "N/A")

with col3:
    st.markdown("### 💸 Dividends & Capital Allocation")
    st.metric("Dividend Yield", f"{dividend_yield:.2f}%")
    st.metric("Dividend Payout Ratio", f"{dividend_payout:.2f}%")
    st.metric("Current Market Price", f"${data['stock_price']:.2f}")

# --- DETAILED DATA TABLE ---
st.markdown("---")
st.markdown("### 🗒️ Raw Financial Data Inputs (in Thousands)")

net_profits_k = (data["net_profits"] / 1000) if data["net_profits"] else 0.0
sales_k = (data["sales"] / 1000) if data["sales"] else 0.0
equity_k = (data["total_equity"] / 1000) if data["total_equity"] else 0.0
assets_k = (data["total_current_assets"] / 1000) if data["total_current_assets"] else 0.0
liab_k = (data["total_current_liabilities"] / 1000) if data["total_current_liabilities"] else 0.0

raw_data = {
    "Financial Metric": ["Net Profits to Common", "Total Revenue (Sales)", "Total Stockholders Equity", "Total Current Assets", "Total Current Liabilities", "Total Shares Outstanding"],
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

    except Exception as e:
        st.error(f"Yahoo Finance is experiencing temporary cloud network rate blocks. Please wait a few moments and try your request again. Details: {e}")
