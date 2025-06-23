import React, { useEffect, useRef, useState } from 'react';
import './VideoView.css';
import { FiMinimize2, FiMaximize2, FiXCircle, FiMaximize } from 'react-icons/fi';

const VideoView = ({ isMini, onToggleMini, onClose, frameData, connectionStatus }) => {
    const canvasRef = useRef(null);
    const containerRef = useRef(null);
    const [position, setPosition] = useState({ x: window.innerWidth - 340, y: window.innerHeight - 250 });
    const [isDragging, setIsDragging] = useState(false);
    const dragStartOffset = useRef({ x: 0, y: 0 });

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
                    <button onClick={handleFullscreen} title="Vollbild">
                        <FiMaximize />
                    </button>
                    <button onClick={onToggleMini} title={isMini ? "Maximieren" : "Mini-Player"}>
                        {isMini ? <FiMaximize2 /> : <FiMinimize2 />}
                    </button>
                    <button onClick={onClose} title="Schließen">
                        <FiXCircle />
                    </button>
                </div>
            </div>
            <div className="video-content">
                <canvas ref={canvasRef} className="video-canvas" />
                {connectionStatus !== 'connected' && (
                    <div className="status-overlay">
                        <p>Status: {connectionStatus}</p>
                        {connectionStatus === 'error' && <p>Verbindung fehlgeschlagen.</p>}
                        {connectionStatus === 'disconnected' && <p>Verbindung wird wiederhergestellt...</p>}
                    </div>
                )}
            </div>
        </div>
    );
};

export default VideoView;