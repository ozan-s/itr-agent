#!/usr/bin/env python3
"""
Create test data for ITR processing.
"""

import pandas as pd


def create_test_excel():
    """Create a test Excel file with sample ITR data including deduplication fields."""
    
    # Sample test data with System hierarchy and deduplication fields
    # Including intentional duplicates to test deduplication functionality
    test_data = [
        {"System": "7-1100-P-01", "System Descr.": "Pump System 1", "SubSystem": "7-1100-P-01-05", "SubSystem Descr.": "Primary Pump", "ITR": "ITR-A", "End Cert.": "Y", "ITEM": "P001", "Rule": "R001", "Test": "T001", "Form": "F001"},
        {"System": "7-1100-P-01", "System Descr.": "Pump System 1", "SubSystem": "7-1100-P-01-05", "SubSystem Descr.": "Primary Pump", "ITR": "ITR-B", "End Cert.": "N", "ITEM": "P002", "Rule": "R002", "Test": "T002", "Form": "F002"},
        {"System": "7-1100-P-01", "System Descr.": "Pump System 1", "SubSystem": "7-1100-P-01-05", "SubSystem Descr.": "Primary Pump", "ITR": "ITR-C", "End Cert.": "", "ITEM": "P003", "Rule": "R003", "Test": "T003", "Form": "F003"},
        
        {"System": "7-1200-P-02", "System Descr.": "Pump System 2", "SubSystem": "7-1200-P-02-01", "SubSystem Descr.": "Secondary Pump", "ITR": "ITR-A", "End Cert.": "Y", "ITEM": "P004", "Rule": "R004", "Test": "T004", "Form": "F004"},
        {"System": "7-1200-P-02", "System Descr.": "Pump System 2", "SubSystem": "7-1200-P-02-01", "SubSystem Descr.": "Secondary Pump", "ITR": "ITR-B", "End Cert.": "Y", "ITEM": "P005", "Rule": "R005", "Test": "T005", "Form": "F005"},
        
        {"System": "7-1300-P-03", "System Descr.": "Valve Control System", "SubSystem": "7-1300-P-03-02", "SubSystem Descr.": "Control Valve", "ITR": "ITR-A", "End Cert.": "", "ITEM": "P006", "Rule": "R006", "Test": "T006", "Form": "F006"},
        {"System": "7-1300-P-03", "System Descr.": "Valve Control System", "SubSystem": "7-1300-P-03-02", "SubSystem Descr.": "Control Valve", "ITR": "ITR-B", "End Cert.": "N", "ITEM": "P007", "Rule": "R007", "Test": "T007", "Form": "F007"},
        {"System": "7-1300-P-03", "System Descr.": "Valve Control System", "SubSystem": "7-1300-P-03-02", "SubSystem Descr.": "Control Valve", "ITR": "ITR-C", "End Cert.": "N", "ITEM": "P008", "Rule": "R008", "Test": "T008", "Form": "F008"},
        
        {"System": "7-1400-P-04", "System Descr.": "Nitrogen System", "SubSystem": "7-1400-P-04-03", "SubSystem Descr.": "Nitrogen Tank", "ITR": "ITR-A", "End Cert.": "Y", "ITEM": "P009", "Rule": "R009", "Test": "T009", "Form": "F009"},
        
        {"System": "7-1500-P-05", "System Descr.": "Cooling System", "SubSystem": "7-1500-P-05-04", "SubSystem Descr.": "Cooling Unit", "ITR": "ITR-A", "End Cert.": "", "ITEM": "P010", "Rule": "R010", "Test": "T010", "Form": "F010"},
        {"System": "7-1500-P-05", "System Descr.": "Cooling System", "SubSystem": "7-1500-P-05-04", "SubSystem Descr.": "Cooling Unit", "ITR": "ITR-B", "End Cert.": "", "ITEM": "P011", "Rule": "R011", "Test": "T011", "Form": "F011"},
        {"System": "7-1500-P-05", "System Descr.": "Cooling System", "SubSystem": "7-1500-P-05-04", "SubSystem Descr.": "Cooling Unit", "ITR": "ITR-C", "End Cert.": "", "ITEM": "P012", "Rule": "R012", "Test": "T012", "Form": "F012"},
        
        # Add intentional duplicates for testing deduplication
        {"System": "7-1100-P-01", "System Descr.": "Pump System 1", "SubSystem": "7-1100-P-01-05", "SubSystem Descr.": "Primary Pump", "ITR": "ITR-D", "End Cert.": "N", "ITEM": "P001", "Rule": "R001", "Test": "T001", "Form": "F001"},  # DUPLICATE of first row (same ITEM+Rule+Test+Form)
        {"System": "7-1200-P-02", "System Descr.": "Pump System 2", "SubSystem": "7-1200-P-02-01", "SubSystem Descr.": "Secondary Pump", "ITR": "ITR-C", "End Cert.": "", "ITEM": "P004", "Rule": "R004", "Test": "T004", "Form": "F004"},  # DUPLICATE of P004 row
        {"System": "7-1300-P-03", "System Descr.": "Valve Control System", "SubSystem": "7-1300-P-03-02", "SubSystem Descr.": "Control Valve", "ITR": "ITR-D", "End Cert.": "Y", "ITEM": "P006", "Rule": "R006", "Test": "T006", "Form": "F006"},  # DUPLICATE of P006 row
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
    print(f"- Total ITRs (with duplicates): {len(df)}")
    print(f"- Unique Systems: {df['System'].nunique()}")
    print(f"- Unique SubSystems: {df['SubSystem'].nunique()}")
    print(f"- ITR Types: {', '.join(df['ITR'].unique())}")
    
    # Calculate deduplication impact
    df['_composite_key'] = df['ITEM'].astype(str) + '|' + df['Rule'].astype(str) + '|' + df['Test'].astype(str) + '|' + df['Form'].astype(str)
    unique_composite_keys = df['_composite_key'].nunique()
    duplicates_count = len(df) - unique_composite_keys
    
    print(f"- Unique composite keys (ITEM+Rule+Test+Form): {unique_composite_keys}")
    print(f"- Duplicates that will be removed: {duplicates_count}")
    print(f"- Final count after deduplication: {unique_composite_keys}")
    
    return df


if __name__ == "__main__":
    create_test_excel()