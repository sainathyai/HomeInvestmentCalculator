# 🏠 Buy vs Rent Calculator

A comprehensive financial calculator that helps you make an informed decision between buying and renting a home.

## Features

### Comprehensive Cost Analysis
- **Buyer Costs**: Mortgage P&I, property taxes, insurance, HOA, maintenance, PMI
- **Renter Costs**: Monthly rent, renters insurance
- **Tax Benefits**: Mortgage interest deduction, property tax deduction (SALT cap applied)
- **Investment Growth**: Models how saved money grows in the market

### Advanced Factors Included
✅ PMI calculations (automatically drops at 20% equity)
✅ Tax deductions with 2024 tax brackets (configurable filing status)
✅ Property tax growth over time
✅ Optional utility cost differences (if buying larger property)
✅ Home appreciation and rent inflation
✅ Closing costs and selling costs
✅ Investment returns on saved capital

### Interactive Features
- Real-time parameter adjustments
- Visual net worth comparison charts
- Breakeven point calculation
- Annual cost breakdown tables
- Equity buildup tracking
- Tax savings visualization

## Installation

### Local Development

1. Clone or download this repository

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the app:
```bash
streamlit run app.py
```

5. Open your browser to `http://localhost:8501`

## Deployment Options

### Option 1: Streamlit Community Cloud (Recommended - Free!)

1. Push this code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app" and select your repository
5. Set main file path to `app.py`
6. Click "Deploy"!

Your app will be live at `https://[your-app-name].streamlit.app`

### Option 2: Railway

1. Create account at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select this repository
4. Railway will auto-detect Streamlit and deploy

### Option 3: Heroku

1. Create a `Procfile`:
```
web: sh setup.sh && streamlit run app.py
```

2. Create `setup.sh`:
```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

3. Deploy to Heroku:
```bash
heroku create your-app-name
git push heroku main
```

### Option 4: Docker

1. Create a `Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

2. Build and run:
```bash
docker build -t home-calculator .
docker run -p 8501:8501 home-calculator
```

## Usage

1. Adjust parameters in the left sidebar:
   - Home price and down payment
   - Mortgage rate and loan term
   - Property taxes, insurance, HOA
   - Rental costs
   - Investment assumptions
   - Tax filing status and income

2. View the results:
   - Main chart shows net worth over time
   - Key metrics displayed at top
   - Breakeven point indicated
   - Detailed tabs for cost breakdown and equity tracking

3. Experiment with different scenarios to find what works for your situation!

## Tax Calculation Details

The calculator uses 2024 tax brackets and includes:
- Standard deductions by filing status
- Marginal tax rate calculation
- Mortgage interest deduction
- Property tax deduction (SALT $10K cap)
- Tax benefit only applied when itemizing beats standard deduction

## Assumptions & Limitations

**What's Modeled:**
- All major ownership and rental costs
- Tax benefits from homeownership
- Investment growth of saved capital
- PMI until 20% equity
- Property value appreciation
- Rent and insurance inflation

**What's NOT Modeled:**
- Refinancing opportunities
- Capital gains tax exclusion ($250K/$500K)
- Market volatility (assumes steady returns)
- Special assessments or major repairs
- Moving costs
- Changes in income over time

## Contributing

Feel free to fork and modify for your needs. Some ideas for enhancements:
- Add refinancing scenarios
- Model capital gains tax on home sale
- Include moving costs
- Add Monte Carlo simulation for market volatility
- Model income changes over time

## License

MIT License - feel free to use and modify!
