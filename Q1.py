import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="High Dividend Stocks Dashboard", layout="wide")

HIGH_DIVIDEND_TICKERS = [
    "CTRE",  # CareTrust REIT
    "MO",    # Altria
    "T",     # AT&T
    "VZ",    # Verizon
    "XOM",   # Exxon Mobil
    "CVX",   # Chevron
    "PFE",   # Pfizer
    "IBM",   # IBM
    "PM",    # Philip Morris
    "O"      # Realty Income
]

def safe_div(a, b):
    try:
        if a is None or b is None:
            return np.nan
        if b == 0:
            return np.nan
        return a / b
    except Exception:
        return np.nan

def _get_last_annual(df: pd.DataFrame, row_name: str):
    if df is None or df.empty:
        return np.nan
    candidates = [row_name]
    # common alternates
    alt = {
        'Total Revenue': ['Revenue', 'TotalRevenue'],
        'Ebitda': ['EBITDA'],
        'Operating Income': ['OperatingIncome'],
        'Net Income': ['NetIncome'],
        'Total Cash From Operating Activities': ['Operating Cash Flow', 'Total Cash From Operating Activities'],
        'Capital Expenditures': ['Capital Expenditures'],
        'Free Cash Flow': ['Free Cash Flow'],
        'Total Assets': ['TotalAssets'],
        'Total Current Assets': ['Total Current Assets'],
        'Total Current Liabilities': ['Total Current Liabilities'],
        'Cash And Cash Equivalents': ['Cash And Cash Equivalents', 'Cash'],
        'Inventory': ['Inventory'],
        'Total Liab': ['Total Liab', 'Total Liabilities'],
        'Total Stockholder Equity': ['Total Stockholder Equity', 'Shareholders Equity'],
        'Long Term Debt': ['Long Term Debt'],
        'Short Long Term Debt': ['Short Long Term Debt'],
        'Total Debt': ['Total Debt'],
        'Interest Expense': ['Interest Expense'],
        'Ebit': ['Ebit', 'EBIT'],
    }
    if row_name in alt:
        candidates += alt[row_name]
    for name in candidates:
        if name in df.index:
            series = df.loc[name]
            if isinstance(series, pd.Series) and not series.empty:
                return series.dropna().iloc[0] if series.dropna().size > 0 else np.nan
    return np.nan

def _get_ttm_from_quarterly(df: pd.DataFrame, row_name: str):
    if df is None or df.empty:
        return np.nan
    candidates = [row_name]
    alt = {
        'Total Revenue': ['Revenue', 'TotalRevenue'],
        'Ebitda': ['EBITDA'],
        'Operating Income': ['OperatingIncome'],
        'Net Income': ['NetIncome'],
        'Total Cash From Operating Activities': ['Operating Cash Flow', 'Total Cash From Operating Activities'],
        'Capital Expenditures': ['Capital Expenditures'],
        'Free Cash Flow': ['Free Cash Flow'],
        'Interest Expense': ['Interest Expense'],
        'Ebit': ['Ebit', 'EBIT'],
    }
    if row_name in alt:
        candidates += alt[row_name]
    for name in candidates:
        if name in df.index:
            series = df.loc[name]
            if isinstance(series, pd.Series) and not series.empty:
                # Sum last up to 4 quarters for TTM
                return series.dropna().iloc[:4].sum()
    return np.nan

