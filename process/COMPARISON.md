# Version Comparison Guide

## Overview of All Versions

This workspace contains three versions of the panel data analysis app:

1. **`app.py`** - Production version (no bootstrap)
2. **`app_experiment.py`** - Standard bootstrap version
3. **`process/app_multi_bootstrap.py`** - Advanced multi-variable bootstrap

## Feature Comparison

| Feature | Production | Standard Bootstrap | Multi-Variable Bootstrap |
|---------|------------|-------------------|-------------------------|
| Fixed Effects | ✓ | ✓ | ✓ |
| Pooled OLS | ✓ | ✓ | ✓ |
| Cluster-robust SE | ✓ | ✓ | ✓ |
| Wild bootstrap | ✗ | ✓ (X only) | ✓ (User select) |
| Bootstrap UI controls | ✗ | ✗ | ✓ |
| Multiple testing warnings | ✗ | ✗ | ✓ |
| Port | 7860 | 7860 | 7861 |
| Computation speed | Fast | Medium | Slow* |
| Target users | All | Most | Advanced |

*Depends on number of variables selected

## Decision Tree: Which Version to Use?

```
Start
  │
  ├─ Do you have small clusters (G < 30)?
  │   │
  │   ├─ NO → Use app.py (Production)
  │   │       • No bootstrap needed
  │   │       • Fastest computation
  │   │       • Standard practice
  │   │
  │   └─ YES → Need bootstrap
  │       │
  │       ├─ Only care about X (primary variable)?
  │       │   │
  │       │   └─ YES → Use app_experiment.py (Standard Bootstrap)
  │       │            • Bootstrap X only
  │       │            • Standard practice
  │       │            • Faster than multi-variable
  │       │
  │       └─ Need bootstrap for controls too?
  │           │
  │           └─ YES → Use process/app_multi_bootstrap.py
  │                    • Select which variables
  │                    • Multiple testing corrections
  │                    • Advanced feature
```

## Detailed Comparison

### app.py (Production Version)

**When to use**:
- ✓ Sufficient clusters (G ≥ 50)
- ✓ Standard panel data analysis
- ✓ No bootstrap needed
- ✓ Want fastest computation
- ✓ Following standard practices

**Features**:
- Fixed Effects with pyfixest
- Pooled OLS
- CRV1 and CRV3 cluster-robust SE
- Multiple clustering dimensions
- Interaction terms
- Lagged dependent variables

**Not included**:
- Wild cluster bootstrap

**Example output**:
```
Coefficient: 0.0453
Std. Error:  0.0189 (CRV3)
t-statistic: 2.397
p-value:     0.0165 *
```

---

### app_experiment.py (Standard Bootstrap)

**When to use**:
- ✓ Small clusters (G < 30)
- ✓ Primary variable is X
- ✓ Controls for confounding only
- ✓ Standard bootstrap practice
- ✓ Want bootstrap but not complicated

**Additional features**:
- All features from app.py PLUS:
- Automatic bootstrap for small clusters
- Bootstrap X only (standard practice)
- Webb weights for small G
- Bootstrap vs. asymptotic comparison

**Example output**:
```
╔═══════════════════════════════════════════╗
║   WILD CLUSTER BOOTSTRAP INFERENCE        ║
╚═══════════════════════════════════════════╝

Variable: emissions
  • Bootstrap p-value:  0.0234 *
  • Asymptotic p-value: 0.0156 *
  
→ Use bootstrap p-value with few clusters
```

**Decision logic**:
```python
# Automatic: If G < 30, bootstrap X
if n_clusters < 30:
    bootstrap(param=independent_var)
```

---

### process/app_multi_bootstrap.py (Advanced)

**When to use**:
- ✓ Small clusters (G < 30)
- ✓ Multiple hypotheses to test
- ✓ Specific controls of interest
- ✓ Need flexible bootstrap selection
- ✓ Understand multiple testing

**Additional features**:
- All features from app_experiment.py PLUS:
- UI to select which variables to bootstrap
- Default: X only (can add controls)
- Multiple variable bootstrap results
- Multiple testing warnings
- Computational cost warnings

**Example output**:
```
╔═══════════════════════════════════════════╗
║   WILD CLUSTER BOOTSTRAP (MULTI-VARIABLE) ║
╚═══════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variable: emissions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Bootstrap p-value:  0.0234 *
  • Asymptotic p-value: 0.0156 *

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variable: size
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Bootstrap p-value:  0.0456 *
  • Asymptotic p-value: 0.0312 *

⚠️  Multiple Testing: Apply corrections!
```

**Decision logic**:
```python
# User-controlled: Select which variables
if use_bootstrap:
    for var in bootstrap_variables:  # User selected
        bootstrap(param=var)
```

## Performance Comparison

### Computation Time (Example: 1000 obs, 100 firms, 10 years)

| Version | Time | Notes |
|---------|------|-------|
| app.py | ~2 sec | No bootstrap |
| app_experiment.py | ~12 sec | Bootstrap X only |
| process/ (1 var) | ~12 sec | Same as standard |
| process/ (3 vars) | ~36 sec | 3 × bootstrap |
| process/ (5 vars) | ~60 sec | 5 × bootstrap |

### Memory Usage

| Version | Memory | Notes |
|---------|--------|-------|
| app.py | Low | No bootstrap |
| app_experiment.py | Medium | One bootstrap |
| process/ | Medium-High | Multiple bootstraps |

