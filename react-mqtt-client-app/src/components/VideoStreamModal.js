import React, { useState, useEffect, useRef } from 'react';

const VideoStreamModal = ({ isOpen, onClose }) => {
    const canvasRef = useRef(null);
    const wsRef = useRef(null);
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const [isLoading, setIsLoading] = useState(false);
    const frameBufferRef = useRef(new Map());

    useEffect(() => {
        if (isOpen) {
            connectToStream();
        } else {
            disconnectFromStream();
        }

        return () => {
            disconnectFromStream();
        };
    }, [isOpen]);

    const connectToStream = () => {
        setIsLoading(true);
        setConnectionStatus('connecting');

        try {
            const ws = new WebSocket('ws://localhost:1337');
            wsRef.current = ws;

            ws.onopen = function () {
                setConnectionStatus('connected');
                setIsLoading(false);
                console.log('Connected to WebRTC server');
            };

            ws.onmessage = function (event) {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === 'video_frame') {
                        displayFrame(data.frame_data);
                    } else if (data.type === 'video_frame_start') {
                        frameBufferRef.current.set(data.frame_index, {
                            chunks: new Array(data.total_chunks),
                            received: 0,
                            total_chunks: data.total_chunks
                        });
                    } else if (data.type === 'video_frame_chunk') {
                        const frameData = frameBufferRef.current.get(data.frame_index);
                        if (frameData) {
                            frameData.chunks[data.chunk_index] = data.chunk_data;
                            frameData.received++;

                            if (frameData.received === frameData.total_chunks) {
                                const completeFrame = frameData.chunks.join('');
                                displayFrame(completeFrame);
                                frameBufferRef.current.delete(data.frame_index);
                            }
                        }
                    }
                } catch (e) {
                    console.error('Error parsing message:', e);
                }
            };

            ws.onclose = function () {
                setConnectionStatus('disconnected');
                setIsLoading(false);
                console.log('Disconnected from WebRTC server');
            };

            ws.onerror = function (error) {
                setConnectionStatus('error');
                setIsLoading(false);
                console.error('WebSocket error:', error);
            };

        } catch (error) {
            setConnectionStatus('error');
            setIsLoading(false);
            console.error('Connection error:', error);
        }
    };

    const disconnectFromStream = () => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        frameBufferRef.current.clear();
        setConnectionStatus('disconnected');
        setIsLoading(false);
    };

    const displayFrame = (base64Data) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.onload = function () {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        };
        img.src = 'data:image/jpeg;base64,' + base64Data;
    };

    const handleClose = () => {
        disconnectFromStream();
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={handleClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Video Stream</h2>
                    <button className="close-button" onClick={handleClose}>×</button>
                </div>

                <div className="modal-body">
                    <div className="connection-status">
                        Status: {connectionStatus}
                    </div>

                    {isLoading && (
                        <div className="loading-spinner">
                            <div className="spinner"></div>
                            <p>Connecting to video stream...</p>
                        </div>
                    )}

                    <canvas
                        ref={canvasRef}
                        width="640"
                        height="480"
                        className="video-canvas"
                        style={{
                            display: connectionStatus === 'connected' ? 'block' : 'none',
                            border: '1px solid #ccc'
                        }}
                    />

                    {connectionStatus === 'error' && (
                        <div className="error-message">
                            Failed to connect to video stream. Please try again.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default VideoStreamModal;