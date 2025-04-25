import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import json
import scipy 
from itertools import islice
import sys
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import time


# THIS IS IMPORTANT SO TAKE THE COMMENTS
def parse_neo4j_data(data_str):
    """Parses Neo4j data with optimized streaming for large datasets."""

    # If the input is already a list, return it as is
    if isinstance(data_str, list):
        return data_str

    # If the input is a string, process it
    if isinstance(data_str, str):
        data_str = data_str.strip()  # Remove leading/trailing whitespace

        # Try to parse the string as a simple JSON array (surrounded by brackets)
        try:
            if data_str.startswith("[") and data_str.endswith("]"):
                return json.loads(data_str)  # Parse directly as a JSON array
        except json.JSONDecodeError:
            pass  # If the array is not valid JSON, continue to further processing

        # Check if the data is wrapped in an extra set of brackets (e.g., "[[...]]")
        if data_str.startswith("[[") and data_str.endswith("]]"):
            data_str = data_str[1:-1]  # Remove the outer brackets

        # Initialize variables for bracket counting and JSON array extraction
        json_arrays = []
        bracket_count = 0
        start_index = 0

        # Traverse the string character by character to extract individual JSON arrays
        for i, char in enumerate(data_str):
            if char == "[":
                bracket_count += (
                    1  # Start counting brackets when encountering an opening bracket
                )
                if bracket_count == 1:  # This is the beginning of a new array
                    start_index = i
            elif char == "]":
                bracket_count -= (
                    1  # Close a bracket when encountering a closing bracket
                )
                if bracket_count == 0:  # End of a complete JSON array
                    json_arrays.append(
                        data_str[start_index : i + 1]
                    )  # Extract the array

        # Prepare to process the arrays in batches
        parsed_data = []
        batch_size = 2000  # Set the batch size to 2000 arrays at a time

        # Process the arrays in batches to avoid memory overload and optimize performance
        for i in range(0, len(json_arrays), batch_size):
            batch = json_arrays[
                i : i + batch_size
            ]  # Get the current batch of JSON arrays
            batch_result = []
            for json_array in batch:
                try:
                    batch_result.append(json.loads(json_array))  # Parse each JSON array
                except json.JSONDecodeError:
                    continue  # Skip invalid JSON arrays

            parsed_data.extend(
                batch_result
            )  # Add the parsed results to the main data list
            print(  # Print progress to track how many arrays have been parsed
                f"Parsed {min(i+batch_size, len(json_arrays))}/{len(json_arrays)} JSON arrays"
            )

        return parsed_data  # Return the fully parsed data

    # If the data is neither a list nor a properly formatted string, print an error
    print("Error: Data is not in a recognizable format")
    return []  # Return an empty list if the data is invalid or unrecognized


def create_network_graph(parsed_data, max_nodes=10000):
    """Creates a NetworkX graph with enhanced node sizing based on connection count."""
    G = nx.Graph()
    nodes = {}
    node_count = 0
    relationship_count = 0

    print("Building graph...")
    start_time = time.time()

    for relationship_set in parsed_data:
        for item in relationship_set:
            if item.get("type") == "node":
                node_id = item.get("id")
                if node_id not in nodes and node_count < max_nodes:
                    label = item.get("labels", ["Unknown"])[0]
                    properties = {
                        k: v
                        for k, v in item.get("properties", {}).items()
                        if k in ["id", "value", "name"]
                    }

                    nodes[node_id] = {
                        "label": label,
                        "properties": properties,
                        "relationships": 0,
                    }
                    node_count += 1

            elif item.get("type") == "relationship":
                start_node = item.get("start", {}).get("id")
                end_node = item.get("end", {}).get("id")

                if start_node in nodes and end_node in nodes:

                    nodes[start_node]["relationships"] += 1
                    nodes[end_node]["relationships"] += 1
                    relationship_count += 1

    for node_id, node_data in nodes.items():
        G.add_node(
            node_id,
            label=node_data["label"],
            relationship_count=node_data["relationships"],
            **node_data["properties"],
        )

    relationship_count = 0

    for relationship_set in parsed_data:
        for item in relationship_set:
            if item.get("type") == "relationship":
                start_node = item.get("start", {}).get("id")
                end_node = item.get("end", {}).get("id")

                if start_node in nodes and end_node in nodes:
                    rel_label = item.get("label", "RELATED_TO")
                    G.add_edge(start_node, end_node, label=rel_label)
                    relationship_count += 1

    elapsed = time.time() - start_time
    print(
        f"Graph created with {len(G.nodes())} nodes and {len(G.edges())} edges in {elapsed:.2f} seconds"
    )
    return G


