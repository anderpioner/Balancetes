import pandas as pd
import glob
import os

def check_data():
    # 1. Inspect Names in CSV
    csv_files = glob.glob(r'c:\D\Python\Balancetes\*BANCOS.CSV')
    if csv_files:
        file_path = sorted(csv_files)[-1]
        print(f"Inspecting {file_path} for Nu/Financeira...")
        try:
            df = pd.read_csv(file_path, encoding='latin1', sep=';', skiprows=3)
            unique_names = sorted(df['NOME_INSTITUICAO'].dropna().unique())
            
            print("--- POTENTIAL NU MATCHES ---")
            for name in unique_names:
                name_u = str(name).upper()
                if 'NU ' in name_u or 'NUBANK' in name_u or 'ROXO' in name_u or 'FINANCEIRA' in name_u:
                    print(name)
        except Exception as e:
            print(f"CSV Error: {e}")

    # 2. Inspect Valuation Data
    val_path = r'c:\D\Python\Balancetes\multiplos.xlsx'
    if os.path.exists(val_path):
        print("\n--- VALUATION DATA (multiplos.xlsx) ---")
        try:
            # Based on previous knowledge, header is likely row 1
            df_val = pd.read_excel(val_path, header=1)
            print(df_val.head())
            print("Tickers found:", df_val.iloc[:, 0].unique())
        except Exception as e:
            print(f"Excel Error: {e}")

if __name__ == "__main__":
    check_data()
