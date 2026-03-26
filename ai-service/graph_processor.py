from torch_geometric.data import Data
import torch


def build_graph_from_history(history_records):
    node_map = {}
    edge_index = []

    def get_node_id(key):
        if key not in node_map:
            node_map[key] = len(node_map)
        return node_map[key]

    for record in history_records:
        device_node = get_node_id(record.get("device", "unknown"))
        status_node = get_node_id(record.get("status", "normal"))
        edge_index.append([device_node, status_node])

    if edge_index:
        edge_tensor = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    else:
        edge_tensor = torch.zeros((2, 0), dtype=torch.long)

    # Build real node features: [temp, vibration, power_usage, is_critical]
    feature_map = {}
    for record in history_records:
        dev = record.get("device", "unknown")
        if dev not in feature_map:
            feature_map[dev] = [
                float(record.get("temp", 0.0)),
                float(record.get("vib", 0.0)),
                float(record.get("pwr", 0.0)),
                1.0 if record.get("status") == "critical" else 0.0
            ]

    x_list = [feature_map.get(name, [0.0, 0.0, 0.0, 0.0]) for name in node_map]
    x = torch.tensor(x_list, dtype=torch.float)
    return Data(x=x, edge_index=edge_tensor), node_map


if __name__ == "__main__":
    dummy = [
        {"device": "Device-001", "status": "normal"},
        {"device": "Device-002", "status": "critical"},
        {"device": "Device-001", "status": "critical"},
    ]
    graph, node_map = build_graph_from_history(dummy)
    print("Nodes:", node_map)
    print("Edge index shape:", graph.edge_index.shape)
    print("Graph built successfully!")
