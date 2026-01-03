
import yfinance as yf
import pandas as pd
from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()

def get_ticker(company_id: str):
    ticker_symbol = company_id.upper()
    # If it's a common name, map it (Legacy) - but now rely on upload detection mainly
    if ticker_symbol == "TCS": ticker_symbol = "TCS.NS"
    elif ticker_symbol == "INFOSYS": ticker_symbol = "INFY.NS"
    elif ticker_symbol == "WIPRO": ticker_symbol = "WIPRO.NS"
    
    # Default behavior: Append .NS if no suffix
    if not ticker_symbol.endswith(".NS") and not ticker_symbol.endswith(".BO"):
         ticker_symbol += ".NS"
         
    return yf.Ticker(ticker_symbol)

@router.get("/company/{company_id}/metrics")
def get_company_metrics(company_id: str, t: int = 0):
    # Retrieve financial metrics using yfinance (Synchronous)
    try:
        ticker = get_ticker(company_id)
        
        # Fetch Data
        financials = ticker.financials
        cashflow = ticker.cashflow
        balance_sheet = ticker.balance_sheet
        inf = ticker.info # Fetch info early for RoE fallback
        
        # Helper to extract trend
        def get_trend(df, row_name, scale=10000000, link_suffix="financials"): 
            link = f"https://finance.yahoo.com/quote/{ticker.ticker}/{link_suffix}"
            if row_name not in df.index:
                return [], link
            series = df.loc[row_name].iloc[:4][::-1] 
            
            # Chart Scaling Content:
            # Yahoo Finance usually returns values in absolute units (e.g., USD).
            # To display in Crores (1 Crore = 10^7), we divide by 10,000,000.
            # If Yahoo were to return values in thousands, the scale would need adjustment (e.g., 10^4 for Crores).
            
            # Currency Conversion (USD to INR fix) 
            
            # Currency Conversion (USD to INR fix)
            # Some Indian tickers on Yahoo return USD financials. We must convert.
            currency = "INR"
            try:
                currency = ticker.info.get("currency", "INR")
            except: pass

            fx_rate = 1.0
            if currency == "USD":
                fx_rate = 85.0 # Approx rate
            
            # DEBUG: Check raw values
            if not series.empty:
                 print(f"DEBUG RAW VALUES ({row_name}): {series.iloc[0]} (Type: {type(series.iloc[0])}) [Currency: {currency}]")
            
            # Apply FX rate and scale to Crores
            series = (series * fx_rate) / scale
            
            data = []
            for date, value in series.items():
                if pd.isna(value): continue
                year_label = date.strftime("FY%y") 
                data.append({"year": year_label, "value": round(value, 1)}) # Value is already scaled
            return data, link

        
        # 1. Revenue
        scale = 10000000 
        revenue, rev_link = get_trend(financials, "Total Revenue", scale, "financials")
        
        # 2. EBIT
        ebit_row = "EBIT" if "EBIT" in financials.index else "Operating Income"
        operating_profit, ebit_link = get_trend(financials, ebit_row, scale, "financials")
        
        # 3. EPS
        eps, eps_link = get_trend(financials, "Basic EPS", 1, "financials") 
        
        # 4. Operating Cash Flow
        ocf, ocf_link = get_trend(cashflow, "Operating Cash Flow", scale, "cash-flow")
        
        # 5. RoE (Calculated or Fallback)
        net_income = financials.loc["Net Income"] if "Net Income" in financials.index else financials.loc["Net Income Common Stockholders"]
        equity = balance_sheet.loc["Stockholders Equity"] if "Stockholders Equity" in balance_sheet.index else \
                 balance_sheet.loc["Total Equity Gross Minority Interest"] 
        
        roe_link = f"https://finance.yahoo.com/quote/{ticker.ticker}/key-statistics"         
        roe_data = []
        cols = net_income.index.intersection(equity.index)
        sorted_cols = sorted(cols, reverse=True)[:4]
        sorted_cols_osc = sorted_cols[::-1]
        
        for date in sorted_cols_osc:
            ni = net_income[date]
            eq = equity[date]
            if eq != 0:
                roe_val = (ni / eq) * 100
                roe_data.append({"year": date.strftime("FY%y"), "value": round(roe_val, 1)})
        
        if not roe_data and inf.get('returnOnEquity'):
             roe_val = round(inf.get('returnOnEquity', 0) * 100, 1)
             roe_data = [{"year": "TTM", "value": roe_val}]

        # 6. Major Holders
        holders_data = []
        comp_link = f"https://finance.yahoo.com/quote/{ticker.ticker}/holders"
        try:
            holders_df = ticker.major_holders
            # Parsing holders (Keys vary by region/version)
            # Try efficient access or fallback
            insiders = 0
            institutions = 0
            
            # holders_df might be dataframe 0/1 columns
            if not holders_df.empty:
               # Often rows are "Breakdown", "Value" or similar
               # We'll trust mapped keys if available or defaults
               pass 
            
            # Fallback to info for holders if DF is messy
            insiders = inf.get('heldPercentInsiders', 0)
            institutions = inf.get('heldPercentInstitutions', 0)
            public = 1.0 - insiders - institutions
            
            holders_data = [
                 {"name": "Promoters/Insiders", "value": round(insiders * 100, 1)},
                 {"name": "Institutions", "value": round(institutions * 100, 1)},
                 {"name": "Public/Others", "value": round(max(0, public * 100), 1)}
            ]
        except:
             holders_data = [] 

        # 7. Ratios Info
        ratios = {
            "P/E Ratio": round(inf.get('trailingPE', 0), 1),
            "P/B Ratio": round(inf.get('priceToBook', 0), 1),
            "Debt/Equity": round(inf.get('debtToEquity', 0), 1),
            "RoE (Latest)": f"{round(inf.get('returnOnEquity', 0) * 100, 1)}%",
            "Gross Margin": f"{round(inf.get('grossMargins', 0) * 100, 1)}%",
            "Op Margin": f"{round(inf.get('operatingMargins', 0) * 100, 1)}%"
        }
        
        # 8. Profile Data
        profile = {
            "name": inf.get('longName', company_id),
            "ticker": ticker.ticker,
            "description": inf.get('longBusinessSummary', 'No description available.'),
            "industry": inf.get('industry', 'N/A'),
            "sector": inf.get('sector', 'N/A'),
            "website": inf.get('website', '#'),
            "employees": inf.get('fullTimeEmployees', 'N/A'),
            "founded": "N/A", # Yahoo often doesn't give founded date easily in 'info', can try 'start' or skip
            "market_cap": inf.get('marketCap', 0),
            "current_price": inf.get('currentPrice', 0) or inf.get('regularMarketPrice', 0),
            "currency": inf.get('currency', 'INR')
        }

        # Check for extracted summary
        from pathlib import Path
        import json
        extracted_summary = None
        try:
             metrics_path = Path("uploads") / company_id / "metrics.json"
             if metrics_path.exists():
                 with open(metrics_path, "r") as f:
                     saved_metrics = json.load(f)
                     extracted_summary = saved_metrics.get("summary")
        except: pass
        
        if extracted_summary:
            profile["extracted_summary"] = extracted_summary

        return {
            "meta": { "currency_symbol": "₹", "currency_unit": "Cr", "link": f"https://finance.yahoo.com/quote/{ticker.ticker}" },
            "profile": profile,
            "revenue": { "data": revenue, "citation": "Yahoo Finance", "link": rev_link },
            "operating_profit": { "data": operating_profit, "citation": "Yahoo Finance", "link": ebit_link },
            "eps": { "data": eps, "citation": "Yahoo Finance", "link": eps_link },
            "cash_flow": { "data": ocf, "citation": "Yahoo Finance", "link": ocf_link },
            "roe": { "data": roe_data, "citation": "Yahoo Finance (Calc)", "link": roe_link },
            "composition": { "data": holders_data, "citation": "Yahoo Finance", "link": comp_link },
            "ratios": ratios
        }
    except Exception as e:
        print(f"Metrics Error: {e}")
        return {}

