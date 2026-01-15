"""
Stepwise Regression Report Module
Generates progressive model specifications for panel data analysis

This module creates a series of nested models that progressively add:
1. Independent variable only
2. All control variables at once
3. Year fixed effects
4. Interaction terms
5. Lagged dependent variables

Author: Saiyidi MAT RONI
Date: December 25, 2025
"""

import pyfixest as pf
import pandas as pd
from typing import List, Dict, Tuple, Optional
from io import StringIO
import sys


def determine_vcov(cluster_method: str, firm_id: str, year: str, 
                   industry_var: Optional[str] = None, 
                   country_var: Optional[str] = None) -> dict:
    """
    Determine vcov specification based on clustering method
    
    Parameters:
    -----------
    cluster_method : str
        Clustering method selected by user
    firm_id : str
        Firm ID column name
    year : str
        Year column name
    industry_var : str, optional
        Industry variable name
    country_var : str, optional
        Country variable name
    
    Returns:
    --------
    dict or str : vcov specification for pyfixest
    """
    
    # One-way firm clustering
    if cluster_method == "One-way (Firm only) with CRV1":
        return {'CRV1': firm_id}
    elif cluster_method == "One-way (Firm only) with CRV3":
        return {'CRV3': firm_id}
    
    # One-way industry clustering
    elif cluster_method == "One-way (Industry) with CRV1":
        return {'CRV1': industry_var}
    elif cluster_method == "One-way (Industry) with CRV3":
        return {'CRV3': industry_var}
    
    # One-way country clustering
    elif cluster_method == "One-way (Country) with CRV1":
        return {'CRV1': country_var}
    elif cluster_method == "One-way (Country) with CRV3":
        return {'CRV3': country_var}
    
    # Two-way firm × year clustering
    elif cluster_method == "Two-way (Firm × Year) with CRV1":
        return {'CRV1': f"{firm_id} + {year}"}
    elif cluster_method == "Two-way (Firm × Year) with CRV3":
        return {'CRV3': f"{firm_id} + {year}"}
    
    # Two-way industry × country clustering
    elif cluster_method == "Two-way (Industry × Country) with CRV1":
        return {'CRV1': f"{industry_var} + {country_var}"}
    elif cluster_method == "Two-way (Industry × Country) with CRV3":
        return {'CRV3': f"{industry_var} + {country_var}"}
    
    # Robust (heteroskedasticity only)
    elif cluster_method == "Robust (Heteroskedasticity only)":
        return 'hetero'
    
    # Default: Firm clustering with CRV1
    else:
        return {'CRV1': firm_id}


