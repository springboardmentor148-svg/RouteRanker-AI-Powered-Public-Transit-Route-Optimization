# RouteRanker Module 4: Train/Validation Strategy and Evaluation Architecture

**Project:** AI-Based Public Transit Route Optimization for Indian Cities (RouteRanker)  
**Dataset:** 8 Indian Transit Networks (`Ahmedabad`, `Bengaluru`, `Davangere`, `Delhi`, `HDBRT`, `Mumbai`, `Pune`, `Rajkot`)  
**Active Modeling Routes:** 9,233 routes  
**Isolated Unserved Routes:** 682 routes  
**Random Seed:** 42  
**Split Ratio:** 80% Training / 20% Validation (Stratified by Agency)

---

## 1. Partitioning Strategy & Small-City Balance

To prevent data leakage (Rule 5) and ensure representative cross-city evaluation, an **80:20 stratified split** was executed on the 9,233 active routes:
* **Training Partition (`X_train`):** **7,386 routes** (80.0%)
* **Validation Partition (`X_val`):** **1,847 routes** (20.0%)

### Exact Counts and Proportions per City:

| Municipal Transit Network | Total Active Routes | Train Set (80%) | Val Set (20%) | Municipal Share in Split | Small-Agency Handling & Representation |
|---|---:|---:|---:|:---:|---|
| **Bengaluru (BMTC)** | 4,416 | 3,533 | 883 | 47.83% | Large network; fully representative across both splits |
| **Delhi (DTC)** | 1,187 | 949 | 238 | 12.86% | Large network; fully representative across both splits |
| **Mumbai (BEST / TMT)** | 1,115 | 892 | 223 | 12.08% | Large network; fully representative across both splits |
| **Ahmedabad (AMTS / BRTS)**| 972 | 778 | 194 | 10.53% | Medium network; fully representative across both splits |
| **HDBRT (Hubballi-Dharwad)**| 630 | 504 | 126 | 6.82% | Medium network; fully representative across both splits |
| **Pune (PMPML)** | 628 | 502 | 126 | 6.80% | Medium network; fully representative across both splits |
| **Rajkot (RMTS / BRTS)** | 271 | 217 | 54 | 2.93% | Small network; fully representative across both splits |
| **Davangere** | 14 | 11 | 3 | 0.15% | **Handled cleanly:** 11 train, 3 val (all 8 cities represented) |
| **TOTAL ACTIVE ROUTES** | **9,233** | **7,386** | **1,847** | **100.00%** | **Synchronized with lookup indices** |

### Small-Agency Handling (Davangere):
Davangere has only 14 active routes in its published GTFS timetable (79 routes in its catalog are unserved). A standard unstratified random split risked placing zero Davangere routes in the validation set. By stratifying strictly by `city`, Davangere is cleanly partitioned into 11 training routes (78.6%) and 3 validation routes (21.4%), guaranteeing that all 8 municipal transit systems are represented in both modeling partitions.

---

## 2. Alignment with Route Identifier Lookups (Rule 3)

The row indices of `X_train` and `X_val` are strictly aligned with dedicated metadata lookup tables:
* `processed/X_train.csv` (7,386 × 12) $\longleftrightarrow$ `processed/route_lookup_train.csv` (7,386 × 11)
* `processed/X_val.csv` (1,847 × 12) $\longleftrightarrow$ `processed/route_lookup_val.csv` (1,847 × 11)

No route names, line numbers, or city identifiers are present in the modeling feature matrices. They remain available in lookup tables to map model outputs back to real-world bus lines.

---

## 3. Unsupervised Clustering Evaluation Strategy (Module 5)

Because GTFS schedule data is unlabelled, clustering models (KMeans and DBSCAN) will be evaluated using a three-tier validation framework combining geometric compactness, generalization stability, and transit engineering validity:

### Tier 1: Internal Geometric Quality Metrics
* **Silhouette Coefficient ($s \in [-1, +1]$):**
  $$s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$$
  Measures within-cluster cohesion $a(i)$ relative to nearest-neighbor cluster separation $b(i)$. Target: $s > 0.35$ indicating well-separated, distinct transit archetypes.
* **Davies-Bouldin Index (Lower is Better):**
  $$\text{DB} = \frac{1}{K} \sum_{i=1}^K \max_{j \neq i} \left( \frac{\sigma_i + \sigma_j}{d(\boldsymbol{\mu}_i, \boldsymbol{\mu}_j)} \right)$$
  Evaluates the average similarity between each cluster and its most similar counterpart.
* **Calinski-Harabasz Index (Higher is Better):**
  Variance ratio criterion measuring the ratio of between-cluster dispersion to within-cluster dispersion.

### Tier 2: Generalization & Stability Across Train/Validation
1. **Centroid Projection Stability:**
   - Fit KMeans cluster centroids $\boldsymbol{\mu}_1, \dots, \boldsymbol{\mu}_K$ on `X_train`.
   - Assign validation routes in `X_val` to their nearest training centroid.
   - Compute validation inertia and validation silhouette score.
   - **Success Criterion:** Validation silhouette score must not degrade by more than $0.05$ relative to training silhouette score, verifying that discovered clusters generalize across unseen routes.
2. **DBSCAN Density Calibration:**
   - Calibrate neighborhood radius $\epsilon$ using k-distance elbow plots on `X_train` ($k = MinPts = 2 \times D = 24$).
   - Confirm that the noise percentage (routes marked as $-1$) remains bounded between $3\%$ and $10\%$ on both train and validation partitions.

### Tier 3: Transit Operational Domain Validity (Human-in-the-Loop)
Statistical clusters must map to coherent public transit operational archetypes:
* **Archetype 1 (High-Frequency Trunk Spines):** Daily trips $\ge 50$, all-day service span ($16$–$20$ hrs), low headway.
* **Archetype 2 (Commuter Peak Corridors):** High morning and evening trip shares ($> 60\%$ combined), moderate trip count.
* **Archetype 3 (Local Stopping Feeders):** High stop count, short-to-medium length, high stopping density.
* **Archetype 4 (Single-Trip Depot / Shift Specials):** Exactly 1 trip/day, zero service span, specialized departure hour.
* **Archetype 5 (Long Peri-Urban Loops):** Route length $> 40$ km, low frequency, connecting peripheral villages.

---

## 4. Supervised Classification Governance (Rule 1 Compliance)

In strict accordance with **Rule 1** and project constraints:

> **"No valid target label is available from GTFS schedule data; classification requires an approved label source (e.g. verified ridership); evaluation strategy is documented in the report."**

### Operational Principles:
1. **No Inferred Labels:** GTFS contains planned timetable supply only. Under no circumstances will synthetic or speculative labels (such as "overcrowded", "balanced", "underutilised", or "inefficient") be generated from schedule frequencies. High scheduled trip counts indicate high vehicle supply, not verified passenger demand.
2. **Future Classification Protocol:** If an external, verified ground-truth dataset (e.g. automated passenger counter boardings, farebox revenue, or vehicle load factors) is supplied:
   - Models will be trained strictly on `X_train` and evaluated on `X_val`.
   - Evaluation will prioritize **Macro-Averaged F1-score**, Balanced Accuracy, and per-class Confusion Matrices to account for operational class imbalance.
