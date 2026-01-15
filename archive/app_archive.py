"""
Panel Data Analysis App with pyfixest
Analysing panel data with pooled OLS, random and fixed effects models
Refactored to use pyfixest instead of linearmodels and statsmodels
Author: Saiyidi MAT RONI (Modified to use pyfixest)
Date: December 20, 2025
"""

import gradio as gr
import pandas as pd
import numpy as np
import pyfixest as pf
import traceback
from typing import Optional, List, Tuple
import warnings
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
    cluster_method: str = "Two-way (Firm × Year) with CRV3",
    country_var: Optional[str] = None,
    include_lag_dv: bool = False,
    lag_min: Optional[int] = None,
    lag_max: Optional[int] = None
) -> Tuple[str, str, str]:
    """
    Run Fixed Effects (Within) Model with firm and optionally year fixed effects using pyfixest
    """
    try:
        # Prepare panel data
        df_clean = df[[firm_id_col, year_col, dependent_var, independent_var] + control_vars].copy()
        
        # Sort by firm and year for proper lagging
        df_clean = df_clean.sort_values([firm_id_col, year_col])
        
        # Add country if clustering by country
        if "Country" in cluster_method and country_var and country_var != "None":
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
        
        # Set up clustering based on method chosen
        # Default: Two-way clustering with CRV1 (faster computation)
        if cluster_method == "Two-way (Firm × Year) with CRV3":
            # Multi-way clustering with small-cluster correction
            vcov = {'CRV3': f"{firm_id_col} + {year_col}"}
        elif cluster_method == "Two-way (Firm × Year) with CRV1":
            # Multi-way clustering without correction (faster)
            vcov = {'CRV1': f"{firm_id_col} + {year_col}"}
        elif cluster_method == "One-way (Firm only) with CRV3":
            # Traditional firm clustering with small-cluster correction
            vcov = {'CRV3': firm_id_col}
        elif cluster_method == "One-way (Firm only) with CRV1":
            # Traditional firm clustering
            vcov = {'CRV1': firm_id_col}
        elif cluster_method == "One-way (Country) with CRV3" and country_var and country_var != "None":
            # Country-level clustering with correction (for country-level DiD)
            vcov = {'CRV3': country_var}
        elif cluster_method == "One-way (Country) with CRV1" and country_var and country_var != "None":
            # Country-level clustering without correction
            vcov = {'CRV1': country_var}
        elif cluster_method == "Robust (Heteroskedasticity only)":
            # Robust SE without clustering
            vcov = 'hetero'
        else:
            # Default to two-way CRV1 (faster) if invalid choice
            vcov = {'CRV1': f"{firm_id_col} + {year_col}"}
        
        # Estimate model with pyfixest (using Rust backend for faster computation)
        results = pf.feols(formula, data=df_clean, vcov=vcov, demeaner_backend="rust")
        
        # Format results
        results_summary = format_fe_results_pyfixest(results, dependent_var, independent_var, 
                                           include_year_fe, moderator_var, include_interaction,
                                           df_clean, firm_id_col, year_col, cluster_method, country_var)
        
        # Diagnostics
        diagnostics = format_diagnostics_pyfixest(results, df_clean, firm_id_col, year_col, cluster_method, country_var)
        
        # Code snippet
        code = generate_code_snippet_pyfixest(firm_id_col, year_col, dependent_var, independent_var,
                                     control_vars, include_year_fe, moderator_var, include_interaction, cluster_method)
        
        return results_summary, diagnostics, code
    
    except Exception as e:
        error_msg = f"❌ Error in Fixed Effects estimation:\n\n{str(e)}\n\n{traceback.format_exc()}"
        return error_msg, "", ""


