"""
Predictor: Drug repurposing predictions for Guizhi Tang.

Generates ranked list of compound-disease predictions,
with pathway analysis and target enrichment.
"""
import os
import json
import numpy as np
import torch
from collections import defaultdict


class DrugRepurposingPredictor:
    """Generate drug repurposing predictions from trained GNN model."""

    def __init__(self, model, graph_data, node_maps, results_dir="results"):
        self.model = model
        self.graph = graph_data
        self.node_maps = node_maps
        self.reverse_maps = {
            nt: {v: k for k, v in nm.items()}
            for nt, nm in node_maps.items()
        }
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)

    @torch.no_grad()
    def predict_all(self, top_k=20, threshold=0.5):
        """
        Predict all possible compound-disease links and rank them.

        Returns ranked predictions with scores.
        """
        self.model.eval()
        n_compounds = self._get_num_nodes("compound")
        n_diseases = self._get_num_nodes("disease")

        # Get existing edges to exclude
        existing_edges = self._get_existing_edges()

        predictions = []
        batch_size = 256

        for c in range(n_compounds):
            src_batch = []
            dst_batch = []
            for d in range(n_diseases):
                if (c, d) not in existing_edges:
                    src_batch.append(c)
                    dst_batch.append(d)

                if len(src_batch) >= batch_size or d == n_diseases - 1:
                    if src_batch:
                        src_tensor = torch.tensor(src_batch, dtype=torch.long)
                        dst_tensor = torch.tensor(dst_batch, dtype=torch.long)
                        logits = self.model(self.graph, src_tensor, dst_tensor)
                        probs = torch.sigmoid(logits).cpu().numpy()

                        for s, dt, p in zip(src_batch, dst_batch, probs):
                            if p >= threshold:
                                comp_name = self.reverse_maps.get("compound", {}).get(s, f"compound_{s}")
                                dis_name = self.reverse_maps.get("disease", {}).get(dt, f"disease_{dt}")
                                predictions.append({
                                    "compound_idx": s,
                                    "compound": comp_name,
                                    "disease_idx": dt,
                                    "disease": dis_name,
                                    "score": float(p),
                                })

                        src_batch = []
                        dst_batch = []

        # Sort by score descending
        predictions.sort(key=lambda x: x["score"], reverse=True)

        # Save top-K
        top_predictions = predictions[:top_k]
        with open(os.path.join(self.results_dir, "top_predictions.json"), "w", encoding="utf-8") as f:
            json.dump(top_predictions, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*60}")
        print(f"Top {min(top_k, len(top_predictions))} Drug Repurposing Predictions")
        print(f"{'='*60}")
        print(f"{'Rank':<5} {'Compound':<25} {'Disease':<30} {'Score':<8}")
        print(f"{'-'*68}")
        for i, pred in enumerate(top_predictions):
            print(f"{i+1:<5} {pred['compound']:<25} {pred['disease']:<30} {pred['score']:.4f}")
        print(f"{'='*60}")

        return top_predictions

    def _get_num_nodes(self, node_type):
        if hasattr(self.graph, 'node_types'):
            return self.graph[node_type].num_nodes
        elif isinstance(self.graph, dict):
            return len(self.graph.get("node_maps", {}).get(node_type, {}))
        return 0

    def _get_existing_edges(self):
        edges_key = ("compound", "may_treat", "disease")
        existing = set()
        if hasattr(self.graph, 'edge_index_dict'):
            ei = self.graph[edges_key].edge_index
            for i in range(ei.shape[1]):
                existing.add((ei[0, i].item(), ei[1, i].item()))
        elif isinstance(self.graph, dict):
            for src, dst in self.graph.get("edges", {}).get(edges_key, []):
                existing.add((src, dst))
        return existing

    def analyze_prediction_paths(self, predictions, top_n=5):
        """
        Analyze the compound->target->disease paths for top predictions.
        Provides mechanistic interpretation.
        """
        # Load target data for path analysis
        from .config import DATA_DIR
        cti_path = os.path.join(str(DATA_DIR), "compound_target_interactions.json")
        tda_path = os.path.join(str(DATA_DIR), "target_disease_associations.json")

        try:
            with open(cti_path, "r", encoding="utf-8") as f:
                cti = json.load(f)
            with open(tda_path, "r", encoding="utf-8") as f:
                tda = json.load(f)
        except FileNotFoundError:
            print("[WARNING] Data files not found for path analysis.")
            return []

        # Build lookup maps
        comp_targets = {}
        for comp in cti["compounds"]:
            comp_targets[comp["name"]] = set(comp["targets"])

        disease_targets = {}
        for dis in tda["diseases"]:
            disease_targets[dis["name"]] = set(dis["associated_targets"])

        path_analysis = []
        for pred in predictions[:top_n]:
            comp = pred["compound"]
            disease = pred["disease"]
            c_targets = comp_targets.get(comp, set())
            d_targets = disease_targets.get(disease, set())
            shared = c_targets & d_targets

            path_analysis.append({
                "compound": comp,
                "disease": disease,
                "score": pred["score"],
                "compound_targets": sorted(c_targets),
                "disease_targets": sorted(d_targets),
                "shared_targets": sorted(shared),
                "num_shared": len(shared),
                "path_description": (
                    f"{comp} acts on {len(c_targets)} targets, "
                    f"{disease} involves {len(d_targets)} targets. "
                    f"Shared targets ({len(shared)}): {', '.join(sorted(shared))}"
                ),
            })

        with open(os.path.join(self.results_dir, "path_analysis.json"), "w", encoding="utf-8") as f:
            json.dump(path_analysis, f, indent=2, ensure_ascii=False)

        print(f"\n{'='*60}")
        print("Mechanistic Path Analysis (Top 5 Predictions)")
        print(f"{'='*60}")
        for pa in path_analysis:
            print(f"\n{pa['compound']} -> {pa['disease']} (score: {pa['score']:.4f})")
            print(f"  Shared targets ({pa['num_shared']}): {', '.join(pa['shared_targets'])}")

        return path_analysis

    def generate_summary(self, predictions, path_analysis):
        """Generate a summary report for the paper."""
        summary = {
            "total_predictions": len(predictions),
            "top_score": predictions[0]["score"] if predictions else 0,
            "mean_score": np.mean([p["score"] for p in predictions]) if predictions else 0,
            "unique_compounds": len(set(p["compound"] for p in predictions)),
            "unique_diseases": len(set(p["disease"] for p in predictions)),
            "top_compounds": self._rank_compounds(predictions),
            "top_diseases": self._rank_diseases(predictions),
        }

        with open(os.path.join(self.results_dir, "prediction_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    def _rank_compounds(self, predictions):
        """Rank compounds by average prediction score."""
        comp_scores = defaultdict(list)
        for p in predictions:
            comp_scores[p["compound"]].append(p["score"])
        ranked = [(c, np.mean(s), len(s)) for c, s in comp_scores.items()]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return [{"compound": c, "avg_score": float(s), "n_predictions": n} for c, s, n in ranked[:10]]

    def _rank_diseases(self, predictions):
        """Rank diseases by average prediction score."""
        dis_scores = defaultdict(list)
        for p in predictions:
            dis_scores[p["disease"]].append(p["score"])
        ranked = [(d, np.mean(s), len(s)) for d, s in dis_scores.items()]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return [{"disease": d, "avg_score": float(s), "n_predictions": n} for d, s, n in ranked[:10]]
