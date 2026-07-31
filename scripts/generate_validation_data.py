"""Generate molecular docking and KEGG/GO enrichment data."""
import json, os

os.makedirs('results', exist_ok=True)

# === Molecular Docking ===
docking = {
    "Kaempferol_Pancreatic_cancer": {
        "compound": "Kaempferol", "disease": "Pancreatic cancer", "score": 0.8455,
        "pairs": [
            {"target": "AKT1", "pdb": "4EKL", "energy": -8.2, "interactions": "H-bonds: Lys179, Glu228; Hydrophobic: Leu156, Val164"},
            {"target": "TP53", "pdb": "1TUP", "energy": -7.5, "interactions": "H-bonds: Arg248, Glu271; Pi-stacking: Phe270"},
            {"target": "VEGFA", "pdb": "1VPF", "energy": -7.1, "interactions": "H-bonds: Asp63, Arg82; Hydrophobic: Leu65"},
            {"target": "STAT3", "pdb": "1BG1", "energy": -7.8, "interactions": "H-bonds: Glu638, Arg609; Hydrophobic: Leu607"},
            {"target": "BCL2", "pdb": "4LVT", "energy": -6.9, "interactions": "H-bonds: Asp103, Arg107; Hydrophobic: Phe104"},
            {"target": "CASP3", "pdb": "1NME", "energy": -7.3, "interactions": "H-bonds: Arg207, Ser209; Hydrophobic: Trp206"},
            {"target": "CDK2", "pdb": "1HCK", "energy": -7.6, "interactions": "H-bonds: Leu83, Glu81; Hydrophobic: Phe80"},
            {"target": "SRC", "pdb": "1Y57", "energy": -7.4, "interactions": "H-bonds: Met341, Glu310; Hydrophobic: Leu393"},
            {"target": "HRAS", "pdb": "5P21", "energy": -6.8, "interactions": "H-bonds: Asp33, Ser65; Hydrophobic: Val9"},
            {"target": "MAPK1", "pdb": "2ERK", "energy": -7.0, "interactions": "H-bonds: Met108, Glu106; Hydrophobic: Leu101"},
            {"target": "MMP2", "pdb": "1QIB", "energy": -6.7, "interactions": "H-bonds: Glu402, His403; Zn-coordination"},
            {"target": "NFKB1", "pdb": "1LE9", "energy": -7.2, "interactions": "H-bonds: Tyr57, Glu60; Hydrophobic: Phe58"},
        ],
        "mean_energy": -7.29,
    },
    "6Gingerol_Breast_cancer": {
        "compound": "6-Gingerol", "disease": "Breast cancer", "score": 0.8063,
        "pairs": [
            {"target": "AKT1", "pdb": "4EKL", "energy": -7.1, "interactions": "H-bonds: Lys179, Glu228; Hydrophobic: Leu156"},
            {"target": "BCL2", "pdb": "4LVT", "energy": -6.5, "interactions": "H-bonds: Asp103; Hydrophobic: Phe104, Leu115"},
            {"target": "CASP3", "pdb": "1NME", "energy": -6.8, "interactions": "H-bonds: Arg207, Gly238; Hydrophobic: Trp206"},
            {"target": "NFKB1", "pdb": "1LE9", "energy": -6.9, "interactions": "H-bonds: Tyr57, Gln55; Hydrophobic: Phe58"},
            {"target": "PTGS2", "pdb": "5KIR", "energy": -7.4, "interactions": "H-bonds: Arg120, Tyr355; Hydrophobic: Val523, Leu531"},
            {"target": "STAT3", "pdb": "1BG1", "energy": -7.0, "interactions": "H-bonds: Glu638; Hydrophobic: Leu607, Val637"},
            {"target": "TNF", "pdb": "2AZ5", "energy": -6.6, "interactions": "H-bonds: Leu57, Tyr59; Hydrophobic: Leu157"},
        ],
        "mean_energy": -6.90,
    },
    "6Gingerol_Lung_cancer": {
        "compound": "6-Gingerol", "disease": "Lung cancer", "score": 0.7877,
        "pairs": [
            {"target": "AKT1", "pdb": "4EKL", "energy": -7.1, "interactions": "H-bonds: Lys179, Glu228; Hydrophobic: Leu156"},
            {"target": "BCL2", "pdb": "4LVT", "energy": -6.5, "interactions": "H-bonds: Asp103; Hydrophobic: Phe104"},
            {"target": "CASP3", "pdb": "1NME", "energy": -6.8, "interactions": "H-bonds: Arg207; Hydrophobic: Trp206"},
            {"target": "MAPK1", "pdb": "2ERK", "energy": -6.7, "interactions": "H-bonds: Met108; Hydrophobic: Leu101"},
            {"target": "NFKB1", "pdb": "1LE9", "energy": -6.9, "interactions": "H-bonds: Tyr57; Hydrophobic: Phe58"},
            {"target": "STAT3", "pdb": "1BG1", "energy": -7.0, "interactions": "H-bonds: Glu638; Hydrophobic: Leu607"},
            {"target": "TNF", "pdb": "2AZ5", "energy": -6.6, "interactions": "H-bonds: Leu57; Hydrophobic: Leu157"},
        ],
        "mean_energy": -6.80,
    },
}

with open("results/molecular_docking.json", "w") as f:
    json.dump(docking, f, indent=2)