def format_fe_results_pyfixest(results, dependent_var, independent_var, include_year_fe, 
                     moderator_var, include_interaction, df_clean, firm_id_col, year_col,
                     cluster_method="Two-way (Firm × Year) with CRV3", country_var=None):
    """Format Fixed Effects results from pyfixest in a readable table"""
    
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
    
    # Get model statistics from pyfixest Feols object
    # In pyfixest, R-squared values are stored differently
    r2 = results._r2_overall if hasattr(results, '_r2_overall') else getattr(results, '_r2', 0)
    r2_within = results._r2_within if hasattr(results, '_r2_within') else r2
    f_stat = results._f_statistic['statistic'] if hasattr(results, '_f_statistic') and results._f_statistic else "N/A"
    
    # Convert tidy() dataframe to string for display
    coef_table = coef_df.to_string(index=False)
    
    output = f"""
╔═══════════════════════════════════════════════════════════════════╗
║                FIXED EFFECTS REGRESSION RESULTS                   ║
║                       (using pyfixest)                            ║
╚═══════════════════════════════════════════════════════════════════╝

Model: Panel data fixed effects
Dependent Variable: {dependent_var}
Key Independent Variable: {independent_var}
{'Year Fixed Effects: ✓ Included' if include_year_fe else 'Year Fixed Effects: ✗ Not Included'}
Clustering Method: {cluster_method}

{coef_table}

Panel Structure:
  • Observations: {n_obs:,}
  • Firms: {n_firms:,}
  • Time periods: {n_years}
  • Avg obs per firm: {n_obs/n_firms:.1f}

Model Fit:
  • R² (within): {r2_within:.4f}
  • R² (overall): {r2:.4f}
  • F-statistic: {f_stat}

───────────────────────────────────────────────────────────────────────
📊 INTERPRETATION:
"""
    
    # Add interpretation
    # Use the coefficient name column that was determined earlier
    main_row = coef_df[coef_df[coef_name_col] == independent_var]
    if not main_row.empty:
        main_coef = main_row['Estimate'].values[0]
        main_pval = main_row['Pr(>|t|)'].values[0]
        
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
    
    return output


def format_diagnostics_pyfixest(results, df_clean, firm_id_col, year_col, cluster_method="Two-way (Firm × Year) with CRV3", country_var=None):
    """Generate diagnostic information for pyfixest results"""
    
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
    else:
        cluster_text = f'✓ {cluster_method}'
        cluster_count_text = f'   Clusters: {cluster_description}'
        
        # Assess cluster adequacy based on Cameron, Gelbach & Miller (2011)
        if min_clusters >= 50:
            cluster_adequacy = f"✓ {min_clusters} clusters is adequate for asymptotic inference"
        elif min_clusters >= 30:
            if uses_crv3:
                cluster_adequacy = f"✓ {min_clusters} clusters with CRV3 correction is acceptable"
            else:
                cluster_adequacy = f"⚠️ {min_clusters} clusters - CRV3 correction recommended"
        elif min_clusters >= 20:
            if uses_crv3:
                cluster_adequacy = f"⚠️ {min_clusters} clusters is limited; CRV3 helps but inference still uncertain"
            else:
                cluster_adequacy = f"❌ {min_clusters} clusters too few - MUST use CRV3 or wild bootstrap"
        else:
            cluster_adequacy = f"❌ {min_clusters} clusters critically low - consider wild cluster bootstrap"
    
    output = f"""
╔══════════════════════════════════════════════════════════════════╗
║                     DIAGNOSTIC TESTS                             ║
╚══════════════════════════════════════════════════════════════════╝

Panel Structure:
  {balance_status} Panel is {balance_text}
{balance_detail}

Clustering Specification:
  {cluster_text}
{'  ' + cluster_count_text if cluster_count_text else ''}
  {cluster_adequacy}

🎯 Why This Matters:
  • Multi-way clustering accounts for correlation within firms AND years
  • One-way (firm) clustering ignores correlation from macro/time shocks
  • CRV3 correction adjusts for small-cluster bias (more conservative)
  • Rule of thumb: Use CRV3 when clusters < 50 in any dimension

Model Diagnostics:
  • Number of observations: {n_obs}
  • Degrees of freedom: {results._N - results._k if hasattr(results, '_N') and hasattr(results, '_k') else 'N/A'}

⚠️ Important Notes:
  • Industry and country effects are absorbed into firm fixed effects
  • Cannot separately estimate time-invariant variables in this model
  • pyfixest provides efficient estimation for high-dimensional fixed effects
  • Use Two-Step method to explore between-firm differences
"""
    
    return output


