# Data Documentation for Guizhi Tang GNN Drug Repurposing Study

## Overview

This document describes all raw data sources, collection methods, processing steps, and file formats used in the Guizhi Tang multi-layer heterogeneous knowledge graph and GNN drug repurposing study.

## Data Sources

### 1. TCMSP (Traditional Chinese Medicine Systems Pharmacology Database)

| Item | Detail |
|------|--------|
| URL | https://old.tcmsp-e.com/tcmsp.php |
| Version | Current as of 2024 |
| Data Used | Active compounds and predicted targets for 5 herbs |
| Screening Criteria | Oral Bioavailability (OB) >= 30%, Drug-Likeness (DL) >= 0.18 |
| Citation | Ru J, et al. TCMSP: A database of systems pharmacology for drug discovery from herbal medicines. J Cheminform. 2014;6:13. |

**Herbs queried:**

| Herb | Latin Name | Species | Compounds Retrieved |
|------|-----------|---------|-------------------|
| Guizhi | Ramulus Cinnamomi | Cinnamomum cassia | 17 |
| Baishao | Radix Paeoniae Alba | Paeonia lactiflora | 16 |
| Shengjiang | Rhizoma Zingiberis Recens | Zingiber officinale | 10 |
| Dazao | Fructus Jujubae | Ziziphus jujuba | 13 |
| Gancao | Radix Glycyrrhizae | Glycyrrhiza uralensis | 30 |

**Total unique compounds after deduplication:** 77

**Data file:** `data/guizhi_tang_compounds.json`

### 2. DrugBank

| Item | Detail |
|------|--------|
| URL | https://go.drugbank.com/ |
| Version | 5.1 |
| Data Used | Drug-target interactions for approved drugs sharing targets with Guizhi Tang compounds |
| Citation | Wishart DS, et al. DrugBank 5.0. Nucleic Acids Res. 2018;46(D1):D1074-D1082. |

**Drugs included:** 29 approved drugs (Celecoxib, Aspirin, Dasatinib, Lapatinib, Sunitinib, Imatinib, Sorafenib, etc.)

**Selection criteria:** Drugs that share >= 1 protein target with Guizhi Tang compounds.

**Data file:** `data/target_disease_associations.json` (field: `drugbank_drugs_sharing_targets`)

### 3. DisGeNET

| Item | Detail |
|------|--------|
| URL | https://www.disgenet.org/ |
| Version | 7.0 |
| Data Used | Gene-disease associations |
| GDA Threshold | >= 0.1 |
| Citation | Pinero J, et al. DisGeNET. Nucleic Acids Res. 2017;45(D1):D833-D839. |

**Diseases included:** 31 diseases across 8 categories (Autoimmune/Inflammatory, Cardiovascular, Metabolic, Neurological, Oncology, Respiratory, Gastrointestinal, Psychiatric, etc.)

**Data file:** `data/target_disease_associations.json` (field: `diseases`)

### 4. OMIM (Online Mendelian Inheritance in Man)

| Item | Detail |
|------|--------|
| URL | https://omim.org/ |
| Data Used | Supplementary genetic disease data |
| Citation | Amberger JS, et al. OMIM.org. Nucleic Acids Res. 2019;47(D1):D1038-D1043. |

### 5. STRING (Search Tool for the Retrieval of Interacting Genes/Proteins)

| Item | Detail |
|------|--------|
| URL | https://string-db.org/ |
| Version | 12.0 |
| Data Used | Protein-protein interactions |
| Minimum Combined Score | 400 (medium confidence) |
| Species | Homo sapiens (9606) |
| Citation | Szklarczyk D, et al. STRING database in 2021. Nucleic Acids Res. 2021;49(D1):D605-D612. |

**PPI edges included:** 218 protein-protein interaction pairs across major signaling pathways (PI3K-Akt, p53, Apoptosis, TNF/NF-kB, MAPK, COX/NOS, Nrf2, VEGF, Cell Cycle, Kinase signaling, Nuclear Receptors, etc.)

**Data file:** PPI pairs are hardcoded in `src/graph_builder.py` method `_get_ppi_pairs()` based on STRING database queries.

### 6. UniProt (Universal Protein Resource)

| Item | Detail |
|------|--------|
| URL | https://www.uniprot.org/ |
| Data Used | Protein target annotations (gene names, UniProt IDs, full names) |

**Targets included:** 47 protein targets with UniProt IDs

**Data file:** `data/compound_target_interactions.json` (field: `target_details`)

## Data Files

### File Structure

