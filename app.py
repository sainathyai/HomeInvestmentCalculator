import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

# Configure page
st.set_page_config(page_title="Buy vs Rent Calculator", page_icon="🏠", layout="wide")

st.title("🏠 Buy vs Rent: Comprehensive Net Worth Calculator")
st.markdown("Compare the long-term financial impact of buying vs renting with all factors included.")

# Sidebar for inputs
st.sidebar.header("📊 Input Parameters")

# Market / Loan Inputs
st.sidebar.subheader("🏡 Home & Loan Details")
home_price = st.sidebar.number_input("Home Price ($)", min_value=50000, max_value=5000000, value=350000, step=10000)
down_payment_percent = st.sidebar.slider("Down Payment (%)", min_value=0, max_value=50, value=20) / 100
mortgage_rate = st.sidebar.slider("Mortgage Interest Rate (%)", min_value=2.0, max_value=10.0, value=6.4, step=0.1) / 100
loan_years = st.sidebar.selectbox("Loan Term (years)", [15, 20, 30], index=2)

# PMI
pmi_rate = 0.0
if down_payment_percent < 0.20:
    pmi_rate = st.sidebar.slider("PMI Rate (% annually)", min_value=0.0, max_value=2.0, value=0.5, step=0.1) / 100
    st.sidebar.info(f"PMI applies until you reach 20% equity")

# Monthly Expenses
st.sidebar.subheader("💰 Ownership Costs")
property_tax_rate = st.sidebar.slider("Property Tax Rate (% annually)", min_value=0.0, max_value=5.0, value=3.0, step=0.1) / 100
property_tax_growth = st.sidebar.slider("Property Tax Growth Rate (% annually)", min_value=0.0, max_value=5.0, value=0.0, step=0.1) / 100
home_insurance_yr = st.sidebar.number_input("Home Insurance ($/year)", min_value=0, max_value=10000, value=3000, step=100)
hoa_monthly = st.sidebar.number_input("HOA Fee ($/month)", min_value=0, max_value=1000, value=100, step=10)
maint_percent = st.sidebar.slider("Maintenance (% of home value/year)", min_value=0.0, max_value=3.0, value=1.0, step=0.1) / 100
utilities_premium = st.sidebar.number_input("Extra Utilities vs Apartment ($/month)", min_value=0, max_value=500, value=50, step=10, help="Homes often have higher utility costs")

# Rental Inputs
st.sidebar.subheader("🏢 Rental Costs")
monthly_rent = st.sidebar.number_input("Monthly Rent ($)", min_value=500, max_value=10000, value=2200, step=100)
rent_inflation = st.sidebar.slider("Rent Inflation Rate (% annually)", min_value=0.0, max_value=10.0, value=3.0, step=0.1) / 100
renters_insurance_yr = st.sidebar.number_input("Renters Insurance ($/year)", min_value=0, max_value=1000, value=250, step=50)

# Investment / Growth Assumptions
st.sidebar.subheader("📈 Market Assumptions")
home_appreciation = st.sidebar.slider("Home Appreciation Rate (% annually)", min_value=0.0, max_value=10.0, value=3.5, step=0.1) / 100
invest_return = st.sidebar.slider("Investment Return Rate (% annually)", min_value=0.0, max_value=15.0, value=7.0, step=0.1) / 100
closing_costs_buy = st.sidebar.slider("Closing Costs to Buy (% of price)", min_value=0.0, max_value=5.0, value=3.0, step=0.1) / 100
selling_costs = st.sidebar.slider("Selling Costs (% of price)", min_value=0.0, max_value=10.0, value=7.0, step=0.1) / 100

# Tax Benefits
st.sidebar.subheader("🧾 Tax Information")
tax_filing_status = st.sidebar.selectbox("Tax Filing Status",
    ["Single", "Married Filing Jointly", "Married Filing Separately", "Head of Household"])

# Tax brackets and deductions for 2024
tax_info = {
    "Single": {
        "standard_deduction": 14600,
        "brackets": [(11000, 0.10), (44725, 0.12), (95375, 0.22), (182100, 0.24), (231250, 0.32), (578125, 0.35), (float('inf'), 0.37)]
    },
    "Married Filing Jointly": {
        "standard_deduction": 29200,
        "brackets": [(22000, 0.10), (89050, 0.12), (190750, 0.22), (364200, 0.24), (462500, 0.32), (693750, 0.35), (float('inf'), 0.37)]
    },
    "Married Filing Separately": {
        "standard_deduction": 14600,
        "brackets": [(11000, 0.10), (44525, 0.12), (95375, 0.22), (182100, 0.24), (231250, 0.32), (346875, 0.35), (float('inf'), 0.37)]
    },
    "Head of Household": {
        "standard_deduction": 21900,
        "brackets": [(15700, 0.10), (59850, 0.12), (95350, 0.22), (182100, 0.24), (231250, 0.32), (578100, 0.35), (float('inf'), 0.37)]
    }
}

