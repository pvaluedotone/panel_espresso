"""
Panel Data Analysis App with pyfixest - EXPERIMENT 1: Native Output Display
Analysing panel data with pooled OLS, random and fixed effects models
Refactored to use pyfixest with Wild Cluster Bootstrap for small clusters
Author: Saiyidi MAT RONI (Modified to use pyfixest with bootstrap)
Date: December 23, 2025

EXPERIMENT 1 FEATURES:
- Uses pyfixest's native .summary() method for cleaner output
- Publication-quality tables directly from pyfixest
- Standard econometric formatting without manual text conversion
- Wild cluster bootstrap inference for datasets with few clusters (< 30)
- Automatic detection of small cluster scenarios
- Bootstrap-based p-values alongside asymptotic inference
- Two-way clustering with WCR31 (preserves correlation structure)
"""

import gradio as gr
import pandas as pd
import numpy as np
import pyfixest as pf
import traceback
from typing import Optional, List, Tuple, Dict
import warnings
import wildboottest
from io import StringIO
import sys
warnings.filterwarnings('ignore')

# Import bootstrap UI module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'process'))
from bootstrap_ui_module import (
    create_bootstrap_ui_section,
    update_bootstrap_variable_choices,
    format_multi_variable_bootstrap_results,
    format_multi_variable_bootstrap_diagnostics,
    generate_multi_variable_bootstrap_code,
    run_wild_bootstrap_for_variable,
    run_bootstrap_for_selected_variables
)
from export_report import (
    export_report_to_word_gradio,
    create_export_ui
)
from stepwise_report import (
    generate_stepwise_report,
    export_stepwise_models_for_word
)


def load_and_validate_data(file_path: str) -> Tuple[Optional[pd.DataFrame], str]:
    """Load CSV and perform basic validation"""
    try:
        df = pd.read_csv(file_path)
        
        if df.empty:
            return None, "❌ Error: Uploaded file is empty"
        
        if len(df.columns) < 3:
            return None, "❌ Error: File must have at least 3 columns (firm ID, year, and one variable)"
        
        return df, f"✅ Data loaded successfully: {len(df):,} rows × {len(df.columns)} columns"
    
    except Exception as e:
        return None, f"❌ Error loading file: {str(e)}"


def run_wild_bootstrap_if_needed(
    results,
    df_clean: pd.DataFrame,
    firm_id_col: str,
    year_col: str,
    cluster_method: str,
    country_var: Optional[str],
    industry_var: Optional[str],
    test_param: str,
    bootstrap_reps: int = 9999
) -> Optional[Dict]:
    """
    Run wild cluster bootstrap if clusters are small (< 30)
    
    NEW: Supports two-way clustering with automatic WCR31 application
    
    Based on Cameron, Gelbach & Miller (2008) and MacKinnon, Nielsen & Webb (2023),
    wild cluster bootstrap provides more reliable inference with few clusters.
    
    This function now delegates to bootstrap_ui_module.run_wild_bootstrap_for_variable
    for consistent bootstrap execution.
    
    Parameters:
    -----------
    results : pyfixest Feols object
        Estimated model results
    df_clean : pd.DataFrame
        Clean data used for estimation (must contain _firm_id_numeric, _year_numeric, etc.)
    firm_id_col : str
        Firm ID column name
    year_col : str
        Year column name
    cluster_method : str
        Clustering method used
    country_var : Optional[str]
        Country variable if applicable
    industry_var : Optional[str]
        Industry variable if applicable
    test_param : str
        Parameter to test (usually the main independent variable)
    bootstrap_reps : int
        Number of bootstrap replications (default 9999)
    
    Returns:
    --------
    Dict or None : Bootstrap results if clusters < 30, otherwise None
    """
    return run_wild_bootstrap_for_variable(
        results, df_clean, firm_id_col, year_col, cluster_method,
        country_var, industry_var, test_param, bootstrap_reps
    )


def get_column_names(file) -> dict:
    """Extract column names from uploaded file for dynamic dropdown population"""
    if file is None:
        empty_list = []
        return {
            firm_id_dropdown: gr.Dropdown(choices=empty_list, value=None),
            year_dropdown: gr.Dropdown(choices=empty_list, value=None),
            dependent_dropdown: gr.Dropdown(choices=empty_list, value=None),
            independent_dropdown: gr.Dropdown(choices=empty_list, value=None),
            control_checkbox: gr.CheckboxGroup(choices=empty_list, value=[]),
            moderator_dropdown: gr.Dropdown(choices=empty_list, value=None),
            industry_dropdown: gr.Dropdown(choices=empty_list, value=None),
            country_dropdown: gr.Dropdown(choices=empty_list, value=None),
            data_status: "⚠️ Please upload a CSV file"
        }
    
    try:
        df = pd.read_csv(file.name)
        columns = list(df.columns)
        
        # Try to detect common column patterns
        firm_id_guess = next((col for col in columns if any(x in col.lower() for x in ['firm', 'company', 'id', 'entity'])), columns[0] if columns else None)
        year_guess = next((col for col in columns if any(x in col.lower() for x in ['year', 'time', 'period', 'date'])), columns[1] if len(columns) > 1 else None)
        
        # Numeric columns for dependent/independent variables
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        return {
            firm_id_dropdown: gr.Dropdown(choices=columns, value=firm_id_guess),
            year_dropdown: gr.Dropdown(choices=columns, value=year_guess),
            dependent_dropdown: gr.Dropdown(choices=numeric_cols, value=numeric_cols[0] if numeric_cols else None),
            independent_dropdown: gr.Dropdown(choices=numeric_cols, value=numeric_cols[1] if len(numeric_cols) > 1 else None),
            control_checkbox: gr.CheckboxGroup(choices=numeric_cols, value=[]),
            moderator_dropdown: gr.Dropdown(choices=columns + ["None"], value="None"),
            industry_dropdown: gr.Dropdown(choices=columns + ["None"], value="None"),
            country_dropdown: gr.Dropdown(choices=columns + ["None"], value="None"),
            data_status: f"✅ Data loaded: {len(df):,} rows × {len(columns)} columns | {len(df[firm_id_guess].unique()) if firm_id_guess else '?'} firms"
        }
    
    except Exception as e:
        empty_list = []
        return {
            firm_id_dropdown: gr.Dropdown(choices=empty_list, value=None),
            year_dropdown: gr.Dropdown(choices=empty_list, value=None),
            dependent_dropdown: gr.Dropdown(choices=empty_list, value=None),
            independent_dropdown: gr.Dropdown(choices=empty_list, value=None),
            control_checkbox: gr.CheckboxGroup(choices=empty_list, value=[]),
            moderator_dropdown: gr.Dropdown(choices=empty_list, value=None),
            industry_dropdown: gr.Dropdown(choices=empty_list, value=None),
            country_dropdown: gr.Dropdown(choices=empty_list, value=None),
            data_status: f"❌ Error: {str(e)}"
        }


def get_significance_stars(pval):
    """Return significance stars based on p-value"""
    if pval < 0.001:
        return "***"
    elif pval < 0.01:
        return "**"
    elif pval < 0.05:
        return "*"
    return ""


