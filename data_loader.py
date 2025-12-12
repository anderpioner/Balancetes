import pandas as pd
import os
import re

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
        final_df = pd.concat(all_data, ignore_index=True)
        # Dates are already datetime from the loop
        return final_df.sort_values(by=['Ticker', 'Date'])
    else:
        return pd.DataFrame()

if __name__ == "__main__":
    # Test run
    df = load_initial_data(r'c:\D\Python\Balancetes\historical')
    print("--- FINAL DATAFRAME HEAD ---")
    print(df.head())
    if not df.empty:
        print("--- STATS ---")
        print(df.groupby('Ticker')['Date'].count())