@st.cache_data(show_spinner=False, ttl=3600)
def get_ticker_info(ticker):
    t = yf.Ticker(ticker)
    # Price and market data
    last_price = np.nan
    currency = None
    market_cap = np.nan
    shares_out = np.nan
    try:
        fi = t.fast_info
        last_price = fi.get("last_price", np.nan)
        currency = fi.get("currency", None)
        market_cap = fi.get("market_cap", np.nan)
    except Exception:
        pass

    try:
        info = t.get_info()
    except Exception:
        try:
            info = t.info
        except Exception:
            info = {}

    if np.isnan(last_price):
        try:
            hist = t.history(period="5d")
            if not hist.empty:
                last_price = float(hist["Close"].iloc[-1])
        except Exception:
            pass

    if np.isnan(market_cap):
        market_cap = info.get("marketCap", np.nan)

    shares_out = info.get("sharesOutstanding", np.nan)
    short_name = info.get("shortName", ticker)
    long_name = info.get("longName", short_name)
    sector = info.get("sector", None)
    industry = info.get("industry", None)

    # Dividend yield and TTM dividends
    dividend_yield = info.get("dividendYield", np.nan)
    if dividend_yield is not None and not np.isnan(dividend_yield) and dividend_yield > 1:
        # Yahoo often gives dividendYield as fraction (0.05). If > 1 assume already percentage and convert to fraction
        dividend_yield = dividend_yield / 100.0
    dividends_ttm = np.nan
    last_div_date = None
    try:
        div = t.dividends
        if div is not None and not div.empty:
            last_year = div[div.index >= (pd.Timestamp.today() - pd.DateOffset(years=1))]
            dividends_ttm = float(last_year.sum()) if not last_year.empty else float(div.tail(4).sum())
            if not div.empty:
                last_div_date = div.index[-1].date().isoformat()
        if np.isnan(dividend_yield) or dividend_yield is None:
            if last_price and not np.isnan(last_price) and dividends_ttm and not np.isnan(dividends_ttm):
                dividend_yield = dividends_ttm / last_price
    except Exception:
        pass

    return {
        "ticker": ticker,
        "short_name": short_name,
        "long_name": long_name,
        "sector": sector,
        "industry": industry,
        "price": last_price,
        "currency": currency,
        "market_cap": market_cap,
        "shares_out": shares_out,
        "dividend_yield": dividend_yield,
        "dividends_ttm": dividends_ttm,
        "last_dividend_date": last_div_date,
        "info_raw": info
    }

@st.cache_data(show_spinner=False, ttl=3600)
def get_statements(ticker):
    t = yf.Ticker(ticker)
    try:
        financials_a = t.financials
    except Exception:
        financials_a = pd.DataFrame()

    try:
        financials_q = t.quarterly_financials
    except Exception:
        financials_q = pd.DataFrame()

    try:
        balance_a = t.balance_sheet
    except Exception:
        balance_a = pd.DataFrame()

    try:
        balance_q = t.quarterly_balance_sheet
    except Exception:
        balance_q = pd.DataFrame()

    try:
        cashflow_a = t.cashflow
    except Exception:
        cashflow_a = pd.DataFrame()

    try:
        cashflow_q = t.quarterly_cashflow
    except Exception:
        cashflow_q = pd.DataFrame()

    return {
        "financials_a": financials_a,
        "financials_q": financials_q,
        "balance_a": balance_a,
        "balance_q": balance_q,
        "cashflow_a": cashflow_a,
        "cashflow_q": cashflow_q
    }

