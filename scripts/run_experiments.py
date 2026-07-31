"""
Run all experiments: baselines, ablations, cross-validation, threshold analysis.

Usage:
    python run_experiments.py [--skip-ablation] [--skip-cv] [--skip-baselines]
"""
import os
import sys
import json
import argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import *
from src.graph_builder import HeterogeneousGraphBuilder
from src.model import build_model
from src.train import Trainer, CrossValidator, ThresholdAnalyzer
from src.baselines import MLPBaseline, SimpleGCN, Node2VecBaseline
from src.ablation import AblationStudy, NegativeSamplingStudy
from src.visualize import generate_all_figures, generate_figures_from_results


def parse_args():
    parser = argparse.ArgumentParser(description="Run all experiments")
    parser.add_argument("--skip-ablation", action="store_true")
    parser.add_argument("--skip-cv", action="store_true")
    parser.add_argument("--skip-baselines", action="store_true")
    parser.add_argument("--skip-neg-study", action="store_true")
    parser.add_argument("--results-dir", type=str, default=str(RESULTS_DIR))
    return parser.parse_args()


def run_baselines(graph_data, config, results_dir):
    """Run baseline models for comparison."""
    print("\n" + "=" * 70)
    print("  BASELINE MODEL COMPARISON")
    print("=" * 70)

    node_maps = graph_data.get("node_maps", {})
    edges = graph_data.get("edges", {})
    node_features = graph_data.get("node_features", {})
    results = {}

    # 1. MLP Baseline
    print("\n[1/3] MLP Baseline (no graph structure)...")
    comp_dim = node_features.get("compound", np.zeros((1, 4))).shape[1]
    dis_dim = node_features.get("disease", np.zeros((1, 2))).shape[1]
    mlp = MLPBaseline(comp_dim, dis_dim, hidden_dim=128)

    # Prepare data same way as Trainer
    edges_key = ("compound", "may_treat", "disease")
    pos_edges = edges.get(edges_key, [])
    n_compounds = len(node_maps.get("compound", {}))
    n_diseases = len(node_maps.get("disease", {}))

    pos_src = np.array([e[0] for e in pos_edges])
    pos_dst = np.array([e[1] for e in pos_edges])

    # Generate negatives
    pos_set = set(zip(pos_src.tolist(), pos_dst.tolist()))
    neg_pairs = []
    while len(neg_pairs) < len(pos_edges) * 5:
        s = np.random.randint(0, n_compounds)
        d = np.random.randint(0, n_diseases)
        if (s, d) not in pos_set:
            neg_pairs.append([s, d])
    neg_arr = np.array(neg_pairs)

    all_src = np.concatenate([pos_src, neg_arr[:, 0]])
    all_dst = np.concatenate([pos_dst, neg_arr[:, 1]])
    all_labels = np.concatenate([np.ones(len(pos_src)), np.zeros(len(neg_arr))])

    from sklearn.model_selection import train_test_split
    train_idx, test_idx = train_test_split(
        np.arange(len(all_src)), test_size=0.3, random_state=42, stratify=all_labels)

    # Get features
    comp_feats = node_features.get("compound", np.zeros((n_compounds, 4)))
    dis_feats = node_features.get("disease", np.zeros((n_diseases, 2)))

    X_train = np.concatenate([
        comp_feats[all_src[train_idx]],
        dis_feats[all_dst[train_idx]]
    ], axis=1)
    X_test = np.concatenate([
        comp_feats[all_src[test_idx]],
        dis_feats[all_dst[test_idx]]
    ], axis=1)
    y_train = all_labels[train_idx]
    y_test = all_labels[test_idx]

    from sklearn.linear_model import LogisticRegression
    clf = LogisticRegression(max_iter=1000, class_weight='balanced')
    clf.fit(X_train, y_train)

    from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, accuracy_score
    probs = clf.predict_proba(X_test)[:, 1]
    preds = clf.predict(X_test)

    mlp_metrics = {
        "auc": float(roc_auc_score(y_test, probs)),
        "auprc": float(average_precision_score(y_test, probs)),
        "accuracy": float(accuracy_score(y_test, preds)),
        "f1": float(f1_score(y_test, preds, zero_division=0)),
    }
    results["MLP Baseline"] = mlp_metrics
    print(f"  AUC: {mlp_metrics['auc']:.4f}, AUPRC: {mlp_metrics['auprc']:.4f}")

    # 2. Node2Vec Baseline
    print("\n[2/3] Node2Vec + Logistic Regression...")
    n2v = Node2VecBaseline(embedding_dim=64, walk_length=10, num_walks=20)
    train_src_arr = all_src[train_idx]
    train_dst_arr = all_dst[train_idx]
    test_src_arr = all_src[test_idx]
    test_dst_arr = all_dst[test_idx]
    n2v_metrics = n2v.fit_predict(
        graph_data,
        train_src_arr, train_dst_arr, all_labels[train_idx],
        test_src_arr, test_dst_arr, all_labels[test_idx],
        node_maps
    )
    results["Node2Vec + LR"] = n2v_metrics
    print(f"  AUC: {n2v_metrics['auc']:.4f}, AUPRC: {n2v_metrics['auprc']:.4f}")

    # 3. Simple GCN (homogeneous)
    print("\n[3/3] Simple GCN (homogeneous graph)...")
    # Build combined node features
    total_nodes = sum(len(v) for v in node_maps.values())
    max_feat_dim = max(f.shape[1] for f in node_features.values())
    combined_feats = np.zeros((total_nodes, max_feat_dim))
    offset = 0
    for nt in node_maps:
        n = len(node_maps[nt])
        feats = node_features.get(nt, np.zeros((n, 1)))
        combined_feats[offset:offset + n, :feats.shape[1]] = feats
        offset += n

    # Build adjacency
    adj = np.zeros((total_nodes, total_nodes))
    global_offset = {}
    off = 0
    for nt in node_maps:
        global_offset[nt] = off
        off += len(node_maps[nt])

    for edge_key, edge_list in edges.items():
        src_type, _, dst_type = edge_key
        for src_local, dst_local in edge_list:
            src_g = global_offset[src_type] + src_local
            dst_g = global_offset[dst_type] + dst_local
            if src_g < total_nodes and dst_g < total_nodes:
                adj[src_g][dst_g] = 1
                adj[dst_g][src_g] = 1

    # Normalize
    deg = adj.sum(axis=1) + 1e-8
    d_inv = np.diag(1.0 / np.sqrt(deg))
    adj_norm = d_inv @ adj @ d_inv + np.eye(total_nodes)

    # Map compound/disease to global indices
    c_off = global_offset["compound"]
    d_off = global_offset["disease"]

    gcn_train_src = all_src[train_idx] + c_off
    gcn_train_dst = all_dst[train_idx] + d_off
    gcn_test_src = all_src[test_idx] + c_off
    gcn_test_dst = all_dst[test_idx] + d_off

    import torch
    feat_tensor = torch.tensor(combined_feats, dtype=torch.float32)
    adj_tensor = torch.tensor(adj_norm, dtype=torch.float32)

    gcn = SimpleGCN(max_feat_dim, hidden_dim=128, num_layers=3, dropout=0.3)
    optimizer = torch.optim.Adam(gcn.parameters(), lr=0.001)
    criterion = torch.nn.BCEWithLogitsLoss()

    # Train
    best_auc = 0
    for epoch in range(50):
        gcn.train()
        logits = gcn(feat_tensor, adj_tensor,
                      torch.tensor(gcn_train_src, dtype=torch.long),
                      torch.tensor(gcn_train_dst, dtype=torch.long))
        loss = criterion(logits, torch.tensor(y_train, dtype=torch.float32))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    # Evaluate
    gcn.eval()
    with torch.no_grad():
        logits = gcn(feat_tensor, adj_tensor,
                      torch.tensor(gcn_test_src, dtype=torch.long),
                      torch.tensor(gcn_test_dst, dtype=torch.long))
        probs = torch.sigmoid(logits).numpy()

    gcn_metrics = {
        "auc": float(roc_auc_score(y_test, probs)),
        "auprc": float(average_precision_score(y_test, probs)),
        "accuracy": float(accuracy_score(y_test, (probs >= 0.5).astype(int))),
        "f1": float(f1_score(y_test, (probs >= 0.5).astype(int), zero_division=0)),
    }
    results["Simple GCN"] = gcn_metrics
    print(f"  AUC: {gcn_metrics['auc']:.4f}, AUPRC: {gcn_metrics['auprc']:.4f}")

    # Save
    output_path = os.path.join(results_dir, "baseline_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n{'='*70}")
    print("  BASELINE COMPARISON SUMMARY")
    print(f"{'='*70}")
    print(f"{'Model':<25} {'AUC-ROC':>10} {'AUPRC':>10} {'Accuracy':>10}")
    print(f"{'-'*55}")
    for name, m in results.items():
        print(f"{name:<25} {m['auc']:>10.4f} {m['auprc']:>10.4f} {m['accuracy']:>10.4f}")
    print(f"{'='*70}")

    return results


