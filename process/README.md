# Multi-Variable Wild Cluster Bootstrap

## Overview

This subfolder contains an **advanced version** of the panel data analysis app that allows users to **optionally select which variables to bootstrap via the UI**.

## Key Difference from Standard Version

### Standard Version (`app_experiment.py`)
- ✅ Automatically bootstraps **only** the main independent variable (X)
- ✅ Default behavior follows best practices
- ✅ Computationally efficient
- ✅ **Recommended for most users**

### Advanced Version (`process/app_multi_bootstrap.py`)
- ✅ Allows users to **select which variables** to bootstrap
- ✅ Can bootstrap multiple variables (X + controls)
- ✅ **Optional** - default still bootstraps only X
- ⚠️ More computationally intensive
- ⚠️ Requires understanding of multiple testing issues
- 🎯 **For advanced users with specific needs**

## When to Use This Version

### ✅ Use Multi-Variable Bootstrap When:

1. **Specific control variables are of substantive interest**
   - Example: Testing both R&D spending AND marketing spending effects
   - Example: Multiple treatment variables in the same model

2. **Conducting formal multiple hypothesis tests**
   - Example: Testing joint significance with individual tests
   - Example: Research question involves multiple key variables

3. **Very small clusters (G < 20)**
   - All coefficients may need bootstrap inference
   - Asymptotic inference questionable even for controls

4. **Robustness checks**
   - Comparing bootstrap vs. asymptotic for all variables
   - Sensitivity analysis of inference methods

### ❌ Do NOT Use Multi-Variable Bootstrap When:

1. **Only interested in primary causal effect**
   - Standard version is appropriate
   - Controls are just for confounding adjustment

2. **Many control variables (K > 10)**
   - Computational cost: K × 9,999 replications
   - Multiple testing corrections become severe

3. **Sufficient clusters (G > 50)**
   - Asymptotic inference works fine
   - Bootstrap provides minimal benefits

4. **Time constraints**
   - Each additional variable adds ~10-30 seconds

## Features

### UI Enhancements

1. **Bootstrap Variable Selection**
   ```
   ✓ Enable Wild Cluster Bootstrap
   
   Variables to Bootstrap:
   [ ] emissions (Independent Variable) ← DEFAULT: Selected
   [ ] size (Control)
   [ ] age (Control)
   [ ] leverage (Control)
   ```

2. **Smart Defaults**
   - Automatically selects only independent variable
   - Updates choices when model specification changes
   - Clear warnings about computational cost

3. **Multi-Variable Results Display**
   - Separate bootstrap results for each variable
   - Side-by-side asymptotic vs. bootstrap p-values
   - Clear indication of which variables were bootstrapped

### Technical Implementation

**Core Function:**
```python
def run_bootstrap_for_selected_variables(
    results,
    df_clean,
    firm_id_col,
    year_col,
    cluster_method,
    country_var,
    industry_var,
    selected_variables,  # User-selected list
    bootstrap_reps=9999
) -> Dict[str, Optional[Dict]]:
    """Run wild cluster bootstrap for multiple selected variables"""
```

**Returns a dictionary:**
```python
{
    'emissions': {...bootstrap results...},
    'size': {...bootstrap results...},
    'age': {...bootstrap results...}
}
```

## Usage

### Running the App

```bash
# From the process subdirectory
cd c:\vs\advanced_panel\process
uv run app_multi_bootstrap.py

# Or from root directory
cd c:\vs\advanced_panel
uv run process/app_multi_bootstrap.py
```

**Note**: Runs on port **7861** (different from standard version on 7860)

### Basic Workflow

1. **Upload data** as usual
2. **Select variables** (X, Y, controls)
3. **Enable bootstrap** (checkbox)
4. **Select which variables to bootstrap:**
   - Default: Only X selected ✓
   - Optional: Check additional variables
5. **Run analysis**

### Example: Testing Two Key Variables

Suppose you want to test both emissions AND R&D spending:

1. Select **emissions** as independent variable
2. Add **R&D** to controls
3. Enable bootstrap
4. Check **both** variables:
   - ☑ emissions
   - ☑ R&D
5. Run analysis

Results will show bootstrap p-values for both.

## Important Considerations

### 1. Multiple Testing Problem

When testing K hypotheses, false positive rate increases:

**Bonferroni Correction:**
```
Adjusted α = 0.05 / K

For 3 variables: α = 0.05 / 3 = 0.0167
Reject H₀ only if p < 0.0167
```

**Holm-Bonferroni (less conservative):**
```
Order p-values: p₁ ≤ p₂ ≤ ... ≤ pₖ
Reject H₀ᵢ if pᵢ < α/(K - i + 1)
```

**FDR Control (Benjamini-Hochberg):**
```
Order p-values: p₁ ≤ p₂ ≤ ... ≤ pₖ
Find largest i where pᵢ ≤ (i/K) × α
Reject all H₀₁, ..., H₀ᵢ
```

### 2. Computational Cost

