pub const GET_ALL_DATA_SHARD1: &str = r#"
    USE fabric.dbshard1
    MATCH (id_node:Id)
    OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
    OPTIONAL MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
    RETURN id_node.value AS id, uuid_node.value AS uuid, color_node.value AS color
"#;


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


pub const GET_ALL_DATA_SHARD3: &str = r#"
    USE fabric.dbshard3
    MATCH (id_node:Id)
    OPTIONAL MATCH (id_node)-[:HAS_TIMESTAMP]->(time_node:Timestamp)
    OPTIONAL MATCH (id_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsumption)
    OPTIONAL MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)
    RETURN id_node.value AS id, {
        timestamp: time_node.value,
        energy_consume: econsume_node.value,
        energy_cost: ecost_node.value
    } AS energy_reading
    ORDER BY id_node.value, time_node.value
"#;


pub const GET_DATA_BY_ID_SHARD1: &str = r#"
    USE fabric.dbshard1
    MATCH (id_node:Id {value: $target_id})
    OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
    OPTIONAL MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
    RETURN id_node.value AS id, uuid_node.value AS uuid, color_node.value AS color
    LIMIT 1
"#;


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


pub const GET_DATA_BY_ID_SHARD3: &str = r#"
    USE fabric.dbshard3
    MATCH (id_node_s3:Id {value: $target_id})
    OPTIONAL MATCH (id_node_s3)-[:HAS_TIMESTAMP]->(time_node:Timestamp)
    OPTIONAL MATCH (id_node_s3)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsumption)
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


pub const CREATE_NODES_SHARD1: &str = r#"
    USE fabric.dbshard1
    UNWIND $batch AS row
    CREATE (id_node:Id {value: row[0]})
    CREATE (uuid_node:Uuid {value: row[1]})
    MERGE (color_node:Color {value: row[2]})
    MERGE (id_node)-[:HAS_UUID]->(uuid_node)
    MERGE (id_node)-[:HAS_COLOR]->(color_node)
    RETURN count(*) as nodes_created
"#;


pub const CREATE_NODES_SHARD2: &str = r#"
    USE fabric.dbshard2
    UNWIND $batch AS row
    MERGE (id_node:Id {value: row[0]})
    CREATE (sensor_data_node:SensorData {timestamp: row[5]})
    MERGE (temp_node:Temperature {value: row[3]})
    MERGE (hum_node:Humidity {value: row[4]})
    MERGE (id_node)-[:HAS_SENSOR_DATA]->(sensor_data_node)
    MERGE (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node)
    MERGE (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node)
    RETURN count(*) as nodes_created
"#;


pub const CREATE_NODES_SHARD3: &str = r#"
    USE fabric.dbshard3
    UNWIND $batch AS row
    MERGE (id:Id {value: row[0]})
    MERGE (ts:Timestamp {value: row[5]})
    CREATE (econsume:EnergyConsumption {value: row[6]})
    CREATE (ecost:EnergyCost {value: row[7]})
    MERGE (id)-[:HAS_TIMESTAMP]->(ts)
    MERGE (id)-[:HAS_ENERGY_CONSUMPTION]->(econsume)
    MERGE (econsume)-[:HAS_ENERGY_COST]->(ecost)
    RETURN count(*) as nodes_created
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

pub const CREATE_ENERGY_COST_NODES_SHARD3: &str = r#"
    USE fabric.dbshard3
    MERGE (time_node:Timestamp {value: $timestamp})
    MERGE (ecost_node:EnergyCost {value: toFloat($energy_cost)})
    MERGE (time_node)-[:ENERGY_COSTS]->(ecost_node)
    RETURN time_node.value AS timestamp
"#;

pub const GET_ENERGY_COSTS: &str = r#"
    USE fabric.dbshard3
    MATCH (time_node:Timestamp)-[:ENERGY_COSTS]->(ecost_node:EnergyCost)
    WHERE time_node.value >= $start    
    AND time_node.value <= $end  
    RETURN 
    time_node.value AS timestamp,
    ecost_node.value AS energy_cost
    ORDER BY energy_cost ASC
    LIMIT 5
    "#;


pub const DELETE_DATA_BY_ID_SHARD1: &str = r#"
    USE fabric.dbshard1
    MATCH (id_node:Id {value: $target_id}) 
    WITH id_node, id_node.value AS id_val 
    OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid) 
    DETACH DELETE id_node, uuid_node 
    RETURN id_val AS deleted_id 
