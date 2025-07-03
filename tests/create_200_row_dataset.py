#!/usr/bin/env python3
"""
Create a 200-row production-like test dataset with edge cases.
"""

import pandas as pd
import random
from pathlib import Path

def create_200_row_dataset():
    """Create a comprehensive 200-row test dataset with edge cases."""
    
    # Define systems and subsystems with realistic patterns
    systems = [
        {"system": "7-1100-P-01", "desc": "Primary Pump System Alpha"},
        {"system": "7-1200-P-02", "desc": "Secondary Pump System Beta"}, 
        {"system": "7-1300-V-03", "desc": "Valve Control System Gamma"},
        {"system": "7-1400-N-04", "desc": "Nitrogen Supply System Delta"},
        {"system": "7-1500-C-05", "desc": "Cooling System Epsilon"},
        {"system": "7-1600-H-06", "desc": "Heating System Zeta"},
        {"system": "7-1700-M-07", "desc": "Monitoring System Eta"},
        {"system": "7-1800-S-08", "desc": "Safety System Theta"},
        {"system": "7-1900-E-09", "desc": "Emergency System Iota"},
        {"system": "7-2000-T-10", "desc": "Testing Equipment System Kappa"}
    ]
    
    # Generate subsystems for each system
    subsystems = []
    for sys in systems:
        # Each system has 3-5 subsystems
        num_subsystems = random.randint(3, 5)
        for i in range(1, num_subsystems + 1):
            subsystem_id = f"{sys['system']}-{i:02d}"
            subsystem_desc = f"{sys['desc']} - Unit {i}"
            subsystems.append({
                "system": sys["system"],
                "system_desc": sys["desc"],
                "subsystem": subsystem_id,
                "subsystem_desc": subsystem_desc
            })
    
    # ITR types
    itr_types = ["ITR-A", "ITR-B", "ITR-C"]
    
    # End Cert values with edge cases
    end_cert_values = [
        "Y",      # Completed (40%)
        "N",      # Ongoing (30%)
        "",       # Not started (20%)
        "y",      # Edge case: lowercase (3%)
        "n",      # Edge case: lowercase (3%)
        " Y ",    # Edge case: whitespace (2%)
        " N ",    # Edge case: whitespace (2%)
    ]
    
    # Weights for realistic distribution
    end_cert_weights = [0.4, 0.3, 0.2, 0.03, 0.03, 0.02, 0.02]
    
    # Generate exactly 200 rows
    data = []
    row_count = 0
    
    while row_count < 200:
        for subsystem in subsystems:
            if row_count >= 200:
                break
                
            # Each subsystem gets 1-3 ITR types
            num_itrs = random.randint(1, 3)
            selected_itrs = random.sample(itr_types, num_itrs)
            
            for itr in selected_itrs:
                if row_count >= 200:
                    break
                    
                # Choose End Cert value based on weights
                end_cert = random.choices(end_cert_values, weights=end_cert_weights)[0]
                
                # Generate unique composite key values
                item_id = f"ITEM-{row_count + 1:03d}"
                rule_id = f"RULE-{(row_count // 3) + 1:03d}"  # Groups of 3 share rule
                test_id = f"TEST-{(row_count // 2) + 1:03d}"  # Groups of 2 share test  
                form_id = f"FORM-{(row_count // 4) + 1:03d}"  # Groups of 4 share form
                
                data.append({
                    "System": subsystem["system"],
                    "System Descr.": subsystem["system_desc"],
                    "SubSystem": subsystem["subsystem"],
                    "SubSystem Descr.": subsystem["subsystem_desc"],
                    "ITR": itr,
                    "End Cert.": end_cert,
                    "ITEM": item_id,
                    "Rule": rule_id,
                    "Test": test_id,
                    "Form": form_id
                })
                row_count += 1
    
    # Ensure we have exactly 200 rows
    data = data[:200]
    
    # Add some intentional duplicates for testing deduplication
    # Take first 10 rows and duplicate them with different ITR types
    duplicates = []
    for i in range(min(10, len(data))):
        original = data[i].copy()
        # Change ITR but keep same composite key (ITEM+Rule+Test+Form)
        original["ITR"] = "ITR-D"  # Different ITR type
        original["End Cert."] = "N"  # Different status
        duplicates.append(original)
    
    # Add duplicates to the dataset
    data.extend(duplicates)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Verify we have edge cases
    end_cert_values_in_data = df['End Cert.'].unique().tolist()
    print("End Cert. values in dataset:", end_cert_values_in_data)
    
    # Add some NaN values for edge case testing (replace some empty strings)
    empty_indices = df[df['End Cert.'] == ""].index[:3]  # Replace first 3 empty strings with NaN
    df.loc[empty_indices, 'End Cert.'] = None
    
    # Save the dataset
    output_file = Path("tests/test_200_rows.xlsx")
    df.to_excel(output_file, index=False)
    
    print(f"✅ Created test dataset: {output_file}")
    print(f"📊 Dataset summary:")
    print(f"   - Total rows (with duplicates): {len(df)}")
    print(f"   - Unique systems: {df['System'].nunique()}")
    print(f"   - Unique subsystems: {df['SubSystem'].nunique()}")
    print(f"   - ITR types: {sorted(df['ITR'].unique())}")
    
    # Calculate deduplication impact
    df['_composite_key'] = df['ITEM'].astype(str) + '|' + df['Rule'].astype(str) + '|' + df['Test'].astype(str) + '|' + df['Form'].astype(str)
    unique_composite_keys = df['_composite_key'].nunique()
    duplicates_count = len(df) - unique_composite_keys
    
    print(f"   - Unique composite keys (ITEM+Rule+Test+Form): {unique_composite_keys}")
    print(f"   - Duplicates that will be removed: {duplicates_count}")
    print(f"   - Final count after deduplication: {unique_composite_keys}")
    
    print(f"   - End Cert. distribution (before deduplication):")
    
    # Show End Cert distribution including NaN
    value_counts = df['End Cert.'].value_counts(dropna=False)
    for value, count in value_counts.items():
        print(f"     '{value}': {count}")
        
    # Remove the temporary column
    df = df.drop(columns=['_composite_key'])
    
    return df

if __name__ == "__main__":
    create_200_row_dataset()