
import yfinance as yf
import pandas as pd
import json

def verify_yahoo_data(ticker_symbol):
    print(f"Fetching data for {ticker_symbol}...")
    ticker = yf.Ticker(ticker_symbol)
    
    data = {}
    
    # 1. Financials (Income Statement) - Revenue, EBIT, EPS
    try:
        financials = ticker.financials
        print("\n--- Financials (First 5 Rows) ---")
        print(financials.head())
        data['financials_columns'] = list(financials.columns)
        data['financials_index'] = list(financials.index)
    except Exception as e:
        print(f"Error fetching financials: {e}")

    # 2. Cash Flow - Operating Cash Flow
    try:
        cashflow = ticker.cashflow
        print("\n--- Cash Flow (First 5 Rows) ---")
        print(cashflow.head())
        data['cashflow_index'] = list(cashflow.index)
    except Exception as e:
        print(f"Error fetching cashflow: {e}")

    # 3. Balance Sheet - Stockholders Equity (for RoE)
    try:
        balance_sheet = ticker.balance_sheet
        print("\n--- Balance Sheet (First 5 Rows) ---")
        print(balance_sheet.head())
        data['balance_sheet_index'] = list(balance_sheet.index)
    except Exception as e:
        print(f"Error fetching balance sheet: {e}")

    # 4. Major Holders
    try:
        holders = ticker.major_holders
        print("\n--- Major Holders ---")
        print(holders)
    except Exception as e:
        print(f"Error fetching holders: {e}")
        
    # 5. Ratios / Info
    try:
        info = ticker.info
        print("\n--- Key Ratios (from .info) ---")
        keys = ['trailingPE', 'forwardPE', 'priceToBook', 'returnOnEquity', 'debtToEquity', 'grossMargins', 'operatingMargins']
        for k in keys:
            print(f"{k}: {info.get(k)}")
    except Exception as e:
        print(f"Error fetching info: {e}")

    # 6. News
    try:
        news = ticker.news
        print("\n--- News (First 2) ---")
        print(news[:2] if news else "No news found")
    except Exception as e:
        print(f"Error fetching news: {e}")

if __name__ == "__main__":
    verify_yahoo_data("TCS.NS")
