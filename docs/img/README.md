# Screenshots for Documentation

## Dashboard
Place a screenshot of the main dashboard here showing:
- Controls panel with parameter inputs
- Performance metrics cards
- Interactive charts (prices, spread/z-score, equity curve)

Filename: `dashboard.png`

## Notebook Analysis
Place a screenshot of a Jupyter notebook showing:
- Cointegration test results
- Signal generation logic
- Backtest performance summary

Filename: `notebook_backtest.png`

## How to Capture

### Dashboard Screenshot
1. Start the backend: `cd backend && uvicorn main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173
4. Run a backtest with AAA/BBB
5. Capture full-page screenshot
6. Save as `dashboard.png` in this directory

### Notebook Screenshot
1. Open `notebooks/03_backtest.ipynb` in Jupyter
2. Run all cells
3. Capture relevant output cells showing:
   - Cointegration statistics
   - Backtest summary table
   - Equity curve plot
4. Save as `notebook_backtest.png` in this directory
