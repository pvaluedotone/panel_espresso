"""
Test script to identify performance issues in panel data analysis
Tests with the actual data configuration from the app
"""

import pandas as pd
import pyfixest as pf
import time
import numpy as np

def test_basic_analysis():
    """Test the analysis with actual settings from the screenshots"""
    
    print("="*70)
    print("PANEL DATA ANALYSIS TEST")
    print("="*70)
    
    # Load data
    print("\n1. Loading data...")
    start_time = time.time()
    df = pd.read_csv('data/data_emission.csv')
    load_time = time.time() - start_time
    print(f"   ✓ Data loaded in {load_time:.2f} seconds")
    print(f"   Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    
    # Configuration from screenshots
    firm_id_col = 'Firm'
    year_col = 'year'
    dependent_var = 'roa'
    independent_var = 'emission'
    control_vars = ['current_ratio', 'size', 'z_score']
    
    print(f"\n2. Data configuration:")
    print(f"   Firm ID: {firm_id_col}")
    print(f"   Time: {year_col}")
    print(f"   Dependent: {dependent_var}")
    print(f"   Independent: {independent_var}")
    print(f"   Controls: {', '.join(control_vars)}")
    
    # Prepare data
    print("\n3. Preparing data...")
    start_time = time.time()
    
    # Select columns
    all_cols = [firm_id_col, year_col, dependent_var, independent_var] + control_vars
    df_clean = df[all_cols].copy()
    
    # Sort by firm and year for lag calculation
    df_clean = df_clean.sort_values([firm_id_col, year_col])
    
    print(f"   Firms: {df_clean[firm_id_col].nunique():,}")
    print(f"   Years: {df_clean[year_col].nunique()}")
    print(f"   Observations before dropna: {len(df_clean):,}")
    
    # Check for missing values
    print("\n4. Checking for missing values...")
    missing_counts = df_clean.isnull().sum()
    if missing_counts.any():
        print("   Missing values found:")
        for col, count in missing_counts[missing_counts > 0].items():
            print(f"     {col}: {count:,} ({count/len(df_clean)*100:.1f}%)")
    
    # Create lagged dependent variables (as in screenshot: min=1, max=1)
    print("\n5. Creating lagged variables...")
    start_time = time.time()
    lag_min = 1
    lag_max = 1
    
    for lag in range(lag_min, lag_max + 1):
        lag_var_name = f'{dependent_var}_lag{lag}'
        df_clean[lag_var_name] = df_clean.groupby(firm_id_col)[dependent_var].shift(lag)
        print(f"   Created: {lag_var_name}")
    
    lag_time = time.time() - start_time
    print(f"   ✓ Lagged variables created in {lag_time:.2f} seconds")
    
    # Drop missing values
    print("\n6. Dropping missing values...")
    before_drop = len(df_clean)
    df_clean = df_clean.dropna()
    after_drop = len(df_clean)
    print(f"   Before: {before_drop:,}")
    print(f"   After: {after_drop:,}")
    print(f"   Dropped: {before_drop - after_drop:,} ({(before_drop - after_drop)/before_drop*100:.1f}%)")
    print(f"   Final firms: {df_clean[firm_id_col].nunique():,}")
    
    # Build formula
    print("\n7. Building formula...")
    exog_vars = [independent_var] + control_vars + [f'{dependent_var}_lag1']
    formula_rhs = ' + '.join(exog_vars)
    fixed_effects = f"{firm_id_col} + {year_col}"
    formula = f"{dependent_var} ~ {formula_rhs} | {fixed_effects}"
    print(f"   Formula: {formula}")
    
    # Test estimation
    print("\n8. Running Fixed Effects model...")
    print("   Using Two-way clustering with CRV3")
    print("   ⏳ This may take a moment...")
    
    start_time = time.time()
    try:
        vcov = {'CRV3': f"{firm_id_col} + {year_col}"}
        results = pf.feols(formula, data=df_clean, vcov=vcov)
        est_time = time.time() - start_time
        
        print(f"\n   ✓ MODEL COMPLETED SUCCESSFULLY in {est_time:.2f} seconds!")
        print("\n" + "="*70)
        print("RESULTS SUMMARY")
        print("="*70)
        print(results.summary())
        
        return True, est_time
        
    except Exception as e:
        est_time = time.time() - start_time
        print(f"\n   ✗ ERROR after {est_time:.2f} seconds!")
        print(f"   Error: {str(e)}")
        import traceback
        print("\n" + traceback.format_exc())
        return False, est_time


def test_simplified_analysis():
    """Test with simplified configuration (no lags, fewer controls)"""
    
    print("\n" + "="*70)
    print("SIMPLIFIED TEST (No lags, single control)")
    print("="*70)
    
    df = pd.read_csv('data/data_emission.csv')
    
    # Simplified configuration
    df_clean = df[['Firm', 'year', 'roa', 'emission', 'size']].dropna()
    
    print(f"Observations: {len(df_clean):,}")
    print(f"Firms: {df_clean['Firm'].nunique():,}")
    
    formula = "roa ~ emission + size | Firm + year"
    print(f"Formula: {formula}")
    
    print("\nRunning model...")
    start_time = time.time()
    
    try:
        results = pf.feols(formula, data=df_clean, vcov={'CRV3': 'Firm + year'})
        est_time = time.time() - start_time
        print(f"✓ Completed in {est_time:.2f} seconds")
        print(results.summary())
        return True, est_time
    except Exception as e:
        est_time = time.time() - start_time
        print(f"✗ Error after {est_time:.2f} seconds: {str(e)}")
        return False, est_time


if __name__ == "__main__":
    print("\n" + "🔬 STARTING PERFORMANCE DIAGNOSTICS" + "\n")
    
    # Test 1: Full analysis as configured in app
    success1, time1 = test_basic_analysis()
    
    # Test 2: Simplified analysis
    if not success1:
        print("\n⚠️  Full test failed, trying simplified version...")
        success2, time2 = test_simplified_analysis()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if success1:
        print(f"✓ Full analysis: SUCCESS ({time1:.2f} seconds)")
        if time1 > 10:
            print("  ⚠️  However, it took longer than expected (>10s)")
            print("  This may cause timeout issues in the web app")
    else:
        print(f"✗ Full analysis: FAILED ({time1:.2f} seconds)")
    
    print("\n💡 RECOMMENDATIONS:")
    if success1 and time1 < 10:
        print("   • Analysis runs properly and fast enough for web app")
        print("   • Issue may be in Gradio interface or data loading")
    elif success1 and time1 > 10:
        print("   • Analysis works but is slow")
        print("   • Consider: reducing sample size, removing lags, or simplifying model")
    else:
        print("   • Analysis has errors - check data quality and formula")
        print("   • Review error messages above for specific issues")
    
    print("\n" + "="*70)
