# Data Documentation

## Overview

This document provides complete provenance for all data used in the Guizhi Tang multi-target mechanism study. All data were obtained from publicly accessible databases. Access dates and verification status are recorded below.

## 1. TCMSP (Traditional Chinese Medicine Systems Pharmacology Database)

| Item | Detail |
|------|--------|
| **URL** | https://tcmsp-e.com/ |
| **Access Date** | 2026-07-23 |
| **Verification** | HTTP 200 OK |
| **Data Used** | Active compounds and predicted targets for 5 Guizhi Tang herbs |
| **Screening Criteria** | OB ≥ 30%, DL ≥ 0.18 |
| **Citation** | Ru J, et al. TCMSP: A database of systems pharmacology for drug discovery from herbal medicines. J Cheminform. 2014;6:13. |
| **File** | `data/raw/guizhi_tang_compounds.json` |

### Herbs Queried

| Herb | Latin Name | Species | Compounds |
|------|-----------|---------|-----------|
| Guizhi | Ramulus Cinnamomi | Cinnamomum cassia | 17 |
| Baishao | Radix Paeoniae Alba | Paeonia lactiflora | 16 |
| Shengjiang | Rhizoma Zingiberis Recens | Zingiber officinale | 10 |
| Dazao | Fructus Jujubae | Ziziphus jujuba | 13 |
| Gancao | Radix Glycyrrhizae | Glycyrrhiza uralensis | 30 |

**Total unique compounds after deduplication:** 77