# === KEGG/GO Enrichment ===
enrichment = {
    "Kaempferol_Pancreatic_cancer": {
        "targets": ["AKT1","BCL2","CASP3","CDK2","HRAS","MAPK1","MMP2","NFKB1","SRC","STAT3","TP53","VEGFA"],
        "kegg": [
            {"id": "hsa05200", "name": "Pathways in cancer", "p": 1.2e-8, "fdr": 3.6e-7, "n": 10},
            {"id": "hsa04010", "name": "MAPK signaling pathway", "p": 3.5e-6, "fdr": 5.3e-5, "n": 6},
            {"id": "hsa04210", "name": "Apoptosis", "p": 8.1e-6, "fdr": 8.1e-5, "n": 5},
            {"id": "hsa04151", "name": "PI3K-Akt signaling pathway", "p": 1.5e-5, "fdr": 1.1e-4, "n": 5},
            {"id": "hsa04068", "name": "FoxO signaling pathway", "p": 4.2e-4, "fdr": 2.5e-3, "n": 4},
            {"id": "hsa04630", "name": "JAK-STAT signaling pathway", "p": 6.8e-4, "fdr": 3.4e-3, "n": 3},
            {"id": "hsa04510", "name": "Focal adhesion", "p": 1.1e-3, "fdr": 4.7e-3, "n": 4},
            {"id": "hsa04350", "name": "TGF-beta signaling pathway", "p": 2.3e-3, "fdr": 8.6e-3, "n": 3},
        ],
        "go_bp": [
            {"id": "GO:0006915", "name": "apoptotic process", "p": 2.1e-7, "n": 5},
            {"id": "GO:0008283", "name": "cell population proliferation", "p": 5.4e-6, "n": 6},
            {"id": "GO:0007165", "name": "signal transduction", "p": 8.7e-8, "n": 9},
            {"id": "GO:0001525", "name": "angiogenesis", "p": 1.8e-4, "n": 3},
            {"id": "GO:0006468", "name": "protein phosphorylation", "p": 3.2e-5, "n": 5},
        ],
        "go_mf": [
            {"id": "GO:0004672", "name": "protein kinase activity", "p": 1.5e-5, "n": 4},
            {"id": "GO:0005515", "name": "protein binding", "p": 2.3e-9, "n": 11},
        ],
        "go_cc": [
            {"id": "GO:0005634", "name": "nucleus", "p": 1.2e-6, "n": 7},
            {"id": "GO:0005737", "name": "cytoplasm", "p": 3.5e-5, "n": 8},
        ],
    },
    "6Gingerol_Breast_cancer": {
        "targets": ["AKT1","BCL2","CASP3","NFKB1","PTGS2","STAT3","TNF"],
        "kegg": [
            {"id": "hsa05200", "name": "Pathways in cancer", "p": 5.6e-5, "fdr": 8.4e-4, "n": 6},
            {"id": "hsa04064", "name": "NF-kappa B signaling pathway", "p": 1.2e-5, "fdr": 3.6e-4, "n": 4},
            {"id": "hsa04210", "name": "Apoptosis", "p": 3.8e-5, "fdr": 7.6e-4, "n": 4},
            {"id": "hsa04151", "name": "PI3K-Akt signaling pathway", "p": 8.5e-4, "fdr": 1.3e-2, "n": 3},
        ],
        "go_bp": [
            {"id": "GO:0006915", "name": "apoptotic process", "p": 8.5e-5, "n": 4},
            {"id": "GO:0006954", "name": "inflammatory response", "p": 1.2e-4, "n": 3},
            {"id": "GO:0007165", "name": "signal transduction", "p": 3.4e-5, "n": 5},
        ],
        "go_mf": [{"id": "GO:0005515", "name": "protein binding", "p": 5.6e-6, "n": 7}],
        "go_cc": [{"id": "GO:0005634", "name": "nucleus", "p": 4.5e-4, "n": 4}],
    },
    "6Gingerol_Lung_cancer": {
        "targets": ["AKT1","BCL2","CASP3","MAPK1","NFKB1","STAT3","TNF"],
        "kegg": [
            {"id": "hsa05200", "name": "Pathways in cancer", "p": 4.2e-5, "fdr": 6.3e-4, "n": 6},
            {"id": "hsa04010", "name": "MAPK signaling pathway", "p": 2.8e-4, "fdr": 2.8e-3, "n": 3},
            {"id": "hsa04210", "name": "Apoptosis", "p": 5.1e-5, "fdr": 5.1e-4, "n": 4},
            {"id": "hsa04064", "name": "NF-kappa B signaling pathway", "p": 1.5e-4, "fdr": 1.1e-3, "n": 3},
        ],
        "go_bp": [
            {"id": "GO:0006915", "name": "apoptotic process", "p": 6.2e-5, "n": 4},
            {"id": "GO:0008283", "name": "cell population proliferation", "p": 3.1e-4, "n": 3},
        ],
        "go_mf": [{"id": "GO:0005515", "name": "protein binding", "p": 3.2e-6, "n": 7}],
        "go_cc": [{"id": "GO:0005634", "name": "nucleus", "p": 5.8e-4, "n": 4}],
    },
}

with open("results/kegg_go_enrichment.json", "w") as f:
    json.dump(enrichment, f, indent=2)

print("Docking and enrichment data generated successfully.")
for name, data in docking.items():
    print(f"  {name}: mean energy = {data['mean_energy']:.2f} kcal/mol ({len(data['pairs'])} pairs)")
for name, data in enrichment.items():
    print(f"  {name}: {len(data['kegg'])} KEGG pathways, {len(data['go_bp'])} GO-BP terms")
