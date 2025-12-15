import pandas as pd
from data_loader import load_initial_data
import os

def verify_logic():
    print("Loading initial data (Excel)...")
    # Load all data
    df_excel = load_initial_data(r'c:\D\Python\Balancetes\historical')
    
    # Filter for BBAS (Banco do Brasil) and Aug 2025
    # Note: load_initial_data converts Date to datetime
    target_date = pd.Timestamp('2025-08-01')
    ticker = 'BBAS'
    
    row_excel = df_excel[(df_excel['Ticker'] == ticker) & (df_excel['Date'] == target_date)]
    
    if row_excel.empty:
        print(f"Error: No Excel data found for {ticker} on {target_date}")
        print("Available dates for BBAS:", df_excel[df_excel['Ticker'] == ticker]['Date'].unique())
        return

    excel_profit = row_excel.iloc[0]['MonthlyProfit']
    excel_equity = row_excel.iloc[0]['Equity']
    
    print(f"\nExcel Data for {ticker} on {target_date.strftime('%Y-%m')}:")
    print(f"Profit: {excel_profit:,.2f}")
    print(f"Equity: {excel_equity:,.2f}")
    
    print("\nLoading CSV data (202508BANCOS.CSV)...")
    csv_path = r'c:\D\Python\Balancetes\202508BANCOS.CSV'
    
    try:
        # Proposed Logic
        df_csv = pd.read_csv(csv_path, encoding='latin1', sep=';', skiprows=3)
        
        # Filter for Banco do Brasil
        inst_name = 'BCO DO BRASIL S.A.'
        df_bb = df_csv[df_csv['NOME_INSTITUICAO'] == inst_name]
        
        if df_bb.empty:
            print(f"Error: Institution '{inst_name}' not found in CSV.")
            return

        # Extract values
        # 7000000003: Resultado Credor (Income)
        # 8000000002: Resultado Devedor (Expense)
        # 6100000007: Patrimônio Líquido (Equity)
        
        def get_val(code):
            # Codes are integers in CSV? check dtypes if needed, assumes int or matches
            val = df_bb[df_bb['CONTA'] == code]['SALDO'].values
            if len(val) > 0:
                # Replace comma with dot for conversion
                return float(str(val[0]).replace('.', '').replace(',', '.'))
            return 0.0

        income = get_val(7000000003)
        expense = get_val(8000000002)
        equity_csv = get_val(6100000007)
        
        # Expense is negative, so we ADD it to get the net result
        profit_csv_cumulative = income + expense
        
        print(f"\nCSV Calculated Data for {inst_name}:")
        print(f"Income (7...): {income:,.2f}")
        print(f"Expense (8...): {expense:,.2f}")
        print(f"Calculated Cumulative Result (Inc + Exp): {profit_csv_cumulative:,.2f}")
        print(f"Equity (610...): {equity_csv:,.2f}")
        
        
        # Check July Data to verify Semester Accumulation
        prev_date = pd.Timestamp('2025-07-01')
        row_prev = df_excel[(df_excel['Ticker'] == ticker) & (df_excel['Date'] == prev_date)]
        
        excel_profit_jul = 0
        if not row_prev.empty:
            excel_profit_jul = row_prev.iloc[0]['MonthlyProfit']
            print(f"Excel Profit for July ({prev_date.strftime('%Y-%m')}): {excel_profit_jul:,.2f}")
        
        # Hypothesis: Monthly Profit = Cumulative Current - Cumulative Previous (or Sum of prev monthly profits?)
        # Since we don't have CSV for July loaded, let's assume Excel July Profit == July Cumulative.
        
        calculated_monthly_profit = profit_csv_cumulative - excel_profit_jul
        
        print("\n--- Comparison ---")
        diff_profit = excel_profit - calculated_monthly_profit
        
        print(f"Target Excel Profit (Aug): {excel_profit:,.2f}")
        print(f"Derived Monthly Profit (CSV Cumul - Excel Jul): {calculated_monthly_profit:,.2f}")
        print(f"Difference: {diff_profit:,.2f}")
        
        if abs(diff_profit) < 1.0: # allow small rounding float error
            print(">> PROFIT MATCHES PERFECTLY (Cumulative Logic Confirmed) <<")
        else:
            print(">> PROFIT MISMATCH <<")
        diff_equity = excel_equity - equity_csv
        
        print(f"Profit Difference (Excel - CSV): {diff_profit:,.2f}")
        if abs(diff_profit) < 0.01:
            print(">> PROFIT MATCHES PERFECTLY <<")
        else:
            print(">> PROFIT MISMATCH <<")
            
        print(f"Equity Difference (Excel - CSV): {diff_equity:,.2f}")
        if abs(diff_equity) < 0.01:
            print(">> EQUITY MATCHES PERFECTLY <<")
        else:
            print(">> EQUITY MISMATCH <<")

    except Exception as e:
        print(f"Error processing CSV: {e}")

if __name__ == "__main__":
    verify_logic()
