# Quick Start Guide: Wild Cluster Bootstrap in app_experiment.py

## What's New?

The experimental version (`app_experiment.py`) automatically uses wild cluster bootstrap when your data has few clusters (< 30), providing more reliable statistical inference.

## Why This Matters

**Problem**: Standard cluster-robust standard errors can be unreliable with few clusters
- Asymptotic theory assumes G → ∞
- With small G (e.g., 10-30 clusters), t-statistics don't follow t-distribution
- Can lead to over-rejection of null hypotheses ("too many false positives")

**Solution**: Wild cluster bootstrap
- Resamples clusters instead of relying on asymptotic theory
- Provides exact (finite-sample) inference
- More conservative and reliable with small clusters

## How It Works

### Automatic Detection
```
Your data: 25 firms, 10 years per firm
→ System detects: 25 clusters (firms)
→ Since 25 < 30: Bootstrap automatically enabled
```

### What You'll See

#### 1. Regular Results (as before)
```
Coefficient: 0.0532
Standard Error: 0.0124
t-statistic: 4.29
Asymptotic p-value: 0.0001
```

#### 2. NEW: Bootstrap Results
```
╔═══════════════════════════════════════════╗
║  WILD CLUSTER BOOTSTRAP INFERENCE         ║
╚═══════════════════════════════════════════╝

⚠️  Small Cluster Detection: 25 clusters
    → Bootstrap recommended for G < 30

Bootstrap Results:
  • Bootstrap replications: 9,999
  • Bootstrap p-value: 0.0032
  • Asymptotic p-value: 0.0001
  
  • Method: Webb weights (optimal for small G)
```

#### 3. Interpretation
```
Which p-value to use?
→ Bootstrap p-value (0.0032)
  
Why?
→ More reliable with 25 clusters
→ Asymptotic p-value too optimistic
→ Bootstrap accounts for finite clusters
```

## Example Scenarios

### Scenario 1: Country-Level Analysis
```
Data: 20 countries, 15 years
Clusters: 20 countries

Result:
✓ Bootstrap enabled automatically
✓ Webb weights used
✓ Bootstrap p-value: More conservative
→ USE: Bootstrap p-value for inference
```

### Scenario 2: Industry-Level Treatment
```
Data: 15 industries, treatment varies by industry
Clusters: 15 industries

Result:  
✓ Bootstrap enabled (15 < 30)
✓ Full enumeration used (2^15 = 32,768 permutations)
✓ Exact inference provided
→ USE: Bootstrap p-value (exact)
```

### Scenario 3: Large Firm Sample
```
Data: 100 firms, 5 years
Clusters: 100 firms

Result:
✗ Bootstrap NOT run (100 > 30)
✓ Asymptotic inference reliable
→ USE: Standard p-value (fine)
```

## Code Example

The generated code includes bootstrap:

```python
import pyfixest as pf

# Estimate model
fit = pf.feols('Y ~ X1 | firm_id', data=df, vcov={'CRV1': 'firm_id'})

# Check clusters
n_clusters = df['firm_id'].nunique()

if n_clusters < 30:
    # Automatic bootstrap
    boot = fit.wildboottest(
        param='X1',
        reps=9999,
        cluster='firm_id',
        weights_type='webb',  # Best for small G
        k_adj=True,
        G_adj=True
    )
    print(f"Bootstrap p-value: {boot['Pr(>|t|)']}")
```

## When to Trust Bootstrap vs. Asymptotic

| Scenario | G | Which p-value? | Why? |
|----------|---|----------------|------|
| Very small | < 20 | Bootstrap ONLY | Asymptotic unreliable |
| Small | 20-30 | Bootstrap preferred | More conservative |
| Medium | 30-50 | Either OK | Bootstrap safer |
| Large | > 50 | Asymptotic OK | Bootstrap unnecessary |

## Technical Details

### Bootstrap Method
- **Type**: Wild cluster bootstrap (restricted)
- **Weights**: Webb (2014) six-point distribution
- **Replications**: 9,999 (or 2^G if G < 10)
- **Corrections**: Small-sample adjustments enabled (k_adj, G_adj)

### Why Webb Weights?
```
Standard Rademacher: {-1, 1}
Mammen: {-1.618, 0.618}
Webb: {-√1.5, -1, -√0.5, √0.5, 1, √1.5}

→ Webb has better finite-sample properties
→ Recommended by MacKinnon et al. (2023)
```

## Limitations

1. **One-way clustering only**
   - Example: Can cluster by firm OR country, not both
   - Two-way bootstrap: Coming in future pyfixest versions

2. **Not for IV models**
   - Only works with OLS/FE models
   - IV bootstrap: Not yet implemented

3. **Computational time**
   - 9,999 reps takes longer than asymptotic
   - For quick testing: Reduce reps (but less precise)

## FAQ

**Q: My p-values are very different. Which one is right?**
A: Bootstrap p-value. Large differences indicate small-cluster problems - exactly when bootstrap is needed.

**Q: Can I turn off bootstrap?**
A: Not in the UI, but you can modify the code: Set `use_wild_bootstrap=False` in function call.

**Q: Bootstrap says "not significant" but asymptotic says "significant". Now what?**
A: Trust the bootstrap. The asymptotic test is too optimistic with few clusters. Your result is not robust.

**Q: How many clusters do I need?**
A: 
- < 20: Bootstrap essential
- 20-30: Bootstrap recommended  
- 30-50: Bootstrap helpful
- > 50: Asymptotic OK

**Q: Can I use this for DiD with few treated clusters?**
A: Yes! This is a prime use case. If you have few treated units, bootstrap is highly recommended.

## Running the Experimental Version

```bash
# Navigate to project directory
cd c:\vs\advanced_panel

# Run experimental version
uv run app_experiment.py
```

The interface looks the same, but results automatically include bootstrap inference when needed.

## Support and References

For more details, see:
- `EXPERIMENTAL_BOOTSTRAP_NOTES.md` - Full technical documentation
- `IMPLEMENTATION_SUMMARY.md` - What was implemented
- pyfixest docs: https://py-econometrics.github.io/pyfixest/

Key papers:
1. Cameron, Gelbach & Miller (2008) - Bootstrap theory
2. MacKinnon, Nielsen & Webb (2023) - Implementation
3. Webb (2014) - Optimal weights

---

**Remember**: Bootstrap makes your inference more reliable, not less reliable. If bootstrap changes your conclusion, that's a feature, not a bug - it's telling you the asymptotic approximation wasn't working.
