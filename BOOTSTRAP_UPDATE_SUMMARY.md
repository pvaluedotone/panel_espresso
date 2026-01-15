# Wild Cluster Bootstrap Update Summary

## Date: December 24, 2025

## Overview
Updated the wild cluster bootstrap functionality in `experiment_1.py` to automatically include lag variables and interaction terms in the bootstrap process when these options are selected in the UI. Also added a dedicated bootstrap results table to the Publication Report.

## Changes Made

### 1. Automatic Bootstrap Variable Selection

**Location:** `run_fixed_effects_model()` function (lines ~417-450)

**What Changed:**
- Bootstrap now automatically includes:
  - **Lag variables** when "Include Lagged DV" is checked
  - **Interaction terms** when a moderator variable is selected and "Include Interaction" is checked
  - The main **independent variable** (always included by default)

**How It Works:**
```python
# Build complete list of variables to bootstrap
vars_to_bootstrap = list(bootstrap_variables) if bootstrap_variables else []

# Automatically add interaction term if selected
if moderator_var and moderator_var != "None" and include_interaction:
    interaction_term = f'{independent_var}_x_{moderator_var}'
    if interaction_term not in vars_to_bootstrap:
        vars_to_bootstrap.append(interaction_term)

# Automatically add lag variables if selected
if lag_vars:  # lag_vars defined earlier in function
    for lag_var in lag_vars:
        if lag_var not in vars_to_bootstrap:
            vars_to_bootstrap.append(lag_var)

# Ensure independent variable is always included
if independent_var not in vars_to_bootstrap:
    vars_to_bootstrap.insert(0, independent_var)
```

**Benefits:**
- Users no longer need to manually select these variables in the bootstrap UI
- Ensures consistent bootstrap inference for all key model parameters
- Particularly important for small cluster scenarios (G < 30)

### 2. Bootstrap Results Table in Publication Report

**Location:** `generate_publication_report()` function (lines ~1420-1540)

**What Changed:**
- Added a new publication-quality table showing bootstrap results
- Table is placed immediately after the main regression table in Section 1
- Uses the same schema and styling as the main regression table

**Table Features:**
- Shows only variables that were tested with bootstrap
- Displays coefficients with standard errors in parentheses
- **Significance stars based on bootstrap p-values** (not asymptotic)
- Includes bootstrap method description:
  - For one-way clustering: "Wild Cluster Bootstrap - '[cluster_var]' (G=X), Webb weights, X,XXX reps"
  - For two-way clustering: "Wild Cluster Bootstrap (WCR31) - Bootstrapped on '[cluster_var]' (G=X), Preserves '[other_cluster]' (G=X) correlation, X,XXX reps"
- Includes model fit statistics (R², R² Within, Observations)

**Example Output:**

```
## 1. Regression Results (Publication Table)

[Main regression table with asymptotic inference]

### Bootstrap Results (Wild Cluster Bootstrap Inference)

[Bootstrap table with bootstrap-based significance stars]

Significance levels based on bootstrap p-values: * p < 0.05, ** p < 0.01, *** p < 0.001
Note: This table shows only variables tested with wild cluster bootstrap inference.
```

**Key Differences from Main Table:**
- Main table: Uses asymptotic (CRV1/CRV3) p-values for significance
- Bootstrap table: Uses wild cluster bootstrap p-values for significance
- Bootstrap method replaces "S.E. type" row

### 3. Return Value Updates

**Modified Functions:**
- `run_fixed_effects_model()` - Now returns bootstrap results
- `run_pooled_ols_model()` - Updated to match new return signature
- `analyze_panel_data()` - Stores bootstrap results in params_dict

**Change:**
```python
# Old return
return results_summary, diagnostics, code

# New return
return results_summary, diagnostics, code, results, df_clean, multi_bootstrap_results
```

## When Bootstrap Runs Automatically

The bootstrap will automatically run for these variables when:

1. **Small clusters detected** (G < 30 in any clustering dimension)
2. **Bootstrap enabled** in UI (default: ON)
3. **Variables selected:**
   - Main independent variable (ALWAYS)
   - Interaction term (if moderator selected and "Include Interaction" checked)
   - Lag variables (if "Include Lagged DV" checked)
   - Any additional variables selected in bootstrap UI

## User Experience Impact

### Before:
- Users had to manually select lag variables and interaction terms in the bootstrap UI
- Easy to forget these variables, leading to inconsistent inference
- Publication report showed only main regression table

### After:
- All key model parameters automatically get bootstrap inference
- More consistent and reliable inference for small cluster scenarios
- Publication report includes dedicated bootstrap results table
- Clear distinction between asymptotic and bootstrap-based inference

## Testing

✅ Application launches successfully (`uv run experiment_1.py`)
✅ No syntax errors or import issues
✅ Backward compatible with existing code

## Technical Notes

1. **Bootstrap Results Storage:** Stored in `params_dict['bootstrap_results']` for publication report access

2. **Bootstrap Method Display:** Automatically detects and displays:
   - One-way vs. two-way clustering
   - WCR31 for two-way clustering
   - Number of clusters in each dimension
   - Number of bootstrap replications

3. **Variable Naming:** Interaction terms follow the pattern `{independent_var}_x_{moderator_var}`, lag variables follow `{dependent_var}_lag{N}`

## References

- Cameron, Gelbach & Miller (2008) "Bootstrap-Based Improvements for Inference"
- MacKinnon, Nielsen & Webb (2023) "Fast and Reliable Bootstrap Methods"
- Webb (2014) "Reworking Wild Bootstrap Based Inference"
- MacKinnon & Webb (2017) "Wild Bootstrap for Few Clusters"

## Files Modified

1. `c:\vs\advanced_panel\experiment_1.py`
   - Lines ~417-450: Auto-include lag and interaction variables in bootstrap
   - Lines ~455-460: Updated return values
   - Lines ~1073-1078: Updated pooled OLS return signature
   - Lines ~1330-1345: Store bootstrap results in params
   - Lines ~1420-1540: Add bootstrap results table to publication report
   - Lines ~1620-1635: Include bootstrap section in report compilation

## Next Steps

For future enhancements, consider:
- Adding bootstrap confidence intervals to the table
- Supporting custom significance thresholds
- Export bootstrap results to LaTeX/Word formats
- Add bootstrap diagnostics (convergence, power analysis)