| Variables | Time (approx) |
|-----------|---------------|
| 1 (X only) | ~10 seconds |
| 3 variables | ~30 seconds |
| 5 variables | ~50 seconds |
| 10 variables | ~100 seconds |

**Formula**: Time ≈ K × 10 seconds (with 9,999 reps)

### 3. Interpretation Guidelines

**Single variable bootstrapped:**
```
emissions: Bootstrap p = 0.023
          Asymptotic p = 0.015
→ Use bootstrap p-value (more conservative, more reliable)
```

**Multiple variables bootstrapped:**
```
emissions: Bootstrap p = 0.023
size:      Bootstrap p = 0.041
age:       Bootstrap p = 0.067

With Bonferroni (α = 0.05/3 = 0.0167):
- emissions: 0.023 > 0.0167 → Not significant
- size:      0.041 > 0.0167 → Not significant
- age:       0.067 > 0.0167 → Not significant
```

### 4. Reporting in Papers

**Example reporting:**
```
"We employ wild cluster bootstrap inference (Webb, 2014) 
with 9,999 replications for both our primary independent 
variable (emissions) and key control variables (firm size 
and R&D spending). P-values are adjusted using the 
Bonferroni correction to account for multiple testing."
```

## Code Generation

The generated code includes:

```python
# MULTI-VARIABLE WILD CLUSTER BOOTSTRAP
n_clusters = df['firm_id'].nunique()

if n_clusters < 30:
    # Variables to test with bootstrap
    test_variables = ['emissions', 'size', 'age']
    
    bootstrap_results = {}
    for var_name in test_variables:
        boot_result = results.wildboottest(
            param=var_name,
            reps=9999,
            cluster='firm_id',
            weights_type='webb',
            impose_null=True,
            bootstrap_type='11',
            seed=12345,
            k_adj=True,
            G_adj=True
        )
        bootstrap_results[var_name] = boot_result
```

## Comparison with Standard Version

| Feature | Standard | Multi-Variable |
|---------|----------|----------------|
| Bootstrap X only | ✓ Default | ✓ Default |
| Bootstrap controls | ✗ | ✓ Optional |
| UI selection | ✗ | ✓ |
| Multiple testing warnings | N/A | ✓ |
| Computation time | Fast | Slower |
| Complexity | Simple | Advanced |
| Target users | All users | Advanced users |

## Theoretical Foundation

### Why Multiple Variables?

**Cameron et al. (2008)** focus on single parameter tests, but extension to multiple parameters is straightforward:

1. **Each variable needs its own null hypothesis:**
   - H₀₁: β_emissions = 0
   - H₀₂: β_size = 0
   - H₀₃: β_age = 0

2. **Each bootstrap test is independent:**
   - Separate resampling for each parameter
   - Different bootstrap t-statistics
   - Different bootstrap p-values

3. **Joint inference requires adjustment:**
   - Family-wise error rate (FWER)
   - False discovery rate (FDR)
   - Standard statistical practice

### When is Asymptotic Inference OK?

Controls can typically rely on asymptotic inference when:
- ✓ Sufficient clusters (G > 50)
- ✓ Balanced cluster sizes
- ✓ Control is not primary hypothesis
- ✓ Conservative inference acceptable

## Best Practices

### DO:
1. ✅ Start with default (X only)
2. ✅ Add controls only if substantively important
3. ✅ Report multiple testing corrections
4. ✅ Justify choice in methods section
5. ✅ Compare asymptotic vs. bootstrap

### DON'T:
1. ❌ Bootstrap all variables "just in case"
2. ❌ Ignore multiple testing problem
3. ❌ Test many variables without correction
4. ❌ Use when clusters are sufficient
5. ❌ Forget computational time constraints

## References

### Key Papers

1. **Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008)**
   - "Bootstrap-Based Improvements for Inference with Clustered Errors"
   - Review of Economics and Statistics
   - Foundation for single-parameter tests

2. **Romano, J. P., & Wolf, M. (2005)**
   - "Stepwise Multiple Testing as Formalized Data Snooping"
   - Econometrica
   - Multiple testing corrections

3. **Benjamini, Y., & Hochberg, Y. (1995)**
   - "Controlling the False Discovery Rate"
   - Journal of the Royal Statistical Society B
   - FDR control procedure

4. **Holm, S. (1979)**
   - "A Simple Sequentially Rejective Multiple Test Procedure"
   - Scandinavian Journal of Statistics
   - Sequential Bonferroni method

## Support

For questions about:
- **Standard bootstrap**: Use `app_experiment.py`
- **Multi-variable bootstrap**: Use this version
- **No bootstrap**: Use `app.py` (production version)

## Version History

- **December 22, 2025**: Initial release
  - Multi-variable bootstrap selection
  - Dynamic UI updates
  - Multiple testing warnings
  - Enhanced documentation

---

**Remember**: Most studies should use the standard version. This advanced version is for specific use cases requiring multi-variable bootstrap inference.
