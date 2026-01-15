# Regression Formula Structure for experiment_1.py

## Overview
This document explains how the regression formulas are built in `experiment_1.py` for use in progressive model specifications like `pf.etable([fit1, fit2, fit3, fit4, fit5, fit6])`.

---

## Formula Building Process (Fixed Effects Model)

### Location in Code
**Function**: `run_fixed_effects_model()` (Lines 178-480)

### Step 1: Prepare Variables
```python
# Base variables
exog_vars = [independent_var] + control_vars

# Add interaction term if specified
if moderator_var and moderator_var != "None" and include_interaction:
    exog_vars.append(f'{independent_var}_x_{moderator_var}')

# Add lagged dependent variables if specified
if lag_vars:  # lag_vars = ['DV_lag1', 'DV_lag2', ...]
    exog_vars.extend(lag_vars)

# Combine all exogenous variables
formula_rhs = ' + '.join(exog_vars)
```

### Step 2: Build Fixed Effects
```python
# Firm FE only
if not include_year_fe:
    fixed_effects = f"{firm_id_col}"

# Firm FE + Year FE
if include_year_fe:
    fixed_effects = f"{firm_id_col} + {year_col}"
```

### Step 3: Complete Formula
```python
# pyfixest formula format: "Y ~ X1 + X2 + ... | FE1 + FE2"
formula = f"{dependent_var} ~ {formula_rhs} | {fixed_effects}"
```

---

## Example Formula Progressions

### Progressive Specification Example 1: Adding Controls
```python
# Model 1: Basic (independent variable only)
formula1 = "ROA ~ CSR | firm_id"

# Model 2: Add control 1
formula2 = "ROA ~ CSR + size | firm_id"

# Model 3: Add control 2
formula3 = "ROA ~ CSR + size + leverage | firm_id"

# Model 4: Add year fixed effects
formula4 = "ROA ~ CSR + size + leverage | firm_id + year"

# Model 5: Add interaction
formula5 = "ROA ~ CSR + size + leverage + CSR_x_governance | firm_id + year"

# Model 6: Add lagged DV
formula6 = "ROA ~ CSR + size + leverage + CSR_x_governance + ROA_lag1 | firm_id + year"
```

### Progressive Specification Example 2: Industry Analysis
```python
# Model 1: Pooled OLS (no FE)
formula1 = "profit ~ innovation | 0"  # 0 means no fixed effects

# Model 2: Add industry dummies
formula2 = "profit ~ innovation | industry"

# Model 3: Add country dummies
formula3 = "profit ~ innovation | industry + country"

# Model 4: Add firm FE (most stringent)
formula4 = "profit ~ innovation | firm_id"

# Model 5: Firm FE + Year FE
formula5 = "profit ~ innovation | firm_id + year"

# Model 6: Add controls
formula6 = "profit ~ innovation + size + debt | firm_id + year"
```

---

## Current Model Structure in Your Code

### Fixed Effects Model
**Line 257-268**:
```python
formula_rhs = ' + '.join(exog_vars)

# Add fixed effects
if include_year_fe:
    fixed_effects = f"{firm_id_col} + {year_col}"
else:
    fixed_effects = f"{firm_id_col}"

formula = f"{dependent_var} ~ {formula_rhs} | {fixed_effects}"
```

**Line 418**: Actual estimation
```python
results = pf.feols(formula, data=df_clean, vcov=vcov, demeaner_backend="rust")
```

### Variables Structure
From your current code:

1. **dependent_var**: String (e.g., "ROA", "profit")
2. **independent_var**: String (e.g., "CSR", "innovation")
3. **control_vars**: List of strings (e.g., ["size", "leverage", "age"])
4. **moderator_var**: String or "None" (e.g., "governance")
5. **lag_vars**: List of strings (e.g., ["ROA_lag1", "ROA_lag2"])
6. **firm_id_col**: String (e.g., "firm_id", "company_id")
7. **year_col**: String (e.g., "year", "time")

---

## Clustering (vcov) Structure

### Location in Code
**Lines 383-415**:

```python
# One-way firm clustering
vcov = {'CRV1': firm_id_col}                    # Standard
vcov = {'CRV3': firm_id_col}                    # Small-cluster correction

# One-way industry clustering
vcov = {'CRV1': industry_var}
vcov = {'CRV3': industry_var}

# One-way country clustering
vcov = {'CRV1': country_var}
vcov = {'CRV3': country_var}

# Two-way firm × year clustering
vcov = {'CRV1': f"{firm_id_col} + {year_col}"}
vcov = {'CRV3': f"{firm_id_col} + {year_col}"}

# Two-way industry × country clustering
vcov = {'CRV1': f"{industry_var} + {country_var}"}
vcov = {'CRV3': f"{industry_var} + {country_var}"}

# Robust (heteroskedasticity only)
vcov = 'hetero'
```

