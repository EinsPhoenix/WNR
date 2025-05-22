import React, { useState, useEffect, useCallback } from 'react';

const generateId = () => `react-client-${Math.random().toString(16).substr(2, 8)}`;

// DAS IST WICHTIG TOBI
const requestTypesAndDataTemplates = [
    { value: 'uuid', label: 'UUID', template: JSON.stringify([{ "uuid": 123 }]) },
    { value: 'all', label: 'All Data', template: JSON.stringify({}) },
    { value: 'color', label: 'Nodes by Color', template: JSON.stringify("red") },
    {
        value: 'time_range', label: 'Nodes by Time Range', template: JSON.stringify({
            "start": "2025-05-22 00:00:00",
            "end": "2025-05-22 23:59:59"
        })
    },
    { value: 'temperature_humidity', label: 'Nodes by Temp/Humidity', template: JSON.stringify({ "temperature": 25.5, "humidity": 60.0 }) },
    { value: 'timestamp', label: 'Temp/Humidity at Timestamp', template: JSON.stringify("YYYY-MM-DDTHH:MM:SSZ") },
    { value: 'id_energy_cost', label: 'Nodes by Energy Cost (>=)', template: JSON.stringify(10.5) },
    { value: 'id_energy_consume', label: 'Nodes by Energy Consumption (>=)', template: JSON.stringify(100.2) },
    { value: 'newestids', label: 'Newest IDs', template: JSON.stringify({}) },
    { value: 'newestsensordata', label: 'Newest Sensor Data', template: JSON.stringify({}) },
    { value: 'newestenergydata', label: 'Newest Energy Data', template: JSON.stringify({}) },
    { value: 'addrobotdata', label: 'Add Robot Data', template: JSON.stringify([{ "id": "robot1", "type": "mobile", "attributes": { "color": "blue" }, "relations": [{ "to_id": "sensor1", "type": "monitors" }] }]) },
    { value: 'addenergydata', label: 'Add Energy Data', template: JSON.stringify([{ "node_id": "node123", "cost": 5.2, "consumption": 100, "timestamp": "YYYY-MM-DDTHH:MM:SSZ" }]) },
    { value: 'addsensordata', label: 'Add Sensor Data', template: JSON.stringify([{ "node_id": "sensorABC", "temperature": 22.5, "humidity": 55.0, "timestamp": "YYYY-MM-DDTHH:MM:SSZ" }]) },
    { value: 'relation', label: 'Export All with Relationships', template: JSON.stringify({}) },
    { value: 'page', label: 'Paginated IDs', template: JSON.stringify(1) },
    { value: 'delete', label: 'Delete Data by ID(s)', template: JSON.stringify([1, 2, 3]) },
    { value: 'topic', label: 'Topic (Not Implemented)', template: JSON.stringify({}) },
];

