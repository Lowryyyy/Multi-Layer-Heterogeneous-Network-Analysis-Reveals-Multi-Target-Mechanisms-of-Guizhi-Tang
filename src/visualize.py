"""
Visualization module for the heterogeneous knowledge graph and GNN results.

Generates SCI publication-quality figures with professional color palettes:
1. Network topology visualization (multi-layer heterogeneous graph)
2. Training curves (loss + AUC/AUPRC with smoothed lines)
3. Prediction heatmaps (clustered with dendrogram)
4. Degree distributions (violin + box + histogram)
5. Model comparison bar charts
6. Ablation study results
7. Cross-validation box plots
8. Threshold / precision-recall analysis
9. Top predictions lollipop / bubble charts
10. Path analysis Sankey-style diagrams
11. Graph statistics overview
12. Compound OB vs DL scatter plot
"""
import os
import json
import numpy as np
from collections import defaultdict, Counter

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.ticker as mticker
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import FancyBboxPatch
    from scipy.ndimage import gaussian_filter1d
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False

try:
    from .config import (SCI_COLORS, NODE_TYPE_COLORS, EDGE_TYPE_COLORS,
                         MODEL_COLORS, HERB_COLORS, FONT_FAMILY,
                         FONT_SIZE_TITLE, FONT_SIZE_LABEL, FONT_SIZE_TICK,
                         FONT_SIZE_LEGEND, DATA_DIR)
    HAS_CFG = True
except ImportError:
    HAS_CFG = False
    SCI_COLORS = {"blue":"#4E79A7","orange":"#F28E2B","red":"#E15759",
                  "teal":"#76B7B2","green":"#59A14F","yellow":"#EDC948",
                  "purple":"#B07AA1","pink":"#FF9DA7","brown":"#9C755F",
                  "gray":"#BAB0AC","darkblue":"#2C5985","darkred":"#A03A3C"}
    NODE_TYPE_COLORS = {"herb":"#E15759","compound":"#4E79A7","target":"#59A14F",
                        "disease":"#F28E2B","drug":"#B07AA1"}
    MODEL_COLORS = {}
    HERB_COLORS = {}
    FONT_FAMILY = "Arial"
    FONT_SIZE_TITLE = 14
    FONT_SIZE_LABEL = 12
    FONT_SIZE_TICK = 10
    FONT_SIZE_LEGEND = 10
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


# ============================================================
# Global Style Setup
# ============================================================
def _setup_style():
    """Configure matplotlib for SCI publication quality."""
    if not HAS_MPL:
        return
    plt.rcParams.update({
        'font.family': FONT_FAMILY,
        'font.size': FONT_SIZE_TICK,
        'axes.titlesize': FONT_SIZE_TITLE,
        'axes.labelsize': FONT_SIZE_LABEL,
        'xtick.labelsize': FONT_SIZE_TICK,
        'ytick.labelsize': FONT_SIZE_TICK,
        'legend.fontsize': FONT_SIZE_LEGEND,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'axes.linewidth': 0.8,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
        'grid.linewidth': 0.5,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.edgecolor': '#333333',
        'axes.labelcolor': '#333333',
        'xtick.color': '#333333',
        'ytick.color': '#333333',
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'savefig.facecolor': 'white',
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.08,
    })


def _smooth(y, sigma=2):
    """Apply Gaussian smoothing to a curve."""
    if not HAS_MPL:
        return y
    return gaussian_filter1d(np.array(y, dtype=float), sigma=sigma)


def _save_fig(fig, output_dir, name, dpi=300):
    """Save figure in both PNG and SVG formats."""
    path_png = os.path.join(output_dir, f"{name}.png")
    fig.savefig(path_png, dpi=dpi, bbox_inches='tight')
    try:
        path_svg = os.path.join(output_dir, f"{name}.svg")
        fig.savefig(path_svg, format='svg', bbox_inches='tight')
    except Exception:
        pass
    plt.close(fig)
    print(f"  [Figure] {name}.png saved to {output_dir}")


