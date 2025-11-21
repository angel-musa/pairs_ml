import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartPricesProps {
    data: any[];
    tickerY: string;
    tickerX: string;
}

export const ChartPrices: React.FC<ChartPricesProps> = ({ data, tickerY, tickerX }) => {
    return (
        <div className="bg-surface p-4 rounded-xl shadow-lg border border-white/5 h-80">
            <h3 className="text-lg font-semibold text-white mb-2">Price Series</h3>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="date" stroke="#666" tick={{ fill: '#666' }} minTickGap={30} />
                    <YAxis stroke="#666" tick={{ fill: '#666' }} domain={['auto', 'auto']} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#0b0b1a', borderColor: '#333', color: '#fff' }}
                        itemStyle={{ color: '#fff' }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="price_y" name={tickerY} stroke="#a855f7" dot={false} strokeWidth={2} />
                    <Line type="monotone" dataKey="price_x" name={tickerX} stroke="#3b82f6" dot={false} strokeWidth={2} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
