import streamlit as st
import yfinance as yf
import pandas as pd

# --- STYLING & CONFIG ---
st.set_page_config(page_title="Stock Valuation Dashboard", layout="wide")
st.title("📊 Corporate Valuation & Financial Ratio Dashboard")

# --- SIDEBAR INPUTS ---
st.sidebar.header("🛠️ Dashboard Controls")
ticker_symbol = st.sidebar.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT, F):", value="AAPL").upper()

# Optional Benchmark Overlays (Using a radio selector so only one can be checked at a time)
benchmark_option = st.sidebar.radio(
    "Select Benchmark Comparison (Optional):",
    options=["None", "Industry Average", "Market Average"],
    index=0
)

# --- BENCHMARK VALUE HEURISTICS ---
# Baseline approximations for broad market (S&P 500 historicals) vs general industry averages
BENCHMARKS = {
    "Market Average": {
        "pe_ratio": 22.0,
        "pb_ratio": 4.0,
        "net_margin": 10.0, # in %
        "div_yield": 1.5,   # in %
        "current_ratio": 1.5
    },
    "Industry Average": {
        "pe_ratio": 19.5,
        "pb_ratio": 3.5,
        "net_margin": 8.5,  # in %
        "div_yield": 2.0,   # in %
        "current_ratio": 1.8
    }
}

# --- COMPARISON LOGIC FUNCTION ---
def get_status_indicator(current_val, metric_key):
    """
    Returns an emoji indicator based on user criteria:
    Green  (🟢) = Above Average (> 10% higher)
    Blue   (🔵) = Average (Within +/- 10% of benchmark)
    Orange (🟠) = Below Average (10% to 30% lower)
    Red    (🔴) = Very Below Average (> 30% lower)
    """
    if benchmark_option == "None" or current_val is None:
        return ""
        
    bench_val = BENCHMARKS[benchmark_option].get(metric_key)
    if not bench_val or bench_val == 0:
        return ""
        
    # Handle ratios where a LOWER number is traditionally better/stronger (like P/E and P/B)
    is_inverse_metric = metric_key in ["pe_ratio", "pb_ratio"]
    
    performance_ratio = current_val / bench_val
    if is_inverse_metric:
        performance_ratio = 1 / performance_ratio  # Invert so higher performance means a lower multiple
        
    if performance_ratio > 1.10:
        return " 🟢 (Above Average)"
    elif performance_ratio >= 0.90:
        return " 🔵 (Average)"
    elif performance_ratio >= 0.70:
        return " 🟠 (Below Average)"
    else:
        return " 🔴 (Very Below Average)"

