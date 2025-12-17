import pandas as pd
import os
import re

def load_csv_data(directory, existing_df):
    """
    Loads data from Central Bank CSV files (*BANCOS.CSV).
    Calculates Monthly Profit from Semester Cumulative Data.
    Merges with existing DataFrame.
    """
    import glob
    import os
    
    # Map CSV Names to Tickers
    NAME_TO_TICKER = {
        'BCO DO BRASIL S.A.': 'BBAS',
        'BCO BRADESCO S.A.': 'BBDC',
        'BCO SANTANDER (BRASIL) S.A.': 'SANB',
        'ITAÚ UNIBANCO HOLDING S.A.': 'ITUB',
        'BCO ABC BRASIL S.A.': 'ABCB',
        'BCO DA AMAZONIA S.A.': 'BAZA',
        'BCO MERCANTIL DO BRASIL S.A.': 'BMEB',
        'BCO BMG S.A.': 'BMGB',
        'BCO PINE S.A.': 'PINE',
        'BCO DO ESTADO DO RS S.A.': 'BRSR',
        'BANCO BTG PACTUAL S.A.': 'BPAC',
        'BCO DO EST. DE SE S.A.': 'BGIP',
        'BCO BANESTES S.A.': 'BEES',
        'BRB - BCO DE BRASILIA S.A.': 'BLIS',
        'BANCO PAN': 'BPAN',
        'NU FINANCEIRA S.A. - SOCIEDADE DE CRÉDITO, FINANCIAMENTO E INVESTIMENTO': 'ROXO',
        'BANCO INTER': 'INBR',
        'BCO XP S.A.': 'XPBR'
    }
    
    csv_files = glob.glob(os.path.join(directory, "*BANCOS.CSV"))
    print(f"Found {len(csv_files)} CSV files.")
    
    new_rows = []
    
    for file_path in sorted(csv_files):
        try:
            print(f"Processing {os.path.basename(file_path)}...")
            # Read CSV (Skip 3 rows, Latin1)
            df = pd.read_csv(file_path, encoding='latin1', sep=';', skiprows=3)
            
            # Extract Date (Format YYYYMM)
            # Assuming all rows have same date, take from first row
            if df.empty:
                continue
            
            # Column name for date might vary? Inspection showed #DATA_BASE
            date_col = next((c for c in df.columns if 'DATA' in str(c).upper()), None)
            if not date_col:
                print("Date column not found.")
                continue

            date_str = str(df.iloc[0][date_col])
            curr_date = pd.to_datetime(date_str, format='%Y%m')
            print(f"  Date detected: {curr_date.strftime('%Y-%m')}")
            
            # Filter for mapped banks
            for inst_name, ticker in NAME_TO_TICKER.items():
                # Check if Ticker + Date already exists in existing_df
                if not existing_df.empty:
                    exists = ((existing_df['Ticker'] == ticker) & (existing_df['Date'] == curr_date)).any()
                    if exists:
                        # print(f"  Skipping {ticker} (already exists).")
                        continue

                df_bank = df[df['NOME_INSTITUICAO'] == inst_name]
                if df_bank.empty:
                    continue
                
                # Extract Values
                def get_val(code):
                    val = df_bank[df_bank['CONTA'] == code]['SALDO'].values
                    if len(val) > 0:
                        v_str = str(val[0])
                        return float(v_str.replace('.', '').replace(',', '.'))
                    return 0.0
                
                # 7000000003: Income, 8000000002: Expense (Negative), 6100000007: Equity
                income = get_val(7000000003)
                expense = get_val(8000000002)
                equity = get_val(6100000007)
                
                cumulative_result = income + expense
                
                # LOGIC: Monthly Profit = Cumulative Result - Sum(Profits of previous months in semester)
                # Semester starts: Month 1 or Month 7.
                semester_start_month = 1 if curr_date.month <= 6 else 7
                semester_start_date = pd.Timestamp(curr_date.year, semester_start_month, 1)
                
                # Get sums from Existing DF + New Rows processed so far
                mask_excel = (existing_df['Ticker'] == ticker) & \
                             (existing_df['Date'] >= semester_start_date) & \
                             (existing_df['Date'] < curr_date)
                sum_excel = existing_df[mask_excel]['MonthlyProfit'].sum()
                
                sum_new = 0
                for row in new_rows:
                    if row['Ticker'] == ticker and row['Date'] >= semester_start_date and row['Date'] < curr_date:
                        sum_new += row['MonthlyProfit']
                        
                prior_profit_sum = sum_excel + sum_new
                
                monthly_profit = cumulative_result - prior_profit_sum
                
                new_rows.append({
                    'Ticker': ticker,
                    'Date': curr_date,
                    'MonthlyProfit': monthly_profit,
                    'Equity': equity,
                    'Accumulated12mProfit': 0, # Placeholders
                    'MonthlyProfit_SMA12': 0,
                    'ProjectedROE3m': 0,
                    'ROE': 0,
                    'Accumulated3mProfit': 0
                })
                
        except Exception as e:
            print(f"Error processing {os.path.basename(file_path)}: {e}")
            
    if new_rows:
        new_df = pd.DataFrame(new_rows)
        # Combine
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        # Sort
        combined_df = combined_df.sort_values(by=['Ticker', 'Date']).reset_index(drop=True)
        
        # Re-calculate KPIs
        final_dfs = []
        for ticker in combined_df['Ticker'].unique():
            t_df = combined_df[combined_df['Ticker'] == ticker].copy().sort_values(by='Date')
            
            # Recalculate Rolling Metrics
            t_df['Accumulated12mProfit'] = t_df['MonthlyProfit'].rolling(window=12, min_periods=12).sum()
            t_df['MonthlyProfit_SMA12'] = t_df['MonthlyProfit'].rolling(window=12, min_periods=12).mean()
            
            # Recalculate ROE & Projected
            t_df['Accumulated3mProfit'] = t_df['MonthlyProfit'].rolling(window=3, min_periods=3).sum()
            
            t_df['ROE'] = t_df.apply(
                lambda row: row['Accumulated12mProfit'] / row['Equity'] if row['Equity'] != 0 else 0, axis=1
            )
            
            t_df['ProjectedROE3m'] = t_df.apply(
                lambda row: (row['Accumulated3mProfit'] * 4) / row['Equity'] if row['Equity'] != 0 else 0, axis=1
            )
            
            final_dfs.append(t_df)
            
        return pd.concat(final_dfs, ignore_index=True)
        
    return existing_df


