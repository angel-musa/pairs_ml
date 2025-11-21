import { Play } from 'lucide-react';

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
                    <label className="block text-sm text-gray-400 mb-1">Ticker Y (Dependent)</label>
                    <select
                        className="w-full bg-background border border-white/10 rounded p-2 text-white focus:border-primary outline-none"
                        value={selectedTickers[1]}
                        onChange={(e) => onTickerChange(1, e.target.value)}
                    >
                        {tickers.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                </div>

                <div>
                    <label className="block text-sm text-gray-400 mb-1">Ticker X (Independent)</label>
                    <select
                        className="w-full bg-background border border-white/10 rounded p-2 text-white focus:border-primary outline-none"
                        value={selectedTickers[0]}
                        onChange={(e) => onTickerChange(0, e.target.value)}
                    >
                        {tickers.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                </div>

                <div className="pt-4 border-t border-white/10">
                    <label className="block text-sm text-gray-400 mb-1">Rolling Window</label>
                    <input
                        type="number"
                        className="w-full bg-background border border-white/10 rounded p-2 text-white focus:border-primary outline-none"
                        value={params.window}
                        onChange={(e) => onParamChange('window', parseInt(e.target.value))}
                    />
                </div>

                <div>
                    <label className="block text-sm text-gray-400 mb-1">Entry Z-Score</label>
                    <input
                        type="number"
                        step="0.1"
                        className="w-full bg-background border border-white/10 rounded p-2 text-white focus:border-primary outline-none"
                        value={params.entry_z}
                        onChange={(e) => onParamChange('entry_z', parseFloat(e.target.value))}
                    />
                </div>

                <div>
                    <label className="block text-sm text-gray-400 mb-1">Exit Z-Score</label>
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