# --- DATA FETCHING ---
if ticker_symbol:
    try:
        with st.spinner(f"Fetching financial data for {ticker_symbol}..."):
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            # Extract Core Income Statement Data
            net_profits = info.get("netIncomeToCommon")
            sales = info.get("totalRevenue")
            shares_outstanding = info.get("sharesOutstanding")
            stock_price = info.get("currentPrice") or info.get("previousClose")
            
            # Extract Balance Sheet Metrics
            total_equity = info.get("totalShareholdersEquity")
            total_current_assets = info.get("totalCurrentAssets")
            total_current_liabilities = info.get("totalCurrentLiabilities")
            
            # Extract Dividends and Growth
            dividend_per_share = info.get("dividendRate") or 0.0
            peg_ratio = info.get("pegRatio")
            
        # --- VERIFICATION CRITICAL EXCEPTION ---
        if not net_profits or not sales or not shares_outstanding:
            st.error("Insufficient financial statement history available for this specific asset ticker layout.")
        else:
            # --- CONVERT RAW DATA TO THOUSANDS FOR CLEAN VIEW ---
            net_profits_k = net_profits / 1000
            sales_k = sales / 1000
            equity_k = total_equity / 1000 if total_equity else None
            
            # --- MATH MODEL COMPUTATIONS ---
            eps = net_profits / shares_outstanding
            
            # Book value and P/B
            book_value_per_share = total_equity / shares_outstanding if total_equity else None
            pb_ratio = stock_price / book_value_per_share if book_value_per_share else None
            
            # Profitability & Valuation Multiples
            pe_ratio = stock_price / eps if eps > 0 else None
            net_profit_margin = (net_profits / sales) * 100
            
            # Dividends
            dividend_yield = (dividend_per_share / stock_price) * 100 if stock_price else 0.0
            dividend_payout = (dividend_per_share / eps) * 100 if eps > 0 else 0.0
            
            # Liquidity
            current_ratio = total_current_assets / total_current_liabilities if total_current_assets and total_current_liabilities else None

            # --- RENDER WEB UI LAYOUT ---
            st.subheader(f"🏢 Company Profile: {info.get('longName', ticker_symbol)}")
            st.write(f"**Sector:** {info.get('sector', 'N/A')} | **Industry:** {info.get('industry', 'N/A')}")
            
            if benchmark_option != "None":
                st.info(f"💡 Currently overlaying **{benchmark_option}** alerts relative to standard target benchmarks.")

            st.markdown("---")
            
            # --- CORE SCREENER COLUMNS ---
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 📈 Earnings & Valuation")
                st.metric("Earnings Per Share (EPS)", f"${eps:.2f}")
                st.metric(
                    "Price-to-Earnings (P/E) Ratio", 
                    f"{pe_ratio:.2f}" if pe_ratio else "N/A",
                    help="Lower P/E is marked higher relative to historic baseline risk benchmarks",
                    delta=get_status_indicator(pe_ratio, "pe_ratio") if pe_ratio else None,
                    delta_color="off"
                )
                st.metric(
                    "Price-to-Book (P/B) Ratio", 
                    f"{pb_ratio:.2f}" if pb_ratio else "N/A",
                    delta=get_status_indicator(pb_ratio, "pb_ratio") if pb_ratio else None,
                    delta_color="off"
                )
                st.metric("PEG Ratio", f"{peg_ratio:.2f}" if peg_ratio else "N/A")

            with col2:
                st.markdown("### 💡 Efficiency & Returns")
                st.metric(
                    "Net Profit Margin", 
                    f"{net_profit_margin:.2f}%",
                    delta=get_status_indicator(net_profit_margin, "net_margin"),
                    delta_color="off"
                )
                st.metric(
                    "Current Liquidity Ratio", 
                    f"{current_ratio:.2f}" if current_ratio else "N/A",
                    delta=get_status_indicator(current_ratio, "current_ratio") if current_ratio else None,
                    delta_color="off"
                )
                if book_value_per_share:
                    st.metric("Book Value Per Share", f"${book_value_per_share:.2f}")

            with col3:
                st.markdown("### 💸 Dividends & Capital Allocation")
                st.metric(
                    "Dividend Yield", 
                    f"{dividend_yield:.2f}%",
                    delta=get_status_indicator(dividend_yield, "div_yield"),
                    delta_color="off"
                )
                st.metric("Dividend Payout Ratio", f"{dividend_payout:.2f}%")
                st.metric("Current Market Price", f"${stock_price:.2f}")

            # --- DETAILED DATA TABLE ---
            st.markdown("---")
            st.markdown("### 🗒️ Raw Financial Data Inputs (in Thousands)")
            raw_data = {
                "Financial Metric": ["Net Profits to Common", "Total Revenue (Sales)", "Total Stockholders Equity", "Total Shares Outstanding"],
                "Value": [f"${net_profits_k:,.2f}K", f"${sales_k:,.2f}K", f"${equity_k:,.2f}K" if equity_k else "N/A", f"{shares_outstanding:,.0f}"]
            }
            st.table(pd.DataFrame(raw_data))

    except Exception as e:
        st.error(f"Could not retrieve data for ticker token '{ticker_symbol}'. Please verify the symbol or API connectivity. Errors: {e}")
