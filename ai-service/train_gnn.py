import os
import sqlite3

import torch
import torch.nn.functional as F
from torch_geometric.data import Data

from gnn_model import FraudGNN


EPOCHS = 50
LR = 0.01
SQLITE_PATHS = [
    "../backend/data/depin_guard.sqlite3",
    "backend/data/depin_guard.sqlite3",
]
TRAINING_SOURCE = os.getenv("TRAINING_SOURCE", "auto").strip().lower()


def find_sqlite_path():
    for candidate in SQLITE_PATHS:
        if os.path.exists(candidate):
            return candidate
    return None


def make_synthetic_graph() -> Data:
    # Fallback graph so training still works before real data is available.
    num_nodes = 12
    x = torch.tensor([[0.1, 0.2, 0.3, 0.0]] * 6 + [[0.9, 0.85, 0.8, 1.0]] * 6, dtype=torch.float32)
    edge_index = torch.tensor(
        [
            [i for i in range(num_nodes - 1)],
            [i + 1 for i in range(num_nodes - 1)],
        ],
        dtype=torch.long,
    )
    y = torch.tensor([0] * 6 + [1] * 6, dtype=torch.long)
    train_mask = torch.ones(num_nodes, dtype=torch.bool)
    return Data(x=x, edge_index=edge_index, y=y, train_mask=train_mask)


def load_graph_from_sqlite() -> Data | None:
    sqlite_path = find_sqlite_path()
    if not sqlite_path:
        return None

    try:
        with sqlite3.connect(sqlite_path) as connection:
            rows = connection.execute(
                """
                SELECT temp, vib, pwr, anomaly
                FROM sensor_readings
                WHERE temp IS NOT NULL AND vib IS NOT NULL AND pwr IS NOT NULL
                ORDER BY id ASC
                """
            ).fetchall()
    except Exception as exc:
        print(f"SQLite graph source unavailable ({exc}); using fallback")
        return None

    if len(rows) < 10:
        print(f"SQLite found at {sqlite_path} but only {len(rows)} rows; need >= 10")
        return None

    features = []
    labels = []
    prev_temp = float(rows[0][0])
    for temp, vib, pwr, anomaly in rows:
        temp = float(temp)
        vib = float(vib)
        pwr = float(pwr)
        anom = int(anomaly or 0)
        temp_delta = temp - prev_temp
        prev_temp = temp

        features.append([temp, vib, pwr, temp_delta])
        labels.append(anom)

    x = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.long)

    num_nodes = len(features)
    edge_index = torch.tensor(
        [
            [i for i in range(num_nodes - 1)],
            [i + 1 for i in range(num_nodes - 1)],
        ],
        dtype=torch.long,
    )
    train_mask = torch.ones(num_nodes, dtype=torch.bool)

    print(f"Loaded GNN training graph from SQLite: {sqlite_path} ({num_nodes} nodes)")
    return Data(x=x, edge_index=edge_index, y=y, train_mask=train_mask)


def load_training_graph() -> Data:
    if TRAINING_SOURCE in ("auto", "sqlite"):
        graph = load_graph_from_sqlite()
        if graph is not None:
            return graph

    print("Using synthetic fallback graph for GNN training")
    return make_synthetic_graph()


def main():
    data = load_training_graph()

    model = FraudGNN(in_features=4, hidden_dim=16, num_classes=2)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    print("Starting GNN training...")
    for epoch in range(1, EPOCHS + 1):
        model.train()
        optimizer.zero_grad()

        out = model(data)
        loss = F.nll_loss(out[data.train_mask], data.y[data.train_mask])

        loss.backward()
        optimizer.step()

        if epoch % 10 == 0:
            print(f"Epoch {epoch}/{EPOCHS} - loss: {loss.item():.4f}")

    torch.save(model.state_dict(), "gnn_model.pth")
    print("GNN training complete. Weights saved to gnn_model.pth")


if __name__ == "__main__":
    main()
