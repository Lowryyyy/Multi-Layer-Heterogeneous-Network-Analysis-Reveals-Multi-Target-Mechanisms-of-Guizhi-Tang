"""Generate new publication figures for JBSD submission: KEGG bubble plot, docking chart, PPI network."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import json, os

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica'],
    'font.size': 8,
    'axes.labelsize': 9,
    'axes.titlesize': 10,
    'xtick.labelsize': 7,
    'ytick.labelsize': 7,
    'legend.fontsize': 7,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 300,
    'savefig.dpi': 300,
})

BLUE = '#0072B2'
GREEN = '#009E73'
ORANGE = '#E69F00'
RED = '#D55E00'
PINK = '#CC79A7'

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(output_dir, exist_ok=True)

# ============================================================
# Figure: KEGG Bubble Plot
# ============================================================
def kegg_bubble():
    fig, ax = plt.subplots(figsize=(5.5, 4))

    # Data: (pathway, n_genes, p_value, prediction_label)
    pathways = [
        ('Pathways in cancer', 10, 1.2e-8, 'Kaempferol \u2192 Pancreatic Ca'),
        ('MAPK signaling pathway', 6, 3.5e-6, 'Kaempferol \u2192 Pancreatic Ca'),
        ('Apoptosis', 5, 8.1e-6, 'Kaempferol \u2192 Pancreatic Ca'),
        ('PI3K-Akt signaling pathway', 5, 1.5e-5, 'Kaempferol \u2192 Pancreatic Ca'),
        ('FoxO signaling pathway', 4, 4.2e-4, 'Kaempferol \u2192 Pancreatic Ca'),
        ('JAK-STAT signaling pathway', 3, 6.8e-4, 'Kaempferol \u2192 Pancreatic Ca'),
        ('Pathways in cancer', 6, 5.6e-5, '6-Gingerol \u2192 Breast Ca'),
        ('NF-\u03baB signaling pathway', 4, 1.2e-5, '6-Gingerol \u2192 Breast Ca'),
        ('Apoptosis', 4, 3.8e-5, '6-Gingerol \u2192 Breast Ca'),
        ('Pathways in cancer', 6, 4.2e-5, '6-Gingerol \u2192 Lung Ca'),
        ('MAPK signaling pathway', 3, 2.8e-4, '6-Gingerol \u2192 Lung Ca'),
        ('NF-\u03baB signaling pathway', 3, 1.5e-4, '6-Gingerol \u2192 Lung Ca'),
    ]

    colors_map = {
        'Kaempferol \u2192 Pancreatic Ca': RED,
        '6-Gingerol \u2192 Breast Ca': ORANGE,
        '6-Gingerol \u2192 Lung Ca': BLUE,
    }

    y_labels = []
    for i, (name, n_genes, pval, pred) in enumerate(pathways):
        neg_log_p = -np.log10(pval)
        color = colors_map[pred]
        size = n_genes * 35
        ax.scatter(neg_log_p, i, s=size, c=color, alpha=0.8, edgecolors='white', linewidths=0.6, zorder=3)
        y_labels.append(f'{name} ({pred.split(" ")[0]})')

    ax.set_yticks(range(len(pathways)))
    ax.set_yticklabels(y_labels, fontsize=6.5)
    ax.set_xlabel('$-\\log_{10}$(p-value)', fontsize=9)
    ax.set_title('KEGG Pathway Enrichment Analysis', fontsize=10, fontweight='bold', pad=8)
    ax.set_xlim(2.5, 8.5)
    ax.set_ylim(-0.5, len(pathways) - 0.5)
    ax.invert_yaxis()

    # Color legend - outside plot
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=RED, edgecolor='white', label='Kaempferol \u2192 Pancreatic Ca'),
        Patch(facecolor=ORANGE, edgecolor='white', label='6-Gingerol \u2192 Breast Ca'),
        Patch(facecolor=BLUE, edgecolor='white', label='6-Gingerol \u2192 Lung Ca'),
    ]
    # Size legend
    size_handles = [
        plt.Line2D([0],[0], marker='o', color='w', markerfacecolor='#AAAAAA',
                   markersize=np.sqrt(3*35/np.pi), label='3 genes'),
        plt.Line2D([0],[0], marker='o', color='w', markerfacecolor='#AAAAAA',
                   markersize=np.sqrt(6*35/np.pi), label='6 genes'),
        plt.Line2D([0],[0], marker='o', color='w', markerfacecolor='#AAAAAA',
                   markersize=np.sqrt(10*35/np.pi), label='10 genes'),
    ]

    leg1 = ax.legend(handles=legend_elements, loc='upper left',
                     bbox_to_anchor=(1.02, 1.0), frameon=True, framealpha=0.95,
                     edgecolor='#CCCCCC', fontsize=6.5, title='Prediction',
                     title_fontsize=7)
    ax.add_artist(leg1)
    ax.legend(handles=size_handles, loc='upper left',
              bbox_to_anchor=(1.02, 0.55), frameon=True, framealpha=0.95,
              edgecolor='#CCCCCC', fontsize=6.5, title='Gene count',
              title_fontsize=7)

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'kegg_bubble.png'), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(output_dir, 'kegg_bubble.svg'), bbox_inches='tight')
    plt.close()
    print('  Saved: kegg_bubble.png')

# ============================================================
# Figure: Molecular Docking Results
# ============================================================
def docking_chart():
    fig, ax = plt.subplots(figsize=(5, 3.5))

    pairs = [
        ('Kaempferol-AKT1', -8.2),
        ('Kaempferol-STAT3', -7.8),
        ('Kaempferol-CDK2', -7.6),
        ('Kaempferol-TP53', -7.5),
        ('Kaempferol-SRC', -7.4),
        ('6Gingerol-PTGS2', -7.4),
        ('Kaempferol-CASP3', -7.3),
        ('Kaempferol-NFKB1', -7.2),
        ('Kaempferol-VEGFA', -7.1),
        ('6Gingerol-AKT1', -7.1),
        ('Kaempferol-MAPK1', -7.0),
        ('6Gingerol-STAT3', -7.0),
        ('Kaempferol-BCL2', -6.9),
        ('6Gingerol-NFKB1', -6.9),
        ('6Gingerol-CASP3', -6.8),
        ('Kaempferol-HRAS', -6.8),
        ('6Gingerol-MAPK1', -6.7),
        ('Kaempferol-MMP2', -6.7),
        ('6Gingerol-TNF', -6.6),
        ('6Gingerol-BCL2', -6.5),
    ]

    names = [p[0] for p in pairs]
    energies = [p[1] for p in pairs]
    colors = [RED if 'Kaempferol' in n else ORANGE for n in names]

    y = np.arange(len(names))
    bars = ax.barh(y, energies, color=colors, edgecolor='white', linewidth=0.5, height=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=6)
    ax.set_xlabel('Binding Energy (kcal/mol)')
    ax.set_title('Molecular Docking Results', fontsize=10, fontweight='bold')
    ax.axvline(x=-5.0, color='#666666', linestyle='--', linewidth=0.8, alpha=0.7)
    ax.text(-5.0, len(names)-0.3, 'Threshold\n(-5.0)', fontsize=5.5, color='#666666', ha='center')
    ax.invert_yaxis()

    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=RED, label='Kaempferol'), Patch(facecolor=ORANGE, label='6-Gingerol')],
              loc='lower left', frameon=False, fontsize=7)

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'docking_results.png'), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(output_dir, 'docking_results.svg'), bbox_inches='tight')
    plt.close()
    print('  Saved: docking_results.png')

# ============================================================
# Figure: GO Enrichment Bar Plot
# ============================================================
def go_enrichment():
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(7, 3))

    # BP
    bp = [('apoptotic process', 5, 2.1e-7), ('signal transduction', 9, 8.7e-8),
          ('cell proliferation', 6, 5.4e-6), ('protein phosphorylation', 5, 3.2e-5),
          ('angiogenesis', 3, 1.8e-4), ('inflammatory response', 3, 1.2e-4)]
    bp_names = [b[0] for b in bp]
    bp_neg_log_p = [-np.log10(b[2]) for b in bp]
    bp_n = [b[1] for b in bp]
    ax1.barh(range(len(bp_names)), bp_neg_log_p, color=BLUE, edgecolor='white', height=0.6)
    ax1.set_yticks(range(len(bp_names)))
    ax1.set_yticklabels(bp_names, fontsize=6)
    ax1.set_xlabel('$-\\log_{10}$(p)')
    ax1.set_title('(A) Biological Process', fontsize=9, fontweight='bold')
    ax1.invert_yaxis()

    # MF
    mf = [('protein binding', 11, 2.3e-9), ('protein kinase activity', 4, 1.5e-5),
          ('DNA binding', 3, 4.1e-4)]
    mf_names = [m[0] for m in mf]
    mf_neg_log_p = [-np.log10(m[2]) for m in mf]
    ax2.barh(range(len(mf_names)), mf_neg_log_p, color=GREEN, edgecolor='white', height=0.6)
    ax2.set_yticks(range(len(mf_names)))
    ax2.set_yticklabels(mf_names, fontsize=6)
    ax2.set_xlabel('$-\\log_{10}$(p)')
    ax2.set_title('(B) Molecular Function', fontsize=9, fontweight='bold')
    ax2.invert_yaxis()

    # CC
    cc = [('nucleus', 7, 1.2e-6), ('cytoplasm', 8, 3.5e-5), ('plasma membrane', 5, 2.1e-4)]
    cc_names = [c[0] for c in cc]
    cc_neg_log_p = [-np.log10(c[2]) for c in cc]
    ax3.barh(range(len(cc_names)), cc_neg_log_p, color=ORANGE, edgecolor='white', height=0.6)
    ax3.set_yticks(range(len(cc_names)))
    ax3.set_yticklabels(cc_names, fontsize=6)
    ax3.set_xlabel('$-\\log_{10}$(p)')
    ax3.set_title('(C) Cellular Component', fontsize=9, fontweight='bold')
    ax3.invert_yaxis()

    plt.tight_layout(w_pad=1.5)
    fig.savefig(os.path.join(output_dir, 'go_enrichment.png'), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(output_dir, 'go_enrichment.svg'), bbox_inches='tight')
    plt.close()
    print('  Saved: go_enrichment.png')

# ============================================================
# Figure: Traditional-Modern Concordance
# ============================================================
def traditional_modern():
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)

    # Traditional uses (left)
    trad = [
        (1.5, 5.5, 'Common cold\n(Shang Han)'),
        (1.5, 4.2, 'Rheumatic\ndisease'),
        (1.5, 2.9, 'Gastric\nulcer'),
        (1.5, 1.6, 'Cardiovascular\ndisorders'),
    ]
    for x, y, label in trad:
        rect = plt.Rectangle((x-1.2, y-0.4), 2.4, 0.8, facecolor='#FDEBD0',
                              edgecolor=ORANGE, linewidth=1, alpha=0.8, zorder=2)
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=6.5, fontweight='bold', zorder=3)

    ax.text(1.5, 6.5, 'Traditional\nIndications', ha='center', fontsize=9, fontweight='bold', color=ORANGE)

    # Modern predictions (right)
    modern = [
        (8.5, 5.5, 'Pancreatic\ncancer'),
        (8.5, 4.2, 'Breast\ncancer'),
        (8.5, 2.9, 'Lung\ncancer'),
        (8.5, 1.6, 'Coronary artery\ndisease'),
    ]
    for x, y, label in modern:
        rect = plt.Rectangle((x-1.2, y-0.4), 2.4, 0.8, facecolor='#D5F5E3',
                              edgecolor=GREEN, linewidth=1, alpha=0.8, zorder=2)
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=6.5, fontweight='bold', zorder=3)

    ax.text(8.5, 6.5, 'GNN-Predicted\nAssociations', ha='center', fontsize=9, fontweight='bold', color=GREEN)

    # Shared mechanisms (center)
    mechs = [
        (5, 5.5, 'TNF / NF-\u03baB\ninflammation'),
        (5, 4.2, 'AKT1 / PI3K\nsurvival'),
        (5, 2.9, 'CASP3 / BCL2\napoptosis'),
        (5, 1.6, 'STAT3 / VEGFA\nangiogenesis'),
    ]
    for x, y, label in mechs:
        rect = plt.Rectangle((x-1.3, y-0.4), 2.6, 0.8, facecolor='#EBF5FB',
                              edgecolor=BLUE, linewidth=1, alpha=0.8, zorder=2)
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=6, color=BLUE, zorder=3)

    ax.text(5, 6.5, 'Shared Molecular\nMechanisms', ha='center', fontsize=9, fontweight='bold', color=BLUE)

    # Arrows
    for y in [5.5, 4.2, 2.9, 1.6]:
        ax.annotate('', xy=(3.7, y), xytext=(2.7, y),
                    arrowprops=dict(arrowstyle='->', color='#999999', lw=1))
        ax.annotate('', xy=(7.3, y), xytext=(6.3, y),
                    arrowprops=dict(arrowstyle='->', color='#999999', lw=1))

    ax.set_title('Traditional Indications and Modern Predictions:\nConvergent Molecular Mechanisms',
                 fontsize=10, fontweight='bold', pad=10)

    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, 'traditional_modern.png'), dpi=300, bbox_inches='tight')
    fig.savefig(os.path.join(output_dir, 'traditional_modern.svg'), bbox_inches='tight')
    plt.close()
    print('  Saved: traditional_modern.png')


print('Generating new figures for JBSD submission...')
kegg_bubble()
docking_chart()
go_enrichment()
traditional_modern()
print('All new figures generated.')
