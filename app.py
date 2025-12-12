import streamlit as st
import pandas as pd
import altair as alt
from data_loader import load_initial_data

# Page Config
st.set_page_config(page_title="Banking Dashboard", layout="wide")

# Constants
DATA_DIR = r'c:\D\Python\Balancetes\historical'

BANK_NAMES = {
    'BAZA': 'BAZA3 - BCO DA AMAZONIA S.A.',
    'BMEB': 'BMEB4 - BCO MERCANTIL DO BRASIL S.A.',
    'BMGB': 'BMGB4 - BCO BMG S.A.',
    'PINE': 'PINE4 - BCO PINE S.A.',
    'ABCB': 'ABCB4 - BCO ABC BRASIL S.A.',
    'BRSR': 'BRSR6 - BCO DO ESTADO DO RS S.A.',
    'BBDC': 'BBDC3/4 - BCO BRADESCO S.A.', # Mapping BBDC to generalized name
    'SANB': 'SANB11 - BCO SANTANDER (BRASIL) S.A.',
    'BPAC': 'BPAC11 - BANCO BTG PACTUAL S.A.',
    'BBAS': 'BBAS3 - BCO DO BRASIL S.A.',
    'ITUB': 'ITUB4 - ITAÚ UNIBANCO HOLDING S.A.',
    'BGIP': 'BGIP4 - BCO DO EST. DE SE S.A.',
    'BEES': 'BEES3 - BCO BANESTES S.A.',
    'BLIS': 'BLIS4 - BRB - BCO DE BRASILIA S.A.',
    'BPAN': 'BPAN4 - BANCO PAN'
}

@st.cache_data
def get_data():
    return load_initial_data(DATA_DIR)

