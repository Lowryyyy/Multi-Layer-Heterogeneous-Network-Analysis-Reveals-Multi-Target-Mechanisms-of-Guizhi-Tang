"""Generate Graphical Abstract for Journal of Ethnopharmacology."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

# Publication style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica'],
    'font.size': 9,
})

# Okabe-Ito colors
BLUE = '#0072B2'
GREEN = '#009E73'
ORANGE = '#E69F00'
RED = '#D55E00'
PINK = '#CC79A7'
SKY = '#56B4E9'

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5.5)
ax.axis('off')

# Title
ax.text(5, 5.2, 'Graphical Abstract', fontsize=14, fontweight='bold',
        ha='center', va='top', color='#333333')

# === Left panel: Knowledge Graph Construction ===
# Box
box1 = FancyBboxPatch((0.3, 1.8), 2.8, 3.0, boxstyle="round,pad=0.1",
                       facecolor='#F0F4F8', edgecolor='#CCCCCC', linewidth=1)
ax.add_patch(box1)
ax.text(1.7, 4.55, 'Knowledge Graph', fontsize=9, fontweight='bold', ha='center')
ax.text(1.7, 4.25, 'Construction', fontsize=9, fontweight='bold', ha='center')

# Database icons
dbs = [('TCMSP', 0.6, 3.6), ('DrugBank', 1.7, 3.6), ('DisGeNET', 2.8, 3.6),
       ('OMIM', 0.6, 3.0), ('STRING', 1.7, 3.0), ('UniProt', 2.8, 3.0)]
for name, x, y in dbs:
    rect = FancyBboxPatch((x-0.35, y-0.15), 0.7, 0.3, boxstyle="round,pad=0.05",
                           facecolor=SKY, edgecolor='white', linewidth=0.5, alpha=0.8)
    ax.add_patch(rect)
    ax.text(x, y, name, fontsize=5.5, ha='center', va='center', color='white', fontweight='bold')

# Graph stats
ax.text(1.7, 2.4, '189 nodes | 1,602 edges', fontsize=7, ha='center', color='#555555')
ax.text(1.7, 2.1, '5 types | 7 relations', fontsize=7, ha='center', color='#555555')

# Node type legend
node_types = [('Herb', RED), ('Compound', BLUE), ('Target', GREEN), ('Disease', ORANGE), ('Drug', PINK)]
for i, (name, color) in enumerate(node_types):
    ax.plot(0.7 + i * 0.55, 1.95, 'o', color=color, markersize=5)
    ax.text(0.7 + i * 0.55, 1.82, name[0], fontsize=5, ha='center', color='#555555')

# === Arrow 1 ===
ax.annotate('', xy=(3.5, 3.3), xytext=(3.15, 3.3),
            arrowprops=dict(arrowstyle='->', color='#666666', lw=1.5))

# === Middle panel: GNN Model ===
box2 = FancyBboxPatch((3.6, 1.8), 2.6, 3.0, boxstyle="round,pad=0.1",
                       facecolor='#F0F8F0', edgecolor='#CCCCCC', linewidth=1)
ax.add_patch(box2)
ax.text(4.9, 4.55, 'HetGNN Model', fontsize=9, fontweight='bold', ha='center')
ax.text(4.9, 4.25, 'Link Prediction', fontsize=9, fontweight='bold', ha='center')

# Model details
details = ['3-layer GAT', '4 attention heads', '128 hidden dim', '238K parameters']
for i, d in enumerate(details):
    ax.text(4.9, 3.7 - i * 0.35, d, fontsize=7, ha='center', color='#555555')

# Performance
ax.text(4.9, 2.3, 'AUC: 0.871', fontsize=8, ha='center', fontweight='bold', color=GREEN)
ax.text(4.9, 2.0, 'F1: 0.560', fontsize=8, ha='center', fontweight='bold', color=GREEN)

# === Arrow 2 ===
ax.annotate('', xy=(6.6, 3.3), xytext=(6.25, 3.3),
            arrowprops=dict(arrowstyle='->', color='#666666', lw=1.5))

# === Right panel: Predictions & Validation ===
box3 = FancyBboxPatch((6.7, 1.8), 3.0, 3.0, boxstyle="round,pad=0.1",
                       facecolor='#FFF8F0', edgecolor='#CCCCCC', linewidth=1)
ax.add_patch(box3)
ax.text(8.2, 4.55, 'Predictions &', fontsize=9, fontweight='bold', ha='center')
ax.text(8.2, 4.25, 'Validation', fontsize=9, fontweight='bold', ha='center')

# Top predictions
preds = [
    ('Kaempferol \u2192 Pancreatic Ca', '0.846', RED),
    ('6-Gingerol \u2192 Breast Ca', '0.806', ORANGE),
    ('6-Gingerol \u2192 Lung Ca', '0.788', ORANGE),
]
for i, (name, score, color) in enumerate(preds):
    y = 3.7 - i * 0.4
    ax.plot(7.0, y, 's', color=color, markersize=6)
    ax.text(7.2, y, name, fontsize=6, va='center', color='#333333')
    ax.text(9.4, y, score, fontsize=7, va='center', fontweight='bold', color=color, ha='right')

# Validation
ax.text(8.2, 2.5, 'Molecular Docking', fontsize=7, ha='center', color='#555555')
ax.text(8.2, 2.2, 'KEGG/GO Enrichment', fontsize=7, ha='center', color='#555555')
ax.text(8.2, 1.95, '26 pairs < -5.0 kcal/mol', fontsize=6.5, ha='center', color=GREEN, fontweight='bold')

# Bottom: Key finding
ax.text(5, 1.3, 'Key Finding: Heterogeneous GNN with herb-node organization resolves degree bias',
        fontsize=8, ha='center', color='#333333', fontstyle='italic')
ax.text(5, 0.95, 'and yields diverse, biologically validated drug repurposing predictions for Guizhi Tang',
        fontsize=8, ha='center', color='#333333', fontstyle='italic')

# Journal name
ax.text(5, 0.4, 'Journal of Ethnopharmacology', fontsize=10, ha='center',
        fontweight='bold', color=RED)

plt.tight_layout(pad=0.5)
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
fig.savefig(os.path.join(output_dir, 'Graphical_Abstract.png'), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(output_dir, 'Graphical_Abstract.svg'), bbox_inches='tight')
plt.close()
print("Graphical Abstract saved.")
