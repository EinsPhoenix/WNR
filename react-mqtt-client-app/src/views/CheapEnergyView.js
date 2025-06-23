import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import './CheapEnergyView.css';

const CheapEnergyView = ({ energyData, isLoading, error }) => {

    const formatXAxis = (tickItem) => {
        try {
            return new Date(tickItem).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return tickItem;
        }
    };

    const hasData = !isLoading && energyData && energyData.length > 0;
    const showNoDataMessage = !isLoading && (!energyData || energyData.length === 0);

    return (
        <div className="cheap-energy-view">
            <h2>Günstigste Energiezeiten</h2>
            {isLoading && <p className="status-text">Lade Daten...</p>}
            {error && <p className="status-text error-text">{error}</p>}
            
            {hasData && (
                <div className="chart-container-energy">
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart
                            data={energyData}
                            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                        >
                            <defs>
                                <linearGradient id="gradient-green" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#2ecc71" stopOpacity={0.9}/>
                                    <stop offset="95%" stopColor="#27ae60" stopOpacity={1}/>
                                </linearGradient>
                                <linearGradient id="gradient-red" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#e74c3c" stopOpacity={0.9}/>
                                    <stop offset="95%" stopColor="#c0392b" stopOpacity={1}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                            <XAxis dataKey="timestamp" stroke="#ccc" tickFormatter={formatXAxis} />
                            <YAxis stroke="#ccc" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#333', border: '1px solid #555' }}
                                labelFormatter={(label) => new Date(label).toLocaleString('de-DE')}
                                cursor={{ fill: 'transparent' }}
                            />
                            <Legend />
                            <Bar dataKey="energy_cost" name="Energiekosten" unit=" €/mWh" className="energy-bar">
                                {energyData.map((entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={entry.energy_cost < 0 ? 'url(#gradient-green)' : 'url(#gradient-red)'}
                                    />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {showNoDataMessage && (
                <div className="no-data-message">
                    <h3>HIER NIX ZU SEHEN</h3>
                    <p>ENERGY API NIX DA</p>
                </div>
            )}
        </div>
    );
};

export default CheapEnergyView;