---

## How to Build Progressive Models for etable()

### Strategy 1: Stepwise Addition (Most Common)
Build models progressively by adding variables:

```python
# Step 1: Build base formula components
base_vars = [independent_var]
all_controls = control_vars  # ["size", "leverage", "age"]

# Step 2: Create progressive formulas
formulas = []

# Model 1: Independent variable only
formulas.append(f"{dependent_var} ~ {independent_var} | {firm_id_col}")

# Model 2-4: Add controls one by one or in groups
for i in range(len(all_controls)):
    vars_so_far = base_vars + all_controls[:i+1]
    formula = f"{dependent_var} ~ {' + '.join(vars_so_far)} | {firm_id_col}"
    formulas.append(formula)

# Model 5: Add year FE
formula = f"{dependent_var} ~ {' + '.join(base_vars + all_controls)} | {firm_id_col} + {year_col}"
formulas.append(formula)

# Model 6: Add interaction
if moderator_var:
    vars_with_interaction = base_vars + all_controls + [f"{independent_var}_x_{moderator_var}"]
    formula = f"{dependent_var} ~ {' + '.join(vars_with_interaction)} | {firm_id_col} + {year_col}"
    formulas.append(formula)

# Step 3: Fit all models
fits = [pf.feols(f, data=df_clean, vcov=vcov) for f in formulas]

# Step 4: Create table
pf.etable(fits)
```

### Strategy 2: Different Estimation Methods
Compare different approaches:

```python
# Model 1: Pooled OLS
fit1 = pf.feols(f"{dependent_var} ~ {independent_var} + {' + '.join(control_vars)}", 
                data=df_clean, vcov='hetero')

# Model 2: Industry FE
fit2 = pf.feols(f"{dependent_var} ~ {independent_var} + {' + '.join(control_vars)} | {industry_var}", 
                data=df_clean, vcov={'CRV1': industry_var})

# Model 3: Firm FE
fit3 = pf.feols(f"{dependent_var} ~ {independent_var} + {' + '.join(control_vars)} | {firm_id_col}", 
                data=df_clean, vcov={'CRV1': firm_id_col})

# Model 4: Firm + Year FE
fit4 = pf.feols(f"{dependent_var} ~ {independent_var} + {' + '.join(control_vars)} | {firm_id_col} + {year_col}", 
                data=df_clean, vcov={'CRV3': f"{firm_id_col} + {year_col}"})

# Create comparison table
pf.etable([fit1, fit2, fit3, fit4])
```

### Strategy 3: Robustness Checks
Same specification, different clustering:

```python
# Same formula, different vcov
formula = f"{dependent_var} ~ {independent_var} + {' + '.join(control_vars)} | {firm_id_col} + {year_col}"

# Model 1: Firm clustering (CRV1)
fit1 = pf.feols(formula, data=df_clean, vcov={'CRV1': firm_id_col})

# Model 2: Firm clustering (CRV3)
fit2 = pf.feols(formula, data=df_clean, vcov={'CRV3': firm_id_col})

# Model 3: Two-way clustering (CRV1)
fit3 = pf.feols(formula, data=df_clean, vcov={'CRV1': f"{firm_id_col} + {year_col}"})

# Model 4: Two-way clustering (CRV3)
fit4 = pf.feols(formula, data=df_clean, vcov={'CRV3': f"{firm_id_col} + {year_col}"})

# Create comparison table
pf.etable([fit1, fit2, fit3, fit4])
```

---

## Key Variables Available in Your Code

### After `run_fixed_effects_model()` returns:
- **results_obj**: The pyfixest Feols object (single model)
- **df_clean**: The cleaned dataframe used for estimation
- **params_dict**: Dictionary with all model parameters

### After `analyze_panel_data()` returns:
```python
results_text, diagnostics_text, code_text, results_obj, df_clean, params_dict = analyze_panel_data(...)
```

Where `params_dict` contains:
```python
{
    'firm_id_col': str,
    'year_col': str,
    'dependent_var': str,
    'independent_var': str,
    'control_vars': list,
    'method': str,
    'include_year_fe': bool,
    'cluster_method': str,
    'moderator_var': str,
    'include_interaction': bool,
    'industry_var': str,
    'country_var': str,
    'include_lag_dv': bool,
    'lag_min': int,
    'lag_max': int,
    'bootstrap_results': dict
}
```

