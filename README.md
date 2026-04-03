# HomeDecide

**Should you buy or rent? Run the numbers.**

A free buy vs rent calculator that models the true financial picture — equity growth, opportunity cost, break-even year, and net worth projection over any time horizon.

Live at [homedecide.aspenitservices.com](https://homedecide.aspenitservices.com)

---

## What It Does

Most buy vs rent calculators show you a single number. HomeDecide shows you the full simulation:

- **Break-even year** — the exact year buying becomes cheaper than renting
- **Net worth projection** — side-by-side wealth trajectory for buyer vs renter
- **True cost of ownership** — mortgage, PMI, property tax, maintenance, insurance
- **Opportunity cost** — what the down payment earns if invested instead
- **5 interactive charts** — net worth, home equity vs mortgage, monthly costs, cumulative spend, tax & PMI
- **Year-by-year tables** — full amortization breakdown for both scenarios
- **CSV / TXT export** — download your results

---

## Inputs

| Category | Parameters |
|---|---|
| Home | Purchase price, down payment %, mortgage rate, loan term |
| Costs | Property tax, HOA, maintenance, home insurance, PMI |
| Rent | Monthly rent, annual rent inflation, renters insurance |
| Market | Home appreciation rate, investment return rate |
| Scenario | Time horizon (years) |

---

## Tech Stack

- **Backend:** Python 3.12, Flask, numpy-financial
- **Frontend:** Vanilla JS, Chart.js
- **Infrastructure:** Docker, Google Cloud Run

---

## Local Development

```bash
# Clone
git clone git@github.com:sainathyai/HomeInvestmentCalculator.git
cd HomeInvestmentCalculator

# Install dependencies
pip install -r requirements.txt

# Run
python run.py
# → http://localhost:5000
```

---

## Deployment

Deployed to Google Cloud Run via source deploy:

```bash
gcloud run deploy homedecide \
  --source . \
  --region us-central1 \
  --project pdfmerger-pro-app
```

---

## Project Structure

```
app/
  static/
    css/style.css     # Design system, dark/light theme
    js/app.js         # Chart.js rendering, form logic, export
  templates/
    index.html        # Single-page app
Dockerfile
requirements.txt
run.py
```

---

Part of the [Veritas Intel](https://veritasintelai.com) tools ecosystem.
