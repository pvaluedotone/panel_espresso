"""
Panel Data Analysis App with pyfixest - MULTI-VARIABLE BOOTSTRAP VERSION
Allows users to optionally select which variables to bootstrap via the UI
Author: Saiyidi MAT RONI
Date: December 22, 2025

ADVANCED FEATURES:
- Multi-variable wild cluster bootstrap selection
- User can choose which variables to test with bootstrap
- Default: Only main independent variable (standard practice)
- Optional: Add control variables to bootstrap testing
"""

import gradio as gr
import pandas as pd
import numpy as np
import pyfixest as pf
import traceback
from typing import Optional, List, Tuple, Dict
import warnings
import wildboottest
warnings.filterwarnings('ignore')


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


def run_wild_bootstrap_for_variable(
    results,
    df_clean: pd.DataFrame,
    firm_id_col: str,
    year_col: str,
    cluster_method: str,
    country_var: Optional[str],
    industry_var: Optional[str],
    variable_name: str,
    bootstrap_reps: int = 9999
) -> Optional[Dict]:
    """
    Run wild cluster bootstrap for a specific variable
    
    Based on Cameron, Gelbach & Miller (2008) and MacKinnon, Nielsen & Webb (2023),
    wild cluster bootstrap provides more reliable inference with few clusters.
    
    Parameters:
    -----------
    results : pyfixest Feols object
        Estimated model results
    df_clean : pd.DataFrame
        Clean data used for estimation
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
    variable_name : str
        Parameter to test (can be independent var or control)
    bootstrap_reps : int
        Number of bootstrap replications (default 9999)
    
    Returns:
    --------
    Dict or None : Bootstrap results if clusters < 30, otherwise None
    """
    try:
        # Determine number of clusters
        is_two_way = "Two-way" in cluster_method
        
        if is_two_way:
            # Determine which two dimensions are being clustered
            if "Industry × Country" in cluster_method:
                n_clusters_1 = df_clean[industry_var].nunique() if industry_var and industry_var != "None" else 999
                n_clusters_2 = df_clean[country_var].nunique() if country_var and country_var != "None" else 999
            else:  # Firm × Year
                n_clusters_1 = df_clean[firm_id_col].nunique()
                n_clusters_2 = df_clean[year_col].nunique()
            min_clusters = min(n_clusters_1, n_clusters_2)
            cluster_var_numeric = None  # Two-way not directly supported by wildboottest
            cluster_var_original = None
        elif "Industry" in cluster_method and industry_var and industry_var != "None":
            min_clusters = df_clean[industry_var].nunique()
            cluster_var_numeric = "_industry_numeric"
            cluster_var_original = industry_var
        elif "Country" in cluster_method and country_var and country_var != "None":
            min_clusters = df_clean[country_var].nunique()
            cluster_var_numeric = "_country_numeric"
            cluster_var_original = country_var
        else:
            min_clusters = df_clean[firm_id_col].nunique()
            cluster_var_numeric = "_firm_id_numeric"
            cluster_var_original = firm_id_col
        
        # Run bootstrap only if clusters < 30 and not two-way
        # Note: wildboottest currently supports one-way clustering
        if min_clusters < 30 and cluster_var_numeric is not None:
            print(f"🔄 Running wild cluster bootstrap for '{variable_name}' with {min_clusters} clusters...")
            
            # Adjust bootstrap replications if clusters are very small
            # When G < 10, full enumeration may be better (2^G permutations)
            if min_clusters < 10:
                max_perms = 2 ** min_clusters
                if bootstrap_reps > max_perms:
                    bootstrap_reps = max_perms
                    print(f"   Using full enumeration: {max_perms} permutations")
            
            # Verify numeric cluster variable exists in dataframe
            if cluster_var_numeric not in df_clean.columns:
                raise ValueError(f"Numeric cluster variable {cluster_var_numeric} not found in dataframe")
            
            print(f"   Using numeric cluster variable '{cluster_var_numeric}' (converted from '{cluster_var_original}')...")
            
            # Run wild cluster bootstrap using Webb weights (best for small clusters)
            boot_result = results.wildboottest(
                param=variable_name,  # Test this specific variable
                reps=bootstrap_reps,
                cluster=cluster_var_numeric,  # Use numeric version
                weights_type="webb",  # Webb (2014) weights best for small G
                impose_null=True,
                bootstrap_type="11",  # Standard restricted bootstrap
                seed=12345,  # For reproducibility
                k_adj=True,  # Small sample adjustment for k
                G_adj=True   # Small sample adjustment for G (critical for small clusters)
            )
            
            return {
                "variable_name": variable_name,
                "n_clusters": min_clusters,
                "cluster_var": cluster_var_original,
                "bootstrap_reps": bootstrap_reps,
                "results": boot_result,
                "recommended": min_clusters < 30
            }
        
        return None
        
    except Exception as e:
        print(f"⚠️ Bootstrap failed for '{variable_name}': {str(e)[:200]}")
        print("   Continuing with asymptotic inference only...")
        return None


