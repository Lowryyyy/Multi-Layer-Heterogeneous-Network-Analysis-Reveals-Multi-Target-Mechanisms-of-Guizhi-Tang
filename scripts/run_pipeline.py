"""
Main Pipeline: End-to-end execution of TCM-GNN Drug Repurposing.

Usage:
    python run_pipeline.py [--model rgcn|hetgnn] [--epochs 200] [--hidden-dim 128]
"""
import os
import sys
import json
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import *
from src.graph_builder import HeterogeneousGraphBuilder
from src.model import build_model, RGCNLinkPredictor, HetGNNLinkPredictor
from src.train import Trainer
from src.predict import DrugRepurposingPredictor
from src.visualize import generate_all_figures, generate_figures_from_results


def parse_args():
    parser = argparse.ArgumentParser(description="TCM-GNN Drug Repurposing Pipeline")
    parser.add_argument("--model", type=str, default="rgcn", choices=["rgcn", "hetgnn"],
                        help="GNN model type (default: rgcn)")
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS,
                        help=f"Number of training epochs (default: {NUM_EPOCHS})")
    parser.add_argument("--hidden-dim", type=int, default=HIDDEN_DIM,
                        help=f"Hidden dimension size (default: {HIDDEN_DIM})")
    parser.add_argument("--num-layers", type=int, default=NUM_GNN_LAYERS,
                        help=f"Number of GNN layers (default: {NUM_GNN_LAYERS})")
    parser.add_argument("--dropout", type=float, default=DROPOUT,
                        help=f"Dropout rate (default: {DROPOUT})")
    parser.add_argument("--lr", type=float, default=LEARNING_RATE,
                        help=f"Learning rate (default: {LEARNING_RATE})")
    parser.add_argument("--top-k", type=int, default=20,
                        help="Number of top predictions to report")
    parser.add_argument("--results-dir", type=str, default=str(RESULTS_DIR),
                        help="Output directory for results")
    return parser.parse_args()


def main():
    args = parse_args()
    results_dir = args.results_dir
    os.makedirs(results_dir, exist_ok=True)

    print("=" * 70)
    print("  TCM-GNN Drug Repurposing Pipeline")
    print("  Guizhi Tang Multi-Layer Heterogeneous Network")
    print("=" * 70)

    # ============================
    # Step 1: Build Heterogeneous Graph
    # ============================
    print("\n[Step 1] Building heterogeneous knowledge graph...")
    builder = HeterogeneousGraphBuilder(str(DATA_DIR))
    graph_data = builder.build_graph()
    builder.save(str(PROCESSED_DIR))

    stats = builder.get_statistics()
    print(f"\nGraph statistics:")
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total edges: {stats['total_edges']}")
    print(f"  Node types: {list(stats['nodes'].keys())}")
    print(f"  Edge types: {list(stats['edges'].keys())}")

    # Save statistics for paper
    with open(os.path.join(results_dir, "graph_statistics.json"), "w") as f:
        json.dump(stats, f, indent=2)

    # ============================
    # Step 2: Initialize GNN Model
    # ============================
    print(f"\n[Step 2] Initializing {args.model.upper()} model...")
    config = {
        "learning_rate": args.lr,
        "weight_decay": WEIGHT_DECAY,
        "negative_sample_ratio": NEGATIVE_SAMPLE_RATIO,
        "results_dir": results_dir,
    }

    model = build_model(
        args.model,
        graph_data,
        hidden_dim=args.hidden_dim,
        num_layers=args.num_layers,
        dropout=args.dropout,
    )

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Model: {args.model.upper()}")
    print(f"  Hidden dim: {args.hidden_dim}")
    print(f"  Num layers: {args.num_layers}")
    print(f"  Total parameters: {total_params:,}")
    print(f"  Trainable parameters: {trainable_params:,}")

    # ============================
    # Step 3: Train Model
    # ============================
    print(f"\n[Step 3] Training model ({args.epochs} epochs max)...")
    trainer = Trainer(model, graph_data, config)
    test_metrics, history = trainer.train(
        num_epochs=args.epochs,
        patience=PATIENCE,
        verbose=True,
    )

    # Save test metrics
    with open(os.path.join(results_dir, "test_metrics.json"), "w") as f:
        json.dump(test_metrics, f, indent=2)

    # ============================
    # Step 4: Generate Predictions
    # ============================
    print(f"\n[Step 4] Generating drug repurposing predictions (top-{args.top_k})...")
    predictor = DrugRepurposingPredictor(
        model, graph_data, builder.node_maps, results_dir
    )
    predictions = predictor.predict_all(top_k=args.top_k, threshold=0.3)

    # Path analysis
    path_analysis = predictor.analyze_prediction_paths(predictions, top_n=5)

    # Summary
    summary = predictor.generate_summary(predictions, path_analysis)

    # ============================
    # Step 5: Generate Visualizations
    # ============================
    print(f"\n[Step 5] Generating publication figures...")
    try:
        generate_all_figures(
            graph_data,
            builder.node_maps,
            history,
            predictions,
            results_dir,
            dpi=FIGURE_DPI,
        )
    except Exception as e:
        print(f"  [WARNING] Figure generation failed: {e}")
        print("  Results are still saved in JSON format.")

    # Also generate supplementary figures from all available JSON result files
    try:
        generate_figures_from_results(results_dir, dpi=FIGURE_DPI)
    except Exception as e:
        print(f"  [WARNING] Supplementary figure generation failed: {e}")

    # ============================
    # Final Summary
    # ============================
    print(f"\n{'='*70}")
    print("  PIPELINE COMPLETE")
    print(f"{'='*70}")
    print(f"  Model: {args.model.upper()}")
    print(f"  Test AUC-ROC: {test_metrics['auc']:.4f}")
    print(f"  Test AUPRC:   {test_metrics['auprc']:.4f}")
    print(f"  Test F1:      {test_metrics['f1']:.4f}")
    print(f"  Predictions:  {len(predictions)} compound-disease pairs")
    print(f"  Results:      {results_dir}")
    print(f"{'='*70}")

    return {
        "model": args.model,
        "test_metrics": test_metrics,
        "predictions": predictions,
        "graph_stats": stats,
        "path_analysis": path_analysis,
    }


if __name__ == "__main__":
    main()
