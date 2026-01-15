# Code Refactoring Summary - December 23, 2025

## Overview
Refactored the codebase to consolidate bootstrap functionality and added support for two-way clustering with WCR31.

## Changes Made

### 1. **Consolidated Bootstrap Functions** ✅
- **Moved** all bootstrap execution functions from `app_multi_bootstrap.py` to `bootstrap_ui_module.py`
- **Centralized** bootstrap logic in a single module for easier maintenance
- `app_multi_bootstrap.py` is now **deprecated** and should not be used

### 2. **Enhanced `bootstrap_ui_module.py`** ✅

#### New Functions Added:
- `run_wild_bootstrap_for_variable()` - Single variable bootstrap with two-way support
- `run_bootstrap_for_selected_variables()` - Multi-variable bootstrap wrapper

#### Enhanced Features:
- **Two-Way Clustering Support**: Automatically detects when two-way clustering is used
- **WCR31 Implementation**: Uses `bootstrap_type="31"` for two-way clustering
- **Automatic Cluster Selection**: Identifies the dimension with fewer clusters
- **Preserves Correlation**: WCR31 accounts for correlation in both clustering dimensions

#### Updated Functions:
- `format_multi_variable_bootstrap_results()` - Now displays WCR31 information
- `generate_multi_variable_bootstrap_code()` - Generates code for one-way or two-way bootstrap

### 3. **Updated `app_experiment.py`** ✅

#### Import Changes:
```python
# OLD (deprecated)
from process.app_multi_bootstrap import run_bootstrap_for_selected_variables

# NEW (centralized)
from bootstrap_ui_module import (
    create_bootstrap_ui_section,
    update_bootstrap_variable_choices,
    format_multi_variable_bootstrap_results,
    format_multi_variable_bootstrap_diagnostics,
    generate_multi_variable_bootstrap_code,
    run_wild_bootstrap_for_variable,      # NEW
    run_bootstrap_for_selected_variables   # NEW
)
```

#### Simplified `run_wild_bootstrap_if_needed()`:
- Now delegates to `run_wild_bootstrap_for_variable()` from `bootstrap_ui_module.py`
- Removed 80+ lines of duplicate code
- Maintains same API for backward compatibility

#### Updated Multi-Variable Bootstrap Call:
```python
# OLD
from process.app_multi_bootstrap import run_bootstrap_for_selected_variables
multi_bootstrap_results = run_bootstrap_for_selected_variables(...)

# NEW
multi_bootstrap_results = run_bootstrap_for_selected_variables(...)  # Already imported
```

## New Feature: Two-Way Clustering with WCR31

### What is WCR31?
- **Wild Cluster Bootstrap with CRV3 adjustment** (bootstrap_type="31")
- Specifically designed for two-way clustering scenarios
- Preserves correlation structure in both clustering dimensions
- More reliable than asymptotic CRV3 when G < 30 in either dimension

### How It Works:

1. **Automatic Detection**: When two-way clustering is selected (e.g., Firm × Year)
2. **Cluster Counting**: Counts clusters in both dimensions
3. **Small Cluster Check**: If either dimension has < 30 clusters
4. **Dimension Selection**: Bootstraps on the dimension with **fewer** clusters
5. **WCR31 Application**: Uses `bootstrap_type="31"` instead of "11"
6. **Correlation Preservation**: Maintains correlation structure in the other dimension

### Example Output:

```
⚠️  Two-Way Clustering Detected
    Primary cluster: 'year' (G=12) ← Bootstrap dimension
    Secondary cluster: 'firm' (G=100)
    → Using WCR31 to preserve correlation structure

Bootstrap Results:
  • Bootstrap type: 31 (WCR31 - preserves correlation in 'firm' dimension)
  • Weights: Webb (2014) - optimal for small G
```

### Code Generation:
The generated Python code automatically includes:
- Cluster counting for both dimensions
- Selection logic for weaker clustering dimension
- Proper WCR31 bootstrap specifications
- Explanatory comments about correlation preservation

## Bootstrap Specifications

### One-Way Clustering (bootstrap_type="11")
```python
boot_result = results.wildboottest(
    param=variable_name,
    reps=9999,
    cluster=cluster_var_numeric,
    weights_type="webb",
    impose_null=True,
    bootstrap_type="11",  # Standard restricted bootstrap
    seed=12345,
    k_adj=True,
    G_adj=True
)
```

### Two-Way Clustering (bootstrap_type="31") - NEW!
```python
boot_result = results.wildboottest(
    param=variable_name,
    reps=9999,
    cluster=weaker_cluster_var,  # Automatically selected
    weights_type="webb",
    impose_null=True,
    bootstrap_type="31",  # WCR31 for two-way clustering
    seed=12345,
    k_adj=True,
    G_adj=True
)
```

## Benefits of This Refactoring

### 1. **Maintainability** 🔧
- Single source of truth for bootstrap logic in `bootstrap_ui_module.py`
- Easy to update bootstrap specifications in one place
- No duplicate code between single and multi-variable implementations

### 2. **Consistency** ✅
- All bootstrap execution uses the same underlying functions
- Identical specifications across UI and code generation
- Consistent error handling and reporting

### 3. **Extensibility** 🚀
- Easy to add new bootstrap types (just update `bootstrap_ui_module.py`)
- Simple to add new clustering dimensions
- Straightforward to enhance formatting or diagnostics

### 4. **Better Inference** 📊
- WCR31 provides more reliable inference for two-way clustering
- Automatically handles complex clustering scenarios
- Preserves correlation structure in both dimensions

## Files Modified

1. ✅ `bootstrap_ui_module.py` - Added bootstrap execution functions
2. ✅ `app_experiment.py` - Updated imports and simplified logic
3. ⚠️ `app_multi_bootstrap.py` - **DEPRECATED** (do not use)

## Migration Guide

### For Future Updates:

1. **Always modify** `bootstrap_ui_module.py` for bootstrap changes
2. **Never modify** `app_multi_bootstrap.py` (deprecated)
3. **Import from** `bootstrap_ui_module` in `app_experiment.py`

### Adding New Bootstrap Types:

1. Update `run_wild_bootstrap_for_variable()` in `bootstrap_ui_module.py`
2. Update `format_multi_variable_bootstrap_results()` for display
3. Update `generate_multi_variable_bootstrap_code()` for code generation
4. Test with small datasets

## Testing Checklist

- [ ] One-way clustering (firm only) with G < 30
- [ ] One-way clustering (firm only) with G > 30
- [ ] Two-way clustering (firm × year) with both G > 30
- [ ] Two-way clustering with one G < 30 (triggers WCR31)
- [ ] Two-way clustering with both G < 30 (triggers WCR31)
- [ ] Multi-variable bootstrap selection
- [ ] Code generation for all scenarios

## References

- Cameron, Gelbach & Miller (2008) "Bootstrap-Based Improvements for Inference with Clustered Errors"
- MacKinnon, Nielsen & Webb (2023) "Fast and Reliable Jackknife and Bootstrap Methods for Cluster-Robust Inference"
- MacKinnon & Webb (2017) "Wild Bootstrap Inference for Wildly Different Cluster Sizes"
- Webb (2014) "Reworking Wild Bootstrap Based Inference for Clustered Errors"

## Questions?

If you need to:
- Add new bootstrap features → Update `bootstrap_ui_module.py`
- Change bootstrap specifications → Update `bootstrap_ui_module.py`
- Modify UI for bootstrap → Update `bootstrap_ui_module.py` (UI section)
- Use bootstrap in main app → Import from `bootstrap_ui_module.py`