def run_bootstrap_for_selected_variables(
    results,
    df_clean: pd.DataFrame,
    firm_id_col: str,
    year_col: str,
    cluster_method: str,
    country_var: Optional[str],
    industry_var: Optional[str],
    selected_variables: List[str],
    bootstrap_reps: int = 9999
) -> Dict[str, Optional[Dict]]:
    """
    Run wild cluster bootstrap for multiple selected variables
    
    Returns a dictionary mapping variable names to their bootstrap results
    """
    bootstrap_results = {}
    
    for var_name in selected_variables:
        result = run_wild_bootstrap_for_variable(
            results, df_clean, firm_id_col, year_col, cluster_method,
            country_var, industry_var, var_name, bootstrap_reps
        )
        bootstrap_results[var_name] = result
    
    return bootstrap_results


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


def update_bootstrap_variable_choices(independent_var, control_vars):
    """
    Update the bootstrap variable selection based on model specification
    Default: Only independent variable is selected
    """
    if not independent_var:
        return gr.CheckboxGroup(choices=[], value=[])
    
    all_vars = [independent_var]
    if control_vars:
        all_vars.extend(control_vars)
    
    # Default: Only select the main independent variable
    return gr.CheckboxGroup(choices=all_vars, value=[independent_var])


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
    use_wild_bootstrap: bool = True,
    bootstrap_variables: List[str] = None,
    bootstrap_reps: int = 9999
) -> Tuple[str, str, str]:
    """
    Run Fixed Effects Model with optional multi-variable wild cluster bootstrap
    
    Parameters:
    -----------
    bootstrap_variables : List[str]
        List of variables to test with wild cluster bootstrap
        Default behavior: Only test the main independent variable
    """
    try:
        # Prepare panel data
        df_clean = df[[firm_id_col, year_col, dependent_var, independent_var] + control_vars].copy()
        
        # Sort by firm and year for proper lagging
        df_clean = df_clean.sort_values([firm_id_col, year_col])
        
        # CRITICAL FIX: Convert cluster variables to numeric codes for wildboottest compatibility
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
        
        # Drop missing values
        df_clean = df_clean.dropna()
        
        # Build formula for pyfixest
        exog_vars = [independent_var] + control_vars
        if moderator_var and moderator_var != "None" and include_interaction:
            exog_vars.append(f'{independent_var}_x_{moderator_var}')
        
        formula_rhs = ' + '.join(exog_vars)
        
        # Add fixed effects
        if include_year_fe:
            fixed_effects = f"{firm_id_col} + {year_col}"
        else:
            fixed_effects = f"{firm_id_col}"
        
        formula = f"{dependent_var} ~ {formula_rhs} | {fixed_effects}"
        
        # Set up clustering based on method chosen
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
        
        # Estimate model with pyfixest
        results = pf.feols(formula, data=df_clean, vcov=vcov, demeaner_backend="rust")
        
        # MULTI-VARIABLE WILD CLUSTER BOOTSTRAP
        multi_bootstrap_results = {}
        if use_wild_bootstrap and bootstrap_variables:
            multi_bootstrap_results = run_bootstrap_for_selected_variables(
                results, df_clean, firm_id_col, year_col, cluster_method,
                country_var, industry_var, bootstrap_variables, bootstrap_reps
            )
        
        # Format results
        results_summary = format_fe_results_with_multi_bootstrap(
            results, dependent_var, independent_var, 
            include_year_fe, moderator_var, include_interaction,
            df_clean, firm_id_col, year_col, cluster_method, country_var,
            multi_bootstrap_results
        )
        
        # Diagnostics
        diagnostics = format_diagnostics_with_multi_bootstrap(
            results, df_clean, firm_id_col, year_col, cluster_method, 
            country_var, multi_bootstrap_results
        )
        
        # Code snippet
        code = generate_code_snippet_multi_bootstrap(
            firm_id_col, year_col, dependent_var, independent_var,
            control_vars, include_year_fe, moderator_var, include_interaction, 
            cluster_method, bootstrap_variables
        )
        
        return results_summary, diagnostics, code
    
    except Exception as e:
        error_msg = f"❌ Error in Fixed Effects estimation:\n\n{str(e)}\n\n{traceback.format_exc()}"
        return error_msg, "", ""