def load_initial_data(directory):
    """
    Loads data from the single historical file 'Balancetes_por_ticker.xlsx'.
    Iterates through sheets (Ticker) and extracts Profit/Equity.
    Returns a single consolidated DataFrame.
    """
    all_data = []
    
    # Path to the new consolidated file
    file_path = os.path.join(directory, 'Balancetes_por_ticker.xlsx')
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return pd.DataFrame()

    try:
        xl = pd.ExcelFile(file_path)
        sheets = xl.sheet_names
        print(f"Found {len(sheets)} banks (sheets): {sheets}")
    except Exception as e:
        print(f"Error opening Excel file: {e}")
        return pd.DataFrame()

    for ticker in sheets:
        try:
            # Load Sheet (which contains both Profit and Equity now)
            df = pd.read_excel(file_path, sheet_name=ticker)
            
            # Helper to find column by substring
            def find_col(df, keywords):
                for col in df.columns:
                    col_str = str(col).upper()
                    if any(k in col_str for k in keywords):
                        return col
                return None

            # Clean column names for safety? (Optional, but find_col handles the search)
            # Find columns
            col_date = find_col(df, ['DATA_BASE', 'DATABASE'])
            col_profit = find_col(df, ['LUCRO', 'LUCRO LIQUIDO']) # Avoid 'LUCRO ACUMULADO' if 'LUCRO' matches strictly? 
            # find_col returns first match. If 'LUCRO' comes before 'LUCRO ACUMULADO', likely fine.
            # But strictly 'LUCRO' is better if present. Let's rely on substring 'LUCRO' but NOT 'ACUMULADO' if possible?
            # Actually, the file has 'LUCRO' and 'LUCRO ACUMULADO'. 'LUCRO' is the monthly one.
            # Only picking 'LUCRO' might be ambiguous if 'LUCRO ACUMULADO' is first.
            # Let's be more specific.
            col_profit = next((c for c in df.columns if str(c).upper().strip() == 'LUCRO'), None)
            if not col_profit: # Fallback
                 col_profit = find_col(df, ['LUCRO']) 
            
            col_equity = find_col(df, ['PATRIM', 'PATRIMONIO'])

            if not all([col_date, col_profit, col_equity]):
                print(f"Skipping {ticker}: Column mismatch.\nCols: {df.columns.tolist()}")
                continue

            # Standardize
            df = df.rename(columns={
                col_date: 'Date',
                col_profit: 'MonthlyProfit',
                col_equity: 'Equity'
            })

            # Add Metadata
            df['Ticker'] = ticker
            
            # Ensure numeric
            df['MonthlyProfit'] = pd.to_numeric(df['MonthlyProfit'], errors='coerce').fillna(0)
            df['Equity'] = pd.to_numeric(df['Equity'], errors='coerce').fillna(0)
            
            # Ensure Date
            df['Date'] = df['Date'].astype(str)
            df['Date'] = pd.to_datetime(df['Date'], format='%Y%m', errors='coerce')
            df = df.sort_values(by='Date')

            # --- CALCULATIONS ---
            # Now we have longer history (2015+), so 12m metrics will be valid for more recent years.
            
            # Accumulated 12m Profit
            df['Accumulated12mProfit'] = df['MonthlyProfit'].rolling(window=12, min_periods=12).sum()
            
            # SMA 12
            df['MonthlyProfit_SMA12'] = df['MonthlyProfit'].rolling(window=12, min_periods=12).mean()
            
            # Projected ROE (3 months annualized)
            # Formula: (Accumulated 3m Profit * 4) / Equity
            df['Accumulated3mProfit'] = df['MonthlyProfit'].rolling(window=3, min_periods=3).sum()
            df['ProjectedROE3m'] = df.apply(
                lambda x: (x['Accumulated3mProfit'] * 4) / x['Equity'] if x['Equity'] != 0 and pd.notnull(x['Accumulated3mProfit']) else float('nan'), axis=1
            )
            
            # Calculate ROE (Accumulated 12m Profit / Equity) -- LTM ROE
            df['ROE'] = df.apply(
                lambda x: x['Accumulated12mProfit'] / x['Equity'] if x['Equity'] != 0 else 0, axis=1
            )

            all_data.append(df[['Ticker', 'Date', 'MonthlyProfit', 'Equity', 'Accumulated12mProfit', 'MonthlyProfit_SMA12', 'ProjectedROE3m', 'ROE']])
            print(f"Loaded {ticker}: {len(df)} records. Date Range: {df['Date'].min()} to {df['Date'].max()}")
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    if all_data:
        df_excel = pd.concat(all_data, ignore_index=True)
    else:
        df_excel = pd.DataFrame(columns=['Ticker', 'Date', 'MonthlyProfit', 'Equity'])

    # 2. Check for CSVs and Merge
    # We pass the Excel DF to the CSV loader
    # The CSV loader manages finding files in the ROOT directory (parent of historical?)
    # Based on user context, CSVs are in 'c:\D\Python\Balancetes', so 'directory' arg might need adjustment.
    # passed directory is '.../historical'. Parent is '.../Balancetes'.
    
    root_dir = os.path.dirname(directory) # Go up one level
    df_final = load_csv_data(root_dir, df_excel)
    
    return df_final

    return df_final

