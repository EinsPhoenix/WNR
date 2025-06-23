import React, { useEffect, useRef, useState } from 'react';
import './VideoView.css';
import { FiMinimize2, FiMaximize2, FiXCircle, FiMaximize, FiPlay, FiPause, FiRewind } from 'react-icons/fi';
import { useTranslation } from 'react-i18next';

const VideoView = ({ 
    isMini, 
    onToggleMini, 
    onClose, 
    frameData, 
    connectionStatus, 
    isPaused, 
    onTogglePause, 
    onRewind,
    onSeek,
    cacheInfo,
    currentTimestamp,
    showPlaybackControls,
}) => {
    const { t } = useTranslation();
    const canvasRef = useRef(null);
    const containerRef = useRef(null);
    const [position, setPosition] = useState({ x: window.innerWidth - 340, y: window.innerHeight - 250 });
    const [isDragging, setIsDragging] = useState(false);
    const dragStartOffset = useRef({ x: 0, y: 0 });
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        if (frameData) {
            displayFrame(frameData);
        }
    }, [frameData]);

    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!isDragging) return;
            setPosition({
                x: e.clientX - dragStartOffset.current.x,
                y: e.clientY - dragStartOffset.current.y
            });
        };

        const handleMouseUp = () => {
            setIsDragging(false);
        };

        if (isDragging) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        }

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging]);

    useEffect(() => {
        const handleFullscreenChange = () => {
            setIsFullscreen(!!document.fullscreenElement);
        };
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        return () => {
            document.removeEventListener('fullscreenchange', handleFullscreenChange);
        };
    }, []);

    const displayFrame = (base64Data) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.onload = () => {
            if (canvas.width !== img.width) canvas.width = img.width;
            if (canvas.height !== img.height) canvas.height = img.height;
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        };
        img.src = `data:image/jpeg;base64,${base64Data}`;
    };

    const handleMouseDown = (e) => {
        if (!isMini) return;
        if (e.target.closest('button')) return;
        setIsDragging(true);
        const containerRect = containerRef.current.getBoundingClientRect();
        dragStartOffset.current = {
            x: e.clientX - containerRect.left,
            y: e.clientY - containerRect.top
        };
        e.preventDefault();
    };

    const handleFullscreen = () => {
        if (containerRef.current) {
            if (!document.fullscreenElement) {
                containerRef.current.requestFullscreen().catch(err => {
                    console.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
                });
            } else {
                document.exitFullscreen();
            }
        }
    };

    const containerClass = isMini ? "video-view-container mini-player" : "video-view-container";
    const miniPlayerStyle = isMini ? {
        left: `${position.x}px`,
        top: `${position.y}px`
    } : {};

    return (
        <div className={containerClass} ref={containerRef} style={miniPlayerStyle}>
            <div className="video-header" onMouseDown={handleMouseDown}>
                <div className="video-controls">
                    <button onClick={onTogglePause} title={isPaused ? t('video.resume') : t('video.pause')}>
                        {isPaused ? <FiPlay /> : <FiPause />}
                    </button>
                    {isPaused && (
                        <button onClick={onRewind} title={t('video.rewind')} disabled={!currentTimestamp}>
                            <FiRewind />
                        </button>
                    )}
                    <button onClick={handleFullscreen} title={t('video.fullscreen')}>
                        <FiMaximize />
                    </button>
                    <button onClick={onToggleMini} title={isMini ? t('video.maximize') : t('video.miniPlayer')}>
                        {isMini ? <FiMaximize2 /> : <FiMinimize2 />}
                    </button>
                    <button onClick={onClose} title={t('video.close')}>
                        <FiXCircle />
                    </button>
                </div>
            </div>
            <div className="video-content">
                <canvas ref={canvasRef} className="video-canvas" />
                {connectionStatus !== 'connected' && (
                    <div className="status-overlay">
                        <p>{t('video.status', { status: connectionStatus })}</p>
                        {connectionStatus === 'error' && <p>{t('video.connectionFailed')}</p>}
                        {connectionStatus === 'disconnected' && <p>{t('video.reconnecting')}</p>}
                    </div>
                )}
            </div>
            {showPlaybackControls && (
                <div className="timeline-container">
                    <input
                        type="range"
                        className="timeline-slider"
                        min={cacheInfo.oldest || 0}
                        max={cacheInfo.newest || 0}
                        value={currentTimestamp || 0}
                        onChange={(e) => onSeek(Number(e.target.value))}
                        disabled={!isPaused || !cacheInfo.oldest}
                        title={t('video.timeline')}
                    />
                </div>
            )}
        </div>
    );
};

export default VideoView;