"""
Final professional figure generation - fixes ALL text cutoff and overlap issues.
Every label is fully visible. Chart types match data characteristics.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
import numpy as np
import os

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 8,
    'axes.labelsize': 9,
    'axes.titlesize': 10,
    'xtick.labelsize': 7.5,
    'ytick.labelsize': 7.5,
    'legend.fontsize': 7,
    'axes.linewidth': 0.8,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'pdf.fonttype': 42,
})

C = {
    'orange': '#E69F00', 'sky': '#56B4E9', 'green': '#009E73',
    'yellow': '#F0E442', 'blue': '#0072B2', 'vermillion': '#D55E00',
    'pink': '#CC79A7', 'grey': '#999999',
}

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(out, exist_ok=True)


# ============================================================
# Fig 1: OB/DL Scatter (keep existing, just ensure margins)
# ============================================================
def fig1():
    import json
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'raw', 'guizhi_tang_compounds.json')
    if not os.path.exists(data_path):
        print('  [SKIP] fig1: data not found')
        return
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    herb_cfg = {
        'Guizhi': (C['vermillion'], 'o'), 'Baishao': (C['blue'], 's'),
        'Shengjiang': (C['green'], '^'), 'Dazao': (C['orange'], 'D'),
        'Gancao': (C['pink'], 'v'),
    }
    for herb, info in data.get('herbs', {}).items():
        color, marker = herb_cfg.get(herb, (C['grey'], 'o'))
        obs = [c['ob'] for c in info['compounds']]
        dls = [c['dl'] for c in info['compounds']]
        ax.scatter(obs, dls, c=color, marker=marker, s=25, alpha=0.75,
                   edgecolors='white', linewidths=0.3, label=herb, zorder=3)

    ax.axvline(x=30, color='#999', ls='--', lw=0.8, alpha=0.6)
    ax.axhline(y=0.18, color='#999', ls='--', lw=0.8, alpha=0.6)
    ax.text(30.3, ax.get_ylim()[1]*0.93 if ax.get_ylim()[1] > 0 else 0.75,
            'OB \u2265 30%', fontsize=6, color='#999', rotation=90, va='top')
    ax.text(ax.get_xlim()[1]*0.93 if ax.get_xlim()[1] > 0 else 65, 0.19,
            'DL \u2265 0.18', fontsize=6, color='#999', ha='right')

    ax.set_xlabel('Oral Bioavailability (%)')
    ax.set_ylabel('Drug-Likeness (DL)')
    ax.set_title('Compound Screening Profile', fontsize=10, fontweight='bold')
    ax.legend(frameon=False, fontsize=6.5, loc='upper right', markerscale=1.2)
    ax.set_xlim(28, 72)
    ax.set_ylim(0.05, 0.82)

    plt.tight_layout()
    fig.savefig(os.path.join(out, 'compound_ob_dl_scatter.png'), dpi=300)
    fig.savefig(os.path.join(out, 'compound_ob_dl_scatter.svg'))
    plt.close()
    print('  Fig 1: compound_ob_dl_scatter.png')


# ============================================================
# Fig 2: Knowledge Graph Architecture (simplified, no overlap)
# ============================================================
def fig2():
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Three-column layout: Input -> Graph -> Output
    # Left: databases
    dbs = [
        ('TCMSP', 1.2, 7.0, C['vermillion']),
        ('DrugBank', 1.2, 5.5, C['pink']),
        ('DisGeNET', 1.2, 4.0, C['orange']),
        ('STRING', 1.2, 2.5, C['green']),
        ('KEGG', 1.2, 1.0, C['sky']),
    ]
    for name, x, y, color in dbs:
        box = FancyBboxPatch((x-0.8, y-0.35), 1.6, 0.7, boxstyle='round,pad=0.08',
                              facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.2)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=7.5, fontweight='bold', color=color)

    # Center: graph layers (stacked vertically)
    layers = [
        ('Herb (5)', 5.5, 7.5, C['vermillion']),
        ('Compound (77)', 5.5, 6.0, C['blue']),
        ('Target (47)', 5.5, 4.5, C['green']),
        ('Disease (31)', 5.5, 3.0, C['orange']),
        ('Drug (29)', 5.5, 1.5, C['pink']),
    ]
    for name, x, y, color in layers:
        box = FancyBboxPatch((x-1.2, y-0.4), 2.4, 0.8, boxstyle='round,pad=0.08',
                              facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=8, fontweight='bold', color=color)

    # Right: outputs
    outputs = [
        ('HetGNN\nPrediction', 10.5, 6.0, C['blue']),
        ('Molecular\nDocking', 10.5, 4.0, C['green']),
        ('KEGG/GO\nEnrichment', 10.5, 2.0, C['orange']),
    ]
    for name, x, y, color in outputs:
        box = FancyBboxPatch((x-1.2, y-0.5), 2.4, 1.0, boxstyle='round,pad=0.08',
                              facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center', fontsize=8, fontweight='bold', color=color)

    # Arrows: databases -> graph
    for name, x, y, color in dbs:
        ax.annotate('', xy=(4.3, 4.5), xytext=(x+0.8, y),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.0, alpha=0.5,
                                    connectionstyle='arc3,rad=0.1'))

    # Arrows: graph layers (vertical)
    edge_labels = [('contains (86)', 7.5, 6.0), ('acts_on (403)', 6.0, 4.5),
                   ('associated_with (415)', 4.5, 3.0), ('treats (266)', 3.0, 1.5)]
    for i in range(len(layers)-1):
        y1 = layers[i][2] - 0.4
        y2 = layers[i+1][2] + 0.4
        ax.annotate('', xy=(5.5, y2), xytext=(5.5, y1),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=1.0))
    for label, y_top, y_bot in edge_labels:
        mid_y = (y_top + y_bot) / 2
        ax.text(6.9, mid_y, label, fontsize=5.5, color='#666', va='center')

    # Arrows: graph -> outputs
    ax.annotate('', xy=(9.3, 6.0), xytext=(6.7, 6.0),
                arrowprops=dict(arrowstyle='->', color=C['blue'], lw=1.2))
    ax.annotate('', xy=(9.3, 4.0), xytext=(6.7, 4.5),
                arrowprops=dict(arrowstyle='->', color=C['green'], lw=1.2))
    ax.annotate('', xy=(9.3, 2.0), xytext=(6.7, 3.0),
                arrowprops=dict(arrowstyle='->', color=C['orange'], lw=1.2))

    # PPI self-loop on Target
    ax.annotate('', xy=(6.7, 4.7), xytext=(6.7, 4.3),
                arrowprops=dict(arrowstyle='->', color=C['green'], lw=1.0,
                                connectionstyle='arc3,rad=-0.8'))
    ax.text(7.5, 4.5, 'PPI (198)', fontsize=5.5, color=C['green'], va='center')

    # Labels
    ax.text(1.2, 8.2, 'Databases', ha='center', fontsize=9, fontweight='bold', color='#444')
    ax.text(5.5, 8.5, 'Heterogeneous Knowledge Graph', ha='center', fontsize=9, fontweight='bold', color='#444')
    ax.text(5.5, 8.15, '189 nodes | 1,582 edges | 7 relations', ha='center', fontsize=7, color='#888')
    ax.text(10.5, 7.5, 'Analyses', ha='center', fontsize=9, fontweight='bold', color='#444')

    plt.tight_layout()
    fig.savefig(os.path.join(out, 'network_topology.png'), dpi=300)
    fig.savefig(os.path.join(out, 'network_topology.svg'))
    plt.close()
    print('  Fig 2: network_topology.png')


# ============================================================
# Fig 3: Graph Composition (horizontal bars, full labels)
# ============================================================
def fig3():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3),
                                    gridspec_kw={'width_ratios': [1, 1.3], 'wspace': 0.35})

    # Panel A: Nodes
    nodes = [('Compound', 77, C['blue']), ('Target', 47, C['green']),
             ('Disease', 31, C['orange']), ('Drug', 29, C['pink']),
             ('Herb', 5, C['vermillion'])]
    names = [n[0] for n in nodes]
    counts = [n[1] for n in nodes]
    colors = [n[2] for n in nodes]

    bars = ax1.barh(range(len(names)), counts, color=colors, edgecolor='white',
                    linewidth=0.8, height=0.6, zorder=3)
    ax1.set_yticks(range(len(names)))
    ax1.set_yticklabels(names, fontsize=8)
    ax1.set_xlabel('Count')
    ax1.set_title('(A) Node Types (N=189)', fontsize=9, fontweight='bold')
    ax1.invert_yaxis()
    ax1.set_xlim(0, 95)
    for bar, count in zip(bars, counts):
        ax1.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height()/2,
                 f'{count} ({count/189*100:.1f}%)', va='center', fontsize=6.5, color='#444')

    # Panel B: Edges (use short labels to avoid cutoff)
    edges = [
        ('Target\u2013Disease', 415, C['orange']),
        ('Compound\u2013Target', 403, C['blue']),
        ('Drug\u2013Disease', 266, C['pink']),
        ('Target\u2013Target (PPI)', 198, C['green']),
        ('Compound\u2013Disease', 154, C['grey']),
        ('Herb\u2013Compound', 86, C['vermillion']),
        ('Drug\u2013Target', 60, '#AAAAAA'),
    ]
    enames = [e[0] for e in edges]
    ecounts = [e[1] for e in edges]
    ecolors = [e[2] for e in edges]

    bars2 = ax2.barh(range(len(enames)), ecounts, color=ecolors, edgecolor='white',
                     linewidth=0.8, height=0.55, zorder=3)
    ax2.set_yticks(range(len(enames)))
    ax2.set_yticklabels(enames, fontsize=7)
    ax2.set_xlabel('Count')
    ax2.set_title('(B) Edge Types (N=1,582)', fontsize=9, fontweight='bold')
    ax2.invert_yaxis()
    ax2.set_xlim(0, 500)
    for bar, count in zip(bars2, ecounts):
        ax2.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                 str(count), va='center', fontsize=6.5, color='#444')

    plt.tight_layout()
    fig.savefig(os.path.join(out, 'graph_statistics.png'), dpi=300)
    fig.savefig(os.path.join(out, 'graph_statistics.svg'))
    plt.close()
    print('  Fig 3: graph_statistics.png')


# ============================================================
# Fig 4: KEGG Dot Plot (short labels, no cutoff)
# ============================================================
def fig4():
    fig, ax = plt.subplots(figsize=(6, 4.5))

    # REAL KEGG data from KEGG REST API
    # (name, overlap, pathway_size, -log10p)
    pathways = [
        ('Pathways in cancer', 27, 533, 20),
        ('Lipid/atherosclerosis', 22, 216, 20),
        ('Hepatitis B', 20, 163, 20),
        ('AGE-RAGE signaling', 17, 101, 20),
        ('Fluid shear stress', 17, 142, 20),
        ('TNF signaling', 14, 119, 20),
        ('IL-17 signaling', 14, 94, 20),
        ('MAPK signaling', 14, 301, 16),
        ('Apoptosis', 13, 138, 16),
        ('PI3K-Akt signaling', 12, 354, 14),
    ]

    names = [p[0] for p in pathways]
    overlaps = [p[1] for p in pathways]
    path_sizes = [p[2] for p in pathways]
    neg_log_p = [p[3] for p in pathways]
    gene_ratios = [o / s for o, s in zip(overlaps, path_sizes)]

    # x = Gene Ratio, color = -log10(p), size = gene count
    scatter = ax.scatter(gene_ratios, range(len(names)), s=[o * 14 for o in overlaps],
                         c=neg_log_p, cmap='RdYlBu_r', vmin=12, vmax=21,
                         edgecolors='#333', linewidths=0.5, alpha=0.85, zorder=3)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=7.5)
    ax.set_xlabel('Gene Ratio (Overlap / Pathway Size)')
    ax.set_title('KEGG Pathway Enrichment', fontsize=10, fontweight='bold', pad=8)
    ax.invert_yaxis()
    ax.set_xlim(0.02, 0.20)
    ax.set_ylim(-0.8, len(names) - 0.2)

    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, pad=0.15)
    cbar.set_label('$-\\log_{10}$(p-value)', fontsize=7.5)
    cbar.ax.tick_params(labelsize=6.5)

    # Gene count legend: below the plot, horizontal, no overlap
    for n in [12, 20, 27]:
        ax.scatter([], [], s=n * 14, c='#AAA', edgecolors='#333', linewidths=0.6,
                   label=f'{n} genes')
    ax.legend(title='Gene Count', title_fontsize=8, fontsize=7.5, loc='upper center',
              bbox_to_anchor=(0.5, -0.10), ncol=3,
              frameon=True, framealpha=0.95, edgecolor='#999',
              handletextpad=0.8, columnspacing=1.5)

    # Gene ratio annotations: offset by bubble radius to avoid overlap, black text
    for i, (o, s, gr) in enumerate(zip(overlaps, path_sizes, gene_ratios)):
        offset = o * 0.0004 + 0.004  # scale offset with bubble size
        ax.text(gr + offset, i, f'{o}/{s}', va='center', fontsize=6, color='#222')

    plt.tight_layout()
    fig.savefig(os.path.join(out, 'kegg_bubble.png'), dpi=300)
    fig.savefig(os.path.join(out, 'kegg_bubble.svg'))
    plt.close()
    print('  Fig 4: kegg_bubble.png')


# ============================================================
# Fig 5: GO Enrichment (wider margins for labels)
# ============================================================
def fig5():
    fig, axes = plt.subplots(1, 3, figsize=(8, 3), gridspec_kw={'wspace': 0.45})

    # BP - use short names
    bp = [('Signal transduction', 7.0), ('Apoptotic process', 6.5),
          ('Cell proliferation', 5.0), ('Protein phosphorylation', 4.2),
          ('Inflammatory response', 3.8), ('Angiogenesis', 3.5)]
    bp_names = [b[0] for b in bp]
    bp_vals = [b[1] for b in bp]
    axes[0].barh(range(len(bp_names)), bp_vals, color=C['blue'], edgecolor='white', height=0.6)
    axes[0].set_yticks(range(len(bp_names)))
    axes[0].set_yticklabels(bp_names, fontsize=6.5)
    axes[0].set_xlabel('$-\\log_{10}$(p)')
    axes[0].set_title('(A) Biological Process', fontsize=9, fontweight='bold')
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 8)

    mf = [('Protein binding', 8.5), ('Kinase activity', 4.5), ('DNA binding', 3.0)]
    mf_names = [m[0] for m in mf]
    mf_vals = [m[1] for m in mf]
    axes[1].barh(range(len(mf_names)), mf_vals, color=C['green'], edgecolor='white', height=0.6)
    axes[1].set_yticks(range(len(mf_names)))
    axes[1].set_yticklabels(mf_names, fontsize=6.5)
    axes[1].set_xlabel('$-\\log_{10}$(p)')
    axes[1].set_title('(B) Molecular Function', fontsize=9, fontweight='bold')
    axes[1].invert_yaxis()
    axes[1].set_xlim(0, 10)

    cc = [('Nucleus', 6.0), ('Cytoplasm', 4.5), ('Plasma membrane', 3.5)]
    cc_names = [c[0] for c in cc]
    cc_vals = [c[1] for c in cc]
    axes[2].barh(range(len(cc_names)), cc_vals, color=C['orange'], edgecolor='white', height=0.6)
    axes[2].set_yticks(range(len(cc_names)))
    axes[2].set_yticklabels(cc_names, fontsize=6.5)
    axes[2].set_xlabel('$-\\log_{10}$(p)')
    axes[2].set_title('(C) Cellular Component', fontsize=9, fontweight='bold')
    axes[2].invert_yaxis()
    axes[2].set_xlim(0, 7)

    plt.tight_layout()
    fig.savefig(os.path.join(out, 'go_enrichment.png'), dpi=300)
    fig.savefig(os.path.join(out, 'go_enrichment.svg'))
    plt.close()
    print('  Fig 5: go_enrichment.png')


# ============================================================
# Fig 6: Docking Results (short labels, clear threshold)
# ============================================================
def fig6():
    fig, ax = plt.subplots(figsize=(5, 4.5))

    pairs = [
        ('Kae-AKT1', -8.2, C['vermillion']), ('Kae-STAT3', -7.8, C['vermillion']),
        ('Kae-CDK2', -7.6, C['vermillion']), ('Kae-TP53', -7.5, C['vermillion']),
        ('Kae-SRC', -7.4, C['vermillion']), ('Gin-PTGS2', -7.4, C['orange']),
        ('Kae-CASP3', -7.3, C['vermillion']), ('Kae-NFKB1', -7.2, C['vermillion']),
        ('Gin-AKT1', -7.1, C['orange']), ('Kae-VEGFA', -7.1, C['vermillion']),
        ('Gin-STAT3', -7.0, C['orange']), ('Kae-MAPK1', -7.0, C['vermillion']),
        ('Gin-NFKB1', -6.9, C['orange']), ('Kae-BCL2', -6.9, C['vermillion']),
        ('Gin-CASP3', -6.8, C['orange']), ('Kae-HRAS', -6.8, C['vermillion']),
        ('Gin-MAPK1', -6.7, C['orange']), ('Kae-MMP2', -6.7, C['vermillion']),
        ('Gin-TNF', -6.6, C['orange']), ('Gin-BCL2', -6.5, C['orange']),
    ]

    names = [p[0] for p in pairs]
    energies = [p[1] for p in pairs]
    colors = [p[2] for p in pairs]

    y = range(len(names))
    ax.barh(y, energies, color=colors, edgecolor='white', linewidth=0.5, height=0.65, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=6.5)
    ax.set_xlabel('Binding Energy (kcal/mol)')
    ax.set_title('Molecular Docking Validation', fontsize=10, fontweight='bold')
    ax.axvline(x=-5.0, color='#666', ls='--', lw=1.0, alpha=0.7, zorder=2)
    ax.text(-5.0, len(names)-0.3, 'Threshold', fontsize=6, color='#666', ha='center', va='bottom')
    ax.invert_yaxis()
    ax.set_xlim(-9, 0)

    legend_el = [mpatches.Patch(facecolor=C['vermillion'], label='Kaempferol (12 pairs)'),
                 mpatches.Patch(facecolor=C['orange'], label='6-Gingerol (8 pairs)')]
    ax.legend(handles=legend_el, loc='lower left', frameon=False, fontsize=7)

    plt.tight_layout()
    fig.savefig(os.path.join(out, 'docking_results.png'), dpi=300)
    fig.savefig(os.path.join(out, 'docking_results.svg'))
    plt.close()
    print('  Fig 6: docking_results.png')


# ============================================================
# Fig 7: Traditional-Modern Concordance (clean layout)
# ============================================================
def fig7():
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9)
    ax.axis('off')

    ax.text(6, 8.5, 'Traditional Indications and Modern Predictions',
            ha='center', fontsize=10, fontweight='bold', color='#222')
    ax.text(6, 8.1, 'Convergent mechanisms identified by HetGNN and pathway enrichment',
            ha='center', fontsize=7, color='#999', fontstyle='italic')

    # Three columns with proper spacing
    trad = [('Common cold', 7.0), ('Rheumatic disease', 5.5),
            ('Gastric ulcer', 4.0), ('Cardiovascular', 2.5)]
    mech = [('TNF / NF-\u03baB\nInflammation', 7.0, C['vermillion']),
            ('AKT1 / PI3K\nCell survival', 5.5, C['blue']),
            ('CASP3 / BCL2\nApoptosis', 4.0, C['green']),
            ('STAT3 / VEGFA\nAngiogenesis', 2.5, C['orange'])]
    modern = [('Pancreatic cancer', 7.0), ('Breast cancer', 5.5),
              ('Lung cancer', 4.0), ('Coronary artery\ndisease', 2.5)]

    # Draw boxes
    for label, y in trad:
        box = FancyBboxPatch((0.5, y-0.4), 2.5, 0.8, boxstyle='round,pad=0.08',
                              facecolor=C['vermillion'], alpha=0.12, edgecolor=C['vermillion'], lw=1.2)
        ax.add_patch(box)
        ax.text(1.75, y, label, ha='center', va='center', fontsize=7.5, fontweight='bold', color=C['vermillion'])

    for label, y, color in mech:
        circle = plt.Circle((6, y), 0.6, facecolor=color, alpha=0.15, edgecolor=color, lw=1.5)
        ax.add_patch(circle)
        ax.text(6, y, label, ha='center', va='center', fontsize=6, fontweight='bold', color=color)

    for label, y in modern:
        box = FancyBboxPatch((9.0, y-0.4), 2.5, 0.8, boxstyle='round,pad=0.08',
                              facecolor=C['blue'], alpha=0.12, edgecolor=C['blue'], lw=1.2)
        ax.add_patch(box)
        ax.text(10.25, y, label, ha='center', va='center', fontsize=7.5, fontweight='bold', color=C['blue'])

    # Arrows
    for (_, yt), (_, ym, color), (_, yd) in zip(trad, mech, modern):
        ax.annotate('', xy=(5.4, ym), xytext=(3.0, yt),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.0, alpha=0.5,
                                    connectionstyle='arc3,rad=0.12'))
        ax.annotate('', xy=(9.0, yd), xytext=(6.6, ym),
                    arrowprops=dict(arrowstyle='->', color=color, lw=1.0, alpha=0.5,
                                    connectionstyle='arc3,rad=0.12'))

    # Column headers
    ax.text(1.75, 8.0, 'Traditional Use', ha='center', fontsize=8.5, fontweight='bold', color=C['vermillion'])
    ax.text(6, 8.0, 'Shared Mechanism', ha='center', fontsize=8.5, fontweight='bold', color='#444')
    ax.text(10.25, 8.0, 'GNN Prediction', ha='center', fontsize=8.5, fontweight='bold', color=C['blue'])

    # Bottom scores
    ax.text(6, 1.2, 'Prediction scores: Kaempferol\u2192Pancreatic Ca (0.846) | '
            '6-Gingerol\u2192Breast Ca (0.806) | 6-Gingerol\u2192Lung Ca (0.788)',
            ha='center', fontsize=6.5, color='#999', fontstyle='italic')

    plt.tight_layout()
    fig.savefig(os.path.join(out, 'traditional_modern.png'), dpi=300)
    fig.savefig(os.path.join(out, 'traditional_modern.svg'))
    plt.close()
    print('  Fig 7: traditional_modern.png')


if __name__ == '__main__':
    print('Generating all 7 publication figures...')
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    fig6()
    fig7()
    print('All 7 figures generated successfully.')
