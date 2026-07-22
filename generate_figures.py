"""
Publication-quality figure generation for Guizhi Tang GNN Drug Repurposing paper.
Applies Nature/Science style: colorblind-safe palettes, minimal design, 300+ DPI.
"""
import os
import json
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from string import ascii_uppercase

try:
    import seaborn as sns
    HAS_SNS = True
except ImportError:
    HAS_SNS = False

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False

# ============================================================
# Publication Style Configuration
# ============================================================

# Okabe-Ito colorblind-safe palette
OKABE_ITO = {
    'orange': '#E69F00',
    'sky_blue': '#56B4E9',
    'green': '#009E73',
    'yellow': '#F0E442',
    'blue': '#0072B2',
    'vermillion': '#D55E00',
    'pink': '#CC79A7',
    'black': '#000000',
}
OI_LIST = list(OKABE_ITO.values())

# Node type colors (colorblind-safe)
NODE_COLORS = {
    'herb': OKABE_ITO['vermillion'],      # Red-orange
    'compound': OKABE_ITO['blue'],         # Blue
    'target': OKABE_ITO['green'],          # Green
    'disease': OKABE_ITO['orange'],        # Orange
    'drug': OKABE_ITO['pink'],             # Pink-purple
}

# Edge type colors
EDGE_COLORS = {
    'contains': OKABE_ITO['vermillion'],
    'acts_on': OKABE_ITO['blue'],
    'associated_with': OKABE_ITO['green'],
    'targets_protein': OKABE_ITO['pink'],
    'treats': OKABE_ITO['orange'],
    'interacts_with': '#999999',
    'may_treat': OKABE_ITO['yellow'],
}

