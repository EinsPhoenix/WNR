import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './DashboardView.css';

const DashboardView = ({ temperatureData, humidityData, energyConsumptionData, energyCostData }) => {

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
            ) : <p className="waiting-text">Warte auf Daten...</p>}
        </div>
    );

    return (
        <div className="dashboard-view">
            <h2>Live Daten Dashboard</h2>
            <div className="charts-grid">
                {renderChart("Temperatur (°C)", temperatureData.slice(-10), "value", "#8884d8", "Temperatur", "°C")}
                {renderChart("Luftfeuchtigkeit (%)", humidityData.slice(-10), "value", "#82ca9d", "Feuchtigkeit", "%")}
                {renderChart("Energieverbrauch (W)", energyConsumptionData.slice(-10), "value", "#ffc658", "Verbrauch", "W")}
                {renderChart("Energiekosten (€/mWh)", energyCostData.slice(-10), "value", "#ff7300", "Kosten", "€/mWh")}
            </div>
        </div>
    );
};

export default DashboardView;