# ============================================================
# 1. Network Topology
# ============================================================
def plot_network_topology(graph_data, node_maps, output_dir, dpi=300):
    """Plot the heterogeneous network topology with SCI-grade styling."""
    if not HAS_NX or not HAS_MPL:
        print("[WARNING] networkx or matplotlib not available. Skipping topology plot.")
        return
    _setup_style()

    G = nx.DiGraph()
    for node_type, nodes in node_maps.items():
        for name, idx in nodes.items():
            node_id = f"{node_type}_{idx}"
            G.add_node(node_id, type=node_type, label=name)

    edge_type_counts = Counter()
    if hasattr(graph_data, 'edge_index_dict'):
        for et in graph_data.edge_types:
            ei = graph_data[et].edge_index
            for i in range(ei.shape[1]):
                src = f"{et[0]}_{ei[0,i].item()}"
                dst = f"{et[2]}_{ei[1,i].item()}"
                G.add_edge(src, dst, relation=et[1])
                edge_type_counts[et[1]] += 1
    elif isinstance(graph_data, dict):
        for edge_key, edges in graph_data.get("edges", {}).items():
            for src_idx, dst_idx in edges:
                src = f"{edge_key[0]}_{src_idx}"
                dst = f"{edge_key[2]}_{dst_idx}"
                G.add_edge(src, dst, relation=edge_key[1])
                edge_type_counts[edge_key[1]] += 1

    fig, ax = plt.subplots(figsize=(22, 18))
    pos = nx.spring_layout(G, k=0.35, iterations=80, seed=42)

    # Draw edges with low alpha, colored by type
    edge_colors_list = []
    edge_list = []
    for u, v, d in G.edges(data=True):
        rel = d.get("relation", "")
        edge_colors_list.append(EDGE_TYPE_COLORS.get(
            (u.split("_")[0], rel, v.split("_")[0]), "#CCCCCC"))
        edge_list.append((u, v))

    nx.draw_networkx_edges(G, pos, edgelist=edge_list, ax=ax,
                          alpha=0.12, width=0.4, edge_color=edge_colors_list)

    # Draw nodes by type
    size_map = {"herb": 900, "compound": 250, "target": 200,
                "disease": 500, "drug": 350}
    for nt, color in NODE_TYPE_COLORS.items():
        nodes_of_type = [n for n in G.nodes() if G.nodes[n].get("type") == nt]
        if not nodes_of_type:
            continue
        sizes = [size_map.get(nt, 200)] * len(nodes_of_type)
        nx.draw_networkx_nodes(G, pos, nodelist=nodes_of_type, ax=ax,
                               node_color=color, node_size=sizes,
                               alpha=0.85, edgecolors='white', linewidths=0.3)

    # Labels only for herbs and diseases (high-level nodes)
    labels_to_show = {}
    for node in G.nodes():
        nt = G.nodes[node].get("type", "")
        if nt in ("herb", "disease"):
            labels_to_show[node] = G.nodes[node].get("label", "")
    nx.draw_networkx_labels(G, pos, labels_to_show, ax=ax,
                            font_size=7, font_color='#333333',
                            font_weight='bold')

    # Legend - node types
    node_patches = [mpatches.Patch(color=c, label=nt.capitalize())
                    for nt, c in NODE_TYPE_COLORS.items()]
    # Legend - edge types
    edge_patches = [mpatches.Patch(color=c, label=rel.replace("_", " "))
                    for (src_t, rel, dst_t), c in EDGE_TYPE_COLORS.items()]

    leg1 = ax.legend(handles=node_patches, loc="upper left",
                     title="Node Types", frameon=True, fancybox=True,
                     framealpha=0.9, edgecolor='#CCCCCC')
    ax.add_artist(leg1)
    ax.legend(handles=edge_patches, loc="lower left",
              title="Edge Types", frameon=True, fancybox=True,
              framealpha=0.9, edgecolor='#CCCCCC', fontsize=8)

    ax.set_title("Guizhi Tang Multi-Layer Heterogeneous Knowledge Graph",
                 fontsize=16, fontweight='bold', pad=15)
    ax.axis("off")
    plt.tight_layout()
    _save_fig(fig, output_dir, "network_topology", dpi)


# ============================================================
# 2. Training Curves
# ============================================================
def plot_training_curves(history, output_dir, dpi=300):
    """Plot training loss and validation metrics with smoothed curves."""
    if not HAS_MPL:
        return
    _setup_style()

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    epochs = range(1, len(history["train_loss"]) + 1)

    # --- Panel A: Loss curves ---
    ax = axes[0]
    ax.plot(epochs, history["train_loss"], color=SCI_COLORS["blue"],
            linewidth=1.5, alpha=0.4, label="Train (raw)")
    ax.plot(epochs, _smooth(history["train_loss"]), color=SCI_COLORS["blue"],
            linewidth=2.5, label="Train (smoothed)")
    ax.plot(epochs, history["val_loss"], color=SCI_COLORS["red"],
            linewidth=1.5, alpha=0.4, label="Val (raw)")
    ax.plot(epochs, _smooth(history["val_loss"]), color=SCI_COLORS["red"],
            linewidth=2.5, label="Val (smoothed)")
    ax.set_xlabel("Epoch", fontweight='bold')
    ax.set_ylabel("Loss", fontweight='bold')
    ax.set_title("(A) Training & Validation Loss", fontweight='bold')
    ax.legend(frameon=True, fancybox=True)

    # --- Panel B: AUC-ROC ---
    ax = axes[1]
    ax.plot(epochs, history["val_auc"], color=SCI_COLORS["green"],
            linewidth=1.5, alpha=0.4)
    ax.plot(epochs, _smooth(history["val_auc"]), color=SCI_COLORS["green"],
            linewidth=2.5, label="Val AUC-ROC")
    best_auc = max(history["val_auc"])
    best_epoch = history["val_auc"].index(best_auc) + 1
    ax.axvline(x=best_epoch, color=SCI_COLORS["gray"],
               linestyle='--', linewidth=1, alpha=0.7)
    ax.annotate(f"Best: {best_auc:.4f}\n(Epoch {best_epoch})",
                xy=(best_epoch, best_auc),
                xytext=(best_epoch + len(epochs) * 0.05, best_auc - 0.08),
                fontsize=9, color=SCI_COLORS["darkblue"],
                arrowprops=dict(arrowstyle='->', color=SCI_COLORS["darkblue"],
                                lw=1.2),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                         edgecolor=SCI_COLORS["blue"], alpha=0.9))
    ax.set_xlabel("Epoch", fontweight='bold')
    ax.set_ylabel("AUC-ROC", fontweight='bold')
    ax.set_title("(B) Validation AUC-ROC", fontweight='bold')
    ax.legend(frameon=True, fancybox=True)
    ax.set_ylim([0.45, 1.0])

    # --- Panel C: AUPRC ---
    ax = axes[2]
    ax.plot(epochs, history["val_auprc"], color=SCI_COLORS["orange"],
            linewidth=1.5, alpha=0.4)
    ax.plot(epochs, _smooth(history["val_auprc"]), color=SCI_COLORS["orange"],
            linewidth=2.5, label="Val AUPRC")
    ax.set_xlabel("Epoch", fontweight='bold')
    ax.set_ylabel("AUPRC", fontweight='bold')
    ax.set_title("(C) Validation AUPRC", fontweight='bold')
    ax.legend(frameon=True, fancybox=True)

    plt.tight_layout()
    _save_fig(fig, output_dir, "training_curves", dpi)


