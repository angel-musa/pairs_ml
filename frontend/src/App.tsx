import { useEffect, useState } from 'react';
import type { BacktestResponse } from './lib/api';
import { api } from './lib/api';
import { ControlsPanel } from './components/ControlsPanel';
import { MetricsCard } from './components/MetricsCard';
import { ChartPrices } from './components/ChartPrices';
import { ChartSpreadZ } from './components/ChartSpreadZ';
import { ChartPnL } from './components/ChartPnL';
import { Loader2 } from 'lucide-react';

// LocalStorage keys
const STORAGE_KEYS = {
    TICKERS: 'statarb_selected_tickers',
    PARAMS: 'statarb_params'
};

// Default parameters
const DEFAULT_PARAMS = {
    window: 60,
    entry_z: 2.0,
    exit_z: 0.5
};

function App() {
    const [tickers, setTickers] = useState<string[]>([]);
    const [selectedTickers, setSelectedTickers] = useState<[string, string]>(() => {
        // Load from localStorage or use defaults
        const saved = localStorage.getItem(STORAGE_KEYS.TICKERS);
        return saved ? JSON.parse(saved) : ['', ''];
    });

    const [params, setParams] = useState(() => {
        // Load from localStorage or use defaults
        const saved = localStorage.getItem(STORAGE_KEYS.PARAMS);
        return saved ? JSON.parse(saved) : DEFAULT_PARAMS;
    });

    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<BacktestResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Persist selectedTickers to localStorage
    useEffect(() => {
        if (selectedTickers[0] && selectedTickers[1]) {
            localStorage.setItem(STORAGE_KEYS.TICKERS, JSON.stringify(selectedTickers));
        }
    }, [selectedTickers]);

    // Persist params to localStorage
    useEffect(() => {
        localStorage.setItem(STORAGE_KEYS.PARAMS, JSON.stringify(params));
    }, [params]);

    // Load available tickers on mount
    useEffect(() => {
        api.getPairs().then(t => {
            setTickers(t);
            // If no saved tickers, use first two available
            if (!selectedTickers[0] && !selectedTickers[1] && t.length >= 2) {
                setSelectedTickers([t[0], t[1]]);
            }
        }).catch(err => {
            console.error("Failed to fetch pairs", err);
            setError("Failed to load tickers. Is the backend running at http://localhost:8000?");
        });
    }, []);

    const handleRun = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await api.runBacktest({
                tickers: selectedTickers,
                ...params
            });
            setResults(res);
        } catch (err: any) {
            console.error(err);
            const errorMsg = err.response?.data?.detail || err.message || "Backtest failed";
            setError(errorMsg);
            // Don't clear previous results on error - keep them visible
        } finally {
            setLoading(false);
        }
    };

    // Prepare chart data
    const chartData = results ? results.dates.map((date, i) => ({
        date,
        price_y: results.price_y[i],
        price_x: results.price_x[i],
        spread: results.spread[i],
        zscore: results.zscore[i],
        equity: results.equity[i],
        position: results.position[i]
    })) : [];

    return (
        <div className="min-h-screen bg-background text-white p-6 font-sans">
            <header className="mb-8 border-b border-white/10 pb-4">
                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                            Stat Arb Research Engine
                        </h1>
                        <p className="text-gray-400 mt-1">Pairs trading & mean-reversion analytics</p>
                    </div>
                    <div className="text-sm text-gray-500 text-right">
                        <div className="font-semibold text-gray-400">Data Source</div>
                        <div className="mt-1">
                            Current: <span className="text-primary">data/prices.csv</span>
                        </div>
                    </div>
                </div>
            </header>

            <main className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* Left Panel: Controls */}
                <div className="lg:col-span-1">
                    <ControlsPanel
                        tickers={tickers}
                        selectedTickers={selectedTickers}
                        params={params}
                        onTickerChange={(idx, val) => {
                            const newTickers = [...selectedTickers] as [string, string];
                            newTickers[idx] = val;
                            setSelectedTickers(newTickers);
                        }}
                        onParamChange={(key, val) => setParams(p => ({ ...p, [key]: val }))}
                        onRun={handleRun}
                        loading={loading}
                    />

                    {error && (
                        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm">
                            <div className="font-semibold mb-1">Error</div>
                            {error}
                        </div>
                    )}
                </div>

                {/* Right Panel: Results */}
                <div className="lg:col-span-3">
                    {loading ? (
                        <div className="h-96 flex flex-col items-center justify-center border border-white/5 rounded-xl bg-surface/50">
                            <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
                            <p className="text-gray-400 text-lg font-medium">Running backtest...</p>
                            <p className="text-gray-500 text-sm mt-2">
                                Testing cointegration and generating signals
                            </p>
                        </div>
                    ) : results ? (
                        <>
                            <MetricsCard metrics={results.metrics} />

                            <div className="space-y-6">
                                <ChartPrices
                                    data={chartData}
                                    tickerY={selectedTickers[1]}
                                    tickerX={selectedTickers[0]}
                                />
                                <ChartSpreadZ
                                    data={chartData}
                                    entryZ={params.entry_z}
                                    exitZ={params.exit_z}
                                />
                                <ChartPnL data={chartData} />
                            </div>
                        </>
                    ) : (
                        <div className="h-96 flex flex-col items-center justify-center border border-white/5 rounded-xl bg-surface/50 text-gray-500">
                            <div className="text-center">
                                <p className="text-lg font-medium mb-2">No Results Yet</p>
                                <p className="text-sm">
                                    Select tickers and parameters on the left, then click "Run Backtest"
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

export default App;
