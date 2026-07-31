"""
Ablation Study Module.

Evaluates the contribution of each component:
1. w/o PPI edges (target-interacts_with-target)
2. w/o Drug nodes (drug-targets_protein-target, drug-treats-disease)
3. w/o Compound features (replace with random features)
4. w/o Target features (replace with random features)
5. 1-layer vs 2-layer vs 3-layer GNN
6. Dot product decoder vs MLP decoder
7. Different negative sampling ratios (1:1, 3:1, 5:1, 10:1)
"""
import os
import json
import copy
import numpy as np
import torch

from .config import *
from .graph_builder import HeterogeneousGraphBuilder
from .model import build_model, RGCNLinkPredictor, HetGNNLinkPredictor
from .train import Trainer


class AblationStudy:
    """Run systematic ablation experiments."""

    def __init__(self, results_dir=None):
        self.results_dir = results_dir or str(RESULTS_DIR / "ablation")
        os.makedirs(self.results_dir, exist_ok=True)
        self.results = {}

    def _build_graph_with_config(self, edge_config):
        """Build graph with specified edges removed."""
        builder = HeterogeneousGraphBuilder(str(DATA_DIR))
        builder.load_data()

        # Build edges based on config
        if edge_config.get("herb_compound", True):
            for herb_name, herb_info in builder.compounds_data["herbs"].items():
                for comp in herb_info["compounds"]:
                    builder._add_edge("herb", "contains", "compound",
                                      herb_name, comp["name"])

        if edge_config.get("compound_target", True):
            for comp in builder.cti_data["compounds"]:
                for target in comp["targets"]:
                    builder._add_edge("compound", "acts_on", "target",
                                      comp["name"], target)

        if edge_config.get("target_disease", True):
            for disease in builder.tda_data["diseases"]:
                for target in disease["associated_targets"]:
                    builder._add_edge("target", "associated_with", "disease",
                                      target, disease["name"])

        if edge_config.get("drug_target", True) and edge_config.get("drug_disease", True):
            drug_targets = {}
            for drug in builder.tda_data["drugbank_drugs_sharing_targets"]:
                for target in drug["targets"]:
                    if target in builder.node_maps.get("target", {}):
                        builder._add_edge("drug", "targets_protein", "target",
                                          drug["name"], target)
                drug_targets[drug["name"]] = set(drug["targets"])

            for drug_name, targets in drug_targets.items():
                for disease in builder.tda_data["diseases"]:
                    disease_targets = set(disease["associated_targets"])
                    if len(targets & disease_targets) >= 2:
                        builder._add_edge("drug", "treats", "disease",
                                          drug_name, disease["name"])

        if edge_config.get("ppi", True):
            for t1, t2 in builder._get_ppi_pairs():
                if t1 in builder.node_maps.get("target", {}) and t2 in builder.node_maps.get("target", {}):
                    builder._add_edge("target", "interacts_with", "target", t1, t2)

        if edge_config.get("compound_disease", True):
            builder._build_compound_disease_links()

        builder._build_features()
        graph = builder._to_dict_data()
        return graph, builder

    def _train_and_evaluate(self, graph_data, config_override=None, model_name="rgcn"):
        """Train model and return test metrics."""
        config = {
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "negative_sample_ratio": NEGATIVE_SAMPLE_RATIO,
            "results_dir": self.results_dir,
        }
        if config_override:
            config.update(config_override)

        model = build_model(
            model_name, graph_data,
            hidden_dim=config_override.get("hidden_dim", HIDDEN_DIM) if config_override else HIDDEN_DIM,
            num_layers=config_override.get("num_layers", NUM_GNN_LAYERS) if config_override else NUM_GNN_LAYERS,
            dropout=DROPOUT,
        )

        trainer = Trainer(model, graph_data, config)
        test_metrics, _ = trainer.train(
            num_epochs=50,
            patience=15,
            verbose=False,
        )
        return test_metrics

    def run_all_ablations(self):
        """Run all ablation experiments."""
        print("=" * 70)
        print("  ABLATION STUDY")
        print("=" * 70)

        # === 1. Full model (baseline) ===
        print("\n[1/7] Full HetGNN model (baseline)...")
        full_config = {"herb_compound": True, "compound_target": True,
                       "target_disease": True, "drug_target": True,
                       "drug_disease": True, "ppi": True, "compound_disease": True}
        full_graph, _ = self._build_graph_with_config(full_config)
        full_metrics = self._train_and_evaluate(full_graph, model_name="hetgnn")
        self.results["Full model (HetGNN)"] = full_metrics
        print(f"  AUC: {full_metrics['auc']:.4f}, AUPRC: {full_metrics['auprc']:.4f}")

        # === 2. w/o PPI edges ===
        print("\n[2/7] w/o PPI edges...")
        no_ppi = copy.deepcopy(full_config)
        no_ppi["ppi"] = False
        no_ppi_graph, _ = self._build_graph_with_config(no_ppi)
        no_ppi_metrics = self._train_and_evaluate(no_ppi_graph, model_name="hetgnn")
        self.results["w/o PPI edges"] = no_ppi_metrics
        print(f"  AUC: {no_ppi_metrics['auc']:.4f}, AUPRC: {no_ppi_metrics['auprc']:.4f}")

        # === 3. w/o Drug bridge nodes ===
        print("\n[3/7] w/o Drug bridge nodes...")
        no_drug = copy.deepcopy(full_config)
        no_drug["drug_target"] = False
        no_drug["drug_disease"] = False
        no_drug_graph, _ = self._build_graph_with_config(no_drug)
        no_drug_metrics = self._train_and_evaluate(no_drug_graph, model_name="hetgnn")
        self.results["w/o Drug nodes"] = no_drug_metrics
        print(f"  AUC: {no_drug_metrics['auc']:.4f}, AUPRC: {no_drug_metrics['auprc']:.4f}")

        # === 4. w/o Herb layer (only compound-target-disease) ===
        print("\n[4/7] w/o Herb nodes...")
        no_herb = copy.deepcopy(full_config)
        no_herb["herb_compound"] = False
        no_herb_graph, _ = self._build_graph_with_config(no_herb)
        no_herb_metrics = self._train_and_evaluate(no_herb_graph, model_name="hetgnn")
        self.results["w/o Herb nodes"] = no_herb_metrics
        print(f"  AUC: {no_herb_metrics['auc']:.4f}, AUPRC: {no_herb_metrics['auprc']:.4f}")

        # === 5. 1-layer GNN ===
        print("\n[5/7] 1-layer HetGNN...")
        layer1_metrics = self._train_and_evaluate(
            full_graph, config_override={"num_layers": 1}, model_name="hetgnn")
        self.results["1-layer HetGNN"] = layer1_metrics
        print(f"  AUC: {layer1_metrics['auc']:.4f}, AUPRC: {layer1_metrics['auprc']:.4f}")

        # === 6. 2-layer GNN ===
        print("\n[6/7] 2-layer HetGNN...")
        layer2_metrics = self._train_and_evaluate(
            full_graph, config_override={"num_layers": 2}, model_name="hetgnn")
        self.results["2-layer HetGNN"] = layer2_metrics
        print(f"  AUC: {layer2_metrics['auc']:.4f}, AUPRC: {layer2_metrics['auprc']:.4f}")

        # === 7. R-GCN instead of HetGNN ===
        print("\n[7/7] R-GCN (instead of HetGNN)...")
        rgcn_metrics = self._train_and_evaluate(full_graph, model_name="rgcn")
        self.results["R-GCN (full graph)"] = rgcn_metrics
        print(f"  AUC: {rgcn_metrics['auc']:.4f}, AUPRC: {rgcn_metrics['auprc']:.4f}")

        # Save results
        self._save_results()
        self._print_summary()

        return self.results

    def _save_results(self):
        """Save ablation results to JSON."""
        # Convert metrics to serializable format
        serializable = {}
        for name, metrics in self.results.items():
            serializable[name] = {k: float(v) for k, v in metrics.items()}

        output_path = os.path.join(self.results_dir, "ablation_results.json")
        with open(output_path, "w") as f:
            json.dump(serializable, f, indent=2)
        print(f"\nAblation results saved to {output_path}")

    def _print_summary(self):
        """Print formatted ablation summary table."""
        print(f"\n{'='*70}")
        print("  ABLATION STUDY SUMMARY")
        print(f"{'='*70}")
        print(f"{'Configuration':<30} {'AUC-ROC':>10} {'AUPRC':>10} {'Accuracy':>10}")
        print(f"{'-'*60}")

        for name, metrics in self.results.items():
            print(f"{name:<30} {metrics['auc']:>10.4f} {metrics['auprc']:>10.4f} {metrics['accuracy']:>10.4f}")

        print(f"{'='*70}")


