import { useEffect, useState } from 'react';
import type { BacktestResponse } from './lib/api';
import { api } from './lib/api';
import { ControlsPanel } from './components/ControlsPanel';
import { MetricsCard } from './components/MetricsCard';
import { ChartPrices } from './components/ChartPrices';
import { ChartSpreadZ } from './components/ChartSpreadZ';
import { ChartPnL } from './components/ChartPnL';

function App() {
    const [tickers, setTickers] = useState<string[]>([]);
    const [selectedTickers, setSelectedTickers] = useState<[string, string]>(['', '']);
    const [params, setParams] = useState({
        window: 60,
        entry_z: 2.0,
        exit_z: 0.5
    });
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<BacktestResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        api.getPairs().then(t => {
            setTickers(t);
            if (t.length >= 2) {
                setSelectedTickers([t[0], t[1]]);
            }
        }).catch(err => {
            console.error("Failed to fetch pairs", err);
            setError("Failed to load tickers. Is backend running?");
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
            setError(err.response?.data?.detail || "Backtest failed");
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
            <header className="mb-8 flex justify-between items-center border-b border-white/10 pb-4">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                        Stat Arb Research Engine
                    </h1>
                    <p className="text-gray-400 mt-1">Pairs trading & mean-reversion analytics</p>
                </div>
                <div className="text-sm text-gray-500">
                    Dataset: prices.csv
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
                            {error}
                        </div>
                    )}
                </div>

                {/* Right Panel: Results */}
                <div className="lg:col-span-3">
                    {results ? (
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
                        <div className="h-96 flex items-center justify-center border border-white/5 rounded-xl bg-surface/50 text-gray-500">
                            Select parameters and run backtest to see results
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

export default App;
