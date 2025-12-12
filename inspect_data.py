import pandas as pd
import os

files = ['BBAS_LL.xlsx', 'BBAS_E.xlsx']
base_dir = r'c:\D\Python\Balancetes'

for f in files:
    path = os.path.join(base_dir, f)
    if os.path.exists(path):
        try:
            print(f"--- READING {f} ---")
            df = pd.read_excel(path, engine='openpyxl')
            print(df.head())
            print(f"COLUMNS: {list(df.columns)}")
            print("-" * 30)
        except Exception as e:
            print(f"ERROR reading {f}: {e}")
    else:
        print(f"File not found: {path}")
