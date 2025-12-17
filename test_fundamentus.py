import pandas as pd
import requests

url = "https://www.fundamentus.com.br/resultado.php"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    print(f"Fetching {url}...")
    # Use requests to get content with headers (often needed for anti-scraping)
    r = requests.get(url, headers=headers)
    
    # Parse tables
    tables = pd.read_html(r.content, decimal=',', thousands='.')
    
    if tables:
        df = tables[0]
        print("Columns found:", df.columns.tolist())
        print("\nFirst 5 rows:")
        print(df.head())
        
        # Check for specific columns
        required = ['Papel', 'Cotação', 'P/L', 'Div.Yield']
        missing = [c for c in required if c not in df.columns]
        if missing:
             print(f"Missing columns: {missing}")
        else:
             print("All required columns found!")
    else:
        print("No tables found.")

except Exception as e:
    print(f"Error: {e}")