income = st.sidebar.number_input("Annual Gross Income ($)", min_value=0, max_value=1000000, value=100000, step=5000,
    help="Used to calculate mortgage interest tax deduction benefit")

# Simulation Time
st.sidebar.subheader("⏱️ Time Horizon")
years_to_plot = st.sidebar.slider("Years to Simulate", min_value=5, max_value=40, value=30)

# Calculate standard deduction and SALT cap
standard_deduction = tax_info[tax_filing_status]["standard_deduction"]
salt_cap = 10000  # State and Local Tax deduction cap

def calculate_marginal_tax_rate(income, filing_status):
    """Calculate marginal tax rate based on income and filing status"""
    brackets = tax_info[filing_status]["brackets"]
    for limit, rate in brackets:
        if income <= limit:
            return rate
    return brackets[-1][1]

marginal_tax_rate = calculate_marginal_tax_rate(income, tax_filing_status)

# ==========================================
# CALCULATIONS
# ==========================================
loan_amount = home_price * (1 - down_payment_percent)
down_payment_amt = home_price * down_payment_percent
monthly_rate = mortgage_rate / 12
total_months = years_to_plot * 12

# Lists to store plotting data
months = []
net_worth_buy = []
net_worth_rent = []
buyer_costs_breakdown = []
renter_costs_breakdown = []

# Additional tracking
tax_savings_list = []
pmi_payments_list = []
equity_buildup_list = []
principal_paid_list = []
interest_paid_list = []
remaining_balance_list = []
home_value_list = []
cumulative_interest_list = []
cumulative_principal_list = []
monthly_payment_list = []
rent_payment_list = []

# Initial setup
renter_portfolio = down_payment_amt + (home_price * closing_costs_buy)
current_home_value = home_price
remaining_loan = loan_amount
current_rent = monthly_rent
current_property_tax_rate = property_tax_rate

# Calculate fixed monthly mortgage payment (Principal + Interest)
mortgage_payment = npf.pmt(monthly_rate, loan_years * 12, -loan_amount)

# Track annual values for tax calculation
annual_interest_paid = 0
annual_property_tax_paid = 0
cumulative_interest = 0
cumulative_principal = 0

for m in range(1, total_months + 1):
    # --- BUYER COSTS ---
    # Property tax, Insurance, Maintenance (monthly)
    monthly_tax = (current_home_value * current_property_tax_rate) / 12
    monthly_ins = home_insurance_yr / 12
    monthly_maint = (current_home_value * maint_percent) / 12

    # PMI (only if equity < 20%)
    current_equity_percent = (current_home_value - remaining_loan) / current_home_value
    monthly_pmi = 0
    if current_equity_percent < 0.20 and pmi_rate > 0:
        monthly_pmi = (loan_amount * pmi_rate) / 12

    # Calculate interest and principal
    interest_payment = remaining_loan * monthly_rate
    principal_payment = mortgage_payment - interest_payment

    # Track annual tax deductible items
    annual_interest_paid += interest_payment
    annual_property_tax_paid += monthly_tax

    # Total buyer costs before tax benefits
    total_cost_buy_pretax = mortgage_payment + monthly_tax + monthly_ins + hoa_monthly + monthly_maint + monthly_pmi + utilities_premium

    # Calculate tax benefit (done annually)
    monthly_tax_benefit = 0
    if m % 12 == 0:  # End of year
        # Itemized deductions = mortgage interest + property tax (capped at SALT limit)
        property_tax_deduction = min(annual_property_tax_paid, salt_cap)
        total_itemized = annual_interest_paid + property_tax_deduction

        # Tax benefit only if itemized > standard deduction
        if total_itemized > standard_deduction:
            annual_tax_benefit = (total_itemized - standard_deduction) * marginal_tax_rate
        else:
            annual_tax_benefit = 0

        # Spread annual benefit across 12 months
        monthly_tax_benefit = annual_tax_benefit / 12

        # Reset annual trackers
        annual_interest_paid = 0
        annual_property_tax_paid = 0

    total_cost_buy = total_cost_buy_pretax - monthly_tax_benefit

    # --- RENTER COSTS ---
    monthly_renter_ins = renters_insurance_yr / 12
    total_cost_rent = current_rent + monthly_renter_ins

    # --- THE DIFFERENCE ---
    monthly_savings = total_cost_buy - total_cost_rent

    # Update Renter Portfolio
    renter_portfolio *= (1 + invest_return / 12)
    renter_portfolio += monthly_savings

    # Update Buyer Stats
    remaining_loan -= principal_payment
    cumulative_interest += interest_payment
    cumulative_principal += principal_payment

    # Update Market Values (Appreciation / Inflation)
    current_home_value *= (1 + home_appreciation / 12)

    # Once a year, increase rent, insurance, and property tax
    if m % 12 == 0:
        current_rent *= (1 + rent_inflation)
        home_insurance_yr *= (1 + rent_inflation)
        renters_insurance_yr *= (1 + rent_inflation)
        current_property_tax_rate *= (1 + property_tax_growth)

    # --- CALCULATE NET WORTH ---
    buyer_equity = current_home_value - remaining_loan - (current_home_value * selling_costs)

    months.append(m / 12)
    net_worth_buy.append(buyer_equity)
    net_worth_rent.append(renter_portfolio)
    tax_savings_list.append(monthly_tax_benefit * 12)  # Annualized
    pmi_payments_list.append(monthly_pmi * 12)  # Annualized
    equity_buildup_list.append(current_home_value - remaining_loan)
    principal_paid_list.append(principal_payment)
    interest_paid_list.append(interest_payment)
    remaining_balance_list.append(remaining_loan)
    home_value_list.append(current_home_value)
    cumulative_interest_list.append(cumulative_interest)
    cumulative_principal_list.append(cumulative_principal)
    monthly_payment_list.append(total_cost_buy)
    rent_payment_list.append(total_cost_rent)

    # Track costs for breakdown
    if m % 12 == 0:  # Store annual costs
        buyer_costs_breakdown.append({
            'Year': m // 12,
            'P&I': mortgage_payment * 12,
            'Property Tax': monthly_tax * 12,
            'Insurance': home_insurance_yr,
            'HOA': hoa_monthly * 12,
            'Maintenance': monthly_maint * 12,
            'PMI': monthly_pmi * 12,
            'Utilities': utilities_premium * 12,
            'Tax Benefit': -monthly_tax_benefit * 12,
            'Total': total_cost_buy * 12
        })
        renter_costs_breakdown.append({
            'Year': m // 12,
            'Rent': current_rent * 12,
            'Insurance': renters_insurance_yr,
            'Total': total_cost_rent * 12
        })