# ============================================================
# 3. Prediction Heatmap (Clustered)
# ============================================================
def plot_prediction_heatmap(predictions, output_dir, dpi=300):
    """Plot compound-disease prediction score heatmap with SCI colormap."""
    if not HAS_MPL or not predictions:
        return
    _setup_style()

    compounds = sorted(set(p["compound"] for p in predictions))
    diseases = sorted(set(p["disease"] for p in predictions))
    if not compounds or not diseases:
        return

    matrix = np.zeros((len(compounds), len(diseases)))
    comp_idx = {c: i for i, c in enumerate(compounds)}
    dis_idx = {d: i for i, d in enumerate(diseases)}
    for p in predictions:
        matrix[comp_idx[p["compound"]], dis_idx[p["disease"]]] = p["score"]

    # Custom SCI colormap: white -> light blue -> dark blue
    sci_cmap = LinearSegmentedColormap.from_list(
        "sci_blue", ["#FFFFFF", "#D6E4F0", "#4E79A7", "#2C5985", "#1A3A5C"])

    fig, ax = plt.subplots(figsize=(max(12, len(diseases) * 0.8),
                                     max(8, len(compounds) * 0.45)))
    im = ax.imshow(matrix, cmap=sci_cmap, aspect='auto', vmin=0, vmax=1)

    ax.set_xticks(range(len(diseases)))
    ax.set_xticklabels(diseases, rotation=45, ha='right', fontsize=8)
    ax.set_yticks(range(len(compounds)))
    ax.set_yticklabels(compounds, fontsize=9)

    # Annotate cells with scores
    for i in range(len(compounds)):
        for j in range(len(diseases)):
            val = matrix[i, j]
            if val > 0:
                text_color = 'white' if val > 0.55 else '#333333'
                ax.text(j, i, f"{val:.2f}", ha='center', va='center',
                        fontsize=6, color=text_color, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Prediction Score", fontweight='bold')
    cbar.ax.tick_params(labelsize=9)

    ax.set_title("Compound-Disease Repurposing Prediction Scores",
                 fontsize=FONT_SIZE_TITLE, fontweight='bold', pad=12)
    ax.set_xlabel("Disease", fontweight='bold')
    ax.set_ylabel("Compound", fontweight='bold')
    ax.grid(False)

    plt.tight_layout()
    _save_fig(fig, output_dir, "prediction_heatmap", dpi)


# ============================================================
# 4. Degree Distribution (Violin + Box + Histogram)
# ============================================================
def plot_degree_distribution(node_maps, graph_data, output_dir, dpi=300):
    """Plot node degree distributions with violin + box + histogram."""
    if not HAS_MPL:
        return
    _setup_style()

    degrees = {}
    if isinstance(graph_data, dict):
        for edge_key, edges in graph_data.get("edges", {}).items():
            src_type, rel, dst_type = edge_key
            for src_idx, dst_idx in edges:
                degrees.setdefault(src_type, {}).setdefault(src_idx, 0)
                degrees[src_type][src_idx] += 1
                degrees.setdefault(dst_type, {}).setdefault(dst_idx, 0)
                degrees[dst_type][dst_idx] += 1

    if not degrees:
        return

    n_types = len(degrees)
    fig, axes = plt.subplots(2, n_types, figsize=(4.5 * n_types, 8),
                             gridspec_kw={'height_ratios': [3, 2]})
    if n_types == 1:
        axes = axes.reshape(2, 1)

    colors = NODE_TYPE_COLORS

    for col, (nt, degs) in enumerate(degrees.items()):
        deg_values = list(degs.values())
        color = colors.get(nt, SCI_COLORS["gray"])

        # Top: Violin + Box
        ax_top = axes[0, col]
        parts = ax_top.violinplot([deg_values], positions=[1],
                                   showmeans=True, showmedians=True,
                                   showextrema=False)
        for pc in parts['bodies']:
            pc.set_facecolor(color)
            pc.set_alpha(0.6)
        ax_top.boxplot([deg_values], positions=[1], widths=0.3,
                       patch_artist=True,
                       boxprops=dict(facecolor=color, alpha=0.3),
                       medianprops=dict(color='white', linewidth=2))
        ax_top.set_xticks([1])
        ax_top.set_xticklabels([nt.capitalize()])
        ax_top.set_ylabel("Degree" if col == 0 else "", fontweight='bold')
        ax_top.set_title(f"{nt.capitalize()} Degree\n(n={len(deg_values)})",
                         fontweight='bold')

        # Bottom: Histogram
        ax_bot = axes[1, col]
        ax_bot.hist(deg_values, bins=min(15, max(len(set(deg_values)), 5)),
                    color=color, alpha=0.75, edgecolor='white', linewidth=0.5)
        ax_bot.set_xlabel("Degree", fontweight='bold')
        ax_bot.set_ylabel("Count" if col == 0 else "", fontweight='bold')

    plt.tight_layout()
    _save_fig(fig, output_dir, "degree_distribution", dpi)


# ============================================================
# 5. Model Comparison (Grouped Bar Chart)
# ============================================================
def plot_model_comparison(baseline_results, test_metrics, output_dir, dpi=300):
    """Plot model comparison as grouped bar chart with SCI styling."""
    if not HAS_MPL:
        return
    _setup_style()

    # Build model metrics dict
    models = {}
    if baseline_results:
        models.update(baseline_results)
    if test_metrics:
        models["HetGNN (ours)"] = test_metrics

    if not models:
        return

    # Order models
    model_order = ["MLP Baseline", "Node2Vec + LR", "Simple GCN",
                   "R-GCN (heterogeneous)", "HetGNN (ours)"]
    ordered = [m for m in model_order if m in models] + \
              [m for m in models if m not in model_order]

    metrics = ["auc", "auprc", "accuracy", "f1"]
    metric_labels = ["AUC-ROC", "AUPRC", "Accuracy", "F1"]
    metric_colors = [SCI_COLORS["blue"], SCI_COLORS["orange"],
                     SCI_COLORS["green"], SCI_COLORS["red"]]

    x = np.arange(len(ordered))
    width = 0.18

    fig, ax = plt.subplots(figsize=(14, 7))
    for i, (metric, label, color) in enumerate(zip(metrics, metric_labels, metric_colors)):
        values = [models[m].get(metric, 0) for m in ordered]
        bars = ax.bar(x + i * width - 1.5 * width, values, width,
                      label=label, color=color, edgecolor='white',
                      linewidth=0.5, alpha=0.9)
        # Add value labels
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f"{val:.3f}", ha='center', va='bottom',
                        fontsize=7, fontweight='bold', color=color)

    ax.set_xticks(x)
    ax.set_xticklabels(ordered, fontsize=9, rotation=15, ha='right')
    ax.set_ylabel("Score", fontweight='bold')
    ax.set_title("Model Comparison on Held-Out Test Set",
                fontweight='bold', pad=12)
    ax.set_ylim([0, 1.05])
    ax.legend(loc='upper right', frameon=True, fancybox=True, ncol=4)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    _save_fig(fig, output_dir, "model_comparison", dpi)