def run_threshold_analysis(graph_data, config, results_dir):
    """Run threshold analysis on the best HetGNN model."""
    print("\n" + "=" * 70)
    print("  THRESHOLD ANALYSIS")
    print("=" * 70)

    model = build_model("hetgnn", graph_data, hidden_dim=HIDDEN_DIM,
                         num_layers=NUM_GNN_LAYERS, dropout=DROPOUT)
    trainer = Trainer(model, graph_data, config)
    test_metrics, _ = trainer.train(num_epochs=50, patience=15, verbose=False)

    analyzer = ThresholdAnalyzer(model, graph_data, trainer.test_data, results_dir)
    thresholds, best = analyzer.analyze()

    return best


def main():
    args = parse_args()
    results_dir = args.results_dir
    os.makedirs(results_dir, exist_ok=True)

    print("=" * 70)
    print("  COMPREHENSIVE EXPERIMENT SUITE")
    print("  Guizhi Tang GNN Drug Repurposing")
    print("=" * 70)

    # Build graph
    print("\n[Building Graph]")
    builder = HeterogeneousGraphBuilder(str(DATA_DIR))
    graph_data = builder.build_graph()

    config = {
        "learning_rate": LEARNING_RATE,
        "weight_decay": WEIGHT_DECAY,
        "negative_sample_ratio": NEGATIVE_SAMPLE_RATIO,
        "results_dir": results_dir,
    }

    all_results = {}

    # 1. Baselines
    if not args.skip_baselines:
        all_results["baselines"] = run_baselines(graph_data, config, results_dir)

    # 2. Main models (HetGNN + R-GCN)
    print("\n[Training HetGNN (full model)]...")
    hetgnn = build_model("hetgnn", graph_data, hidden_dim=HIDDEN_DIM,
                          num_layers=NUM_GNN_LAYERS, dropout=DROPOUT)
    hetgnn_trainer = Trainer(hetgnn, graph_data, config)
    hetgnn_metrics, hetgnn_history = hetgnn_trainer.train(num_epochs=50, patience=15, verbose=True)
    all_results["HetGNN"] = hetgnn_metrics

    # Threshold analysis
    analyzer = ThresholdAnalyzer(hetgnn, graph_data, hetgnn_trainer.test_data, results_dir)
    threshold_results, best_threshold = analyzer.analyze()
    all_results["threshold_analysis"] = best_threshold

    # 3. Cross-validation
    if not args.skip_cv:
        print("\n[Running 5-fold Cross-Validation]")
        cv = CrossValidator(graph_data, "hetgnn", config, k_folds=5)
        cv_results = cv.run(num_epochs=50, patience=15)
        all_results["cross_validation"] = cv_results

        with open(os.path.join(results_dir, "cv_results.json"), "w") as f:
            json.dump(cv_results, f, indent=2)

    # 4. Ablation study
    if not args.skip_ablation:
        print("\n[Running Ablation Study]")
        ablation = AblationStudy(results_dir=os.path.join(results_dir, "ablation"))
        ablation_results = ablation.run_all_ablations()
        all_results["ablation"] = {k: {m: float(v) for m, v in met.items()}
                                    for k, met in ablation_results.items()}

    # 5. Negative sampling study
    if not args.skip_neg_study:
        print("\n[Running Negative Sampling Study]")
        neg_study = NegativeSamplingStudy(results_dir=os.path.join(results_dir, "ablation"))
        neg_results = neg_study.run()
        all_results["neg_sampling"] = {k: {m: float(v) for m, v in met.items()}
                                        for k, met in neg_results.items()}

    # Save all results
    with open(os.path.join(results_dir, "all_experiment_results.json"), "w") as f:
        json.dump(all_results, f, indent=2)

    # Generate comprehensive publication figures
    print("\n[Generating Publication Figures]")
    try:
        generate_figures_from_results(results_dir, dpi=300)
    except Exception as e:
        print(f"  [WARNING] Figure generation failed: {e}")

    print(f"\n{'='*70}")
    print("  ALL EXPERIMENTS COMPLETE")
    print(f"  Results saved to: {results_dir}")
    print(f"{'='*70}")

    return all_results


if __name__ == "__main__":
    main()
