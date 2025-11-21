import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

interface ChartSpreadZProps {
    data: any[];
    entryZ: number;
    exitZ: number;
}

export const ChartSpreadZ: React.FC<ChartSpreadZProps> = ({ data, entryZ, exitZ }) => {
    return (
        <div className="bg-surface p-4 rounded-xl shadow-lg border border-white/5 h-80">
            <h3 className="text-lg font-semibold text-white mb-2">Z-Score & Signals</h3>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="date" stroke="#666" tick={{ fill: '#666' }} minTickGap={30} />
                    <YAxis stroke="#666" tick={{ fill: '#666' }} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#0b0b1a', borderColor: '#333', color: '#fff' }}
                        itemStyle={{ color: '#fff' }}
                    />
                    <Legend />
                    <ReferenceLine y={entryZ} stroke="red" strokeDasharray="3 3" label="Entry +" />
                    <ReferenceLine y={-entryZ} stroke="green" strokeDasharray="3 3" label="Entry -" />
                    <ReferenceLine y={exitZ} stroke="gray" strokeDasharray="3 3" />
                    <ReferenceLine y={-exitZ} stroke="gray" strokeDasharray="3 3" />
                    <Line type="monotone" dataKey="zscore" name="Z-Score" stroke="#f59e0b" dot={false} strokeWidth={1.5} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