"#;

pub const DELETE_DATA_BY_ID_SHARD2: &str = r#"
    USE fabric.dbshard2
    MATCH (id_node:Id {value: $target_id}) 
    WITH id_node, id_node.value AS id_val 
    OPTIONAL MATCH (id_node)-[:HAS_SENSOR_DATA]->(sensor_data_node:SensorData) 
    DETACH DELETE id_node, sensor_data_node 
    RETURN id_val AS deleted_id
"#;

pub const DELETE_DATA_BY_ID_SHARD3: &str = r#"
    USE fabric.dbshard3
    MATCH (id_node:Id {value: $target_id}) 
    WITH id_node, id_node.value AS id_val 
    OPTIONAL MATCH (id_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsumption)
    OPTIONAL MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)
    DETACH DELETE id_node, econsume_node, ecost_node
    RETURN id_val AS deleted_id
"#;

pub const GET_NEWEST_SENSORDATA: &str = r#"
    USE fabric.dbshard2
    MATCH (sensor_data_node:SensorData)
    OPTIONAL MATCH (id_node:Id)-[:HAS_SENSOR_DATA]->(sensor_data_node)
    OPTIONAL MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
    OPTIONAL MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
    RETURN id_node.value AS id, {
        timestamp: sensor_data_node.timestamp,
        temperature: temp_node.value,
        humidity: hum_node.value
    } AS sensor_reading
    ORDER BY sensor_data_node.timestamp DESC
    LIMIT 50
"#;

pub const GET_NEWEST_ENERGYDATA: &str = r#"
    USE fabric.dbshard3
    MATCH (time_node:Timestamp)
    OPTIONAL MATCH (id_node:Id)-[:HAS_TIMESTAMP]->(time_node)
    OPTIONAL MATCH (id_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsumption)
    OPTIONAL MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)
    RETURN id_node.value AS id, {
        timestamp: time_node.value,
        energy_consume: econsume_node.value,
        energy_cost: ecost_node.value
    } AS energy_reading
    ORDER BY time_node.value DESC
    LIMIT 50
"#;

pub const GET_TEMPERATURE_HUMIDITY_AT_TIME: &str = r#"
    USE fabric.dbshard3
    MATCH (time_node:Timestamp {value: $timestamp})
    WITH time_node
    USE fabric.dbshard2
    MATCH (id_node:Id)-[:HAS_SENSOR_DATA]->(sensor_data_node:SensorData)
    WHERE sensor_data_node.timestamp = datetime($timestamp)
    OPTIONAL MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
    OPTIONAL MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
    RETURN temp_node.value AS temperature, hum_node.value AS humidity
"#;

pub const GET_NODES_IN_TIME_RANGE: &str = r#"
    USE fabric.dbshard3
    MATCH (id_node:Id)-[:HAS_TIMESTAMP]->(time_node:Timestamp)
    WHERE time_node.value >= $start AND time_node.value <= $end
    RETURN id_node.value AS uuid

"#;

pub const GET_NODES_WITH_TEMPERATURE_OR_HUMIDITY: &str = r#"
    USE fabric.dbshard2
    MATCH (id_node:Id)-[:HAS_SENSOR_DATA]->(sensor_data_node:SensorData)
    WHERE 
        EXISTS((sensor_data_node)-[:MEASURES_TEMPERATURE]->(:Temperature {value: $temp})) OR
        EXISTS((sensor_data_node)-[:MEASURES_HUMIDITY]->(:Humidity {value: $humidity}))
    RETURN id_node.value AS uuid
"#;

pub const GET_NODES_WITH_ENERGY_COST: &str = r#"
    USE fabric.dbshard3
    MATCH (id_node:Id)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsumption)
    MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost {value: $energy_cost})
    RETURN id_node.value AS uuid
"#;

pub const GET_NODES_WITH_ENERGY_CONSUME: &str = r#"
    USE fabric.dbshard3
    MATCH (id_node:Id)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsumption {value: $energy_consume})
    RETURN id_node.value AS uuid
"#;

pub const GET_NODES_WITH_COLOR: &str = r#"
    USE fabric.dbshard1
    MATCH (id_node:Id)-[:HAS_COLOR]->(color_node:Color {value: $color})
    OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
    RETURN id_node.value AS id, uuid_node.value AS uuid, color_node.value AS color