def format_fe_results_with_multi_bootstrap(
    results, dependent_var, independent_var, include_year_fe, 
    moderator_var, include_interaction, df_clean, firm_id_col, year_col,
    cluster_method="Two-way (Firm × Year) with CRV3", country_var=None,
    multi_bootstrap_results: Dict[str, Optional[Dict]] = None
):
    """Format Fixed Effects results with multi-variable bootstrap results"""
    
    n_firms = df_clean[firm_id_col].nunique()
    n_years = df_clean[year_col].nunique()
    n_obs = len(df_clean)
    
    # Get coefficient summary
    coef_df = results.tidy()
    if coef_df.index.name:
        coef_df = coef_df.reset_index()
        coef_name_col = coef_df.columns[0]
    else:
        coef_df = coef_df.reset_index()
        coef_name_col = 'index'
    
    # Get model statistics
    r2 = results._r2_overall if hasattr(results, '_r2_overall') else getattr(results, '_r2', 0)
    r2_within = results._r2_within if hasattr(results, '_r2_within') else r2
    f_stat = results._f_statistic['statistic'] if hasattr(results, '_f_statistic') and results._f_statistic else "N/A"
    
    coef_table = coef_df.to_string(index=False)
    
    # Add bootstrap sections if available
    bootstrap_section = ""
    if multi_bootstrap_results:
        # Check if any bootstrap was actually run
        any_bootstrap = any(v is not None for v in multi_bootstrap_results.values())
        
        if any_bootstrap:
            bootstrap_section = """
╔═══════════════════════════════════════════════════════════════════╗
║        WILD CLUSTER BOOTSTRAP INFERENCE (MULTI-VARIABLE)          ║
╚═══════════════════════════════════════════════════════════════════╝
"""
            
            for var_name, boot_res_dict in multi_bootstrap_results.items():
                if boot_res_dict is not None:
                    boot_res = boot_res_dict["results"]
                    n_clusters = boot_res_dict["n_clusters"]
                    cluster_var = boot_res_dict["cluster_var"]
                    boot_reps = boot_res_dict["bootstrap_reps"]
                    
                    # Get asymptotic p-value
                    var_row = coef_df[coef_df[coef_name_col] == var_name]
                    asymp_pval = var_row['Pr(>|t|)'].values[0] if len(var_row) > 0 else None
                    
                    # Format asymptotic p-value and stars
                    if asymp_pval is not None:
                        asymp_pval_str = f"{asymp_pval:.4f}"
                        asymp_stars = get_significance_stars(asymp_pval)
                    else:
                        asymp_pval_str = "N/A"
                        asymp_stars = ""
                    
                    bootstrap_section += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variable: {var_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  Small Cluster Detection: {n_clusters} clusters in '{cluster_var}'
    → Wild cluster bootstrap recommended for G < 30

Bootstrap Results:
  • Bootstrap replications: {boot_reps:,}
  • Bootstrap t-statistic: {boot_res['t value']:.4f}
  • Bootstrap p-value: {boot_res['Pr(>|t|)']:.4f} {get_significance_stars(boot_res['Pr(>|t|)'])}
  • Asymptotic p-value: {asymp_pval_str} {asymp_stars}
  
  • Bootstrap type: {boot_res['bootstrap_type']} (restricted)
  • Weights: Webb (2014) - optimal for small G
  • Inference: {boot_res['inference']}

📊 Interpretation:
  • Bootstrap p-value is more reliable with few clusters
  • Use bootstrap p-value for hypothesis testing
  • Difference in p-values indicates small-cluster issues
"""
    
    output = f"""
╔══════════════════════════════════════════════════════════════════╗
║              FIXED EFFECTS REGRESSION RESULTS                    ║
║             (High-Dimensional FE with pyfixest)                  ║
╚══════════════════════════════════════════════════════════════════╝

Model: Fixed Effects (Within Estimator)
Dependent Variable: {dependent_var}
Key Independent Variable: {independent_var}
Firm Fixed Effects: ✓
{'Year Fixed Effects: ✓' if include_year_fe else 'Year Fixed Effects: ✗'}
Clustering: {cluster_method}

Panel Structure:
  • Firms: {n_firms:,}
  • Years: {n_years:,}
  • Observations: {n_obs:,}
  • Avg obs per firm: {n_obs/n_firms:.1f}

{coef_table}

Model Fit:
  • R² (Overall): {r2:.4f}
  • R² (Within): {r2_within:.4f}
  • F-statistic: {f_stat}

{bootstrap_section}

─────────────────────────────────────────────────────────────────
📊 INTERPRETATION:
• Fixed Effects controls for ALL time-invariant firm characteristics
• Estimates based on within-firm variation over time
• Multi-variable bootstrap allows testing multiple hypotheses

⚠️ NOTE ON MULTIPLE TESTING:
• When testing multiple variables, consider multiple testing corrections
• Bonferroni: Multiply p-values by number of tests
• FDR control: Use Benjamini-Hochberg procedure
• Focus on primary hypothesis (usually the independent variable)
"""
    
    return output


def format_diagnostics_with_multi_bootstrap(
    results, df_clean, firm_id_col, year_col, cluster_method, 
    country_var, multi_bootstrap_results
):
    """Format diagnostics with multi-variable bootstrap information"""
    
    n_firms = df_clean[firm_id_col].nunique()
    n_years = df_clean[year_col].nunique()
    
    # Determine clustering dimension
    if "Two-way" in cluster_method:
        if "Industry × Country" in cluster_method:
            cluster_info = f"Two-way clustering (not supported by wildboottest)"
        else:
            cluster_info = f"Two-way: {n_firms} firms × {n_years} years (min={min(n_firms, n_years)})"
    else:
        cluster_info = f"One-way: {n_firms} firms"
    
    # Bootstrap summary
    bootstrap_summary = ""
    if multi_bootstrap_results:
        tested_vars = [k for k, v in multi_bootstrap_results.items() if v is not None]
        if tested_vars:
            bootstrap_summary = f"""
╔═══════════════════════════════════════════════════════════════════╗
║              MULTI-VARIABLE BOOTSTRAP SUMMARY                     ║
╚═══════════════════════════════════════════════════════════════════╝

Variables tested with wild cluster bootstrap:
{chr(10).join([f'  • {var}' for var in tested_vars])}

📖 Interpretation Guide:
- These variables received bootstrap inference due to small clusters
- Use bootstrap p-values for these variables
- Other variables rely on asymptotic cluster-robust inference
- Consider multiple testing corrections when testing multiple hypotheses

"""
    
    output = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    MODEL DIAGNOSTICS                             ║
╚══════════════════════════════════════════════════════════════════╝

Panel Balance:
  • Total firms: {n_firms:,}
  • Time periods: {n_years:,}
  • Total observations: {len(df_clean):,}

Clustering Structure:
  • Method: {cluster_method}
  • Details: {cluster_info}

{bootstrap_summary}

✅ VALIDITY CHECKS:
✓ Fixed effects estimated via within transformation
✓ Cluster-robust standard errors applied
{'✓ Wild cluster bootstrap used for small clusters' if multi_bootstrap_results else ''}
"""
    
    return output


def generate_code_snippet_multi_bootstrap(
    firm_id_col, year_col, dependent_var, independent_var,
    control_vars, include_year_fe, moderator_var, include_interaction, 
    cluster_method, bootstrap_variables
):
    """Generate code snippet with multi-variable bootstrap"""
    
    controls_str = ' + '.join(control_vars) if control_vars else ''
    
    exog_list = [independent_var] + (control_vars if control_vars else [])
    if moderator_var and moderator_var != "None" and include_interaction:
        exog_list.append(f'{independent_var}_x_{moderator_var}')
    
    formula_rhs = ' + '.join(exog_list)
    
    if include_year_fe:
        fixed_effects = f"{firm_id_col} + {year_col}"
    else:
        fixed_effects = f"{firm_id_col}"
    
    formula = f"{dependent_var} ~ {formula_rhs} | {fixed_effects}"
    
    # Clustering setup
    if "Two-way" in cluster_method and "CRV3" in cluster_method:
        vcov_code = f"vcov = {{'CRV3': '{firm_id_col} + {year_col}'}}"
        cluster_var = firm_id_col
    elif "Two-way" in cluster_method and "CRV1" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': '{firm_id_col} + {year_col}'}}"
        cluster_var = firm_id_col
    elif "Firm only" in cluster_method and "CRV3" in cluster_method:
        vcov_code = f"vcov = {{'CRV3': '{firm_id_col}'}}"
        cluster_var = firm_id_col
    elif "Firm only" in cluster_method and "CRV1" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': '{firm_id_col}'}}"
        cluster_var = firm_id_col
    else:
        vcov_code = "vcov = 'hetero'"
        cluster_var = None
    
    # Multi-variable bootstrap code
    bootstrap_code = ""
    if cluster_var and bootstrap_variables:
        var_list_str = ', '.join([f"'{v}'" for v in bootstrap_variables])
        bootstrap_code = f"""

# MULTI-VARIABLE WILD CLUSTER BOOTSTRAP
n_clusters = df['{cluster_var}'].nunique()
print(f"Number of clusters: {{n_clusters}}")

if n_clusters < 30:
    print("⚠️  Running wild cluster bootstrap for selected variables...")
    
    # Variables to test with bootstrap
    test_variables = [{var_list_str}]
    
    bootstrap_results = {{}}
    for var_name in test_variables:
        print(f"\\nBootstrapping {{var_name}}...")
        boot_result = results.wildboottest(
            param=var_name,             # Test this specific variable
            reps=9999,                  # Bootstrap replications
            cluster='{cluster_var}',    # Cluster variable
            weights_type='webb',        # Webb (2014) weights
            impose_null=True,           
            bootstrap_type='11',        
            seed=12345,                 
            k_adj=True,                 
            G_adj=True                  
        )
        bootstrap_results[var_name] = boot_result
        print(f"  Bootstrap p-value: {{boot_result['Pr(>|t|)']:.4f}}")
        print(f"  Asymptotic p-value: {{results.tidy().loc[var_name, 'Pr(>|t|)']:.4f}}")
    
    print("\\n→ Use bootstrap p-values for inference with few clusters")
    print("⚠️  Consider multiple testing corrections when testing multiple variables")
"""
    
    code = f"""
# Panel Data Analysis with Multi-Variable Wild Cluster Bootstrap

import pandas as pd
import pyfixest as pf

# Load data
df = pd.read_csv('your_data.csv')

# Drop missing values
df = df[['{firm_id_col}', '{year_col}', '{dependent_var}', '{independent_var}'{", " + ", ".join([f"'{c}'" for c in control_vars]) if control_vars else ""}]].dropna()

# Build formula
formula = "{formula}"

# Estimate Fixed Effects model
results = pf.feols(formula, data=df, {vcov_code}, demeaner_backend="rust")

# Display results
print(results.summary())
{bootstrap_code}
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
    use_bootstrap,
    bootstrap_variables
):
    """
    Main analysis function with multi-variable bootstrap support
    """
    if file is None:
        return "⚠️ Please upload a CSV file", "", ""
    
    if not all([firm_id_col, year_col, dependent_var, independent_var]):
        return "⚠️ Please specify all required variables", "", ""
    
    try:
        # Load data
        df, status = load_and_validate_data(file.name)
        if df is None:
            return status, "", ""
        
        # Route to Fixed Effects (simplified for this example)
        if method == "Fixed Effects (Firm + Year)":
            return run_fixed_effects_model(
                df, firm_id_col, year_col, dependent_var, independent_var,
                control_vars if control_vars else [], include_year_fe,
                moderator_var, include_interaction, cluster_method, country_var,
                industry_var, use_bootstrap, bootstrap_variables
            )
        else:
            return "⚠️ Only Fixed Effects implemented in this version", "", ""
    
    except Exception as e:
        error_msg = f"❌ Unexpected error:\n\n{str(e)}\n\n{traceback.format_exc()}"
        return error_msg, "", ""


# ═══════════════════════════════════════════════════════════════════════════
#                            GRADIO INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    with gr.Blocks(title="Panel Data Analyzer - Multi-Variable Bootstrap") as demo:
        
        gr.Markdown("""
        # 📊 Panel Data Analysis Tool - Multi-Variable Bootstrap Edition
        ### Wild Cluster Bootstrap for Multiple Variables (Optional)
    
        **Version**: Multi-Variable Bootstrap | Advanced Feature
        **Key Feature**: Select which variables to test with wild cluster bootstrap
    
        ### 🆕 What's Different:
        - **Default**: Only main independent variable bootstrapped (standard practice)
        - **Optional**: Add control variables to bootstrap testing
        - **Flexibility**: Choose exactly which variables need robust inference
        - **Note**: Consider multiple testing corrections when bootstrapping multiple variables
        """)
    
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 📁 Step 1: Upload Data")
                file_input = gr.File(
                    label="Upload CSV File",
                    file_types=[".csv"],
                    type="filepath"
                )
                data_status = gr.Textbox(label="Data Status", interactive=False, lines=2)
            
                gr.Markdown("---")
                gr.Markdown("## 🔧 Step 2: Configure Variables")
            
                with gr.Group():
                    gr.Markdown("**Panel Structure** (Required)")
                    firm_id_dropdown = gr.Dropdown(
                        choices=[],
                        label="Firm ID Column"
                    )
                    year_dropdown = gr.Dropdown(
                        choices=[],
                        label="Time Column"
                    )
            
                with gr.Group():
                    gr.Markdown("**Variables of Interest** (Required)")
                    dependent_dropdown = gr.Dropdown(
                        choices=[],
                        label="Dependent Variable (Y)"
                    )
                    independent_dropdown = gr.Dropdown(
                        choices=[],
                        label="Key Independent Variable (X)"
                    )
                    control_checkbox = gr.CheckboxGroup(
                        choices=[],
                        value=[],
                        label="Control Variables"
                    )
            
                with gr.Group():
                    gr.Markdown("**Time-Invariant Variables** (Optional)")
                    industry_dropdown = gr.Dropdown(
                        choices=[],
                        value="None",
                        label="Industry Variable"
                    )
                    country_dropdown = gr.Dropdown(
                        choices=[],
                        value="None",
                        label="Country Variable"
                    )
        
            with gr.Column(scale=1):
                gr.Markdown("## ⚙️ Step 3: Choose Method")
            
                method = gr.Radio(
                    choices=["Fixed Effects (Firm + Year)"],
                    value="Fixed Effects (Firm + Year)",
                    label="Estimation Method"
                )
            
                gr.Markdown("---")
                gr.Markdown("## 🎛️ Step 4: Specifications")
            
                include_year_fe = gr.Checkbox(
                    label="Include Year Fixed Effects",
                    value=True
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
                    label="Clustering Method"
                )
            
                with gr.Group():
                    gr.Markdown("**Moderating Variable** (Optional)")
                    moderator_dropdown = gr.Dropdown(
                        choices=[],
                        value="None",
                        label="Moderator Variable"
                    )
                    include_interaction = gr.Checkbox(
                        label="Include Interaction Term",
                        value=False
                    )
            
                gr.Markdown("---")
                gr.Markdown("## 🔬 Wild Cluster Bootstrap Settings")
            
                with gr.Accordion("⚠️ ADVANCED: Multi-Variable Bootstrap Selection", open=True):
                    gr.Markdown("""
                    **Default Behavior**: Only the main independent variable is tested with bootstrap (standard practice)
                
                    **Optional**: Select additional variables below if you need bootstrap inference for controls
                
                    ⚠️ **Important Considerations**:
                    - Each variable adds ~10 seconds of computation
                    - Consider multiple testing corrections
                    - Most studies only bootstrap the primary variable
                    """)
                
                    use_bootstrap = gr.Checkbox(
                        label="Enable Wild Cluster Bootstrap",
                        value=True,
                        info="Automatically runs when clusters < 30"
                    )
                
                    bootstrap_variables = gr.CheckboxGroup(
                        choices=[],
                        value=[],
                        label="Variables to Bootstrap",
                        info="Default: Only independent variable (recommended)"
                    )
            
                gr.Markdown("---")
                analyze_btn = gr.Button("🚀 Run Analysis", variant="primary", size="lg")
    
        gr.Markdown("---")
        gr.Markdown("## 📈 Results")
    
        with gr.Tabs():
            with gr.Tab("📊 Regression Output"):
                results_output = gr.Textbox(
                    label="Estimation Results",
                    lines=40,
                    max_lines=60
                )
        
            with gr.Tab("🔍 Diagnostics"):
                diagnostics_output = gr.Textbox(
                    label="Model Diagnostics",
                    lines=20,
                    max_lines=30
                )
        
            with gr.Tab("💻 Python Code"):
                code_output = gr.Code(
                    label="Reproducible Code",
                    language="python",
                    lines=30,
                    max_lines=40
                )
    
        gr.Markdown("""
        ---
        ### 📖 About Multi-Variable Bootstrap
    
        **Standard Practice**: Wild cluster bootstrap is typically applied only to the primary independent variable
    
        **When to Bootstrap Multiple Variables**:
        - ✅ When specific control variables are of substantive interest
        - ✅ When conducting multiple hypothesis tests
        - ✅ When clusters are very small (G < 20)
    
        **When NOT to Bootstrap All Variables**:
        - ❌ Computational cost: K variables × 9,999 reps each
        - ❌ Multiple testing issues need correction
        - ❌ Control variables usually ok with asymptotic inference
    
        **Multiple Testing Corrections**:
        - Bonferroni: Multiply p-values by number of tests
        - Holm-Bonferroni: Sequential Bonferroni (less conservative)
        - FDR: Benjamini-Hochberg procedure
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
                use_bootstrap, bootstrap_variables
            ],
            outputs=[results_output, diagnostics_output, code_output]
        )
    
        demo.launch(share=False, server_name="127.0.0.1", server_port=7861, inbrowser=True)
