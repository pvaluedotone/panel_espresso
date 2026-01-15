# Bootstrap UI Module Documentation

## Overview

The `bootstrap_ui_module.py` provides reusable Gradio UI components for wild cluster bootstrap variable selection in panel data analysis applications.

## Purpose

This module was created to:
1. Enable multi-variable wild cluster bootstrap selection via UI
2. Provide a reusable component that can be integrated into any panel data app
3. Maintain consistent bootstrap UI across different app versions

## Integration

### In app_experiment.py

The module has been integrated into `app_experiment.py` immediately before the "Moderating Variable (Interaction Term)" section. Users can now:

1. **Enable/Disable Bootstrap**: Checkbox to toggle wild cluster bootstrap
2. **Select Variables**: Choose which variables to bootstrap (default: only X)
3. **View Warnings**: See computational cost and multiple testing warnings

### Usage in app_experiment.py

The bootstrap UI appears as:
```
Step 4: Specifications
  ├─ Year Fixed Effects
  ├─ Clustering Method
  ├─ Wild Cluster Bootstrap Settings ← NEW!
  │   ├─ Enable Wild Cluster Bootstrap
  │   └─ Variables to Bootstrap (for illustration)
  │       ☑ emissions (default - main predictor)
  │       □ size
  │       □ age
  │       □ leverage
  └─ Moderating Variable (Optional)
```

## Module Functions

### 1. `create_bootstrap_ui_section()`
Creates the complete bootstrap UI section including:
- Accordion wrapper
- Enable/disable checkbox
- Variable selection checkboxes
- Educational text and warnings

**Returns**: `(use_bootstrap, bootstrap_variables, accordion)`

### 2. `update_bootstrap_variable_choices(independent_var, control_vars)`
Dynamically updates bootstrap variable options when model specification changes.

**Parameters**:
- `independent_var`: Main independent variable
- `control_vars`: List of control variables

**Returns**: Updated CheckboxGroup with new choices

**Default Behavior**: Only independent variable is pre-selected

### 3. `format_multi_variable_bootstrap_results(multi_bootstrap_results, coef_df, coef_name_col)`
Formats bootstrap results for multiple variables for display.

**Parameters**:
- `multi_bootstrap_results`: Dict mapping variable names to bootstrap results
- `coef_df`: Coefficient dataframe from pyfixest
- `coef_name_col`: Name of coefficient column

**Returns**: Formatted string with bootstrap results for each variable

### 4. `format_multi_variable_bootstrap_diagnostics(multi_bootstrap_results)`
Creates diagnostic summary showing which variables were bootstrapped.

**Returns**: Formatted diagnostic section string

### 5. `generate_multi_variable_bootstrap_code(cluster_var, bootstrap_variables)`
Generates Python code for multi-variable bootstrap.

**Parameters**:
- `cluster_var`: Clustering variable name
- `bootstrap_variables`: List of variables to bootstrap

**Returns**: Python code snippet

## Integration Steps

To integrate this module into another app:

### Step 1: Import the module
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'process'))
from bootstrap_ui_module import (
    create_bootstrap_ui_section,
    update_bootstrap_variable_choices,
    format_multi_variable_bootstrap_results,
    format_multi_variable_bootstrap_diagnostics,
    generate_multi_variable_bootstrap_code
)
```

### Step 2: Add UI components
```python
# In your Gradio interface, add before moderator section:
use_bootstrap, bootstrap_variables, bootstrap_accordion = create_bootstrap_ui_section()
```

### Step 3: Add event handlers
```python
# Update bootstrap choices when model changes
independent_dropdown.change(
    fn=update_bootstrap_variable_choices,
    inputs=[independent_dropdown, control_checkbox],
    outputs=[bootstrap_variables]
)

control_checkbox.change(
    fn=update_bootstrap_variable_choices,
    inputs=[independent_dropdown, control_checkbox],
    outputs=[bootstrap_variables]
)
```

### Step 4: Update analysis function
```python
def analyze_panel_data(..., use_bootstrap, bootstrap_variables):
    # Pass to model estimation function
    run_fixed_effects_model(..., use_bootstrap, bootstrap_variables)
```

### Step 5: Use formatting functions
```python
# In results formatting:
bootstrap_section = format_multi_variable_bootstrap_results(
    multi_bootstrap_results, coef_df, coef_name_col
)

# In diagnostics:
bootstrap_diagnostics = format_multi_variable_bootstrap_diagnostics(
    multi_bootstrap_results
)

# In code generation:
bootstrap_code = generate_multi_variable_bootstrap_code(
    cluster_var, bootstrap_variables
)
```

## Default Behavior

**Important**: The module maintains standard practice by default:
- ✅ Only independent variable is pre-selected
- ✅ Users must consciously add controls
- ✅ Warnings about multiple testing displayed
- ✅ Accordion starts collapsed (non-intrusive)

## Features

### Educational Content
- Explains when to use multi-variable bootstrap
- Warns about computational cost
- Discusses multiple testing corrections
- Provides best practice guidance

### Dynamic Updates
- Variable choices update when model specification changes
- Default selection always includes only X
- Smooth user experience

### Multiple Testing
- Automatic detection when > 1 variable selected
- Bonferroni correction formula displayed
- References to Holm-Bonferroni and FDR methods

## Files

### Module
- `process/bootstrap_ui_module.py` - Main module file

### Integration
- `app_experiment.py` - Now includes bootstrap UI module
- `process/app_multi_bootstrap.py` - Standalone multi-variable app (reference)

## Comparison

### Without Module (Original app_experiment.py)
- Bootstrap runs automatically for X only
- No UI controls
- Standard practice enforced

### With Module (Updated app_experiment.py)
- Bootstrap UI section added
- Default: Only X selected (standard practice)
- Optional: Add controls via UI
- User has full control

## Documentation

See also:
- `process/README.md` - Multi-variable bootstrap documentation
- `process/QUICKSTART.md` - Usage examples
- `process/COMPARISON.md` - Version comparison
- `EXPERIMENTAL_BOOTSTRAP_NOTES.md` - Bootstrap theory

## Version History

- **December 22, 2025**: Initial module creation and integration
  - Created reusable bootstrap UI components
  - Integrated into app_experiment.py
  - Maintains backward compatibility (default behavior unchanged)

## Support

For questions:
1. Check this README for integration steps
2. See example usage in `app_experiment.py`
3. Review standalone implementation in `process/app_multi_bootstrap.py`

---

**Design Philosophy**: Provide advanced features while maintaining standard practice as default. Users must consciously opt-in to multi-variable bootstrap, ensuring thoughtful usage.