## Code Generation Comparison

### app.py
```python
# No bootstrap code generated
results = pf.feols(formula, data=df, vcov=vcov)
print(results.summary())
```

### app_experiment.py
```python
# Bootstrap code for X only
if n_clusters < 30:
    boot = results.wildboottest(
        param='emissions',  # X only
        reps=9999,
        ...
    )
```

### process/app_multi_bootstrap.py
```python
# Bootstrap code for selected variables
test_variables = ['emissions', 'size', 'age']

bootstrap_results = {}
for var_name in test_variables:
    boot = results.wildboottest(
        param=var_name,  # Each variable
        reps=9999,
        ...
    )
    bootstrap_results[var_name] = boot
```

## Use Case Examples

### Example 1: Standard Panel Study (500 firms)

**Scenario**: Standard firm-level panel, sufficient clusters
```
Data: 500 firms × 10 years
Research: Effect of emissions on ROA
Controls: Size, age, leverage

→ Use: app.py (Production)
Reason: G = 500, no bootstrap needed
```

### Example 2: Country-Level Analysis (25 countries)

**Scenario**: Small number of countries
```
Data: 25 countries × 15 years
Research: Effect of emissions on GDP
Controls: Population, trade

→ Use: app_experiment.py (Standard Bootstrap)
Reason: G = 25, bootstrap X (emissions) only
```

### Example 3: Multiple Policy Variables (15 states)

**Scenario**: Testing multiple policy effects
```
Data: 15 states × 20 years
Research: Effects of policy_A AND policy_B
Controls: Demographics

→ Use: process/app_multi_bootstrap.py (Advanced)
Reason: G = 15, need bootstrap for both policies
Bootstrap: [policy_A, policy_B]
```

### Example 4: Industry-Level Study (20 industries)

**Scenario**: Very small clusters, all variables questionable
```
Data: 20 industries × 10 years
Research: Effect of regulation
Controls: Market concentration, R&D

→ Use: process/app_multi_bootstrap.py (Advanced)
Reason: G = 20, bootstrap all variables
Bootstrap: [regulation, concentration, RD]
Warning: Consider if inference viable at all
```

## Migration Between Versions

### From app.py → app_experiment.py

**Reason**: Discovered small clusters
**Steps**:
1. Run app_experiment.py instead
2. Same workflow, no UI changes
3. Bootstrap runs automatically
4. Compare bootstrap vs. asymptotic p-values

### From app_experiment.py → process/app_multi_bootstrap.py

**Reason**: Reviewer asked about control significance
**Steps**:
1. Run process/app_multi_bootstrap.py
2. Same workflow, but:
   - Enable bootstrap checkbox
   - Select additional variables
3. Apply multiple testing corrections
4. Report in response to reviewers

### From process/ → app_experiment.py

**Reason**: Too complicated, revert to standard
**Steps**:
1. Run app_experiment.py instead
2. Back to X-only bootstrap
3. Simpler results, faster computation

## Recommendation by Discipline

### Economics / Finance
- **Default**: app_experiment.py (Standard Bootstrap)
- **Reason**: Small cluster common, X-only standard

### Management / Strategy
- **Default**: app.py (Production)
- **Reason**: Usually sufficient firms, no bootstrap needed

### Environmental Studies
- **Default**: app_experiment.py (Standard Bootstrap)
- **Reason**: Often country/region-level, small G

### Political Science
- **Default**: process/ (Multi-Variable Bootstrap)
- **Reason**: Multiple treatments, policy variables

### Sociology
- **Default**: app.py → app_experiment.py as needed
- **Reason**: Mix of large and small cluster studies

## Summary Table

### Quick Reference

| Your Situation | Use | Bootstrap |
|----------------|-----|-----------|
| G ≥ 50, standard study | app.py | None |
| G < 30, focus on X | app_experiment.py | X only |
| G < 30, need controls | process/ | Select |
| G < 20, all variables | process/ | All |
| Reviewer request | process/ | Specific |
| Robustness check | process/ | Varies |
| Time constraint | app.py | None |
| Standard practice | app_experiment.py | X only |

## File Locations

```
c:\vs\advanced_panel\
├── app.py                          ← Production
├── app_experiment.py               ← Standard Bootstrap
└── process\
    ├── app_multi_bootstrap.py      ← Advanced Multi-Variable
    ├── README.md                   ← Full documentation
    ├── QUICKSTART.md               ← Quick start guide
    └── COMPARISON.md               ← This file
```

## Running Each Version

```powershell
# Production (no bootstrap)
uv run app.py

# Standard bootstrap (X only)
uv run app_experiment.py

# Multi-variable bootstrap
uv run process/app_multi_bootstrap.py
# OR
cd process
uv run app_multi_bootstrap.py
```

## Final Recommendation

**For most users**: Start with `app_experiment.py`
- Handles both small and large clusters
- Follows best practices
- Provides bootstrap when needed
- Not overwhelming with options

**Advanced users only**: Use `process/app_multi_bootstrap.py`
- When you have specific needs
- Understand multiple testing
- Prepared for longer computation
- Required by reviewer/research design

**Large clusters**: Can use `app.py`
- Simpler, faster
- No bootstrap overhead
- Standard cluster-robust SE sufficient

---

**Remember**: The choice depends on your data structure (cluster size) and research design (single vs. multiple hypotheses), not on sophistication preference!