def compute_ratios(ticker):
    meta = get_ticker_info(ticker)
    stmts = get_statements(ticker)

    info = meta.get("info_raw", {}) or {}
    price = meta.get("price", np.nan)
    market_cap = meta.get("market_cap", np.nan)
    shares_out = meta.get("shares_out", np.nan)

    fin_a = stmts["financials_a"]
    fin_q = stmts["financials_q"]
    bal_a = stmts["balance_a"]
    cash_a = stmts["cashflow_a"]
    cash_q = stmts["cashflow_q"]
    bal_q = stmts["balance_q"]

    # TTM metrics
    revenue_ttm = _get_ttm_from_quarterly(fin_q, "Total Revenue")
    if np.isnan(revenue_ttm):
        revenue_ttm = _get_last_annual(fin_a, "Total Revenue")

    ebitda_ttm = _get_ttm_from_quarterly(fin_q, "Ebitda")
    if np.isnan(ebitda_ttm):
        ebitda_ttm = _get_last_annual(fin_a, "Ebitda")

    op_income_ttm = _get_ttm_from_quarterly(fin_q, "Operating Income")
    if np.isnan(op_income_ttm):
        op_income_ttm = _get_last_annual(fin_a, "Operating Income")

    net_income_ttm = _get_ttm_from_quarterly(fin_q, "Net Income")
    if np.isnan(net_income_ttm):
        net_income_ttm = _get_last_annual(fin_a, "Net Income")

    interest_exp_ttm = _get_ttm_from_quarterly(fin_q, "Interest Expense")
    if np.isnan(interest_exp_ttm):
        interest_exp_ttm = _get_last_annual(fin_a, "Interest Expense")

    cfo_ttm = _get_ttm_from_quarterly(cash_q, "Total Cash From Operating Activities")
    if np.isnan(cfo_ttm):
        cfo_ttm = _get_last_annual(cash_a, "Total Cash From Operating Activities")

    capex_ttm = _get_ttm_from_quarterly(cash_q, "Capital Expenditures")
    if np.isnan(capex_ttm):
        capex_ttm = _get_last_annual(cash_a, "Capital Expenditures")

    fcf_ttm = _get_ttm_from_quarterly(cash_q, "Free Cash Flow")
    if np.isnan(fcf_ttm):
        fcf_ttm = _get_last_annual(cash_a, "Free Cash Flow")
    if np.isnan(fcf_ttm):
        if not np.isnan(cfo_ttm) and not np.isnan(capex_ttm):
            fcf_ttm = cfo_ttm + capex_ttm  # Yahoo 'Capital Expenditures' is negative capex, so CFO + CapEx
        else:
            fcf_ttm = np.nan

    # Balance sheet latest (use annual if quarterly not available)
    total_assets = _get_last_annual(bal_q, "Total Assets")
    if np.isnan(total_assets):
        total_assets = _get_last_annual(bal_a, "Total Assets")

    total_equity = _get_last_annual(bal_q, "Total Stockholder Equity")
    if np.isnan(total_equity):
        total_equity = _get_last_annual(bal_a, "Total Stockholder Equity")

    current_assets = _get_last_annual(bal_q, "Total Current Assets")
    if np.isnan(current_assets):
        current_assets = _get_last_annual(bal_a, "Total Current Assets")

    current_liab = _get_last_annual(bal_q, "Total Current Liabilities")
    if np.isnan(current_liab):
        current_liab = _get_last_annual(bal_a, "Total Current Liabilities")

    inventory = _get_last_annual(bal_q, "Inventory")
    if np.isnan(inventory):
        inventory = _get_last_annual(bal_a, "Inventory")

    cash_and_eq = _get_last_annual(bal_q, "Cash And Cash Equivalents")
    if np.isnan(cash_and_eq):
        cash_and_eq = _get_last_annual(bal_a, "Cash And Cash Equivalents")

    total_debt = _get_last_annual(bal_q, "Total Debt")
    if np.isnan(total_debt):
        ltd = _get_last_annual(bal_q, "Long Term Debt")
        std = _get_last_annual(bal_q, "Short Long Term Debt")
        if np.isnan(ltd):
            ltd = _get_last_annual(bal_a, "Long Term Debt")
        if np.isnan(std):
            std = _get_last_annual(bal_a, "Short Long Term Debt")
        if not np.isnan(ltd) or not np.isnan(std):
            total_debt = (0 if np.isnan(ltd) else ltd) + (0 if np.isnan(std) else std)
    if np.isnan(total_debt):
        total_debt = _get_last_annual(bal_a, "Total Debt")

    # Ratios using Yahoo direct info when available
    trailing_eps = info.get("trailingEps", np.nan)
    forward_eps = info.get("forwardEps", np.nan)

    trailing_pe = info.get("trailingPE", np.nan)
    if np.isnan(trailing_pe) and not np.isnan(price) and not np.isnan(trailing_eps) and trailing_eps != 0:
        trailing_pe = price / trailing_eps

    forward_pe = info.get("forwardPE", np.nan)
    peg_ratio = info.get("pegRatio", np.nan)

    price_to_book = info.get("priceToBook", np.nan)
    if np.isnan(price_to_book) and not np.isnan(price) and not np.isnan(total_equity) and not np.isnan(shares_out) and shares_out > 0:
        bvps = total_equity / shares_out
        price_to_book = safe_div(price, bvps)

    price_to_sales = info.get("priceToSalesTrailing12Months", np.nan)
    if np.isnan(price_to_sales) and not np.isnan(market_cap) and not np.isnan(revenue_ttm) and revenue_ttm != 0:
        price_to_sales = market_cap / revenue_ttm

    enterprise_value = info.get("enterpriseValue", np.nan)
    if np.isnan(enterprise_value) and not np.isnan(market_cap):
        if np.isnan(cash_and_eq):
            cash_and_eq = 0
        if np.isnan(total_debt):
            total_debt = 0
        enterprise_value = market_cap + total_debt - cash_and_eq

    ev_ebitda = info.get("enterpriseToEbitda", np.nan)
    if np.isnan(ev_ebitda) and not np.isnan(enterprise_value) and not np.isnan(ebitda_ttm) and ebitda_ttm != 0:
        ev_ebitda = enterprise_value / ebitda_ttm

    ev_revenue = info.get("enterpriseToRevenue", np.nan)
    if np.isnan(ev_revenue) and not np.isnan(enterprise_value) and not np.isnan(revenue_ttm) and revenue_ttm != 0:
        ev_revenue = enterprise_value / revenue_ttm

    roe = info.get("returnOnEquity", np.nan)
    if (roe is None or np.isnan(roe)) and not np.isnan(net_income_ttm) and not np.isnan(total_equity) and total_equity != 0:
        roe = net_income_ttm / total_equity

    roa = info.get("returnOnAssets", np.nan)
    if (roa is None or np.isnan(roa)) and not np.isnan(net_income_ttm) and not np.isnan(total_assets) and total_assets != 0:
        roa = net_income_ttm / total_assets

    profit_margin = info.get("profitMargins", np.nan)
    if (profit_margin is None or np.isnan(profit_margin)) and not np.isnan(net_income_ttm) and not np.isnan(revenue_ttm) and revenue_ttm != 0:
        profit_margin = net_income_ttm / revenue_ttm

    operating_margin = info.get("operatingMargins", np.nan)
    if (operating_margin is None or np.isnan(operating_margin)) and not np.isnan(op_income_ttm) and not np.isnan(revenue_ttm) and revenue_ttm != 0:
        operating_margin = op_income_ttm / revenue_ttm

    current_ratio = info.get("currentRatio", np.nan)
    if np.isnan(current_ratio) and not np.isnan(current_assets) and not np.isnan(current_liab) and current_liab != 0:
        current_ratio = current_assets / current_liab

    quick_ratio = info.get("quickRatio", np.nan)
    if np.isnan(quick_ratio) and not np.isnan(current_assets) and not np.isnan(current_liab) and current_liab != 0:
        inv = 0 if np.isnan(inventory) else inventory
        quick_ratio = (current_assets - inv) / current_liab

    debt_to_equity = info.get("debtToEquity", np.nan)
    if np.isnan(debt_to_equity) and not np.isnan(total_debt) and not np.isnan(total_equity) and total_equity != 0:
        debt_to_equity = (total_debt / total_equity) * 100  # Yahoo often reports D/E in percentage in info
        # Convert to ratio (not percent):
        debt_to_equity = debt_to_equity / 100.0

    payout_ratio = info.get("payoutRatio", np.nan)
    dividend_yield = meta.get("dividend_yield", np.nan)

    fcf_yield = np.nan
    if not np.isnan(fcf_ttm) and not np.isnan(market_cap) and market_cap != 0:
        fcf_yield = fcf_ttm / market_cap

    interest_coverage = np.nan
    ebit_ttm = _get_ttm_from_quarterly(fin_q, "Ebit")
    if np.isnan(ebit_ttm):
        ebit_ttm = _get_last_annual(fin_a, "Ebit")
    if not np.isnan(ebit_ttm) and not np.isnan(interest_exp_ttm) and interest_exp_ttm != 0:
        interest_coverage = ebit_ttm / abs(interest_exp_ttm)

    result = {
        "Ticker": ticker,
        "Company": meta.get("short_name", ticker),
        "Price": price,
        "Currency": meta.get("currency", None),
        "Market Cap": market_cap,
        "Dividend Yield": dividend_yield,
        "Dividend TTM": meta.get("dividends_ttm", np.nan),
        "Trailing EPS": trailing_eps,
        "Forward EPS": forward_eps,
        "Revenue TTM": revenue_ttm,
        "EBITDA TTM": ebitda_ttm,
        "Operating Income TTM": op_income_ttm,
        "Net Income TTM": net_income_ttm,
        "Free Cash Flow TTM": fcf_ttm,
        "Total Debt": total_debt,
        "Cash & Equivalents": cash_and_eq,
        "Total Assets": total_assets,
        "Total Equity": total_equity,
        "Current Assets": current_assets,
        "Current Liabilities": current_liab,
        "Inventory": inventory,
        "Trailing P/E": trailing_pe,
        "Forward P/E": forward_pe,
        "PEG Ratio": peg_ratio,
        "Price/Sales TTM": price_to_sales,
        "Price/Book": price_to_book,
        "EV/EBITDA": ev_ebitda,
        "EV/Revenue": ev_revenue,
        "ROE": roe,
        "ROA": roa,
        "Profit Margin": profit_margin,
        "Operating Margin": operating_margin,
        "Current Ratio": current_ratio,
        "Quick Ratio": quick_ratio,
        "Debt/Equity": debt_to_equity,
        "Payout Ratio": payout_ratio,
        "FCF Yield": fcf_yield,
        "Interest Coverage": interest_coverage,
        "Sector": meta.get("sector", None),
        "Industry": meta.get("industry", None),
        "Last Dividend Date": meta.get("last_dividend_date", None),
    }
    return result