def load_valuation_data(directory):
    """
    Loads valuation data from 'multiplos.xlsx'.
    Returns DataFrame with columns: [Ticker, Price, P/L, DY]
    Ticker is normalized to 4 chars to match internal keys.
    """
    import os
    file_path = os.path.join(directory, 'multiplos.xlsx')
    if not os.path.exists(file_path):
        print(f"Valuation file not found: {file_path}")
        return pd.DataFrame()

    try:
        # Read with header=None based on inspection finding header is effectively row 1 (index 1? No, usually row 0 is 1st line)
        # Inspection showed "Ticker" in row 1 (0-indexed). So skiprows=1 ?
        # Wait, inspection output:
        # 1   Ticker  Preço   P/L ...
        # So row 0 is metadata, row 1 is header.
        # But we saw Unnamed columns when reading default?
        # Let's read header=1 to skip row 0.
        
        df = pd.read_excel(file_path, header=0)
        
        # Determine strict indices based on user request/inspection
        # Col 0: Ticker
        # Col 1: Price
        # Col 2: P/L
        # Col 5: DY
        
        # Rename columns by index to be safe against naming variations
        df = df.iloc[:, [0, 1, 2, 5]].copy()
        df.columns = ['Ticker', 'Price', 'P/L', 'DY']
        
        # Clean Data
        df = df.dropna(subset=['Ticker'])
        
        def clean_float(x):
            if isinstance(x, str):
                x = x.replace('.', '').replace(',', '.')
                if '%' in x:
                    x = x.replace('%', '')
                    return float(x) / 100
                return float(x)
            return x
            
        df['Price'] = df['Price'].apply(clean_float)
        df['P/L'] = df['P/L'].apply(clean_float)
        df['DY'] = df['DY'].apply(clean_float)
        
        # Normalize Ticker (First 4 chars)
        df['Ticker'] = df['Ticker'].astype(str).str.strip().str[:4]
        
        # Drop duplicates (keep first found for now, user didn't specify preference between ON/PN)
        df = df.drop_duplicates(subset=['Ticker'])
        
        return df[['Ticker', 'Price', 'P/L', 'DY']]
        
    except Exception as e:
        print(f"Error loading valuation data: {e}")
        return pd.DataFrame()

