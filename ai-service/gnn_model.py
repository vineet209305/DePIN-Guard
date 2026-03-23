import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
 
 
class FraudGNN(torch.nn.Module):
    """
    Two-layer Graph Convolutional Network for fraud detection.
 
    Forward pass:
        GCNConv(in_features → hidden_dim)  → ReLU → Dropout(0.3)
        GCNConv(hidden_dim  → num_classes) → log_softmax
 
    Args:
        in_features  (int): Number of input node features. Default 4.
        hidden_dim   (int): Hidden layer width.            Default 16.
        num_classes  (int): Number of output classes.      Default 2.
    """
 
    def __init__(self, in_features: int = 4, hidden_dim: int = 16, num_classes: int = 2):
        super().__init__()
        self.conv1 = GCNConv(in_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, num_classes)
 
    def forward(self, data):
        x, edge_index = data.x, data.edge_index
 
        # Layer 1: graph convolution + activation
        x = F.relu(self.conv1(x, edge_index))
 
        # Regularisation: dropout during training only
        x = F.dropout(x, p=0.3, training=self.training)
 
        # Layer 2: graph convolution → class logits
        x = self.conv2(x, edge_index)
 
        # Log-softmax for use with F.nll_loss
        return F.log_softmax(x, dim=1)
 
 
# ---------------------------------------------------------------------------
# Self-test — run: python gnn_model.py
# Expected output:
#   Output shape: torch.Size([5, 2])
#   FraudGNN loaded successfully!
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from torch_geometric.data import Data
 
    # Build a tiny dummy graph: 5 nodes, 4 features each, 3 directed edges
    model = FraudGNN(in_features=4, hidden_dim=16, num_classes=2)
 
    test_data = Data(
        x=torch.zeros((5, 4)),                                        # 5 nodes × 4 features
        edge_index=torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long)  # 3 edges
    )
 
    # Run in eval mode (disables dropout)
    model.eval()
    with torch.no_grad():
        out = model(test_data)
 
    print("Output shape:", out.shape)   # expected: torch.Size([5, 2])
    print("FraudGNN loaded successfully!")