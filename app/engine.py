import numpy_financial as npf
import numpy as np

TAX_INFO = {
    "single": {
        "standard_deduction": 14600,
        "brackets": [(11000, 0.10), (44725, 0.12), (95375, 0.22), (182100, 0.24),
                     (231250, 0.32), (578125, 0.35), (float('inf'), 0.37)]
    },
    "married_jointly": {
        "standard_deduction": 29200,
        "brackets": [(22000, 0.10), (89050, 0.12), (190750, 0.22), (364200, 0.24),
                     (462500, 0.32), (693750, 0.35), (float('inf'), 0.37)]
    },
    "married_separately": {
        "standard_deduction": 14600,
        "brackets": [(11000, 0.10), (44525, 0.12), (95375, 0.22), (182100, 0.24),
                     (231250, 0.32), (346875, 0.35), (float('inf'), 0.37)]
    },
    "head_of_household": {
        "standard_deduction": 21900,
        "brackets": [(15700, 0.10), (59850, 0.12), (95350, 0.22), (182100, 0.24),
                     (231250, 0.32), (578100, 0.35), (float('inf'), 0.37)]
    },
}

SALT_CAP = 10000


def _marginal_rate(income, filing_status):
    for limit, rate in TAX_INFO[filing_status]["brackets"]:
        if income <= limit:
            return rate
    return TAX_INFO[filing_status]["brackets"][-1][1]


