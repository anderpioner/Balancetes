import pandas as pd
import io

file_path = r"c:\D\Python\Balancetes\202509BANCOS.CSV"
output_file = r"c:\D\Python\Balancetes\csv_info.txt"

def get_csv_info():
    try:
        # Read with correct skip parameters
        df = pd.read_csv(file_path, encoding='latin1', sep=';', skiprows=3)
        
        # Search for Profit/Equity accounts
        keywords = ['LUCRO', 'RESULTADO', 'PATRIMONIO', 'PATRIMÔNIO', 'PATRIMONIO LIQUIDO']
        relevant_accounts = df[df['NOME_CONTA'].str.upper().str.contains('|'.join(keywords), na=False)][['CONTA', 'NOME_CONTA']].drop_duplicates().head(50)
        
        # Get list of banks
        banks = df['NOME_INSTITUICAO'].unique()
        
        info = []
        info.append("Relevant Accounts found:")
        info.append(relevant_accounts.to_string())
        
        info.append("\n\nDistinct Institutions:")
        for bank in sorted(banks):
            info.append(f"- {bank}")
            
        return "\n".join(info)
        
    except Exception as e:
        return f"Error analyzing CSV: {e}"

with open(output_file, "w", encoding="utf-8") as f:
    f.write(get_csv_info())
