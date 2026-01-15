# UI Visual Guide: Multi-Variable Bootstrap

## What's Different in the UI?

### Standard Version (app_experiment.py)

```
┌─────────────────────────────────────────┐
│ Step 2: Configure Variables            │
├─────────────────────────────────────────┤
│ Dependent Variable (Y)                  │
│ ├─ ROA                                  │
│                                         │
│ Key Independent Variable (X)            │
│ ├─ emissions                            │
│                                         │
│ Control Variables                       │
│ ├─ □ size                               │
│ ├─ □ age                                │
│ ├─ □ leverage                           │
└─────────────────────────────────────────┘

Bootstrap behavior:
✓ Automatic when G < 30
✓ Bootstraps 'emissions' only
✗ No UI controls for bootstrap selection
```

### Multi-Variable Version (process/app_multi_bootstrap.py)

```
┌─────────────────────────────────────────┐
│ Step 2: Configure Variables            │
├─────────────────────────────────────────┤
│ Dependent Variable (Y)                  │
│ ├─ ROA                                  │
│                                         │
│ Key Independent Variable (X)            │
│ ├─ emissions                            │
│                                         │
│ Control Variables                       │
│ ├─ □ size                               │
│ ├─ □ age                                │
│ ├─ □ leverage                           │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Wild Cluster Bootstrap Settings ▼       │
├─────────────────────────────────────────┤
│ ⚠️ ADVANCED: Multi-Variable Bootstrap   │
│                                         │
│ Default: Only main independent variable │
│ Optional: Add controls below            │
│                                         │
│ ⚠️ Considerations:                      │
│ • Each variable adds ~10 seconds        │
│ • Consider multiple testing             │
│ • Most studies only bootstrap primary   │
│                                         │
│ ☑ Enable Wild Cluster Bootstrap        │
│                                         │
│ Variables to Bootstrap:                 │
│ ├─ ☑ emissions    ← DEFAULT: Selected  │
│ ├─ □ size                               │
│ ├─ □ age                                │
│ ├─ □ leverage                           │
└─────────────────────────────────────────┘

Bootstrap behavior:
✓ User-controlled
✓ Default: Only 'emissions' checked
✓ Optional: Check additional variables
✓ Dynamic updates when model changes
```

## Side-by-Side Comparison

### Feature 1: Bootstrap Variable Selection

**Standard Version**:
- No UI controls
- Hardcoded: bootstrap X only
- User cannot change

**Multi-Variable Version**:
- Checkbox group in accordion
- Default: X selected
- User can add controls
- Updates dynamically

### Feature 2: Results Display

**Standard Version**:
```
╔═══════════════════════════════════════╗
║   WILD CLUSTER BOOTSTRAP INFERENCE    ║
╚═══════════════════════════════════════╝

Bootstrap Results for emissions:
  • Bootstrap p-value: 0.0234 *
  • Asymptotic p-value: 0.0156 *
  
→ Use bootstrap p-value for inference
```

**Multi-Variable Version**:
```
╔═══════════════════════════════════════╗
║   WILD CLUSTER BOOTSTRAP (MULTI-VAR)  ║
╚═══════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variable: emissions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Bootstrap p-value: 0.0234 *
  • Asymptotic p-value: 0.0156 *

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variable: size
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Bootstrap p-value: 0.0456 *
  • Asymptotic p-value: 0.0312 *

⚠️ Multiple Testing: Apply corrections!
```

### Feature 3: Diagnostics

**Standard Version**:
```
Clustering Structure:
  • Method: One-way (Firm) CRV3
  • Details: 25 firms
  
✓ Wild cluster bootstrap used
```

**Multi-Variable Version**:
```
Clustering Structure:
  • Method: One-way (Firm) CRV3
  • Details: 25 firms

╔═══════════════════════════════════════╗
║   MULTI-VARIABLE BOOTSTRAP SUMMARY    ║
╚═══════════════════════════════════════╝

Variables tested with wild cluster bootstrap:
  • emissions
  • size

📖 Interpretation:
- Use bootstrap p-values for these variables
- Other variables rely on asymptotic inference
- Consider multiple testing corrections
```

### Feature 4: Code Generation

**Standard Version**:
```python
if n_clusters < 30:
    boot = results.wildboottest(
        param='emissions',  # Fixed: X only
        reps=9999,
        ...
    )
```

**Multi-Variable Version**:
```python
if n_clusters < 30:
    # Variables to test with bootstrap
    test_variables = ['emissions', 'size']  # User selected
    
    bootstrap_results = {}
    for var_name in test_variables:
        boot = results.wildboottest(
            param=var_name,  # Each variable
            reps=9999,
            ...
        )
        bootstrap_results[var_name] = boot
```

## UI Interaction Flow

### Standard Version

