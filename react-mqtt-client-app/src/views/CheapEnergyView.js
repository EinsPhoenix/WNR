import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import './CheapEnergyView.css';
import { useTranslation } from 'react-i18next';

const CheapEnergyView = ({ energyData, isLoading, error }) => {
    const { t } = useTranslation();

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
            <h2>{t('cheapEnergy.title')}</h2>
            {isLoading && <p className="status-text">{t('cheapEnergy.loading')}</p>}
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
                                    <stop offset="5%" stopColor="var(--pastel-green-color)" stopOpacity={0.9}/>
                                    <stop offset="95%" stopColor="var(--pastel-green-color)" stopOpacity={1}/>
                                </linearGradient>
                                <linearGradient id="gradient-red" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--pastel-red-color)" stopOpacity={0.9}/>
                                    <stop offset="95%" stopColor="var(--pastel-red-color)" stopOpacity={1}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.2)" />
                            <XAxis dataKey="timestamp" stroke="var(--pastel-white-color)" tickFormatter={formatXAxis} />
                            <YAxis stroke="var(--pastel-white-color)" />
                            <Tooltip
                                contentStyle={{ 
                                    backgroundColor: 'rgba(44, 62, 80, 0.8)', 
                                    border: '1px solid var(--primary-color)',
                                    borderRadius: '8px',
                                    color: 'var(--pastel-white-color)'
                                }}
                                labelFormatter={(label) => new Date(label).toLocaleString('de-DE')}
                                cursor={{ fill: 'rgba(255,255,255,0.1)' }}
                            />
                            <Legend wrapperStyle={{color: 'var(--pastel-white-color)'}}/>
                            <Bar dataKey="energy_cost" name={t('cheapEnergy.costLegend')} unit=" €/mWh" className="energy-bar">
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
                    <h3>{t('cheapEnergy.noDataTitle')}</h3>
                    <p>{t('cheapEnergy.noDataText')}</p>
                </div>
            )}
        </div>
    );
};

export default CheapEnergyView;