# ==========================================
# DISPLAY RESULTS
# ==========================================

# Key Metrics at top
col1, col2, col3, col4 = st.columns(4)

final_buy_networth = net_worth_buy[-1]
final_rent_networth = net_worth_rent[-1]
difference = final_buy_networth - final_rent_networth

with col1:
    st.metric("Monthly P&I Payment", f"${mortgage_payment:,.0f}")
with col2:
    st.metric(f"Buy Net Worth (Year {years_to_plot})", f"${final_buy_networth:,.0f}")
with col3:
    st.metric(f"Rent Net Worth (Year {years_to_plot})", f"${final_rent_networth:,.0f}")
with col4:
    if difference > 0:
        st.metric("Advantage", "Buying", f"${difference:,.0f}", delta_color="normal")
    else:
        st.metric("Advantage", "Renting", f"${abs(difference):,.0f}", delta_color="inverse")

# Net Worth Calculation Explanation (Collapsible)
with st.expander("💡 Understanding Net Worth Calculations", expanded=False):
    col_explain1, col_explain2 = st.columns(2)

    with col_explain1:
        st.markdown("""
        **🏠 Buyer's Net Worth Components:**

        **Assets:**
        - Current home value (with appreciation)

        **Liabilities:**
        - Remaining mortgage balance
        - Selling costs ({:.1f}% of home value)

        **Formula:**
        ```
        Net Worth = Home Value
                    - Remaining Loan Balance
                    - Selling Costs
        ```

        **What's Included:**
        - ✅ Home equity buildup (principal payments)
        - ✅ Property appreciation over time
        - ✅ Tax benefits (reduce monthly costs)
        - ❌ Not included: Down payment & closing costs (already spent)
        """.format(selling_costs * 100))

    with col_explain2:
        st.markdown("""
        **💼 Renter's Net Worth Components:**

        **Investment Portfolio:**
        - Down payment saved (${:,.0f})
        - Closing costs saved (${:,.0f})
        - Monthly cost differences invested
        - Compound growth at {:.1f}% annually

        **Formula:**
        ```
        Net Worth = Investment Portfolio Balance
        ```

        **How It Grows:**
        1. Starts with down payment + closing costs
        2. Each month: Portfolio grows at investment rate
        3. Monthly difference added/subtracted:
           - If renting is cheaper → money invested
           - If renting is more expensive → money withdrawn
        """.format(down_payment_amt, home_price * closing_costs_buy, invest_return * 100))

st.markdown("---")

# Find Breakeven
crossover_idx = np.argwhere(np.diff(np.sign(np.array(net_worth_buy) - np.array(net_worth_rent)))).flatten()
if len(crossover_idx) > 0:
    breakeven_year = months[crossover_idx[0]]
    st.info(f"📍 **Breakeven Point**: Buying becomes advantageous after **{breakeven_year:.1f} years**")
else:
    if difference > 0:
        st.success("✅ **Buying is advantageous** from the start in this scenario")
    else:
        st.warning("⚠️ **No breakeven found** - Renting remains advantageous throughout the entire timeframe")

# Main Chart - Net Worth Comparison (smaller)
st.subheader("📊 Key Comparisons")

