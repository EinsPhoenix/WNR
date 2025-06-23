import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import './TestView.css';

const generateId = () => `react-client-${Math.random().toString(16).substr(2, 8)}`;

const TestView = ({ mqttClient }) => {
    const { t } = useTranslation();

    const requestTypesAndDataTemplates = useMemo(() => [
        { value: 'uuid', label: t('requestTypes.uuid'), template: JSON.stringify([{ "uuid": 123 }]) },
        { value: 'all', label: t('requestTypes.all'), template: JSON.stringify({}) },
        { value: 'color', label: t('requestTypes.color'), template: JSON.stringify("red") },
        { value: 'time_range', label: t('requestTypes.time_range'), template: JSON.stringify({ "start": "2025-05-22 00:00:00", "end": "2025-05-22 23:59:59" }) },
        { value: 'temperature_humidity', label: t('requestTypes.temperature_humidity'), template: JSON.stringify({ "temperature": 25.5, "humidity": 60.0 }) },
        { value: 'timestamp', label: t('requestTypes.timestamp'), template: JSON.stringify("YYYY-MM-DDTHH:MM:SSZ") },
        { value: 'id_energy_cost', label: t('requestTypes.id_energy_cost'), template: JSON.stringify(10.5) },
        { value: 'id_energy_consume', label: t('requestTypes.id_energy_consume'), template: JSON.stringify(100.2) },
        { value: 'newestids', label: t('requestTypes.newestids'), template: JSON.stringify({}) },
        { value: 'newestsensordata', label: t('requestTypes.newestsensordata'), template: JSON.stringify({}) },
        { value: 'newestenergydata', label: t('requestTypes.newestenergydata'), template: JSON.stringify({}) },
        { value: 'addrobotdata', label: t('requestTypes.addrobotdata'), template: JSON.stringify([{"id": 7, "uuid": "efg567hij007", "color": "green", "sensor_data": {"temperature": 19.5, "humidity": 57}, "timestamp": "2025-03-10 18:00:00", "energy_consume": 0.28, "energy_cost": 0.006}]) },
        { value: 'addenergydata', label: t('requestTypes.addenergydata'), template: JSON.stringify([{"timestamp": "2025-05-23T10:00:00Z", "energy_consume": 15.5, "energy_cost": 2.3}]) },
        { value: 'addsensordata', label: t('requestTypes.addsensordata'), template: JSON.stringify([{"timestamp": "2025-05-23T11:00:00Z", "temperature": 22.5, "humidity": 45.2}]) },
        { value: 'relation', label: t('requestTypes.relation'), template: JSON.stringify({}) },
        { value: 'page', label: t('requestTypes.page'), template: JSON.stringify(1) },
        { value: 'delete', label: t('requestTypes.delete'), template: JSON.stringify([1, 2, 3]) },
        { value: 'cheap_energy', label: t('requestTypes.cheap_energy'), template: JSON.stringify({}) },
    ], [t]);

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
        const topicParts = topic.split('/');
        if (!(topicParts.length >= 3 && topicParts[0] === 'rust' && topicParts[2] === requestingClientId)) {
            return;
        }

        setRawResponseStream(prev => `${prev}Topic: ${topic}\nMessage: ${messageString}\n----------\n`);
        let parsedMessage;
        try {
            parsedMessage = JSON.parse(messageString);
        } catch (e) {
            setError(t('testView.errorFailedToParseMqtt', { message: e.message }));
            setIsLoading(false);
            return;
        }

        if (parsedMessage.type === "summary") {
            const { request_id, total_pages, topic_base } = parsedMessage;
            setActivePagination({
                requestId: request_id,
                totalPages: total_pages,
                topicBase: topic_base,
                pages: new Array(total_pages).fill(null),
                receivedPageNumbers: new Set(),
            });
            setDisplayPageNumber(1);
            setCurrentDisplayData(null);
            setIsLoading(true);
            setError('');
        } else if (parsedMessage.type === "paginated") {
            const { request_id: msgRequestId, page, data } = parsedMessage;
            setActivePagination(prev => {
                if (prev && prev.requestId === msgRequestId) {
                    const newPages = [...prev.pages];
                    const newReceivedPageNumbers = new Set(prev.receivedPageNumbers);
                    if (!newReceivedPageNumbers.has(page)) {
                        newPages[page - 1] = data;
                        newReceivedPageNumbers.add(page);
                    }
                    return { ...prev, pages: newPages, receivedPageNumbers: newReceivedPageNumbers };
                }
                return prev;
            });
        } else {
            setCurrentDisplayData(parsedMessage);
            setIsLoading(false);
            setError(parsedMessage.status === 'error' ? `Error: ${parsedMessage.message}` : '');
        }
    }, [requestingClientId]);

    useEffect(() => {
        if (mqttClient && mqttClient.connected) {
            const subscriptionTopic = `rust/+/${requestingClientId}/#`;
            mqttClient.subscribe(subscriptionTopic, { qos: 1 });
            mqttClient.on('message', handleIncomingMessage);
            return () => {
                if (mqttClient.connected) mqttClient.unsubscribe(subscriptionTopic);
                mqttClient.off('message', handleIncomingMessage);
            };
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
        setJsonData(requestTypesAndDataTemplates.find(rt => rt.value === newRequestType)?.template || '{}');
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!mqttClient || !mqttClient.connected) {
            setError(t('testView.errorMqttNotConnected'));
            return;
        }
        let parsedJsonData;
        try {
            parsedJsonData = jsonData.trim() === '' ? null : JSON.parse(jsonData);
        } catch (parseError) {
            setError(t('testView.errorInvalidJson', { message: parseError.message }));
            return;
        }

        const requestPayloadBase = { client_id: requestingClientId, request: requestType };
        let finalPayload = (requestType === 'time_range' || requestType === 'temperature_humidity')
            ? { ...requestPayloadBase, ...parsedJsonData }
            : { ...requestPayloadBase, data: parsedJsonData };

        setSentRequest(finalPayload);
        setRawResponseStream('');
        setCurrentDisplayData(null);
        setError('');
        setIsLoading(true);
        setActivePagination(null);

        mqttClient.publish('rust/request', JSON.stringify(finalPayload), { qos: 1 }, (err) => {
            if (err) {
                setError(t('testView.errorFailedToPublish', { message: err.message }));
                setIsLoading(false);
            }
        });
    };

    const handlePageChange = (newPage) => {
        if (activePagination) {
            setDisplayPageNumber(Math.max(1, Math.min(newPage, activePagination.totalPages)));
        }
    };

    return (
        <div className="test-view">
            <h2>{t('testView.title')}</h2>
            <div className="request-form-container">
                <p><strong>{t('testView.clientId')}:</strong> <code>{requestingClientId}</code></p>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>{t('testView.requestType')}</label>
                        <select value={requestType} onChange={handleRequestTypeChange}>
                            {requestTypesAndDataTemplates.map(rt => (
                                <option key={rt.value} value={rt.value}>{rt.label}</option>
                            ))}
                        </select>
                    </div>
                    <div className="form-group">
                        <label>{t('testView.jsonData')}</label>
                        <textarea value={jsonData} onChange={(e) => setJsonData(e.target.value)} rows={6} />
                    </div>
                    <button type="submit" disabled={isLoading || !mqttClient || !mqttClient.connected}>
                        {isLoading ? t('testView.sending') : t('testView.sendRequest')}
                    </button>
                </form>
            </div>

            {error && <div className="response-box error-box"><strong>{t('testView.errorPrefix')}:</strong> {error}</div>}
            {isLoading && <div className="loading-indicator">{t('testView.loadingResponse')}</div>}

            {activePagination && (
                <div className="response-box pagination-box">
                    <h4>{t('testView.paginationProgress')}</h4>
                    <p>{t('testView.paginationStatus', { displayPageNumber, totalPages: activePagination.totalPages, receivedCount: activePagination.receivedPageNumbers.size })}</p>
                    <div>
                        <button onClick={() => handlePageChange(displayPageNumber - 1)} disabled={isLoading || displayPageNumber <= 1}>{t('testView.previous')}</button>
                        <button onClick={() => handlePageChange(displayPageNumber + 1)} disabled={isLoading || displayPageNumber >= activePagination.totalPages}>{t('testView.next')}</button>
                    </div>
                </div>
            )}

            <div className="results-grid">
                {sentRequest && (
                    <div className="response-box">
                        <h4>{t('testView.sentPayload')}</h4>
                        <pre>{JSON.stringify(sentRequest, null, 2)}</pre>
                    </div>
                )}
                {currentDisplayData && (
                    <div className="response-box">
                        <h4>{activePagination ? t('testView.responseDataForPage', { displayPageNumber }) : t('testView.responseData')}</h4>
                        <pre>{JSON.stringify(currentDisplayData, null, 2)}</pre>
                    </div>
                )}
            </div>

            {rawResponseStream && (
                <div className="response-box raw-log-box">
                    <h4>{t('testView.rawMqttLog')}</h4>
                    <pre>{rawResponseStream}</pre>
                </div>
            )}
        </div>
    );
};

export default TestView;