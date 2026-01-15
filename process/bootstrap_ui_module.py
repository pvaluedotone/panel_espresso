"""
Wild Cluster Bootstrap UI Module
Reusable Gradio components and execution functions for multi-variable wild cluster bootstrap

This module provides:
- UI components for variable selection
- Bootstrap execution functions (single and multi-variable)
- Formatting and code generation utilities
- Support for one-way and two-way clustering with WCR31

Author: Saiyidi MAT RONI
Date: December 23, 2025
"""

import gradio as gr
import pandas as pd
from typing import List, Optional, Dict, Tuple


def create_bootstrap_ui_section():
    """
    Create the Wild Cluster Bootstrap UI section
    
    Returns:
    --------
    tuple: (use_bootstrap_checkbox, bootstrap_variables_checkbox, accordion)
        - use_bootstrap_checkbox: Checkbox to enable/disable bootstrap
        - bootstrap_variables_checkbox: CheckboxGroup for variable selection
        - accordion: The accordion container (for styling purposes)
    """
    
    with gr.Accordion("⚠️ ADVANCED: Wild Cluster Bootstrap Settings", open=False) as accordion:
        
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
        """)
                      
        gr.Markdown("""
        ---
        **💡 Recommendation**: 
        - For most studies: Leave only the independent variable checked
        - Only add controls if they are of direct substantive interest
        - Always report multiple testing corrections when testing multiple variables
        """)
    
    return use_bootstrap, bootstrap_variables, accordion


def update_bootstrap_variable_choices(independent_var: Optional[str], 
                                      control_vars: Optional[List[str]]) -> gr.CheckboxGroup:
    """
    Update the bootstrap variable selection based on model specification
    Default: Only independent variable is selected
    
    Parameters:
    -----------
    independent_var : str or None
        The main independent variable
    control_vars : list or None
        List of control variables
    
    Returns:
    --------
    gr.CheckboxGroup
        Updated checkbox group with new choices and default selection
    """
    if not independent_var:
        return gr.CheckboxGroup(choices=[], value=[])
    
    all_vars = [independent_var]
    if control_vars:
        all_vars.extend(control_vars)
    
    # Default: Only select the main independent variable
    return gr.CheckboxGroup(choices=all_vars, value=[independent_var])


def format_multi_variable_bootstrap_results(
    multi_bootstrap_results: dict,
    coef_df,
    coef_name_col: str
) -> str:
    """
    Format bootstrap results for multiple variables in a clean table format
    
    Parameters:
    -----------
    multi_bootstrap_results : dict
        Dictionary mapping variable names to bootstrap results
    coef_df : DataFrame
        Coefficient dataframe from pyfixest
    coef_name_col : str
        Name of the coefficient column
    
    Returns:
    --------
    str : Formatted bootstrap section for display
    """
    
    def get_significance_stars(pval):
        """Return significance stars based on p-value"""
        if pval < 0.001:
            return "***"
        elif pval < 0.01:
            return "**"
        elif pval < 0.05:
            return "*"
        return ""
    
    # Check if any bootstrap was actually run
    if not multi_bootstrap_results:
        return ""
    
    any_bootstrap = any(v is not None for v in multi_bootstrap_results.values())
    
    if not any_bootstrap:
        return ""
    
    # Collect bootstrap info from first valid result
    first_valid = next((v for v in multi_bootstrap_results.values() if v is not None), None)
    if not first_valid:
        return ""
    
    n_clusters = first_valid["n_clusters"]
    cluster_var = first_valid["cluster_var"]
    boot_reps = first_valid["bootstrap_reps"]
    is_two_way = first_valid.get("is_two_way", False)
    bootstrap_type = first_valid.get("bootstrap_type", "11")
    
    # Build header with clustering info
    bootstrap_section = """
╔═════════════════════════════════════════════════════════╗
║   WILD CLUSTER BOOTSTRAP INFERENCE (MULTI-VARIABLE)     ║
╚═════════════════════════════════════════════════════════╝
"""
    
    if is_two_way:
        other_cluster = first_valid.get("other_cluster", "")
        n_clusters_other = first_valid.get("n_clusters_other", 0)
        bootstrap_section += f"""
⚠️  Two-Way Clustering Detected
    Primary cluster: '{cluster_var}' (G={n_clusters}) ← Bootstrap dimension (SMALLER)
    Secondary cluster: '{other_cluster}' (G={n_clusters_other})
    → WCR31 bootstraps on '{cluster_var}' to preserve correlation in '{other_cluster}'

