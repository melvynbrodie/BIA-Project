
import requests
import json
import sys
import asyncio
from app.api.metrics import get_company_metrics

async def test():
    print("Testing metrics for RELIANCE...")
    try:
        data = await get_company_metrics("RELIANCE")
        print("Success!")
        print(f"Revenue Data Points: {len(data['revenue']['data'])}")
        print(f"Stock Data Price: {data['stock_price']['data'][-1]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_data()
