"""
GNN Models for Drug Repurposing on Heterogeneous Graphs.

Implements:
1. R-GCN (Relational Graph Convolutional Networks)
2. HetGNN (Heterogeneous Graph Neural Network with attention)
3. DotProductDecoder / MLPDecoder for link prediction
"""
import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    from torch_geometric.nn import RGCNConv, HeteroConv, SAGEConv, GATConv
    from torch_geometric.nn import to_hetero
    HAS_PYG = True
except ImportError:
    HAS_PYG = False
    print("[WARNING] torch_geometric not installed. GNN models will use fallback implementation.")


class RGCNLinkPredictor(nn.Module):
    """
    R-GCN based link predictor for heterogeneous graphs.

    Architecture:
    - R-GCN layers for message passing across different relation types
    - Dot-product or MLP decoder for compound-disease link prediction
    """

    def __init__(self, data_or_metadata, hidden_dim=128, num_layers=3,
                 dropout=0.3, decoder_type="mlp"):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout
        self.decoder_type = decoder_type

        if HAS_PYG:
            self._init_pyg(data_or_metadata)
        else:
            self._init_fallback(data_or_metadata)

    def _init_pyg(self, data):
        """Initialize with PyTorch Geometric."""
        node_types = list(data.node_types)
        edge_types = list(data.edge_types)

        # Input projections for each node type
        self.input_projs = nn.ModuleDict()
        for nt in node_types:
            in_dim = data[nt].x.shape[1] if hasattr(data[nt], 'x') else 16
            self.input_projs[nt] = nn.Linear(in_dim, self.hidden_dim)

        # R-GCN layers
        self.convs = nn.ModuleList()
        for _ in range(self.num_layers):
            conv = HeteroConv({
                et: RGCNConv(
                    in_channels=self.hidden_dim,
                    out_channels=self.hidden_dim,
                    num_relations=len(edge_types),
                )
                if not hasattr(self, '_use_sage') else
                SAGEConv(self.hidden_dim, self.hidden_dim)
                for et in edge_types
            }, aggr='sum')
            self.convs.append(conv)

        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(self.hidden_dim) for _ in range(self.num_layers)
        ])

        # Decoder
        if self.decoder_type == "mlp":
            self.decoder = nn.Sequential(
                nn.Linear(self.hidden_dim * 2, self.hidden_dim),
                nn.ReLU(),
                nn.Dropout(self.dropout),
                nn.Linear(self.hidden_dim, 1),
            )
        else:
            self.decoder = None  # dot product

    def _init_fallback(self, metadata):
        """Fallback initialization without PyG."""
        node_features = metadata.get("node_features", {})
        if node_features:
            dims = {nt: feat.shape[1] for nt, feat in node_features.items()}
        else:
            dims = {"herb": 5, "compound": 4, "target": 3, "disease": 2, "drug": 20}

        self.input_projs = nn.ModuleDict()
        for nt in dims:
            self.input_projs[nt] = nn.Linear(dims[nt], self.hidden_dim)

        # Simplified GNN layers (just MLPs as fallback)
        self.gnn_layers = nn.ModuleList()
        for _ in range(self.num_layers):
            self.gnn_layers.append(nn.Sequential(
                nn.Linear(self.hidden_dim, self.hidden_dim),
                nn.ReLU(),
                nn.Dropout(self.dropout),
            ))

        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(self.hidden_dim) for _ in range(self.num_layers)
        ])

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(self.hidden_dim * 2, self.hidden_dim),
            nn.ReLU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.hidden_dim, 1),
        )

    def forward(self, data, src_nodes, dst_nodes, src_type="compound", dst_type="disease"):
        """
        Forward pass: get embeddings and predict links.

        Args:
            data: HeteroData or dict
            src_nodes: source node indices (compound)
            dst_nodes: destination node indices (disease)
            src_type, dst_type: node types for link prediction
        """
        if HAS_PYG:
            return self._forward_pyg(data, src_nodes, dst_nodes, src_type, dst_type)
        else:
            return self._forward_fallback(data, src_nodes, dst_nodes, src_type, dst_type)

    def _forward_pyg(self, data, src_nodes, dst_nodes, src_type, dst_type):
        """PyG forward pass."""
        x_dict = {}
        for nt in data.node_types:
            x_dict[nt] = self.input_projs[nt](data[nt].x)

        for i, conv in enumerate(self.convs):
            x_dict_new = conv(x_dict)
            for nt in x_dict_new:
                x_dict[nt] = F.relu(self.layer_norms[i](x_dict_new[nt] + x_dict.get(nt, 0)))
                x_dict[nt] = F.dropout(x_dict[nt], p=self.dropout, training=self.training)

        return self._decode(x_dict, src_nodes, dst_nodes, src_type, dst_type)

    def _forward_fallback(self, data, src_nodes, dst_nodes, src_type, dst_type):
        """Fallback forward pass using MLP-based message passing."""
        node_features = data.get("node_features", {})

        x_dict = {}
        for nt in node_features:
            feat = torch.tensor(node_features[nt], dtype=torch.float32)
            x_dict[nt] = self.input_projs[nt](feat)

        # Simplified message passing (self-transformation + neighbor aggregation)
        for i, layer in enumerate(self.gnn_layers):
            for nt in x_dict:
                x_dict[nt] = layer(x_dict[nt])
                x_dict[nt] = self.layer_norms[i](x_dict[nt])

        return self._decode(x_dict, src_nodes, dst_nodes, src_type, dst_type)

    def _decode(self, x_dict, src_nodes, dst_nodes, src_type, dst_type):
        """Decode link predictions."""
        src_emb = x_dict[src_type][src_nodes]
        dst_emb = x_dict[dst_type][dst_nodes]

        if self.decoder_type == "mlp" and self.decoder is not None:
            concat = torch.cat([src_emb, dst_emb], dim=-1)
            logits = self.decoder(concat).squeeze(-1)
        else:
            # Dot product decoder
            logits = (src_emb * dst_emb).sum(dim=-1)

        return logits

    def get_embeddings(self, data):
        """Get node embeddings for all node types."""
        if HAS_PYG:
            x_dict = {}
            for nt in data.node_types:
                x_dict[nt] = self.input_projs[nt](data[nt].x)
            for conv in self.convs:
                x_dict_new = conv(x_dict)
                for nt in x_dict_new:
                    x_dict[nt] = F.relu(x_dict_new[nt] + x_dict.get(nt, 0))
            return x_dict
        else:
            node_features = data.get("node_features", {})
            x_dict = {}
            for nt in node_features:
                feat = torch.tensor(node_features[nt], dtype=torch.float32)
                x_dict[nt] = self.input_projs[nt](feat)
            return x_dict