Bootstrap Configuration:
  • Bootstrap replications: {boot_reps:,}
  • Bootstrap type: {bootstrap_type} (WCR31 - bootstrapped on '{cluster_var}', preserves correlation in '{other_cluster}')
  • Weights: Webb (2014) - optimal for small G

"""
    else:
        bootstrap_section += f"""
⚠️  Small Cluster Detection: {n_clusters} clusters in '{cluster_var}'
    → Wild cluster bootstrap recommended for G < 30

Bootstrap Configuration:
  • Bootstrap replications: {boot_reps:,}
  • Bootstrap type: {bootstrap_type} (restricted)
  • Weights: Webb (2014) - optimal for small G

"""
    
    # Build table header
    bootstrap_section += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bootstrap Results Table:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    # Collect data for table
    table_rows = []
    for var_name, boot_res_dict in multi_bootstrap_results.items():
        if boot_res_dict is not None:
            boot_res = boot_res_dict["results"]
            
            # Get asymptotic p-value
            var_row = coef_df[coef_df[coef_name_col] == var_name]
            asymp_pval = var_row['Pr(>|t|)'].values[0] if len(var_row) > 0 else None
            
            # Get bootstrap values
            boot_t = boot_res['t value']
            boot_pval = boot_res['Pr(>|t|)']
            boot_stars = get_significance_stars(boot_pval)
            
            # Format asymptotic p-value
            if asymp_pval is not None:
                asymp_pval_str = f"{asymp_pval:.4f}"
                asymp_stars = get_significance_stars(asymp_pval)
            else:
                asymp_pval_str = "N/A"
                asymp_stars = ""
            
            table_rows.append({
                'variable': var_name,
                'boot_t': boot_t,
                'boot_pval': boot_pval,
                'boot_stars': boot_stars,
                'asymp_pval': asymp_pval,
                'asymp_pval_str': asymp_pval_str,
                'asymp_stars': asymp_stars
            })
    
    # Format table
    if table_rows:
        # Calculate column widths
        max_var_len = max(len(row['variable']) for row in table_rows)
        var_width = max(max_var_len, 8)  # minimum 8 for "Variable"
        
        # Table header
        bootstrap_section += f"{'Variable':<{var_width}}  {'Boot t-stat':>12}  {'Boot p-value':>15}  {'Asymp p-value':>16}\n"
        bootstrap_section += "─" * (var_width + 12 + 15 + 16 + 6) + "\n"
        
        # Table rows
        for row in table_rows:
            var_display = f"{row['variable']:<{var_width}}"
            boot_t_display = f"{row['boot_t']:>12.4f}"
            boot_pval_display = f"{row['boot_pval']:>11.4f} {row['boot_stars']:<3}"
            asymp_pval_display = f"{row['asymp_pval_str']:>12} {row['asymp_stars']:<3}"
            
            bootstrap_section += f"{var_display}  {boot_t_display}  {boot_pval_display}  {asymp_pval_display}\n"
        
        bootstrap_section += "\n"
    
    # Add interpretation section
    bootstrap_section += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Interpretation:
"""
    
    if is_two_way:
        other_cluster = first_valid.get("other_cluster", "")
        bootstrap_section += f"""  • Bootstrap p-values are more reliable with few clusters
  • Use bootstrap p-values (not asymptotic) for hypothesis testing
  • WCR31: Bootstrapped on {cluster_var} (G={n_clusters}), accounts for {other_cluster} correlation
  • Significance: *** p<0.001, ** p<0.01, * p<0.05
"""
    else:
        bootstrap_section += f"""  • Bootstrap p-values are more reliable with few clusters (G={n_clusters})
  • Use bootstrap p-values (not asymptotic) for hypothesis testing
  • Large differences between bootstrap and asymptotic p-values indicate small-cluster issues
  • Significance: *** p<0.001, ** p<0.01, * p<0.05
"""
    
    # Add multiple testing warning if more than one variable
    n_tested = len(table_rows)
    if n_tested > 1:
        bootstrap_section += f"""
⚠️  MULTIPLE TESTING CORRECTION REQUIRED
    You tested {n_tested} variables. Consider corrections:
    • Bonferroni: Use α = 0.05/{n_tested} = {0.05/n_tested:.4f}
    • Holm-Bonferroni: Sequential procedure (less conservative)
    • FDR: Benjamini-Hochberg for false discovery rate control
"""
    
    return bootstrap_section


