import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './DashboardView.css';
import { useTranslation } from 'react-i18next';

const DashboardView = ({ temperatureData, humidityData, energyConsumptionData, energyCostData }) => {
    const { t } = useTranslation();

    const renderChart = (title, data, dataKey, strokeColor, name, unit) => (
        <div className="chart-container">
            <h3>{title}</h3>
            {data.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                        <XAxis dataKey="time" stroke="#ccc" />
                        <YAxis stroke="#ccc" />
                        <Tooltip contentStyle={{ backgroundColor: '#333', border: '1px solid #555' }} />
                        <Legend />
                        <Line type="monotone" dataKey={dataKey} stroke={strokeColor} name={name} dot={false} strokeWidth={2} unit={unit} />
                    </LineChart>
                </ResponsiveContainer>
            ) : <p className="waiting-text">{t('dashboard.waitingForData')}</p>}
        </div>
    );

    return (
        <div className="dashboard-view">
            <h2>{t('dashboard.title')}</h2>
            <div className="charts-grid">
                {renderChart(t('dashboard.tempChartTitle'), temperatureData.slice(-10), "value", "var(--pastel-red-color)", t('dashboard.tempLegend'), "°C")}
                {renderChart(t('dashboard.humidityChartTitle'), humidityData.slice(-10), "value", "var(--pastel-green-color)", t('dashboard.humidityLegend'), "%")}
                {renderChart(t('dashboard.consumptionChartTitle'), energyConsumptionData.slice(-10), "value", "var(--pastel-yellow-color)", t('dashboard.consumptionLegend'), "W")}
                {renderChart(t('dashboard.costChartTitle'), energyCostData.slice(-10), "value", "var(--pastel-orange-color)", t('dashboard.costLegend'), "€/mWh")}
            </div>
        </div>
    );
};

export default DashboardView;