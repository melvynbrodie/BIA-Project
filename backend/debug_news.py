
import yfinance as yf
import json

def debug_news():
    try:
        t = yf.Ticker("TCS.NS")
        news = t.news
        print(f"Type: {type(news)}")
        if news:
            print(f"First Item Type: {type(news[0])}")
            print(f"First Item Dir: {dir(news[0])}")
            print(f"First Item Content: {news[0]}")
        else:
            print("No news found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_news()