# ============================================================
# 6. Ablation Study Results
# ============================================================
def plot_ablation_results(ablation_data, output_dir, dpi=300):
    """Plot ablation study as horizontal bar chart."""
    if not HAS_MPL or not ablation_data:
        return
    _setup_style()

    configs = list(ablation_data.keys())
    auc_vals = [ablation_data[c].get("auc", 0) for c in configs]
    auprc_vals = [ablation_data[c].get("auprc", 0) for c in configs]
    f1_vals = [ablation_data[c].get("f1", 0) for c in configs]

    y = np.arange(len(configs))
    height = 0.22

    fig, ax = plt.subplots(figsize=(12, max(5, len(configs) * 0.7)))
    ax.barh(y + height, auc_vals, height, label='AUC-ROC',
            color=SCI_COLORS["blue"], edgecolor='white', alpha=0.9)
    ax.barh(y, auprc_vals, height, label='AUPRC',
            color=SCI_COLORS["orange"], edgecolor='white', alpha=0.9)
    ax.barh(y - height, f1_vals, height, label='F1',
            color=SCI_COLORS["red"], edgecolor='white', alpha=0.9)

    ax.set_yticks(y)
    ax.set_yticklabels(configs, fontsize=9)
    ax.set_xlabel("Score", fontweight='bold')
    ax.set_title("Ablation Study: Component Contribution Analysis",
                 fontweight='bold', pad=12)
    ax.legend(loc='lower right', frameon=True, fancybox=True)
    ax.set_xlim([0, 1.05])
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    _save_fig(fig, output_dir, "ablation_study", dpi)


# ============================================================
# 7. Cross-Validation Box Plot
# ============================================================
def plot_cv_results(cv_data, output_dir, dpi=300):
    """Plot cross-validation results as box plots."""
    if not HAS_MPL or not cv_data:
        return
    _setup_style()

    folds = cv_data.get("folds", [])
    mean = cv_data.get("mean", {})
    std = cv_data.get("std", {})
    if not folds:
        return

    metrics = ["auc", "auprc", "f1", "accuracy"]
    metric_labels = ["AUC-ROC", "AUPRC", "F1", "Accuracy"]
    colors = [SCI_COLORS["blue"], SCI_COLORS["orange"],
              SCI_COLORS["red"], SCI_COLORS["green"]]

    fig, axes = plt.subplots(1, 4, figsize=(18, 5))
    for idx, (ax, metric, label, color) in enumerate(zip(axes, metrics, metric_labels, colors)):
        vals = [f.get(metric, 0) for f in folds]
        fold_labels = [f"Fold {i+1}" for i in range(len(vals))]

        bp = ax.boxplot([vals], positions=[1.5], widths=0.4, patch_artist=True,
                        boxprops=dict(facecolor=color, alpha=0.3),
                        medianprops=dict(color=color, linewidth=2))
        ax.scatter(np.ones(len(vals)) * 1.5 + np.random.randn(len(vals)) * 0.05,
                   vals, color=color, s=60, zorder=5, edgecolors='white',
                   linewidths=0.5, label="Individual folds")

        ax.axhline(y=mean.get(metric, 0), color=color, linestyle='--',
                   linewidth=1.5, alpha=0.7,
                   label=f"Mean: {mean.get(metric, 0):.4f}")
        ax.fill_between([0.8, 2.2],
                        mean.get(metric, 0) - std.get(metric, 0),
                        mean.get(metric, 0) + std.get(metric, 0),
                        color=color, alpha=0.1)

        ax.set_xticks([1.5])
        ax.set_xticklabels([f"5-Fold CV"])
        ax.set_ylabel(label, fontweight='bold')
        ax.set_title(f"({chr(65 + idx)}) {label}",
                     fontweight='bold')
        ax.legend(fontsize=8, frameon=True)
        ax.set_ylim([0, 1.05])

    plt.suptitle("5-Fold Cross-Validation Results (HetGNN)",
                 fontsize=FONT_SIZE_TITLE, fontweight='bold', y=1.02)
    plt.tight_layout()
    _save_fig(fig, output_dir, "cv_results", dpi)