def run_fixed_effects_model(
    df: pd.DataFrame,
    firm_id_col: str,
    year_col: str,
    dependent_var: str,
    independent_var: str,
    control_vars: List[str],
    include_year_fe: bool,
    moderator_var: Optional[str],
    include_interaction: bool,
    cluster_method: str = "One-way (Firm only) with CRV1",
    country_var: Optional[str] = None,
    industry_var: Optional[str] = None,
    include_lag_dv: bool = False,
    lag_min: Optional[int] = None,
    lag_max: Optional[int] = None,
    use_wild_bootstrap: bool = True,
    bootstrap_variables: List[str] = None,
    bootstrap_reps: int = 9999
) -> Tuple[str, str, str]:
    """
    Run Fixed Effects (Within) Model with firm and optionally year fixed effects using pyfixest
    
    EXPERIMENTAL: Includes wild cluster bootstrap for small cluster inference
    - Automatically runs bootstrap when clusters < 30
    - Provides bootstrap p-values alongside asymptotic inference
    - Uses Webb weights for better small-sample properties
    """
    try:
        # Prepare panel data
        df_clean = df[[firm_id_col, year_col, dependent_var, independent_var] + control_vars].copy()
        
        # Sort by firm and year for proper lagging
        df_clean = df_clean.sort_values([firm_id_col, year_col])
        
        # CRITICAL FIX: Convert cluster variables to numeric codes for wildboottest compatibility
        # wildboottest/Numba requires numeric types, not strings/objects
        firm_id_numeric = f"_firm_id_numeric"
        year_numeric = f"_year_numeric"
        df_clean[firm_id_numeric] = pd.Categorical(df_clean[firm_id_col]).codes
        df_clean[year_numeric] = pd.Categorical(df_clean[year_col]).codes
        
        # Add country if clustering by country
        if "Country" in cluster_method and country_var and country_var != "None":
            df_clean[country_var] = df[country_var]
            country_numeric = f"_country_numeric"
            df_clean[country_numeric] = pd.Categorical(df_clean[country_var]).codes
        
        # Add industry if clustering by industry
        if "Industry" in cluster_method and industry_var and industry_var != "None":
            df_clean[industry_var] = df[industry_var]
            industry_numeric = f"_industry_numeric"
            df_clean[industry_numeric] = pd.Categorical(df_clean[industry_var]).codes
        
        # Add moderator if specified
        if moderator_var and moderator_var != "None" and include_interaction:
            df_clean[moderator_var] = df[moderator_var]
            df_clean[f'{independent_var}_x_{moderator_var}'] = df[independent_var] * df[moderator_var]
        
        # Create lagged dependent variables if requested
        lag_vars = []
        if include_lag_dv and lag_min is not None and lag_max is not None:
            for lag in range(lag_min, lag_max + 1):
                lag_var_name = f'{dependent_var}_lag{lag}'
                df_clean[lag_var_name] = df_clean.groupby(firm_id_col)[dependent_var].shift(lag)
                lag_vars.append(lag_var_name)
        
        # Drop missing values
        df_clean = df_clean.dropna()
        
        # Build formula for pyfixest
        # Base formula
        exog_vars = [independent_var] + control_vars
        if moderator_var and moderator_var != "None" and include_interaction:
            exog_vars.append(f'{independent_var}_x_{moderator_var}')
        if lag_vars:
            exog_vars.extend(lag_vars)
        
        formula_rhs = ' + '.join(exog_vars)
        
        # Add fixed effects
        if include_year_fe:
            fixed_effects = f"{firm_id_col} + {year_col}"
        else:
            fixed_effects = f"{firm_id_col}"
        
        formula = f"{dependent_var} ~ {formula_rhs} | {fixed_effects}"
        
        # Validate clustering method against available variables
        # Check if required cluster variables are defined
        if "Industry" in cluster_method and (not industry_var or industry_var == "None"):
            error_msg = """❌ **Clustering Method Error: Industry Variable Required**

The selected clustering method requires an **Industry** variable, but none is defined.

**To fix this:**
1. Go to **Step 2: Select Variables**
2. In the **Time-invariant Variables (Optional)** section
3. Select your industry column in the **Industry/Sector Column** dropdown

**Why this matters:**
Industry-level clustering accounts for correlation within industries, which is essential when:
- Treatment or policies vary by industry
- Industry-level shocks affect multiple firms
- You want standard errors robust to industry-level clustering

Please define the Industry variable and try again.
"""
            return error_msg, "", "", None, None, {}
        
        if "Country" in cluster_method and (not country_var or country_var == "None"):
            # Check if it's two-way Industry×Country (needs country)
            if "Industry × Country" in cluster_method:
                error_msg = """❌ **Clustering Method Error: Country Variable Required**

The selected clustering method **Two-way (Industry × Country)** requires both Industry and Country variables.

**To fix this:**
1. Go to **Step 2: Select Variables**
2. In the **Time-invariant Variables (Optional)** section
3. Select your country column in the **Country Column** dropdown

**Why this matters:**
Two-way Industry×Country clustering accounts for:
- Correlation within industries across countries
- Correlation within countries across industries
- Essential for cross-country industry analysis

Please define the Country variable and try again.
"""
                return error_msg, "", "", None, None, {}
            else:
                error_msg = """❌ **Clustering Method Error: Country Variable Required**

The selected clustering method requires a **Country** variable, but none is defined.

**To fix this:**
1. Go to **Step 2: Select Variables**
2. In the **Time-invariant Variables (Optional)** section
3. Select your country column in the **Country Column** dropdown

**Why this matters:**
Country-level clustering accounts for correlation within countries, which is essential when:
- Treatment or policies vary by country
- Country-level shocks affect multiple firms
- You want standard errors robust to country-level clustering

Please define the Country variable and try again.
"""
                return error_msg, "", "", None, None, {}
        
        if "Two-way (Industry × Country)" in cluster_method:
            # Check if both industry and country are defined
            missing_vars = []
            if not industry_var or industry_var == "None":
                missing_vars.append("Industry")
            if not country_var or country_var == "None":
                missing_vars.append("Country")
            
            if missing_vars:
                vars_list = " and ".join(missing_vars)
                error_msg = f"""❌ **Clustering Method Error: Missing Required Variables**

The selected clustering method **Two-way (Industry × Country)** requires both Industry and Country variables.

**Missing variable(s):** {vars_list}

**To fix this:**
1. Go to **Step 2: Select Variables**
2. In the **Time-invariant Variables (Optional)** section
3. Define the missing variable(s):
   - **Industry/Sector Column** dropdown
   - **Country Column** dropdown

**Why this matters:**
Two-way Industry×Country clustering accounts for correlation both within industries (across countries) and within countries (across industries).

Please define both variables and try again.
"""
                return error_msg, "", "", None, None, {}
        
        # Validate firm and year columns exist (should always be defined, but check anyway)
        if not firm_id_col or not year_col:
            error_msg = """❌ **Data Configuration Error: Missing Core Panel Variables**

Panel data analysis requires both **Firm ID** and **Year** columns to be defined.

**To fix this:**
1. Go to **Step 2: Select Variables**
2. Ensure both are selected:
   - **Firm/Entity ID Column**
   - **Year/Time Column**

Please define these core variables and try again.
"""
            return error_msg, "", "", None, None, {}
        
        # Set up clustering based on method chosen
        # Default: One-way firm clustering with CRV1
        if cluster_method == "One-way (Firm only) with CRV1":
            # Traditional firm clustering
            vcov = {'CRV1': firm_id_col}
        elif cluster_method == "One-way (Firm only) with CRV3":
            # Traditional firm clustering with small-cluster correction
            vcov = {'CRV3': firm_id_col}
        elif cluster_method == "One-way (Industry) with CRV1":
            # Industry-level clustering (already validated)
            vcov = {'CRV1': industry_var}
        elif cluster_method == "One-way (Industry) with CRV3":
            # Industry-level clustering with small-cluster correction (already validated)
            vcov = {'CRV3': industry_var}
        elif cluster_method == "One-way (Country) with CRV1":
            # Country-level clustering without correction (already validated)
            vcov = {'CRV1': country_var}
        elif cluster_method == "One-way (Country) with CRV3":
            # Country-level clustering with correction (already validated)
            vcov = {'CRV3': country_var}
        elif cluster_method == "Two-way (Firm × Year) with CRV1":
            # Multi-way clustering without correction (faster)
            vcov = {'CRV1': f"{firm_id_col} + {year_col}"}
        elif cluster_method == "Two-way (Firm × Year) with CRV3":
            # Multi-way clustering with small-cluster correction
            vcov = {'CRV3': f"{firm_id_col} + {year_col}"}
        elif cluster_method == "Two-way (Industry × Country) with CRV1":
            # Industry × Country two-way clustering (already validated)
            vcov = {'CRV1': f"{industry_var} + {country_var}"}
        elif cluster_method == "Two-way (Industry × Country) with CRV3":
            # Industry × Country two-way clustering with small-cluster correction (already validated)
            vcov = {'CRV3': f"{industry_var} + {country_var}"}
        elif cluster_method == "Robust (Heteroskedasticity only)":
            # Robust SE without clustering
            vcov = 'hetero'
        else:
            # Should not reach here due to validation above
            vcov = {'CRV1': firm_id_col}
        
        # Estimate model with pyfixest (using Rust backend for faster computation)
        results = pf.feols(formula, data=df_clean, vcov=vcov, demeaner_backend="rust")
        
        # Run wild cluster bootstrap for small clusters
        # Support multi-variable bootstrap if bootstrap_variables provided
        bootstrap_results = None
        multi_bootstrap_results = {}
        
        if use_wild_bootstrap:
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
            
            # Ensure independent variable is always included if not already
            if independent_var not in vars_to_bootstrap:
                vars_to_bootstrap.insert(0, independent_var)
            
            if len(vars_to_bootstrap) > 0:
                # Multi-variable bootstrap - use function from bootstrap_ui_module
                multi_bootstrap_results = run_bootstrap_for_selected_variables(
                    results, df_clean, firm_id_col, year_col, cluster_method,
                    country_var, industry_var, vars_to_bootstrap, bootstrap_reps
                )
            else:
                # Single variable bootstrap (original behavior - fallback)
                bootstrap_results = run_wild_bootstrap_if_needed(
                    results, df_clean, firm_id_col, year_col, cluster_method, 
                    country_var, industry_var, independent_var, bootstrap_reps
                )
        
        # Format results
        # Pass both bootstrap results separately (function handles both types)
        results_summary = format_fe_results_pyfixest(results, dependent_var, independent_var, 
                                           include_year_fe, moderator_var, include_interaction,
                                           df_clean, firm_id_col, year_col, cluster_method, country_var,
                                           bootstrap_results, multi_bootstrap_results)
        
        # Diagnostics
        diagnostics = format_diagnostics_pyfixest(results, df_clean, firm_id_col, year_col, cluster_method, country_var, multi_bootstrap_results)
        
        # Code snippet
        code = generate_code_snippet_pyfixest(firm_id_col, year_col, dependent_var, independent_var,
                                     control_vars, include_year_fe, moderator_var, include_interaction, cluster_method, bootstrap_variables)
        
        # Return results object and bootstrap results for publication report
        return results_summary, diagnostics, code, results, df_clean, multi_bootstrap_results
    
    except Exception as e:
        error_msg = f"❌ Error in Fixed Effects estimation:\n\n{str(e)}\n\n{traceback.format_exc()}"
        return error_msg, "", "", None, None, {}


def format_fe_results_pyfixest(results, dependent_var, independent_var, include_year_fe, 
                     moderator_var, include_interaction, df_clean, firm_id_col, year_col,
                     cluster_method="Two-way (Firm × Year) with CRV3", country_var=None,
                     bootstrap_results: Optional[Dict] = None,
                     multi_bootstrap_results: Optional[Dict] = None):
    """Format Fixed Effects results using pyfixest's native .summary() method
    
    EXPERIMENT 1: Uses pyfixest's built-in summary for cleaner output
    FEATURE: includes wild cluster bootstrap results for small clusters
    Supports both single-variable and multi-variable bootstrap
    """
    
    n_firms = df_clean[firm_id_col].nunique()
    n_years = df_clean[year_col].nunique()
    n_obs = len(df_clean)
    
    # Get coefficient summary using pyfixest tidy()
    coef_df = results.tidy()
    
    # The tidy() output has coefficient names as the index
    # Reset index to make it a column (name will be determined by the index name)
    if coef_df.index.name:
        coef_df = coef_df.reset_index()
        coef_name_col = coef_df.columns[0]  # First column after reset_index
    else:
        coef_df = coef_df.reset_index()
        coef_name_col = 'index'  # Default name when index has no name
    
    # USE PYFIXEST's NATIVE SUMMARY - Much cleaner!
    # Capture stdout since summary() prints rather than returns
    buffer = StringIO()
    sys.stdout = buffer
    results.summary()
    sys.stdout = sys.__stdout__
    pyfixest_summary = buffer.getvalue()
    
    # Add bootstrap section if available
    bootstrap_section = ""
    
    # Check for multi-variable bootstrap first (takes precedence)
    if multi_bootstrap_results and len(multi_bootstrap_results) > 0:
        bootstrap_section = format_multi_variable_bootstrap_results(
            multi_bootstrap_results, coef_df, coef_name_col
        )
    elif bootstrap_results:
        # Single-variable bootstrap
        boot_res = bootstrap_results["results"]
        n_clusters = bootstrap_results["n_clusters"]
        cluster_var = bootstrap_results["cluster_var"]
        boot_reps = bootstrap_results["bootstrap_reps"]
        
        bootstrap_section = f"""
╔══════════════════════════════════════════════╗
║        WILD CLUSTER BOOTSTRAP INFERENCE      ║
╚══════════════════════════════════════════════╝

⚠️  Small Cluster Detection: {n_clusters} clusters in '{cluster_var}'
    → Wild cluster bootstrap recommended for G < 30 (Cameron et al., 2008)

Bootstrap Results for {independent_var}:
  • Bootstrap replications: {boot_reps:,}
  • Bootstrap t-statistic: {boot_res['t value']:.4f}
  • Bootstrap p-value: {boot_res['Pr(>|t|)']:.4f}
  • Asymptotic p-value: {coef_df[coef_df[coef_name_col] == independent_var]['Pr(>|t|)'].values[0]:.4f}
  
  • Bootstrap type: {boot_res['bootstrap_type']} (restricted)
  • Weights: Webb (2014) - optimal for small G
  • Inference: {boot_res['inference']}
  • Null imposed: {boot_res['impose_null']}

📊 Interpretation:
  • Bootstrap p-value is more reliable with few clusters
  • Asymptotic inference may be liberal (too many rejections)
  • Webb weights provide better finite-sample properties
  
"""
    
    output = f"""
╔═════════════════════════════════════════════════════╗
║          FIXED EFFECTS REGRESSION RESULTS           ║
║         (pyfixest native output - Experiment 1)     ║
╚═════════════════════════════════════════════════════╝

Model: Panel data fixed effects
Dependent Variable: {dependent_var}
Key Independent Variable: {independent_var}
{'Year Fixed Effects: ✓ Included' if include_year_fe else 'Year Fixed Effects: ✗ Not Included'}
Clustering Method: {cluster_method}

{pyfixest_summary}

Panel Structure:
  • Observations: {n_obs:,}
  • Firms: {n_firms:,}
  • Time periods: {n_years}
  • Avg obs per firm: {n_obs/n_firms:.1f}

───────────────────────────────────────────────────────────────
📊 INTERPRETATION:
"""
    
    # Add interpretation
    # Use the coefficient name column that was determined earlier
    main_row = coef_df[coef_df[coef_name_col] == independent_var]
    if not main_row.empty:
        main_coef = main_row['Estimate'].values[0]
        main_pval = main_row['Pr(>|t|)'].values[0]
        
        # Use bootstrap p-value if available
        if bootstrap_results:
            main_pval = bootstrap_results["results"]['Pr(>|t|)']
            output += "  (Using BOOTSTRAP p-value for inference)\n"
        
        if main_pval < 0.05:
            direction = "increase" if main_coef > 0 else "decrease"
            output += f"• A 1-unit increase in {independent_var} is associated with a {abs(main_coef):.4f}\n"
            output += f"  {direction} in {dependent_var} (statistically significant, p={main_pval:.4f})\n"
        else:
            output += f"• No statistically significant relationship detected between {independent_var}\n"
            output += f"  and {dependent_var} (p={main_pval:.4f})\n"
    
    if moderator_var and moderator_var != "None" and include_interaction:
        interaction_var = f'{independent_var}_x_{moderator_var}'
        int_row = coef_df[coef_df[coef_name_col] == interaction_var]
        if not int_row.empty:
            int_pval = int_row['Pr(>|t|)'].values[0]
            if int_pval < 0.05:
                output += f"• The effect is moderated by {moderator_var} (interaction significant, p={int_pval:.4f})\n"
            else:
                output += f"• No significant moderating effect of {moderator_var} detected (p={int_pval:.4f})\n"
    
    output += "• Results control for all time-invariant firm characteristics\n"
    if include_year_fe:
        output += "• Common time shocks are controlled via year fixed effects\n"
    
    # Add bootstrap section after interpretation
    output += f"\n{bootstrap_section}"
    
    return output


