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
st.markdown("""
This dashboard replicates the corporate financial analysis and valuation models 
we explored during our foundational valuation studies. Input any public ticker symbol 
to instantly pull real-time market metrics and financial statement data.
""")

# Sidebar Input
st.sidebar.header("User Input Settings")
ticker_symbol = st.sidebar.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT, F)", value="AAPL").upper().strip()

if ticker_symbol:
    try:
        with st.spinner(f"Fetching financial data for {ticker_symbol}..."):
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # Fetch Statements
            financials = ticker.financials      # Income Statement
            balance_sheet = ticker.balance_sheet # Balance Sheet
            
        if financials.empty or balance_sheet.empty:
            st.error(f"Could not find complete financial statements for {ticker_symbol}. Please try a different asset.")
    except Exception as e:
        st.error(f"Error fetching data for '{ticker_symbol}': {str(e)}")
        st.info("Tip: Double-check the ticker symbol on Yahoo Finance (e.g., BRK-B instead of BRK.B).")
        st.stop()

    # --- Header Metrics Block ---
    company_name = info.get('longName', ticker_symbol)
    current_price = info.get('currentPrice', info.get('previousClose', 0.0))
    currency = info.get('currency', 'USD')
    
    st.header(f"🏢 {company_name} ({ticker_symbol})")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Stock Price", f"{current_price:,.2f} {currency}")
    col2.metric("Market Capitalization", f"${info.get('marketCap', 0):,}")
    col3.metric("Trailing P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
    col4.metric("Forward P/E Ratio", f"{info.get('forwardPE', 'N/A')}")
    
    st.markdown("---")
    
    # --- Dynamic Metrics Calculation Block ---
    try:
        # Extract required raw line items from the most recent reporting year
        latest_year_fin = financials.columns[0]
        latest_year_bal = balance_sheet.columns[0]
        
        # Safe extraction helper with fallback names often used in yfinance
        def get_financial_item(df, keys, column):
            for key in keys:
                if key in df.index:
                    return df.loc[key, column]
            return 0.0

        net_income = get_financial_item(financials, ['Net Income', 'Net Income Common Stockholders'], latest_year_fin)
        total_revenue = get_financial_item(financials, ['Total Revenue'], latest_year_fin)
        shares_outstanding = info.get('sharesOutstanding', get_financial_item(balance_sheet, ['Ordinary Shares Number', 'Share Issued'], latest_year_bal))
        total_equity = get_financial_item(balance_sheet, ['Stockholders Equity', 'Total Stockholders Equity'], latest_year_bal)
        total_assets = get_financial_item(balance_sheet, ['Total Assets'], latest_year_bal)
        current_assets = get_financial_item(balance_sheet, ['Total Current Assets'], latest_year_bal)
        current_liabilities = get_financial_item(balance_sheet, ['Total Current Liabilities'], latest_year_bal)
        long_term_debt = get_financial_item(balance_sheet, ['Long Term Debt', 'LongTermDebt'], latest_year_bal)
        dividend_per_share = info.get('dividendRate', 0.0) if info.get('dividendRate') is not None else 0.0
        eps_trailing = info.get('trailingEps', (net_income / shares_outstanding if shares_outstanding else 0.0))
        earnings_growth = info.get('earningsGrowth', 0.05) # fallback fallback standard growth 5% whole integer target
        if earnings_growth:
            growth_pct = earnings_growth * 100
        else:
            growth_pct = 5.0

        # Calculations
        computed_eps = net_income / shares_outstanding if shares_outstanding else 0.0
        book_value_per_share = total_equity / shares_outstanding if shares_outstanding else 0.0
        price_to_book = current_price / book_value_per_share if book_value_per_share else 0.0
        net_profit_margin = (net_income / total_revenue) * 100 if total_revenue else 0.0
        current_ratio = current_assets / current_liabilities if current_liabilities else 0.0
        debt_to_equity = (long_term_debt / total_equity) * 100 if total_equity else 0.0
        roa = (net_income / total_assets) * 100 if total_assets else 0.0
        roe = (net_income / total_equity) * 100 if total_equity else 0.0
        
        # Dividend Metrics
        payout_ratio = (dividend_per_share / eps_trailing) * 100 if eps_trailing and dividend_per_share else 0.0
        if payout_ratio == 0.0 and info.get('payoutRatio'):
            payout_ratio = info.get('payoutRatio') * 100
        div_yield = (dividend_per_share / current_price) * 100 if current_price else 0.0
        
        # PEG Calculation
        pe_ratio = info.get('trailingPE', 0.0)
        peg_ratio = (pe_ratio / growth_pct) if growth_pct and pe_ratio else 0.0

        # --- Display Computed Dashboard Metrics ---
        st.header("📊 Replicated Portfolio & Valuation Metrics")
        st.markdown(f"Calculated using the latest annual report data available *({latest_year_fin.strftime('%Y-%m-%d') if hasattr(latest_year_fin, 'strftime') else latest_year_fin})*:")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        
        with m_col1:
            st.subheader("💡 Profitability & Efficiency")
            st.metric("Net Profit Margin", f"{net_profit_margin:.2f}%")
            st.metric("Return on Assets (ROA)", f"{roa:.2f}%")
            st.metric("Return on Equity (ROE)", f"{roe:.2f}%")
            st.metric("Calculated EPS", f"${computed_eps:.2f}")

        with m_col2:
            st.subheader("📖 Book Value & Price Multiples")
            st.metric("Book Value Per Share", f"${book_value_per_share:.2f}")
            st.metric("Price-to-Book (P/B) Ratio", f"{price_to_book:.2f}x")
            st.metric("Price-to-Sales (P/S) Ratio", f"{info.get('priceToSalesTrailing12Months', 'N/A') if isinstance(info.get('priceToSalesTrailing12Months'), (int, float)) else 'N/A'}")
            st.metric("PEG Ratio", f"{peg_ratio:.2f}x" if peg_ratio else "N/A")

        with m_col3:
            st.subheader("🛡️ Liquidity, Leverage & Dividends")
            st.metric("Current Ratio", f"{current_ratio:.2f}")
            st.metric("Debt-to-Equity Ratio", f"{debt_to_equity:.2f}%")
            st.metric("Dividend Yield", f"{div_yield:.2f}%")
            st.metric("Dividend Payout Ratio", f"{payout_ratio:.2f}%")

    except Exception as calc_error:
        st.warning("Could not calculate all specific metrics due to non-standard financial formatting for this ticker.")
        st.info("Showing raw data options instead.")

    st.markdown("---")
    
    # --- Raw Statements Explorer Tab Structure ---
    st.header("🗂️ Underlying Financial Statements Explorer")
    tab1, tab2 = st.tabs(["Income Statement", "Balance Sheet"])
    
    with tab1:
        st.subheader("Income Statement (Most Recent Years)")
        st.dataframe(financials)
        
    with tab2:
        st.subheader("Balance Sheet (Most Recent Years)")
        st.dataframe(balance_sheet)

else:
    st.info("Please enter a valid stock ticker symbol in the sidebar to begin generating data visualization maps.")
