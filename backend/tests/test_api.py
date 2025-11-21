"""
Tests for the Statistical Arbitrage Research Engine API

Run with: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test basic health and info endpoints"""
    
    def test_root_endpoint(self):
        """Test root health check"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
    
    def test_get_pairs(self):
        """Test fetching available ticker pairs"""
        response = client.get("/api/pairs")
        assert response.status_code == 200
        data = response.json()
        assert "tickers" in data
        assert isinstance(data["tickers"], list)
        assert len(data["tickers"]) > 0


class TestBacktestEndpoint:
    """Test backtest execution endpoint"""
    
    def test_successful_backtest(self):
        """Test a valid backtest request"""
        request_data = {
            "tickers": ["AAA", "BBB"],
            "window": 60,
            "entry_z": 2.0,
            "exit_z": 0.5,
            "notional": 1000.0
        }
        
        response = client.post("/api/run_backtest", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields exist
        assert "dates" in data
        assert "price_y" in data
        assert "price_x" in data
        assert "spread" in data
        assert "zscore" in data
        assert "position" in data
        assert "equity" in data
        assert "metrics" in data
        assert "hedge_ratio" in data
        
        # Check metrics structure
        metrics = data["metrics"]
        assert "sharpe" in metrics
        assert "total_return" in metrics
        assert "max_drawdown" in metrics
        assert "hit_rate" in metrics
        assert "turnover" in metrics
        assert "estimated_capital" in metrics
        
        # Check array lengths are consistent
        n = len(data["dates"])
        assert len(data["price_y"]) == n
        assert len(data["price_x"]) == n
        assert len(data["spread"]) == n
        assert len(data["zscore"]) == n
        assert len(data["position"]) == n
        assert len(data["equity"]) == n
        
        # Check metrics are reasonable types
        assert isinstance(metrics["sharpe"], (int, float))
        assert isinstance(metrics["total_return"], (int, float))
        assert isinstance(metrics["turnover"], (int, float))
    
    def test_invalid_ticker_count(self):
        """Test error when providing != 2 tickers"""
        request_data = {
            "tickers": ["AAA"],  # Only 1 ticker
            "window": 60,
            "entry_z": 2.0,
            "exit_z": 0.5
        }
        
        response = client.post("/api/run_backtest", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_same_tickers(self):
        """Test error when providing duplicate tickers"""
        request_data = {
            "tickers": ["AAA", "AAA"],  # Same ticker twice
            "window": 60,
            "entry_z": 2.0,
            "exit_z": 0.5
        }
        
        response = client.post("/api/run_backtest", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_window_too_small(self):
        """Test error for window < minimum"""
        request_data = {
            "tickers": ["AAA", "BBB"],
            "window": 10,  # Too small
            "entry_z": 2.0,
            "exit_z": 0.5
        }
        
        response = client.post("/api/run_backtest", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_exit_greater_than_entry(self):
        """Test error when exit_z >= entry_z"""
        request_data = {
            "tickers": ["AAA", "BBB"],
            "window": 60,
            "entry_z": 2.0,
            "exit_z": 2.5  # Exit > Entry (invalid)
        }
        
        response = client.post("/api/run_backtest", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_nonexistent_ticker(self):
        """Test error when ticker doesn't exist in data"""
        request_data = {
            "tickers": ["INVALID", "BBB"],
            "window": 60,
            "entry_z": 2.0,
            "exit_z": 0.5
        }
        
        response = client.post("/api/run_backtest", json=request_data)
        assert response.status_code == 400  # Bad request
        assert "not found" in response.json()["detail"].lower()
    
    def test_custom_parameters(self):
        """Test backtest with non-default parameters"""
        request_data = {
            "tickers": ["AAA", "BBB"],
            "window": 40,
            "entry_z": 2.5,
            "exit_z": 0.25,
            "notional": 5000.0
        }
        
        response = client.post("/api/run_backtest", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert isinstance(data["metrics"]["sharpe"], (int, float))


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_minimum_valid_window(self):
        """Test backtest with minimum valid window size"""
        request_data = {
            "tickers": ["AAA", "BBB"],
            "window": 20,  # Minimum allowed
            "entry_z": 2.0,
            "exit_z": 0.5
        }
        
        response = client.post("/api/run_backtest", json=request_data)
        assert response.status_code == 200
    
    def test_zero_exit_z(self):
        """Test with exit_z = 0 (exit at mean)"""
        request_data = {
            "tickers": ["AAA", "BBB"],
            "window": 60,
            "entry_z": 2.0,
            "exit_z": 0.0  # Exit exactly at mean
        }
        
        response = client.post("/api/run_backtest", json=request_data)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