# Calculate tax benefit threshold
# Tax benefit = (itemized - standard deduction) * marginal rate
# At year 1, we have mortgage interest
first_year_interest = mortgage_payment * 12 - (mortgage_payment * 12 - loan_amount * mortgage_rate)
first_year_property_tax = (home_price * property_tax_rate)
property_tax_deduction = min(first_year_property_tax, salt_cap)

# Calculate income needed for tax benefit
itemized_deductions = first_year_interest + property_tax_deduction
income_for_tax_benefit = standard_deduction / marginal_tax_rate  # Approximate threshold

# More precise: find income where itemized > standard
if itemized_deductions > standard_deduction:
    # Tax benefit exists, calculate minimum income to make it worthwhile
    tax_benefit_threshold = standard_deduction
    benefit_nullified = False
else:
    tax_benefit_threshold = itemized_deductions / marginal_tax_rate
    benefit_nullified = True

col_nw1, col_nw2 = st.columns(2)

with col_nw1:
    fig1, ax1 = plt.subplots(figsize=(5, 3.5))
    ax1.plot(months, net_worth_buy, label='Net Worth (Buying)', color='#2E86AB', linewidth=2)
    ax1.plot(months, net_worth_rent, label='Net Worth (Renting)', color='#06A77D', linewidth=2, linestyle='--')

    if len(crossover_idx) > 0:
        ax1.axvline(x=breakeven_year, color='#D62828', linestyle=':', linewidth=2, label=f'Breakeven: {breakeven_year:.1f}Y')

    ax1.set_xlabel('Years', fontsize=9)
    ax1.set_ylabel('Net Worth ($)', fontsize=9)
    ax1.set_title('Net Worth Comparison', fontsize=10, fontweight='bold')
    ax1.grid(True, which='both', linestyle='--', alpha=0.3)
    ax1.legend(fontsize=8, loc='best')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    ax1.tick_params(labelsize=8)
    plt.tight_layout()
    st.pyplot(fig1)

    # Add net worth difference chart below
    st.markdown("##### 📊 Net Worth Difference Over Time")
    fig1b, ax1b = plt.subplots(figsize=(5, 3))
    net_worth_diff = np.array(net_worth_buy) - np.array(net_worth_rent)

    # Color the area based on who's ahead
    colors = ['#2E86AB' if diff > 0 else '#06A77D' for diff in net_worth_diff]
    ax1b.fill_between(months, net_worth_diff, 0, alpha=0.3,
                       color='#2E86AB', where=(net_worth_diff > 0), label='Buyer Ahead')
    ax1b.fill_between(months, net_worth_diff, 0, alpha=0.3,
                       color='#06A77D', where=(net_worth_diff <= 0), label='Renter Ahead')
    ax1b.plot(months, net_worth_diff, color='#262730', linewidth=2)
    ax1b.axhline(y=0, color='black', linestyle='-', linewidth=0.8)

    if len(crossover_idx) > 0:
        ax1b.axvline(x=breakeven_year, color='#D62828', linestyle=':', linewidth=2)

    ax1b.set_xlabel('Years', fontsize=9)
    ax1b.set_ylabel('Difference ($)', fontsize=9)
    ax1b.set_title('Buy - Rent Net Worth Difference', fontsize=10, fontweight='bold')
    ax1b.grid(True, alpha=0.3)
    ax1b.legend(fontsize=8, loc='best')
    ax1b.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    ax1b.tick_params(labelsize=8)
    plt.tight_layout()
    st.pyplot(fig1b)

with col_nw2:
    # Tax benefit analysis
    st.markdown("##### 🧾 Tax Benefit Analysis")

    # Calculate total tax benefit over the years
    total_tax_benefit = sum(tax_savings_list)
    avg_annual_tax_benefit = total_tax_benefit / years_to_plot if years_to_plot > 0 else 0

    st.metric("Avg Annual Tax Benefit", f"${avg_annual_tax_benefit:,.0f}")
    st.metric("Total Tax Benefit", f"${total_tax_benefit:,.0f}")

    # Show when tax benefits matter
    st.markdown(f"""
    **Tax Benefit Threshold:**
    - Your itemized deductions (Year 1): **${itemized_deductions:,.0f}**
    - Standard deduction ({tax_filing_status}): **${standard_deduction:,.0f}**
    """)

    if itemized_deductions > standard_deduction:
        excess = itemized_deductions - standard_deduction
        st.success(f"✅ You benefit from itemizing (+${excess:,.0f})")

        # Calculate approximate income threshold
        # If income is too low, marginal rate drops and benefit decreases
        min_income_for_benefit = standard_deduction / 0.12  # 12% bracket minimum
        st.info(f"""
        **Income Impact:**
        - Tax benefits are maximized at your current income (${income:,.0f})
        - Benefits would be reduced if income < ${min_income_for_benefit:,.0f}
        - At very low incomes (<${standard_deduction:,.0f}), standard deduction is better
        """)
    else:
        deficit = standard_deduction - itemized_deductions
        st.warning(f"⚠️ Standard deduction is better (-${deficit:,.0f})")
        st.info(f"Tax benefits are **nullified** at all income levels for this scenario")

    # Show marginal rate impact
    st.markdown(f"""
    **Your Tax Bracket:**
    - Marginal rate: **{marginal_tax_rate*100:.0f}%**
    - Each $1,000 of deductions saves ${marginal_tax_rate*1000:.0f}
    """)