# ============================================================
# 8. Threshold / Precision-Recall Analysis
# ============================================================
def plot_threshold_analysis(threshold_data, output_dir, dpi=300):
    """Plot threshold analysis with precision-recall curve and F1."""
    if not HAS_MPL or not threshold_data:
        return
    _setup_style()

    thresholds_data = threshold_data.get("thresholds", [])
    optimal = threshold_data.get("optimal", {})

    if not thresholds_data:
        return

    ts = [t["threshold"] for t in thresholds_data]
    precisions = [t["precision"] for t in thresholds_data]
    recalls = [t["recall"] for t in thresholds_data]
    f1s = [t["f1"] for t in thresholds_data]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Panel A: Precision, Recall, F1 vs Threshold
    ax = axes[0]
    ax.plot(ts, precisions, color=SCI_COLORS["blue"], linewidth=2.5,
            marker='o', markersize=4, label="Precision")
    ax.plot(ts, recalls, color=SCI_COLORS["orange"], linewidth=2.5,
            marker='s', markersize=4, label="Recall")
    ax.plot(ts, f1s, color=SCI_COLORS["red"], linewidth=2.5,
            marker='^', markersize=4, label="F1 Score")

    opt_t = optimal.get("threshold", 0.5)
    ax.axvline(x=opt_t, color=SCI_COLORS["gray"], linestyle='--',
               linewidth=1.5, alpha=0.7)
    ax.annotate(f"Optimal\nT={opt_t:.2f}", xy=(opt_t, max(f1s)),
                xytext=(opt_t + 0.1, max(f1s)),
                fontsize=9, color=SCI_COLORS["darkred"],
                arrowprops=dict(arrowstyle='->', color=SCI_COLORS["darkred"]),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                         edgecolor=SCI_COLORS["red"], alpha=0.9))

    ax.set_xlabel("Decision Threshold", fontweight='bold')
    ax.set_ylabel("Score", fontweight='bold')
    ax.set_title("(A) Metrics vs. Decision Threshold", fontweight='bold')
    ax.legend(frameon=True, fancybox=True)

    # Panel B: Precision-Recall curve
    ax = axes[1]
    ax.plot(recalls, precisions, color=SCI_COLORS["green"], linewidth=2.5,
            marker='o', markersize=3, label="Precision-Recall")
    ax.fill_between(recalls, precisions, alpha=0.15, color=SCI_COLORS["green"])

    opt_p = optimal.get("precision", 0)
    opt_r = optimal.get("recall", 0)
    ax.scatter([opt_r], [opt_p], color=SCI_COLORS["red"], s=120,
               zorder=5, edgecolors='white', linewidths=1.5,
               label=f"Optimal (P={opt_p:.3f}, R={opt_r:.3f})")

    ax.set_xlabel("Recall", fontweight='bold')
    ax.set_ylabel("Precision", fontweight='bold')
    ax.set_title("(B) Precision-Recall Curve", fontweight='bold')
    ax.legend(frameon=True, fancybox=True)
    ax.set_xlim([0, 1.02])
    ax.set_ylim([0, 1.02])

    plt.tight_layout()
    _save_fig(fig, output_dir, "threshold_analysis", dpi)


# ============================================================
# 9. Top Predictions (Lollipop / Bubble Chart)
# ============================================================
def plot_top_predictions(predictions, output_dir, dpi=300):
    """Plot top drug repurposing predictions as a lollipop chart."""
    if not HAS_MPL or not predictions:
        return
    _setup_style()

    top_preds = predictions[:15]
    labels = [f"{p['compound']} → {p['disease']}" for p in top_preds]
    scores = [p["score"] for p in top_preds]

    # Color by score
    norm_scores = (np.array(scores) - min(scores)) / (max(scores) - min(scores) + 1e-8)
    colors = plt.cm.RdYlBu_r(norm_scores * 0.7 + 0.15)

    fig, ax = plt.subplots(figsize=(10, max(6, len(top_preds) * 0.45)))
    y = np.arange(len(top_preds))[::-1]

    ax.hlines(y=y, xmin=0, xmax=scores, color=colors, linewidth=2.5, alpha=0.7)
    ax.scatter(scores, y, color=colors, s=150, zorder=5, edgecolors='white',
              linewidths=1)

    for yi, s, p in zip(y, scores, top_preds):
        ax.text(s + 0.005, yi, f"{s:.4f}", va='center', fontsize=8,
                fontweight='bold', color='#333333')

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Prediction Score", fontweight='bold')
    ax.set_title("Top Drug Repurposing Predictions (HetGNN)",
                 fontweight='bold', pad=12)
    ax.set_xlim([0, max(scores) * 1.12])
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    _save_fig(fig, output_dir, "top_predictions", dpi)


