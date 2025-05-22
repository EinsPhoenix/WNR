import React from 'react';

const MqttClientDisplay = ({ connectStatus }) => {
    return (
        <div style={{ padding: '10px', border: '1px solid lightgray', marginBottom: '20px' }}>
            <p><strong>Overall MQTT Connection Status:</strong> {connectStatus}</p>
        </div>
    );
};

export default MqttClientDisplay;