def format_multi_variable_bootstrap_diagnostics(
    multi_bootstrap_results: dict
) -> str:
    """
    Format diagnostic summary for multi-variable bootstrap
    
    Parameters:
    -----------
    multi_bootstrap_results : dict
        Dictionary mapping variable names to bootstrap results
    
    Returns:
    --------
    str : Formatted diagnostic section
    """
    if not multi_bootstrap_results:
        return ""
    
    tested_vars = [k for k, v in multi_bootstrap_results.items() if v is not None]
    
    if not tested_vars:
        return ""
    
    bootstrap_summary = f"""
╔══════════════════════════════════════════════════════╗
║        MULTI-VARIABLE BOOTSTRAP SUMMARY              ║
╚══════════════════════════════════════════════════════╝

Variables tested with wild cluster bootstrap:
{chr(10).join([f'  • {var}' for var in tested_vars])}

📖 Interpretation Guide:
- These variables received bootstrap inference due to small clusters
- Use bootstrap p-values for these variables
- Other variables rely on asymptotic cluster-robust inference
- Consider multiple testing corrections when testing multiple hypotheses

"""
    
    return bootstrap_summary


def generate_multi_variable_bootstrap_code(
    cluster_var: Optional[str],
    bootstrap_variables: Optional[List[str]],
    is_two_way: bool = False,
    cluster_var_2: Optional[str] = None
) -> str:
    """
    Generate Python code for multi-variable bootstrap
    
    NEW: Supports two-way clustering with WCR31
    
    Parameters:
    -----------
    cluster_var : str or None
        Primary clustering variable name
    bootstrap_variables : list or None
        List of variables to bootstrap
    is_two_way : bool
        Whether two-way clustering is used
    cluster_var_2 : str or None
        Secondary clustering variable for two-way
    
    Returns:
    --------
    str : Python code snippet
    """
    if not cluster_var or not bootstrap_variables:
        return ""
    
    var_list_str = ', '.join([f"'{v}'" for v in bootstrap_variables])
    
    if is_two_way and cluster_var_2:
        # Two-way clustering code with WCR31
        code = f"""

# MULTI-VARIABLE WILD CLUSTER BOOTSTRAP (TWO-WAY CLUSTERING)
# Detect which dimension has fewer clusters for WCR31
n_clusters_1 = df['{cluster_var}'].nunique()
n_clusters_2 = df['{cluster_var_2}'].nunique()
print(f"Clusters in '{cluster_var}': {{n_clusters_1}}")
print(f"Clusters in '{cluster_var_2}': {{n_clusters_2}}")

min_clusters = min(n_clusters_1, n_clusters_2)

if min_clusters < 30:
    # Choose weaker clustering dimension for bootstrap
    if n_clusters_1 < n_clusters_2:
        bootstrap_cluster = '{cluster_var}'
        n_bootstrap_clusters = n_clusters_1
        other_cluster = '{cluster_var_2}'
        n_other_clusters = n_clusters_2
    else:
        bootstrap_cluster = '{cluster_var_2}'
        n_bootstrap_clusters = n_clusters_2
        other_cluster = '{cluster_var}'
        n_other_clusters = n_clusters_1
    
    print(f"\\n⚠️  Two-way clustering with small clusters detected")
    print(f"   Bootstrapping on '{{bootstrap_cluster}}' (G={{n_bootstrap_clusters}}) - SMALLER dimension")
    print(f"   Preserving correlation in '{{other_cluster}}' (G={{n_other_clusters}})")
    print(f"   Using WCR31 (bootstrap_type='31')...")
    
    # Variables to test with bootstrap
    test_variables = [{var_list_str}]
    
    bootstrap_results = {{}}
    for var_name in test_variables:
        print(f"\\nBootstrapping {{var_name}}...")
        boot_result = results.wildboottest(
            param=var_name,
            reps=9999,
            cluster=bootstrap_cluster,    # Bootstrap on SMALLER dimension
            weights_type='webb',
            impose_null=True,           
            bootstrap_type='31',          # WCR31 for two-way clustering
            seed=12345,                 
            k_adj=True,                 
            G_adj=True                  
        )
        bootstrap_results[var_name] = boot_result
        print(f"  Bootstrap p-value (WCR31): {{boot_result['Pr(>|t|)']:.4f}}")
        print(f"  Asymptotic p-value: {{results.tidy().loc[var_name, 'Pr(>|t|)']:.4f}}")
    
    print("\\n→ Use WCR31 bootstrap p-values for inference")
    print(f"→ Bootstrapped on '{{bootstrap_cluster}}' to account for correlation in '{{other_cluster}}'")
    
    # Multiple testing correction
    n_tests = len(test_variables)
    if n_tests > 1:
        print(f"\\n⚠️  Multiple Testing: Testing {{n_tests}} variables")
        print(f"   Bonferroni-adjusted α = 0.05/{{n_tests}} = {{0.05/n_tests:.4f}}")
"""
    else:
        # One-way clustering code (original)
        code = f"""

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
            bootstrap_type='11',        # Standard restricted bootstrap
            seed=12345,                 
            k_adj=True,                 
            G_adj=True                  
        )
        bootstrap_results[var_name] = boot_result
        print(f"  Bootstrap p-value: {{boot_result['Pr(>|t|)']:.4f}}")
        print(f"  Asymptotic p-value: {{results.tidy().loc[var_name, 'Pr(>|t|)']:.4f}}")
    
    print("\\n→ Use bootstrap p-values for inference with few clusters")
    
    # Multiple testing correction
    n_tests = len(test_variables)
    if n_tests > 1:
        print(f"\\n⚠️  Multiple Testing: Testing {{n_tests}} variables")
        print(f"   Bonferroni-adjusted α = 0.05/{{n_tests}} = {{0.05/n_tests:.4f}}")
        print("   Consider using Holm-Bonferroni or FDR control")
"""
    
    return code


