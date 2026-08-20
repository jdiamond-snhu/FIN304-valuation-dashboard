import streamlit as st
import yfinance as yf
import pandas as pd

# --- STYLING & CONFIG ---
st.set_page_config(page_title="Stock Valuation Dashboard", layout="wide")
st.title("📊 Corporate Valuation & Financial Ratio Dashboard")

# --- SIDEBAR INPUTS ---
st.sidebar.header("🛠️ Dashboard Controls")
ticker_symbol = st.sidebar.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT, F):", value="AAPL").upper()

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
            st.markdown("---")
            
            # --- CORE SCREENER COLUMNS ---
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Group 1 Header with Tooltip
                st.markdown(
                    "### 📊 Profitability & Efficiency", 
                    help="**EPS:** Net Income ÷ Shares Outstanding. Measures core profit allocated to each share.\n\n"
                         "**Net Profit Margin:** (Net Income ÷ Sales) × 100. Percentage of revenue left over after all expenses."
                )
                st.metric("Earnings Per Share (EPS)", f"${eps:.2f}")
                st.metric("Net Profit Margin", f"{net_profit_margin:.2f}%")

            with col2:
                # Group 2 Header with Tooltip
                st.markdown(
                    "### 📖 Book Value & Price Multiples", 
                    help="**Book Value Per Share:** Total Equity ÷ Shares Outstanding. The net asset value of a company on paper.\n\n"
                         "**P/E Ratio:** Stock Price ÷ EPS. Measures what the market pays per dollar of current earnings.\n\n"
                         "**P/B Ratio:** Stock Price ÷ Book Value Per Share. Compares market valuation to accounting balance sheet value."
                )
                if book_value_per_share:
                    st.metric("Book Value Per Share", f"${book_value_per_share:.2f}")
                st.metric("Price-to-Earnings (P/E) Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
                st.metric("Price-to-Book (P/B) Ratio", f"{pb_ratio:.2f}" if pb_ratio else "N/A")

            with col3:
                # Group 3 Header with Tooltip
                st.markdown(
                    "### 💸 Liquidity, Leverage & Dividends", 
                    help="**Current Ratio:** Current Assets ÷ Current Liabilities. Evaluates short-term obligation coverage.\n\n"
                         "**PEG Ratio:** P/E Ratio ÷ Expected Annual Growth Rate. Adjusts a multiple for its growth engine context.\n\n"
                         "**Dividend Yield:** (Dividend Per Share ÷ Stock Price) × 100. Annual cash return rate on price paid.\n\n"
                         "**Dividend Payout Ratio:** (Dividend Per Share ÷ EPS) × 100. Percentage of net profits returned to shareholders."
                )
                st.metric("Current Liquidity Ratio", f"{current_ratio:.2f}" if current_ratio else "N/A")
                st.metric("PEG Ratio", f"{peg_ratio:.2f}" if peg_ratio else "N/A")
                st.metric("Dividend Yield", f"{dividend_yield:.2f}%")
                st.metric("Dividend Payout Ratio", f"{dividend_payout:.2f}%")

            # --- DETAILED DATA TABLE ---
            st.markdown("---")
            st.markdown("### 🗒️ Raw Financial Data Inputs (in Thousands)")
            raw_data = {
                "Financial Metric": ["Net Profits to Common", "Total Revenue (Sales)", "Total Stockholders Equity", "Total Shares Outstanding", "Current Stock Market Price"],
                "Value": [f"${net_profits_k:,.2f}K", f"${sales_k:,.2f}K", f"${equity_k:,.2f}K" if equity_k else "N/A", f"{shares_outstanding:,.0f}", f"${stock_price:.2f}"]
            }
            st.table(pd.DataFrame(raw_data))

    except Exception as e:
        st.error(f"Could not retrieve data for ticker token '{ticker_symbol}'. Please verify the symbol or API connectivity. Error: {e}")
