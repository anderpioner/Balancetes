import pandas as pd
import os

file_path = r'c:\D\Python\Balancetes\historical\Balancetes_por_ticker.xlsx'

if os.path.exists(file_path):
    try:
        xl = pd.ExcelFile(file_path)
        print(f"Sheets found: {xl.sheet_names}")
        
        # Inspect first sheet
        first_sheet = xl.sheet_names[0]
        df = pd.read_excel(file_path, sheet_name=first_sheet)
        print(f"\n--- HEADER OF SHEET '{first_sheet}' ---")
        print(df.head())
        print(f"COLUMNS: {list(df.columns)}")
        
        # Check if Equity is also here or just Profit?
        # User said "data of banks" and "history of profit". Need to check if Equity is included.
    except Exception as e:
        print(f"Error reading file: {e}")
else:
    print(f"File not found: {file_path}")
