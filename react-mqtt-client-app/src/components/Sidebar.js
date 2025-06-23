import React from 'react';
import './Sidebar.css';
import { FiGrid, FiVideo, FiTerminal, FiPower, FiDollarSign } from 'react-icons/fi';

const Sidebar = ({ activeView, setActiveView, connectStatus }) => {
    const getStatusColor = () => {
        if (connectStatus === 'Connected') return '#2ecc71';
        if (connectStatus === 'Connecting' || connectStatus === 'Reconnecting') return '#f39c12';
        return '#e74c3c';
    };

    return (
        <nav className="sidebar">
            <div className="sidebar-header">
                <h3>WNR</h3>
            </div>
            <ul className="sidebar-nav">
                <li className={activeView === 'dashboard' ? 'active' : ''}>
                    <button onClick={() => setActiveView('dashboard')}>
                        <FiGrid />
                        <span>Dashboard</span>
                    </button>
                </li>
                <li className={activeView === 'cheap_energy' ? 'active' : ''}>
                    <button onClick={() => setActiveView('cheap_energy')}>
                        <FiDollarSign />
                        <span>Cheap Energy</span>
                    </button>
                </li>
                <li className={activeView === 'video' ? 'active' : ''}>
                    <button onClick={() => setActiveView('video')}>
                        <FiVideo />
                        <span>Video</span>
                    </button>
                </li>
                <li className={activeView === 'test' ? 'active' : ''}>
                    <button onClick={() => setActiveView('test')}>
                        <FiTerminal />
                        <span>MQTT Test</span>
                    </button>
                </li>
                
            </ul>
            <div className="sidebar-footer">
                <div className="connection-indicator">
                    <FiPower style={{ color: getStatusColor() }} />
                    <span>{connectStatus}</span>
                </div>
            </div>
        </nav>
    );
};

export default Sidebar;