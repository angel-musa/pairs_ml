import { XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface ChartPnLProps {
    data: any[];
}

export const ChartPnL: React.FC<ChartPnLProps> = ({ data }) => {
    return (
        <div className="bg-surface p-4 rounded-xl shadow-lg border border-white/5 h-80">
            <h3 className="text-lg font-semibold text-white mb-2">Equity Curve</h3>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="date" stroke="#666" tick={{ fill: '#666' }} minTickGap={30} />
                    <YAxis stroke="#666" tick={{ fill: '#666' }} domain={['auto', 'auto']} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#0b0b1a', borderColor: '#333', color: '#fff' }}
                        itemStyle={{ color: '#fff' }}
                    />
                    <Legend />
                    <Area type="monotone" dataKey="equity" name="Equity" stroke="#10b981" fillOpacity={1} fill="url(#colorEquity)" strokeWidth={2} />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};