"#;

pub const RELATIONSHIP_QUERY: &str = r#"
    USE fabric.{}
    MATCH p=()-[]->() 
    WITH p
    {}  
    WITH collect(p) AS paths
    RETURN apoc.convert.toJson(paths) AS json_result
"#;

// Admin queries

pub const ADD_NEW_NODE_ADMIN_SHARD_1: &str = r#"
       USE fabric.dbshard1
    UNWIND $batch AS row
    CREATE (id_node:Id {value: row[0]})
    CREATE (uuid_node:Uuid {value: row[1]})
    MERGE (color_node:Color {value: row[2]})
    MERGE (id_node)-[:HAS_UUID]->(uuid_node)
    MERGE (id_node)-[:HAS_COLOR]->(color_node)
    RETURN id_node.value AS nodeId
        "#;

pub const ADD_NEW_NODE_ADMIN_SHARD_2: &str = r#"
            USE fabric.dbshard2
            UNWIND $batch AS row
            MERGE (id_node:Id {value: row[0]})
            CREATE (sensor_data_node:SensorData {timestamp: datetime()})
            MERGE (temp_node:Temperature {value: row[1]})
            MERGE (hum_node:Humidity {value: row[2]})
            MERGE (id_node)-[:HAS_SENSOR_DATA]->(sensor_data_node)
            MERGE (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node)
            MERGE (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node)
            RETURN id_node.value AS nodeId
        "#;

pub const ADD_NEW_NODE_ADMIN_SHARD_3: &str = r#"
        USE fabric.dbshard3
        UNWIND $batch AS row
        MERGE (id:Id {value: row[0]})
        MERGE (ts:Timestamp {value: row[1]})
        CREATE (econsume:EnergyConsumption {value: row[2]})
        CREATE (ecost:EnergyCost {value: row[3]})
        MERGE (id)-[:HAS_TIMESTAMP]->(ts)
        MERGE (id)-[:HAS_ENERGY_CONSUMPTION]->(econsume)
        MERGE (econsume)-[:HAS_ENERGY_COST]->(ecost)
        RETURN id.value AS nodeId
        "#;

pub const DELETE_NODE_ADMIN_SHARD_1: &str = r#"
    USE fabric.dbshard1
    MATCH (n) DETACH DELETE n"#;

pub const DELETE_NODE_ADMIN_SHARD_2: &str = r#"
    USE fabric.dbshard2
    MATCH (n) DETACH DELETE n"#;

pub const DELETE_NODE_ADMIN_SHARD_3: &str = r#"
    USE fabric.dbshard3
    MATCH (n) DETACH DELETE n"#;



pub const GET_DATA_BY_IDS_SHARD1: &str = r#"
    USE fabric.dbshard1
    MATCH (id_node:Id) WHERE id_node.value IN $target_ids
    OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
    OPTIONAL MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
    RETURN id_node.value AS id, uuid_node.value AS uuid, color_node.value AS color
"#;

pub const GET_DATA_BY_IDS_SHARD2: &str = r#"
    USE fabric.dbshard2
    MATCH (id_node:Id) WHERE id_node.value IN $target_ids
    OPTIONAL MATCH (id_node)-[:HAS_SENSOR_DATA]->(sensor_data_node:SensorData)
    OPTIONAL MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
    OPTIONAL MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
    WITH id_node, sensor_data_node, temp_node, hum_node
    WHERE sensor_data_node IS NOT NULL
    RETURN id_node.value AS id, {
        temperature: temp_node.value,
        humidity: hum_node.value
    } AS sensor_reading
"#;

pub const GET_ENERGY_DATA_BY_IDS_SHARD3: &str = r#"
    USE fabric.dbshard3
    MATCH (id_node:Id) WHERE id_node.value IN $target_ids
    OPTIONAL MATCH (id_node)-[:HAS_TIMESTAMP]->(time_node:Timestamp)
    OPTIONAL MATCH (id_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsumption)
    OPTIONAL MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)
    WITH id_node, time_node, econsume_node, ecost_node
    WHERE time_node IS NOT NULL OR econsume_node IS NOT NULL OR ecost_node IS NOT NULL
    RETURN id_node.value AS id, {
        timestamp: time_node.value,
        energy_consume: econsume_node.value,
        energy_cost: ecost_node.value
    } AS energy_reading
    ORDER BY id_node.value, time_node.value
"#;