# Benchmark of the structure searches (reviewer comment R1-5)

Measured on 2026-10-08 with `benchmarks/benchmark_tools.py`. The data are the full table download (`/api/v1/download/all.csv`) from the local copy of the database,
so the numbers should be re-run on the live site before they are quoted: `python benchmarks/benchmark_tools.py --part openbabel --csv all.csv` and `--part app`.
Ten drugs from the database are used as queries: {daunorubicin, doxorubicin, gemcitabine, lenalidomide, decitabine, imatinib, cyclophosphamide, sorafenib, paclitaxel, vorinostat}.

## Summary

- **2D similarity** (Morgan, radius 2, 2048 bits, Tanimoto) gives the same hit list as Open Babel's ECFP4 at the default threshold of 0.5 for all ten queries. The two rank all structures alike (Spearman rho 0.84 to 0.97, mean 0.91); they differ in the order of weak matches, because the two programs hash the circular fragments differently.
- **MACCS similarity** agrees with Open Babel's MACCS keys almost exactly (Spearman rho 0.995 or higher, mean absolute difference 0.006).
- **Substructure search** returns the same structures as Open Babel for six of eight fragments. Sulfonamide agrees once Open Babel is given the element-only form of the fragment. Indole differs for three N-substituted indoles (tubastatin A, apicidin, osimertinib): a query typed as SMILES ignores hydrogen counts, so `[nH]` also matches them.
- **Speed**: one search over all 1,409 study rows takes about 0.02 s (2D), 0.09 s (MACCS) and 0.01 s (substructure). A 3D search takes a median of 6.5 s and at most 10.5 s, because each query conformer is aligned onto every stored model.
- **3D search**: the query drug's own structure ranks first or second of 96 for all ten drugs; it ranks second for daunorubicin, sorafenib and vorinostat, where another structure scores higher than the identical one. Rankings depend moderately on the random seed used to build the query conformers (Spearman rho 0.62 to 0.98), which is why the seed is fixed at 42 and searches are reproducible.
- No open-source shape-alignment tool was available to compare the 3D search with, so the 3D search is checked only against itself.

