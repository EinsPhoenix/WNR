# Neo4j Database Operations - Documentation

## 📌 Overview

This Rust implementation provides comprehensive database operations for a Neo4j graph database, including CRUD operations, complex queries, and data processing utilities.

## ✨ Features

- **Node Creation**: Create nodes with relationships
- **Data Validation**: Robust input validation
- **Query Operations**: Various query types (UUID, time range, pagination etc.)
- **Database Management**: Indexing, reset, and configuration
- **Bulk Processing**: Large JSON file processing
- **Error Handling**: Comprehensive error management

## 🚀 Quick Start

1. **Ensure Neo4j is running** with appropriate connection settings
2. **Import the module**:
   ```rust
   use your_crate::db_operations;
   ```
3. **Initialize a Graph connection**:
   ```rust
   let graph = neo4rs::Graph::new(uri, user, password).await?;
   ```

## 📋 Core Functions

### Data Validation

| Function | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `validate_data` | Validates JSON data structure | `data: &Value` | `bool` |
| `validate_item` | Validates individual item structure | `item: &Value` | `bool` |

### CRUD Operations

| Function | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `create_new_relation` | Creates nodes with relationships | `data: &Value`, `graph: &Graph` | `Result<bool, String>` |
| `get_specific_uuid_node` | Retrieves node by UUID | `uuid: &str`, `graph: &Graph` | `Option<Value>` |
| `get_all_uuid_nodes` | Retrieves all UUID nodes | `graph: &Graph` | `Option<Value>` |

### Query Operations

| Function | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `get_nodes_in_time_range` | Nodes within time range | `start: &str`, `end: &str`, `graph: &Graph` | `Option<Value>` |
| `get_nodes_with_color` | Nodes by color | `color: &str`, `graph: &Graph` | `Option<Value>` |
| `get_paginated_uuids` | Paginated UUID results | `graph: &Graph`, `page: usize` | `Option<Value>` |

### Database Management

| Function | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `index_database` | Creates indexes | `graph: &Graph` | `Result<bool, String>` |
| `reset_database` | Clears all data | `graph: &Graph` | `Result<bool, String>` |
| `alter_database` | Modifies DB topology | `graph: &Graph` | `Result<bool, String>` |

### Bulk Processing

| Function | Description | Parameters | Returns |
|----------|-------------|------------|---------|
| `process_large_json_file` | Processes large JSON file | `graph: &Graph` | `Result<bool, Box<dyn Error>>` |

## 📊 Data Structure

### Node Structure
```json
{
  "uuid": "string",
  "color": "string",
  "sensor_data": {
    "temperature": float,
    "humidity": float
  },
  "timestamp": "ISO8601",
  "energy_consume": float,
  "energy_cost": float
}
```

### Relationships
- `(UUID)-[:HAS_COLOR]->(Color)`
- `(UUID)-[:HAS_TEMPERATURE]->(Temperature)`
- `(UUID)-[:HAS_HUMIDITY]->(Humidity)`
- `(UUID)-[:HAS_TIMESTAMP]->(Timestamp)`
- `(UUID)-[:HAS_ENERGYCOST]->(EnergyCost)`
- `(UUID)-[:HAS_ENERGYCONSUME]->(EnergyConsume)`

## ⚙️ Configuration

### Required Indexes
```cypher
CREATE INDEX FOR (u:UUID) ON (u.id)
CREATE INDEX FOR (c:Color) ON (c.value)
CREATE INDEX FOR (t:Temperature) ON (t.value)
CREATE INDEX FOR (h:Humidity) ON (h.value)
CREATE INDEX FOR (ts:Timestamp) ON (ts.value)
CREATE INDEX FOR (ec:EnergyCost) ON (ec.value)
CREATE INDEX FOR (e:EnergyConsume) ON (e.value)
```

## 💡 Usage Examples

### Creating Nodes
```rust
let data = json!({
    "data": [{
        "uuid": "test123",
        "color": "red",
        "sensor_data": {"temperature": 22.5, "humidity": 45.0},
        "timestamp": "2023-01-01T00:00:00Z",
        "energy_consume": 100.0,
        "energy_cost": 50.0
    }]
});
create_new_relation(&data, &graph).await?;
```

### Querying Data
```rust
// Get specific UUID
let node = get_specific_uuid_node("test123", &graph).await;

// Get paginated results
let page = get_paginated_uuids(&graph, 0).await;
```

### Database Maintenance
```rust
// Create indexes
index_database(&graph).await?;

// Reset database
reset_database(&graph).await?;
```

## ⚠️ Important Notes

1. **Data Validation**: All input data is strictly validated
2. **Error Handling**: Functions return detailed error messages
3. **Pagination**: Default page size is 25 items
4. **Bulk Processing**: Large files are processed in streams
5. **Cleanup**: Always clean test data after operations

## 📈 Performance Tips

1. Use indexes for frequently queried properties
2. For large imports, use `process_large_json_file`
3. Paginate results for large datasets
4. Reuse Graph connections where possible

## 🔍 Detailed Function Documentation

### `create_new_relation()`

Creates nodes with all relationships in a single transaction.

**Validation Steps**:
1. Checks for required fields
2. Validates data types
3. Ensures proper JSON structure

**Neo4j Operations**:
1. Creates UUID node
2. Creates related nodes (Color, Temperature, etc.)
3. Establishes all relationships
4. Uses MERGE to avoid duplicates

### `get_paginated_uuids()`

Returns paginated results with metadata.

**Response Structure**:
```json
{
  "nodes": [...],
  "pagination": {
    "total_count": 100,
    "total_pages": 4,
    "current_page": 0,
    "page_size": 25
  }
}
```

### `process_large_json_file()`

Processes large JSON files with:

1. **Streaming**: Uses buffered reading
2. **Progress Tracking**: Logs every 100 items
3. **Error Handling**: Continues after errors
4. **Summary Reporting**: Success/failure counts

## 🛠️ Troubleshooting

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| Validation failures | Missing/malformed fields | Check input structure |
| Duplicate nodes | Existing UUIDs | Use MERGE in queries |
| Slow queries | Missing indexes | Run `index_database()` |
| Connection issues | Neo4j unavailable | Check Neo4j service |

