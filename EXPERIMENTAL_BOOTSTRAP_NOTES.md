# Wild Cluster Bootstrap Implementation Notes

## Overview
This document describes the experimental wild cluster bootstrap implementation in `app_experiment.py` based on the pyfixest GitHub repository research.

## Key Changes

### 1. Automatic Bootstrap for Small Clusters
- **Threshold**: Automatically runs wild cluster bootstrap when G < 30 clusters
- **Detection**: Analyzes the cluster structure before running bootstrap
- **Implementation**: New function `run_wild_bootstrap_if_needed()`

### 2. Bootstrap Configuration

#### Optimal Settings for Small Clusters
Based on MacKinnon, Nielsen & Webb (2023) and Cameron et al. (2008):

```python
results.wildboottest(
    param=independent_var,      # Variable to test
    reps=9999,                  # Bootstrap replications
    cluster=cluster_var,        # One-way clustering variable
    weights_type='webb',        # Webb (2014) weights - BEST for small G
    impose_null=True,           # Restricted bootstrap
    bootstrap_type='11',        # Standard WCB
    seed=12345,                 # Reproducibility
    k_adj=True,                 # Small-sample adjustment for k
    G_adj=True                  # Small-sample adjustment for G (CRITICAL)
)
```

#### Key Parameters Explained

1. **weights_type='webb'**: 
   - Six-point distribution: {-√1.5, -1, -√0.5, √0.5, 1, √1.5}
   - Better finite-sample properties than Rademacher or Mammen
   - Recommended by Webb (2014) for small clusters

2. **G_adj=True**: 
   - Critical for small cluster scenarios
   - Applies correction factor: G/(G-1)
   - More conservative inference

3. **Full Enumeration for Very Small G**:
   - When G < 10, automatically switches to full enumeration
   - Uses all 2^G permutations instead of random sampling
   - Provides exact inference

### 3. Enhanced Display

#### Bootstrap Results Section
Shows:
- Number of clusters detected
- Bootstrap p-value vs. asymptotic p-value
- Bootstrap methodology details
- Interpretation guidance

#### Diagnostic Section
Enhanced with:
- Automatic bootstrap recommendations
- Cluster adequacy assessment
- References to key papers

### 4. Code Generation
Updated to include:
- Cluster counting
- Conditional bootstrap execution
- Full bootstrap code example
- References to methodology papers

## Limitations

### Current Constraints
1. **One-way clustering only**: 
   - wildboottest() in pyfixest currently supports only one-way clustering
   - Two-way clustering defaults to firm-level bootstrap only
   
2. **Not for IV models**:
   - Wild bootstrap not implemented for IV estimation in pyfixest
   
3. **Computational intensity**:
   - 9,999 replications can be slow for large datasets
   - Consider reducing reps for quick testing

### Future Enhancements
- Multi-way wild cluster bootstrap (pending pyfixest support)
- Parallel execution options
- Alternative weight schemes
- User-configurable bootstrap parameters via UI

## References

### Key Papers
1. **Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008)**
   - "Bootstrap-Based Improvements for Inference with Clustered Errors"
   - Review of Economics and Statistics
   - Establishes wild bootstrap for cluster-robust inference

2. **MacKinnon, J. G., Nielsen, M. Ø., & Webb, M. D. (2023)**
   - "Fast and Reliable Jackknife and Bootstrap Methods for Cluster-Robust Inference"
   - Journal of Applied Econometrics
   - Modern implementation and best practices

3. **Webb, M. D. (2014)**
   - "Reworking Wild Bootstrap Based Inference for Clustered Errors"
   - Queen's Economics Department Working Paper
   - Introduces six-point distribution

### pyfixest Documentation
- GitHub: https://github.com/py-econometrics/pyfixest
- Wild bootstrap docs: https://py-econometrics.github.io/pyfixest/quickstart.html#inference-via-the-wild-bootstrap
- API reference: `wildboottest()` method

## Testing Recommendations

### When to Use Bootstrap
✅ **Use bootstrap when**:
- G < 30 clusters in any dimension
- Cluster sizes are unbalanced
- Treatment is clustered (DiD, etc.)
- Conservative inference needed

❌ **Don't use bootstrap when**:
- G > 50 clusters (asymptotic inference OK)
- No clustering (use robust SE)
- Two-way clustering (not yet supported)

### Interpreting Results
1. **Bootstrap p-value > Asymptotic p-value**: 
   - Common with small clusters
   - Bootstrap is more conservative
   - Trust the bootstrap

2. **Bootstrap p-value ≈ Asymptotic p-value**:
   - Asymptotic approximation working well
   - Either inference method acceptable

3. **Very different p-values**:
   - Sign of small-cluster problems
   - Definitely use bootstrap
   - Consider if inference is viable at all

## Usage Example

```python
import pyfixest as pf
import pandas as pd

# Load data
df = pd.read_csv('data.csv')

# Estimate model
fit = pf.feols('Y ~ X1 | firm_id', data=df, vcov={'CRV1': 'firm_id'})

# Check clusters
n_clusters = df['firm_id'].nunique()
print(f"Clusters: {n_clusters}")

if n_clusters < 30:
    # Run wild bootstrap
    boot = fit.wildboottest(
        param='X1',
        reps=9999,
        cluster='firm_id',
        weights_type='webb',
        k_adj=True,
        G_adj=True
    )
    print(f"Bootstrap p-value: {boot['Pr(>|t|)']}")
```

## Changelog

### December 22, 2025
- Initial implementation in `app_experiment.py`
- Automatic detection for G < 30
- Webb weights as default
- Enhanced documentation and code generation
- Full integration with existing FE model workflow

---

**Note**: This is an experimental feature. Always compare with asymptotic inference and assess reasonableness of results given your data structure.