def format_diagnostics_pyfixest(results, df_clean, firm_id_col, year_col, cluster_method="Two-way (Firm × Year) with CRV3", country_var=None, multi_bootstrap_results=None):
    """Generate diagnostic information for pyfixest results
    
    EXPERIMENTAL: Enhanced with wild bootstrap recommendations and multi-variable support
    """
    
    n_firms = df_clean[firm_id_col].nunique()
    n_years = df_clean[year_col].nunique()
    n_obs = len(df_clean)
    
    # Check balance
    firm_counts = df_clean.groupby(firm_id_col).size()
    is_balanced = firm_counts.std() == 0
    
    # Determine number of clusters and assess adequacy
    is_two_way = "Two-way" in cluster_method
    uses_crv3 = "CRV3" in cluster_method
    
    if is_two_way:
        n_clusters_firm = n_firms
        n_clusters_year = n_years
        min_clusters = min(n_clusters_firm, n_clusters_year)
        cluster_description = f"{n_clusters_firm} firms × {n_clusters_year} years"
    elif "Country" in cluster_method and country_var and country_var != "None":
        n_clusters = df_clean[country_var].nunique()
        min_clusters = n_clusters
        cluster_description = f"{n_clusters} countries"
    else:
        n_clusters = n_firms
        min_clusters = n_clusters
        cluster_description = f"{n_clusters} firms"
    
    # Format panel balance info
    balance_status = '✓' if is_balanced else '⚠️'
    balance_text = 'balanced' if is_balanced else 'unbalanced'
    if is_balanced:
        balance_detail = '  All firms observed for all time periods'
    else:
        balance_detail = f'  Obs per firm: min={firm_counts.min()}, max={firm_counts.max()}, mean={firm_counts.mean():.1f}'
    
    # Format clustering info and assess adequacy
    if "Robust" in cluster_method:
        cluster_text = '✓ Robust standard errors (heteroskedasticity only)'
        cluster_count_text = ""
        cluster_adequacy = "⚠️ No clustering - assumes independence across all observations"
        bootstrap_rec = ""
    else:
        cluster_text = f'✓ {cluster_method}'
        cluster_count_text = f'   Clusters: {cluster_description}'
        
        # EXPERIMENTAL: Enhanced cluster adequacy with bootstrap recommendations
        # Based on Cameron, Gelbach & Miller (2008) and MacKinnon et al. (2023)
        if min_clusters >= 50:
            cluster_adequacy = f"✓ {min_clusters} clusters is adequate for asymptotic inference"
            bootstrap_rec = ""
        elif min_clusters >= 30:
            if uses_crv3:
                cluster_adequacy = f"✓ {min_clusters} clusters with CRV3 correction is acceptable"
                bootstrap_rec = ""
            else:
                cluster_adequacy = f"⚠️ {min_clusters} clusters - CRV3 correction recommended"
                bootstrap_rec = ""
        elif min_clusters >= 20:
            if uses_crv3:
                cluster_adequacy = f"⚠️ {min_clusters} clusters is limited; CRV3 helps but inference still uncertain"
                bootstrap_rec = "  💡 RECOMMENDATION: Consider wild cluster bootstrap (enabled automatically)"
            else:
                cluster_adequacy = f"❌ {min_clusters} clusters too few - MUST use CRV3 or wild bootstrap"
                bootstrap_rec = "  💡 RECOMMENDATION: Wild cluster bootstrap enabled automatically for better inference"
        else:
            cluster_adequacy = f"❌ {min_clusters} clusters critically low"
            bootstrap_rec = """  
  🚨 CRITICAL: Wild cluster bootstrap is ESSENTIAL with < 20 clusters
     → Bootstrap automatically enabled in experimental version
     → Using Webb (2014) weights optimal for small G
     → See MacKinnon, Nielsen & Webb (2023) for methodology
"""
    
    # Add multi-variable bootstrap summary if available
    multi_bootstrap_summary = ""
    if multi_bootstrap_results:
        multi_bootstrap_summary = format_multi_variable_bootstrap_diagnostics(multi_bootstrap_results)
    
    output = f"""
╔═══════════════════════════════════════════════════╗
║                  DIAGNOSTIC TESTS                 ║
╚═══════════════════════════════════════════════════╝

Panel Structure:
  {balance_status} Panel is {balance_text}
{balance_detail}

Clustering Specification:
  {cluster_text}
{'  ' + cluster_count_text if cluster_count_text else ''}
  {cluster_adequacy}
{bootstrap_rec}

{multi_bootstrap_summary}

🎯 Why This Matters:
  • Multi-way clustering accounts for correlation within firms AND years
  • One-way (firm) clustering ignores correlation from macro/time shocks
  • CRV3 correction adjusts for small-cluster bias (more conservative)
  • Rule of thumb: Use CRV3 when clusters < 50 in any dimension
  • EXPERIMENTAL: Wild bootstrap recommended for G < 30 (automatic)

🧪 EXPERIMENTAL FEATURES:
  • Wild cluster bootstrap inference for small clusters (G < 30)
  • Webb (2014) weights for better finite-sample properties  
  • Automatic detection and application when needed
  • Bootstrap p-values reported alongside asymptotic inference
  • NEW: WCR31 for two-way clustering (preserves correlation structure)

Model Diagnostics:
  • Number of observations: {n_obs}
  • Degrees of freedom: {results._N - results._k if hasattr(results, '_N') and hasattr(results, '_k') else 'N/A'}

⚠️ Important Notes:
  • Industry and country effects are absorbed into firm fixed effects
  • Cannot separately estimate time-invariant variables in this model
  • pyfixest provides efficient estimation for high-dimensional fixed effects
  • Use Two-Step method to explore between-firm differences
  
📚 References for Wild Bootstrap:
  • Cameron, Gelbach & Miller (2008) "Bootstrap-Based Improvements"
  • MacKinnon, Nielsen & Webb (2023) "Fast and Reliable Bootstrap"
  • Webb (2014) "Reworking Wild Bootstrap"
  • MacKinnon & Webb (2017) "Wild Bootstrap for Few Clusters"
  
📖 About WCR31 (Two-Way Clustering):
  • When two-way clustering is detected with G < 30 in either dimension
  • Bootstrap type "31" accounts for clustering in BOTH dimensions
  • Bootstraps on the dimension with FEWER clusters (weaker dimension)
  • Preserves correlation structure in the dimension with MORE clusters
  • More reliable inference than asymptotic CRV3 with small clusters
  • Example: If Firm (G=100) × Year (G=11), bootstrap on Year to preserve Firm correlation
"""
    
    return output


