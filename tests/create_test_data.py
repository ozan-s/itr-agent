#!/usr/bin/env python3
"""
Create test data for ITR processing.
"""

import pandas as pd


def create_test_excel():
    """Create a test Excel file with sample ITR data."""
    
    # Sample test data
    test_data = [
        {"SubSystem": "7-1100-P-01-05", "ITR": "ITR-A", "End Cert.": "Y"},
        {"SubSystem": "7-1100-P-01-05", "ITR": "ITR-B", "End Cert.": "N"},
        {"SubSystem": "7-1100-P-01-05", "ITR": "ITR-C", "End Cert.": ""},
        {"SubSystem": "7-1200-P-02-01", "ITR": "ITR-A", "End Cert.": "Y"},
        {"SubSystem": "7-1200-P-02-01", "ITR": "ITR-B", "End Cert.": "Y"},
        {"SubSystem": "7-1300-P-03-02", "ITR": "ITR-A", "End Cert.": ""},
        {"SubSystem": "7-1300-P-03-02", "ITR": "ITR-B", "End Cert.": "N"},
        {"SubSystem": "7-1300-P-03-02", "ITR": "ITR-C", "End Cert.": "N"},
        {"SubSystem": "7-1400-P-04-03", "ITR": "ITR-A", "End Cert.": "Y"},
        {"SubSystem": "7-1500-P-05-04", "ITR": "ITR-A", "End Cert.": ""},
        {"SubSystem": "7-1500-P-05-04", "ITR": "ITR-B", "End Cert.": ""},
        {"SubSystem": "7-1500-P-05-04", "ITR": "ITR-C", "End Cert.": ""},
    ]
    
    # Create DataFrame
    df = pd.DataFrame(test_data)
    
    # Save to Excel
    df.to_excel("test_pcos.xlsx", index=False)
    print("✅ Created test Excel file: test_pcos.xlsx")
    
    # Display the data
    print("\nTest data:")
    print(df.to_string(index=False))
    
    # Show summary
    print(f"\nSummary:")
    print(f"- Total ITRs: {len(df)}")
    print(f"- Unique SubSystems: {df['SubSystem'].nunique()}")
    print(f"- ITR Types: {', '.join(df['ITR'].unique())}")
    
    return df


if __name__ == "__main__":
    create_test_excel()