# ============================================================
# 10. Path Analysis (Sankey-style Chord Diagram)
# ============================================================
def plot_path_analysis(path_data, output_dir, dpi=300):
    """Plot mechanistic path analysis as a compound-target-disease flow diagram."""
    if not HAS_MPL or not path_data:
        return
    _setup_style()

    top_paths = path_data[:5]
    n_paths = len(top_paths)

    fig, axes = plt.subplots(1, n_paths, figsize=(5 * n_paths, 6))
    if n_paths == 1:
        axes = [axes]

    for ax, pa in zip(axes, top_paths):
        comp = pa["compound"]
        disease = pa["disease"]
        score = pa.get("score", 0)
        shared = pa.get("shared_targets", [])
        comp_targets = pa.get("compound_targets", [])
        dis_targets = pa.get("disease_targets", [])

        # Draw compound node (left)
        ax.scatter(0, 0.5, s=2000, color=SCI_COLORS["blue"], zorder=5,
                   edgecolors='white', linewidths=1.5)
        ax.text(0, 0.5, comp[:10], ha='center', va='center', fontsize=7,
                fontweight='bold', color='white', zorder=6)

        # Draw disease node (right)
        ax.scatter(1, 0.5, s=2000, color=SCI_COLORS["orange"], zorder=5,
                   edgecolors='white', linewidths=1.5)
        ax.text(1, 0.5, disease[:10], ha='center', va='center', fontsize=7,
                fontweight='bold', color='white', zorder=6)

        # Draw shared targets in middle
        n_shared = len(shared)
        if n_shared > 0:
            target_y = np.linspace(0.15, 0.85, n_shared) if n_shared > 1 else [0.5]
            for i, (target, ty) in enumerate(zip(shared, target_y)):
                ax.scatter(0.5, ty, s=300, color=SCI_COLORS["green"],
                           zorder=4, edgecolors='white', linewidths=0.8)
                ax.text(0.5, ty, target, ha='center', va='center', fontsize=5.5,
                        fontweight='bold', color='white', zorder=5)
                # Lines from compound to target
                ax.plot([0, 0.5], [0.5, ty], color=SCI_COLORS["blue"],
                        alpha=0.3, linewidth=0.8)
                # Lines from target to disease
                ax.plot([0.5, 1], [ty, 0.5], color=SCI_COLORS["orange"],
                        alpha=0.3, linewidth=0.8)

        ax.set_xlim([-0.15, 1.15])
        ax.set_ylim([0, 1])
        ax.set_title(f"{comp}\n→ {disease}\nScore: {score:.4f} | {n_shared} shared",
                     fontsize=9, fontweight='bold')
        ax.axis('off')

    plt.suptitle("Mechanistic Path Analysis: Compound → Target → Disease",
                 fontsize=FONT_SIZE_TITLE, fontweight='bold', y=1.02)
    plt.tight_layout()
    _save_fig(fig, output_dir, "path_analysis", dpi)


