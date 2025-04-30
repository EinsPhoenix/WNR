// acquire_global_id
pub const ACQUIRE_GLOBAL_ID: &str = r#"
    USE fabric.dbshard1
    MERGE (global_counter:GlobalIdCounter {name: 'global_counter'})
    ON CREATE SET global_counter.current = 0
    SET global_counter.current = global_counter.current + 1
    RETURN global_counter.current AS new_id
"#;

// get_all_data - Shard 1
pub const GET_ALL_DATA_SHARD1: &str = r#"
    USE fabric.dbshard1
    MATCH (id_node:Id)
    OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
    OPTIONAL MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
    RETURN id_node.value AS id, uuid_node.value AS uuid, color_node.value AS color
"#;

// get_all_data - Shard 2
pub const GET_ALL_DATA_SHARD2: &str = r#"
    USE fabric.dbshard2
    MATCH (id_node:Id)-[:HAS_SENSOR_DATA]->(sensor_data_node:SensorData)
    OPTIONAL MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
    OPTIONAL MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
    RETURN id_node.value AS id, {
        temperature: temp_node.value,
        humidity: hum_node.value
    } AS sensor_reading
"#;

// get_all_data - Shard 3
pub const GET_ALL_DATA_SHARD3: &str = r#"
    USE fabric.dbshard3
    MATCH (id_node:Id)
    OPTIONAL MATCH (id_node)-[:RECORDED_AT]->(time_node:Timestamp)
    OPTIONAL MATCH (id_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsume)
    OPTIONAL MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)
    RETURN id_node.value AS id, {
        timestamp: time_node.value,
        energy_consume: econsume_node.value,
        energy_cost: ecost_node.value
    } AS energy_reading
    ORDER BY id_node.value, time_node.value
"#;

// get_data_by_id - Shard 1
pub const GET_DATA_BY_ID_SHARD1: &str = r#"
    USE fabric.dbshard1
    MATCH (id_node:Id {value: $target_id})
    OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
    OPTIONAL MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
    RETURN id_node.value AS id, uuid_node.value AS uuid, color_node.value AS color
    LIMIT 1
"#;

// get_data_by_id - Shard 2
pub const GET_DATA_BY_ID_SHARD2: &str = r#"
    USE fabric.dbshard2
    MATCH (id_node_s2:Id {value: $target_id})
    OPTIONAL MATCH (id_node_s2)-[:HAS_SENSOR_DATA]->(sensor_data_node:SensorData)
    OPTIONAL MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
    OPTIONAL MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
    WITH sensor_data_node, temp_node, hum_node
    WHERE sensor_data_node IS NOT NULL
    RETURN {
        temperature: temp_node.value,
        humidity: hum_node.value
    } AS sensor_reading
"#;

// get_data_by_id - Shard 3
pub const GET_DATA_BY_ID_SHARD3: &str = r#"
    USE fabric.dbshard3
    MATCH (id_node_s3:Id {value: $target_id})
    OPTIONAL MATCH (id_node_s3)-[:RECORDED_AT]->(time_node:Timestamp)
    OPTIONAL MATCH (id_node_s3)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsume)
    OPTIONAL MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)
    WITH time_node, econsume_node, ecost_node
    WHERE time_node IS NOT NULL OR econsume_node IS NOT NULL
    RETURN {
        timestamp: time_node.value,
        energy_consume: econsume_node.value,
        energy_cost: ecost_node.value
    } AS energy_reading
    ORDER BY time_node.value
"#;

// execute_shard1_query (create_new_nodes)
pub const CREATE_NODES_SHARD1: &str = r#"
    USE fabric.dbshard1
    CREATE (id_node:Id {value: toInteger($new_id)})
    CREATE (uuid_node:Uuid {value: $uuid})
    MERGE (color_node:Color {value: $color})
    MERGE (id_node)-[:HAS_UUID]->(uuid_node)
    MERGE (id_node)-[:HAS_COLOR]->(color_node)
    RETURN id_node.value AS processed_id
"#;

// execute_shard2_query (create_new_nodes)
pub const CREATE_NODES_SHARD2: &str = r#"
    USE fabric.dbshard2
    MERGE (id_node:Id {value: toInteger($new_id)})
    CREATE (sensor_data_node:SensorData {timestamp: datetime()})
    MERGE (temp_node:Temperature {value: toFloat($temperature)})
    MERGE (hum_node:Humidity {value: toFloat($humidity)})
    MERGE (id_node)-[:HAS_SENSOR_DATA]->(sensor_data_node)
    MERGE (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node)
    MERGE (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node)
    RETURN id_node.value AS processed_id
"#;

// execute_shard3_query (create_new_nodes)
pub const CREATE_NODES_SHARD3: &str = r#"
    USE fabric.dbshard3
    MERGE (id_node:Id {value: toInteger($new_id)})
    CREATE (time_node:Timestamp {value: $timestamp})
    CREATE (econsume_node:EnergyConsume {value: toFloat($energy_consume)})
    CREATE (ecost_node:EnergyCost {value: toFloat($energy_cost)})
    MERGE (id_node)-[:RECORDED_AT]->(time_node)
    MERGE (id_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node)
    MERGE (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node)
    RETURN id_node.value AS processed_id
"#;

pub const CREATE_SENSOR_NODES_SHARD2: &str = r#"
    USE fabric.dbshard2
    CREATE (sensor_data_node:SensorData {value: $timestamp})
    MERGE (temp_node:Temperature {value: toFloat($temperature)})
    MERGE (hum_node:Humidity {value: toFloat($humidity)})
    MERGE (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node)
    MERGE (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node)
    RETURN sensor_data_node.value AS timestamp
"#;

pub const CREATE_ENERGY_NODES_SHARD3: &str = r#"
    USE fabric.dbshard3
    CREATE (time_node:Timestamp {value: $timestamp})
    CREATE (econsume_node:EnergyConsume {value: toFloat($energy_consume)})
    CREATE (ecost_node:EnergyCost {value: toFloat($energy_cost)})
    RETURN time_node.value AS timestamp
"#;