import pandas as pd

file_path = r"c:\D\Python\Balancetes\multiplos.xlsx"

try:
    df = pd.read_excel(file_path, header=None)
    print("\nFirst 10 rows (Raw):")
    print(df.head(10).to_string())
except Exception as e:
    print(f"Error reading Excel: {e}")
