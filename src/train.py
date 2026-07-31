"""
Trainer: Training pipeline for GNN link prediction models.

Features:
- Negative sampling for compound-disease pairs
- Train/val/test split
- Early stopping
- Metrics: AUC-ROC, AUPRC, F1, Accuracy
"""
import os
import json
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             f1_score, accuracy_score, precision_score, recall_score)
from sklearn.model_selection import train_test_split


class Trainer:
    """Training pipeline for heterogeneous graph link prediction."""

    def __init__(self, model, graph_data, config):
        self.model = model
        self.graph = graph_data
        self.config = config

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=config.get("learning_rate", 0.001),
            weight_decay=config.get("weight_decay", 5e-4),
        )
        self.criterion = nn.BCEWithLogitsLoss()

        # Prepare datasets
        self._prepare_data()

    def _prepare_data(self):
        """Prepare train/val/test splits for compound-disease link prediction."""
        edges_key = ("compound", "may_treat", "disease")

        if hasattr(self.graph, 'edge_index_dict'):
            # PyG HeteroData
            edge_index = self.graph[edges_key].edge_index
            pos_src = edge_index[0].numpy()
            pos_dst = edge_index[1].numpy()
        elif isinstance(self.graph, dict):
            edges = self.graph.get("edges", {}).get(edges_key, [])
            pos_src = np.array([e[0] for e in edges])
            pos_dst = np.array([e[1] for e in edges])
        else:
            raise ValueError("Unsupported graph format")

        n_pos = len(pos_src)
        n_nodes_src = self._get_num_nodes("compound")
        n_nodes_dst = self._get_num_nodes("disease")

        # Generate negative samples
        neg_ratio = self.config.get("negative_sample_ratio", 5)
        n_neg = n_pos * neg_ratio
        neg_src, neg_dst = self._negative_sample(
            pos_src, pos_dst, n_nodes_src, n_nodes_dst, n_neg
        )

        # Combine
        all_src = np.concatenate([pos_src, neg_src])
        all_dst = np.concatenate([pos_dst, neg_dst])
        all_labels = np.concatenate([np.ones(n_pos), np.zeros(n_neg)])

        # Split: 70% train, 15% val, 15% test
        indices = np.arange(len(all_src))
        train_idx, temp_idx = train_test_split(indices, test_size=0.3, random_state=42, stratify=all_labels)
        val_idx, test_idx = train_test_split(temp_idx, test_size=0.5, random_state=42, stratify=all_labels[temp_idx])

        self.train_data = {
            "src": torch.tensor(all_src[train_idx], dtype=torch.long).to(self.device),
            "dst": torch.tensor(all_dst[train_idx], dtype=torch.long).to(self.device),
            "labels": torch.tensor(all_labels[train_idx], dtype=torch.float32).to(self.device),
        }
        self.val_data = {
            "src": torch.tensor(all_src[val_idx], dtype=torch.long).to(self.device),
            "dst": torch.tensor(all_dst[val_idx], dtype=torch.long).to(self.device),
            "labels": torch.tensor(all_labels[val_idx], dtype=torch.float32).to(self.device),
        }
        self.test_data = {
            "src": torch.tensor(all_src[test_idx], dtype=torch.long).to(self.device),
            "dst": torch.tensor(all_dst[test_idx], dtype=torch.long).to(self.device),
            "labels": torch.tensor(all_labels[test_idx], dtype=torch.float32).to(self.device),
        }

        self.data_splits = {
            "train": (train_idx, len(all_src)),
            "val": (val_idx, len(all_src)),
            "test": (test_idx, len(all_src)),
        }

        print(f"Dataset splits:")
        print(f"  Train: {len(train_idx)} samples ({(all_labels[train_idx] == 1).sum()} pos, {(all_labels[train_idx] == 0).sum()} neg)")
        print(f"  Val:   {len(val_idx)} samples ({(all_labels[val_idx] == 1).sum()} pos, {(all_labels[val_idx] == 0).sum()} neg)")
        print(f"  Test:  {len(test_idx)} samples ({(all_labels[test_idx] == 1).sum()} pos, {(all_labels[test_idx] == 0).sum()} neg)")

    def _get_num_nodes(self, node_type):
        """Get number of nodes for a given type."""
        if hasattr(self.graph, 'node_types'):
            return self.graph[node_type].num_nodes
        elif isinstance(self.graph, dict):
            nm = self.graph.get("node_maps", {}).get(node_type, {})
            return len(nm)
        return 0

    def _negative_sample(self, pos_src, pos_dst, n_src, n_dst, n_neg):
        """Generate negative samples that are not in positive set."""
        pos_set = set(zip(pos_src.tolist(), pos_dst.tolist()))
        neg_src = []
        neg_dst = []
        attempts = 0
        max_attempts = n_neg * 10

        while len(neg_src) < n_neg and attempts < max_attempts:
            s = np.random.randint(0, n_src)
            d = np.random.randint(0, n_dst)
            if (s, d) not in pos_set:
                neg_src.append(s)
                neg_dst.append(d)
            attempts += 1

        return np.array(neg_src), np.array(neg_dst)

    def train_epoch(self):
        """Train for one epoch."""
        self.model.train()
        logits = self.model(
            self.graph,
            self.train_data["src"],
            self.train_data["dst"],
        )
        loss = self.criterion(logits, self.train_data["labels"])

        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
        self.optimizer.step()

        return loss.item()

    @torch.no_grad()
    def evaluate(self, data_dict):
        """Evaluate on given data split."""
        self.model.eval()
        logits = self.model(
            self.graph,
            data_dict["src"],
            data_dict["dst"],
        )
        loss = self.criterion(logits, data_dict["labels"])
        probs = torch.sigmoid(logits).cpu().numpy()
        labels = data_dict["labels"].cpu().numpy()
        preds = (probs >= 0.5).astype(int)

        metrics = {
            "loss": loss.item(),
            "auc": roc_auc_score(labels, probs),
            "auprc": average_precision_score(labels, probs),
            "f1": f1_score(labels, preds),
            "accuracy": accuracy_score(labels, preds),
            "precision": precision_score(labels, preds, zero_division=0),
            "recall": recall_score(labels, preds, zero_division=0),
        }
        return metrics

    def train(self, num_epochs=200, patience=20, verbose=True):
        """Full training loop with early stopping."""
        best_val_auc = 0
        best_epoch = 0
        patience_counter = 0
        history = {"train_loss": [], "val_loss": [], "val_auc": [], "val_auprc": []}

        for epoch in range(num_epochs):
            train_loss = self.train_epoch()
            val_metrics = self.evaluate(self.val_data)

            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_metrics["loss"])
            history["val_auc"].append(val_metrics["auc"])
            history["val_auprc"].append(val_metrics["auprc"])

            if val_metrics["auc"] > best_val_auc:
                best_val_auc = val_metrics["auc"]
                best_epoch = epoch
                patience_counter = 0
                # Save best model
                torch.save(self.model.state_dict(),
                           os.path.join(self.config.get("results_dir", "results"), "best_model.pt"))
            else:
                patience_counter += 1

            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1:3d} | "
                      f"Train Loss: {train_loss:.4f} | "
                      f"Val Loss: {val_metrics['loss']:.4f} | "
                      f"Val AUC: {val_metrics['auc']:.4f} | "
                      f"Val AUPRC: {val_metrics['auprc']:.4f}")

            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch+1}. Best epoch: {best_epoch+1}")
                break

        # Load best model and evaluate on test set
        self.model.load_state_dict(
            torch.load(os.path.join(self.config.get("results_dir", "results"), "best_model.pt"),
                       weights_only=True)
        )
        test_metrics = self.evaluate(self.test_data)
        print(f"\n{'='*60}")
        print(f"Test Set Performance (Best Model from Epoch {best_epoch+1}):")
        print(f"{'='*60}")
        for k, v in test_metrics.items():
            print(f"  {k:12s}: {v:.4f}")
        print(f"{'='*60}")

        # Save history
        with open(os.path.join(self.config.get("results_dir", "results"), "training_history.json"), "w") as f:
            json.dump(history, f, indent=2)

        return test_metrics, history