def generate_code_snippet_pyfixest(firm_id_col, year_col, dependent_var, independent_var,
                         control_vars, include_year_fe, moderator_var, include_interaction, cluster_method, bootstrap_variables=None):
    """Generate reproducible Python code using pyfixest
    
    EXPERIMENTAL: Includes wild cluster bootstrap code for small clusters
    Supports multi-variable bootstrap when bootstrap_variables provided
    """
    
    controls_str = ' + '.join(control_vars) if control_vars else ''
    
    interaction_code = ""
    if moderator_var and moderator_var != "None" and include_interaction:
        interaction_code = f"""
# Create interaction term
df['{independent_var}_x_{moderator_var}'] = df['{independent_var}'] * df['{moderator_var}']
"""
    
    # Build formula
    exog_list = [independent_var] + (control_vars if control_vars else [])
    if moderator_var and moderator_var != "None" and include_interaction:
        exog_list.append(f'{independent_var}_x_{moderator_var}')
    
    formula_rhs = ' + '.join(exog_list)
    
    if include_year_fe:
        fixed_effects = f"{firm_id_col} + {year_col}"
    else:
        fixed_effects = f"{firm_id_col}"
    
    formula = f"{dependent_var} ~ {formula_rhs} | {fixed_effects}"
    
    # Clustering setup - match selected method
    cluster_var_2 = None
    is_two_way_bootstrap = False
    
    if "Two-way" in cluster_method and "CRV3" in cluster_method:
        vcov_code = f"vcov = {{'CRV3': '{firm_id_col} + {year_col}'}}  # Multi-way with small-cluster correction"
        cluster_var = firm_id_col
        cluster_var_2 = year_col
        is_two_way_bootstrap = True
    elif "Two-way" in cluster_method and "CRV1" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': '{firm_id_col} + {year_col}'}}  # Multi-way clustering"
        cluster_var = firm_id_col
        cluster_var_2 = year_col
        is_two_way_bootstrap = True
    elif "Firm only" in cluster_method and "CRV3" in cluster_method:
        vcov_code = f"vcov = {{'CRV3': '{firm_id_col}'}}  # One-way with correction"
        cluster_var = firm_id_col
    elif "Firm only" in cluster_method and "CRV1" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': '{firm_id_col}'}}  # Traditional firm clustering"
        cluster_var = firm_id_col
    elif "Country" in cluster_method and "CRV3" in cluster_method:
        vcov_code = f"vcov = {{'CRV3': 'country_var'}}  # Country-level with correction"
        cluster_var = 'country_var'
    elif "Country" in cluster_method and "CRV1" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': 'country_var'}}  # Country-level clustering"
        cluster_var = 'country_var'
    else:
        vcov_code = "vcov = 'hetero'  # Robust SE only"
        cluster_var = None
    
    # Add bootstrap code if clustering is used
    bootstrap_code = ""
    if cluster_var:
        # Check if multi-variable bootstrap requested
        if bootstrap_variables and len(bootstrap_variables) > 0:
            bootstrap_code = generate_multi_variable_bootstrap_code(
                cluster_var, bootstrap_variables, is_two_way_bootstrap, cluster_var_2
            )
        else:
            # Single variable bootstrap (original)
            bootstrap_code = f"""

# Wild cluster bootstrap for small clusters (G < 30)
# Check number of clusters
n_clusters = df['{cluster_var}'].nunique()
print(f"Number of clusters: {{n_clusters}}")

if n_clusters < 30:
    print("⚠️  Running wild cluster bootstrap (recommended for few clusters)...")
    
    # Run wild cluster bootstrap with Webb weights
    boot_result = results.wildboottest(
        param='{independent_var}',  # Parameter to test
        reps=9999,                  # Bootstrap replications
        cluster='{cluster_var}',    # Cluster variable
        weights_type='webb',        # Webb (2014) weights - best for small G
        impose_null=True,           # Impose null hypothesis
        bootstrap_type='11',        # Standard restricted bootstrap
        seed=12345,                 # For reproducibility
        k_adj=True,                 # Small sample adjustment for k
        G_adj=True                  # Small sample adjustment for G
    )
    
    print("\\nWild Bootstrap Results:")
    print(boot_result)
    print(f"\\nBootstrap p-value: {{boot_result['Pr(>|t|)']:.4f}}")
    print(f"Asymptotic p-value: {{results.tidy().loc['{independent_var}', 'Pr(>|t|)']:.4f}}")
    print("\\n→ Use bootstrap p-value for inference with few clusters")
"""
    
    code = f"""
# Reproducible Panel Data Analysis with pyfixest (EXPERIMENTAL)
# Fixed Effects Model with Wild Cluster Bootstrap Support

import pandas as pd
import pyfixest as pf

# Load data
df = pd.read_csv('your_data.csv')

# Drop missing values
df = df[['{firm_id_col}', '{year_col}', '{dependent_var}', '{independent_var}'{", " + ", ".join([f"'{c}'" for c in control_vars]) if control_vars else ""}]].dropna()
{interaction_code}
# Build formula
formula = "{formula}"

# Estimate Fixed Effects model (using Rust backend for faster computation)
results = pf.feols(formula, data=df, {vcov_code}, demeaner_backend="rust")

# Display results
print(results.summary())

# Get coefficient table
print(results.tidy())
{bootstrap_code}

# References:
# - Cameron, Gelbach & Miller (2008) "Bootstrap-Based Improvements for Inference"
# - MacKinnon, Nielsen & Webb (2023) "Fast and Reliable Bootstrap Methods"
# - Webb (2014) "Reworking Wild Bootstrap Based Inference"
"""
    
    return code


def run_pooled_ols_model(
    df: pd.DataFrame,
    firm_id_col: str,
    year_col: str,
    dependent_var: str,
    independent_var: str,
    control_vars: List[str],
    include_year_fe: bool,
    moderator_var: Optional[str],
    include_interaction: bool,
    industry_var: Optional[str],
    country_var: Optional[str],
    cluster_method: str = "Two-way (Firm × Year) with CRV3",
    include_lag_dv: bool = False,
    lag_min: Optional[int] = None,
    lag_max: Optional[int] = None
) -> Tuple[str, str, str]:
    """
    Pooled OLS with Industry/Country Dummies using pyfixest
    """
    try:
        # Prepare data
        df_clean = df[[firm_id_col, year_col, dependent_var, independent_var] + control_vars].copy()
        df_clean = df_clean.sort_values([firm_id_col, year_col])
        
        # Add industry/country
        if industry_var and industry_var != "None":
            df_clean[industry_var] = df[industry_var]
        if country_var and country_var != "None":
            df_clean[country_var] = df[country_var]
        
        # Add moderator if specified
        if moderator_var and moderator_var != "None" and include_interaction:
            df_clean[moderator_var] = df[moderator_var]
            df_clean[f'{independent_var}_x_{moderator_var}'] = df[independent_var] * df[moderator_var]
        
        # Create lagged dependent variables if requested
        lag_vars = []
        if include_lag_dv and lag_min is not None and lag_max is not None:
            for lag in range(lag_min, lag_max + 1):
                lag_var_name = f'{dependent_var}_lag{lag}'
                df_clean[lag_var_name] = df_clean.groupby(firm_id_col)[dependent_var].shift(lag)
                lag_vars.append(lag_var_name)
        
        df_clean = df_clean.dropna()
        
        # Build formula
        exog_vars = [independent_var] + control_vars
        if moderator_var and moderator_var != "None" and include_interaction:
            exog_vars.append(f'{independent_var}_x_{moderator_var}')
        if lag_vars:
            exog_vars.extend(lag_vars)
        
        formula_rhs = ' + '.join(exog_vars)
        
        # Add fixed effects for year, industry, country
        fe_list = []
        if include_year_fe:
            fe_list.append(year_col)
        if industry_var and industry_var != "None":
            fe_list.append(industry_var)
        if country_var and country_var != "None":
            fe_list.append(country_var)
        
        if fe_list:
            formula = f"{dependent_var} ~ {formula_rhs} | {' + '.join(fe_list)}"
        else:
            formula = f"{dependent_var} ~ {formula_rhs}"
        
        # Validate clustering method against available variables
        if "Industry" in cluster_method and (not industry_var or industry_var == "None"):
            error_msg = """❌ **Clustering Method Error: Industry Variable Required**

The selected clustering method requires an **Industry** variable, but none is defined.

**To fix this:**
1. Go to **Step 2: Select Variables**
2. In the **Time-invariant Variables (Optional)** section
3. Select your industry column in the **Industry/Sector Column** dropdown

Please define the Industry variable and try again.
"""
            return error_msg, "", ""
        
        if "Country" in cluster_method and (not country_var or country_var == "None"):
            if "Industry × Country" in cluster_method:
                error_msg = """❌ **Clustering Method Error: Country Variable Required**

The selected clustering method **Two-way (Industry × Country)** requires both Industry and Country variables.

**To fix this:**
1. Go to **Step 2: Select Variables**
2. In the **Time-invariant Variables (Optional)** section
3. Select your country column in the **Country Column** dropdown

Please define the Country variable and try again.
"""
            else:
                error_msg = """❌ **Clustering Method Error: Country Variable Required**

The selected clustering method requires a **Country** variable, but none is defined.

**To fix this:**
1. Go to **Step 2: Select Variables**
2. In the **Time-invariant Variables (Optional)** section
3. Select your country column in the **Country Column** dropdown

Please define the Country variable and try again.
"""
            return error_msg, "", ""
        
        if "Two-way (Industry × Country)" in cluster_method:
            missing_vars = []
            if not industry_var or industry_var == "None":
                missing_vars.append("Industry")
            if not country_var or country_var == "None":
                missing_vars.append("Country")
            
            if missing_vars:
                vars_list = " and ".join(missing_vars)
                error_msg = f"""❌ **Clustering Method Error: Missing Required Variables**

The selected clustering method **Two-way (Industry × Country)** requires both Industry and Country variables.

**Missing variable(s):** {vars_list}

**To fix this:**
1. Go to **Step 2: Select Variables**
2. In the **Time-invariant Variables (Optional)** section
3. Define the missing variable(s):
   - **Industry/Sector Column** dropdown
   - **Country Column** dropdown

Please define both variables and try again.
"""
                return error_msg, "", ""
        
        # Set up clustering (same logic as FE model)
        if cluster_method == "One-way (Firm only) with CRV1":
            vcov = {'CRV1': firm_id_col}
        elif cluster_method == "One-way (Firm only) with CRV3":
            vcov = {'CRV3': firm_id_col}
        elif cluster_method == "One-way (Industry) with CRV1":
            vcov = {'CRV1': industry_var}
        elif cluster_method == "One-way (Industry) with CRV3":
            vcov = {'CRV3': industry_var}
        elif cluster_method == "One-way (Country) with CRV1":
            vcov = {'CRV1': country_var}
        elif cluster_method == "One-way (Country) with CRV3":
            vcov = {'CRV3': country_var}
        elif cluster_method == "Two-way (Firm × Year) with CRV1":
            vcov = {'CRV1': f"{firm_id_col} + {year_col}"}
        elif cluster_method == "Two-way (Firm × Year) with CRV3":
            vcov = {'CRV3': f"{firm_id_col} + {year_col}"}
        elif cluster_method == "Two-way (Industry × Country) with CRV1":
            vcov = {'CRV1': f"{industry_var} + {country_var}"}
        elif cluster_method == "Two-way (Industry × Country) with CRV3":
            vcov = {'CRV3': f"{industry_var} + {country_var}"}
        elif cluster_method == "Robust (Heteroskedasticity only)":
            vcov = 'hetero'
        else:
            vcov = {'CRV1': firm_id_col}
        
        # Estimate Pooled OLS (using Rust backend for faster computation)
        results = pf.feols(formula, data=df_clean, vcov=vcov, demeaner_backend="rust")
        
        # Format results
        results_summary = format_pooled_results_pyfixest(
            results, dependent_var, independent_var, include_year_fe,
            moderator_var, include_interaction, df_clean, industry_var, country_var
        )
        
        diagnostics = format_pooled_diagnostics_pyfixest(results, df_clean, firm_id_col)
        
        code = generate_pooled_code_pyfixest(firm_id_col, year_col, dependent_var, independent_var,
                                   control_vars, include_year_fe, moderator_var, include_interaction,
                                   industry_var, country_var, cluster_method)
        
        return results_summary, diagnostics, code, results, df_clean, {}
    
    except Exception as e:
        error_msg = f"❌ Error in Pooled OLS estimation:\n\n{str(e)}\n\n{traceback.format_exc()}"
        return error_msg, "", "", None, None, {}


