import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt

# ==========================================
# 1. INPUTS (Update these values as needed)
# ==========================================
# Market / Loan Inputs
home_price = 350000
down_payment_percent = 0.20
mortgage_rate = 0.064       # 6.4% Interest rate
loan_years = 15

# Monthly Expenses
property_tax_rate = 0.030   # 3.0% (High TX rate)
home_insurance_yr = 3000    # Annual insurance premium
hoa_monthly = 100
maint_percent = 0.01        # 1% of home value/year for repairs

# Rental Inputs
monthly_rent = 2200
rent_inflation = 0.03       # Rents rise 3% / year
renters_insurance_yr = 250  # Cheap renters insurance

# Investment / Growth Assumptions
home_appreciation = 0.035   # Home price grows 3.5% / year
invest_return = 0.07        # S&P 500 avg return (7%)
closing_costs_buy = 0.03    # 3% to buy (Title, fees)
selling_costs = 0.07        # 7% to sell (Agent fees, staging)

# Simulation Time
years_to_plot = 30

# ==========================================
# 2. CALCULATIONS
# ==========================================
loan_amount = home_price * (1 - down_payment_percent)
down_payment_amt = home_price * down_payment_percent
monthly_rate = mortgage_rate / 12
total_months = years_to_plot * 12

# Lists to store plotting data
months = []
net_worth_buy = []
net_worth_rent = []

# Initial setup
# Renter starts with the Cash that the Buyer spent upfront
renter_portfolio = down_payment_amt + (home_price * closing_costs_buy)
current_home_value = home_price
remaining_loan = loan_amount
current_rent = monthly_rent

# Calculate fixed monthly mortgage payment (Principal + Interest)
mortgage_payment = npf.pmt(monthly_rate, loan_years * 12, -loan_amount)

print(f"Monthly P&I: ${mortgage_payment:,.2f}")

for m in range(1, total_months + 1):
    # --- BUYER COSTS ---
    # Property tax, Insurance, Maintenance (monthly)
    monthly_tax = (current_home_value * property_tax_rate) / 12
    monthly_ins = home_insurance_yr / 12
    monthly_maint = (current_home_value * maint_percent) / 12
    
    total_cost_buy = mortgage_payment + monthly_tax + monthly_ins + hoa_monthly + monthly_maint

    # --- RENTER COSTS ---
    monthly_renter_ins = renters_insurance_yr / 12
    total_cost_rent = current_rent + monthly_renter_ins

    # --- THE DIFFERENCE ---
    # Compare costs. The one who saves money invests it.
    monthly_savings = total_cost_buy - total_cost_rent
    
    # Update Renter Portfolio
    # Renter earns investment return on previous balance
    renter_portfolio *= (1 + invest_return / 12)
    # If Buying is cheaper, Renter withdraws to pay rent. If Renting is cheaper, Renter invests savings.
    renter_portfolio += monthly_savings 
    
    # Update Buyer Stats
    interest_payment = remaining_loan * monthly_rate
    principal_payment = mortgage_payment - interest_payment
    remaining_loan -= principal_payment
    
    # Update Market Values (Appreciation / Inflation)
    current_home_value *= (1 + home_appreciation / 12)
    
    # Once a year, increase rent & insurance
    if m % 12 == 0:
        current_rent *= (1 + rent_inflation)
        home_insurance_yr *= (1 + rent_inflation) # Assume insurance rises w/ inflation

    # --- CALCULATE NET WORTH ---
    # Buyer Net Worth = Home Value - Mortgage - Cost to Sell
    buyer_equity = current_home_value - remaining_loan - (current_home_value * selling_costs)
    
    months.append(m / 12) # Convert to years
    net_worth_buy.append(buyer_equity)
    net_worth_rent.append(renter_portfolio)

# ==========================================
# 3. PLOTTING
# ==========================================
plt.figure(figsize=(10, 6))
plt.plot(months, net_worth_buy, label='Net Worth (Buying)', color='blue', linewidth=2)
plt.plot(months, net_worth_rent, label='Net Worth (Renting)', color='green', linewidth=2, linestyle='--')

# Find Breakeven
crossover_idx = np.argwhere(np.diff(np.sign(np.array(net_worth_buy) - np.array(net_worth_rent)))).flatten()
if len(crossover_idx) > 0:
    breakeven_year = months[crossover_idx[0]]
    plt.axvline(x=breakeven_year, color='red', linestyle=':', label=f'Breakeven: {breakeven_year:.1f} Years')
    print(f"Breakeven occurs at Year: {breakeven_year:.1f}")
else:
    print("No breakeven found in the selected timeframe.")

plt.title(f'Buy vs Rent: Net Worth Comparison ($350k Home, 3.0% Tax)', fontsize=14)
plt.xlabel('Years', fontsize=12)
plt.ylabel('Net Worth ($)', fontsize=12)
plt.grid(True, which='both', linestyle='--', alpha=0.7)
plt.legend()
plt.show()