# ═══════════════════════════════════════════════════════════════════════════
#                    BOOTSTRAP EXECUTION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


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
    
    NEW: Supports two-way clustering with bootstrap_type="31" (WCR31)
    When two-way clustering is detected, automatically identifies the dimension
    with fewer clusters and applies WCR31 to preserve correlation structure.
    
    Based on:
    - Cameron, Gelbach & Miller (2008) "Bootstrap-Based Improvements"
    - MacKinnon, Nielsen & Webb (2023) "Fast and Reliable Bootstrap"
    - Webb (2014) "Reworking Wild Bootstrap"
    
    Parameters:
    -----------
    results : pyfixest Feols object
        Estimated model results
    df_clean : pd.DataFrame
        Clean data used for estimation (must contain numeric cluster variables)
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
        Includes: variable_name, n_clusters, cluster_var, bootstrap_reps,
                 results, recommended, is_two_way, bootstrap_type
    """
    try:
        # Determine clustering structure
        is_two_way = "Two-way" in cluster_method
        
        if is_two_way:
            # Handle two-way clustering with WCR31
            if "Industry × Country" in cluster_method:
                n_clusters_1 = df_clean[industry_var].nunique() if industry_var and industry_var != "None" else 999
                n_clusters_2 = df_clean[country_var].nunique() if country_var and country_var != "None" else 999
                cluster_var_1 = "_industry_numeric"
                cluster_var_2 = "_country_numeric"
                cluster_name_1 = industry_var
                cluster_name_2 = country_var
            else:  # Firm × Year
                n_clusters_1 = df_clean[firm_id_col].nunique()
                n_clusters_2 = df_clean[year_col].nunique()
                cluster_var_1 = "_firm_id_numeric"
                cluster_var_2 = "_year_numeric"
                cluster_name_1 = firm_id_col
                cluster_name_2 = year_col
            
            min_clusters = min(n_clusters_1, n_clusters_2)
            
            # Only run bootstrap if at least one dimension has < 30 clusters
            if min_clusters < 30:
                # Identify the weaker clustering dimension
                if n_clusters_1 < n_clusters_2:
                    cluster_var_numeric = cluster_var_1
                    cluster_var_original = cluster_name_1
                    n_clusters_used = n_clusters_1
                    other_cluster = cluster_name_2
                    n_clusters_other = n_clusters_2
                else:
                    cluster_var_numeric = cluster_var_2
                    cluster_var_original = cluster_name_2
                    n_clusters_used = n_clusters_2
                    other_cluster = cluster_name_1
                    n_clusters_other = n_clusters_1
                
                print(f"🔄 Two-way clustering detected: {cluster_name_1} (G={n_clusters_1}) × {cluster_name_2} (G={n_clusters_2})")
                print(f"   Bootstrapping on '{cluster_var_original}' (smaller dimension) with WCR31...")
                
                # Verify numeric cluster variable exists
                if cluster_var_numeric not in df_clean.columns:
                    raise ValueError(f"Numeric cluster variable {cluster_var_numeric} not found in dataframe")
                
                # Adjust replications if clusters very small
                if n_clusters_used < 10:
                    max_perms = 2 ** n_clusters_used
                    if bootstrap_reps > max_perms:
                        bootstrap_reps = max_perms
                        print(f"   Using full enumeration: {max_perms} permutations")
                
                # Run WCR31: Wild cluster bootstrap with CRV3 adjustment
                # This preserves the correlation structure in the other dimension
                boot_result = results.wildboottest(
                    param=variable_name,
                    reps=bootstrap_reps,
                    cluster=cluster_var_numeric,  # Bootstrap on weaker dimension
                    weights_type="webb",
                    impose_null=True,
                    bootstrap_type="31",  # WCR31 for two-way clustering
                    seed=12345,
                    k_adj=True,
                    G_adj=True
                )
                
                return {
                    "variable_name": variable_name,
                    "n_clusters": n_clusters_used,
                    "cluster_var": cluster_var_original,
                    "bootstrap_reps": bootstrap_reps,
                    "results": boot_result,
                    "recommended": True,
                    "is_two_way": True,
                    "bootstrap_type": "31",
                    "other_cluster": other_cluster,
                    "n_clusters_other": n_clusters_other
                }
            
            return None
            
        else:
            # One-way clustering (original logic)
            if "Industry" in cluster_method and industry_var and industry_var != "None":
                n_clusters = df_clean[industry_var].nunique()
                cluster_var_numeric = "_industry_numeric"
                cluster_var_original = industry_var
            elif "Country" in cluster_method and country_var and country_var != "None":
                n_clusters = df_clean[country_var].nunique()
                cluster_var_numeric = "_country_numeric"
                cluster_var_original = country_var
            else:
                n_clusters = df_clean[firm_id_col].nunique()
                cluster_var_numeric = "_firm_id_numeric"
                cluster_var_original = firm_id_col
            
            # Run bootstrap only if clusters < 30
            if n_clusters < 30:
                print(f"🔄 Running wild cluster bootstrap for '{variable_name}' with {n_clusters} clusters...")
                
                # Adjust bootstrap replications if clusters very small
                if n_clusters < 10:
                    max_perms = 2 ** n_clusters
                    if bootstrap_reps > max_perms:
                        bootstrap_reps = max_perms
                        print(f"   Using full enumeration: {max_perms} permutations")
                
                # Verify numeric cluster variable exists
                if cluster_var_numeric not in df_clean.columns:
                    raise ValueError(f"Numeric cluster variable {cluster_var_numeric} not found in dataframe")
                
                print(f"   Using numeric cluster variable '{cluster_var_numeric}'...")
                
                # Run standard wild cluster bootstrap (type "11")
                boot_result = results.wildboottest(
                    param=variable_name,
                    reps=bootstrap_reps,
                    cluster=cluster_var_numeric,
                    weights_type="webb",
                    impose_null=True,
                    bootstrap_type="11",  # Standard restricted bootstrap
                    seed=12345,
                    k_adj=True,
                    G_adj=True
                )
                
                return {
                    "variable_name": variable_name,
                    "n_clusters": n_clusters,
                    "cluster_var": cluster_var_original,
                    "bootstrap_reps": bootstrap_reps,
                    "results": boot_result,
                    "recommended": True,
                    "is_two_way": False,
                    "bootstrap_type": "11"
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
    
    NEW: Supports two-way clustering with automatic WCR31 application
    
    Parameters:
    -----------
    results : pyfixest Feols object
        Estimated model results
    df_clean : pd.DataFrame
        Clean data with numeric cluster variables
    firm_id_col, year_col : str
        ID columns
    cluster_method : str
        Clustering method
    country_var, industry_var : Optional[str]
        Additional clustering dimensions
    selected_variables : List[str]
        Variables to bootstrap
    bootstrap_reps : int
        Number of replications
    
    Returns:
    --------
    Dict[str, Optional[Dict]] : Dictionary mapping variable names to bootstrap results
    """
    bootstrap_results = {}
    
    for var_name in selected_variables:
        result = run_wild_bootstrap_for_variable(
            results, df_clean, firm_id_col, year_col, cluster_method,
            country_var, industry_var, var_name, bootstrap_reps
        )
        bootstrap_results[var_name] = result
    
    return bootstrap_results
