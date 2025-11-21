# Backend Testing Guide

The backend includes a comprehensive test suite using pytest.

## Running Tests

```bash
cd backend

#Set PYTHONPATH (Windows PowerShell)
$env:PYTHONPATH="C:\projects\pairs;C:\projects\pairs\backend"
pytest tests/ -v

# Set PYTHONPATH (Windows CMD)
set PYTHONPATH=C:\projects\pairs;C:\projects\pairs\backend
pytest tests/ -v

# Or run from project root
cd ..
pytest backend/tests/ -v
```

## Test Coverage

The test suite includes **13 test cases** covering:

### Health Endpoints (2 tests)
- Root endpoint `/` returns healthy status
- `/api/pairs` returns list of available tickers

### Backtest Endpoint (6 tests)
- Successful backtest with valid parameters
- Invalid ticker count (not 2)
- Same ticker used twice
- Window size too small (< 20)
- Exit z-score >= entry z-score
- Nonexistent ticker in data
- Custom parameters

### Edge Cases (2 tests)
- Minimum valid window (20)
- Zero exit z-score

## Expected Output

All tests should pass:
```
=================== test session starts ====================
collected 13 items

tests/test_api.py::TestHealthEndpoints::test_root_endpoint PASSED
tests/test_api.py::TestHealthEndpoints::test_get_pairs PASSED
tests/test_api.py::TestBacktestEndpoint::test_successful_backtest PASSED
...
=================== 13 passed in 2.34s =====================
```

## Troubleshooting

If you see import errors:
1. Ensure you're in the `backend/` directory
2. Set PYTHONPATH to include project root
3. Verify pandas, numpy, statsmodels are installed
4. Check that `data/prices.csv` exists in project root
