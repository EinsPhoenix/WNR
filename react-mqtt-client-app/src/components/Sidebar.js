import React from 'react';
import './Sidebar.css';
import { FiGrid, FiVideo, FiTerminal, FiPower, FiDollarSign } from 'react-icons/fi';
import wnrLogo from '../static/wnrcutealpha.png';
import { useTranslation } from 'react-i18next';

const Sidebar = ({ activeView, setActiveView, connectStatus }) => {
    const { t, i18n } = useTranslation();

    const changeLanguage = (lng) => {
        i18n.changeLanguage(lng);
    };

    const getStatusColor = () => {
        if (connectStatus === 'Connected') return 'var(--pastel-green-color)';
        if (connectStatus === 'Connecting' || connectStatus === 'Reconnecting') return 'var(--pastel-orange-color)';
        return 'var(--pastel-red-color)';
    };

    return (
        <nav className="sidebar">
            <div className="sidebar-header">
                <img src={wnrLogo} alt="WNR Logo" className="sidebar-logo" />
            </div>
            <ul className="sidebar-nav">
                <li className={activeView === 'dashboard' ? 'active' : ''}>
                    <button onClick={() => setActiveView('dashboard')}><FiGrid /> {t('sidebar.dashboard')}</button>
                </li>
                <li className={activeView === 'cheap_energy' ? 'active' : ''}>
                    <button onClick={() => setActiveView('cheap_energy')}><FiDollarSign /> {t('sidebar.cheapEnergy')}</button>
                </li>
                <li className={activeView === 'video' ? 'active' : ''}>
                    <button onClick={() => setActiveView('video')}><FiVideo /> {t('sidebar.video')}</button>
                </li>

                <li className={activeView === 'test' ? 'active' : ''}>
                    <button onClick={() => setActiveView('test')}><FiTerminal /> {t('sidebar.test')}</button>
                </li>
                
            </ul>
            <div className="sidebar-footer">
                <div className="language-switcher">
                    <button onClick={() => changeLanguage('de')} disabled={i18n.language === 'de'}>DE</button>
                    <button onClick={() => changeLanguage('en')} disabled={i18n.language === 'en'}>EN</button>
                </div>
                <div className="connection-indicator">
                    <FiPower style={{ color: getStatusColor() }} />
                    <span>{connectStatus}</span>
                </div>
            </div>
        </nav>
    );
};

export default Sidebar;