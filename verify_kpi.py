from data_loader import load_initial_data
import pandas as pd

DATA_DIR = r'c:\D\Python\Balancetes\historical'

def verify():
    df = load_initial_data(DATA_DIR)
    
    # Check for BBAS
    bank_df = df[df['Ticker'] == 'BBAS'].sort_values(by='Date').reset_index(drop=True)
    
    if bank_df.empty:
        print("No data for BBAS")
        return

    last_row = bank_df.iloc[-1]
    last_date = last_row['Date']
    
    # Logic from app.py
    # acc_3m = bank_df[bank_df['Date'] > last_date - pd.DateOffset(months=3)]['MonthlyProfit'].sum()
    
    cutoff_date = last_date - pd.DateOffset(months=3)
    filtered_df = bank_df[bank_df['Date'] > cutoff_date]
    
    print(f"--- VERIFICATION FOR BBAS ---")
    print(f"Last Date: {last_date}")
    print(f"Cutoff Date (>): {cutoff_date}")
    print("\nRows included in Sum:")
    print(filtered_df[['Date', 'MonthlyProfit']])
    print(f"\nTotal Sum: {filtered_df['MonthlyProfit'].sum()}")
    print(f"Count: {len(filtered_df)}")

if __name__ == "__main__":
    verify()
