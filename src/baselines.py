"""
Baseline Models for comparison with GNN approaches.

Implements:
1. MLP baseline (no graph structure)
2. Simple GCN on homogeneous graph (ignoring edge types)
3. Node2Vec-style random walk embeddings + MLP classifier
"""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score


class MLPBaseline(nn.Module):
    """
    MLP baseline that uses only node features (no graph structure).
    Concatenates compound and disease features for classification.
    """
    def __init__(self, compound_dim, disease_dim, hidden_dim=128, dropout=0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(compound_dim + disease_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, compound_feats, disease_feats):
        x = torch.cat([compound_feats, disease_feats], dim=-1)
        return self.net(x).squeeze(-1)


class SimpleGCN(nn.Module):
    """
    Simple GCN that treats all edges as the same type (homogeneous graph).
    Uses adjacency matrix multiplication for message passing.
    """
    def __init__(self, input_dim, hidden_dim=128, num_layers=3, dropout=0.3):
        super().__init__()
        self.layers = nn.ModuleList()
        self.norms = nn.ModuleList()

        # First layer
        self.layers.append(nn.Linear(input_dim, hidden_dim))
        self.norms.append(nn.LayerNorm(hidden_dim))

        # Hidden layers
        for _ in range(num_layers - 1):
            self.layers.append(nn.Linear(hidden_dim, hidden_dim))
            self.norms.append(nn.LayerNorm(hidden_dim))

        self.dropout = dropout

        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def _build_adjacency(self, edges_dict, num_nodes):
        """Build normalized adjacency matrix from all edges."""
        adj = torch.zeros(num_nodes, num_nodes)
        for edge_key, edge_list in edges_dict.items():
            for src, dst in edge_list:
                if src < num_nodes and dst < num_nodes:
                    adj[src][dst] = 1.0
                    adj[dst][src] = 1.0  # make undirected

        # Symmetric normalization: D^{-1/2} A D^{-1/2}
        deg = adj.sum(dim=1) + 1e-8
        d_inv_sqrt = torch.diag(1.0 / torch.sqrt(deg))
        adj_norm = d_inv_sqrt @ adj @ d_inv_sqrt

        # Add self-loops
        adj_norm = adj_norm + torch.eye(num_nodes)
        return adj_norm

    def forward(self, node_features, adj_matrix, src_indices, dst_indices):
        """Forward pass with adjacency matrix message passing."""
        x = node_features
        for i, (layer, norm) in enumerate(zip(self.layers, self.norms)):
            x = adj_matrix @ x  # message passing
            x = layer(x)
            x = norm(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        src_emb = x[src_indices]
        dst_emb = x[dst_indices]
        concat = torch.cat([src_emb, dst_emb], dim=-1)
        return self.decoder(concat).squeeze(-1)


class Node2VecBaseline:
    """
    Node2Vec-style baseline using random walk embeddings + Logistic Regression.
    Simplified implementation without requiring the node2vec package.
    """
    def __init__(self, embedding_dim=64, walk_length=10, num_walks=20):
        self.embedding_dim = embedding_dim
        self.walk_length = walk_length
        self.num_walks = num_walks

    def _build_adjacency_list(self, edges_dict, node_maps):
        """Build adjacency list from heterogeneous edges."""
        adj_list = {}
        # Assign global node IDs
        global_offset = {}
        offset = 0
        for nt, nm in node_maps.items():
            global_offset[nt] = offset
            offset += len(nm)

        self.total_nodes = offset
        self.global_offset = global_offset

        for edge_key, edge_list in edges_dict.items():
            src_type, rel, dst_type = edge_key
            for src_local, dst_local in edge_list:
                src_global = global_offset[src_type] + src_local
                dst_global = global_offset[dst_type] + dst_local
                adj_list.setdefault(src_global, []).append(dst_global)
                adj_list.setdefault(dst_global, []).append(src_global)

        return adj_list

    def _random_walks(self, adj_list, num_nodes):
        """Generate random walk co-occurrence matrix."""
        cooccurrence = np.zeros((num_nodes, num_nodes))

        for start in range(num_nodes):
            for _ in range(self.num_walks):
                walk = [start]
                current = start
                for _ in range(self.walk_length):
                    neighbors = adj_list.get(current, [])
                    if not neighbors:
                        break
                    current = np.random.choice(neighbors)
                    walk.append(current)

                # Update co-occurrence with window
                for i, node_i in enumerate(walk):
                    for j in range(max(0, i-5), min(len(walk), i+6)):
                        if i != j:
                            cooccurrence[node_i][walk[j]] += 1

        return cooccurrence

    def fit_predict(self, graph_data, train_src, train_dst, train_labels,
                    test_src, test_dst, test_labels, node_maps):
        """Train and evaluate using random walk embeddings + LR."""
        edges_dict = graph_data.get("edges", {})
        adj_list = self._build_adjacency_list(edges_dict, node_maps)

        # Generate embeddings via SVD on co-occurrence matrix
        cooc = self._random_walks(adj_list, self.total_nodes)
        # Add small constant to avoid log(0)
        cooc = np.log(cooc + 1)

        U, S, Vt = np.linalg.svd(cooc, full_matrices=False)
        embeddings = U[:, :self.embedding_dim] * np.sqrt(S[:self.embedding_dim])

        # Build training features
        off_c = self.global_offset.get("compound", 0)
        off_d = self.global_offset.get("disease", 0)

        X_train = np.concatenate([
            embeddings[train_src + off_c],
            embeddings[test_src + off_c] if len(test_src) > 0 else np.zeros((0, self.embedding_dim))
        ], axis=0) if len(train_src) > 0 else np.zeros((0, self.embedding_dim * 2))

        # Actually build proper feature vectors
        X_train_list = []
        y_train_list = []
        for s, d, l in zip(train_src, train_dst, train_labels):
            feat = np.concatenate([embeddings[s + off_c], embeddings[d + off_d]])
            X_train_list.append(feat)
            y_train_list.append(l)

        X_test_list = []
        y_test_list = []
        for s, d, l in zip(test_src, test_dst, test_labels):
            feat = np.concatenate([embeddings[s + off_c], embeddings[d + off_d]])
            X_test_list.append(feat)
            y_test_list.append(l)

        if not X_train_list:
            return {"auc": 0.5, "auprc": 0.5, "accuracy": 0.5, "f1": 0.0,
                    "precision": 0.0, "recall": 0.0, "loss": 0.5}

        X_train = np.array(X_train_list)
        y_train = np.array(y_train_list)
        X_test = np.array(X_test_list)
        y_test = np.array(y_test_list)

        clf = LogisticRegression(max_iter=1000, class_weight='balanced')
        clf.fit(X_train, y_train)

        probs = clf.predict_proba(X_test)[:, 1]
        preds = clf.predict(X_test)

        metrics = {
            "auc": roc_auc_score(y_test, probs) if len(np.unique(y_test)) > 1 else 0.5,
            "auprc": average_precision_score(y_test, probs),
            "accuracy": (preds == y_test).mean(),
            "f1": (2 * (preds == 1).sum() * (y_test == 1).sum() /
                   max((preds == 1).sum() + (y_test == 1).sum(), 1)) if (preds == 1).any() else 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "loss": 0.5,
        }

        # Compute precision/recall properly
        tp = ((preds == 1) & (y_test == 1)).sum()
        fp = ((preds == 1) & (y_test == 0)).sum()
        fn = ((preds == 0) & (y_test == 1)).sum()
        metrics["precision"] = tp / max(tp + fp, 1)
        metrics["recall"] = tp / max(tp + fn, 1)
        metrics["f1"] = 2 * metrics["precision"] * metrics["recall"] / max(metrics["precision"] + metrics["recall"], 1e-8)

        return metrics