# ============================================================
# 11. Graph Statistics Overview (Pie + Bar)
# ============================================================
def plot_graph_statistics(stats, output_dir, dpi=300):
    """Plot graph statistics as combined pie + bar chart."""
    if not HAS_MPL or not stats:
        return
    _setup_style()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Panel A: Node type distribution (pie chart)
    ax = axes[0]
    nodes = stats.get("nodes", {})
    node_labels = list(nodes.keys())
    node_vals = list(nodes.values())
    node_colors = [NODE_TYPE_COLORS.get(nt, SCI_COLORS["gray"]) for nt in node_labels]

    explode = [0.03] * len(node_labels)
    wedges, texts, autotexts = ax.pie(
        node_vals, labels=[n.capitalize() for n in node_labels],
        colors=node_colors, autopct='%1.1f%%', startangle=90,
        explode=explode, textprops={'fontsize': 10, 'fontweight': 'bold'},
        wedgeprops=dict(edgecolor='white', linewidth=1.5))
    for at in autotexts:
        at.set_color('white')
        at.set_fontweight('bold')
    ax.set_title(f"(A) Node Type Distribution (Total: {stats.get('total_nodes', 0)})",
                 fontweight='bold')

    # Panel B: Edge type distribution (horizontal bar chart)
    ax = axes[1]
    edges = stats.get("edges", {})
    edge_labels = list(edges.keys())
    edge_vals = list(edges.values())
    edge_colors_list = [SCI_COLORS["teal"]] * len(edge_labels)

    y_pos = np.arange(len(edge_labels))
    ax.barh(y_pos, edge_vals, color=edge_colors_list, edgecolor='white',
            linewidth=0.5, alpha=0.85)
    for i, val in enumerate(edge_vals):
        ax.text(val + max(edge_vals)*0.01, i, str(val), va='center',
                fontsize=9, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels([e.replace("-", " → ") for e in edge_labels], fontsize=8)
    ax.set_xlabel("Edge Count", fontweight='bold')
    ax.set_title(f"(B) Edge Type Distribution (Total: {stats.get('total_edges', 0)})",
                 fontweight='bold')
    ax.invert_yaxis()

    plt.tight_layout()
    _save_fig(fig, output_dir, "graph_statistics", dpi)


# ============================================================
# 12. Compound OB vs DL Scatter Plot
# ============================================================
def plot_compound_ob_dl(compounds_data, output_dir, dpi=300):
    """Plot compound oral bioavailability vs drug-likeness, colored by herb."""
    if not HAS_MPL:
        return
    _setup_style()

    fig, ax = plt.subplots(figsize=(12, 8))

    for herb_name, herb_info in compounds_data.get("herbs", {}).items():
        color = HERB_COLORS.get(herb_name, SCI_COLORS["gray"])
        obs = [c["ob"] for c in herb_info["compounds"]]
        dls = [c["dl"] for c in herb_info["compounds"]]
        names = [c["name"] for c in herb_info["compounds"]]

        ax.scatter(obs, dls, color=color, s=80, alpha=0.75, edgecolors='white',
                   linewidths=0.5, label=herb_name, zorder=5)

    # Screening thresholds
    ax.axhline(y=0.18, color=SCI_COLORS["gray"], linestyle='--',
               linewidth=1, alpha=0.5)
    ax.axvline(x=30, color=SCI_COLORS["gray"], linestyle='--',
               linewidth=1, alpha=0.5)
    ax.text(30.5, 0.85, "OB ≥ 30%", fontsize=8, color=SCI_COLORS["gray"],
            rotation=90, va='top')
    ax.text(80, 0.19, "DL ≥ 0.18", fontsize=8, color=SCI_COLORS["gray"])

    ax.set_xlabel("Oral Bioavailability (%)", fontweight='bold')
    ax.set_ylabel("Drug-Likeness (DL)", fontweight='bold')
    ax.set_title("Compound Screening: Oral Bioavailability vs. Drug-Likeness",
                 fontweight='bold', pad=12)
    ax.legend(title="Herb Source", frameon=True, fancybox=True,
              ncol=3, loc='upper right')

    plt.tight_layout()
    _save_fig(fig, output_dir, "compound_ob_dl_scatter", dpi)


# ============================================================
# 13. Prediction Summary: Compound & Disease Rankings
# ============================================================
def plot_prediction_summary(summary, output_dir, dpi=300):
    """Plot prediction summary with compound and disease rankings."""
    if not HAS_MPL or not summary:
        return
    _setup_style()

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Panel A: Top compounds (horizontal bar)
    ax = axes[0]
    top_comps = summary.get("top_compounds", [])[:10]
    comp_names = [c["compound"] for c in top_comps]
    comp_scores = [c["avg_score"] for c in top_comps]
    comp_counts = [c["n_predictions"] for c in top_comps]

    y = np.arange(len(comp_names))
    bars = ax.barh(y, comp_scores, color=SCI_COLORS["blue"], alpha=0.8,
                   edgecolor='white', linewidth=0.5)
    for bar, count, score in zip(bars, comp_counts, comp_scores):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                f"{score:.4f} (n={count})", va='center', fontsize=8,
                fontweight='bold')
    ax.set_yticks(y)
    ax.set_yticklabels(comp_names, fontsize=9)
    ax.set_xlabel("Average Prediction Score", fontweight='bold')
    ax.set_title("(A) Top Compounds by Average Score", fontweight='bold')
    ax.invert_yaxis()
    ax.set_xlim([0, max(comp_scores) * 1.25])

    # Panel B: Top diseases (horizontal bar)
    ax = axes[1]
    top_dis = summary.get("top_diseases", [])[:10]
    dis_names = [d["disease"] for d in top_dis]
    dis_scores = [d["avg_score"] for d in top_dis]
    dis_counts = [d["n_predictions"] for d in top_dis]

    y = np.arange(len(dis_names))
    bars = ax.barh(y, dis_scores, color=SCI_COLORS["orange"], alpha=0.8,
                   edgecolor='white', linewidth=0.5)
    for bar, count, score in zip(bars, dis_counts, dis_scores):
        ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
                f"{score:.4f} (n={count})", va='center', fontsize=8,
                fontweight='bold')
    ax.set_yticks(y)
    ax.set_yticklabels(dis_names, fontsize=9)
    ax.set_xlabel("Average Prediction Score", fontweight='bold')
    ax.set_title("(B) Top Diseases by Average Score", fontweight='bold')
    ax.invert_yaxis()
    ax.set_xlim([0, max(dis_scores) * 1.25])

    plt.tight_layout()
    _save_fig(fig, output_dir, "prediction_summary", dpi)


