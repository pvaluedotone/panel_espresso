"""
Quick test script for panel analysis with CRV1 clustering
Should complete in under 1 minute
"""
import pandas as pd
import pyfixest as pf
import time

print("Loading data...")
df = pd.read_csv('data/data_emission.csv')
print(f"Data loaded: {len(df)} rows × {len(df.columns)} columns")
print(f"Firms: {df['Firm'].nunique()}, Years: {df['year'].nunique()}")

# Prepare data
df_clean = df[['Firm', 'year', 'roa', 'emission', 'current_ratio', 'size', 'z_score']].dropna()
print(f"\nAfter dropping NAs: {len(df_clean)} rows")

# Test model with CRV1 (faster)
print("\n" + "="*60)
print("Running Fixed Effects with Two-way CRV1 clustering...")
print("="*60)

formula = "roa ~ emission + current_ratio + size + z_score | Firm + year"

start = time.time()
try:
    results = pf.feols(formula, data=df_clean, vcov={'CRV1': 'Firm + year'})
    elapsed = time.time() - start
    
    print(f"\n✅ Model completed in {elapsed:.2f} seconds")
    print("\nResults:")
    print(results.summary())
    
    # Extract key coefficient using correct pyfixest API
    print(f"\n{'='*60}")
    print(f"EMISSION COEFFICIENT RESULTS")
    print(f"{'='*60}")
    print(f"Coefficient: {results.coef().iloc[0]:.6f}")
    print(f"Std. Error:  {results.se().iloc[0]:.6f}")
    print(f"t-statistic: {results.tstat().iloc[0]:.4f}")
    
    # pyfixest doesn't have pval() method, calculate from t-statistic or read from summary
    print("\nFull coefficient table shown above in summary()")
    print("The model ran successfully with CRV1 clustering!")
    
except Exception as e:
    elapsed = time.time() - start
    print(f"\n❌ Error after {elapsed:.2f} seconds:")
    print(str(e))
    import traceback
    traceback.print_exc()

print(f"\n{'='*60}")
print("Test complete!")
print(f"{'='*60}")