def format_pooled_results_pyfixest(results, dependent_var, independent_var, include_year_fe,
                         moderator_var, include_interaction, df_clean, industry_var, country_var):
    """Format Pooled OLS results using pyfixest's native .summary() method
    
    EXPERIMENT 1: Uses pyfixest's built-in summary for cleaner output
    """
    
    n_obs = len(df_clean)
    
    # Get coefficient summary using pyfixest tidy()
    coef_df = results.tidy()
    
    # USE PYFIXEST's NATIVE SUMMARY - Much cleaner!
    # Capture stdout since summary() prints rather than returns
    buffer = StringIO()
    sys.stdout = buffer
    results.summary()
    sys.stdout = sys.__stdout__
    pyfixest_summary = buffer.getvalue()
    
    output = f"""
╔════════════════════════════════════════════════╗
║         POOLED OLS REGRESSION RESULTS          ║
║        (pyfixest native output - Exp 1)        ║
╚════════════════════════════════════════════════╝

Model: Pooled OLS with Dummy Variables
Dependent Variable: {dependent_var}
Key Independent Variable: {independent_var}
{'Year Fixed Effects: ✓ Included' if include_year_fe else 'Year Fixed Effects: ✗ Not Included'}
{'Industry Dummies: ✓ Included' if industry_var and industry_var != "None" else ''}
{'Country Dummies: ✓ Included' if country_var and country_var != "None" else ''}

{pyfixest_summary}

Model Fit:
  • Observations: {n_obs:,}

─────────────────────────────────────────────────────────────────
📊 INTERPRETATION:
• Pooled OLS treats all observations independently
• Can estimate industry and country dummy coefficients
• Does NOT control for unobserved firm-specific effects

⚠️ CRITICAL WARNINGS:
• This model assumes NO unobserved firm heterogeneity
• If firms have unobserved traits correlated with X, estimates are BIASED
• Pooled OLS typically produces inconsistent estimates in panel data
• Use ONLY if you believe no omitted firm-level variables exist
• Strongly recommend Fixed Effects instead
"""
    
    return output


def format_pooled_diagnostics_pyfixest(results, df_clean, firm_id_col):
    """Diagnostics for Pooled OLS from pyfixest"""
    
    n_obs = len(df_clean)
    
    output = f"""
╔══════════════════════════════════════════════════════════════════╗
║                     DIAGNOSTIC TESTS                             ║
╚══════════════════════════════════════════════════════════════════╝

Model Specification:
  ⚠️ Pooled OLS ignores panel structure
  ⚠️ Assumes no firm-specific unobserved effects
  ⚠️ Standard errors may be underestimated

Model Diagnostics:
  • Number of observations: {n_obs}
  • Degrees of freedom: {results._N - results._k if hasattr(results, '_N') and hasattr(results, '_k') else 'N/A'}

⚠️ RECOMMENDATION:
  1. Compare with Fixed Effects model
  2. If panel structure is important, DO NOT use Pooled OLS results
  3. Use only for preliminary analysis or when FE is not feasible
  4. pyfixest makes Fixed Effects estimation very efficient - prefer FE!
"""
    
    return output


def generate_pooled_code_pyfixest(firm_id_col, year_col, dependent_var, independent_var, control_vars,
                        include_year_fe, moderator_var, include_interaction, industry_var, country_var, cluster_method):
    """Generate code for Pooled OLS using pyfixest"""
    
    exog_vars = [independent_var] + (control_vars if control_vars else [])
    if moderator_var and moderator_var != "None" and include_interaction:
        exog_vars.append(f'{independent_var}_x_{moderator_var}')
    
    formula_rhs = ' + '.join(exog_vars)
    
    # Add fixed effects
    fe_list = []
    if include_year_fe:
        fe_list.append(year_col)
    if industry_var and industry_var != "None":
        fe_list.append(industry_var)
    if country_var and country_var != "None":
        fe_list.append(country_var)
    
    if fe_list:
        formula = f"{dependent_var} ~ {formula_rhs} | {' + '.join(fe_list)}"
    else:
        formula = f"{dependent_var} ~ {formula_rhs}"
    
    # Clustering setup - match selected method
    if "Two-way" in cluster_method and "CRV3" in cluster_method:
        vcov_code = f"vcov = {{'CRV3': '{firm_id_col} + {year_col}'}}  # Multi-way with correction"
    elif "Two-way" in cluster_method and "CRV1" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': '{firm_id_col} + {year_col}'}}  # Multi-way clustering"
    elif "Firm only" in cluster_method and "CRV3" in cluster_method:
        vcov_code = f"vcov = {{'CRV3': '{firm_id_col}'}}  # One-way with correction"
    elif "Firm only" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': '{firm_id_col}'}}  # Firm clustering"
    elif "Country" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': '{country_var}'}}  # Country clustering"
    else:
        vcov_code = "vcov = 'hetero'"
    
    code = f"""
# Pooled OLS with pyfixest
import pandas as pd
import pyfixest as pf

# Load data
df = pd.read_csv('your_data.csv')

# Prepare data
df = df.dropna()

# Estimate Pooled OLS (using Rust backend for faster computation)
formula = "{formula}"
results = pf.feols(formula, data=df, {vcov_code}, demeaner_backend="rust")

print(results.summary())

# IMPORTANT: Compare with Fixed Effects!
fe_formula = "{dependent_var} ~ {formula_rhs} | {firm_id_col}"
results_fe = pf.feols(fe_formula, data=df, vcov={{'CRV1': '{firm_id_col}'}}, demeaner_backend="rust")
print("\\nFixed Effects for comparison:")
print(results_fe.summary())
"""
    
    return code


def analyze_panel_data(
    file,
    firm_id_col,
    year_col,
    dependent_var,
    independent_var,
    control_vars,
    method,
    include_year_fe,
    cluster_method,
    moderator_var,
    include_interaction,
    industry_var,
    country_var,
    include_lag_dv,
    lag_min,
    lag_max,
    use_bootstrap,
    bootstrap_variables
):
    """
    Main analysis function that routes to appropriate estimation method
    Now also returns results, dataframe, and parameters for publication report
    """
    if file is None:
        return "⚠️ Please upload a CSV file", "", "", None, None, None
    
    if not all([firm_id_col, year_col, dependent_var, independent_var]):
        return "⚠️ Please specify all required variables (Firm ID, Year, Dependent, Independent)", "", "", None, None, None
    
    # Validate lag parameters
    if include_lag_dv:
        try:
            lag_min_int = int(lag_min)
            lag_max_int = int(lag_max)
            
            if lag_min_int < 1 or lag_max_int < 1:
                return "❌ Lag values must be at least 1", "", "", None, None, None
            
            if lag_min_int > lag_max_int:
                return "❌ Minimum lag cannot be greater than maximum lag", "", "", None, None, None
            
            if lag_max_int > 10:
                return "❌ Maximum lag is limited to 10 periods", "", "", None, None, None
        except (ValueError, TypeError):
            return "❌ Invalid lag values. Please enter valid integers.", "", "", None, None, None
    else:
        lag_min_int = None
        lag_max_int = None
    
    try:
        # Load data
        df, status = load_and_validate_data(file.name)
        if df is None:
            return status, "", "", None, None, None
        
        # Validate lag against data
        if include_lag_dv and lag_max_int is not None:
            time_periods = df.groupby(firm_id_col)[year_col].nunique()
            min_periods = time_periods.min()
            n_total_firms = len(time_periods)
            insufficient_firms = (time_periods <= lag_max_int).sum()
            sufficient_firms = n_total_firms - insufficient_firms
            pct_insufficient = (insufficient_firms / n_total_firms) * 100
            
            if sufficient_firms < 10:
                message = f"""❌ Data insufficient for lag analysis with max lag = {lag_max_int}

📊 Data Summary:
• Total firms: {n_total_firms:,}
• Firms with insufficient data: {insufficient_firms:,} ({pct_insufficient:.1f}%)
• Minimum periods per firm: {min_periods}
• Required periods: {lag_max_int + 1} periods per firm

💡 Suggestion: Reduce maximum lag to {max(0, min_periods - 1)}
"""
                return message, "", "", None, None, None
            
            elif pct_insufficient > 50:
                message = f"""❌ More than 50% of firms would be dropped!

💡 Reduce maximum lag to {max(0, min_periods - 1)}
"""
                return message, "", "", None, None, None
        
        # Store parameters for publication report
        params_dict = {
            'firm_id_col': firm_id_col,
            'year_col': year_col,
            'dependent_var': dependent_var,
            'independent_var': independent_var,
            'control_vars': control_vars,
            'method': method,
            'include_year_fe': include_year_fe,
            'cluster_method': cluster_method,
            'moderator_var': moderator_var,
            'include_interaction': include_interaction,
            'industry_var': industry_var,
            'country_var': country_var,
            'include_lag_dv': include_lag_dv,
            'lag_min': lag_min_int,
            'lag_max': lag_max_int
        }
        
        # Route to appropriate method
        if method == "Fixed Effects (Firm + Year)":
            results_text, diagnostics_text, code_text, results_obj, df_clean, bootstrap_results = run_fixed_effects_model(
                df, firm_id_col, year_col, dependent_var, independent_var,
                control_vars if control_vars else [], include_year_fe,
                moderator_var, include_interaction, cluster_method, country_var,
                industry_var, include_lag_dv, lag_min_int, lag_max_int,
                use_bootstrap, bootstrap_variables
            )
            # Store bootstrap results in params for publication report
            params_dict['bootstrap_results'] = bootstrap_results
            return results_text, diagnostics_text, code_text, results_obj, df_clean, params_dict
        
        elif method == "Pooled OLS (with Industry/Country Dummies)":
            results_text, diagnostics_text, code_text, results_obj, df_clean, bootstrap_results = run_pooled_ols_model(
                df, firm_id_col, year_col, dependent_var, independent_var,
                control_vars if control_vars else [], include_year_fe,
                moderator_var, include_interaction, industry_var, country_var,
                cluster_method, include_lag_dv, lag_min_int, lag_max_int
            )
            # Store bootstrap results (empty for pooled OLS)
            params_dict['bootstrap_results'] = bootstrap_results
            return results_text, diagnostics_text, code_text, results_obj, df_clean, params_dict
        
        else:
            return f"⚠️ Method '{method}' is not yet implemented with pyfixest. Currently available: Fixed Effects and Pooled OLS.", "", "", None, None, None
    
    except Exception as e:
        error_msg = f"❌ Unexpected error:\n\n{str(e)}\n\n{traceback.format_exc()}"
        return error_msg, "", "", None, None, None


