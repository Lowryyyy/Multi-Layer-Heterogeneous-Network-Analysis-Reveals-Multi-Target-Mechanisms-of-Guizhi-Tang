"""
Configuration for TCM-GNN Drug Repurposing Project
Guizhi Tang Multi-layer Heterogeneous Network
"""
import os
from pathlib import Path

# === Paths ===
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

for d in [DATA_DIR, RESULTS_DIR, RAW_DATA_DIR, PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# === Database URLs ===
TCMSP_BASE_URL = "https://old.tcmsp-e.com/tcmsp.php"
DRUGBANK_XML_URL = "https://go.drugbank.com/releases/latest"
OMIM_API_URL = "https://api.omim.org/api/entry"
DISGENET_API_URL = "https://www.disgenet.org/api"
STRING_API_URL = "https://string-db.org/api"

# API Keys (set via environment variables)
OMIM_API_KEY = os.environ.get("OMIM_API_KEY", "")
DRUGBANK_USER = os.environ.get("DRUGBANK_USER", "")
DRUGBANK_PASS = os.environ.get("DRUGBANK_PASS", "")

# === Guizhi Tang Herbs ===
# Latin names used in TCMSP queries
HERBS = {
    "Guizhi": {
        "chinese": "Guizhi",
        "latin": "Ramulus Cinnamomi",
        "species": "Cinnamomum cassia",
        "tcmsp_herb_id": "Guizhi",
    },
    "Baishao": {
        "chinese": "Baishao",
        "latin": "Radix Paeoniae Alba",
        "species": "Paeonia lactiflora",
        "tcmsp_herb_id": "Baishao",
    },
    "Shengjiang": {
        "chinese": "Shengjiang",
        "latin": "Rhizoma Zingiberis Recens",
        "species": "Zingiber officinale",
        "tcmsp_herb_id": "Shengjiang",
    },
    "Dazao": {
        "chinese": "Dazao",
        "latin": "Fructus Jujubae",
        "species": "Ziziphus jujuba",
        "tcmsp_herb_id": "Dazao",
    },
    "Gancao": {
        "chinese": "Gancao",
        "latin": "Radix Glycyrrhizae",
        "species": "Glycyrrhiza uralensis",
        "tcmsp_herb_id": "Gancao",
    },
}

# === Screening Criteria (TCMSP standard) ===
OB_THRESHOLD = 30.0   # Oral Bioavailability >= 30%
DL_THRESHOLD = 0.18   # Drug-Likeness >= 0.18

# === GNN Model Hyperparameters ===
HIDDEN_DIM = 128
NUM_GNN_LAYERS = 3
NUM_RELATION_TYPES = 7
DROPOUT = 0.3
LEARNING_RATE = 0.001
WEIGHT_DECAY = 5e-4
NUM_EPOCHS = 200
BATCH_SIZE = 1024
NEGATIVE_SAMPLE_RATIO = 5  # negative:positive ratio
PATIENCE = 20  # early stopping patience

# === Link Prediction Target ===
# We predict new compound -> disease links (drug repurposing)
PREDICTION_EDGE_TYPE = ("compound", "may_treat", "disease")

# === Molecular Docking ===
AUTODOCK_VINA_PATH = "vina"  # path to AutoDock Vina binary
DOCKING_EXHAUSTIVENESS = 32
DOCKING_NUM_MODES = 9

# === Visualization (SCI Publication Quality) ===
FIGURE_DPI = 300
NETWORK_LAYOUT = "spring"  # or "kamada_kawai"
NODE_SIZE_HERB = 900
NODE_SIZE_COMPOUND = 400
NODE_SIZE_TARGET = 300
NODE_SIZE_DISEASE = 550
NODE_SIZE_DRUG = 450

# SCI-grade color palette (Tableau 10 / Nature style)
SCI_COLORS = {
    "blue":    "#4E79A7",
    "orange":  "#F28E2B",
    "red":     "#E15759",
    "teal":    "#76B7B2",
    "green":   "#59A14F",
    "yellow":  "#EDC948",
    "purple":  "#B07AA1",
    "pink":    "#FF9DA7",
    "brown":   "#9C755F",
    "gray":    "#BAB0AC",
    "darkblue":"#2C5985",
    "darkred": "#A03A3C",
}

# Node type colors for heterogeneous graph
NODE_TYPE_COLORS = {
    "herb":      "#E15759",   # red
    "compound":  "#4E79A7",   # blue
    "target":    "#59A14F",   # green
    "disease":   "#F28E2B",   # orange
    "drug":      "#B07AA1",   # purple
}

# Edge type colors
EDGE_TYPE_COLORS = {
    ("herb", "contains", "compound"):         "#E15759",
    ("compound", "acts_on", "target"):          "#4E79A7",
    ("target", "associated_with", "disease"):   "#59A14F",
    ("drug", "targets_protein", "target"):      "#B07AA1",
    ("drug", "treats", "disease"):               "#9C755F",
    ("target", "interacts_with", "target"):      "#76B7B2",
    ("compound", "may_treat", "disease"):        "#F28E2B",
}

# Model colors for comparison charts
MODEL_COLORS = {
    "MLP Baseline":          "#BAB0AC",
    "Node2Vec + LR":        "#9C755F",
    "Simple GCN":           "#76B7B2",
    "R-GCN":                "#59A14F",
    "HetGNN":               "#4E79A7",
    "R-GCN (heterogeneous)": "#59A14F",
    "HetGNN (full, ours)":  "#4E79A7",
}

# Herb colors for compound source
HERB_COLORS = {
    "Guizhi":    "#E15759",
    "Baishao":   "#4E79A7",
    "Shengjiang": "#59A14F",
    "Dazao":    "#F28E2B",
    "Gancao":   "#B07AA1",
}

# Publication font settings
FONT_FAMILY = "Arial"
FONT_SIZE_TITLE = 14
FONT_SIZE_LABEL = 12
FONT_SIZE_TICK = 10
FONT_SIZE_LEGEND = 10
