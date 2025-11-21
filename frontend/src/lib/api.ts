import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export interface BacktestRequest {
    tickers: [string, string];
    window: number;
    entry_z: number;
    exit_z: number;
    notional?: number;
}

export interface Metrics {
    sharpe: number;
    max_drawdown: number;
    hit_rate: number;
    total_return: number;
    turnover: number;
    estimated_capital: number;
}

export interface BacktestResponse {
    dates: string[];
    price_y: number[];
    price_x: number[];
    spread: number[];
    zscore: number[];
    position: number[];
    pnl: number[];
    equity: number[];
    metrics: Metrics;
    hedge_ratio: number;
    intercept: number;
}

export const api = {
    getPairs: async () => {
        const res = await axios.get<{ tickers: string[] }>(`${API_URL}/pairs`);
        return res.data.tickers;
    },
    runBacktest: async (req: BacktestRequest) => {
        const res = await axios.post<BacktestResponse>(`${API_URL}/run_backtest`, req);
        return res.data;
    }
};
