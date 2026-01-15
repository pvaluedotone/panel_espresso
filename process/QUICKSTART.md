# Quick Start: Multi-Variable Bootstrap

## Installation

No additional installation needed - uses same dependencies as main app.

## Running the App

```powershell
# Option 1: From root directory
cd c:\vs\advanced_panel
uv run process/app_multi_bootstrap.py

# Option 2: From process directory
cd c:\vs\advanced_panel\process
uv run app_multi_bootstrap.py
```

**Note**: App runs on port **7861** (not 7860 like the standard version)

## Quick Example

### Scenario 1: Default Behavior (Recommended)

**Goal**: Test only emissions (your primary variable)

**Steps**:
1. Upload CSV
2. Select variables:
   - Dependent: `ROA`
   - Independent: `emissions`
   - Controls: `size`, `age`, `leverage`
3. Enable bootstrap: ✓
4. Bootstrap variables: **Only `emissions` checked** (default)
5. Run analysis

**Result**: Bootstrap inference only for emissions, asymptotic for controls

---

### Scenario 2: Test Multiple Key Variables

**Goal**: Test both emissions AND R&D spending

**Steps**:
1. Upload CSV
2. Select variables:
   - Dependent: `ROA`
   - Independent: `emissions`
   - Controls: `RD_spending`, `size`, `age`
3. Enable bootstrap: ✓
4. Bootstrap variables: **Check both**:
   - ☑ `emissions`
   - ☑ `RD_spending`
5. Run analysis

**Result**: Bootstrap inference for both emissions and R&D

**⚠️ Remember**: Apply multiple testing correction!

---

### Scenario 3: Very Small Clusters (G < 20)

**Goal**: Bootstrap all variables due to insufficient clusters

**Steps**:
1. Upload CSV with few clusters
2. Select variables as usual
3. Enable bootstrap: ✓
4. Bootstrap variables: **Check all**:
   - ☑ `emissions`
   - ☑ `size`
   - ☑ `age`
   - ☑ `leverage`
5. Run analysis

**Result**: Robust inference for all coefficients

**⚠️ Remember**: 
- Computational time: ~10 seconds per variable
- Apply multiple testing correction
- Consider if inference is viable at all with G < 20

---

## Common Patterns

### Pattern 1: Primary Hypothesis Only
```
Bootstrap: [X]
Result:    Bootstrap p-value for X
Use case:  Standard causal inference
```

### Pattern 2: Primary + Key Control
```
Bootstrap: [X, important_control]
Result:    Bootstrap p-values for both
Use case:  Two substantive hypotheses
```

### Pattern 3: All Variables (Small Clusters)
```
Bootstrap: [X, control1, control2, control3]
Result:    Bootstrap p-values for all
Use case:  G < 20, need robust inference everywhere
```

## Interpreting Results

### Output Structure

```
╔═══════════════════════════════════════════════════════╗
║    WILD CLUSTER BOOTSTRAP INFERENCE (MULTI-VARIABLE)  ║
╚═══════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variable: emissions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  Small Cluster Detection: 25 clusters
    
Bootstrap Results:
  • Bootstrap p-value: 0.0234 *
  • Asymptotic p-value: 0.0156 *
  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variable: size
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bootstrap Results:
  • Bootstrap p-value: 0.0456 *
  • Asymptotic p-value: 0.0312 *
```

### Decision Rules

**Single Variable (No Correction Needed)**:
- Use bootstrap p-value directly
- Standard α = 0.05 threshold

**Multiple Variables (Correction Required)**:
- Apply Bonferroni: α = 0.05 / K
- Or use Holm-Bonferroni (less conservative)
- Or use FDR control (Benjamini-Hochberg)

## Multiple Testing Corrections

### Bonferroni (Most Conservative)

**2 variables**: α = 0.05 / 2 = 0.025
```
emissions: p = 0.023 < 0.025 → Significant ✓
size:      p = 0.046 > 0.025 → Not significant
```

**3 variables**: α = 0.05 / 3 = 0.0167
```
emissions: p = 0.023 > 0.0167 → Not significant
size:      p = 0.046 > 0.0167 → Not significant
age:       p = 0.012 < 0.0167 → Significant ✓
```

### Holm-Bonferroni (Sequential)

**Steps**:
1. Order p-values: p₁ ≤ p₂ ≤ p₃
2. Test p₁ against α/3 = 0.0167
3. If rejected, test p₂ against α/2 = 0.025
4. If rejected, test p₃ against α/1 = 0.05