# ═══════════════════════════════════════════════════════════════════════════
#                      PUBLICATION REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def generate_publication_report(
    stored_results,
    stored_df,
    stored_params
) -> str:
    """
    Generate publication-ready report with:
    - Publication-quality regression table (etable)
    - Descriptive statistics (dtable) with grouping by country/industry
    - Categorical variable summaries
    - Cross-tabulations (firms per industry/country)
    """
    if stored_results is None or stored_df is None or stored_params is None:
        return "❌ No analysis results available. Please run an analysis first."
    
    try:
        results = stored_results
        df_clean = stored_df
        params = stored_params
        
        # Extract parameters
        firm_id_col = params['firm_id_col']
        year_col = params['year_col']
        dependent_var = params['dependent_var']
        independent_var = params['independent_var']
        control_vars = params.get('control_vars', [])
        industry_var = params.get('industry_var')
        country_var = params.get('country_var')
        
        # 1. Publication-Ready Regression Table - custom formatting for academic papers
        # Build a clean table manually from regression results with minimal borders
        try:
            # Get model statistics
            coef_df = results.tidy().reset_index()
            n_obs = int(results._N) if hasattr(results, '_N') else len(df_clean)
            r2 = results._r2 if hasattr(results, '_r2') else 0
            r2_within = results._r2_within if hasattr(results, '_r2_within') else 0
            
            # Get vcov type for SE description
            vcov_type = params.get('cluster_method', 'Robust')
            
            # Build HTML table for precise border control (academic paper style)
            html_rows = []
            html_rows.append('<table style="border-collapse: collapse; border-top: 1px solid black; border-bottom: 1px solid black;">')
            
            # Header with border below
            html_rows.append(f'<tr style="border-bottom: 1px solid black;"><td style="padding: 4px 8px;"></td><td style="padding: 4px 8px; text-align: center;"><strong>{dependent_var}</strong></td></tr>')
            html_rows.append(f'<tr style="border-bottom: 1px solid black;"><td style="padding: 4px 8px;"></td><td style="padding: 4px 8px; text-align: center;">(1)</td></tr>')
            
            # Add coefficients (no borders between variables)
            for _, row in coef_df.iterrows():
                var_name = row.iloc[0] if len(row) > 0 else str(row.name)
                coef = row['Estimate']
                se = row['Std. Error']
                pval = row['Pr(>|t|)']
                
                # Significance stars
                stars = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else ''
                
                # Format: coefficient with stars, SE in parentheses below
                html_rows.append(f'<tr><td style="padding: 4px 8px;">{var_name}</td><td style="padding: 4px 8px; text-align: center;">{coef:.3f}{stars}</td></tr>')
                html_rows.append(f'<tr><td style="padding: 4px 8px;"></td><td style="padding: 4px 8px; text-align: center;">({se:.3f})</td></tr>')
            
            # Add fixed effects (combine into single row if multiple)
            if hasattr(results, '_fixef') and results._fixef:
                # _fixef is a string like "firm" or can be a list
                fe_str = results._fixef if isinstance(results._fixef, str) else ', '.join(results._fixef) if results._fixef else ''
                if fe_str:
                    html_rows.append(f'<tr><td style="padding: 4px 8px;">{fe_str.replace("_", " ").title()} FE</td><td style="padding: 4px 8px; text-align: center;">✓</td></tr>')
            
            # Model statistics section with border above
            html_rows.append(f'<tr style="border-top: 1px solid black;"><td style="padding: 4px 8px;">Observations</td><td style="padding: 4px 8px; text-align: center;">{n_obs:,}</td></tr>')
            html_rows.append(f'<tr><td style="padding: 4px 8px;">S.E. type</td><td style="padding: 4px 8px; text-align: center;">{vcov_type}</td></tr>')
            html_rows.append(f'<tr><td style="padding: 4px 8px;">R²</td><td style="padding: 4px 8px; text-align: center;">{r2:.3f}</td></tr>')
            if r2_within > 0:
                html_rows.append(f'<tr style="border-bottom: 1px solid black;"><td style="padding: 4px 8px;">R² Within</td><td style="padding: 4px 8px; text-align: center;">{r2_within:.3f}</td></tr>')
            else:
                # Add bottom border to R² if R² Within not present
                html_rows[-1] = html_rows[-1].replace('<tr>', '<tr style="border-bottom: 1px solid black;">')
            
            html_rows.append('</table>')
            html_rows.append('<p style="font-size: 0.9em; margin-top: 8px;"><em>Significance levels: * p < 0.05, ** p < 0.01, *** p < 0.001</em></p>')
            
            regression_table = '\n'.join(html_rows)
            
        except Exception as e:
            # Fallback to tidy() if custom table fails
            coef_table = results.tidy()
            regression_table = coef_table.to_markdown(index=False)
        
        # 1b. Bootstrap Results Table (if available)
        bootstrap_table = ""
        bootstrap_results = params.get('bootstrap_results', {})
        
        if bootstrap_results and any(v is not None for v in bootstrap_results.values()):
            try:
                coef_df = results.tidy().reset_index()
                
                # Get coefficient name column
                if coef_df.index.name:
                    coef_name_col = coef_df.columns[0]
                else:
                    coef_name_col = 'Coefficient' if 'Coefficient' in coef_df.columns else coef_df.columns[0]
                
                # Determine bootstrap method description
                first_valid = next((v for v in bootstrap_results.values() if v is not None), None)
                if first_valid:
                    is_two_way = first_valid.get('is_two_way', False)
                    bootstrap_type = first_valid.get('bootstrap_type', '11')
                    cluster_var = first_valid.get('cluster_var', 'cluster')
                    n_clusters = first_valid.get('n_clusters', 0)
                    boot_reps = first_valid.get('bootstrap_reps', 9999)
                    
                    if is_two_way:
                        other_cluster = first_valid.get('other_cluster', '')
                        n_clusters_other = first_valid.get('n_clusters_other', 0)
                        bootstrap_method = f"Wild Cluster Bootstrap (WCR31) - Bootstrapped on '{cluster_var}' (G={n_clusters}), Preserves '{other_cluster}' (G={n_clusters_other}) correlation, {boot_reps:,} reps"
                    else:
                        bootstrap_method = f"Wild Cluster Bootstrap - '{cluster_var}' (G={n_clusters}), Webb weights, {boot_reps:,} reps"
                    
                    # Build HTML table for bootstrap results
                    html_rows_boot = []
                    html_rows_boot.append('<table style="border-collapse: collapse; border-top: 1px solid black; border-bottom: 1px solid black;">')
                    
                    # Header with border below
                    html_rows_boot.append(f'<tr style="border-bottom: 1px solid black;"><td style="padding: 4px 8px;"></td><td style="padding: 4px 8px; text-align: center;"><strong>{dependent_var}</strong></td></tr>')
                    html_rows_boot.append(f'<tr style="border-bottom: 1px solid black;"><td style="padding: 4px 8px;"></td><td style="padding: 4px 8px; text-align: center;">(1)</td></tr>')
                    
                    # Add coefficients for bootstrapped variables only
                    for var_name, boot_res_dict in bootstrap_results.items():
                        if boot_res_dict is not None:
                            boot_res = boot_res_dict['results']
                            
                            # Get asymptotic values from main results
                            var_row = coef_df[coef_df[coef_name_col] == var_name]
                            if len(var_row) > 0:
                                coef = var_row['Estimate'].values[0]
                                se = var_row['Std. Error'].values[0]
                            else:
                                continue
                            
                            # Get bootstrap p-value
                            boot_pval = boot_res['Pr(>|t|)']
                            
                            # Significance stars based on BOOTSTRAP p-value
                            stars = '***' if boot_pval < 0.001 else '**' if boot_pval < 0.01 else '*' if boot_pval < 0.05 else ''
                            
                            # Format: coefficient with bootstrap-based stars, SE in parentheses below
                            html_rows_boot.append(f'<tr><td style="padding: 4px 8px;">{var_name}</td><td style="padding: 4px 8px; text-align: center;">{coef:.3f}{stars}</td></tr>')
                            html_rows_boot.append(f'<tr><td style="padding: 4px 8px;"></td><td style="padding: 4px 8px; text-align: center;">({se:.3f})</td></tr>')
                    
                    # Add fixed effects
                    if hasattr(results, '_fixef') and results._fixef:
                        fe_str = results._fixef if isinstance(results._fixef, str) else ', '.join(results._fixef) if results._fixef else ''
                        if fe_str:
                            html_rows_boot.append(f'<tr><td style="padding: 4px 8px;">{fe_str.replace("_", " ").title()} FE</td><td style="padding: 4px 8px; text-align: center;">✓</td></tr>')
                    
                    # Model statistics section with border above
                    n_obs = int(results._N) if hasattr(results, '_N') else len(df_clean)
                    r2 = results._r2 if hasattr(results, '_r2') else 0
                    r2_within = results._r2_within if hasattr(results, '_r2_within') else 0
                    
                    html_rows_boot.append(f'<tr style="border-top: 1px solid black;"><td style="padding: 4px 8px;">Observations</td><td style="padding: 4px 8px; text-align: center;">{n_obs:,}</td></tr>')
                    html_rows_boot.append(f'<tr><td style="padding: 4px 8px;">Bootstrap Method</td><td style="padding: 4px 8px; text-align: center; font-size: 0.85em;">{bootstrap_method}</td></tr>')
                    html_rows_boot.append(f'<tr><td style="padding: 4px 8px;">R²</td><td style="padding: 4px 8px; text-align: center;">{r2:.3f}</td></tr>')
                    if r2_within > 0:
                        html_rows_boot.append(f'<tr style="border-bottom: 1px solid black;"><td style="padding: 4px 8px;">R² Within</td><td style="padding: 4px 8px; text-align: center;">{r2_within:.3f}</td></tr>')
                    else:
                        html_rows_boot[-1] = html_rows_boot[-1].replace('<tr>', '<tr style="border-bottom: 1px solid black;">')
                    
                    html_rows_boot.append('</table>')
                    html_rows_boot.append('<p style="font-size: 0.9em; margin-top: 8px;"><em>Significance levels based on bootstrap p-values: * p < 0.05, ** p < 0.01, *** p < 0.001</em></p>')
                    html_rows_boot.append('<p style="font-size: 0.9em; margin-top: 4px;"><em>Note: This table shows only variables tested with wild cluster bootstrap inference.</em></p>')
                    
                    bootstrap_table = '\n'.join(html_rows_boot)
                    
            except Exception as e:
                bootstrap_table = f"<p><em>Note: Bootstrap results available but could not be formatted: {str(e)}</em></p>"
        
        # 2. Descriptive Statistics using dtable with advanced options
        # Collect all NUMERICAL variables used in the analysis
        vars_for_desc = [dependent_var, independent_var] + control_vars
        # Filter to only numerical variables that exist in df_clean
        vars_for_desc = [v for v in vars_for_desc if v in df_clean.columns and pd.api.types.is_numeric_dtype(df_clean[v])]
        
        # Build custom descriptive statistics table
        # Format: Variables in rows, statistics in columns
        desc_data = []
        
        for var in vars_for_desc:
            var_data = df_clean[var]
            desc_data.append({
                'Variable': var.replace('_', ' ').title(),
                'Count': f"{int(var_data.count()):,}",
                'Mean': f"{var_data.mean():.4f}",
                'Std Dev': f"{var_data.std():.4f}",
                'Min': f"{var_data.min():.4f}",
                'Max': f"{var_data.max():.4f}"
            })
        
        # Add country count row if country variable exists
        if country_var and country_var != "None" and country_var in df_clean.columns:
            n_countries = df_clean[country_var].nunique()
            desc_data.append({
                'Variable': f'Countries ({country_var})',
                'Count': f"{n_countries}",
                'Mean': '—',
                'Std Dev': '—',
                'Min': '—',
                'Max': '—'
            })
        
        # Add industry count row if industry variable exists
        if industry_var and industry_var != "None" and industry_var in df_clean.columns:
            n_industries = df_clean[industry_var].nunique()
            desc_data.append({
                'Variable': f'Industries ({industry_var})',
                'Count': f"{n_industries}",
                'Mean': '—',
                'Std Dev': '—',
                'Min': '—',
                'Max': '—'
            })
        
        # Convert to DataFrame and format as markdown
        desc_df = pd.DataFrame(desc_data)
        descriptive_stats = "**Descriptive statistics**\n\n" + desc_df.to_markdown(index=False)
        
        # 3. Categorical variable summaries
        categorical_summaries = ""
        
        # Panel structure summary
        n_firms = df_clean[firm_id_col].nunique()
        n_years = df_clean[year_col].nunique()
        n_obs = len(df_clean)
        
        categorical_summaries += f"""
### Panel structure summary

| Dimension | Count |
|-----------|-------|
| Total Observations | {n_obs:,} |
| Unique Firms | {n_firms:,} |
| Time Periods (Years) | {n_years} |
| Average Obs per Firm | {n_obs/n_firms:.2f} |

"""
        
        # 4. Country Summary (if applicable)
        if country_var and country_var != "None" and country_var in df_clean.columns:
            country_counts = df_clean[country_var].value_counts().reset_index()
            country_counts.columns = ['Country', 'Observations']
            categorical_summaries += f"""
### Country distribution

**Total Countries: {df_clean[country_var].nunique()}**

{country_counts.to_markdown(index=False)}

"""
        
        # 5. Industry Summary (if applicable)
        if industry_var and industry_var != "None" and industry_var in df_clean.columns:
            industry_counts = df_clean[industry_var].value_counts().reset_index()
            industry_counts.columns = ['Industry', 'Observations']
            categorical_summaries += f"""
### Industry distribution

**Total Industries: {df_clean[industry_var].nunique()}**

{industry_counts.to_markdown(index=False)}

"""
        
        # 6. Cross-tabulations
        cross_tabs = ""
        
        # Firms per Industry
        if industry_var and industry_var != "None" and industry_var in df_clean.columns:
            firms_per_industry = df_clean.groupby(industry_var)[firm_id_col].nunique().reset_index()
            firms_per_industry.columns = ['Industry', 'Number of Firms']
            firms_per_industry = firms_per_industry.sort_values('Number of Firms', ascending=False)
            cross_tabs += f"""
### Firms per Industry

{firms_per_industry.to_markdown(index=False)}

"""
        
        # Firms per Country
        if country_var and country_var != "None" and country_var in df_clean.columns:
            firms_per_country = df_clean.groupby(country_var)[firm_id_col].nunique().reset_index()
            firms_per_country.columns = ['Country', 'Number of Firms']
            firms_per_country = firms_per_country.sort_values('Number of Firms', ascending=False)
            cross_tabs += f"""
### Firms per Country

{firms_per_country.to_markdown(index=False)}

"""
        
        # 7. Year distribution
        year_counts = df_clean.groupby(year_col).size().reset_index()
        year_counts.columns = ['Year', 'Observations']
        year_summary = f"""
### Year distribution
{year_counts.to_markdown(index=False)}

"""
        
        # Compile full report
        bootstrap_section = ""
        if bootstrap_table:
            bootstrap_section = f"""
### Bootstrap results (wild cluster bootstrap inference)

{bootstrap_table}

---
"""
        
        report = f"""
# 📊 Comprehensive result

*Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*

---

## 1. Regression results

{regression_table}

{bootstrap_section}
---

## 2. Descriptive statistics

{descriptive_stats}

---

## 3. Categorical variables

{categorical_summaries}

{year_summary}

---

## 4. Cross-tabulations

{cross_tabs}

---

### Notes:
- This report is based on the most recent analysis run
- All statistics reflect the data after cleaning (dropped missing values)
- Regression table shows coefficients, standard errors, and significance levels
- Descriptive statistics include mean, standard deviation, min, max, and percentiles
"""
        
        return report
        
    except Exception as e:
        return f"❌ Error generating publication report: {str(e)}\n\nPlease ensure you have run an analysis first."