def main():
    # Custom CSS to reduce metric font size
    st.markdown("""
    <style>
    div[data-testid="stMetricValue"] {
        font_size: 16px !important;
    }
    div[data-testid="stMetricLabel"] {
        font_size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Banking Financial Dashboard")

    df = get_data()

    if df.empty:
        st.error(f"No data found in {DATA_DIR}. Please ensure files are present.")
        return

    # Sidebar
    st.sidebar.header("Settings")
    
    
    if st.sidebar.button("Clear Cache"):
        st.cache_data.clear()
        st.rerun()

    # Get unique tickers
    available_tickers = sorted(df['Ticker'].unique())
    selected_ticker = st.sidebar.selectbox("Select Bank", available_tickers, format_func=lambda x: BANK_NAMES.get(x, x))
    
    # Filter Data
    bank_df = df[df['Ticker'] == selected_ticker].sort_values(by='Date').reset_index(drop=True)

    if bank_df.empty:
        st.warning("No data for selected bank.")
        return
    
    with st.expander("Show Raw Data"):
        st.write(bank_df.sort_values(by='Date', ascending=False).head(20))

    # Calculations for KPIs
    # Ensure enough data
    if len(bank_df) >= 1:
        last_row = bank_df.iloc[-1]
        last_date = last_row['Date']
        
        # Last Month Profit
        last_profit = last_row['MonthlyProfit']
        
        # Penultimate Profit
        if len(bank_df) >= 2:
            penult_profit = bank_df.iloc[-2]['MonthlyProfit']
            profit_var_pct = ((last_profit - penult_profit) / abs(penult_profit)) * 100 if penult_profit != 0 else 0
        else:
            penult_profit = 0
            profit_var_pct = 0

        # Accumulated 3 Months
        # Filter last 3 months inclusive
        acc_3m = bank_df[bank_df['Date'] > last_date - pd.DateOffset(months=3)]['MonthlyProfit'].sum()
        
        # Accumulated 12 Months
        acc_12m = bank_df[bank_df['Date'] > last_date - pd.DateOffset(months=12)]['MonthlyProfit'].sum()

        st.subheader(f"{BANK_NAMES.get(selected_ticker, selected_ticker)}")
        st.write(f"Ref: {last_date.strftime('%B %Y')}")

        # Last Month ROE
        last_roe = last_row['ROE']
        # Last Projected ROE 3m
        last_proj_roe = last_row['ProjectedROE3m']

        # Helper for formatting
        def format_large_currency(value):
            if abs(value) >= 1e9:
                return f"{value / 1e9:,.2f} B"
            else:
                return f"{value / 1e6:,.2f} M"

        # KPI Columns
        kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
        
        kpi1.metric("Acc. Last 12 Months", format_large_currency(acc_12m))
        kpi2.metric("Acc. Last 3 Months", format_large_currency(acc_3m))
        kpi3.metric("Last Month Profit", format_large_currency(last_profit))
        kpi4.metric("MoM Variation", f"{profit_var_pct:+.2f}%", delta_color="normal")
        kpi5.metric("Last Month ROE", f"{last_roe:.2%}")
        kpi6.metric("Projected ROE (3m)", f"{last_proj_roe:.2%}")

    # --- CHARTS ---
    
    # Pre-calc Variations for Charts
    bank_df['Profit_Var'] = bank_df['MonthlyProfit'].diff()
    bank_df['Equity_Var'] = bank_df['Equity'].diff()

    # Helper to determine scale and normalize data
    def prepare_chart_data(df, col, title_prefix):
        # Check max absolute value to decide scale
        max_val = df[col].abs().max()
        if pd.isna(max_val) or max_val == 0:
            scale_factor = 1e6
            unit = "M"
        elif max_val >= 1e9:
            scale_factor = 1e9
            unit = "B"
        else:
            scale_factor = 1e6
            unit = "M"
            
        scaled_col = f"{col}_Scaled"
        df[scaled_col] = df[col] / scale_factor
        axis_title = f"{title_prefix} ({unit})"
        return df, scaled_col, axis_title

    # 1. Monthly Profit (Bar) and SMA (Line)
    # Scale based on MonthlyProfit
    bank_df, col_profit_scaled, title_profit = prepare_chart_data(bank_df, 'MonthlyProfit', 'Monthly Profit')
    # Scale SMA using same factor as Profit for consistency
    scale_factor_profit = 1e9 if 'B' in title_profit else 1e6
    bank_df['MonthlyProfit_SMA12_Scaled'] = bank_df['MonthlyProfit_SMA12'] / scale_factor_profit

    st.markdown("### Monthly Profit Evolution")
    
    base = alt.Chart(bank_df).encode(x=alt.X('Date:T', scale=alt.Scale(nice=True)))

    bar_profit = base.mark_bar().encode(
        y=alt.Y(f'{col_profit_scaled}:Q', title=title_profit),
        tooltip=['Date', alt.Tooltip(f'{col_profit_scaled}:Q', title=title_profit, format=',.2f')]
    )

    line_sma = base.mark_line(color='orange').encode(
        y=f'MonthlyProfit_SMA12_Scaled:Q',
        tooltip=['Date', alt.Tooltip(f'MonthlyProfit_SMA12_Scaled:Q', title=f"SMA12 ({title_profit.split('(')[1]}", format=',.2f')]
    )

    chart_profit = alt.layer(bar_profit, line_sma).resolve_scale(y='shared')
    st.altair_chart(chart_profit, use_container_width=True)

    # 1.b Accumulated 12m Profit (Line)
    st.markdown("### Accumulated 12m Profit Evolution")
    # Filter out the initial rows where Accumulated12mProfit is NaN
    df_ltm = bank_df.dropna(subset=['Accumulated12mProfit']).copy()
    
    # Scale LTM
    df_ltm, col_ltm_scaled, title_ltm = prepare_chart_data(df_ltm, 'Accumulated12mProfit', 'Accumulated 12m Profit')

    chart_acc_profit = alt.Chart(df_ltm).mark_line(point=True, color='green').encode(
        x=alt.X('Date:T', scale=alt.Scale(nice=True)),
        y=alt.Y(f'{col_ltm_scaled}:Q', title=title_ltm),
        tooltip=['Date', alt.Tooltip(f'{col_ltm_scaled}:Q', title=title_ltm, format=',.2f')]
    )
    st.altair_chart(chart_acc_profit, use_container_width=True)

    # 2. Accumulated 12m Profit Variation (Bar)
    df_ltm['Acc12m_Var'] = df_ltm['Accumulated12mProfit'].diff()
    # Scale Variation
    df_ltm, col_var_scaled, title_var = prepare_chart_data(df_ltm, 'Acc12m_Var', 'Variation LTM')
    
    st.markdown("### Accumulated 12m Profit Variation")
    chart_profit_var = alt.Chart(df_ltm).mark_bar().encode(
        x=alt.X('Date:T', scale=alt.Scale(nice=True)),
        y=alt.Y(f'{col_var_scaled}:Q', title=title_var),
        color=alt.condition(
            alt.datum[col_var_scaled] > 0,
            alt.value("green"),
            alt.value("red")
        ),
        tooltip=['Date', alt.Tooltip(f'{col_var_scaled}:Q', title=title_var, format=',.2f')]
    )
    st.altair_chart(chart_profit_var, use_container_width=True)

    # 3. ROE (Line) - No scaling needed (Percentage)
    st.markdown("### ROE Evolution")
    chart_roe = alt.Chart(bank_df).mark_line(point=True, color='orange').encode(
        x=alt.X('Date:T', scale=alt.Scale(nice=True)),
        y=alt.Y('ROE:Q', axis=alt.Axis(format='%')),
        tooltip=['Date', alt.Tooltip('ROE', format='.2%')]
    )
    st.altair_chart(chart_roe, use_container_width=True)

    # 3.b Projected ROE 3m (Line) - No scaling needed
    st.markdown("### Projected ROE (3m Annualized) Evolution")
    df_proj = bank_df.dropna(subset=['ProjectedROE3m'])
    
    chart_proj_roe = alt.Chart(df_proj).mark_line(point=True, color='teal').encode(
        x=alt.X('Date:T', scale=alt.Scale(nice=True)),
        y=alt.Y('ProjectedROE3m:Q', axis=alt.Axis(format='%')),
        tooltip=['Date', alt.Tooltip('ProjectedROE3m', format='.2%')]
    )
    st.altair_chart(chart_proj_roe, use_container_width=True)

    # 4. Equity (Line)
    scale_factor_equity = 1e6 # Default
    # Scale Equity
    bank_df, col_equity_scaled, title_equity = prepare_chart_data(bank_df, 'Equity', 'Equity')
    
    st.markdown("### Equity Evolution")
    chart_equity = alt.Chart(bank_df).mark_line(point=True, color='purple').encode(
        x=alt.X('Date:T', scale=alt.Scale(nice=True)),
        y=alt.Y(f'{col_equity_scaled}:Q', title=title_equity),
        tooltip=['Date', alt.Tooltip(f'{col_equity_scaled}:Q', title=title_equity, format=',.2f')]
    )
    st.altair_chart(chart_equity, use_container_width=True)

    # 5. Equity Variation (Bar)
    bank_df, col_eq_var_scaled, title_eq_var = prepare_chart_data(bank_df, 'Equity_Var', 'Equity Variation')
    
    st.markdown("### Equity Variation")
    chart_equity_var = alt.Chart(bank_df).mark_bar().encode(
        x=alt.X('Date:T', scale=alt.Scale(nice=True)),
        y=alt.Y(f'{col_eq_var_scaled}:Q', title=title_eq_var),
        color=alt.condition(
            alt.datum[col_eq_var_scaled] > 0,
            alt.value("blue"),
            alt.value("red")
        ),
        tooltip=['Date', alt.Tooltip(f'{col_eq_var_scaled}:Q', title=title_eq_var, format=',.2f')]
    )
    st.altair_chart(chart_equity_var, use_container_width=True)

if __name__ == "__main__":
    main()