def generate_progressive_models(df_clean: pd.DataFrame, params: dict) -> Tuple[List, List[str]]:
    """
    Generate progressive model specifications with controls added all at once
    
    Progression:
    1. Independent variable only (+ firm FE)
    2. Independent variable + ALL controls (+ firm FE)
    3. Independent variable + ALL controls (+ firm FE + year FE)
    4. Add interaction term (if specified)
    5. Add lagged dependent variables (if specified)
    
    Parameters:
    -----------
    df_clean : pd.DataFrame
        Cleaned data used for estimation
    params : dict
        Dictionary containing all model parameters
    
    Returns:
    --------
    tuple : (fits, model_labels)
        - fits: List of fitted pyfixest models
        - model_labels: List of model descriptions
    """
    
    # Extract parameters
    dv = params['dependent_var']
    iv = params['independent_var']
    controls = params['control_vars'] if params['control_vars'] else []
    firm_id = params['firm_id_col']
    year = params['year_col']
    include_year_fe = params['include_year_fe']
    moderator = params.get('moderator_var', None)
    include_interaction = params.get('include_interaction', False)
    cluster_method = params['cluster_method']
    industry_var = params.get('industry_var', None)
    country_var = params.get('country_var', None)
    include_lag_dv = params.get('include_lag_dv', False)
    lag_min = params.get('lag_min', None)
    lag_max = params.get('lag_max', None)
    
    # Determine vcov
    vcov = determine_vcov(cluster_method, firm_id, year, industry_var, country_var)
    
    # Storage for models and labels
    fits = []
    model_labels = []
    
    # MODEL 1: Independent variable only (baseline)
    formula1 = f"{dv} ~ {iv} | {firm_id}"
    try:
        fit1 = pf.feols(formula1, data=df_clean, vcov=vcov, demeaner_backend="rust")
        fits.append(fit1)
        model_labels.append("Model 1: IV only")
    except Exception as e:
        print(f"Warning: Model 1 failed: {str(e)}")
    
    # MODEL 2: Add ALL controls at once
    if controls:
        vars_with_controls = [iv] + controls
        formula2 = f"{dv} ~ {' + '.join(vars_with_controls)} | {firm_id}"
        try:
            fit2 = pf.feols(formula2, data=df_clean, vcov=vcov, demeaner_backend="rust")
            fits.append(fit2)
            model_labels.append("Model 2: IV + Controls")
        except Exception as e:
            print(f"Warning: Model 2 failed: {str(e)}")
    
    # MODEL 3: Add year fixed effects (if requested)
    if include_year_fe:
        vars_all = [iv] + controls
        formula3 = f"{dv} ~ {' + '.join(vars_all)} | {firm_id} + {year}"
        try:
            fit3 = pf.feols(formula3, data=df_clean, vcov=vcov, demeaner_backend="rust")
            fits.append(fit3)
            model_labels.append("Model 3: + Year FE")
        except Exception as e:
            print(f"Warning: Model 3 failed: {str(e)}")
    
    # MODEL 4: Add interaction term (if specified)
    if moderator and moderator != "None" and include_interaction:
        vars_with_interaction = [iv] + controls + [f"{iv}_x_{moderator}"]
        fe = f"{firm_id} + {year}" if include_year_fe else firm_id
        formula4 = f"{dv} ~ {' + '.join(vars_with_interaction)} | {fe}"
        try:
            fit4 = pf.feols(formula4, data=df_clean, vcov=vcov, demeaner_backend="rust")
            fits.append(fit4)
            model_labels.append("Model 4: + Interaction")
        except Exception as e:
            print(f"Warning: Model 4 failed: {str(e)}")
    
    # MODEL 5: Add lagged dependent variables (if specified)
    if include_lag_dv and lag_min is not None and lag_max is not None:
        # Build lag variable names
        lag_vars = []
        for lag in range(lag_min, lag_max + 1):
            lag_vars.append(f"{dv}_lag{lag}")
        
        # Check if lag variables exist in dataframe
        lag_vars_exist = all(lv in df_clean.columns for lv in lag_vars)
        
        if lag_vars_exist:
            # Build variables list with lags
            vars_with_lags = [iv] + controls
            if moderator and moderator != "None" and include_interaction:
                vars_with_lags.append(f"{iv}_x_{moderator}")
            vars_with_lags.extend(lag_vars)
            
            fe = f"{firm_id} + {year}" if include_year_fe else firm_id
            formula5 = f"{dv} ~ {' + '.join(vars_with_lags)} | {fe}"
            try:
                fit5 = pf.feols(formula5, data=df_clean, vcov=vcov, demeaner_backend="rust")
                fits.append(fit5)
                model_labels.append("Model 5: + Lags")
            except Exception as e:
                print(f"Warning: Model 5 failed: {str(e)}")
        else:
            print(f"Warning: Lagged variables not found in dataframe. Skipping Model 5.")
    
    return fits, model_labels


def generate_etable_text(fits: List, model_labels: List[str] = None) -> str:
    """
    Generate pyfixest etable and return as text with proper formatting
    
    Parameters:
    -----------
    fits : list
        List of fitted pyfixest models
    model_labels : list, optional
        List of model descriptions
    
    Returns:
    --------
    str : Formatted etable as text
    """
    
    if not fits:
        return "No models were successfully estimated."
    
    try:
        # DIAGNOSTIC: Try multiple approaches to capture etable
        
        # Approach 1: Try to get HTML output for IPython-style display
        try:
            table_html = pf.etable(
                fits,
                coef_fmt="b (se)",
                signif_code=[0.001, 0.01, 0.05],
                type="html"  # Try HTML output
            )
            if table_html:
                print(f"DEBUG: Got HTML table, length: {len(table_html)}")
                # Add model labels
                if model_labels and len(model_labels) == len(fits):
                    header = "Model Progression:\n"
                    for i, label in enumerate(model_labels, 1):
                        header += f"  ({i}) {label}\n"
                    return header + "\n\nHTML OUTPUT:\n" + table_html
        except Exception as e:
            print(f"DEBUG: HTML approach failed: {str(e)}")
        
        # Approach 2: Capture stdout (original approach)
        buffer = StringIO()
        sys.stdout = buffer
        
        pf.etable(
            fits,
            coef_fmt="b (se)",
            signif_code=[0.001, 0.01, 0.05]
        )
        
        sys.stdout = sys.__stdout__
        etable_text = buffer.getvalue()
        
        print(f"DEBUG: Captured text length: {len(etable_text)}")
        print(f"DEBUG: First 200 chars: {etable_text[:200]}")
        
        # Add model labels header if provided
        if model_labels and len(model_labels) == len(fits):
            header = "Model Progression:\n"
            for i, label in enumerate(model_labels, 1):
                header += f"  ({i}) {label}\n"
            return header + "\n" + etable_text
        
        return etable_text if etable_text else "ERROR: No table output captured"
    
    except Exception as e:
        sys.stdout = sys.__stdout__
        return f"Error generating etable: {str(e)}\n\nDEBUG: Number of models: {len(fits)}"


