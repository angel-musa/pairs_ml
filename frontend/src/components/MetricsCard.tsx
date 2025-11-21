import type { Metrics } from '../lib/api';
import { Tooltip } from './Tooltip';

interface MetricsCardProps {
    metrics: Metrics;
}

const MetricItem = ({ label, value, isPercent = false, color = "text-white", tooltip }: { label: string, value: number, isPercent?: boolean, color?: string, tooltip: string }) => (
    <div className="flex flex-col">
        <span className="text-xs text-gray-400 uppercase tracking-wider">
            {label}
            <Tooltip content={tooltip} />
        </span>
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
                    tooltip="Risk-adjusted return metric. Measures excess returns per unit of volatility. Higher is better. Values > 1 are good, > 2 are excellent. Formula: (Mean Return / Std Dev) × √252."
                />
                <MetricItem
                    label="Total Return"
                    value={metrics.total_return}
                    isPercent
                    color={metrics.total_return > 0 ? "text-green-400" : "text-red-400"}
                    tooltip="Cumulative percentage return over the entire backtest period. This shows how much your initial capital would have grown (or shrunk) if you followed this strategy."
                />
                <MetricItem
                    label="Max Drawdown"
                    value={metrics.max_drawdown}
                    isPercent
                    color="text-red-400"
                    tooltip="The largest peak-to-trough decline in equity. Measures worst-case scenario risk. A -10% drawdown means your portfolio fell 10% from its peak before recovering. Lower (less negative) is better."
                />
                <MetricItem
                    label="Hit Rate"
                    value={metrics.hit_rate}
                    isPercent
                    color="text-blue-400"
                    tooltip="Percentage of profitable trades out of all trades. A 70% hit rate means 7 out of 10 trades were winners. Note: A high hit rate with small wins and large losses can still be unprofitable."
                />
                <MetricItem
                    label="Turnover"
                    value={metrics.turnover}
                    tooltip="Total number of position changes during the backtest. Higher turnover means more frequent trading, which can increase transaction costs and slippage in live trading."
                />
                <MetricItem
                    label="Est. Capital"
                    value={metrics.estimated_capital}
                    tooltip="Estimated capital required to hold 1 unit of the spread position, calculated as: Price(Y) + Hedge_Ratio × Price(X). This represents the gross market value of the position."
                />
            </div>
        </div>
    );
};