def visualize_3d_graph(G, show_labels=True, max_edges_to_show=20000):
    """Enhanced 3D visualization with better performance and aesthetics."""
    if len(G.nodes()) == 0:
        print("Error: Graph has no nodes to visualize")
        return

    node_count = len(G.nodes())
    edge_count = len(G.edges())

    print(f"Calculating layout for {node_count} nodes...")
    start_time = time.time()

    if node_count > 1000:
        print("Using random layout for very large graph...")
        pos_3d = nx.random_layout(G, dim=3)
    elif node_count > 500:
        print("Using spectral layout for large graph...")
        try:
            pos_3d = nx.spectral_layout(G, dim=3)
        except:
            print("Spectral layout failed, falling back to spring layout...")
            pos_3d = nx.spring_layout(
                G, dim=3, seed=42, iterations=50, k=0.5 / np.sqrt(node_count)
            )
    else:

        pos_3d = nx.spring_layout(G, dim=3, seed=42, k=0.8 / np.sqrt(node_count))

    layout_time = time.time() - start_time
    print(f"Layout calculated in {layout_time:.2f} seconds")

    fig = plt.figure(figsize=(16, 12), dpi=100)
    ax = fig.add_subplot(111, projection="3d", computed_zorder=False)

    # Calculate node sizes based on relationship count

    relationship_counts = np.array(
        [data.get("relationship_count", 0) for _, data in G.nodes(data=True)]
    )

    max_relationships = max(relationship_counts) if relationship_counts.size > 0 else 1
    min_relationships = min(relationship_counts) if relationship_counts.size > 0 else 0

    min_size = 50
    max_size = 500

    node_colors = []
    node_sizes = []
    node_labels = {}

    color_map = {
        "UUID": "#3498db",
        "Color": "#2ecc71",
        "Temperature": "#e74c3c",
        "Humidity": "#1abc9c",
        "Timestamp": "#f1c40f",
        "EnergyCost": "#9b59b6",
        "EnergyConsume": "#e67e22",
        "Unknown": "#95a5a6",
    }

    xs, ys, zs = [], [], []

    for node, attrs in G.nodes(data=True):
        label = attrs.get("label", "Unknown")
        rel_count = attrs.get("relationship_count", 0)

        node_colors.append(color_map.get(label, color_map["Unknown"]))

        if max_relationships > min_relationships:

            size = min_size + (max_size - min_size) * np.log1p(rel_count) / np.log1p(
                max_relationships
            )
        else:
            size = min_size

        node_sizes.append(size)

        xs.append(pos_3d[node][0])
        ys.append(pos_3d[node][1])
        zs.append(pos_3d[node][2])

        if show_labels:

            if rel_count > max_relationships * 0.1 or (node_count <= 100):
                if "value" in attrs:
                    node_labels[node] = f"{label}: {attrs['value']}"
                elif "name" in attrs:
                    node_labels[node] = f"{attrs['name']}"
                elif "id" in attrs:
                    node_labels[node] = f"{attrs['id']}"
                else:
                    node_labels[node] = f"{label}"

    scatter = ax.scatter(
        xs,
        ys,
        zs,
        c=node_colors,
        s=node_sizes,
        alpha=0.8,
        edgecolors="black",
        linewidths=0.5,
        depthshade=True,
    )

    print("Drawing edges...")
    start_time = time.time()

    if edge_count > max_edges_to_show:
        print(
            f"Limiting visualization to {max_edges_to_show} edges out of {edge_count}"
        )
        edges_to_draw = list(islice(G.edges(), max_edges_to_show))
    else:
        edges_to_draw = G.edges()

    for u, v in edges_to_draw:
        u_count = G.nodes[u].get("relationship_count", 0)
        v_count = G.nodes[v].get("relationship_count", 0)

        importance = (u_count + v_count) / (2 * max_relationships)
        alpha = 0.1 + 0.4 * importance

        x = [pos_3d[u][0], pos_3d[v][0]]
        y = [pos_3d[u][1], pos_3d[v][1]]
        z = [pos_3d[u][2], pos_3d[v][2]]

        linewidth = 0.5 + importance * 1.5
        ax.plot(x, y, z, color="gray", alpha=alpha, linewidth=linewidth)

    edge_time = time.time() - start_time
    print(f"Edges drawn in {edge_time:.2f} seconds")

    if show_labels and node_labels:
        print("Adding labels to significant nodes...")
        for node, label in node_labels.items():
            x, y, z = pos_3d[node]
            ax.text(
                x,
                y,
                z,
                label,
                fontsize=8,
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=1),
                ha="center",
                va="center",
            )

    legend_elements = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=color,
            markersize=10,
            label=label,
        )
        for label, color in color_map.items()
        if any(attrs.get("label") == label for _, attrs in G.nodes(data=True))
    ]

    if legend_elements:
        ax.legend(
            handles=legend_elements, loc="upper right", fontsize=9, framealpha=0.7
        )

    if node_count > 0:
        ax.text2D(
            0.02,
            0.02,
            f"Node size: connections (min={min_relationships}, max={max_relationships})",
            transform=ax.transAxes,
            fontsize=9,
            bbox=dict(facecolor="white", alpha=0.7),
        )

    ax.set_facecolor("#f8f9fa")
    ax.grid(True, alpha=0.3, linestyle="--")

    max_range = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) * 0.5

    mid_x = (max(xs) + min(xs)) * 0.5
    mid_y = (max(ys) + min(ys)) * 0.5
    mid_z = (max(zs) + min(zs)) * 0.5

    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    # Set labels and title
    ax.set_xlabel("X", fontsize=12)
    ax.set_ylabel("Y", fontsize=12)
    ax.set_zlabel("Z", fontsize=12)
    ax.set_title(
        f"3D Neo4j Graph Visualization ({node_count} nodes, {edge_count} edges)",
        fontsize=14,
    )

    ax.set_box_aspect([1, 1, 1])

    ax.view_init(elev=20, azim=30)

    plt.tight_layout()
    print("Rendering visualization...")
    plt.show()