# ============================================================
# 14. Negative Sampling Ratio Study
# ============================================================
def plot_neg_sampling_study(neg_data, output_dir, dpi=300):
    """Plot negative sampling ratio study results."""
    if not HAS_MPL or not neg_data:
        return
    _setup_style()

    ratios = sorted(neg_data.keys())
    ratio_nums = [int(r.split("_")[-1]) for r in ratios]
    auc_vals = [neg_data[r].get("auc", 0) for r in ratios]
    auprc_vals = [neg_data[r].get("auprc", 0) for r in ratios]
    f1_vals = [neg_data[r].get("f1", 0) for r in ratios]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(ratio_nums))
    width = 0.25

    ax.bar(x - width, auc_vals, width, label='AUC-ROC',
           color=SCI_COLORS["blue"], edgecolor='white', alpha=0.9)
    ax.bar(x, auprc_vals, width, label='AUPRC',
           color=SCI_COLORS["orange"], edgecolor='white', alpha=0.9)
    ax.bar(x + width, f1_vals, width, label='F1',
           color=SCI_COLORS["red"], edgecolor='white', alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{r}:1" for r in ratio_nums])
    ax.set_xlabel("Negative:Positive Sampling Ratio", fontweight='bold')
    ax.set_ylabel("Score", fontweight='bold')
    ax.set_title("Effect of Negative Sampling Ratio on Model Performance",
                 fontweight='bold', pad=12)
    ax.legend(frameon=True, fancybox=True)
    ax.set_ylim([0, 1.05])

    plt.tight_layout()
    _save_fig(fig, output_dir, "neg_sampling_study", dpi)


# ============================================================
# Orchestrator Functions
# ============================================================
def generate_all_figures(graph_data, node_maps, history, predictions,
                         results_dir, dpi=300):
    """Generate all publication figures from pipeline data."""
    print("\nGenerating publication figures...")
    _setup_style()

    plot_network_topology(graph_data, node_maps, results_dir, dpi)
    if history:
        plot_training_curves(history, results_dir, dpi)
    if predictions:
        plot_prediction_heatmap(predictions, results_dir, dpi)
        plot_top_predictions(predictions, results_dir, dpi)
    plot_degree_distribution(node_maps, graph_data, results_dir, dpi)

    # Try to generate additional figures from saved JSON files
    _generate_figures_from_json(results_dir, graph_data, node_maps, dpi)

    print("All figures generated successfully!")


def _generate_figures_from_json(results_dir, graph_data=None, node_maps=None, dpi=300):
    """Generate additional figures from saved JSON result files."""
    _setup_style()

    # Graph statistics
    stats_path = os.path.join(results_dir, "graph_statistics.json")
    if os.path.exists(stats_path):
        with open(stats_path, "r") as f:
            stats = json.load(f)
        plot_graph_statistics(stats, results_dir, dpi)

    # Baseline / model comparison
    baseline_path = os.path.join(results_dir, "baseline_results.json")
    test_path = os.path.join(results_dir, "test_metrics.json")
    baseline_results = None
    test_metrics = None
    if os.path.exists(baseline_path):
        with open(baseline_path, "r") as f:
            baseline_results = json.load(f)
    if os.path.exists(test_path):
        with open(test_path, "r") as f:
            test_metrics = json.load(f)
    if baseline_results or test_metrics:
        plot_model_comparison(baseline_results, test_metrics, results_dir, dpi)

    # Ablation study
    ablation_path = os.path.join(results_dir, "ablation", "ablation_results.json")
    if os.path.exists(ablation_path):
        with open(ablation_path, "r") as f:
            ablation_data = json.load(f)
        plot_ablation_results(ablation_data, results_dir, dpi)

    # Cross-validation
    cv_path = os.path.join(results_dir, "cv_results.json")
    if os.path.exists(cv_path):
        with open(cv_path, "r") as f:
            cv_data = json.load(f)
        plot_cv_results(cv_data, results_dir, dpi)

    # Threshold analysis
    threshold_path = os.path.join(results_dir, "threshold_analysis.json")
    if os.path.exists(threshold_path):
        with open(threshold_path, "r") as f:
            threshold_data = json.load(f)
        plot_threshold_analysis(threshold_data, results_dir, dpi)

    # Prediction summary
    summary_path = os.path.join(results_dir, "prediction_summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r") as f:
            summary = json.load(f)
        plot_prediction_summary(summary, results_dir, dpi)

    # Path analysis
    path_path = os.path.join(results_dir, "path_analysis.json")
    if os.path.exists(path_path):
        with open(path_path, "r") as f:
            path_data = json.load(f)
        plot_path_analysis(path_data, results_dir, dpi)

    # Compound OB vs DL scatter
    compounds_path = os.path.join(str(DATA_DIR), "guizhi_tang_compounds.json")
    if os.path.exists(compounds_path):
        with open(compounds_path, "r", encoding="utf-8") as f:
            compounds_data = json.load(f)
        plot_compound_ob_dl(compounds_data, results_dir, dpi)

    # Negative sampling study
    neg_path = os.path.join(results_dir, "ablation", "neg_sampling_study.json")
    if os.path.exists(neg_path):
        with open(neg_path, "r") as f:
            neg_data = json.load(f)
        plot_neg_sampling_study(neg_data, results_dir, dpi)


def generate_figures_from_results(results_dir, dpi=300):
    """
    Generate all figures from existing JSON result files.
    This allows regenerating figures without retraining the model.

    Usage:
        python -c "from src.visualize import generate_figures_from_results; generate_figures_from_results('results')"
    """
    print(f"\nRegenerating all figures from results in: {results_dir}")
    _setup_style()

    # Rebuild graph for topology and degree plots
    try:
        from .graph_builder import HeterogeneousGraphBuilder
        from .config import DATA_DIR as cfg_data_dir
        builder = HeterogeneousGraphBuilder(str(cfg_data_dir))
        graph_data = builder.build_graph()
        node_maps = builder.node_maps
    except Exception as e:
        print(f"  [WARNING] Could not rebuild graph: {e}")
        graph_data = None
        node_maps = None

    if graph_data and node_maps:
        plot_network_topology(graph_data, node_maps, results_dir, dpi)
        plot_degree_distribution(node_maps, graph_data, results_dir, dpi)

    _generate_figures_from_json(results_dir, graph_data, node_maps, dpi)

    # Training curves
    history_path = os.path.join(results_dir, "training_history.json")
    if os.path.exists(history_path):
        with open(history_path, "r") as f:
            history = json.load(f)
        plot_training_curves(history, results_dir, dpi)

    # Top predictions
    top_path = os.path.join(results_dir, "top_predictions.json")
    if os.path.exists(top_path):
        with open(top_path, "r") as f:
            predictions = json.load(f)
        plot_prediction_heatmap(predictions, results_dir, dpi)
        plot_top_predictions(predictions, results_dir, dpi)

    print("All figures regenerated successfully!")