```
User uploads data
    ↓
Selects variables (X, Y, controls)
    ↓
Clicks "Run Analysis"
    ↓
App detects G < 30 automatically
    ↓
Bootstraps X only (no user choice)
    ↓
Shows results
```

### Multi-Variable Version

```
User uploads data
    ↓
Selects variables (X, Y, controls)
    ↓
Bootstrap UI updates automatically
    └─ Shows available variables
    └─ X is pre-selected
    ↓
User optionally checks more variables
    ├─ Default: Only X (standard)
    └─ Optional: Add controls
    ↓
Clicks "Run Analysis"
    ↓
App bootstraps selected variables
    ↓
Shows results for each variable
```

## Dynamic UI Updates

The multi-variable version has smart UI that updates automatically:

**Scenario 1: Change Independent Variable**
```
Action: Change X from 'emissions' to 'RD_spending'
Result: Bootstrap variables updates to:
        ☑ RD_spending    ← New X, auto-selected
        □ size
        □ age
        □ leverage
```

**Scenario 2: Add/Remove Controls**
```
Action: Check 'profit' in control variables
Result: Bootstrap variables updates to:
        ☑ emissions
        □ size
        □ age
        □ leverage
        □ profit        ← New option appears
```

**Scenario 3: Remove Independent Variable**
```
Action: Clear independent variable
Result: Bootstrap variables updates to:
        (empty - no variables available)
```

## Visual Warnings

The multi-variable version includes visual warnings:

### Warning Box 1: Multiple Testing
```
┌─────────────────────────────────────────┐
│ ⚠️ ADVANCED: Multi-Variable Bootstrap   │
│                                         │
│ Default: Only main independent variable │
│ Optional: Add controls below            │
│                                         │
│ ⚠️ Important Considerations:            │
│ • Each variable adds ~10 seconds        │
│ • Consider multiple testing corrections │
│ • Most studies only bootstrap primary   │
└─────────────────────────────────────────┘
```

### Warning Box 2: Results Interpretation
```
⚠️ NOTE ON MULTIPLE TESTING:
• When testing multiple variables, consider corrections
• Bonferroni: Multiply p-values by number of tests
• FDR control: Use Benjamini-Hochberg procedure
• Focus on primary hypothesis (usually X)
```

## UI Organization

### Standard Version Layout
```
Step 1: Upload Data
Step 2: Configure Variables
Step 3: Choose Method
Step 4: Specifications
   ├─ Year Fixed Effects
   ├─ Clustering Method
   └─ Moderator Variable
[Run Analysis Button]
```

### Multi-Variable Version Layout
```
Step 1: Upload Data
Step 2: Configure Variables
Step 3: Choose Method
Step 4: Specifications
   ├─ Year Fixed Effects
   ├─ Clustering Method
   └─ Moderator Variable
Step 5: Wild Cluster Bootstrap Settings  ← NEW!
   ├─ Enable Bootstrap
   └─ Select Variables
[Run Analysis Button]
```

## Accordion State

Both versions use accordions, but differently:

**Standard Version**:
- Method descriptions: Collapsed by default
- Clustering guide: Collapsed by default

**Multi-Variable Version**:
- Method descriptions: Collapsed by default
- Clustering guide: Collapsed by default
- Bootstrap settings: **Expanded by default** ← Key difference!
  - Reason: Users need to see new feature
  - Can collapse after selection

## Color Coding

Visual indicators in multi-variable version:

```
Variables to Bootstrap:
  ☑ emissions        ← Checked: Will bootstrap (blue)
  □ size            ← Unchecked: Asymptotic only (gray)
  □ age             ← Unchecked: Asymptotic only (gray)
```

In results:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variable: emissions        ← Separator (visual)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Bootstrap p-value: 0.0234 *    ← Star for significance
  • Asymptotic p-value: 0.0156 *
```

## User Experience Differences

### Standard Version UX
**Pros**:
- Simple, one-button analysis
- No decisions about bootstrap
- Follows best practices automatically
- Fast learning curve

**Cons**:
- Cannot bootstrap controls if needed
- Less flexibility

### Multi-Variable Version UX
**Pros**:
- Full control over bootstrap
- Can test multiple hypotheses
- Educational (shows what's being tested)
- Flexibility for advanced needs

**Cons**:
- More complex UI
- Requires understanding of multiple testing
- Longer computation if many variables
- Steeper learning curve

## Recommendation

**For teaching**: Use multi-variable version
- Shows students what bootstrap does
- Demonstrates multiple testing issues
- Educational value

**For research (most cases)**: Use standard version
- Follows best practices
- Simpler, faster
- Less prone to fishing expeditions

**For advanced research**: Use multi-variable version
- When genuinely need control bootstrap
- Multiple treatment variables
- Very small clusters (all variables questionable)

---

**Bottom line**: The UI difference is intentional. Standard version hides complexity, multi-variable version exposes it for users who need it.