# Comprehensive Visualizations - Multiple smaller charts
st.subheader("📊 Comprehensive Financial Analysis")

# Row 1: Home Value & Mortgage Balance
col1, col2 = st.columns(2)

with col1:
    fig2, ax2 = plt.subplots(figsize=(5, 3.5))
    ax2.plot(months, home_value_list, color='#06A77D', linewidth=2, label='Home Value')
    ax2.plot(months, remaining_balance_list, color='#D62828', linewidth=2, label='Mortgage Balance')
    ax2.fill_between(months, home_value_list, remaining_balance_list, alpha=0.2, color='#06A77D', label='Equity')
    ax2.set_xlabel('Years', fontsize=9)
    ax2.set_ylabel('Amount ($)', fontsize=9)
    ax2.set_title('Home Value vs Mortgage Balance', fontsize=10, fontweight='bold')
    ax2.legend(fontsize=8, loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    ax2.tick_params(labelsize=8)
    plt.tight_layout()
    st.pyplot(fig2)

with col2:
    fig3, ax3 = plt.subplots(figsize=(5, 3.5))
    ax3.plot(months, principal_paid_list, color='#2E86AB', linewidth=2, label='Principal')
    ax3.plot(months, interest_paid_list, color='#F77F00', linewidth=2, label='Interest')
    ax3.set_xlabel('Years', fontsize=9)
    ax3.set_ylabel('Monthly Payment ($)', fontsize=9)
    ax3.set_title('Principal vs Interest (Monthly)', fontsize=10, fontweight='bold')
    ax3.legend(fontsize=8, loc='best')
    ax3.grid(True, alpha=0.3)
    ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax3.tick_params(labelsize=8)
    plt.tight_layout()
    st.pyplot(fig3)

# Row 2: Cumulative Interest & Monthly Costs
col3, col4 = st.columns(2)

with col3:
    fig4, ax4 = plt.subplots(figsize=(5, 3.5))
    ax4.plot(months, cumulative_interest_list, color='#D62828', linewidth=2.5, label='Total Interest Paid')
    ax4.plot(months, cumulative_principal_list, color='#06A77D', linewidth=2.5, label='Total Principal Paid')
    ax4.set_xlabel('Years', fontsize=9)
    ax4.set_ylabel('Cumulative Amount ($)', fontsize=9)
    ax4.set_title('Cumulative Principal & Interest Paid', fontsize=10, fontweight='bold')
    ax4.legend(fontsize=8, loc='best')
    ax4.grid(True, alpha=0.3)
    ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    ax4.tick_params(labelsize=8)
    plt.tight_layout()
    st.pyplot(fig4)

with col4:
    fig5, ax5 = plt.subplots(figsize=(5, 3.5))
    ax5.plot(months, monthly_payment_list, color='#2E86AB', linewidth=2, label='Buyer Total Cost')
    ax5.plot(months, rent_payment_list, color='#06A77D', linewidth=2, linestyle='--', label='Renter Total Cost')
    ax5.set_xlabel('Years', fontsize=9)
    ax5.set_ylabel('Monthly Cost ($)', fontsize=9)
    ax5.set_title('Monthly Total Costs Comparison', fontsize=10, fontweight='bold')
    ax5.legend(fontsize=8, loc='best')
    ax5.grid(True, alpha=0.3)
    ax5.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax5.tick_params(labelsize=8)
    plt.tight_layout()
    st.pyplot(fig5)

# Row 3: Equity Growth & Tax Benefits
col5, col6 = st.columns(2)

with col5:
    fig6, ax6 = plt.subplots(figsize=(5, 3.5))
    ax6.plot(months, equity_buildup_list, color='#2E86AB', linewidth=2.5)
    ax6.fill_between(months, equity_buildup_list, alpha=0.3, color='#2E86AB')
    ax6.set_xlabel('Years', fontsize=9)
    ax6.set_ylabel('Equity ($)', fontsize=9)
    ax6.set_title('Home Equity Growth Over Time', fontsize=10, fontweight='bold')
    ax6.grid(True, alpha=0.3)
    ax6.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    ax6.tick_params(labelsize=8)
    plt.tight_layout()
    st.pyplot(fig6)

with col6:
    fig7, ax7 = plt.subplots(figsize=(5, 3.5))
    ax7.plot(months, tax_savings_list, color='#06A77D', linewidth=2, label='Tax Savings')
    if max(pmi_payments_list) > 0:
        ax7.plot(months, pmi_payments_list, color='#D62828', linewidth=2, label='PMI Payments')
    ax7.set_xlabel('Years', fontsize=9)
    ax7.set_ylabel('Annual Amount ($)', fontsize=9)
    ax7.set_title('Annual Tax Benefits & PMI', fontsize=10, fontweight='bold')
    ax7.legend(fontsize=8, loc='best')
    ax7.grid(True, alpha=0.3)
    ax7.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    ax7.tick_params(labelsize=8)
    plt.tight_layout()
    st.pyplot(fig7)

# Additional summary metrics
st.subheader("💰 Key Financial Metrics")
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

total_interest_paid = cumulative_interest_list[-1]
total_principal_paid = cumulative_principal_list[-1]
final_home_value = home_value_list[-1]
total_pmi_paid = sum(pmi_payments_list)

with metric_col1:
    st.metric("Total Interest Paid", f"${total_interest_paid:,.0f}")
with metric_col2:
    st.metric("Total Principal Paid", f"${total_principal_paid:,.0f}")
with metric_col3:
    st.metric(f"Final Home Value (Year {years_to_plot})", f"${final_home_value:,.0f}")
with metric_col4:
    st.metric("Total PMI Paid", f"${total_pmi_paid:,.0f}")

# Detailed Tables in Expander
with st.expander("📋 View Detailed Annual Breakdown Tables"):
    col_a, col_b = st.columns(2)

    with col_a:
        st.write("**Buyer Annual Costs**")
        buyer_df = pd.DataFrame(buyer_costs_breakdown)
        st.dataframe(buyer_df.style.format({
            'P&I': '${:,.0f}',
            'Property Tax': '${:,.0f}',
            'Insurance': '${:,.0f}',
            'HOA': '${:,.0f}',
            'Maintenance': '${:,.0f}',
            'PMI': '${:,.0f}',
            'Utilities': '${:,.0f}',
            'Tax Benefit': '${:,.0f}',
            'Total': '${:,.0f}'
        }), width=600)

    with col_b:
        st.write("**Renter Annual Costs**")
        renter_df = pd.DataFrame(renter_costs_breakdown)
        st.dataframe(renter_df.style.format({
            'Rent': '${:,.0f}',
            'Insurance': '${:,.0f}',
            'Total': '${:,.0f}'
        }), width=600)

# Footer with assumptions
with st.expander("ℹ️ See Calculation Assumptions & Notes"):
    st.markdown("""
    ### What's Included:

    **Buyer Costs:**
    - Monthly mortgage payment (Principal & Interest)
    - Property taxes (with optional growth rate)
    - Home insurance (grows with inflation)
    - HOA fees
    - Maintenance (% of home value)
    - PMI (if down payment < 20%, until 20% equity reached)
    - Extra utilities vs apartment
    - **Tax benefits** from mortgage interest & property tax deductions (SALT cap applied)
    - Closing costs to buy
    - Selling costs when liquidating

    **Renter Costs:**
    - Monthly rent (grows with inflation)
    - Renters insurance (grows with inflation)

    **Investment Growth:**
    - Renter invests: down payment saved + closing costs saved + monthly difference (if renting is cheaper)
    - Home appreciates at specified rate
    - Renter's portfolio grows at specified investment return rate

    ### Tax Calculation Notes:
    - Uses 2024 tax brackets and standard deductions
    - Mortgage interest is fully deductible
    - Property tax deduction capped at $10,000 (SALT cap)
    - Tax benefit only applies if itemized deductions > standard deduction
    - Marginal tax rate used based on your income

    ### Limitations:
    - Doesn't account for refinancing opportunities
    - Assumes consistent investment returns (no market volatility)
    - Capital gains exclusion ($250K/$500K) not modeled in net worth calculation
    - Doesn't model special assessments or major repairs
    """)

st.sidebar.markdown("---")
st.sidebar.info("💡 Adjust parameters on the left to see how different scenarios affect your decision!")

# Export Options
st.markdown("---")
st.subheader("📥 Export Results")

col_export1, col_export2 = st.columns(2)

with col_export1:
    # Generate summary report as text
    report_text = f"""
BUY VS RENT ANALYSIS REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{'='*60}
INPUT PARAMETERS
{'='*60}

HOME & LOAN DETAILS:
  Home Price:                ${home_price:,}
  Down Payment:              {down_payment_percent*100:.1f}% (${down_payment_amt:,})
  Mortgage Rate:             {mortgage_rate*100:.2f}%
  Loan Term:                 {loan_years} years
  Loan Amount:               ${loan_amount:,}
  Monthly P&I:               ${mortgage_payment:,.2f}

OWNERSHIP COSTS:
  Property Tax Rate:         {property_tax_rate*100:.2f}% annually
  Property Tax Growth:       {property_tax_growth*100:.2f}% annually
  Home Insurance:            ${home_insurance_yr:,}/year
  HOA Fee:                   ${hoa_monthly:,}/month
  Maintenance:               {maint_percent*100:.2f}% of home value/year
  Extra Utilities:           ${utilities_premium:,}/month
  PMI Rate:                  {pmi_rate*100:.2f}% annually

RENTAL COSTS:
  Monthly Rent:              ${monthly_rent:,}
  Rent Inflation:            {rent_inflation*100:.2f}% annually
  Renters Insurance:         ${renters_insurance_yr:,}/year

MARKET ASSUMPTIONS:
  Home Appreciation:         {home_appreciation*100:.2f}% annually
  Investment Return:         {invest_return*100:.2f}% annually
  Closing Costs (Buy):       {closing_costs_buy*100:.2f}% of price
  Selling Costs:             {selling_costs*100:.2f}% of price

TAX INFORMATION:
  Filing Status:             {tax_filing_status}
  Annual Income:             ${income:,}
  Marginal Tax Rate:         {marginal_tax_rate*100:.0f}%
  Standard Deduction:        ${standard_deduction:,}

SIMULATION:
  Years Simulated:           {years_to_plot} years

{'='*60}
RESULTS SUMMARY
{'='*60}

NET WORTH AT YEAR {years_to_plot}:
  Buying:                    ${final_buy_networth:,.0f}
  Renting:                   ${final_rent_networth:,.0f}
  Difference:                ${difference:,.0f}
  {"Advantage: BUYING" if difference > 0 else "Advantage: RENTING"}

BREAKEVEN ANALYSIS:
  {f"Breakeven at Year {breakeven_year:.1f}" if len(crossover_idx) > 0 else "No breakeven found in timeframe"}

TOTAL COSTS (BUYING):
  Total Interest Paid:       ${total_interest_paid:,.0f}
  Total Principal Paid:      ${total_principal_paid:,.0f}
  Total PMI Paid:            ${total_pmi_paid:,.0f}
  Final Home Value:          ${final_home_value:,.0f}

TAX BENEFITS:
  Total Tax Savings:         ${total_tax_benefit:,.0f}
  Average Annual Benefit:    ${avg_annual_tax_benefit:,.0f}

{'='*60}
CALCULATION NOTES
{'='*60}

The renter's portfolio includes:
1. Down payment saved (${down_payment_amt:,})
2. Closing costs saved (${home_price * closing_costs_buy:,})
3. Monthly cost differences invested at {invest_return*100:.2f}%

The buyer's net worth accounts for:
1. Home equity (value minus remaining loan)
2. Selling costs ({selling_costs*100:.0f}% of home value)

Tax benefits calculated using:
- Mortgage interest deduction
- Property tax deduction (SALT cap: $10,000)
- Only applied when itemized > standard deduction

{'='*60}
"""

    # Download as text file
    st.download_button(
        label="📄 Download Summary Report (TXT)",
        data=report_text,
        file_name=f"buy_vs_rent_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

with col_export2:
    # Create CSV with all annual data
    export_df = pd.DataFrame({
        'Year': [b['Year'] for b in buyer_costs_breakdown],
        'Buyer_PI': [b['P&I'] for b in buyer_costs_breakdown],
        'Buyer_PropertyTax': [b['Property Tax'] for b in buyer_costs_breakdown],
        'Buyer_Insurance': [b['Insurance'] for b in buyer_costs_breakdown],
        'Buyer_HOA': [b['HOA'] for b in buyer_costs_breakdown],
        'Buyer_Maintenance': [b['Maintenance'] for b in buyer_costs_breakdown],
        'Buyer_PMI': [b['PMI'] for b in buyer_costs_breakdown],
        'Buyer_Utilities': [b['Utilities'] for b in buyer_costs_breakdown],
        'Buyer_TaxBenefit': [b['Tax Benefit'] for b in buyer_costs_breakdown],
        'Buyer_TotalCost': [b['Total'] for b in buyer_costs_breakdown],
        'Renter_Rent': [r['Rent'] for r in renter_costs_breakdown],
        'Renter_Insurance': [r['Insurance'] for r in renter_costs_breakdown],
        'Renter_TotalCost': [r['Total'] for r in renter_costs_breakdown],
        'Buyer_NetWorth': [net_worth_buy[i*12-1] for i in range(1, years_to_plot+1)],
        'Renter_NetWorth': [net_worth_rent[i*12-1] for i in range(1, years_to_plot+1)],
        'Home_Value': [home_value_list[i*12-1] for i in range(1, years_to_plot+1)],
        'Mortgage_Balance': [remaining_balance_list[i*12-1] for i in range(1, years_to_plot+1)],
        'Home_Equity': [equity_buildup_list[i*12-1] for i in range(1, years_to_plot+1)],
    })

    csv = export_df.to_csv(index=False)

    st.download_button(
        label="📊 Download Data (CSV)",
        data=csv,
        file_name=f"buy_vs_rent_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# Calculation verification section
st.markdown("---")
st.subheader("🔍 Calculation Verification")

with st.expander("📊 View Net Worth Calculation Breakdown (Month 1)"):
    st.markdown("### 🧮 Detailed Net Worth Calculation - Month 1")

    # Recalculate Month 1 for verification
    month1_tax = (home_price * property_tax_rate) / 12
    month1_ins = home_insurance_yr / 12
    month1_maint = (home_price * maint_percent) / 12
    month1_interest = loan_amount * monthly_rate
    month1_principal = mortgage_payment - month1_interest
    month1_pmi = (loan_amount * pmi_rate) / 12 if down_payment_percent < 0.20 and pmi_rate > 0 else 0

    # Month 1 values
    month1_home_value = home_price * (1 + home_appreciation / 12)
    month1_remaining_loan = loan_amount - month1_principal
    month1_equity = month1_home_value - month1_remaining_loan
    month1_selling_costs = month1_home_value * selling_costs
    month1_buyer_networth = month1_home_value - month1_remaining_loan - month1_selling_costs

    month1_buyer_total = mortgage_payment + month1_tax + month1_ins + hoa_monthly + month1_maint + month1_pmi + utilities_premium
    month1_renter_total = monthly_rent + renters_insurance_yr/12
    month1_difference = month1_buyer_total - month1_renter_total

    month1_renter_portfolio_start = down_payment_amt + (home_price * closing_costs_buy)
    month1_renter_portfolio_growth = month1_renter_portfolio_start * (invest_return / 12)
    month1_renter_networth = month1_renter_portfolio_start * (1 + invest_return / 12) + month1_difference

    col_nw1, col_nw2 = st.columns(2)

    with col_nw1:
        st.markdown("#### 🏠 BUYER Net Worth Calculation")
        st.markdown(f"""
        **Step 1: Home Value After Month 1**
        - Purchase price: ${home_price:,.2f}
        - Appreciation (1 month @ {home_appreciation*100:.2f}%/year): ${month1_home_value - home_price:,.2f}
        - **Home value**: ${month1_home_value:,.2f}

        **Step 2: Remaining Mortgage**
        - Original loan: ${loan_amount:,.2f}
        - Principal paid (Month 1): ${month1_principal:,.2f}
        - Interest paid (Month 1): ${month1_interest:,.2f}
        - **Remaining balance**: ${month1_remaining_loan:,.2f}

        **Step 3: Calculate Equity**
        - Home value: ${month1_home_value:,.2f}
        - Minus remaining loan: -${month1_remaining_loan:,.2f}
        - **Gross equity**: ${month1_equity:,.2f}

        **Step 4: Subtract Selling Costs**
        - Selling costs ({selling_costs*100:.1f}%): -${month1_selling_costs:,.2f}

        ---
        **🎯 BUYER NET WORTH (Month 1): ${month1_buyer_networth:,.2f}**
        """)

    with col_nw2:
        st.markdown("#### 💼 RENTER Net Worth Calculation")
        st.markdown(f"""
        **Step 1: Starting Investment Portfolio**
        - Down payment saved: ${down_payment_amt:,.2f}
        - Closing costs saved: ${home_price * closing_costs_buy:,.2f}
        - **Initial portfolio**: ${month1_renter_portfolio_start:,.2f}

        **Step 2: Investment Growth (1 Month)**
        - Return rate: {invest_return*100:.2f}%/year = {invest_return/12*100:.3f}%/month
        - Investment gain: ${month1_renter_portfolio_growth:,.2f}
        - **Portfolio after growth**: ${month1_renter_portfolio_start * (1 + invest_return / 12):,.2f}

        **Step 3: Monthly Cost Difference**
        - Buyer total cost: ${month1_buyer_total:,.2f}
        - Renter total cost: ${month1_renter_total:,.2f}
        - Difference: ${month1_difference:,.2f}
        - {"(Buyer costs MORE → money withdrawn)" if month1_difference > 0 else "(Renter costs MORE → money withdrawn)"}

        **Step 4: Add/Subtract Difference**
        - Portfolio: ${month1_renter_portfolio_start * (1 + invest_return / 12):,.2f}
        - {"Plus" if month1_difference > 0 else "Minus"} difference: {"+" if month1_difference > 0 else ""}{month1_difference:,.2f}

        ---
        **🎯 RENTER NET WORTH (Month 1): ${month1_renter_networth:,.2f}**
        """)

    st.markdown("---")
    st.markdown(f"""
    ### 📊 Net Worth Comparison After Month 1:
    - **Buyer Net Worth**: ${month1_buyer_networth:,.2f}
    - **Renter Net Worth**: ${month1_renter_networth:,.2f}
    - **Difference**: ${month1_buyer_networth - month1_renter_networth:,.2f} ({("Buyer ahead" if month1_buyer_networth > month1_renter_networth else "Renter ahead")})

    💡 **Note**: This is just Month 1. The gap changes over time due to:
    - Home appreciation vs investment returns
    - Increasing principal payments (amortization)
    - Rising rent vs fixed mortgage P&I
    - Tax benefits accumulating over the year
    """)
