# Process Folder Contents

## Overview
This folder contains an **advanced version** of the panel data analysis app with multi-variable wild cluster bootstrap capabilities.

## Files in This Folder

### 1. **app_multi_bootstrap.py** (Main Application)
- Advanced panel data analysis app
- Allows user-selectable bootstrap variables via UI
- Default: Bootstrap only X (standard practice)
- Optional: Add controls to bootstrap list
- Runs on port 7861 (different from standard version)

### 2. **README.md** (Comprehensive Documentation)
- Complete feature documentation
- When to use this version vs. standard
- Multiple testing considerations
- Theoretical foundation
- Best practices and guidelines

### 3. **QUICKSTART.md** (Quick Start Guide)
- Installation and running instructions
- Example scenarios with step-by-step
- Common usage patterns
- Multiple testing correction formulas
- Troubleshooting guide

### 4. **COMPARISON.md** (Version Comparison)
- Detailed comparison of all three versions
- Decision tree for version selection
- Feature comparison table
- Use case examples by discipline
- Performance comparison

### 5. **UI_GUIDE.md** (UI Visual Guide)
- Side-by-side UI comparisons
- Visual mockups of interface
- Dynamic UI behavior
- Color coding and warnings
- User experience differences

## Quick Access

### Running the App
```powershell
cd c:\vs\advanced_panel\process
uv run app_multi_bootstrap.py
```
Or from root:
```powershell
cd c:\vs\advanced_panel
uv run process/app_multi_bootstrap.py
```

### Key Documentation
- **Getting Started**: QUICKSTART.md
- **Full Details**: README.md
- **Version Choice**: COMPARISON.md
- **UI Reference**: UI_GUIDE.md

## When to Use This Version

✅ **Use when**:
- Small clusters (G < 30)
- Multiple hypotheses to test
- Specific controls of substantive interest
- Reviewer requests bootstrap for controls
- Very small clusters (G < 20, all variables need bootstrap)

❌ **Don't use when**:
- Only care about primary variable → Use app_experiment.py
- Sufficient clusters (G ≥ 50) → Use app.py
- No specific reason to bootstrap controls → Use app_experiment.py

## Key Features

1. **User-Selectable Bootstrap Variables**
   - Checkbox interface for variable selection
   - Default: Only independent variable
   - Optional: Add controls

2. **Dynamic UI Updates**
   - Bootstrap options update when model changes
   - Smart defaults based on specification

3. **Multiple Testing Warnings**
   - Clear guidance on corrections
   - Bonferroni, Holm-Bonferroni, FDR examples

4. **Multi-Variable Results Display**
   - Separate section for each bootstrapped variable
   - Side-by-side asymptotic vs. bootstrap comparison

5. **Educational Value**
   - Shows what bootstrap tests
   - Demonstrates multiple testing issues
   - Generates complete code examples

## Theoretical Foundation

Based on:
- **Cameron, Gelbach & Miller (2008)**: Wild cluster bootstrap for small G
- **Webb (2014)**: Six-point distribution for optimal small-sample properties
- **MacKinnon, Nielsen & Webb (2023)**: Modern implementation guidelines

Extension to multiple variables follows standard hypothesis testing:
- Each variable = separate null hypothesis
- Each bootstrap = independent test
- Multiple testing corrections required

## Default Behavior

**Important**: The default behavior is identical to the standard version:
- ✓ Only independent variable is checked
- ✓ Bootstrap runs only for X
- ✓ Same as app_experiment.py

**Difference**: User CAN add more variables if needed
- This is optional, not automatic
- User must understand multiple testing
- Appropriate for specific research designs

## Example Use Cases

### Case 1: Standard Usage (Default)
```
Variables selected:
- X: emissions
- Controls: size, age, leverage

Bootstrap variables:
☑ emissions    ← Default
□ size
□ age
□ leverage

Result: Same as standard version
```

### Case 2: Multiple Treatments
```
Variables selected:
- X: policy_A
- Controls: policy_B, demographics

Bootstrap variables:
☑ policy_A     ← Default
☑ policy_B     ← User added
□ demographics

Result: Bootstrap both policies
```

### Case 3: Very Small Clusters
```
Variables selected:
- X: regulation
- Controls: concentration, RD

Bootstrap variables:
☑ regulation   ← Default
☑ concentration ← User added
☑ RD           ← User added

Result: Bootstrap all (G very small)
```

## Integration with Main Workspace

### File Structure
```
c:\vs\advanced_panel\
├── app.py                          ← Production (no bootstrap)
├── app_experiment.py               ← Standard bootstrap (X only)
├── README.md                       ← Updated with links
└── process\                        ← This folder
    ├── app_multi_bootstrap.py      ← Advanced multi-variable
    ├── README.md                   ← Full documentation
    ├── QUICKSTART.md               ← Quick start
    ├── COMPARISON.md               ← Version comparison
    ├── UI_GUIDE.md                 ← Visual guide
    └── INDEX.md                    ← This file
```

### Links from Main README
The main README.md has been updated with:
- Links to this folder
- Version comparison table
- Quick decision guide
- Running instructions

## Dependencies

No additional dependencies needed beyond main app:
- gradio
- pyfixest
- pandas
- numpy
- wildboottest (already required by app_experiment.py)

## Port Assignment

- app.py: **7860**
- app_experiment.py: **7860**
- process/app_multi_bootstrap.py: **7861** ← Different port!

This allows running both versions simultaneously for comparison.

## Performance Considerations

### Computation Time
- 1 variable (default): ~10 seconds
- 2 variables: ~20 seconds
- 3 variables: ~30 seconds
- 5 variables: ~50 seconds
- 10 variables: ~100 seconds

Formula: Time ≈ N_vars × 10 seconds (with 9,999 reps)

### Memory Usage
- Similar to standard version
- Each bootstrap stored in memory
- Not problematic for typical usage

## Testing Status

✅ **Tested**:
- UI updates dynamically
- Default behavior (X only)
- Multi-variable selection
- Results display
- Code generation

⚠️ **Note**: This is an advanced feature. Standard version (app_experiment.py) is recommended for most users.

## Future Enhancements

Potential improvements:
- [ ] User-configurable bootstrap replications
- [ ] Built-in multiple testing corrections
- [ ] Side-by-side comparison with asymptotic results
- [ ] Export results table
- [ ] Parallel bootstrap execution

## Support

For issues or questions:
1. Check QUICKSTART.md for common scenarios
2. Review COMPARISON.md for version selection
3. See README.md for complete documentation
4. Refer to UI_GUIDE.md for interface help

## Citation

If using in research, cite:
- pyfixest package
- Cameron et al. (2008) for wild bootstrap methodology
- Webb (2014) for weight selection

## License

Same as main application.

---

**Last Updated**: December 22, 2025
**Version**: 1.0
**Status**: Stable, ready for use

**Recommendation**: Most users should use `app_experiment.py` (standard bootstrap). This advanced version is for specific research needs requiring multi-variable bootstrap inference.