def generate_stepwise_report(stored_results, stored_df, stored_params) -> str:
    """
    Generate complete stepwise regression report
    
    This is the main function to call from Gradio interface
    
    Parameters:
    -----------
    stored_results : pyfixest Feols object
        Original fitted model from main analysis
    stored_df : pd.DataFrame
        Cleaned dataframe used in analysis
    stored_params : dict
        Dictionary containing all model parameters
    
    Returns:
    --------
    str : Formatted report with progressive model specifications
    """
    
    if stored_results is None or stored_df is None or stored_params is None:
        return "❌ No results available. Please run the analysis first."
    
    try:
        # Generate progressive models
        fits, model_labels = generate_progressive_models(stored_df, stored_params)
        
        if not fits:
            return "❌ Error: No models could be estimated. Please check your data and specifications."
        
        # Generate etable
        etable_text = generate_etable_text(fits, model_labels)
        
        # Build complete report
        report = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    STEPWISE REGRESSION REPORT                             ║
║                  Progressive Model Specifications                         ║
╚═══════════════════════════════════════════════════════════════════════════╝

**Analysis Strategy**: Controls added all at once (not one-by-one)

**Clustering Method**: {stored_params['cluster_method']}
**Number of Models Estimated**: {len(fits)}

───────────────────────────────────────────────────────────────────────────

```
{etable_text}
```

───────────────────────────────────────────────────────────────────────────

📊 **Interpretation Guidelines**:

1. **Model Stability**: Compare coefficients across models
   - If coefficient changes dramatically, investigate omitted variable bias
   - Stable coefficients suggest robust relationship

2. **R-squared Progression**: Should increase (or stay similar) as models become more complex
   - Large jumps indicate important controls
   - Decreases may signal overfitting or multicollinearity

3. **Year Fixed Effects**: Model 3 controls for time-varying common shocks
   - Compare Model 2 vs Model 3 to see impact of time effects
   - Year FE absorbs macro trends, policy changes, etc.

4. **Interaction Terms**: Model 4 tests if effect varies by moderator
   - Check if main effect and interaction are jointly significant
   - Interpret carefully with centering of variables

5. **Statistical Significance**:
   - Use cluster-robust standard errors (already applied)
   - Consider multiple testing corrections if testing many hypotheses
   - Bootstrap p-values reported separately (if applicable)

⚠️ **Important Notes**:
- All models use the same clustering specification
- Fixed effects (firm) included in all models
- Sample size should be constant across models (check N)
- Compare nested models using adjusted R-squared or information criteria

📚 **References**:
- Wooldridge (2010) "Econometric Analysis of Cross Section and Panel Data"
- Angrist & Pischke (2009) "Mostly Harmless Econometrics"
- Cameron & Miller (2015) "A Practitioner's Guide to Cluster-Robust Inference"

"""
        
        return report
    
    except Exception as e:
        return f"❌ Error generating stepwise report:\n\n{str(e)}"


def export_stepwise_models_for_word(stored_results, stored_df, stored_params) -> Tuple[List, str]:
    """
    Generate progressive models for Word document export
    
    Returns both the fitted models and formatted table for export module
    
    Parameters:
    -----------
    stored_results : pyfixest Feols object
        Original fitted model
    stored_df : pd.DataFrame
        Cleaned dataframe
    stored_params : dict
        Model parameters
    
    Returns:
    --------
    tuple : (fits, etable_text)
        - fits: List of fitted models
        - etable_text: Formatted table as string
    """
    
    if stored_results is None or stored_df is None or stored_params is None:
        return [], "No results available"
    
    try:
        fits, model_labels = generate_progressive_models(stored_df, stored_params)
        etable_text = generate_etable_text(fits, model_labels)
        return fits, etable_text
    
    except Exception as e:
        return [], f"Error: {str(e)}"