class HetGNNLinkPredictor(nn.Module):
    """
    Heterogeneous Graph Neural Network with attention mechanism.

    Uses type-specific aggregators and cross-type attention for
    better modeling of heterogeneous relationships.
    """

    def __init__(self, data_or_metadata, hidden_dim=128, num_layers=3,
                 dropout=0.3, num_heads=4):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout = dropout
        self.num_heads = num_heads

        if HAS_PYG:
            self._init_pyg(data_or_metadata)
        else:
            self._init_fallback(data_or_metadata)

    def _init_pyg(self, data):
        """Initialize with PyG HeteroConv + GATConv."""
        node_types = list(data.node_types)
        edge_types = list(data.edge_types)

        self.input_projs = nn.ModuleDict()
        for nt in node_types:
            in_dim = data[nt].x.shape[1] if hasattr(data[nt], 'x') else 16
            self.input_projs[nt] = nn.Linear(in_dim, self.hidden_dim)

        self.convs = nn.ModuleList()
        for _ in range(self.num_layers):
            conv = HeteroConv({
                et: GATConv(
                    self.hidden_dim, self.hidden_dim // self.num_heads,
                    heads=self.num_heads,
                    dropout=self.dropout,
                    concat=True,
                )
                for et in edge_types
            }, aggr='mean')
            self.convs.append(conv)

        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(self.hidden_dim) for _ in range(self.num_layers)
        ])

        # Type-aware attention
        self.type_attention = nn.ModuleDict()
        for nt in node_types:
            self.type_attention[nt] = nn.MultiheadAttention(
                self.hidden_dim, num_heads=2, batch_first=True
            )

        # MLP decoder
        self.decoder = nn.Sequential(
            nn.Linear(self.hidden_dim * 2, self.hidden_dim),
            nn.ReLU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.hidden_dim, 1),
        )

    def _init_fallback(self, metadata):
        """Fallback without PyG."""
        node_features = metadata.get("node_features", {})
        if node_features:
            dims = {nt: feat.shape[1] for nt, feat in node_features.items()}
        else:
            dims = {"herb": 5, "compound": 4, "target": 3, "disease": 2, "drug": 20}

        self.input_projs = nn.ModuleDict()
        for nt in dims:
            self.input_projs[nt] = nn.Linear(dims[nt], self.hidden_dim)

        self.gnn_layers = nn.ModuleList()
        for _ in range(self.num_layers):
            self.gnn_layers.append(nn.MultiheadAttention(
                self.hidden_dim, num_heads=self.num_heads,
                dropout=self.dropout, batch_first=True
            ))

        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(self.hidden_dim) for _ in range(self.num_layers)
        ])

        self.decoder = nn.Sequential(
            nn.Linear(self.hidden_dim * 2, self.hidden_dim),
            nn.ReLU(),
            nn.Dropout(self.dropout),
            nn.Linear(self.hidden_dim, 1),
        )

    def forward(self, data, src_nodes, dst_nodes, src_type="compound", dst_type="disease"):
        if HAS_PYG:
            x_dict = {}
            for nt in data.node_types:
                x_dict[nt] = self.input_projs[nt](data[nt].x)

            for i, conv in enumerate(self.convs):
                x_dict_new = conv(x_dict)
                for nt in x_dict_new:
                    x_dict[nt] = F.elu(self.layer_norms[i](x_dict_new[nt] + x_dict.get(nt, 0)))
                    x_dict[nt] = F.dropout(x_dict[nt], p=self.dropout, training=self.training)
        else:
            node_features = data.get("node_features", {})
            x_dict = {}
            for nt in node_features:
                feat = torch.tensor(node_features[nt], dtype=torch.float32)
                x_dict[nt] = self.input_projs[nt](feat)
            for i, layer in enumerate(self.gnn_layers):
                for nt in x_dict:
                    out, _ = layer(x_dict[nt].unsqueeze(0), x_dict[nt].unsqueeze(0), x_dict[nt].unsqueeze(0))
                    x_dict[nt] = F.elu(self.layer_norms[i](out.squeeze(0) + x_dict[nt]))

        src_emb = x_dict[src_type][src_nodes]
        dst_emb = x_dict[dst_type][dst_nodes]
        concat = torch.cat([src_emb, dst_emb], dim=-1)
        logits = self.decoder(concat).squeeze(-1)
        return logits


def build_model(model_name, data, hidden_dim=128, num_layers=3, dropout=0.3, **kwargs):
    """Factory function to build model."""
    models = {
        "rgcn": RGCNLinkPredictor,
        "hetgnn": HetGNNLinkPredictor,
    }
    if model_name not in models:
        raise ValueError(f"Unknown model: {model_name}. Choose from {list(models.keys())}")
    return models[model_name](data, hidden_dim=hidden_dim,
                              num_layers=num_layers, dropout=dropout, **kwargs)