---

## How to Extract Formula from Your Current Code

### Option 1: Reconstruct from params_dict
```python
def reconstruct_formula(params):
    """Reconstruct the formula used in estimation"""
    
    # Build RHS variables
    exog_vars = [params['independent_var']] + params['control_vars']
    
    # Add interaction if present
    if params['moderator_var'] and params['moderator_var'] != "None" and params['include_interaction']:
        interaction = f"{params['independent_var']}_x_{params['moderator_var']}"
        exog_vars.append(interaction)
    
    # Add lags if present
    if params['include_lag_dv']:
        for lag in range(params['lag_min'], params['lag_max'] + 1):
            exog_vars.append(f"{params['dependent_var']}_lag{lag}")
    
    formula_rhs = ' + '.join(exog_vars)
    
    # Build fixed effects
    if params['include_year_fe']:
        fixed_effects = f"{params['firm_id_col']} + {params['year_col']}"
    else:
        fixed_effects = params['firm_id_col']
    
    # Complete formula
    formula = f"{params['dependent_var']} ~ {formula_rhs} | {fixed_effects}"
    
    return formula
```

### Option 2: Store formula in results
Add to `run_fixed_effects_model()` before return:
```python
# Add this before the return statement (around line 468)
params_dict['formula'] = formula
params_dict['vcov'] = vcov
```

Then return an extended params_dict.

---

## Recommended Approach for export_report.py

### Create a function to generate progressive models:

```python
def generate_progressive_models(df_clean, params):
    """
    Generate progressive model specifications for etable
    
    Returns:
    --------
    list : List of fitted pyfixest models
    """
    
    # Extract parameters
    dv = params['dependent_var']
    iv = params['independent_var']
    controls = params['control_vars']
    firm_id = params['firm_id_col']
    year = params['year_col']
    include_year_fe = params['include_year_fe']
    moderator = params['moderator_var']
    include_interaction = params['include_interaction']
    cluster_method = params['cluster_method']
    
    # Determine vcov (same logic as main code)
    if cluster_method == "One-way (Firm only) with CRV1":
        vcov = {'CRV1': firm_id}
    elif cluster_method == "Two-way (Firm × Year) with CRV3":
        vcov = {'CRV3': f"{firm_id} + {year}"}
    # ... etc
    
    fits = []
    
    # Model 1: Independent variable only
    formula1 = f"{dv} ~ {iv} | {firm_id}"
    fits.append(pf.feols(formula1, data=df_clean, vcov=vcov))
    
    # Model 2-N: Add controls progressively
    for i in range(len(controls)):
        vars_so_far = [iv] + controls[:i+1]
        formula = f"{dv} ~ {' + '.join(vars_so_far)} | {firm_id}"
        fits.append(pf.feols(formula, data=df_clean, vcov=vcov))
    
    # Model N+1: Add year FE if requested
    if include_year_fe:
        vars_all = [iv] + controls
        formula = f"{dv} ~ {' + '.join(vars_all)} | {firm_id} + {year}"
        fits.append(pf.feols(formula, data=df_clean, vcov=vcov))
    
    # Model N+2: Add interaction if present
    if moderator and moderator != "None" and include_interaction:
        vars_with_interaction = [iv] + controls + [f"{iv}_x_{moderator}"]
        fe = f"{firm_id} + {year}" if include_year_fe else firm_id
        formula = f"{dv} ~ {' + '.join(vars_with_interaction)} | {fe}"
        fits.append(pf.feols(formula, data=df_clean, vcov=vcov))
    
    return fits
```

### Use in export_report.py:

```python
from pyfixest import etable
from io import StringIO

def generate_etable_for_export(df_clean, params):
    """
    Generate pyfixest etable for Word export
    """
    # Generate progressive models
    fits = generate_progressive_models(df_clean, params)
    
    # Create etable
    table = etable(fits)
    
    # Convert to string if needed
    return str(table)
```

---

## Summary

**Current formula structure**:
- Built in `run_fixed_effects_model()` at **lines 253-268**
- Stored as `results_obj` (pyfixest Feols object) at **line 418**
- Parameters stored in `params_dict` at **lines 1320-1335**

**To use in export_report.py**:
1. Extract `df_clean` and `params_dict` from stored results
2. Reconstruct formula components from `params_dict`
3. Generate progressive model specifications
4. Fit models with `pf.feols()`
5. Create table with `pf.etable([fit1, fit2, fit3, ...])`
6. Export to Word document

**Key insight**: You have all the information needed in `params_dict` to reconstruct any formula variant.
