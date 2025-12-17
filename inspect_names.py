import pandas as pd
import glob
import os

def find_bank_names():
    csv_files = glob.glob(r'c:\D\Python\Balancetes\*BANCOS.CSV')
    if not csv_files:
        print("No CSV files found.")
        return

    # Use the latest file
    file_path = sorted(csv_files)[-1]
    print(f"Inspecting {file_path}...")
    
    try:
        df = pd.read_csv(file_path, encoding='latin1', sep=';', skiprows=3)
        unique_names = sorted(df['NOME_INSTITUICAO'].dropna().unique())
        
        keywords = ['NU', 'INTER', 'XP', 'ROXO', 'INBR']
        
        print("--- MATCHING NAMES ---")
        for name in unique_names:
            name_upper = str(name).upper()
            if any(k in name_upper for k in keywords):
                print(name)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_bank_names()
