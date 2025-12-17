import streamlit as st
import pandas as pd
import altair as alt
from data_loader import load_initial_data, load_fundamentus_data

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
    df = load_initial_data(DATA_DIR)
    
    # Load Valuation Data from Fundamentus (Live)
    val_df = load_fundamentus_data()
    
    return df, val_df

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

def render_general_overview(df):
    st.subheader("General Overview - Key Performance Indicators")
    
    # Get unique tickers
    tickers = sorted(df['Ticker'].unique())
    summary_data = []

    for ticker in tickers:
        bank_df = df[df['Ticker'] == ticker].sort_values(by='Date').reset_index(drop=True)
        if bank_df.empty:
            continue
            
        last_row = bank_df.iloc[-1]
        last_date = last_row['Date']
        
        # Calculations (Mirroring detail view logic)
        acc_3m = bank_df[bank_df['Date'] > last_date - pd.DateOffset(months=3)]['MonthlyProfit'].sum()
        acc_12m = bank_df[bank_df['Date'] > last_date - pd.DateOffset(months=12)]['MonthlyProfit'].sum()
        
        # Penultimate Profit for MoM Var
        if len(bank_df) >= 2:
            penult_profit = bank_df.iloc[-2]['MonthlyProfit']
            profit_var_pct = ((last_row['MonthlyProfit'] - penult_profit) / abs(penult_profit)) if penult_profit != 0 else 0
        else:
            profit_var_pct = 0

        # Construct URL for Ticker Link (?ticker=XYZ)
        # We rely on Streamlit's query param handling. 
        # Note: We use relative path "./?ticker=" to ensure it keeps current host.
        ticker_link = f"./?ticker={ticker}"

        summary_data.append({
            "Bank": BANK_NAMES.get(ticker, ticker),
            "Ticker": ticker_link, # This will be the URL
            "Ref Date": last_date.strftime('%Y-%m'),
            "LTM Profit": acc_12m / 1e6,
            "Last 3m Profit": acc_3m / 1e6,
            "Last Mo. Profit": last_row['MonthlyProfit'] / 1e6,
            "MoM Var": profit_var_pct * 100,
            "ROE": last_row['ROE'] * 100,
            "Proj ROE 3m": last_row['ProjectedROE3m'] * 100, # Shortened name
            "Equity": last_row['Equity'] / 1e9
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # Sorting Controls
    c_sort1, c_sort2 = st.columns([2, 1])
    with c_sort1:
        # Default sort by Proj ROE 3m
        cols = list(summary_df.columns)
        default_ix = cols.index("Proj ROE 3m") if "Proj ROE 3m" in cols else 0
        sort_col = st.selectbox("Sort By", summary_df.columns, index=default_ix)
    with c_sort2:
        # Default Descending
        sort_order = st.radio("Order", ["Ascending", "Descending"], index=1, horizontal=True)
    
    ascending = sort_order == "Ascending"
    summary_df = summary_df.sort_values(by=sort_col, ascending=ascending).reset_index(drop=True)
    
    # helper for concise formatting (unused, can be removed or ignored)
    def format_millions(x):
        return f"{x/1e6:,.2f} M"

    # Apply styling
    # usage of background_gradient requires numeric columns. They are numeric.
    # cmap='RdYlGn' (Red=Low, Green=High) which matches "green highest and red lowest"
    styled_df = summary_df.style.background_gradient(
        subset=['MoM Var', 'Proj ROE 3m'],
        cmap='Greens'
    ).format({
        'LTM Profit': "{:.2f}", # Note: column_config overrides display text usually, but format here helps underlying string usage if exported
        'Last 3m Profit': "{:.2f}",
        'Last Mo. Profit': "{:.2f}",
        'MoM Var': "{:.2f}",
        'ROE': "{:.2f}",
        'Proj ROE 3m': "{:.2f}",
        'Equity': "{:.2f}"
    })
    
    # Streamlit dataframe supports Styler objects
    st.dataframe(
        styled_df,
        column_config={
            "Bank": st.column_config.TextColumn(width="medium"),
            "Ticker": st.column_config.LinkColumn(
                display_text="ticker=([A-Z0-9]+)", # Regex to extract ticker from URL
                help="Click to view details",
                width="small"
            ),
            "Ref Date": st.column_config.TextColumn(width="small"),
            "LTM Profit": st.column_config.NumberColumn(format="%.2f M", help="Accumulated Last 12 Months (Millions)", width="small"),
            "Last 3m Profit": st.column_config.NumberColumn(format="%.2f M", help="Accumulated Last 3 Months (Millions)", width="small"),
            "Last Mo. Profit": st.column_config.NumberColumn(format="%.2f M", help="Millions", width="small"),
            "MoM Var": st.column_config.NumberColumn(format="%.2f %%", width="small"),
            "ROE": st.column_config.NumberColumn(format="%.2f %%", width="small"),
            "Proj ROE 3m": st.column_config.NumberColumn(format="%.2f %%", width="small"),
            "Equity": st.column_config.NumberColumn(format="%.2f B", help="Billions", width="small"),
        },
        use_container_width=True,
        hide_index=True,
        height=600
    )


def render_bank_details(df, selected_ticker):
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
    st.markdown(
        """
        <div style="display: flex; align-items: center; margin-bottom: 10px; font-size: 0.8em; color: gray;">
            <span style="display: inline-block; width: 30px; height: 3px; background-color: orange; margin-right: 8px;"></span>
            12-Month Simple Moving Average
        </div>
        """,
        unsafe_allow_html=True
    )
    
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


def render_valuation_view(df, val_df):
    st.subheader("Valuation & Comparative Analysis")
    
    if val_df.empty:
        st.warning("Valuation data (multiplos.xlsx) not found or empty.")
        return

    # Prepare Data
    # 1. Get latest financial row for each ticker
    tickers = sorted(df['Ticker'].unique())
    latest_data = []
    
    for ticker in tickers:
        bank_df = df[df['Ticker'] == ticker].sort_values(by='Date')
        if bank_df.empty:
            continue
            
        last_row = bank_df.iloc[-1]
        
        # Calculate MoM Growth
        if len(bank_df) >= 2:
            penult_profit = bank_df.iloc[-2]['MonthlyProfit']
            mom_growth = ((last_row['MonthlyProfit'] - penult_profit) / abs(penult_profit)) if penult_profit != 0 else 0
        else:
            mom_growth = 0
            
        latest_data.append({
            'Ticker': ticker,
            'ROE': last_row['ROE'] * 100, # Scale to 0-100 for display
            'Proj ROE 3m': last_row['ProjectedROE3m'] * 100,
            'MoM Growth': mom_growth * 100
        })
        
    fin_df = pd.DataFrame(latest_data)
    
    # 2. Merge with Valuation Data
    merged_df = pd.merge(fin_df, val_df, on='Ticker', how='left')
    
    # 3. Add Bank Names
    merged_df['Bank'] = merged_df['Ticker'].map(lambda x: BANK_NAMES.get(x, x))
    
    # Create Link for Ticker
    merged_df['Ticker_Link'] = merged_df['Ticker'].apply(lambda t: f"./?ticker={t}")
    
    # Scale DY by 100 if it exists
    if 'DY' in merged_df.columns:
        merged_df['DY'] = merged_df['DY'] * 100

    # --- DASHBOARD TABLE ---
    # Customize Display
    # Use Ticker_Link instead of Ticker for the column data, but label it "Ticker"
    display_df = merged_df[['Bank', 'Ticker_Link', 'Price', 'DY', 'P/L', 'ROE', 'Proj ROE 3m', 'MoM Growth']].copy()
    display_df = display_df.rename(columns={'Ticker_Link': 'Ticker'})
    
    # Sorting Controls
    c_sort1, c_sort2 = st.columns([2, 1])
    with c_sort1:
        # Default sort by P/L
        cols = list(display_df.columns)
        default_ix = cols.index("P/L") if "P/L" in cols else 0
        sort_col = st.selectbox("Sort By", display_df.columns, index=default_ix, key="val_sort_col")
    with c_sort2:
        # Default Ascending for P/L (lower is usually better/cheaper)
        sort_order = st.radio("Order", ["Ascending", "Descending"], index=0, horizontal=True, key="val_sort_order")
    
    ascending = sort_order == "Ascending"
    display_df = display_df.sort_values(by=sort_col, ascending=ascending).reset_index(drop=True)

    # Apply styling
    styled_display_df = display_df.style.background_gradient(
        subset=['Proj ROE 3m', 'MoM Growth'],
        cmap='Greens'
    ).format({
        'Price': "R$ {:.2f}",
        'DY': "{:.2f} %",
        'P/L': "{:.2f}",
        'ROE': "{:.2f} %",
        'Proj ROE 3m': "{:.2f} %",
        'MoM Growth': "{:.2f} %"
    })

    st.dataframe(
        styled_display_df,
        column_config={
            "Ticker": st.column_config.LinkColumn(
                display_text="ticker=([A-Z0-9]+)", # Regex to extract ticker from URL
                help="Click to view details",
                width="small"
            ),
            "Price": st.column_config.NumberColumn(format="R$ %.2f", width="small"),
            "DY": st.column_config.NumberColumn(format="%.2f %%", width="small", help="Dividend Yield"),
            "P/L": st.column_config.NumberColumn(format="%.2f", width="small", help="Price / Earnings"),
            "ROE": st.column_config.NumberColumn(format="%.2f %%", width="small", help="Return on Equity (LTM)"),
            "Proj ROE 3m": st.column_config.NumberColumn(format="%.2f %%", width="small", help="Projected ROE (Last 3m Annualized)"),
            "MoM Growth": st.column_config.NumberColumn(format="%.2f %%", width="small", help="Month-over-Month Profit Growth")
        },
        use_container_width=True,
        hide_index=True
    )
    
    st.divider()
    
    # --- SCATTER PLOT ---
    st.subheader("Correlation: ROE vs P/L")
    
    # Filter Controls (Checkboxes)
    # Create columns for checkboxes
    st.write("Filter Banks:")
    chk_cols = st.columns(6)
    selected_banks = []
    
    # Sort by Ticker for checkbox order
    all_tickers = sorted(merged_df['Ticker'].unique())
    
    for i, ticker in enumerate(all_tickers):
        col_idx = i % 6
        with chk_cols[col_idx]:
            # Default True
            if st.checkbox(ticker, value=True, key=f"chk_{ticker}"):
                selected_banks.append(ticker)
                
    # Filter Data based on selection
    chart_df = merged_df[merged_df['Ticker'].isin(selected_banks)].copy()
    
    if chart_df.empty:
        st.warning("No banks selected.")
        return

    # Create Unscaled Columns for Charts (since df has 0-100 values, but Altair % format wants 0-1)
    chart_df['ROE_Unscaled'] = chart_df['ROE'] / 100

    # Altair Chart 1: ROE vs P/L
    base = alt.Chart(chart_df).encode(
        x=alt.X('P/L', scale=alt.Scale(zero=False), title='P/L (Price/Earnings)'),
        y=alt.Y('ROE_Unscaled', axis=alt.Axis(format='%'), scale=alt.Scale(zero=False), title='ROE')
    )
    
    points = base.mark_circle(size=100, color='blue').encode(
        tooltip=['Bank', 'Ticker', 'P/L', alt.Tooltip('ROE_Unscaled', format='.1%', title='ROE')]
    )
    
    text = base.mark_text(
        align='left',
        baseline='middle',
        dx=7
    ).encode(
        text='Ticker'
    )
    
    # Trendline
    regression_line = base.transform_regression('P/L', 'ROE_Unscaled').mark_line(color='red', strokeDash=[5,5])
    
    chart = (points + text + regression_line).properties(height=500)
    
    st.altair_chart(chart, use_container_width=True)
    
    st.divider()
    
    # --- SCATTER PLOT 2 ---
    st.subheader("Correlation: Projected ROE (3m) vs P/L")
    
    # Reuse chart_df (filtered data)
    
    # X = P/L, Y = Proj ROE 3m
    base_proj = alt.Chart(chart_df).encode(
        x=alt.X('P/L', scale=alt.Scale(zero=False), title='P/L (Price/Earnings)'),
        y=alt.Y('Proj ROE 3m', axis=alt.Axis(format='%'), scale=alt.Scale(zero=False), title='Projected ROE (Unscaled for Chart)') 
        # Note: In dataframe we scaled by 100, but Altair format='%' expects 0-1.
        # Wait, in the table we scaled 'Proj ROE 3m' by 100.
        # So 'Proj ROE 3m' is now 15.0, 20.0 etc.
        # If we use format='%', 15.0 becomes 1500%.
        # We need to unscale it for the chart or change format.
        # Let's create a temp unscaled column for chart correctness if needed.
        # Actually, let's just use format='.1f' and add % in title, OR unscale.
        # Cleaner to unscale for 'format=%'
    )
    
    # Create Unscaled Column for Plotting
    chart_df['Proj_ROE_Unscaled'] = chart_df['Proj ROE 3m'] / 100
    
    base_proj = alt.Chart(chart_df).encode(
        x=alt.X('P/L', scale=alt.Scale(zero=False), title='P/L (Price/Earnings)'),
        y=alt.Y('Proj_ROE_Unscaled', axis=alt.Axis(format='%'), scale=alt.Scale(zero=False), title='Projected ROE (3m)')
    )
    
    points_proj = base_proj.mark_circle(size=100, color='teal').encode(
        tooltip=['Bank', 'Ticker', 'P/L', alt.Tooltip('Proj_ROE_Unscaled', format='.1%', title="Proj ROE")]
    )
    
    text_proj = base_proj.mark_text(
        align='left',
        baseline='middle',
        dx=7
    ).encode(
        text='Ticker'
    )
    
    # Trendline
    regression_line_proj = base_proj.transform_regression('P/L', 'Proj_ROE_Unscaled').mark_line(color='orange', strokeDash=[5,5])
    
    chart_proj = (points_proj + text_proj + regression_line_proj).properties(height=500)
    
    st.altair_chart(chart_proj, use_container_width=True)


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

    df, val_df = get_data() # Modified to receive val_df

    if df.empty:
        st.error(f"No data found in {DATA_DIR}. Please ensure files are present.")
        return

    # Check query params for navigation
    # We use st.query_params to get 'ticker'
    query_params = st.query_params
    nav_ticker = query_params.get("ticker", None)

    # Sidebar
    st.sidebar.header("Settings")
    
    if st.sidebar.button("Clear Cache"):
        st.cache_data.clear()
        st.rerun()

    # Determine default View Mode and Ticker index
    # If nav_ticker is present, switch to 'Bank Details' and select that ticker
    default_view_index = 0 # General Overview
    default_ticker_index = 0

    available_tickers = sorted(df['Ticker'].unique())

    if nav_ticker and nav_ticker in available_tickers:
        default_view_index = 1 # Bank Details
        try:
            default_ticker_index = available_tickers.index(nav_ticker)
        except ValueError:
            default_ticker_index = 0

    # View Selection
    view_mode = st.sidebar.radio(
        "View Mode", 
        ["General Overview", "Bank Details", "Valuation"], # Added "Valuation"
        index=default_view_index
    )

    if view_mode == "Bank Details":
        selected_ticker = st.sidebar.selectbox(
            "Select Bank", 
            available_tickers, 
            index=default_ticker_index,
            format_func=lambda x: BANK_NAMES.get(x, x)
        )
        render_bank_details(df, selected_ticker)
    elif view_mode == "Valuation": # Added new condition for Valuation view
        render_valuation_view(df, val_df)
    else:
        render_general_overview(df)

if __name__ == "__main__":
    main()