def load_neo4j_data(file_path):
    """Loads Neo4j data with optimized memory handling."""
    print(f"Loading data from {file_path}...")
    try:
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        print(f"File size: {file_size:.2f} MB")

        if file_size > 500:
            print("Large file detected, using streaming mode...")

            import ijson

            with open(file_path, "rb") as f:

                try:

                    objects = ijson.items(f, "item")
                    return list(objects)
                except:
                    print("Streaming parser failed, falling back to standard parser...")

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

            try:
                data = json.loads(content)
                return data
            except json.JSONDecodeError:
                return content

    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except MemoryError:
        print("Error: Not enough memory to load the file.")
        return None
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        return None


def main():
    """Main function with enhanced performance options."""
    import os

    print("\n" + "=" * 70)
    print("Hochperformante 3D Neo4j Graph Visualisierung".center(70))
    print("=" * 70 + "\n")

    file_path = input("Pfad zur Neo4j-Datendatei (leer lassen für Standard): ")

    if not file_path:
        file_path = r"./export_all_data.json"
        print(f"Verwende Standardpfad: {file_path}")

    try:
        max_nodes = input("Maximale Anzahl der Knoten (leer lassen für 10000): ")
        max_nodes = int(max_nodes) if max_nodes else 10000

        show_labels = input(
            "Knotenbeschriftungen anzeigen? (j/n, Standard: n für große Graphen): "
        ).lower()
        show_labels = show_labels == "j" if show_labels else (max_nodes <= 500)

        max_edges = input(
            "Maximale Anzahl der anzuzeigenden Kanten (leer lassen für 20000): "
        )
        max_edges = int(max_edges) if max_edges else 20000
    except ValueError:
        print("Ungültige Eingabe, verwende Standardwerte")
        max_nodes = 10000
        show_labels = False
        max_edges = 20000

    raw_data = load_neo4j_data(file_path)

    if raw_data is None:
        print("Fehler beim Laden der Daten. Beenden.")
        return

    parsed_data = parse_neo4j_data(raw_data)

    if not parsed_data:
        print("Keine gültigen Daten nach dem Parsen gefunden. Beenden.")
        return

    G = create_network_graph(parsed_data, max_nodes=max_nodes)

    if len(G.nodes()) == 0:
        print("Graph hat keine Knoten. Überprüfen Sie Ihr Datenformat.")
        return

    visualize_3d_graph(G, show_labels=show_labels, max_edges_to_show=max_edges)
    print("\nVisualisierung abgeschlossen!")


if __name__ == "__main__":
    try:

        import os

        main()
    except KeyboardInterrupt:
        print("\nOperation vom Benutzer abgebrochen.")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}")
        import traceback

        traceback.print_exc()
