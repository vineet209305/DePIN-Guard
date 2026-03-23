import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from gnn_model import FraudGNN
 
 
def make_graph(num_nodes: int, label: int, feature_val: float) -> Data:
    """
    Build a simple synthetic linear graph for training.
 
    Args:
        num_nodes   : Number of nodes in the graph.
        label       : Class label for every node (0=normal, 1=fraud).
        feature_val : Constant value filled into all node features.
 
    Returns:
        torch_geometric.data.Data object with x, edge_index, y, train_mask.
    """
    # Node features: all nodes share the same constant feature value
    x = torch.full((num_nodes, 4), feature_val)
 
    # Edges: simple chain  0→1, 1→2, ..., (n-2)→(n-1)
    edge_index = torch.tensor(
        [
            [i for i in range(num_nodes - 1)],       # source nodes
            [i + 1 for i in range(num_nodes - 1)],   # target nodes
        ],
        dtype=torch.long,
    )
 
    # All nodes carry the same label for this synthetic dataset
    y = torch.full((num_nodes,), label, dtype=torch.long)
 
    # All nodes participate in training
    train_mask = torch.ones(num_nodes, dtype=torch.bool)
 
    return Data(x=x, edge_index=edge_index, y=y, train_mask=train_mask)
 
 
# ---------------------------------------------------------------------------
# Synthetic training data
#   normal_data : low feature values  (0.1) → label 0
#   fraud_data  : high feature values (0.9) → label 1
# ---------------------------------------------------------------------------
normal_data = make_graph(num_nodes=6, label=0, feature_val=0.1)
fraud_data  = make_graph(num_nodes=6, label=1, feature_val=0.9)
 
# ---------------------------------------------------------------------------
# Model, optimiser
# ---------------------------------------------------------------------------
model     = FraudGNN(in_features=4, hidden_dim=16, num_classes=2)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
 
# ---------------------------------------------------------------------------
# Training loop — 50 epochs over both graphs
# ---------------------------------------------------------------------------
print("Starting GNN training...")
 
for epoch in range(1, 51):
    total_loss = 0.0
 
    for data in [normal_data, fraud_data]:
        model.train()
        optimizer.zero_grad()
 
        out  = model(data)                                        # (num_nodes, 2)
        loss = F.nll_loss(out[data.train_mask], data.y[data.train_mask])
 
        loss.backward()
        optimizer.step()
 
        total_loss += loss.item()
 
    # Print progress every 10 epochs so demo terminal looks readable
    if epoch % 10 == 0:
        print(f"Epoch {epoch}/50 — combined loss: {total_loss:.4f}")
 
# ---------------------------------------------------------------------------
# Save trained weights
# ---------------------------------------------------------------------------
torch.save(model.state_dict(), "gnn_model.pth")
print("GNN training complete. Weights saved to gnn_model.pth")