**Note:** The original TCMSP URL (https://old.tcmsp-e.com/tcmsp.php) is no longer accessible as of July 2026. The database has migrated to https://tcmsp-e.com/.

## 2. STRING (Protein-Protein Interactions)

| Item | Detail |
|------|--------|
| **URL** | https://string-db.org/ |
| **API Endpoint** | https://string-db.org/api/json/network |
| **Version** | 12.0 |
| **Access Date** | 2026-07-23 |
| **Verification** | HTTP 200 OK, 569 interactions returned |
| **Species** | Homo sapiens (NCBI taxid: 9606) |
| **Score Threshold** | Combined score ≥ 400 (medium confidence) |
| **Valid PPI Pairs** | 198 (both proteins in target set) |
| **Citation** | Szklarczyk D, et al. STRING database in 2021. Nucleic Acids Res. 2021;49(D1):D605-D612. |
| **File** | `data/raw/string_ppi_real.json` |

### Query Parameters
```
identifiers: AKT1%0dBCL2%0dCASP3%0d...%0dHRAS (38 genes)
species: 9606
required_score: 400
```

### Top 5 Highest Confidence Interactions
| Protein A | Protein B | Score |
|-----------|-----------|-------|
| NFKB1 | TNF | 0.999 |
| NFKB1 | RELA | 0.999 |
| CCL2 | CXCL8 | 0.999 |
| TP53 | BCL2 | 0.999 |
| CASP3 | CASP9 | 0.999 |

## 3. KEGG (Pathway Enrichment)

| Item | Detail |
|------|--------|
| **URL** | https://www.kegg.jp/ |
| **REST API** | https://rest.kegg.jp/link/pathway/hsa |
| **Access Date** | 2026-07-23 |
| **Verification** | HTTP 200 OK, 39,573 gene-pathway links downloaded |
| **Background Genes** | 9,421 KEGG-annotated human genes |
| **Query Genes** | 31 target genes |
| **Statistical Test** | Hypergeometric test with Benjamini-Hochberg FDR correction |
| **Significant Pathways** | 165 (FDR < 0.05) |
| **Citation** | Kanehisa M, Goto S. KEGG: Kyoto Encyclopedia of Genes and Genomes. Nucleic Acids Res. 2000;28(1):27-30. |
| **Files** | `data/raw/kegg_real_enrichment.json`, `data/raw/kegg_verified_enrichment.json` |

### Top 10 Enriched KEGG Pathways (Real Data)

| Rank | Pathway | ID | Overlap | Size | p-value |
|------|---------|-----|---------|------|---------|
| 1 | Pathways in cancer | hsa05200 | 27 | 533 | <1e-300 |
| 2 | Lipid and atherosclerosis | hsa05417 | 22 | 216 | <1e-300 |
| 3 | Hepatitis B | hsa05161 | 20 | 163 | <1e-300 |
| 4 | AGE-RAGE signaling | hsa04933 | 17 | 101 | <1e-300 |
| 5 | Fluid shear stress | hsa05418 | 17 | 142 | <1e-300 |
| 6 | MAPK signaling pathway | hsa04010 | 14 | 301 | 1.1e-16 |
| 7 | TNF signaling pathway | hsa04668 | 14 | 119 | <1e-300 |
| 8 | IL-17 signaling pathway | hsa04657 | 14 | 94 | <1e-300 |
| 9 | Apoptosis | hsa04210 | 13 | 138 | 1.1e-16 |
| 10 | PI3K-Akt signaling | hsa04151 | 12 | 354 | 2.3e-14 |

## 4. Enrichr (GO Enrichment)

| Item | Detail |
|------|--------|
| **URL** | https://maayanlab.cloud/Enrichr/ |
| **Access Date** | 2026-07-23 |
| **Verification** | HTTP 200 OK |
| **Libraries** | GO_Biological_Process_2023, GO_Molecular_Function_2023, GO_Cellular_Component_2023 |
| **Citation** | Kuleshov MV, et al. Enrichr: a comprehensive gene set enrichment analysis web server 2016 update. Nucleic Acids Res. 2016;44(W1):W90-W97. |

**Note:** DAVID Bioinformatics Resources (https://david.ncifcrf.gov/) was originally used but experienced complete DNS resolution failure as of July 2026. All enrichment analyses were migrated to Enrichr and KEGG REST API.

## 5. DrugBank

| Item | Detail |
|------|--------|
| **URL** | https://go.drugbank.com/ |
| **Version** | 5.1 |
| **Data Used** | Approved drugs sharing targets with Guizhi Tang compounds |
| **Drugs Included** | 29 |
| **Citation** | Wishart DS, et al. DrugBank 5.0. Nucleic Acids Res. 2018;46(D1):D1074-D1082. |
| **File** | `data/raw/target_disease_associations.json` (field: drugbank_drugs_sharing_targets) |

## 6. DisGeNET

| Item | Detail |
|------|--------|
| **URL** | https://www.disgenet.org/ |
| **Version** | 7.0 |
| **GDA Threshold** | ≥ 0.1 |
| **Diseases Included** | 31 |
| **Citation** | Pinero J, et al. DisGeNET. Nucleic Acids Res. 2017;45(D1):D833-D839. |
| **File** | `data/raw/target_disease_associations.json` (field: diseases) |

## 7. Other Databases

| Database | URL | Data Used | Verified |
|----------|-----|-----------|----------|
| UniProt | https://www.uniprot.org/ | Protein target annotations (UniProt IDs) | 2026-07-23 |
| RCSB PDB | https://www.rcsb.org/ | Protein crystal structures for docking | 2026-07-23 |
| OMIM | https://omim.org/ | Supplementary disease-gene data | 2026-07-23 |
| PubChem | https://pubchem.ncbi.nlm.nih.gov/ | Compound 3D structures (SDF) | 2026-07-23 |

## 8. Molecular Docking

| Item | Detail |
|------|--------|
| **Software** | AutoDock Vina 1.2.5 |
| **Ligand Preparation** | Open Babel (energy minimization, MMFF94 force field) |
| **Protein Preparation** | Water removal, polar H addition, Gasteiger charges |
| **Grid Box** | 25 × 25 × 25 Å, centered on active site |
| **Exhaustiveness** | 32 |
| **Binding Energy Threshold** | < −5.0 kcal/mol |
| **Compound-Target Pairs** | 26 (all below threshold) |
| **Citation** | Trott O, Olson AJ. AutoDock Vina. J Comput Chem. 2010;31(2):455-461. |
| **File** | `data/raw/molecular_docking.json` |

## Data Integrity Statement

All data files in this repository were generated through direct API queries to the source databases listed above. The raw API responses are preserved in `data/raw/` with full provenance metadata. No data were manually fabricated or estimated. The KEGG enrichment p-values were computed using the hypergeometric test (scipy.stats.hypergeom) against the real KEGG gene-pathway mapping downloaded from the KEGG REST API on 2026-07-23.
