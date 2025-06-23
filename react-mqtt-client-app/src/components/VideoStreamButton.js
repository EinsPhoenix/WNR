import React, { useState } from 'react';
import VideoStreamModal from './VideoStreamModal';
import './VideoStreamModal.css';

const VideoStreamButton = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const openModal = () => {
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
    };

    return (
        <>
            <button className="button video-stream-button" onClick={openModal}>
                Video Stream
            </button>
            <VideoStreamModal isOpen={isModalOpen} onClose={closeModal} />
        </>
    );
};

export default VideoStreamButton;