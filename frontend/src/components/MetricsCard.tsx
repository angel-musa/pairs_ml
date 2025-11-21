import type { Metrics } from '../lib/api';

interface MetricsCardProps {
    metrics: Metrics;
}

const MetricItem = ({ label, value, isPercent = false, color = "text-white" }: { label: string, value: number, isPercent?: boolean, color?: string }) => (
    <div className="flex flex-col">
        <span className="text-xs text-gray-400 uppercase tracking-wider">{label}</span>
        <span className={`text-2xl font-bold ${color}`}>
            {isPercent ? `${(value * 100).toFixed(2)}%` : value.toFixed(2)}
        </span>
    </div>
);

export const MetricsCard: React.FC<MetricsCardProps> = ({ metrics }) => {
    return (
        <div className="bg-surface p-6 rounded-xl shadow-lg border border-white/5 mb-6">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
                <MetricItem
                    label="Sharpe Ratio"
                    value={metrics.sharpe}
                    color={metrics.sharpe > 0 ? "text-green-400" : "text-red-400"}
                />
                <MetricItem
                    label="Total Return"
                    value={metrics.total_return}
                    isPercent
                    color={metrics.total_return > 0 ? "text-green-400" : "text-red-400"}
                />
                <MetricItem
                    label="Max Drawdown"
                    value={metrics.max_drawdown}
                    isPercent
                    color="text-red-400"
                />
                <MetricItem
                    label="Hit Rate"
                    value={metrics.hit_rate}
                    isPercent
                    color="text-blue-400"
                />
                <MetricItem
                    label="Turnover"
                    value={metrics.turnover}
                />
                <MetricItem
                    label="Est. Capital"
                    value={metrics.estimated_capital}
                />
            </div>
        </div>
    );
};