**Example**:
```
Ordered: 0.012, 0.023, 0.046

age:       0.012 < 0.0167 → Significant ✓, continue
emissions: 0.023 < 0.025  → Significant ✓, continue
size:      0.046 < 0.05   → Significant ✓
```

All three significant with Holm-Bonferroni!

### FDR Control (Benjamini-Hochberg)

**Steps**:
1. Order p-values: p₁ ≤ p₂ ≤ p₃
2. Find largest i where pᵢ ≤ (i/K) × α
3. Reject all H₀₁, ..., H₀ᵢ

**Example** (K=3, α=0.05):
```
i=1: 0.012 ≤ (1/3)×0.05 = 0.0167 ✓
i=2: 0.023 ≤ (2/3)×0.05 = 0.0333 ✓
i=3: 0.046 ≤ (3/3)×0.05 = 0.0500 ✓

Largest i = 3, reject all three
```

## Troubleshooting

### Issue: Bootstrap takes too long

**Solution**:
- Reduce number of variables selected
- Check if clusters are actually small (< 30)
- Consider using standard version if G > 50

### Issue: All p-values become non-significant

**Solution**:
- Expected with conservative corrections
- Consider Holm-Bonferroni instead of Bonferroni
- Evaluate if you truly need to test all variables

### Issue: Bootstrap fails for some variables

**Solution**:
- Check if variable exists in model
- Verify interaction terms are properly specified
- Review error messages in diagnostics

### Issue: Different results than standard version

**Solution**:
- Expected - testing multiple variables
- Standard version tests only X
- Both are correct for their purposes

## Best Practices Checklist

Before bootstrapping multiple variables, ask:

- [ ] Do I have a substantive reason to test this control?
- [ ] Is the cluster count actually small (< 30)?
- [ ] Am I prepared to apply multiple testing corrections?
- [ ] Do I have time for the computation (K × 10 seconds)?
- [ ] Will I report this appropriately in my paper?

If all Yes → Use multi-variable bootstrap
If any No → Consider standard version

## When to Use Standard Version Instead

Use `app_experiment.py` (standard version) when:

1. ✅ Only care about primary independent variable
2. ✅ Controls are just for confounding adjustment
3. ✅ Want faster computation
4. ✅ Following standard practice in literature
5. ✅ Reviewer didn't specifically request control bootstrap

**Remember**: Standard practice is to bootstrap only the primary variable!

## Example Research Scenarios

### ✅ Good Use Cases

**Scenario A**: Multiple Treatment Variables
```
Research Question: 
"Do both environmental AND social performance affect firm value?"

Bootstrap: [environmental_score, social_score]
Rationale: Both are primary hypotheses
```

**Scenario B**: Treatment-Control Comparison
```
Research Question:
"Does treatment effect differ from control variable effect?"

Bootstrap: [treatment, important_control]
Rationale: Formal comparison of magnitudes
```

**Scenario C**: Very Small Sample
```
Data: 15 countries over 10 years (G = 15)

Bootstrap: [X, control1, control2, control3]
Rationale: Asymptotic inference unreliable for all
```

### ❌ Poor Use Cases

**Scenario X**: "Just to be safe"
```
Bootstrap: [X, size, age, leverage, ROA_lag, ...]
Problem: No substantive reason, multiple testing burden
Solution: Use standard version, bootstrap only X
```

**Scenario Y**: Large clusters
```
Data: 500 firms over 10 years (G = 500)
Bootstrap: [X, controls...]
Problem: Asymptotic inference works fine
Solution: Use standard version or no bootstrap
```

**Scenario Z**: Publication pressure
```
Reason: "Reviewer might ask about control significance"
Problem: Not a valid statistical reason
Solution: Report asymptotic SE, defend if needed
```

## Generated Code

The app generates complete code including:

```python
# Variables to test with bootstrap
test_variables = ['emissions', 'size']

bootstrap_results = {}
for var_name in test_variables:
    boot_result = results.wildboottest(
        param=var_name,
        reps=9999,
        cluster='firm_id',
        weights_type='webb',
        ...
    )
    bootstrap_results[var_name] = boot_result
```

Copy this code for your own analysis!

## Support

Questions? Check:
1. Main README: `../README.md`
2. Bootstrap theory: `../EXPERIMENTAL_BOOTSTRAP_NOTES.md`
3. Implementation details: `../IMPLEMENTATION_SUMMARY.md`
4. This guide: `README.md`

---

**Quick Rule**: When in doubt, use the standard version (bootstrap X only). This advanced version is for specific cases where you need bootstrap inference for multiple variables.
