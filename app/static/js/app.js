'use strict';

// ── Theme ─────────────────────────────────────────────────────────
const html = document.documentElement;
const savedTheme = localStorage.getItem('hd-theme') ||
  (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
html.setAttribute('data-theme', savedTheme);

document.getElementById('themeToggle').addEventListener('click', () => {
  const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  localStorage.setItem('hd-theme', next);
  if (lastResult) renderCharts(lastResult); // re-render with new colors
});

// ── Slider labels ─────────────────────────────────────────────────
const sliderMap = {
  down_payment_pct:    ['lbl_down',  v => v + '%'],
  mortgage_rate:       ['lbl_rate',  v => parseFloat(v).toFixed(1) + '%'],
  pmi_rate:            ['lbl_pmi',   v => parseFloat(v).toFixed(1) + '%'],
  property_tax_rate:   ['lbl_ptax',  v => parseFloat(v).toFixed(1) + '%'],
  property_tax_growth: ['lbl_ptaxg', v => parseFloat(v).toFixed(1) + '%'],
  maintenance_pct:     ['lbl_maint', v => parseFloat(v).toFixed(1) + '%'],
  rent_inflation:      ['lbl_rinf',  v => parseFloat(v).toFixed(1) + '%'],
  home_appreciation:   ['lbl_appr',  v => parseFloat(v).toFixed(1) + '%'],
  invest_return:       ['lbl_inv',   v => parseFloat(v).toFixed(1) + '%'],
  closing_costs_pct:   ['lbl_close', v => parseFloat(v).toFixed(1) + '%'],
  selling_costs_pct:   ['lbl_sell',  v => parseFloat(v).toFixed(1) + '%'],
  years:               ['lbl_years', v => v + ' yrs'],
};

document.querySelectorAll('input[type="range"]').forEach(input => {
  const cfg = sliderMap[input.name];
  if (!cfg) return;
  const [id, fmt] = cfg;
  const label = document.getElementById(id);
  if (label) {
    input.addEventListener('input', () => { label.textContent = fmt(input.value); });
  }
});

// PMI field visibility
const downSlider = document.querySelector('[name="down_payment_pct"]');
const pmiField   = document.getElementById('pmiField');
function togglePMI() { pmiField.style.display = parseFloat(downSlider.value) < 20 ? '' : 'none'; }
downSlider.addEventListener('input', togglePMI);
togglePMI();

// ── Helpers ───────────────────────────────────────────────────────
const fmt  = n => '$' + Math.round(n).toLocaleString();
const fmtK = n => {
  const abs = Math.abs(n);
  if (abs >= 1e6) return (n < 0 ? '-$' : '$') + (abs / 1e6).toFixed(1) + 'M';
  if (abs >= 1e3) return (n < 0 ? '-$' : '$') + (abs / 1e3).toFixed(0) + 'K';
  return fmt(n);
};

function getChartColors() {
  const dark = html.getAttribute('data-theme') === 'dark';
  return {
    grid:   dark ? 'rgba(255,255,255,.07)' : 'rgba(0,0,0,.06)',
    text:   dark ? '#9CA3AF' : '#6B7280',
    buy:    '#2E86AB',
    rent:   '#06A77D',
    danger: '#D62828',
    accent: '#4F46E5',
    orange: '#F77F00',
  };
}

// ── Chart instances ───────────────────────────────────────────────
let charts = {};
function destroyCharts() { Object.values(charts).forEach(c => c.destroy()); charts = {}; }

function makeChart(id, config) {
  const ctx = document.getElementById(id).getContext('2d');
  charts[id] = new Chart(ctx, config);
}

function lineOptions(title, yFmt) {
  const c = getChartColors();
  return {
    responsive: true,
    plugins: {
      legend: { labels: { color: c.text, font: { size: 11 } } },
      title:  { display: true, text: title, color: c.text, font: { size: 12, weight: '600' } },
      tooltip: { callbacks: { label: ctx => ' ' + fmtK(ctx.parsed.y) } },
    },
    scales: {
      x: { ticks: { color: c.text, font: { size: 10 } }, grid: { color: c.grid } },
      y: {
        ticks: { color: c.text, font: { size: 10 }, callback: yFmt || (v => fmtK(v)) },
        grid: { color: c.grid },
      },
    },
  };
}

function renderCharts(r) {
  destroyCharts();
  const c  = getChartColors();
  const yr = r.charts.year_labels;

  // Net Worth
  makeChart('chartNetWorth', {
    type: 'line',
    data: {
      labels: yr,
      datasets: [
        { label: 'Buy Net Worth', data: r.charts.net_worth_buy, borderColor: c.buy, backgroundColor: c.buy + '22', fill: true, tension: .3, pointRadius: 0, borderWidth: 2 },
        { label: 'Rent Net Worth', data: r.charts.net_worth_rent, borderColor: c.rent, backgroundColor: c.rent + '22', fill: true, tension: .3, pointRadius: 0, borderWidth: 2, borderDash: [5,3] },
      ],
    },
    options: {
      ...lineOptions('Net Worth Over Time'),
      plugins: {
        ...lineOptions('Net Worth Over Time').plugins,
        annotation: r.summary.breakeven_year ? {
          annotations: { line1: {
            type: 'line', xMin: r.summary.breakeven_year, xMax: r.summary.breakeven_year,
            borderColor: c.danger, borderWidth: 1, borderDash: [4, 3],
            label: { content: `Breakeven yr ${r.summary.breakeven_year}`, display: true, color: c.danger, font: { size: 10 } },
          }},
        } : {},
      },
    },
  });

  // Home Value vs Mortgage
  makeChart('chartHomeVsMortgage', {
    type: 'line',
    data: {
      labels: yr,
      datasets: [
        { label: 'Home Value',      data: r.charts.home_value,       borderColor: c.rent, fill: false, tension: .3, pointRadius: 0, borderWidth: 2 },
        { label: 'Mortgage Balance',data: r.charts.mortgage_balance, borderColor: c.danger, fill: false, tension: .3, pointRadius: 0, borderWidth: 2 },
        { label: 'Equity',          data: r.charts.equity,           borderColor: c.buy, backgroundColor: c.buy + '18', fill: true, tension: .3, pointRadius: 0, borderWidth: 1.5 },
      ],
    },
    options: lineOptions('Home Value vs Mortgage Balance'),
  });

  // Monthly Costs
  makeChart('chartMonthlyCosts', {
    type: 'line',
    data: {
      labels: yr,
      datasets: [
        { label: 'Buyer Total Cost', data: r.charts.monthly_cost_buy,  borderColor: c.buy,  fill: false, tension: .3, pointRadius: 0, borderWidth: 2 },
        { label: 'Renter Total Cost',data: r.charts.monthly_cost_rent, borderColor: c.rent, fill: false, tension: .3, pointRadius: 0, borderWidth: 2, borderDash: [5,3] },
      ],
    },
    options: lineOptions('Monthly Total Costs', v => '$' + Math.round(v).toLocaleString()),
  });

  // Cumulative P&I
  makeChart('chartCumulative', {
    type: 'line',
    data: {
      labels: yr,
      datasets: [
        { label: 'Cumulative Interest',  data: r.charts.cumulative_interest,  borderColor: c.danger, fill: false, tension: .3, pointRadius: 0, borderWidth: 2 },
        { label: 'Cumulative Principal', data: r.charts.cumulative_principal, borderColor: c.rent,   fill: false, tension: .3, pointRadius: 0, borderWidth: 2 },
      ],
    },
    options: lineOptions('Cumulative Principal & Interest Paid'),
  });

  // Tax & PMI
  makeChart('chartTaxPMI', {
    type: 'bar',
    data: {
      labels: yr,
      datasets: [
        { label: 'Annual Tax Savings', data: r.charts.tax_savings,   backgroundColor: c.rent + 'BB' },
        { label: 'Annual PMI Paid',    data: r.charts.pmi_payments,  backgroundColor: c.danger + 'BB' },
      ],
    },
    options: { ...lineOptions('Annual Tax Savings & PMI'), scales: { ...lineOptions('Annual Tax Savings & PMI').scales, x: { ...lineOptions('Annual Tax Savings & PMI').scales.x, stacked: false } } },
  });
}

// ── Tables ────────────────────────────────────────────────────────
function buildTable(tableId, rows, cols) {
  const tbl = document.getElementById(tableId);
  tbl.innerHTML = '';
  const head = tbl.insertRow();
  cols.forEach(([label]) => {
    const th = document.createElement('th');
    th.textContent = label;
    head.appendChild(th);
  });
  rows.forEach(row => {
    const tr = tbl.insertRow();
    cols.forEach(([, key, money]) => {
      const td = tr.insertCell();
      td.textContent = money ? fmt(row[key]) : row[key];
    });
  });
}

// ── Render Results ────────────────────────────────────────────────
let lastResult = null;

function renderResults(r) {
  lastResult = r;
  const s = r.summary;

  // Banner
  const banner = document.getElementById('advantageBanner');
  if (s.advantage === 'buying') {
    banner.className = 'summary-banner buy';
    banner.innerHTML = `🏠 <strong>Buying</strong> builds ${fmtK(Math.abs(s.difference))} more wealth over ${s.years} years`;
  } else {
    banner.className = 'summary-banner rent';
    banner.innerHTML = `💼 <strong>Renting & investing</strong> builds ${fmtK(Math.abs(s.difference))} more wealth over ${s.years} years`;
  }
  if (s.breakeven_year) {
    banner.innerHTML += ` &nbsp;·&nbsp; Breakeven at year ${s.breakeven_year}`;
  }

  // Metrics row 1
  document.getElementById('mMonthlyPI').textContent    = fmt(s.mortgage_payment);
  document.getElementById('lblBuyNW').textContent      = `Buy Net Worth (Yr ${s.years})`;
  document.getElementById('mBuyNW').textContent        = fmtK(s.final_buy_networth);
  document.getElementById('lblRentNW').textContent     = `Rent Net Worth (Yr ${s.years})`;
  document.getElementById('mRentNW').textContent       = fmtK(s.final_rent_networth);
  const adv = document.getElementById('mAdvantage');
  adv.textContent  = s.advantage === 'buying' ? '🏠 Buying' : '💼 Renting';
  adv.style.color  = s.advantage === 'buying' ? 'var(--buy-color)' : 'var(--rent-color)';

  // Metrics row 2
  document.getElementById('mTotalInterest').textContent = fmtK(s.total_interest);
  document.getElementById('mFinalHome').textContent     = fmtK(s.final_home_value);
  document.getElementById('mTaxSavings').textContent    = fmtK(s.total_tax_savings);
  document.getElementById('mPMI').textContent           = fmtK(s.total_pmi);

  // Charts
  renderCharts(r);

  // Tables
  buildTable('buyerTable', r.annual_buyer, [
    ['Year','year',false],['P&I','pi',true],['Prop Tax','property_tax',true],
    ['Insurance','insurance',true],['HOA','hoa',true],['Maintenance','maintenance',true],
    ['PMI','pmi',true],['Tax Benefit','tax_benefit',true],['Total','total',true],
  ]);
  buildTable('renterTable', r.annual_renter, [
    ['Year','year',false],['Rent','rent',true],['Insurance','insurance',true],['Total','total',true],
  ]);

  // Show results
  document.getElementById('emptyState').classList.add('hidden');
  document.getElementById('resultsContent').classList.remove('hidden');

  // Store for CSV/TXT export
  window._hdResult = r;
}

// ── Form submit ───────────────────────────────────────────────────
document.getElementById('calcForm').addEventListener('submit', async e => {
  e.preventDefault();
  const fd   = new FormData(e.target);
  const body = Object.fromEntries(fd.entries());

  document.getElementById('emptyState').classList.add('hidden');
  document.getElementById('resultsContent').classList.add('hidden');
  document.getElementById('loadingState').classList.remove('hidden');

  try {
    const res  = await fetch('/api/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Calculation failed');
    renderResults(data);
  } catch (err) {
    alert('Error: ' + err.message);
    document.getElementById('emptyState').classList.remove('hidden');
  } finally {
    document.getElementById('loadingState').classList.add('hidden');
  }
});

// Auto-calculate on load
document.getElementById('calcForm').dispatchEvent(new Event('submit'));

// ── Export CSV ────────────────────────────────────────────────────
document.getElementById('btnExportCSV').addEventListener('click', () => {
  const r = window._hdResult; if (!r) return;
  const rows = r.annual_buyer.map((b, i) => {
    const rn = r.annual_renter[i];
    return [b.year,b.pi,b.property_tax,b.insurance,b.hoa,b.maintenance,b.pmi,b.tax_benefit,b.total,
            rn.rent,rn.insurance,rn.total,
            r.charts.net_worth_buy[i],r.charts.net_worth_rent[i],
            r.charts.home_value[i],r.charts.mortgage_balance[i]].join(',');
  });
  const header = 'Year,P&I,PropertyTax,Insurance,HOA,Maintenance,PMI,TaxBenefit,BuyerTotal,Rent,RenterInsurance,RenterTotal,BuyNetWorth,RentNetWorth,HomeValue,MortgageBalance';
  const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv' });
  const url  = URL.createObjectURL(blob);
  const a    = Object.assign(document.createElement('a'), { href: url, download: 'homedecide-analysis.csv' });
  a.click(); URL.revokeObjectURL(url);
});

// ── Export TXT ────────────────────────────────────────────────────
document.getElementById('btnExportTXT').addEventListener('click', () => {
  const r = window._hdResult; if (!r) return;
  const s = r.summary;
  const lines = [
    'HOMEDECIDE — BUY VS RENT ANALYSIS REPORT',
    '='.repeat(50),
    `Generated: ${new Date().toLocaleString()}`,
    '',
    'RESULTS SUMMARY',
    '='.repeat(50),
    `Monthly P&I:           ${fmt(s.mortgage_payment)}`,
    `Buy Net Worth (Yr ${s.years}):  ${fmtK(s.final_buy_networth)}`,
    `Rent Net Worth (Yr ${s.years}): ${fmtK(s.final_rent_networth)}`,
    `Advantage:             ${s.advantage.toUpperCase()}  (${fmtK(Math.abs(s.difference))})`,
    `Breakeven:             ${s.breakeven_year ? 'Year ' + s.breakeven_year : 'No breakeven in timeframe'}`,
    '',
    'BUYER TOTALS',
    '-'.repeat(30),
    `Total Interest Paid:   ${fmtK(s.total_interest)}`,
    `Final Home Value:      ${fmtK(s.final_home_value)}`,
    `Total PMI Paid:        ${fmtK(s.total_pmi)}`,
    `Total Tax Savings:     ${fmtK(s.total_tax_savings)}`,
    `Avg Annual Tax Benefit:${fmtK(s.avg_annual_tax_benefit)}`,
  ];
  const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
  const url  = URL.createObjectURL(blob);
  const a    = Object.assign(document.createElement('a'), { href: url, download: 'homedecide-report.txt' });
  a.click(); URL.revokeObjectURL(url);
});