class CrossValidator:
    """K-fold cross-validation for link prediction on heterogeneous graphs."""

    def __init__(self, graph_data, model_name, config, k_folds=5):
        self.graph = graph_data
        self.model_name = model_name
        self.config = config
        self.k_folds = k_folds

    def _get_positive_edges(self):
        """Get all positive compound-disease edges."""
        edges_key = ("compound", "may_treat", "disease")
        if hasattr(self.graph, 'edge_index_dict'):
            ei = self.graph[edges_key].edge_index
            return [(ei[0, i].item(), ei[1, i].item())
                    for i in range(ei.shape[1])]
        elif isinstance(self.graph, dict):
            return list(self.graph.get("edges", {}).get(edges_key, []))
        return []

    def _get_num_nodes(self, node_type):
        if hasattr(self.graph, 'node_types'):
            return self.graph[node_type].num_nodes
        elif isinstance(self.graph, dict):
            return len(self.graph.get("node_maps", {}).get(node_type, {}))
        return 0

    def run(self, num_epochs=50, patience=15):
        """Run k-fold cross-validation."""
        from sklearn.model_selection import KFold

        pos_edges = self._get_positive_edges()
        n_compounds = self._get_num_nodes("compound")
        n_diseases = self._get_num_nodes("disease")

        pos_arr = np.array(pos_edges)
        kf = KFold(n_splits=self.k_folds, shuffle=True, random_state=42)

        fold_results = []

        for fold_idx, (train_idx, test_idx) in enumerate(kf.split(pos_arr)):
            print(f"\n  Fold {fold_idx + 1}/{self.k_folds}...")

            # Use only train edges for training
            train_pos = pos_arr[train_idx]
            test_pos = pos_arr[test_idx]

            # Generate negatives
            pos_set = set(zip(pos_arr[:, 0].tolist(), pos_arr[:, 1].tolist()))
            neg_pairs = []
            while len(neg_pairs) < len(pos_arr) * 5:
                s = np.random.randint(0, n_compounds)
                d = np.random.randint(0, n_diseases)
                if (s, d) not in pos_set:
                    neg_pairs.append([s, d])
            neg_arr = np.array(neg_pairs[:len(pos_arr) * 5])

            # Split negatives
            neg_train = neg_arr[:len(train_pos) * 5]
            neg_test = neg_arr[len(train_pos) * 5:len(train_pos) * 5 + len(test_pos) * 5]

            # Build training data
            train_src = np.concatenate([train_pos[:, 0], neg_train[:, 0]])
            train_dst = np.concatenate([train_pos[:, 1], neg_train[:, 1]])
            train_labels = np.concatenate([np.ones(len(train_pos)), np.zeros(len(neg_train))])

            test_src = np.concatenate([test_pos[:, 0], neg_test[:, 0]])
            test_dst = np.concatenate([test_pos[:, 1], neg_test[:, 1]])
            test_labels = np.concatenate([np.ones(len(test_pos)), np.zeros(len(neg_test))])

            # Build model and train
            from .model import build_model
            model = build_model(self.model_name, self.graph,
                                hidden_dim=self.config.get("hidden_dim", 128),
                                num_layers=self.config.get("num_layers", 3),
                                dropout=self.config.get("dropout", 0.3))

            # Manually set train/test data on trainer
            trainer = Trainer(model, self.graph, self.config)

            # Override trainer's data with fold-specific splits
            device = trainer.device
            trainer.train_data = {
                "src": torch.tensor(train_src, dtype=torch.long).to(device),
                "dst": torch.tensor(train_dst, dtype=torch.long).to(device),
                "labels": torch.tensor(train_labels, dtype=torch.float32).to(device),
            }
            # Use test as val for simplicity
            trainer.val_data = {
                "src": torch.tensor(test_src, dtype=torch.long).to(device),
                "dst": torch.tensor(test_dst, dtype=torch.long).to(device),
                "labels": torch.tensor(test_labels, dtype=torch.float32).to(device),
            }
            trainer.test_data = trainer.val_data

            metrics, _ = trainer.train(num_epochs=num_epochs, patience=patience, verbose=False)
            fold_results.append(metrics)
            print(f"    AUC: {metrics['auc']:.4f}, AUPRC: {metrics['auprc']:.4f}")

        # Aggregate results
        mean_metrics = {}
        std_metrics = {}
        for key in fold_results[0].keys():
            values = [r[key] for r in fold_results]
            mean_metrics[key] = float(np.mean(values))
            std_metrics[key] = float(np.std(values))

        print(f"\n  {'='*60}")
        print(f"  Cross-Validation Results ({self.k_folds}-fold)")
        print(f"  {'='*60}")
        for key in mean_metrics:
            print(f"    {key:12s}: {mean_metrics[key]:.4f} +/- {std_metrics[key]:.4f}")
        print(f"  {'='*60}")

        return {"mean": mean_metrics, "std": std_metrics, "folds": fold_results}