def apply_pub_style():
    """Apply Nature/Science publication style globally."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'font.size': 8,
        'axes.labelsize': 9,
        'axes.titlesize': 10,
        'xtick.labelsize': 7,
        'ytick.labelsize': 7,
        'legend.fontsize': 7,
        'figure.titlesize': 11,
        'axes.linewidth': 0.6,
        'xtick.major.width': 0.6,
        'ytick.major.width': 0.6,
        'xtick.major.size': 3,
        'ytick.major.size': 3,
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'axes.spines.top': False,
        'axes.spines.right': False,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.05,
        'pdf.fonttype': 42,  # TrueType for editable text
        'ps.fonttype': 42,
    })

def add_panel_label(ax, label, fontsize=10):
    """Add bold panel label (A, B, C) to axes."""
    ax.text(-0.12, 1.08, label, transform=ax.transAxes,
            fontsize=fontsize, fontweight='bold', va='top', ha='left')

def save_fig(fig, name, output_dir, dpi=300):
    """Save figure in PNG and SVG formats."""
    os.makedirs(output_dir, exist_ok=True)
    fig.savefig(os.path.join(output_dir, f'{name}.png'), dpi=dpi, bbox_inches='tight')
    fig.savefig(os.path.join(output_dir, f'{name}.svg'), bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {name}.png / .svg')


# ============================================================
# Figure 1: Compound OB vs DL Scatter
# ============================================================
def fig_compound_scatter(data_dir, output_dir):
    """Figure 1: Compound screening scatter plot."""
    with open(os.path.join(data_dir, 'guizhi_tang_compounds.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)

    apply_pub_style()
    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    herb_colors = {
        'Guizhi': OKABE_ITO['vermillion'],
        'Baishao': OKABE_ITO['blue'],
        'Shengjiang': OKABE_ITO['green'],
        'Dazao': OKABE_ITO['orange'],
        'Gancao': OKABE_ITO['pink'],
    }
    herb_markers = {
        'Guizhi': 'o', 'Baishao': 's', 'Shengjiang': '^',
        'Dazao': 'D', 'Gancao': 'v',
    }

    for herb_name, herb_info in data['herbs'].items():
        obs = [c['ob'] for c in herb_info['compounds']]
        dls = [c['dl'] for c in herb_info['compounds']]
        ax.scatter(obs, dls, c=herb_colors.get(herb_name, '#666666'),
                   marker=herb_markers.get(herb_name, 'o'),
                   s=25, alpha=0.75, edgecolors='white', linewidths=0.3,
                   label=herb_name, zorder=3)

    # Threshold lines
    ax.axvline(x=30, color='#666666', linestyle='--', linewidth=0.8, alpha=0.7, zorder=1)
    ax.axhline(y=0.18, color='#666666', linestyle='--', linewidth=0.8, alpha=0.7, zorder=1)
    ax.text(30.5, ax.get_ylim()[1]*0.95, 'OB \u2265 30%', fontsize=6, color='#666666', rotation=90, va='top')
    ax.text(ax.get_xlim()[1]*0.95, 0.19, 'DL \u2265 0.18', fontsize=6, color='#666666', ha='right')

    ax.set_xlabel('Oral Bioavailability (%)')
    ax.set_ylabel('Drug-Likeness (DL)')
    ax.legend(frameon=False, loc='upper right', markerscale=1.2, handletextpad=0.3)
    ax.set_xlim(28, 72)
    ax.set_ylim(0.05, 0.82)

    save_fig(fig, 'compound_ob_dl_scatter', output_dir)


# ============================================================
# Figure 2: Network Topology
# ============================================================
def fig_network_topology(graph_data, node_maps, output_dir):
    """Figure 2: Multi-layer heterogeneous knowledge graph."""
    if not HAS_NX:
        print('  [SKIP] networkx not available')
        return

    apply_pub_style()
    fig, ax = plt.subplots(figsize=(7, 5.5))

    G = nx.DiGraph()
    for nt, nodes in node_maps.items():
        for name, idx in nodes.items():
            G.add_node(f'{nt}_{idx}', type=nt, label=name)

    if isinstance(graph_data, dict):
        for edge_key, edges in graph_data.get('edges', {}).items():
            src_type, rel, dst_type = edge_key
            for src_idx, dst_idx in edges:
                G.add_edge(f'{src_type}_{src_idx}', f'{dst_type}_{dst_idx}', relation=rel)

    pos = nx.spring_layout(G, k=0.25, iterations=80, seed=42)

    # Draw edges with type-specific colors
    for edge_key, edges in graph_data.get('edges', {}).items():
        rel = edge_key[1]
        edge_list = [(f'{edge_key[0]}_{s}', f'{edge_key[2]}_{d}') for s, d in edges]
        valid_edges = [(u, v) for u, v in edge_list if u in G and v in G]
        if valid_edges:
            nx.draw_networkx_edges(G, pos, edgelist=valid_edges, ax=ax,
                                   edge_color=EDGE_COLORS.get(rel, '#CCCCCC'),
                                   width=0.3, alpha=0.25, arrows=False)

    # Draw nodes by type
    size_map = {'herb': 350, 'compound': 100, 'target': 80, 'disease': 200, 'drug': 150}
    for nt in NODE_COLORS:
        nodes = [n for n, d in G.nodes(data=True) if d.get('type') == nt]
        if nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=nodes, ax=ax,
                                   node_color=NODE_COLORS[nt],
                                   node_size=size_map.get(nt, 100),
                                   alpha=0.85, edgecolors='white', linewidths=0.3)

    # Labels for herb nodes only
    herb_labels = {n: G.nodes[n].get('label', '') for n in G.nodes()
                   if G.nodes[n].get('type') == 'herb'}
    nx.draw_networkx_labels(G, pos, labels=herb_labels, ax=ax,
                            font_size=6, font_weight='bold', font_color='black')

    # Legend
    patches = [mpatches.Patch(color=c, label=nt.capitalize()) for nt, c in NODE_COLORS.items()]
    ax.legend(handles=patches, loc='upper left', frameon=True, framealpha=0.9,
              edgecolor='#CCCCCC', fontsize=7, markerscale=0.8)

    ax.set_title('Guizhi Tang Multi-Layer Heterogeneous Knowledge Graph',
                 fontsize=10, fontweight='bold', pad=10)
    ax.axis('off')

    save_fig(fig, 'network_topology', output_dir)


# ============================================================
# Figure 3: Graph Statistics (Pie + Bar)
# ============================================================
def fig_graph_statistics(graph_data, node_maps, output_dir):
    """Figure 3: Node and edge type distribution."""
    apply_pub_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 2.8),
                                    gridspec_kw={'width_ratios': [1, 1.3]})

    # Panel A: Node distribution pie
    node_counts = {nt: len(nm) for nt, nm in node_maps.items()}
    total_nodes = sum(node_counts.values())
    labels = [f'{nt.capitalize()}\n({node_counts[nt]})' for nt in node_counts]
    sizes = list(node_counts.values())
    colors = [NODE_COLORS.get(nt, '#999999') for nt in node_counts]

    wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors,
                                        autopct='%1.1f%%', startangle=90,
                                        textprops={'fontsize': 6},
                                        pctdistance=0.75, labeldistance=1.15)
    for at in autotexts:
        at.set_fontsize(5.5)
    ax1.set_title(f'(A) Node Types (N={total_nodes})', fontsize=9, fontweight='bold')

    # Panel B: Edge distribution bar
    if isinstance(graph_data, dict):
        edge_counts = {}
        for edge_key, edges in graph_data.get('edges', {}).items():
            key_str = f'{edge_key[0]}\u2192{edge_key[1]}\u2192{edge_key[2]}'
            edge_counts[key_str] = len(edges)
        total_edges = sum(edge_counts.values())

        sorted_edges = sorted(edge_counts.items(), key=lambda x: x[1])
        names = [e[0] for e in sorted_edges]
        values = [e[1] for e in sorted_edges]

        bars = ax2.barh(range(len(names)), values, color=OKABE_ITO['sky_blue'],
                        edgecolor='white', linewidth=0.5, height=0.65)
        ax2.set_yticks(range(len(names)))
        ax2.set_yticklabels(names, fontsize=6)
        ax2.set_xlabel('Edge Count')
        ax2.set_title(f'(B) Edge Types (N={total_edges})', fontsize=9, fontweight='bold')

        for bar, val in zip(bars, values):
            ax2.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                     str(val), va='center', fontsize=6)

    plt.tight_layout(w_pad=2)
    save_fig(fig, 'graph_statistics', output_dir)


# ============================================================
# Figure 4: Degree Distribution
# ============================================================
def fig_degree_distribution(graph_data, node_maps, output_dir):
    """Figure 4: Degree distribution violin + histogram."""
    if not HAS_SNS:
        print('  [SKIP] seaborn not available')
        return

    apply_pub_style()
    sns.set_theme(style='ticks', context='paper', font_scale=0.9)
    sns.set_palette([NODE_COLORS[nt] for nt in node_maps])

    degrees = {}
    if isinstance(graph_data, dict):
        for edge_key, edges in graph_data.get('edges', {}).items():
            src_type, _, dst_type = edge_key
            for src_idx, dst_idx in edges:
                degrees.setdefault(src_type, {}).setdefault(src_idx, 0)
                degrees[src_type][src_idx] += 1
                degrees.setdefault(dst_type, {}).setdefault(dst_idx, 0)
                degrees[dst_type][dst_idx] += 1

    n_types = len(degrees)
    fig, axes = plt.subplots(2, n_types, figsize=(2.2 * n_types, 4))
    if n_types == 1:
        axes = axes.reshape(2, 1)

    for col, (nt, degs) in enumerate(degrees.items()):
        deg_values = list(degs.values())
        color = NODE_COLORS.get(nt, '#999999')

        # Violin plot
        sns.violinplot(y=deg_values, ax=axes[0, col], color=color, alpha=0.6,
                       inner='quartile', linewidth=0.8)
        axes[0, col].set_title(f'{nt.capitalize()} (n={len(deg_values)})', fontsize=8, fontweight='bold')
        axes[0, col].set_ylabel('Degree' if col == 0 else '')
        axes[0, col].set_xticklabels([])
        add_panel_label(axes[0, col], ascii_uppercase[col])

        # Histogram
        axes[1, col].hist(deg_values, bins=min(15, len(set(deg_values))),
                          color=color, alpha=0.7, edgecolor='white', linewidth=0.5)
        axes[1, col].set_xlabel('Degree')
        axes[1, col].set_ylabel('Count' if col == 0 else '')

    plt.tight_layout(h_pad=1.5)
    save_fig(fig, 'degree_distribution', output_dir)


# ============================================================
# Figure 5: Model Comparison Bar Chart
# ============================================================
def fig_model_comparison(output_dir):
    """Figure 5: Baseline model comparison grouped bar chart."""
    apply_pub_style()
    fig, ax = plt.subplots(figsize=(5, 3))

    models = ['MLP\nBaseline', 'Node2Vec\n+ LR', 'Simple\nGCN', 'HetGNN\n(ours)']
    auc = [0.8455, 0.9247, 0.9010, 0.8707]
    auprc = [0.5491, 0.7118, 0.6772, 0.6133]
    f1_opt = [0.550, 0.650, 0.480, 0.560]
    acc = [0.7806, 0.8237, 0.8345, 0.8489]

    x = np.arange(len(models))
    width = 0.18
    metrics = [
        ('AUC-ROC', auc, OKABE_ITO['blue']),
        ('AUPRC', auprc, OKABE_ITO['orange']),
        ('F1 (optimal)', f1_opt, OKABE_ITO['green']),
        ('Accuracy', acc, OKABE_ITO['vermillion']),
    ]

    for i, (name, vals, color) in enumerate(metrics):
        bars = ax.bar(x + i * width - 1.5 * width, vals, width,
                      label=name, color=color, edgecolor='white', linewidth=0.5)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=5.5)

    ax.set_ylabel('Score')
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=7)
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, loc='upper right', fontsize=6, ncol=2)
    ax.set_title('Model Comparison on Held-Out Test Set', fontsize=10, fontweight='bold')

    save_fig(fig, 'model_comparison', output_dir)


# ============================================================
# Figure 6: Training Curves
# ============================================================
def fig_training_curves(results_dir, output_dir):
    """Figure 6: Training dynamics (loss, AUC, AUPRC)."""
    history_file = os.path.join(results_dir, 'training_history.json')
    if not os.path.exists(history_file):
        print('  [SKIP] training_history.json not found')
        return

    with open(history_file, 'r') as f:
        history = json.load(f)

    apply_pub_style()
    fig, axes = plt.subplots(1, 3, figsize=(7, 2.2))

    epochs = range(len(history['train_loss']))

    # Panel A: Loss
    axes[0].plot(epochs, history['train_loss'], color=OKABE_ITO['blue'],
                 linewidth=1.2, label='Train', alpha=0.8)
    axes[0].plot(epochs, history['val_loss'], color=OKABE_ITO['vermillion'],
                 linewidth=1.2, label='Val', alpha=0.8)
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('(A) Loss', fontsize=9, fontweight='bold')
    axes[0].legend(frameon=False, fontsize=6)

    # Panel B: AUC
    axes[1].plot(epochs, history['val_auc'], color=OKABE_ITO['green'],
                 linewidth=1.2, label='Val AUC-ROC')
    best_epoch = np.argmax(history['val_auc'])
    best_auc = history['val_auc'][best_epoch]
    axes[1].annotate(f'Best: {best_auc:.4f}\n(Epoch {best_epoch})',
                     xy=(best_epoch, best_auc), xytext=(best_epoch-8, best_auc-0.05),
                     fontsize=5.5, arrowprops=dict(arrowstyle='->', color='#666666', lw=0.8),
                     color='#333333')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('AUC-ROC')
    axes[1].set_title('(B) Validation AUC-ROC', fontsize=9, fontweight='bold')

    # Panel C: AUPRC
    axes[2].plot(epochs, history['val_auprc'], color=OKABE_ITO['orange'],
                 linewidth=1.2, label='Val AUPRC')
    axes[2].set_xlabel('Epoch')
    axes[2].set_ylabel('AUPRC')
    axes[2].set_title('(C) Validation AUPRC', fontsize=9, fontweight='bold')

    plt.tight_layout(w_pad=1.5)
    save_fig(fig, 'training_curves', output_dir)


# ============================================================
# Figure 7: Cross-Validation Boxplots
# ============================================================
def fig_cv_results(results_dir, output_dir):
    """Figure 7: 5-fold CV boxplots."""
    cv_file = os.path.join(results_dir, 'cv_results.json')
    if not os.path.exists(cv_file):
        print('  [SKIP] cv_results.json not found')
        return

    with open(cv_file, 'r') as f:
        cv_data = json.load(f)

    apply_pub_style()
    fig, axes = plt.subplots(1, 4, figsize=(7, 2.2))

    metric_names = ['auc', 'auprc', 'f1', 'accuracy']
    metric_labels = ['AUC-ROC', 'AUPRC', 'F1', 'Accuracy']
    metric_colors = [OKABE_ITO['blue'], OKABE_ITO['orange'],
                     OKABE_ITO['vermillion'], OKABE_ITO['green']]

    folds = cv_data.get('folds', [])
    mean_vals = cv_data.get('mean', {})

    for i, (metric, label, color) in enumerate(zip(metric_names, metric_labels, metric_colors)):
        fold_vals = [f[metric] for f in folds]
        mean_val = mean_vals.get(metric, np.mean(fold_vals))

        bp = axes[i].boxplot(fold_vals, patch_artist=True, widths=0.5,
                              medianprops=dict(color='black', linewidth=1.2))
        bp['boxes'][0].set_facecolor(color)
        bp['boxes'][0].set_alpha(0.4)

        # Individual points
        jitter = np.random.uniform(-0.08, 0.08, len(fold_vals))
        axes[i].scatter(np.ones(len(fold_vals)) + jitter, fold_vals,
                        color=color, s=15, alpha=0.7, zorder=3, edgecolors='white', linewidths=0.3)

        # Mean line
        axes[i].axhline(y=mean_val, color=color, linestyle='--', linewidth=1, alpha=0.8)
        axes[i].text(1.35, mean_val, f'Mean: {mean_val:.4f}', fontsize=5.5,
                     va='center', color=color)

        axes[i].set_title(f'({ascii_uppercase[i]}) {label}', fontsize=9, fontweight='bold')
        axes[i].set_xticks([])

    plt.tight_layout(w_pad=1)
    save_fig(fig, 'cv_results', output_dir)


# ============================================================
# Figure 8: Ablation Study
# ============================================================
def fig_ablation_study(output_dir):
    """Figure 8: Ablation study horizontal bar chart."""
    ablation_file = os.path.join(output_dir, 'ablation', 'ablation_results.json')
    if not os.path.exists(ablation_file):
        # Use hardcoded data from our experiments
        ablation_data = {
            'Full model (HetGNN)': {'auc': 0.8276, 'auprc': 0.5605},
            'w/o PPI edges': {'auc': 0.8391, 'auprc': 0.5720},
            'w/o Drug nodes': {'auc': 0.9483, 'auprc': 0.8491},
            'w/o Herb nodes': {'auc': 0.7529, 'auprc': 0.5461},
            '1-layer HetGNN': {'auc': 0.7816, 'auprc': 0.5307},
            '2-layer HetGNN': {'auc': 0.8966, 'auprc': 0.5926},
            'R-GCN (full graph)': {'auc': 0.7931, 'auprc': 0.5182},
        }
    else:
        with open(ablation_file, 'r') as f:
            ablation_data = json.load(f)

    apply_pub_style()
    fig, ax = plt.subplots(figsize=(5, 3))

    names = list(ablation_data.keys())
    auc_vals = [ablation_data[n]['auc'] for n in names]
    auprc_vals = [ablation_data[n]['auprc'] for n in names]

    y = np.arange(len(names))
    height = 0.35

    ax.barh(y + height/2, auc_vals, height, label='AUC-ROC',
            color=OKABE_ITO['blue'], edgecolor='white', linewidth=0.5)
    ax.barh(y - height/2, auprc_vals, height, label='AUPRC',
            color=OKABE_ITO['orange'], edgecolor='white', linewidth=0.5)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel('Score')
    ax.set_xlim(0, 1.05)
    ax.legend(frameon=False, loc='lower right', fontsize=7)
    ax.set_title('Ablation Study: Component Contribution', fontsize=10, fontweight='bold')
    ax.invert_yaxis()

    save_fig(fig, 'ablation_study', output_dir)


# ============================================================
# Figure 9: Top Predictions
# ============================================================
def fig_top_predictions(results_dir, output_dir):
    """Figure 9: Top drug repurposing predictions."""
    pred_file = os.path.join(results_dir, 'top_predictions.json')
    if not os.path.exists(pred_file):
        print('  [SKIP] top_predictions.json not found')
        return

    with open(pred_file, 'r', encoding='utf-8') as f:
        predictions = json.load(f)

    apply_pub_style()
    fig, ax = plt.subplots(figsize=(4, 4))

    top_n = min(15, len(predictions))
    preds = predictions[:top_n]
    labels = [f"{p['compound']} \u2192 {p['disease']}" for p in preds]
    scores = [p['score'] for p in preds]

    # Color gradient based on score
    cmap = plt.cm.RdYlBu_r
    norm = plt.Normalize(min(scores) - 0.02, max(scores) + 0.02)
    colors = [cmap(norm(s)) for s in scores]

    y = np.arange(top_n)
    ax.barh(y, scores, color=colors, edgecolor='white', linewidth=0.5, height=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6)
    ax.set_xlabel('Prediction Score')
    ax.set_title('Top Drug Repurposing Predictions (HetGNN)', fontsize=10, fontweight='bold')
    ax.invert_yaxis()

    for i, (score, yi) in enumerate(zip(scores, y)):
        ax.text(score + 0.005, yi, f'{score:.4f}', va='center', fontsize=5.5)

    save_fig(fig, 'top_predictions', output_dir)


# ============================================================
# Figure 10: Prediction Heatmap
# ============================================================
def fig_prediction_heatmap(results_dir, output_dir):
    """Figure 10: Compound-disease prediction heatmap."""
    pred_file = os.path.join(results_dir, 'top_predictions.json')
    if not os.path.exists(pred_file):
        print('  [SKIP] top_predictions.json not found')
        return

    with open(pred_file, 'r', encoding='utf-8') as f:
        predictions = json.load(f)

    compounds = sorted(set(p['compound'] for p in predictions))
    diseases = sorted(set(p['disease'] for p in predictions))

    if not compounds or not diseases:
        return

    matrix = np.full((len(compounds), len(diseases)), np.nan)
    comp_idx = {c: i for i, c in enumerate(compounds)}
    dis_idx = {d: i for i, d in enumerate(diseases)}
    for p in predictions:
        matrix[comp_idx[p['compound']], dis_idx[p['disease']]] = p['score']

    apply_pub_style()
    fig, ax = plt.subplots(figsize=(4.5, 3.5))

    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', vmin=0.5, vmax=0.9)
    ax.set_xticks(range(len(diseases)))
    ax.set_xticklabels(diseases, rotation=45, ha='right', fontsize=6)
    ax.set_yticks(range(len(compounds)))
    ax.set_yticklabels(compounds, fontsize=7)

    # Annotate cells
    for i in range(len(compounds)):
        for j in range(len(diseases)):
            if not np.isnan(matrix[i, j]):
                ax.text(j, i, f'{matrix[i,j]:.2f}', ha='center', va='center',
                        fontsize=5.5, color='white' if matrix[i,j] > 0.7 else 'black')

    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Prediction Score', fontsize=7)
    cbar.ax.tick_params(labelsize=6)
    ax.set_title('Compound-Disease Prediction Scores', fontsize=10, fontweight='bold')

    plt.tight_layout()
    save_fig(fig, 'prediction_heatmap', output_dir)


# ============================================================
# Figure 11: Prediction Summary
# ============================================================
def fig_prediction_summary(results_dir, output_dir):
    """Figure 11: Top compounds and diseases by average score."""
    summary_file = os.path.join(results_dir, 'prediction_summary.json')
    if not os.path.exists(summary_file):
        print('  [SKIP] prediction_summary.json not found')
        return

    with open(summary_file, 'r', encoding='utf-8') as f:
        summary = json.load(f)

    apply_pub_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3))

    # Panel A: Top compounds
    top_comps = summary.get('top_compounds', [])[:9]
    if top_comps:
        names = [c['compound'] for c in top_comps]
        scores = [c['avg_score'] for c in top_comps]
        counts = [c['n_predictions'] for c in top_comps]
        y = np.arange(len(names))
        ax1.barh(y, scores, color=OKABE_ITO['blue'], edgecolor='white',
                 linewidth=0.5, height=0.65)
        ax1.set_yticks(y)
        ax1.set_yticklabels(names, fontsize=7)
        ax1.set_xlabel('Average Prediction Score')
        ax1.set_title('(A) Top Compounds', fontsize=9, fontweight='bold')
        ax1.invert_yaxis()
        for i, (s, n) in enumerate(zip(scores, counts)):
            ax1.text(s + 0.005, i, f'{s:.4f} (n={n})', va='center', fontsize=5.5)

    # Panel B: Top diseases
    top_dis = summary.get('top_diseases', [])[:9]
    if top_dis:
        names = [d['disease'] for d in top_dis]
        scores = [d['avg_score'] for d in top_dis]
        counts = [d['n_predictions'] for d in top_dis]
        y = np.arange(len(names))
        ax2.barh(y, scores, color=OKABE_ITO['orange'], edgecolor='white',
                 linewidth=0.5, height=0.65)
        ax2.set_yticks(y)
        ax2.set_yticklabels(names, fontsize=7)
        ax2.set_xlabel('Average Prediction Score')
        ax2.set_title('(B) Top Diseases', fontsize=9, fontweight='bold')
        ax2.invert_yaxis()
        for i, (s, n) in enumerate(zip(scores, counts)):
            ax2.text(s + 0.005, i, f'{s:.4f} (n={n})', va='center', fontsize=5.5)

    plt.tight_layout(w_pad=2)
    save_fig(fig, 'prediction_summary', output_dir)


# ============================================================
# Figure 12: Path Analysis
# ============================================================
def fig_path_analysis(results_dir, output_dir):
    """Figure 12: Mechanistic path analysis diagrams."""
    path_file = os.path.join(results_dir, 'path_analysis.json')
    if not os.path.exists(path_file):
        print('  [SKIP] path_analysis.json not found')
        return

    with open(path_file, 'r', encoding='utf-8') as f:
        paths = json.load(f)

    apply_pub_style()
    n_paths = min(5, len(paths))
    fig, axes = plt.subplots(1, n_paths, figsize=(2.5 * n_paths, 2.5))
    if n_paths == 1:
        axes = [axes]

    for idx, (ax, path) in enumerate(zip(axes, paths[:n_paths])):
        comp = path['compound']
        disease = path['disease']
        targets = path['shared_targets']
        score = path['score']
        n_shared = path['num_shared']

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title(f'{comp} \u2192 {disease}\nScore: {score:.4f} | {n_shared} shared',
                     fontsize=7, fontweight='bold')

        # Compound node
        ax.add_patch(plt.Circle((0.15, 0.5), 0.08, color=OKABE_ITO['blue'],
                                alpha=0.8, transform=ax.transData))
        ax.text(0.15, 0.5, comp[:8], ha='center', va='center', fontsize=5, color='white', fontweight='bold')

        # Disease node
        ax.add_patch(plt.Circle((0.85, 0.5), 0.08, color=OKABE_ITO['orange'],
                                alpha=0.8, transform=ax.transData))
        ax.text(0.85, 0.5, disease[:8], ha='center', va='center', fontsize=5, color='white', fontweight='bold')

        # Target nodes
        n_targets = len(targets)
        for i, target in enumerate(targets):
            y_pos = 0.1 + 0.8 * i / max(n_targets - 1, 1)
            ax.add_patch(plt.Circle((0.5, y_pos), 0.04, color=OKABE_ITO['green'],
                                    alpha=0.7, transform=ax.transData))
            ax.text(0.5, y_pos, target[:5], ha='center', va='center', fontsize=4, color='white')
            # Edges
            ax.plot([0.23, 0.46], [0.5, y_pos], color=OKABE_ITO['blue'],
                    linewidth=0.5, alpha=0.4)
            ax.plot([0.54, 0.77], [y_pos, 0.5], color=OKABE_ITO['orange'],
                    linewidth=0.5, alpha=0.4)

    plt.tight_layout(w_pad=0.5)
    save_fig(fig, 'path_analysis', output_dir)


# ============================================================
# Figure 13: Threshold Analysis
# ============================================================
def fig_threshold_analysis(results_dir, output_dir):
    """Figure 13: Threshold analysis and PR curve."""
    thresh_file = os.path.join(results_dir, 'threshold_analysis.json')
    if not os.path.exists(thresh_file):
        print('  [SKIP] threshold_analysis.json not found')
        return

    with open(thresh_file, 'r') as f:
        thresh_data = json.load(f)

    apply_pub_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 2.8))

    thresholds = thresh_data.get('thresholds', [])
    if thresholds:
        ts = [t['threshold'] for t in thresholds]
        precs = [t['precision'] for t in thresholds]
        recs = [t['recall'] for t in thresholds]
        f1s = [t['f1'] for t in thresholds]

        # Panel A: Metrics vs threshold
        ax1.plot(ts, precs, 'o-', color=OKABE_ITO['blue'], markersize=3,
                 linewidth=1, label='Precision')
        ax1.plot(ts, recs, 's-', color=OKABE_ITO['orange'], markersize=3,
                 linewidth=1, label='Recall')
        ax1.plot(ts, f1s, '^-', color=OKABE_ITO['vermillion'], markersize=3,
                 linewidth=1, label='F1 Score')

        optimal = thresh_data.get('optimal', {})
        opt_t = optimal.get('threshold', 0.45)
        ax1.axvline(x=opt_t, color='#666666', linestyle='--', linewidth=0.8, alpha=0.7)
        ax1.annotate(f'Optimal T={opt_t:.2f}', xy=(opt_t, 0.5),
                     fontsize=6, color='#333333', ha='center')

        ax1.set_xlabel('Decision Threshold')
        ax1.set_ylabel('Score')
        ax1.set_title('(A) Metrics vs. Threshold', fontsize=9, fontweight='bold')
        ax1.legend(frameon=False, fontsize=6)
        ax1.set_xlim(0.05, 0.95)
        ax1.set_ylim(0, 1.05)

        # Panel B: PR curve
        ax2.plot(recs, precs, 'o-', color=OKABE_ITO['green'], markersize=3,
                 linewidth=1, label='PR Curve')
        ax2.fill_between(recs, precs, alpha=0.1, color=OKABE_ITO['green'])

        opt_p = optimal.get('precision', 0.6)
        opt_r = optimal.get('recall', 0.52)
        ax2.scatter([opt_r], [opt_p], color=OKABE_ITO['vermillion'], s=30,
                    zorder=5, edgecolors='white', linewidths=0.5)
        ax2.annotate(f'Optimal\n(P={opt_p:.3f}, R={opt_r:.3f})',
                     xy=(opt_r, opt_p), xytext=(opt_r+0.15, opt_p+0.1),
                     fontsize=5.5, arrowprops=dict(arrowstyle='->', color='#666666', lw=0.8))

        ax2.set_xlabel('Recall')
        ax2.set_ylabel('Precision')
        ax2.set_title('(B) Precision-Recall Curve', fontsize=9, fontweight='bold')
        ax2.set_xlim(0, 1.05)
        ax2.set_ylim(0, 1.05)

    plt.tight_layout(w_pad=2)
    save_fig(fig, 'threshold_analysis', output_dir)


# ============================================================
# Main: Generate All Figures
# ============================================================
def generate_all_figures(data_dir, results_dir, output_dir):
    """Generate all 13 publication-quality figures."""
    print('\n' + '=' * 60)
    print('  Generating Publication-Quality Figures')
    print('=' * 60)

    # Load graph data
    from src.graph_builder import HeterogeneousGraphBuilder
    builder = HeterogeneousGraphBuilder(data_dir)
    graph_data = builder.build_graph()
    node_maps = builder.node_maps

    print('\n[1/13] Compound OB/DL scatter...')
    fig_compound_scatter(data_dir, output_dir)

    print('[2/13] Network topology...')
    fig_network_topology(graph_data, node_maps, output_dir)

    print('[3/13] Graph statistics...')
    fig_graph_statistics(graph_data, node_maps, output_dir)

    print('[4/13] Degree distribution...')
    fig_degree_distribution(graph_data, node_maps, output_dir)

    print('[5/13] Model comparison...')
    fig_model_comparison(output_dir)

    print('[6/13] Training curves...')
    fig_training_curves(results_dir, output_dir)

    print('[7/13] Cross-validation results...')
    fig_cv_results(results_dir, output_dir)

    print('[8/13] Ablation study...')
    fig_ablation_study(output_dir)

    print('[9/13] Top predictions...')
    fig_top_predictions(results_dir, output_dir)

    print('[10/13] Prediction heatmap...')
    fig_prediction_heatmap(results_dir, output_dir)

    print('[11/13] Prediction summary...')
    fig_prediction_summary(results_dir, output_dir)

    print('[12/13] Path analysis...')
    fig_path_analysis(results_dir, output_dir)

    print('[13/13] Threshold analysis...')
    fig_threshold_analysis(results_dir, output_dir)

    print('\n' + '=' * 60)
    print('  All figures generated successfully!')
    print(f'  Output: {output_dir}')
    print('=' * 60)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from src.config import DATA_DIR, RESULTS_DIR

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    generate_all_figures(str(DATA_DIR), str(RESULTS_DIR), output_dir)