def calculate(params):
    # Unpack inputs
    home_price         = float(params["home_price"])
    down_pct           = float(params["down_payment_pct"]) / 100
    mortgage_rate      = float(params["mortgage_rate"]) / 100
    loan_years         = int(params["loan_years"])
    pmi_rate           = float(params.get("pmi_rate", 0)) / 100
    property_tax_rate  = float(params["property_tax_rate"]) / 100
    property_tax_growth= float(params.get("property_tax_growth", 0)) / 100
    home_insurance_yr  = float(params["home_insurance_yr"])
    hoa_monthly        = float(params["hoa_monthly"])
    maint_pct          = float(params["maintenance_pct"]) / 100
    utilities_premium  = float(params.get("utilities_premium", 0))
    monthly_rent       = float(params["monthly_rent"])
    rent_inflation     = float(params["rent_inflation"]) / 100
    renters_ins_yr     = float(params["renters_insurance_yr"])
    home_appreciation  = float(params["home_appreciation"]) / 100
    invest_return      = float(params["invest_return"]) / 100
    closing_costs_pct  = float(params["closing_costs_pct"]) / 100
    selling_costs_pct  = float(params["selling_costs_pct"]) / 100
    filing_status      = params.get("filing_status", "single")
    income             = float(params.get("income", 100000))
    years              = int(params["years"])

    standard_deduction = TAX_INFO[filing_status]["standard_deduction"]
    marginal_rate      = _marginal_rate(income, filing_status)

    loan_amount        = home_price * (1 - down_pct)
    down_payment_amt   = home_price * down_pct
    monthly_rate       = mortgage_rate / 12
    total_months       = years * 12

    mortgage_payment   = float(npf.pmt(monthly_rate, loan_years * 12, -loan_amount)) if loan_amount > 0 else 0

    # State
    renter_portfolio        = down_payment_amt + home_price * closing_costs_pct
    current_home_value      = home_price
    remaining_loan          = loan_amount
    current_rent            = monthly_rent
    current_insurance_yr    = home_insurance_yr
    current_renters_ins_yr  = renters_ins_yr
    current_prop_tax_rate   = property_tax_rate

    # Accumulators
    annual_interest_paid    = 0.0
    annual_property_tax_paid= 0.0
    cumulative_interest     = 0.0
    cumulative_principal    = 0.0
    last_monthly_tax_benefit= 0.0

    # Output series (monthly, indexed by year fraction)
    series = {
        "months":             [],
        "net_worth_buy":      [],
        "net_worth_rent":     [],
        "home_value":         [],
        "mortgage_balance":   [],
        "equity":             [],
        "cumulative_interest":[],
        "cumulative_principal":[],
        "monthly_cost_buy":   [],
        "monthly_cost_rent":  [],
        "principal_payment":  [],
        "interest_payment":   [],
        "tax_savings_annual": [],
        "pmi_annual":         [],
    }

    annual_buyer_rows  = []
    annual_renter_rows = []

    for m in range(1, total_months + 1):
        monthly_tax   = (current_home_value * current_prop_tax_rate) / 12
        monthly_ins   = current_insurance_yr / 12
        monthly_maint = (current_home_value * maint_pct) / 12

        equity_pct    = (current_home_value - remaining_loan) / current_home_value if current_home_value > 0 else 1
        monthly_pmi   = (loan_amount * pmi_rate) / 12 if (equity_pct < 0.20 and pmi_rate > 0) else 0

        if remaining_loan > 0:
            interest_payment  = remaining_loan * monthly_rate
            principal_payment = min(mortgage_payment - interest_payment, remaining_loan)
            mortgage_actual   = interest_payment + principal_payment
        else:
            interest_payment  = 0.0
            principal_payment = 0.0
            mortgage_actual   = 0.0

        annual_interest_paid     += interest_payment
        annual_property_tax_paid += monthly_tax

        total_cost_buy_pretax = (mortgage_actual + monthly_tax + monthly_ins +
                                 hoa_monthly + monthly_maint + monthly_pmi + utilities_premium)

        monthly_tax_benefit = 0.0
        if m % 12 == 0:
            prop_tax_ded    = min(annual_property_tax_paid, SALT_CAP)
            total_itemized  = annual_interest_paid + prop_tax_ded
            if total_itemized > standard_deduction:
                annual_tax_benefit = (total_itemized - standard_deduction) * marginal_rate
            else:
                annual_tax_benefit = 0.0
            last_monthly_tax_benefit = annual_tax_benefit / 12
            annual_interest_paid     = 0.0
            annual_property_tax_paid = 0.0

        monthly_tax_benefit = last_monthly_tax_benefit
        total_cost_buy      = total_cost_buy_pretax - monthly_tax_benefit

        monthly_renter_ins = current_renters_ins_yr / 12
        total_cost_rent    = current_rent + monthly_renter_ins

        monthly_savings    = total_cost_buy - total_cost_rent
        renter_portfolio  *= (1 + invest_return / 12)
        renter_portfolio  += monthly_savings

        remaining_loan     = max(0, remaining_loan - principal_payment)
        cumulative_interest   += interest_payment
        cumulative_principal  += principal_payment
        current_home_value    *= (1 + home_appreciation / 12)

        if m % 12 == 0:
            current_rent           *= (1 + rent_inflation)
            current_insurance_yr   *= (1 + rent_inflation)
            current_renters_ins_yr *= (1 + rent_inflation)
            current_prop_tax_rate  *= (1 + property_tax_growth)

        buyer_equity = current_home_value - remaining_loan - (current_home_value * selling_costs_pct)

        series["months"].append(round(m / 12, 4))
        series["net_worth_buy"].append(round(buyer_equity, 2))
        series["net_worth_rent"].append(round(renter_portfolio, 2))
        series["home_value"].append(round(current_home_value, 2))
        series["mortgage_balance"].append(round(remaining_loan, 2))
        series["equity"].append(round(current_home_value - remaining_loan, 2))
        series["cumulative_interest"].append(round(cumulative_interest, 2))
        series["cumulative_principal"].append(round(cumulative_principal, 2))
        series["monthly_cost_buy"].append(round(total_cost_buy, 2))
        series["monthly_cost_rent"].append(round(total_cost_rent, 2))
        series["principal_payment"].append(round(principal_payment, 2))
        series["interest_payment"].append(round(interest_payment, 2))
        series["tax_savings_annual"].append(round(monthly_tax_benefit * 12, 2))
        series["pmi_annual"].append(round(monthly_pmi * 12, 2))

        if m % 12 == 0:
            annual_buyer_rows.append({
                "year":        m // 12,
                "pi":          round(mortgage_payment * 12, 0),
                "property_tax":round(monthly_tax * 12, 0),
                "insurance":   round(current_insurance_yr, 0),
                "hoa":         round(hoa_monthly * 12, 0),
                "maintenance": round(monthly_maint * 12, 0),
                "pmi":         round(monthly_pmi * 12, 0),
                "utilities":   round(utilities_premium * 12, 0),
                "tax_benefit": round(-monthly_tax_benefit * 12, 0),
                "total":       round(total_cost_buy * 12, 0),
            })
            annual_renter_rows.append({
                "year":      m // 12,
                "rent":      round(current_rent * 12, 0),
                "insurance": round(current_renters_ins_yr, 0),
                "total":     round(total_cost_rent * 12, 0),
            })

    # Breakeven
    nwb = np.array(series["net_worth_buy"])
    nwr = np.array(series["net_worth_rent"])
    crossover = np.argwhere(np.diff(np.sign(nwb - nwr))).flatten()
    breakeven_year = round(series["months"][crossover[0]], 1) if len(crossover) > 0 else None

    final_buy  = series["net_worth_buy"][-1]
    final_rent = series["net_worth_rent"][-1]

    # Year-end only series for charts (less data to send)
    def year_end(lst):
        return [lst[i * 12 - 1] for i in range(1, years + 1)]

    summary = {
        "mortgage_payment":     round(mortgage_payment, 2),
        "final_buy_networth":   round(final_buy, 0),
        "final_rent_networth":  round(final_rent, 0),
        "difference":           round(final_buy - final_rent, 0),
        "advantage":            "buying" if final_buy > final_rent else "renting",
        "breakeven_year":       breakeven_year,
        "total_interest":       round(series["cumulative_interest"][-1], 0),
        "total_principal":      round(series["cumulative_principal"][-1], 0),
        "final_home_value":     round(series["home_value"][-1], 0),
        "total_pmi":            round(sum(series["pmi_annual"]) / 12, 0),
        "total_tax_savings":    round(sum(series["tax_savings_annual"]) / 12, 0),
        "avg_annual_tax_benefit": round(sum(series["tax_savings_annual"]) / 12 / years, 0),
        "marginal_rate":        marginal_rate,
        "standard_deduction":   standard_deduction,
        "down_payment_amt":     round(down_payment_amt, 0),
        "closing_costs_amt":    round(home_price * closing_costs_pct, 0),
        "invest_return_pct":    invest_return * 100,
        "selling_costs_pct":    selling_costs_pct * 100,
        "years":                years,
    }

    charts = {
        "year_labels":          list(range(1, years + 1)),
        "net_worth_buy":        year_end(series["net_worth_buy"]),
        "net_worth_rent":       year_end(series["net_worth_rent"]),
        "home_value":           year_end(series["home_value"]),
        "mortgage_balance":     year_end(series["mortgage_balance"]),
        "equity":               year_end(series["equity"]),
        "cumulative_interest":  year_end(series["cumulative_interest"]),
        "cumulative_principal": year_end(series["cumulative_principal"]),
        "monthly_cost_buy":     year_end(series["monthly_cost_buy"]),
        "monthly_cost_rent":    year_end(series["monthly_cost_rent"]),
        "tax_savings":          year_end(series["tax_savings_annual"]),
        "pmi_payments":         year_end(series["pmi_annual"]),
    }

    return {
        "summary":       summary,
        "charts":        charts,
        "annual_buyer":  annual_buyer_rows,
        "annual_renter": annual_renter_rows,
    }