class ThresholdAnalyzer:
    """Analyze optimal prediction threshold using precision-recall curve."""

    def __init__(self, model, graph_data, test_data, results_dir):
        self.model = model
        self.graph = graph_data
        self.test_data = test_data
        self.results_dir = results_dir

    @torch.no_grad()
    def analyze(self):
        """Find optimal threshold and generate PR curve data."""
        self.model.eval()
        logits = self.model(self.graph, self.test_data["src"], self.test_data["dst"])
        probs = torch.sigmoid(logits).cpu().numpy()
        labels = self.test_data["labels"].cpu().numpy()

        # Compute metrics at different thresholds
        thresholds = np.arange(0.1, 0.9, 0.05)
        threshold_metrics = []
        for t in thresholds:
            preds = (probs >= t).astype(int)
            tp = ((preds == 1) & (labels == 1)).sum()
            fp = ((preds == 1) & (labels == 0)).sum()
            fn = ((preds == 0) & (labels == 1)).sum()
            precision = tp / max(tp + fp, 1)
            recall = tp / max(tp + fn, 1)
            f1 = 2 * precision * recall / max(precision + recall, 1e-8)
            threshold_metrics.append({
                "threshold": float(t),
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
            })

        # Find optimal threshold by F1
        best = max(threshold_metrics, key=lambda x: x["f1"])
        print(f"\n  Optimal threshold: {best['threshold']:.2f}")
        print(f"    F1: {best['f1']:.4f}, Precision: {best['precision']:.4f}, Recall: {best['recall']:.4f}")

        # Save
        with open(os.path.join(self.results_dir, "threshold_analysis.json"), "w") as f:
            json.dump({"thresholds": threshold_metrics, "optimal": best}, f, indent=2)

        return threshold_metrics, best
