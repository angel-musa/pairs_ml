import { Play } from 'lucide-react';
import { Tooltip } from './Tooltip';

interface ControlsPanelProps {
    tickers: string[];
    selectedTickers: [string, string];
    params: {
        window: number;
        entry_z: number;
        exit_z: number;
    };
    onTickerChange: (index: 0 | 1, value: string) => void;
    onParamChange: (key: string, value: number) => void;
    onRun: () => void;
    loading: boolean;
}

export const ControlsPanel: React.FC<ControlsPanelProps> = ({
    tickers,
    selectedTickers,
    params,
    onTickerChange,
    onParamChange,
    onRun,
    loading
}) => {
    return (
        <div className="bg-surface p-6 rounded-xl shadow-lg border border-white/5">
            <h2 className="text-xl font-bold mb-4 text-white">Configuration</h2>

            <div className="space-y-4">
                <div>
                    <label className="block text-sm text-gray-400 mb-1">
                        Ticker Y (Dependent)
                        <Tooltip content="The dependent variable in the regression. This is the asset whose price we're trying to predict/explain using Ticker X. In mean-reversion trading, we look for deviations from the relationship Y = a + b*X." />
                    </label>
                    <select
                        className="w-full bg-background border border-white/10 rounded p-2 text-white focus:border-primary outline-none"
                        value={selectedTickers[1]}
                        onChange={(e) => onTickerChange(1, e.target.value)}
                    >
                        {tickers.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                </div>

                <div>
                    <label className="block text-sm text-gray-400 mb-1">
                        Ticker X (Independent)
                        <Tooltip content="The independent variable in the regression. This is the asset used to predict/explain Ticker Y's price movements. We regress Y on X to find their cointegration relationship." />
                    </label>
                    <select
                        className="w-full bg-background border border-white/10 rounded p-2 text-white focus:border-primary outline-none"
                        value={selectedTickers[0]}
                        onChange={(e) => onTickerChange(0, e.target.value)}
                    >
                        {tickers.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                </div>

                <div className="pt-4 border-t border-white/10">
                    <label className="block text-sm text-gray-400 mb-1">
                        Rolling Window
                        <Tooltip content="Number of days used to calculate the rolling mean and standard deviation for the z-score. A larger window (e.g., 60-120) captures longer-term mean-reversion; a smaller window (e.g., 20-40) is more responsive to recent changes." />
                    </label>
                    <input
                        type="number"
                        className="w-full bg-background border border-white/10 rounded p-2 text-white focus:border-primary outline-none"
                        value={params.window}
                        onChange={(e) => onParamChange('window', parseInt(e.target.value))}
                    />
                </div>

                <div>
                    <label className="block text-sm text-gray-400 mb-1">
                        Entry Z-Score
                        <Tooltip content="The z-score threshold to enter a position. When the spread z-score exceeds +Entry (overbought), we short the spread. When it falls below -Entry (oversold), we long the spread. Typical values: 1.5-3.0." />
                    </label>
                    <input
                        type="number"
                        step="0.1"
                        className="w-full bg-background border border-white/10 rounded p-2 text-white focus:border-primary outline-none"
                        value={params.entry_z}
                        onChange={(e) => onParamChange('entry_z', parseFloat(e.target.value))}
                    />
                </div>

                <div>
                    <label className="block text-sm text-gray-400 mb-1">
                        Exit Z-Score
                        <Tooltip content="The z-score threshold to exit a position. When the spread returns to within ±Exit of the mean, we close the trade and take profit. Typical values: 0.25-1.0. Lower values mean tighter profit-taking." />
                    </label>
                    <input
                        type="number"
                        step="0.1"
                        className="w-full bg-background border border-white/10 rounded p-2 text-white focus:border-primary outline-none"
                        value={params.exit_z}
                        onChange={(e) => onParamChange('exit_z', parseFloat(e.target.value))}
                    />
                </div>

                <button
                    onClick={onRun}
                    disabled={loading}
                    className="w-full mt-6 bg-primary hover:bg-secondary text-white font-bold py-3 px-4 rounded flex items-center justify-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <span className="animate-pulse">Running...</span>
                    ) : (
                        <>
                            <Play size={18} className="mr-2" /> Run Backtest
                        </>
                    )}
                </button>
            </div>
        </div>
    );
};
