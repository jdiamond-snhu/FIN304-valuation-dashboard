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
            
            # Extract Balance Sheet Metrics safely
            total_equity = info.get("totalShareholdersEquity")
            
            # --- PATCH: Fetch current liquidity lines directly from financial statements ---
            total_current_assets = None
            total_current_liabilities = None
            try:
                q_bs = stock.quarterly_balance_sheet
                if not q_bs.empty:
                    latest_col = q_bs.columns[0]
                    total_current_assets = float(q_bs.loc['Current Assets', latest_col])
                    total_current_liabilities = float(q_bs.loc['Current Liabilities', latest_col])
            except Exception:
                # Fallback to summary info tags if the data frame fails
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
            
            # Liquidity Calculation
            current_ratio = total_current_assets / total_current_liabilities if total_current_assets and total_current_liabilities else None

            # --- RENDER WEB UI LAYOUT ---
            st.subheader(f"🏢 Company Profile: {info.get('longName', ticker_symbol)}")
            st.write(f"**Sector:** {info.get('sector', 'N/A')} | **Industry:** {info.get('industry', 'N/A')}")
            st.markdown("---")
            
            # --- CORE SCREENER COLUMNS ---
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 📈 Earnings & Valuation")
                st.metric("Earnings Per Share (EPS)", f"${eps:.2f}")
                st.metric("Price-to-Earnings (P/E) Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
                st.metric("Price-to-Book (P/B) Ratio", f"{pb_ratio:.2f}" if pb_ratio else "N/A")
                st.metric("PEG Ratio", f"{peg_ratio:.2f}" if peg_ratio else "N/A")

            with col2:
                st.markdown("### 💡 Efficiency & Returns")
                st.metric("Net Profit Margin", f"{net_profit_margin:.2f}%")
                st.metric("Current Liquidity Ratio", f"{current_ratio:.2f}" if current_ratio else "N/A")
                if book_value_per_share:
                    st.metric("Book Value Per Share", f"${book_value_per_share:.2f}")

            with col3:
                st.markdown("### 💸 Dividends & Capital Allocation")
                st.metric("Dividend Yield", f"{dividend_yield:.2f}%")
                st.metric("Dividend Payout Ratio", f"{dividend_payout:.2f}%")
                st.metric("Current Market Price", f"${stock_price:.2f}")

            # --- DETAILED DATA TABLE ---
            st.markdown("---")
            st.markdown("### 🗒️ Raw Financial Data Inputs (in Thousands)")
            
            assets_val = f"${total_current_assets/1000:,.2f}K" if total_current_assets else "N/A"
            liab_val = f"${total_current_liabilities/1000:,.2f}K" if total_current_liabilities else "N/A"
            
            raw_data = {
                "Financial Metric": ["Net Profits to Common", "Total Revenue (Sales)", "Total Stockholders Equity", "Total Current Assets", "Total Current Liabilities", "Total Shares Outstanding"],
                "Value": [f"${net_profits_k:,.2f}K", f"${sales_k:,.2f}K", f"${equity_k:,.2f}K" if equity_k else "N/A", assets_val, liab_val, f"{shares_outstanding:,.0f}"]
            }
            st.table(pd.DataFrame(raw_data))

    except Exception as e:
        st.error(f"Could not retrieve data for ticker token '{ticker_symbol}'. Please verify the symbol or API connectivity. Error: {e}")