class NegativeSamplingStudy:
    """Study the effect of different negative sampling ratios."""

    def __init__(self, results_dir=None):
        self.results_dir = results_dir or str(RESULTS_DIR / "ablation")
        os.makedirs(self.results_dir, exist_ok=True)

    def run(self):
        """Test different negative sampling ratios."""
        print("\n" + "=" * 70)
        print("  NEGATIVE SAMPLING RATIO STUDY")
        print("=" * 70)

        builder = HeterogeneousGraphBuilder(str(DATA_DIR))
        graph_data = builder.build_graph()

        ratios = [1, 3, 5, 10]
        results = {}

        for ratio in ratios:
            print(f"\n  Ratio {ratio}:1 (negative:positive)...")
            config = {
                "learning_rate": LEARNING_RATE,
                "weight_decay": WEIGHT_DECAY,
                "negative_sample_ratio": ratio,
                "results_dir": self.results_dir,
            }

            model = build_model("hetgnn", graph_data,
                                hidden_dim=HIDDEN_DIM, num_layers=NUM_GNN_LAYERS,
                                dropout=DROPOUT)
            trainer = Trainer(model, graph_data, config)
            test_metrics, _ = trainer.train(num_epochs=50, patience=15, verbose=False)
            results[f"neg_ratio_{ratio}"] = test_metrics
            print(f"    AUC: {test_metrics['auc']:.4f}, AUPRC: {test_metrics['auprc']:.4f}")

        output_path = os.path.join(self.results_dir, "neg_sampling_study.json")
        with open(output_path, "w") as f:
            json.dump({k: {m: float(v) for m, v in met.items()}
                       for k, met in results.items()}, f, indent=2)

        return results