@router.get("/company/{company_id}/stock")
async def get_stock_data(company_id: str):
    try:
        ticker = get_ticker(company_id)
        hist = ticker.history(period="1y")
        data = [{"date": d.strftime("%Y-%m-%d"), "price": round(r['Close'], 2)} for d, r in hist.iterrows()]
        link = f"https://finance.yahoo.com/quote/{ticker.ticker}"
        try:
            info = ticker.info
            # print(f"DEBUG INFO: {info.get('currency', 'No Currency')}")
            trading_info = {
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "volume": info.get("volume"),  # Current/Avg volume
                "pe_ratio": info.get("trailingPE"),
                "market_cap": info.get("marketCap"),
                "beta": info.get("beta")
            }
        except Exception as e:
            print(f"Trading Info Error: {e}")
            trading_info = None

        return {"data": data, "citation": "Yahoo Finance API", "link": link, "info": trading_info}
    except Exception as e:
        print(f"Stock Data Critical Error: {e}")
        return {"data": [], "citation": "Unavailable"}

@router.get("/company/{company_id}/news")
async def get_company_news(company_id: str):
    try:
        ticker = get_ticker(company_id)
        news = ticker.news
        
        processed_news = []
        for n in news[:10]: # Valid request for 10
             # Based on debug output, structure is: {'id': '...', 'content': {'title': '...', ...}}
             # OR sometimes flat dicts. We handle both.
             
             data = n.get('content', n) # Try to get 'content' dict, else use n itself
             
             title = data.get('title', 'No Title')
             publisher = data.get('provider', {}).get('displayName', 'Yahoo Finance') if isinstance(data.get('provider'), dict) else data.get('publisher', 'Yahoo Finance')
             
             # Link handling
             clickThroughUrl = data.get('clickThroughUrl')
             link = clickThroughUrl.get('url') if clickThroughUrl else data.get('link', '#')
             # Date handling: Prefer timestamp (seconds), fallback to 0
             pub_time = data.get('providerPublishTime', 0)
             if not pub_time or pub_time == 0:
                  # Fallback: Sometimes it's directly in the dict
                  pub_time = n.get('providerPublishTime', 0)

             processed_news.append({
                "title": title,
                "publisher": publisher,
                "link": link,
                "time": pub_time 
            })
            
        return processed_news
    except Exception as e:
        print(f"News Error: {e}")
        return []

@router.get("/company/{company_id}/status")
def get_company_status(company_id: str):
    """
    Checks if the processing for a company is complete.
    Status is 'ready' if metrics.json exists.
    """
    # 1. Check in-memory DB (fastest)
    # Using a relative import hack or just relying on file system for simplicity/reliability across workers
    # File system is best because upload is in background task
    from pathlib import Path
    
    metrics_path = Path("uploads") / company_id / "metrics.json"
    
    if metrics_path.exists():
        return {"status": "ready", "company_id": company_id}
        
    return {"status": "processing", "company_id": company_id}