# ═══════════════════════════════════════════════════════════════════════════
#                            GRADIO INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

with gr.Blocks(title="Panel Espresso") as demo:
    
    # State variables to store results for publication report
    stored_results_state = gr.State(None)
    stored_df_state = gr.State(None)
    stored_params_state = gr.State(None)
    
    # State variables to store results for publication report
    stored_results_state = gr.State(None)
    stored_df_state = gr.State(None)
    stored_params_state = gr.State(None)
    
    gr.Markdown("""
    # 📊 Panel Espresso
    ### Fixed effects and pooled OLS with standard errors clustering
    
    **Status**: 🧪 DEPLOYED | CRV1, CRV3, HAC1, and wild bootstrap for small clusters
    **Note**: Standard errors clustering and bootstrap p-values for robust inference.
    
    ### 🆕 Features:
    - **Wild Cluster Bootstrap**: Automatic inference for datasets with < 30 clusters
    - **Webb Weights**: Optimal weights for small-sample scenarios
    - **Bootstrap p-values**: More reliable inference than asymptotic approximations
    - **NEW: WCR31 for Two-Way Clustering**: Preserves correlation in both dimensions
    - **Based on**: MacKinnon, Nielsen & Webb (2023), Cameron et al. (2008)
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 📁 Step 1: Upload data")
            file_input = gr.File(
                label="Upload CSV File",
                file_types=[".csv"],
                type="filepath"
            )
            data_status = gr.Textbox(label="Data Status", interactive=False, lines=2)
            
            gr.Markdown("---")
            gr.Markdown("## 🔧 Step 2: Configure variables")
            
            with gr.Group():
                gr.Markdown("**Panel Structure** (Required)")
                firm_id_dropdown = gr.Dropdown(
                    choices=[],
                    label="Firm ID Column",
                    info="Unique identifier for each entity"
                )
                year_dropdown = gr.Dropdown(
                    choices=[],
                    label="Time Column",
                    info="Year or time period variable"
                )
            
            with gr.Group():
                gr.Markdown("**Variables of Interest** (Required)")
                dependent_dropdown = gr.Dropdown(
                    choices=[],
                    label="Dependent Variable (Y)",
                    info="Outcome to be explained (e.g., ROA, performance)"
                )
                
                with gr.Row():
                    include_lag_dv = gr.Checkbox(
                        label="Include Lag of Dependent Variable",
                        value=False,
                        info="Add lagged Y as control variable"
                    )
                with gr.Row():
                    lag_min = gr.Number(
                        label="Minimum Lag",
                        value=1,
                        minimum=1,
                        maximum=10,
                        step=1,
                        interactive=False,
                        info="Starting lag period (e.g., 1 = t-1)"
                    )
                    lag_max = gr.Number(
                        label="Maximum Lag",
                        value=1,
                        minimum=1,
                        maximum=10,
                        step=1,
                        interactive=False,
                        info="Ending lag period (e.g., 1 = t-1 only)"
                    )
                
                independent_dropdown = gr.Dropdown(
                    choices=[],
                    label="Main independent variable (x)",
                    info="Main explanatory variable (e.g., emission, R&D)"
                )
                control_checkbox = gr.CheckboxGroup(
                    choices=[],
                    value=[],
                    label="Control variables",
                    info="Select time-varying control variables"
                )
            
            with gr.Group():
                gr.Markdown("**Time-invariant variables** (Optional)")
                industry_dropdown = gr.Dropdown(
                    choices=[],
                    value="None",
                    label="Industry variable",
                    info="For Pooled OLS; absorbed in FE"
                )
                country_dropdown = gr.Dropdown(
                    choices=[],
                    value="None",
                    label="Country variable",
                    info="For Pooled OLS; absorbed in FE"
                )
        
        with gr.Column(scale=1):
            gr.Markdown("## ⚙️ Step 3: Choose method")
            
            method = gr.Radio(
                choices=[
                    "Fixed Effects (Firm + Year)",
                    "Pooled OLS (with Industry/Country Dummies)"
                ],
                value="Fixed Effects (Firm + Year)",
                label="Estimation Method"
            )
            
            with gr.Accordion("📚 Method descriptions", open=False):
                gr.Markdown("""
                **✅ Fixed Effects**
                - Within-firm changes over time
                - Controls for ALL time-invariant firm traits
                - Industry/country absorbed into firm effects
                - Most rigorous for causal inference
                - Recommended for panel data
                
                **✅ Pooled OLS**
                - Includes industry/country dummies directly
                - Assumes no unobserved heterogeneity
                - USE WITH CAUTION - likely biased in panel data
                - Only if firm effects are negligible (homogeneous firms)
                                
                """)
            
            gr.Markdown("---")
            gr.Markdown("## 🎛️ Step 4: Specifications")
            
            include_year_fe = gr.Checkbox(
                label="Include year fixed effects",
                value=True,
                info="✓ Recommended - controls for common time shocks"
            )
            
            cluster_method = gr.Dropdown(
                choices=[
                    "One-way (Firm only) with CRV1",
                    "One-way (Firm only) with CRV3",
                    "One-way (Industry) with CRV1",
                    "One-way (Industry) with CRV3",
                    "One-way (Country) with CRV1",
                    "One-way (Country) with CRV3",
                    "Two-way (Firm × Year) with CRV1",
                    "Two-way (Firm × Year) with CRV3",
                    "Two-way (Industry × Country) with CRV1",
                    "Two-way (Industry × Country) with CRV3",
                    "Robust (Heteroskedasticity only)"
                ],
                value="One-way (Firm only) with CRV1",
                label="Clustering Method",
                info="✅ One-way firm clustering is the default - choose based on your data structure"
            )
            
            with gr.Accordion("📚 Clustering guide: when to use each method", open=False):
                gr.Markdown("""
                ### 🎯 Default: One-way (Firm only) with CRV1
                
                **Why one-way firm clustering**
                - Most common starting point for panel data
                - Accounts for correlation within firms over time
                - Computationally efficient
                
                **When to use CRV3 (vs CRV1)**
                - CRV3 = Small-cluster correction (more conservative)
                - Use when clusters < 50
                - CRV1 = Standard asymptotic (assumes many clusters)
                
                ---
                
                ### 📖 Decision Guide
                
                | Situation | Recommended method |
                |-----------|---------------------|
                | Standard panel with many firms | **One-way (Firm) CRV1** ✅ |
                | Few firms (<50) | One-way (Firm) CRV3 |
                | Panel with year FE + time correlation | Two-way (Firm × Year) CRV3 |
                | Many firms (>50), many years (>50) | Two-way (Firm × Year) CRV1 |
                | Industry-level treatment | One-way (Industry) CRV3 |
                | Country-level treatment | One-way (Country) CRV3 |
                | Industry-country analysis | Two-way (Industry × Country) CRV3 |
                | Few years (<20) | **Two-way CRV3** (critical) |
                | Country-level DiD | Country CRV3 |
                | No time/macro shocks expected | One-way Firm CRV3 |
                | Extremely small clusters (<6) | Consider wild bootstrap* |
                
                * Wild cluster bootstrap is available for small clusters to improve inference              
                ---
                
                ### 🚨 Common mistakes to avoid
                
                ❌ **Using one-way clustering when you have year fixed effects**
                   → Ignores correlation from common time shocks
                   → Standard errors too small → false significance
                
                ❌ **Using CRV1 with few clusters (<30 or <50)**
                   → Downward-biased standard errors
                   → Use CRV3 instead
                
                ❌ **No clustering at all in panel data**
                   → Assumes independence across firms and time
                   → Almost always biased results in practice
                
                ---
                
                ### 📚 References
                
                - Cameron, A. C., & Miller, D. L. (2015). A practitioner's guide to cluster-robust inference. The Journal of Human Resources, 50(2), 317-372. http://www.jstor.org/stable/24735989
                - MacKinnon, J. G., Nielsen, M. Ø., & Webb, M. D. (2023). Fast and reliable jackknife and bootstrap methods for cluster-robust inference. Journal of Applied Econometrics, 38(5), 671-694. https://doi.org/https://doi.org/10.1002/jae.2969 
                - MacKinnon, J. G., & Webb, M. D. (2017). Wild cluster bootstrap inference for wildly different cluster sizes. Journal of Applied Econometrics, 32(2), 233–254. https://www.jstor.org/stable/26609716
                
                """)
            
            gr.Markdown("---")
            gr.Markdown("## 🔬 Wild cluster bootstrap settings")
            
            # Wild Cluster Bootstrap UI Section (Experiment 1: with nested accordion)
            with gr.Accordion("⚠️ ADVANCED: wild cluster bootstrap settings", open=False) as bootstrap_accordion:
                
                use_bootstrap = gr.Checkbox(
                    label="Enable Wild Cluster Bootstrap",
                    value=True,
                    info="Automatically runs when clusters < 30"
                )
                
                bootstrap_variables = gr.CheckboxGroup(
                    choices=[],
                    value=[],
                    label="Variables to bootstrap",
                    info="Default: Only independent variable (recommended)"
                )

                gr.Markdown("""
                **Default Behavior**: Only the main independent variable is tested with bootstrap
                
                **Optional**: Select additional variables below if you need bootstrap inference for controls
                """)
                
                # Nested accordion for considerations and guidelines
                with gr.Accordion("📚 Bootstrap guidelines & multiple testing", open=False):
                    gr.Markdown("""
                    ⚠️ **Important considerations**:
                    - Each variable adds ~10 seconds of computation
                    - Consider multiple testing corrections when testing multiple variables
                    - Consider bootstrap the primary predictor variable only
                    
                    📚 **When to use multi-variable bootstrap**:
                    - ✅ Specific control variables are of substantive interest
                    - ✅ Testing multiple treatment variables
                    - ✅ Very small clusters (G < 20) - all coefficients questionable
                    - ❌ "Just to be safe" - not a valid reason
                    - ❌ When clusters are sufficient (G > 50)
                    
                    📖 **Multiple Testing**:
                    When testing multiple variables, apply corrections:
                    - **Bonferroni**: α = 0.05 / K (most conservative)
                    - **Holm-Bonferroni**: Sequential Bonferroni (less conservative)
                    - **FDR**: Benjamini-Hochberg procedure
                    
                    💡 **Recommendation**: 
                    - For most studies: Leave only the independent variable checked
                    - Only add controls if they are of direct substantive interest
                    - Always report multiple testing corrections when testing multiple variables
                    """)
            
            gr.Markdown("---")
            
            with gr.Group():
                gr.Markdown("**Moderating variable (interaction term)** - Optional")
                moderator_dropdown = gr.Dropdown(
                    choices=[],
                    value="None",
                    label="Moderator variable",
                    info="Variable that may change the effect of x on y"
                )
                include_interaction = gr.Checkbox(
                    label="Include interaction term (x × moderator)",
                    value=False,
                    info="Tests if the moderator changes the x→y relationship"
                )
            
            gr.Markdown("---")
            analyze_btn = gr.Button("🚀 Run analysis", variant="primary", size="lg")
    
    gr.Markdown("---")
    gr.Markdown("## 📈 Results")
    
    with gr.Tabs():
        with gr.Tab("📊 Estimates"):
            results_output = gr.Textbox(
                label="Estimation results",
                lines=30,
                max_lines=50
            )
        
        with gr.Tab("🔍 Diagnostics"):
            diagnostics_output = gr.Textbox(
                label="Model Diagnostics",
                lines=15,
                max_lines=15
            )
        
        with gr.Tab("💻 Python code"):
            code_output = gr.Code(
                label="Reproducible code",
                language="python",
                lines=20,
                max_lines=20
            )
        
        with gr.Tab("📑 Comprehensive result"):
            gr.Markdown("""
            ### Publication-Ready Report
            
            Click the button below to generate a comprehensive publication report including:
            - Publication-quality regression table (pyfixest etable)
            - Descriptive statistics for all variables used in analysis
            - Categorical variable summaries (firms, countries, industries, years)
            - Cross-tabulations (firms per industry/country)
            
            **Note**: Generate this report after running your analysis to ensure it reflects the current results.
            """)
            
            generate_report_btn = gr.Button("📊 Generate full result", variant="primary")
            publication_output = gr.Markdown(label="Comprehensive result")
            
            # Export button - only visible after report is generated
            export_button = gr.Button(
                "📥 Export to Word Document",
                variant="secondary",
                size="lg",
                visible=False
            )
            export_status = gr.Textbox(
                label="Export Status",
                lines=8,
                interactive=False,
                visible=False
            )
        
        with gr.Tab("📈 Stepwise Models"):
            gr.Markdown("""
            ### Progressive Model Specifications
            
            This report shows your analysis as a series of nested models:
            - **Model 1**: Independent variable only
            - **Model 2**: Independent variable + ALL controls
            - **Model 3**: Add year fixed effects
            - **Model 4**: Add interaction terms (if specified)
            - **Model 5**: Add lagged variables (if specified)
            
            **Strategy**: Controls are added all at once (not one-by-one) to show the complete vs. restricted specification.
            
            **Why use stepwise models?**
            - Check coefficient stability across specifications
            - Assess impact of controls on your main variable
            - Demonstrate robustness of findings
            - Standard practice in panel data research
            
            **Note**: All models use the same clustering method specified in your analysis.
            """)
            
            generate_stepwise_btn = gr.Button("📊 Generate Stepwise Report", variant="primary")
            stepwise_output = gr.Markdown(label="Stepwise Report")

    
    with gr.Row():
        gr.Markdown("""
        ### 📖 Implementation status

        **Core estimation methods:**
        - ✅ Fixed Effects (Firm + Year) with clustered SE
        - ✅ Pooled OLS with industry/country dummies
        
        **Features:**
        - ✅ Interaction terms with moderating variables
        - ✅ Dynamic variable selection from uploaded data
        - ✅ Lagged dependent variables support
        - ✅ Comprehensive diagnostics for each method
        - ✅ Reproducible Python code generation
        - ✅ Efficient high-dimensional fixed effects 
        
        **About Panel Espresso:**
        - Fast estimation for models with many fixed effects
        - Python implementation inspired by R's fixest package
        - Excellent for panel data and difference-in-differences designs
        """)
    
    # Event handlers
    file_input.change(
        fn=get_column_names,
        inputs=[file_input],
        outputs=[
            firm_id_dropdown, year_dropdown, dependent_dropdown, independent_dropdown,
            control_checkbox, moderator_dropdown, industry_dropdown, country_dropdown,
            data_status
        ]
    )
    
    # Enable/disable lag inputs based on checkbox
    include_lag_dv.change(
        fn=lambda checked: (gr.Number(interactive=checked), gr.Number(interactive=checked)),
        inputs=[include_lag_dv],
        outputs=[lag_min, lag_max]
    )
    
    # Update bootstrap variable choices when model specification changes
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
    
    analyze_btn.click(
        fn=analyze_panel_data,
        inputs=[
            file_input, firm_id_dropdown, year_dropdown, dependent_dropdown, independent_dropdown,
            control_checkbox, method, include_year_fe, cluster_method,
            moderator_dropdown, include_interaction, industry_dropdown, country_dropdown,
            include_lag_dv, lag_min, lag_max,
            use_bootstrap, bootstrap_variables
        ],
        outputs=[results_output, diagnostics_output, code_output, stored_results_state, stored_df_state, stored_params_state]
    )
    
    # Generate publication report button - also shows export button
    def generate_report_and_show_export(stored_results, stored_df, stored_params):
        report = generate_publication_report(stored_results, stored_df, stored_params)
        # Show export button only if report was successfully generated
        show_export = not ("No results available" in report or "Error" in report)
        return (
            report,
            gr.update(visible=show_export),
            gr.update(visible=False)  # Hide export status initially
        )
    
    generate_report_btn.click(
        fn=generate_report_and_show_export,
        inputs=[stored_results_state, stored_df_state, stored_params_state],
        outputs=[publication_output, export_button, export_status]
    )
    
    # Export to Word button
    def export_and_show_status(report_text, stored_results, stored_df, stored_params):
        status = export_report_to_word_gradio(
            report_text, 
            output_dir="./",
            stored_results=stored_results,
            stored_df=stored_df,
            stored_params=stored_params
        )
        return status, gr.update(visible=True)
    
    export_button.click(
        fn=export_and_show_status,
        inputs=[publication_output, stored_results_state, stored_df_state, stored_params_state],
        outputs=[export_status, export_status]
    )
    
    # Generate stepwise report button
    generate_stepwise_btn.click(
        fn=generate_stepwise_report,
        inputs=[stored_results_state, stored_df_state, stored_params_state],
        outputs=[stepwise_output]
    )
    
    gr.Markdown("""
    ---
    **Important notes**
    - Panel Espresso is built on python libraries designed for efficient fixed effects estimation
    - Fixed Effects is the recommended method for most panel data applications
    - Always validate results and check assumptions
    - Refer to the documentation and references for guidance on clustering and bootstrap methods
    """)

if __name__ == "__main__":
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860, inbrowser=True)