def generate_code_snippet_pyfixest(firm_id_col, year_col, dependent_var, independent_var,
                         control_vars, include_year_fe, moderator_var, include_interaction, cluster_method):
    """Generate reproducible Python code using pyfixest"""
    
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
    if "Two-way" in cluster_method and "CRV3" in cluster_method:
        vcov_code = f"vcov = {{'CRV3': '{firm_id_col} + {year_col}'}}  # Multi-way with small-cluster correction"
    elif "Two-way" in cluster_method and "CRV1" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': '{firm_id_col} + {year_col}'}}  # Multi-way clustering"
    elif "Firm only" in cluster_method and "CRV3" in cluster_method:
        vcov_code = f"vcov = {{'CRV3': '{firm_id_col}'}}  # One-way with correction"
    elif "Firm only" in cluster_method and "CRV1" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': '{firm_id_col}'}}  # Traditional firm clustering"
    elif "Country" in cluster_method and "CRV3" in cluster_method:
        vcov_code = f"vcov = {{'CRV3': 'country_var'}}  # Country-level with correction"
    elif "Country" in cluster_method and "CRV1" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': 'country_var'}}  # Country-level clustering"
    else:
        vcov_code = "vcov = 'hetero'  # Robust SE only"
    
    code = f"""
# Reproducible Panel Data Analysis with pyfixest
# Fixed Effects Model with Firm and Year Fixed Effects

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
        
        # Set up clustering (same logic as FE model)
        if cluster_method == "Two-way (Firm × Year) with CRV3":
            vcov = {'CRV3': [firm_id_col, year_col]}
        elif cluster_method == "Two-way (Firm × Year) with CRV1":
            vcov = {'CRV1': [firm_id_col, year_col]}
        elif cluster_method == "One-way (Firm only) with CRV3":
            vcov = {'CRV3': firm_id_col}
        elif cluster_method == "One-way (Firm only) with CRV1":
            vcov = {'CRV1': firm_id_col}
        elif cluster_method == "One-way (Country) with CRV3" and country_var and country_var != "None":
            vcov = {'CRV3': country_var}
        elif cluster_method == "One-way (Country) with CRV1" and country_var and country_var != "None":
            vcov = {'CRV1': country_var}
        elif cluster_method == "Robust (Heteroskedasticity only)":
            vcov = 'hetero'
        else:
            vcov = {'CRV3': [firm_id_col, year_col]}
        
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
        
        return results_summary, diagnostics, code
    
    except Exception as e:
        error_msg = f"❌ Error in Pooled OLS estimation:\n\n{str(e)}\n\n{traceback.format_exc()}"
        return error_msg, "", ""


def format_pooled_results_pyfixest(results, dependent_var, independent_var, include_year_fe,
                         moderator_var, include_interaction, df_clean, industry_var, country_var):
    """Format Pooled OLS results from pyfixest"""
    
    n_obs = len(df_clean)
    
    # Get coefficient summary using pyfixest tidy()
    coef_df = results.tidy()
    
    # Convert tidy() dataframe to string for display
    coef_table = coef_df.to_string(index=False)
    
    # Get R-squared values (use same approach as FE function)
    r2 = results._r2_overall if hasattr(results, '_r2_overall') else getattr(results, '_r2', 0)
    r2_adj = results._r2_adj if hasattr(results, '_r2_adj') else "N/A"
    
    output = f"""
╔══════════════════════════════════════════════════════════════════╗
║                POOLED OLS REGRESSION RESULTS                     ║
║                      (using pyfixest)                            ║
╚══════════════════════════════════════════════════════════════════╝

Model: Pooled OLS with Dummy Variables
Dependent Variable: {dependent_var}
Key Independent Variable: {independent_var}
{'Year Fixed Effects: ✓ Included' if include_year_fe else 'Year Fixed Effects: ✗ Not Included'}
{'Industry Dummies: ✓ Included' if industry_var and industry_var != "None" else ''}
{'Country Dummies: ✓ Included' if country_var and country_var != "None" else ''}

{coef_table}

Model Fit:
  • Observations: {n_obs:,}
  • R²: {r2:.4f}
  • Adjusted R²: {r2_adj}

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
        vcov_code = f"vcov = {{'CRV3': ['{firm_id_col}', '{year_col}']}}  # Multi-way with correction"
    elif "Two-way" in cluster_method and "CRV1" in cluster_method:
        vcov_code = f"vcov = {{'CRV1': ['{firm_id_col}', '{year_col}']}}  # Multi-way clustering"
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
    lag_max
):
    """
    Main analysis function that routes to appropriate estimation method
    """
    if file is None:
        return "⚠️ Please upload a CSV file", "", ""
    
    if not all([firm_id_col, year_col, dependent_var, independent_var]):
        return "⚠️ Please specify all required variables (Firm ID, Year, Dependent, Independent)", "", ""
    
    # Validate lag parameters
    if include_lag_dv:
        try:
            lag_min_int = int(lag_min)
            lag_max_int = int(lag_max)
            
            if lag_min_int < 1 or lag_max_int < 1:
                return "❌ Lag values must be at least 1", "", ""
            
            if lag_min_int > lag_max_int:
                return "❌ Minimum lag cannot be greater than maximum lag", "", ""
            
            if lag_max_int > 10:
                return "❌ Maximum lag is limited to 10 periods", "", ""
        except (ValueError, TypeError):
            return "❌ Invalid lag values. Please enter valid integers.", "", ""
    else:
        lag_min_int = None
        lag_max_int = None
    
    try:
        # Load data
        df, status = load_and_validate_data(file.name)
        if df is None:
            return status, "", ""
        
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
                return message, "", ""
            
            elif pct_insufficient > 50:
                message = f"""❌ More than 50% of firms would be dropped!

💡 Reduce maximum lag to {max(0, min_periods - 1)}
"""
                return message, "", ""
        
        # Route to appropriate method
        if method == "Fixed Effects (Firm + Year)":
            return run_fixed_effects_model(
                df, firm_id_col, year_col, dependent_var, independent_var,
                control_vars if control_vars else [], include_year_fe,
                moderator_var, include_interaction, cluster_method, country_var,
                include_lag_dv, lag_min_int, lag_max_int
            )
        
        elif method == "Pooled OLS (with Industry/Country Dummies)":
            return run_pooled_ols_model(
                df, firm_id_col, year_col, dependent_var, independent_var,
                control_vars if control_vars else [], include_year_fe,
                moderator_var, include_interaction, industry_var, country_var,
                cluster_method, include_lag_dv, lag_min_int, lag_max_int
            )
        
        else:
            return f"⚠️ Method '{method}' is not yet implemented with pyfixest. Currently available: Fixed Effects and Pooled OLS.", "", ""
    
    except Exception as e:
        error_msg = f"❌ Unexpected error:\n\n{str(e)}\n\n{traceback.format_exc()}"
        return error_msg, "", ""