@st.cache_data(show_spinner=False, ttl=900)
def get_prices_frame(tickers, period="1y", interval="1d", auto_adjust=True):
    try:
        data = yf.download(
            tickers=tickers,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            threads=True,
            group_by='ticker',
            progress=False
        )
        if isinstance(tickers, str) or len(tickers) == 1:
            # Single ticker: DataFrame with OHLC columns
            if isinstance(tickers, list):
                col_name = tickers[0]
            else:
                col_name = tickers
            close = data["Close"].rename(col_name).to_frame()
        else:
            # Multi-index columns: (Ticker, Field)
            # Extract Close for each ticker
            close_frames = []
            for tk in tickers:
                if (tk, 'Close') in data.columns:
                    s = data[(tk, 'Close')].rename(tk)
                    close_frames.append(s)
            if not close_frames:
                return pd.DataFrame()
            close = pd.concat(close_frames, axis=1)
        close = close.dropna(how='all')
        return close
    except Exception:
        return pd.DataFrame()

def human_format(num, precision=2):
    try:
        if num is None or np.isnan(num):
            return "—"
        num = float(num)
        magnitude = 0
        units = ['', 'K', 'M', 'B', 'T']
        while abs(num) >= 1000 and magnitude < len(units) - 1:
            magnitude += 1
            num /= 1000.0
        if precision == 0:
            return f"{num:.0f}{units[magnitude]}"
        return f"{num:.{precision}f}{units[magnitude]}"
    except Exception:
        return "—"