const RustRequestSender = ({ mqttClient }) => {

    const [requestingClientId] = useState(generateId());
    const [requestType, setRequestType] = useState(requestTypesAndDataTemplates[0].value);
    const [jsonData, setJsonData] = useState(requestTypesAndDataTemplates[0].template);

    const [sentRequest, setSentRequest] = useState(null);
    const [rawResponseStream, setRawResponseStream] = useState('');
    const [currentDisplayData, setCurrentDisplayData] = useState(null);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const [activePagination, setActivePagination] = useState(null);
    const [displayPageNumber, setDisplayPageNumber] = useState(1);

    const handleIncomingMessage = useCallback((topic, message) => {
        const messageString = message.toString();
        setRawResponseStream(prev => `${prev}Topic: ${topic}\nMessage: ${messageString}\n----------\n`);

        let parsedMessage;
        try {
            parsedMessage = JSON.parse(messageString);
        } catch (e) {
            console.error(`[${requestingClientId}] Failed to parse incoming MQTT message JSON:`, e, messageString);
            setError(`Failed to parse MQTT message: ${e.message}`);
            setIsLoading(false);
            return;
        }

        const topicParts = topic.split('/');
        if (!(topicParts.length >= 3 && topicParts[0] === 'rust' && topicParts[2] === requestingClientId)) {
            return;
        }

        if (parsedMessage.type === "summary") {
            const { request_id, total_pages, topic_base } = parsedMessage;
            console.log(`[${requestingClientId}] Received pagination summary for ${request_id}: ${total_pages} pages, base: ${topic_base}`);

            setActivePagination(prev => {
                let newPagesArray = new Array(total_pages).fill(null);
                let newReceivedPageNumbers = new Set();

                if (prev && prev.requestId === request_id) {
                    newReceivedPageNumbers = new Set(
                        Array.from(prev.receivedPageNumbers).filter(pNum => pNum <= total_pages)
                    );

                    if (prev.pages) {
                        prev.pages.forEach((pData, idx) => {
                            if (idx < total_pages && pData !== null && newReceivedPageNumbers.has(idx + 1)) {
                                newPagesArray[idx] = pData;
                            }
                        });
                    }
                    console.log(`[${requestingClientId}] Summary for active request ${request_id}. Updated. Preserved/validated ${newReceivedPageNumbers.size} pages.`);
                } else {
                    console.log(`[${requestingClientId}] Summary for new request ${request_id}. Initializing pagination.`);
                }

                return {
                    requestId: request_id,
                    totalPages: total_pages,
                    topicBase: topic_base,
                    pages: newPagesArray,
                    receivedPageNumbers: newReceivedPageNumbers,
                };
            });

            setDisplayPageNumber(1);
            setCurrentDisplayData(null);
            setIsLoading(true);
            setError('');

        } else if (parsedMessage.type === "paginated") {
            const { request_id: msgRequestId, page, data } = parsedMessage;

            setActivePagination(prev => {
                if (prev && prev.requestId === msgRequestId) {

                    if (prev.topicBase && !topic.startsWith(prev.topicBase + '/page/')) {
                        console.warn(`[${requestingClientId}] Paginated message for ${msgRequestId} (page ${page}) on topic ${topic} MISMATCHES active session topic base ${prev.topicBase}. Ignoring page.`);
                        return prev;
                    }

                    const pageIndex = page - 1;

                    const currentTotalPages = prev.totalPages;

                    if (typeof currentTotalPages === 'number' && (pageIndex < 0 || pageIndex >= currentTotalPages)) {
                        console.warn(`[${requestingClientId}] Received out-of-bounds page number ${page} for ${msgRequestId}. Total pages: ${currentTotalPages}. Ignoring.`);
                        return prev;
                    }

                    let newPages = prev.pages ? [...prev.pages] : [];
                    while (newPages.length <= pageIndex) {
                        newPages.push(null);
                    }

                    const newReceivedPageNumbers = new Set(prev.receivedPageNumbers);

                    if (!newReceivedPageNumbers.has(page)) {
                        newPages[pageIndex] = data;
                        newReceivedPageNumbers.add(page);
                        console.log(`[${requestingClientId}] Received page ${page}/${currentTotalPages || 'unknown'} for ${msgRequestId}. Total received: ${newReceivedPageNumbers.size}`);
                    } else {
                        console.warn(`[${requestingClientId}] Received duplicate page ${page} for ${msgRequestId}.`);
                    }
                    return { ...prev, pages: newPages, receivedPageNumbers: newReceivedPageNumbers };

                } else if (!prev || prev.requestId !== msgRequestId) {

                    console.warn(`[${requestingClientId}] Paginated message for new/different request ${msgRequestId} (page ${page}). Initializing preliminary session.`);
                    const pageIndex = page - 1;
                    const newPages = [];
                    if (pageIndex >= 0) {
                        while (newPages.length <= pageIndex) {
                            newPages.push(null);
                        }
                        newPages[pageIndex] = data;
                    }

                    return {
                        requestId: msgRequestId,
                        totalPages: undefined,
                        topicBase: undefined,
                        pages: newPages,
                        receivedPageNumbers: new Set([page]),
                    };
                }
                return prev;
            });

        } else {

            console.log(`[${requestingClientId}] Received direct/other response: `, parsedMessage);
            setCurrentDisplayData(parsedMessage);
            setIsLoading(false);

            if (!activePagination || (parsedMessage.request_id && activePagination.requestId !== parsedMessage.request_id)) {

            }
            setError(parsedMessage.status === 'error' ? `Error: ${parsedMessage.message}` : '');
        }
    }, [requestingClientId, mqttClient]);

    useEffect(() => {
        if (mqttClient && mqttClient.connected) {
            const subscriptionTopic = `rust/+/${requestingClientId}/#`;
            console.log(`[${requestingClientId}] Subscribing to ${subscriptionTopic}`);
            mqttClient.subscribe(subscriptionTopic, { qos: 1 }, (err) => {
                if (err) {
                    console.error(`[${requestingClientId}] Subscription error to ${subscriptionTopic}:`, err);
                    setError(`Failed to subscribe: ${err.message}`);
                } else {
                    console.log(`[${requestingClientId}] Successfully subscribed to ${subscriptionTopic}`);
                }
            });
            mqttClient.on('message', handleIncomingMessage);

            return () => {
                if (mqttClient.connected) {
                    console.log(`[${requestingClientId}] Unsubscribing from ${subscriptionTopic}`);
                    mqttClient.unsubscribe(subscriptionTopic, (err) => {
                        if (err) console.error(`[${requestingClientId}] Error unsubscribing from ${subscriptionTopic}:`, err);
                    });
                }
                mqttClient.off('message', handleIncomingMessage);
            };
        } else {
            console.log(`[${requestingClientId}] MQTT client not available or not connected. Skipping subscription.`);
        }
    }, [mqttClient, requestingClientId, handleIncomingMessage]);

    useEffect(() => {
        if (activePagination) {
            const pageIndex = displayPageNumber - 1;
            if (activePagination.pages[pageIndex]) {
                setCurrentDisplayData(activePagination.pages[pageIndex]);
                setIsLoading(false);
            } else {

                setCurrentDisplayData(null);
                setIsLoading(true);
            }
        }

    }, [displayPageNumber, activePagination]);

    const handleRequestTypeChange = (e) => {
        const newRequestType = e.target.value;
        setRequestType(newRequestType);
        const selectedTypeConfig = requestTypesAndDataTemplates.find(rt => rt.value === newRequestType);
        if (selectedTypeConfig) {
            setJsonData(selectedTypeConfig.template);
        } else {
            setJsonData(JSON.stringify({}));
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!mqttClient || !mqttClient.connected) {
            setError('MQTT client not connected.');
            setIsLoading(false);
            return;
        }

        let parsedJsonData;
        try {
            parsedJsonData = jsonData.trim() === '' ? null : JSON.parse(jsonData);
        } catch (parseError) {
            setError(`Invalid JSON in data field: ${parseError.message}`);
            setIsLoading(false);
            return;
        }

        const requestPayloadBase = {
            client_id: requestingClientId,
            request: requestType,
        };

        let finalPayload;
        if (requestType === 'time_range' || requestType === 'temperature_humidity') {
            if (typeof parsedJsonData === 'object' && parsedJsonData !== null) {
                finalPayload = { ...requestPayloadBase, ...parsedJsonData };
            } else {
                setError(`For ${requestType}, JSON Data must be an object with the required fields.`);
                setIsLoading(false);
                return;
            }
        } else {
            finalPayload = { ...requestPayloadBase, data: parsedJsonData };
        }

        const publishTopic = 'rust/request';
        console.log(`[${requestingClientId}] Publishing to ${publishTopic}:`, finalPayload);

        setSentRequest(finalPayload);
        setRawResponseStream('');
        setCurrentDisplayData(null);
        setError('');
        setIsLoading(true);
        setActivePagination(null);

        mqttClient.publish(publishTopic, JSON.stringify(finalPayload), { qos: 1 }, (err) => {
            if (err) {
                console.error(`[${requestingClientId}] Publish error:`, err);
                setError(`Failed to publish request: ${err.message}`);
                setIsLoading(false);
            } else {
                console.log(`[${requestingClientId}] Request published successfully to ${publishTopic}.`);
            }
        });
    };

    const handlePreviousPage = () => {
        if (activePagination) {
            setDisplayPageNumber(prev => Math.max(1, prev - 1));
        }
    };

    const handleNextPage = () => {
        if (activePagination) {
            setDisplayPageNumber(prev => Math.min(activePagination.totalPages, prev + 1));
        }
    };

    return (
        <div style={{ border: '1px solid #ccc', padding: '15px', margin: '10px' }}>
            <h3>MQTT Request Sender</h3>
            <p><strong>My Requesting Client ID:</strong> <code>{requestingClientId}</code></p>
            <form onSubmit={handleSubmit}>
                <div style={{ marginBottom: '10px' }}>
                    <label htmlFor={`requestType-${requestingClientId}`} style={{ marginRight: '5px' }}>Request Type: </label>
                    <select
                        id={`requestType-${requestingClientId}`}
                        value={requestType}
                        onChange={handleRequestTypeChange}
                        style={{ padding: '5px' }}
                    >
                        {requestTypesAndDataTemplates.map(rt => (
                            <option key={rt.value} value={rt.value}>{rt.label}</option>
                        ))}
                    </select>
                </div>
                <div style={{ marginBottom: '10px' }}>
                    <label htmlFor={`jsonData-${requestingClientId}`} style={{ display: 'block', marginBottom: '5px' }}>
                        JSON Data
                        {(requestType === 'time_range' || requestType === 'temperature_humidity')
                            ? " (Top-level parameters for payload)"
                            : " (Content for 'data' field)"}:
                    </label>
                    <textarea
                        id={`jsonData-${requestingClientId}`}
                        value={jsonData}
                        onChange={(e) => setJsonData(e.target.value)}
                        rows={5}
                        style={{ width: '90%', padding: '5px', minHeight: '60px' }}
                    />
                </div>
                <button
                    type="submit"
                    disabled={isLoading || !mqttClient || !mqttClient.connected}
                    style={{ padding: '8px 15px', cursor: 'pointer' }}
                >
                    {isLoading ? 'Sending...' : 'Send Request'}
                </button>
            </form>

            {error && <div style={{ color: 'red', marginTop: '10px', whiteSpace: 'pre-wrap' }}><strong>Error:</strong> {error}</div>}

            {isLoading && <div style={{ marginTop: '10px' }}>Loading response...</div>}

            {activePagination && (
                <div style={{ marginTop: '10px', padding: '10px', border: '1px dashed blue' }}>
                    <h4>Pagination Progress:</h4>
                    <p>Request ID: {activePagination.requestId}</p>
                    <p>
                        Page {displayPageNumber} of {activePagination.totalPages}.
                        (Received {activePagination.receivedPageNumbers.size} / {activePagination.totalPages} total pages for this request)
                    </p>
                    <div>
                        <button onClick={handlePreviousPage} disabled={isLoading || displayPageNumber <= 1}>
                            Previous
                        </button>
                        <button
                            onClick={handleNextPage}
                            disabled={isLoading || displayPageNumber >= activePagination.totalPages}
                            style={{ marginLeft: '5px' }}
                        >
                            Next
                        </button>
                    </div>
                </div>
            )}

            {sentRequest && (
                <div style={{ marginTop: '15px' }}>
                    <h4>Sent Payload to <code>rust/request</code>:</h4>
                    <pre style={{ background: '#f0f0f0', padding: '10px', borderRadius: '4px', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                        {JSON.stringify(sentRequest, null, 2)}
                    </pre>
                </div>
            )}

            {currentDisplayData && (
                <div style={{ marginTop: '15px' }}>
                    <h4>
                        {activePagination ? `Data for Page ${displayPageNumber}:` : 'Response Data:'}
                    </h4>
                    <pre style={{ background: '#e6ffe6', padding: '10px', borderRadius: '4px', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                        {JSON.stringify(currentDisplayData, null, 2)}
                    </pre>
                </div>
            )}

            {rawResponseStream && (
                <div style={{ marginTop: '15px' }}>
                    <h4>Raw MQTT Messages Log (for this client ID):</h4>
                    <pre style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid #eee', padding: '10px', background: '#fafafa', fontSize: '0.9em', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                        {rawResponseStream}
                    </pre>
                </div>
            )}
        </div>
    );
};

export default RustRequestSender;