def load_fundamentus_data():
    """
    Scrapes valuation data from 'www.fundamentus.com.br'.
    Returns DataFrame with columns: [Ticker, Price, P/L, DY]
    """
    import requests
    import io
    
    url = "https://www.fundamentus.com.br/resultado.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse table using pandas
        # Brazil uses decimal=',' and thousands='.'
        tables = pd.read_html(io.StringIO(response.text), decimal=',', thousands='.')
        
        if not tables:
            print("No tables found on Fundamentus.")
            return pd.DataFrame()
            
        df = tables[0]
        
        # Rename columns to match our internal schema
        # Expected columns from Fundamentus: 'Papel', 'Cotação', 'P/L', 'Div.Yield'
        # We need to map them to: 'Ticker', 'Price', 'P/L', 'DY'
        
        rename_map = {
            'Papel': 'Ticker',
            'Cotação': 'Price',
            'P/L': 'P/L',
            'Div.Yield': 'DY'
        }
        
        # Check if required columns exist
        if not set(rename_map.keys()).issubset(df.columns):
            print(f"Fundamentus schema changed. Found: {df.columns.tolist()}")
            return pd.DataFrame()
            
        df = df.rename(columns=rename_map)
        df = df[list(rename_map.values())].copy()
        
        # Data Cleaning
        def clean_percentage(x):
            if isinstance(x, str):
                x = x.replace('%', '').replace('.', '').replace(',', '.')
                return float(x) / 100
            if isinstance(x, (int, float)):
                return float(x) / 100 # Fundamentus usually returns % as string, but if pandas parsed it as float (e.g. 5.0 for 5%), we might need diving. 
                # Actually read_html(decimal=',') handles numbers well, but % often remains string.
                # Let's inspect typical behavior: '6,67%' -> string. 
            return x

        # Price and P/L should be floats already due to read_html(decimal=','), but let's ensure
        # Sometimes read_html might miss if there are weird chars. 
        # Fundamental: 'Cotação' matches 1000 with user locale? Yes.
        
        # Handle simple numeric conversions just in case
        for col in ['Price', 'P/L']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # Handle Percentage for DY
        # Fundamentus sends 'Div.Yield' as '6,00%'. pd.read_html might not strip %.
        # If it is object type, we clean.
        if df['DY'].dtype == 'object':
             df['DY'] = df['DY'].apply(clean_percentage)
        else:
             # If it parsed as float (unlikely with %), check scale. 
             # Usually request returns string "6,75%".
             pass
             
        # Normalize Ticker (First 4 chars)
        # e.g. ITUB4 -> ITUB
        df['Ticker'] = df['Ticker'].astype(str).str.strip().str[:4]
        
        # Drop duplicates, keeping first
        df = df.drop_duplicates(subset=['Ticker'])
        
        print(f"Successfully loaded {len(df)} records from Fundamentus.")
        return df[['Ticker', 'Price', 'P/L', 'DY']]

    except Exception as e:
        print(f"Error scraping Fundamentus: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test run
    # df = load_initial_data(r'c:\D\Python\Balancetes\historical')
    # ... existing test code ...
    # val_df = load_valuation_data(r'c:\D\Python\Balancetes')
    
    fund_df = load_fundamentus_data()
    print("--- FUNDAMENTUS HEAD ---")
    print(fund_df.head())