```
data/
  guizhi_tang_compounds.json          # Herb-compound data from TCMSP
  compound_target_interactions.json    # Compound-target pairs from TCMSP
  target_disease_associations.json     # Target-disease + Drug data
  processed/
    graph_metadata.json               # Processed graph metadata
    feature_dims.json                 # Node feature dimensions
results/
  graph_statistics.json               # Graph statistics
  test_metrics.json                   # Model test performance
  top_predictions.json                # Drug repurposing predictions
  path_analysis.json                  # Mechanistic path analysis
  threshold_analysis.json             # Threshold optimization results
  training_history.json               # Training curves data
  all_experiment_results.json         # Complete experiment results
  ablation/
    ablation_results.json             # Ablation study results
```

### File Formats

**guizhi_tang_compounds.json:**
```json
{
  "herbs": {
    "Guizhi": {
      "latin": "Ramulus Cinnamomi",
      "species": "Cinnamomum cassia",
      "compounds": [
        {"mol_id": "MOL000492", "name": "Cinnamaldehyde", "ob": 53.4, "dl": 0.09},
        ...
      ]
    }
  }
}
```

**compound_target_interactions.json:**
```json
{
  "compounds": [
    {"mol_id": "MOL000098", "name": "Quercetin", "targets": ["PTGS1", "PTGS2", ...]},
    ...
  ],
  "target_details": [
    {"gene": "PTGS1", "uniprot": "P23219", "name": "...", "alias": "COX-1"},
    ...
  ]
}
```

**target_disease_associations.json:**
```json
{
  "diseases": [
    {"disease_id": "DOID:633", "name": "Rheumatoid arthritis", "icd10": "M06.9",
     "category": "Autoimmune/Inflammatory", "associated_targets": [...]},
    ...
  ],
  "drugbank_drugs_sharing_targets": [
    {"drug_id": "DB00482", "name": "Celecoxib", "targets": ["PTGS2"], "indication": "..."},
    ...
  ],
  "compound_disease_known_links": {
    "Quercetin": ["Rheumatoid arthritis", "Hypertension", ...],
    ...
  }
}
```

## Graph Construction Summary

| Metric | Value |
|--------|-------|
| Total Nodes | 189 |
| Herb nodes | 5 |
| Compound nodes | 77 |
| Target nodes | 47 |
| Disease nodes | 31 |
| Drug nodes | 29 |
| Total Edges | 1,602 |
| herb-contains-compound | 86 |
| compound-acts_on-target | 403 |
| target-associated_with-disease | 415 |
| drug-targets_protein-target | 60 |
| drug-treats-disease | 266 |
| target-interacts_with-target | 218 |
| compound-may_treat-disease | 154 |

## Compound-Disease Training Labels

The `compound_disease_known_links` field in `target_disease_associations.json` contains 154 known compound-disease associations derived from:
1. Compound-target-disease path analysis (compound targets overlap with disease-associated genes)
2. Published experimental evidence in the literature
3. Clinical application records in TCM pharmacopoeia

These links serve as ground truth for training the GNN link prediction model.

## Model Training Configuration

| Parameter | Value |
|-----------|-------|
| Model | HetGNN (Heterogeneous Graph Neural Network) |
| Hidden dimension | 128 |
| Number of layers | 3 |
| Attention heads | 4 |
| Total parameters | 238,081 |
| Optimizer | Adam |
| Learning rate | 0.001 |
| Weight decay | 5e-4 |
| Dropout | 0.3 |
| Loss function | BCEWithLogitsLoss |
| Negative sampling ratio | 5:1 |
| Train/Val/Test split | 70/15/15 |
| Early stopping patience | 20 epochs |
| Max epochs | 80 |
| Gradient clipping | max norm 1.0 |

## Software Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.10 | Runtime |
| PyTorch | 1.13.1 | Deep learning framework |
| scikit-learn | >=1.3 | Metrics, cross-validation |
| numpy | >=1.24 | Numerical computing |
| matplotlib | >=3.7 | Visualization |
| networkx | >=3.0 | Graph analysis |
| python-docx | 1.2.0 | DOCX generation |
| requests | >=2.28 | API data collection |

## Reproducibility

To reproduce all results:

```bash
# Install dependencies
pip install -r requirements.txt

# Run main pipeline
python run_pipeline.py --model hetgnn --epochs 80

# Run R-GCN comparison
python run_pipeline.py --model rgcn --epochs 80 --results-dir results_rgcn

# Run all experiments (baselines, ablation, cross-validation)
python run_experiments.py

# Generate paper
python generate_paper.py
```

## Data Availability Statement

All data used in this study are derived from publicly available databases:
- TCMSP: https://old.tcmsp-e.com/tcmsp.php (free access)
- DrugBank: https://go.drugbank.com/ (free for academic use)
- DisGeNET: https://www.disgenet.org/ (free access)
- OMIM: https://omim.org/ (free for academic use with API key)
- STRING: https://string-db.org/ (free for academic use)
- UniProt: https://www.uniprot.org/ (free access)

The processed datasets and code are available in the project repository.
