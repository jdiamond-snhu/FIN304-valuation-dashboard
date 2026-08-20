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
ticker_symbol = st.sidebar.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT, F):", value="F").upper()

# --- DATA FETCHING ---
if ticker_symbol:
    try:
        with st.spinner(f"Fetching financial data for {ticker_symbol}..."):
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            
            # --- INCOME STATEMENT FIELDS WITH FALLBACKS ---
            sales = info.get("totalRevenue") or info.get("grossProfits") or 0.0
            shares_outstanding = info.get("sharesOutstanding")
            stock_price = info.get("currentPrice") or info.get("previousClose") or 0.0
            
            # Extract net profits
            net_profits = info.get("netIncomeToCommon") or info.get("netIncome")
            
            # Calculate or extract EPS safely
            if shares_outstanding and net_profits:
                eps = net_profits / shares_outstanding
            else:
                eps = info.get("trailingEps") or info.get("forwardEps") or 0.0
                if eps and shares_outstanding and not net_profits:
                    net_profits = eps * shares_outstanding
                    
            # --- BALANCE SHEET FIELDS WITH FALLBACKS ---
            total_equity = info.get("totalShareholdersEquity") or info.get("bookValue", 0.0) * (shares_outstanding or 1)
            
            total_current_assets = None
            total_current_liabilities = None
            
            try:
                q_bs = stock.quarterly_balance_sheet
                if not q_bs.empty:
                    # Safely isolate the first scalar item from the latest reporting column
                    latest_col = q_bs.columns[0]
                    
                    if 'Current Assets' in q_bs.index:
                        val_assets = q_bs.loc['Current Assets', latest_col]
                        total_current_assets = float(val_assets.iloc[0] if isinstance(val_assets, pd.Series) else val_assets)
                        
                    if 'Current Liabilities' in q_bs.index:
                        val_liab = q_bs.loc['Current Liabilities', latest_col]
                        total_current_liabilities = float(val_liab.iloc[0] if isinstance(val_liab, pd.Series) else val_liab)
            except Exception:
                pass
                
            # Final fallback for current liquidity elements
            if total_current_assets is None:
                total_current_assets = info.get("totalCurrentAssets") or 0.0
            if total_current_liabilities is None:
                total_current_liabilities = info.get("totalCurrentLiabilities") or 0.0
            
            # --- DIVIDENDS AND MULTIPLES WITH FALLBACKS ---
            dividend_per_share = info.get("dividendRate") or info.get("trailingAnnualDividendRate") or 0.0
            # If rate is missing but yield exists, reverse engineer it
            if not dividend_per_share and info.get("dividendYield"):
                dividend_per_share = info.get("dividendYield") * stock_price
                
            peg_ratio = info.get("pegRatio")
            
        # --- SCREENING AND VALIDATION RENDER ---
        if not shares_outstanding or stock_price == 0.0:
            st.error(f"Ticker symbol '{ticker_symbol}' is valid, but Yahoo Finance does not have public shares outstanding information for it.")
        else:
            # --- CALCULATE METRICS ---
            # Book value and P/B Ratio
            if total_equity and shares_outstanding:
                book_value_per_share = total_equity / shares_outstanding
            else:
                book_value_per_share = info.get("bookValue") or 0.0
                
            if stock_price and book_value_per_share:
                pb_ratio = stock_price / book_value_per_share
            else:
                pb_ratio = info.get("priceToBook") or 0.0
                
            # P/E Ratio
            if stock_price and eps and eps > 0:
                pe_ratio = stock_price / eps
            else:
                pe_ratio = info.get("trailingPE") or info.get("forwardPE") or 0.0
                
            # Margins & Liquidity
            net_profit_margin = ((net_profits / sales) * 100) if sales and net_profits else (info.get("profitMargins", 0.0) * 100)
            current_ratio = (total_current_assets / total_current_liabilities) if total_current_assets and total_current_liabilities else (info.get("currentRatio") or 0.0)
            
            # Dividend Multiples
            dividend_yield = (dividend_per_share / stock_price) * 100 if stock_price else (info.get("dividendYield", 0.0) * 100)
            if eps and eps > 0:
                dividend_payout = (dividend_per_share / eps) * 100
            else:
                dividend_payout = (info.get("payoutRatio", 0.0) * 100)

            # --- RENDER WEB UI LAYOUT ---
            st.subheader(f"🏢 Company Profile: {info.get('longName', ticker_symbol)}")
            st.write(f"**Sector:** {info.get('sector', 'N/A')} | **Industry:** {info.get('industry', 'N/A')}")
            st.markdown("---")
            
            # --- CORE SCREENER COLUMNS ---
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 📈 Earnings & Valuation")
                st.metric("Earnings Per Share (EPS)", f"${eps:.2f}" if eps else "N/A")
                st.metric("Price-to-Earnings (P/E) Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
                st.metric("Price-to-Book (P/B) Ratio", f"{pb_ratio:.2f}" if pb_ratio else "N/A")
                st.metric("PEG Ratio", f"{peg_ratio:.2f}" if peg_ratio else "N/A")

            with col2:
                st.markdown("### 💡 Efficiency & Returns")
                st.metric("Net Profit Margin", f"{net_profit_margin:.2f}%")
                st.metric("Current Liquidity Ratio", f"{current_ratio:.2f}" if current_ratio else "N/A")
                st.metric("Book Value Per Share", f"${book_value_per_share:.2f}" if book_value_per_share else "N/A")

            with col3:
                st.markdown("### 💸 Dividends & Capital Allocation")
                st.metric("Dividend Yield", f"{dividend_yield:.2f}%")
                st.metric("Dividend Payout Ratio", f"{dividend_payout:.2f}%")
                st.metric("Current Market Price", f"${stock_price:.2f}")

            # --- DETAILED DATA TABLE ---
            st.markdown("---")
            st.markdown("### 🗒️ Raw Financial Data Inputs (in Thousands)")
            
            net_profits_k = (net_profits / 1000) if net_profits else 0.0
            sales_k = (sales / 1000) if sales else 0.0
            equity_k = (total_equity / 1000) if total_equity else 0.0
            assets_k = (total_current_assets / 1000) if total_current_assets else 0.0
            liab_k = (total_current_liabilities / 1000) if total_current_liabilities else 0.0
            
            raw_data = {
                "Financial Metric": ["Net Profits to Common", "Total Revenue (Sales)", "Total Stockholders Equity", "Total Current Assets", "Total Current Liabilities", "Total Shares Outstanding"],
                "Value": [
                    f"${net_profits_k:,.2f}K" if net_profits_k else "N/A", 
                    f"${sales_k:,.2f}K" if sales_k else "N/A", 
                    f"${equity_k:,.2f}K" if equity_k else "N/A", 
                    f"${assets_k:,.2f}K" if assets_k else "N/A", 
                    f"${liab_k:,.2f}K" if liab_k else "N/A", 
                    f"{shares_outstanding:,.0f}" if shares_outstanding else "N/A"
                ]
            }
            st.table(pd.DataFrame(raw_data))

    except Exception as e:
        st.error(f"Could not retrieve data for ticker token '{ticker_symbol}'. Please verify the symbol or API connectivity. Error: {e}")
