from torch_geometric.data import Data
import torch


def _coerce_float(record, *keys, default=0.0):
    for key in keys:
        value = record.get(key)
        if value is not None:
            return float(value)
    return default


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

    # Build node features: [temperature, vibration, power_usage, is_critical]
    feature_map = {}
    for record in history_records:
        dev = record.get("device", "unknown")
        feature_map[dev] = [
            _coerce_float(record, "temperature", "temp"),
            _coerce_float(record, "vibration", "vib"),
            _coerce_float(record, "pressure", "power_usage", "pwr"),
            1.0 if str(record.get("status", "normal")).lower() == "critical" else 0.0,
        ]

    x_list = []
    for name in node_map:
        if name in feature_map:
            x_list.append(feature_map[name])
        else:
            x_list.append([0.0, 0.0, 0.0, 1.0 if name == "critical" else 0.0])

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