def percent_format(x, precision=2):
    try:
        if x is None or np.isnan(x):
            return "—"
        return f"{x*100:.{precision}f}%"
    except Exception:
        return "—"

def build_overview_table(tickers):
    rows = []
    for tk in tickers:
        meta = get_ticker_info(tk)
        rows.append({
            "Ticker": tk,
            "Company": meta.get("short_name", tk),
            "Price": meta.get("price", np.nan),
            "Currency": meta.get("currency", None),
            "Market Cap": meta.get("market_cap", np.nan),
            "Dividend Yield": meta.get("dividend_yield", np.nan),
            "Dividend TTM": meta.get("dividends_ttm", np.nan),
            "Sector": meta.get("sector", None),
            "Industry": meta.get("industry", None)
        })
    df = pd.DataFrame(rows)
    return df

def build_ratios_table(tickers):
    rows = []
    for tk in tickers:
        try:
            rows.append(compute_ratios(tk))
        except Exception:
            pass
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df

def render_overview(df):
    if df.empty:
        st.info("No overview data available.")
        return
    # Display nicely formatted table
    display = df.copy()
    display["Market Cap"] = display["Market Cap"].apply(lambda x: human_format(x, 2))
    display["Price"] = display.apply(lambda r: f"{r['Price']:.2f} {r['Currency'] or ''}" if pd.notna(r["Price"]) else "—", axis=1)
    display["Dividend Yield"] = display["Dividend Yield"].apply(lambda x: percent_format(x, 2))
    display["Dividend TTM"] = display["Dividend TTM"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    st.dataframe(display[["Ticker", "Company", "Price", "Market Cap", "Dividend Yield", "Dividend TTM", "Sector", "Industry"]], use_container_width=True)

def render_price_charts(tickers, period="1y"):
    prices = get_prices_frame(tickers, period=period, interval="1d", auto_adjust=True)
    if prices.empty:
        st.info("No price data available.")
        return
    # Normalized chart
    norm = prices / prices.iloc[0] * 100.0
    st.subheader("Normalized Price (Start = 100)")
    st.line_chart(norm, use_container_width=True)
    st.subheader("Actual Prices")
    st.line_chart(prices, use_container_width=True)

def render_ratios(df):
    if df.empty:
        st.info("No ratio data available.")
        return
    display = df.copy()

    # Format columns
    money_cols = ["Price", "Market Cap", "Revenue TTM", "EBITDA TTM", "Operating Income TTM", "Net Income TTM", "Free Cash Flow TTM", "Total Debt", "Cash & Equivalents", "Total Assets", "Total Equity"]
    for c in money_cols:
        if c in display.columns:
            display[c] = display[c].apply(lambda x: human_format(x, 2))

    percent_cols = ["Dividend Yield", "ROE", "ROA", "Profit Margin", "Operating Margin", "Payout Ratio", "FCF Yield"]
    for c in percent_cols:
        if c in display.columns:
            display[c] = display[c].apply(lambda x: percent_format(x, 2))

    float_cols = ["Trailing P/E", "Forward P/E", "PEG Ratio", "Price/Sales TTM", "Price/Book", "EV/EBITDA", "EV/Revenue", "Current Ratio", "Quick Ratio", "Debt/Equity", "Interest Coverage"]
    for c in float_cols:
        if c in display.columns:
            display[c] = display[c].apply(lambda x: "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.2f}")

    show_cols = [
        "Ticker", "Company", "Price", "Market Cap", "Dividend Yield", "Dividend TTM", "Trailing P/E", "Forward P/E",
        "PEG Ratio", "Price/Sales TTM", "Price/Book", "EV/EBITDA", "EV/Revenue", "ROE", "ROA", "Profit Margin",
        "Operating Margin", "Current Ratio", "Quick Ratio", "Debt/Equity", "Payout Ratio", "FCF Yield", "Interest Coverage",
        "Revenue TTM", "EBITDA TTM", "Net Income TTM", "Free Cash Flow TTM", "Total Debt", "Cash & Equivalents"
    ]
    show_cols = [c for c in show_cols if c in display.columns]
    st.dataframe(display[show_cols], use_container_width=True)

    # Download raw numeric ratios
    st.download_button(
        "Download ratios (CSV)",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="financial_ratios.csv",
        mime="text/csv"
    )

def main():
    st.title("High Dividend Companies - Yahoo Finance Dashboard")

    with st.sidebar:
        st.header("Settings")
        default_tickers = HIGH_DIVIDEND_TICKERS
        choose = st.toggle("Choose custom tickers", value=False)
        if choose:
            user_input = st.text_input("Enter comma-separated tickers", value=",".join(default_tickers))
            selected = [x.strip().upper() for x in user_input.split(",") if x.strip()]
        else:
            selected = default_tickers

        period = st.selectbox("Price History Period", options=["3mo", "6mo", "1y", "2y", "5y", "10y", "max"], index=2)
        st.caption("Tip: Use the toggle above to analyze other tickers as needed.")

    st.subheader("Top High Dividend Companies")
    overview_df = build_overview_table(selected)
    # Sort by Dividend Yield descending if available
    if "Dividend Yield" in overview_df.columns and not overview_df["Dividend Yield"].isna().all():
        overview_df = overview_df.sort_values(by="Dividend Yield", ascending=False, na_position="last")
    render_overview(overview_df)

    st.divider()
    st.subheader("Stock Prices")
    render_price_charts(overview_df["Ticker"].tolist(), period=period)

    st.divider()
    st.subheader("Financial Ratios Analysis")
    with st.spinner("Computing ratios..."):
        ratios_df = build_ratios_table(overview_df["Ticker"].tolist())
    render_ratios(ratios_df)

if __name__ == "__main__":
    main()