The two parts ran in different environments (Open Babel 3.1.0 with RDKit 2024.09.3, and the project's RDKit 2023.03.2), so their structure counts differ slightly: the newer RDKit reads 3 more distinct structures. Part 2 first confirms that the app's functions return exactly the numbers plain RDKit gives.

## Part 1: agreement with Open Babel

RDKit 2024.09.3, Open Babel 3.1.0
1673 study rows in the file, 1441 with a structure RDKit reads, 101 distinct structures; 10 query drugs.
101 distinct structures read by both toolkits (used below).

### 2D similarity: RDKit Morgan (radius 2, 2048 bits) against Open Babel ECFP4, Tanimoto

| Query | Spearman rho | Top-10 overlap | Hits at 0.5 (RDKit) | Hits at 0.5 (Open Babel) | Hit-set overlap |
| --- | --- | --- | --- | --- | --- |
| Daunorubicin | 0.922 | 0.67 | 2 | 2 | 1.00 |
| Doxorubicin | 0.912 | 0.43 | 2 | 2 | 1.00 |
| Gemcitabine | 0.846 | 0.82 | 1 | 1 | 1.00 |
| Lenalidomide | 0.909 | 0.67 | 4 | 4 | 1.00 |
| Decitabine | 0.851 | 0.67 | 3 | 3 | 1.00 |
| Imatinib | 0.972 | 1.00 | 2 | 2 | 1.00 |
| Cyclophosphamide | 0.877 | 0.54 | 1 | 1 | 1.00 |
| Sorafenib | 0.970 | 0.82 | 2 | 2 | 1.00 |
| Paclitaxel | 0.838 | 0.54 | 2 | 2 | 1.00 |
| Vorinostat | 0.963 | 0.82 | 2 | 2 | 1.00 |

Mean rho 0.906 (lowest 0.838); mean top-10 overlap 0.70.

### MACCS similarity: RDKit MACCS keys against Open Babel MACCS, Tanimoto

| Query | Spearman rho | Pearson r | Mean absolute difference | Top-10 overlap |
| --- | --- | --- | --- | --- |
| Daunorubicin | 0.995 | 0.999 | 0.007 | 1.00 |
| Doxorubicin | 0.998 | 0.999 | 0.007 | 1.00 |
| Gemcitabine | 0.999 | 1.000 | 0.004 | 1.00 |
| Lenalidomide | 0.999 | 1.000 | 0.005 | 1.00 |
| Decitabine | 0.999 | 1.000 | 0.004 | 1.00 |
| Imatinib | 0.998 | 0.999 | 0.007 | 1.00 |
| Cyclophosphamide | 0.999 | 1.000 | 0.004 | 1.00 |
| Sorafenib | 0.997 | 0.999 | 0.007 | 1.00 |
| Paclitaxel | 0.995 | 0.999 | 0.007 | 1.00 |
| Vorinostat | 0.999 | 0.999 | 0.004 | 1.00 |

Mean rho 0.998; mean absolute difference 0.006.

### Substructure search: RDKit against Open Babel SMARTS matching (distinct structures that contain the fragment)

A fragment typed as SMILES matches on element and bond type only, like the element-only SMARTS that RDKit writes for it.
Open Babel reads a typed SMARTS strictly (for example [nH] needs exactly one hydrogen, N needs a non-aromatic nitrogen),
so each fragment is also given to Open Babel in that element-only form.

| Fragment | RDKit | Open Babel, SMARTS as typed | Same structures | Open Babel, element-only SMARTS | Same structures |
| --- | --- | --- | --- | --- | --- |
| glutarimide ring | 4 | 4 | 1.00 | 4 | 1.00 |
| benzene ring | 77 | 77 | 1.00 | 77 | 1.00 |
| pyrimidine ring | 28 | 28 | 1.00 | 28 | 1.00 |
| indole | 7 | 4 | 0.57 | 4 | 0.57 |
| pyridine ring | 23 | 23 | 1.00 | 23 | 1.00 |
| carboxylic acid | 22 | 22 | 1.00 | 22 | 1.00 |
| amide | 57 | 57 | 1.00 | 57 | 1.00 |
| sulfonamide | 6 | 5 | 0.83 | 6 | 1.00 |

## Part 2: the app

RDKit 2023.03.2, Python 3.10.14, x86_64, 12 logical CPUs, one process.
1409 study rows with a structure, 98 distinct structures, 10 query drugs.

### The app computes what plain RDKit computes

500 random pairs: 2D identical = True, MACCS identical = True, substructure identical = True.

### Run time per search (the same search functions the website runs: one query against every study row)

| Search | Median | Slowest |
| --- | --- | --- |
| 2D | 0.015 s | 0.020 s |
| MACCS | 0.090 s | 0.175 s |
| substructure | 0.008 s | 0.009 s |
| 3D | 6.530 s | 10.531 s |

### 3D search: does the ranking depend on the random seed used to build the query conformers?

| Query | Spearman rho (seed 42 vs 7) | Spearman rho (seed 42 vs 123) | Top-10 overlap (42 vs 7) | Own score | Own rank |
| --- | --- | --- | --- | --- |  --- |
| Daunorubicin | 0.775 | 0.620 | 0.67 | 0.66 | 2 of 96 |
| Doxorubicin | 0.857 | 0.872 | 0.43 | 0.79 | 1 of 96 |
| Gemcitabine | 0.976 | 0.971 | 0.82 | 1.0 | 1 of 96 |
| Lenalidomide | 0.963 | 0.980 | 0.82 | 1.0 | 1 of 96 |
| Decitabine | 0.959 | 0.946 | 0.67 | 1.0 | 1 of 96 |
| Imatinib | 0.678 | 0.677 | 0.33 | 0.57 | 1 of 96 |
| Cyclophosphamide | 0.956 | 0.924 | 0.54 | 1.0 | 1 of 96 |
| Sorafenib | 0.871 | 0.869 | 0.43 | 0.63 | 2 of 96 |
| Paclitaxel | 0.824 | 0.776 | 0.54 | 0.55 | 1 of 96 |
| Vorinostat | 0.887 | 0.863 | 0.33 | 0.75 | 2 of 96 |

Mean rho 0.874 (seed 7) and 0.850 (seed 123).