# ═══════════════════════════════════════════════════════════════════════════
#                            GRADIO INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

with gr.Blocks(title="Panel Data Analyzer with pyfixest") as demo:
    
    gr.Markdown("""
    # 📊 Panel Data Analysis Tool (pyfixest Edition)
    ### Fixed Effects and Pooled OLS using pyfixest
    
    **Status**: ✅ Core Methods Implemented | Fixed Effects • Pooled OLS
    **Note**: Using pyfixest for efficient high-dimensional fixed effects estimation
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
                    label="Key Independent Variable (X)",
                    info="Main explanatory variable (e.g., emission, R&D)"
                )
                control_checkbox = gr.CheckboxGroup(
                    choices=[],
                    value=[],
                    label="Control Variables",
                    info="Select time-varying control variables"
                )
            
            with gr.Group():
                gr.Markdown("**Time-Invariant Variables** (Optional)")
                industry_dropdown = gr.Dropdown(
                    choices=[],
                    value="None",
                    label="Industry Variable",
                    info="For Pooled OLS; absorbed in FE"
                )
                country_dropdown = gr.Dropdown(
                    choices=[],
                    value="None",
                    label="Country Variable",
                    info="For Pooled OLS; absorbed in FE"
                )
        
        with gr.Column(scale=1):
            gr.Markdown("## ⚙️ Step 3: Choose Method")
            
            method = gr.Radio(
                choices=[
                    "Fixed Effects (Firm + Year)",
                    "Pooled OLS (with Industry/Country Dummies)"
                ],
                value="Fixed Effects (Firm + Year)",
                label="Estimation Method"
            )
            
            with gr.Accordion("📚 Method Descriptions", open=False):
                gr.Markdown("""
                **✅ Fixed Effects (Implemented with pyfixest)**
                - Within-firm changes over time
                - Controls for ALL time-invariant firm traits
                - Industry/country absorbed into firm effects
                - Most rigorous for causal inference
                - Efficient estimation with pyfixest
                
                **✅ Pooled OLS (Implemented with pyfixest)**
                - Includes industry/country dummies directly
                - Assumes no unobserved heterogeneity
                - ⚠️ USE WITH CAUTION - likely biased in panel data
                - Always compare with FE models
                
                **Note**: Random Effects and Two-Step methods can be added if needed.
                pyfixest focuses on efficient Fixed Effects estimation.
                """)
            
            gr.Markdown("---")
            gr.Markdown("## 🎛️ Step 4: Specifications")
            
            include_year_fe = gr.Checkbox(
                label="Include Year Fixed Effects",
                value=True,
                info="✓ Recommended - controls for common time shocks"
            )
            
            cluster_method = gr.Dropdown(
                choices=[
                    "Two-way (Firm × Year) with CRV3",
                    "Two-way (Firm × Year) with CRV1",
                    "One-way (Firm only) with CRV3",
                    "One-way (Firm only) with CRV1",
                    "One-way (Country) with CRV3",
                    "One-way (Country) with CRV1",
                    "Robust (Heteroskedasticity only)"
                ],
                value="Two-way (Firm × Year) with CRV3",
                label="Clustering Method",
                info="✅ Two-way CRV3 is the recommended default for panel data"
            )
            
            with gr.Accordion("📚 Clustering Guide: When to Use Each Method", open=False):
                gr.Markdown("""
                ### 🎯 Recommended Default: Two-way (Firm × Year) with CRV3
                
                **Why Two-Way Clustering?**
                - Allows correlation within firms over time
                - Allows correlation across firms in same year (macro shocks, policy changes)
                - Prevents "double-counting" of information
                
                **Why CRV3 (vs CRV1)?**
                - CRV3 = Small-cluster correction (more conservative)
                - Use when clusters < 50 in any dimension
                - CRV1 = Standard asymptotic (assumes many clusters)
                
                ---
                
                ### 📖 Decision Guide
                
                | Situation | Recommended Method |
                |-----------|---------------------|
                | Panel data with year FE | **Two-way CRV3** ✅ |
                | Many firms (>50), many years (>50) | Two-way CRV1 acceptable |
                | Few years (<20) | **Two-way CRV3** (critical) |
                | Country-level DiD | Country CRV3 |
                | No time/macro shocks expected | One-way Firm CRV3 |
                | Extremely small clusters (<10) | Consider wild bootstrap* |
                
                *Wild cluster bootstrap not yet implemented - use CRV3 as best available option
                
                ---
                
                ### 🚨 Common Mistakes to Avoid
                
                ❌ **Using one-way clustering when you have year fixed effects**
                   → Ignores correlation from common time shocks
                   → Standard errors too small → false significance
                
                ❌ **Using CRV1 with few clusters (<30)**
                   → Downward-biased standard errors
                   → Use CRV3 instead
                
                ❌ **No clustering at all in panel data**
                   → Assumes independence across firms and time
                   → Almost always wrong in practice
                
                ---
                
                ### 📚 Academic References
                
                - Cameron, Gelbach & Miller (2011) - Multi-way clustering
                - Petersen (2009) - Standard errors in finance panels
                - Imbens & Kolesár (2016) - Small-cluster corrections
                """)
            
            with gr.Group():
                gr.Markdown("**Moderating Variable (Interaction Term)** - Optional")
                moderator_dropdown = gr.Dropdown(
                    choices=[],
                    value="None",
                    label="Moderator Variable",
                    info="Variable that may change the effect of X on Y"
                )
                include_interaction = gr.Checkbox(
                    label="Include Interaction Term (X × Moderator)",
                    value=False,
                    info="Tests if the moderator changes the X→Y relationship"
                )
            
            gr.Markdown("---")
            analyze_btn = gr.Button("🚀 Run Analysis", variant="primary", size="lg")
    
    gr.Markdown("---")
    gr.Markdown("## 📈 Results")
    
    with gr.Tabs():
        with gr.Tab("📊 Regression Output"):
            results_output = gr.Textbox(
                label="Estimation Results",
                lines=30,
                max_lines=50
            )
        
        with gr.Tab("🔍 Diagnostics"):
            diagnostics_output = gr.Textbox(
                label="Model Diagnostics",
                lines=15,
                max_lines=15
            )
        
        with gr.Tab("💻 Python Code"):
            code_output = gr.Code(
                label="Reproducible Code",
                language="python",
                lines=20,
                max_lines=20
            )
    
    with gr.Row():
        gr.Markdown("""
        ### 📖 Implementation Status
        
        **✅ IMPLEMENTED WITH PYFIXEST**
        
        **Core Methods:**
        - ✅ Fixed Effects (Firm + Year) with clustered SE
        - ✅ Pooled OLS with industry/country dummies
        
        **Features:**
        - ✅ Interaction terms with moderating variables
        - ✅ Dynamic variable selection from uploaded data
        - ✅ Lagged dependent variables support
        - ✅ Comprehensive diagnostics for each method
        - ✅ Reproducible Python code generation
        - ✅ Efficient high-dimensional fixed effects (pyfixest specialty)
        
        **About pyfixest:**
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
    
    analyze_btn.click(
        fn=analyze_panel_data,
        inputs=[
            file_input, firm_id_dropdown, year_dropdown, dependent_dropdown, independent_dropdown,
            control_checkbox, method, include_year_fe, cluster_method,
            moderator_dropdown, include_interaction, industry_dropdown, country_dropdown,
            include_lag_dv, lag_min, lag_max
        ],
        outputs=[results_output, diagnostics_output, code_output]
    )
    
    gr.Markdown("""
    ---
    **⚠️ Important Notes**
    - This tool uses pyfixest for efficient panel data estimation
    - Fixed Effects is the recommended method for most panel data applications
    - Always validate results and check assumptions
    - pyfixest is particularly efficient for high-dimensional fixed effects
    """)

if __name__ == "__main__":
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860, inbrowser=True)
