#!/usr/bin/env python3
"""
Comprehensive test suite for ITR Processing Agent.
Focus on function-LLM integration and core functionality validation.
"""

import sys
import os
import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import ITRProcessor, query_subsystem_itrs, search_subsystems, search_systems, manage_cache


class TestDataset:
    """Test the 200-row production-like dataset."""
    
    def test_200_row_dataset_exists(self):
        """Test that we have a test dataset with proper structure including deduplication fields."""
        test_file = "tests/test_200_rows.xlsx"
        assert Path(test_file).exists(), f"Test dataset {test_file} does not exist"
        
        df = pd.read_excel(test_file)
        # Dataset now includes duplicates for testing - should have > 200 rows
        assert len(df) >= 200, f"Expected at least 200 rows, got {len(df)}"
        
        # Verify required columns (original + new deduplication columns)
        required_columns = ['System', 'System Descr.', 'SubSystem', 'SubSystem Descr.', 'ITR', 'End Cert.']
        dedup_columns = ['ITEM', 'Rule', 'Test', 'Form']
        all_required_columns = required_columns + dedup_columns
        
        for col in all_required_columns:
            assert col in df.columns, f"Missing required column: {col}"
            
        # Verify we have duplicates for testing deduplication
        df['_composite_key'] = df['ITEM'].astype(str) + '|' + df['Rule'].astype(str) + '|' + df['Test'].astype(str) + '|' + df['Form'].astype(str)
        unique_keys = df['_composite_key'].nunique()
        total_rows = len(df)
        
        assert unique_keys < total_rows, f"Expected duplicates in test data, but all {total_rows} rows have unique composite keys"
        
    def test_dataset_has_edge_cases(self):
        """Test that dataset includes edge cases for End Cert. values."""
        test_file = "tests/test_200_rows.xlsx"
        df = pd.read_excel(test_file)
        
        end_cert_values = df['End Cert.'].tolist()
        
        # Should have empty strings (not started)
        assert "" in end_cert_values or pd.isna(df['End Cert.']).any(), "Missing empty/blank End Cert. values"
        
        # Should have "N" (ongoing)
        assert "N" in end_cert_values, "Missing 'N' End Cert. values"
        
        # Should have "Y" (completed)  
        assert "Y" in end_cert_values, "Missing 'Y' End Cert. values"
        
        # Should have edge cases (lowercase, whitespace)
        assert any(val in ["n", "y", " N ", " Y "] for val in end_cert_values if isinstance(val, str)), "Missing edge case End Cert. values"


class TestITRStatusMethod:
    """Unit tests for get_itr_status method."""
    
    def test_get_itr_status_completed(self):
        """Test get_itr_status returns 'Completed' for 'Y'."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        result = processor.get_itr_status("Y")
        assert result == "Completed", f"Expected 'Completed', got '{result}'"
        
    def test_get_itr_status_ongoing(self):
        """Test get_itr_status returns 'Ongoing' for 'N'."""
        processor = ITRProcessor("tests/test_200_rows.xlsx") 
        result = processor.get_itr_status("N")
        assert result == "Ongoing", f"Expected 'Ongoing', got '{result}'"
        
    def test_get_itr_status_not_started(self):
        """Test get_itr_status returns 'Not Started' for empty/blank."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        
        # Test empty string
        result = processor.get_itr_status("")
        assert result == "Not Started", f"Expected 'Not Started', got '{result}'"
        
        # Test None/NaN
        result = processor.get_itr_status(None)
        assert result == "Not Started", f"Expected 'Not Started', got '{result}'"
        
    def test_get_itr_status_edge_cases(self):
        """Test get_itr_status handles edge cases properly."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        
        # Test lowercase
        assert processor.get_itr_status("y") == "Completed"
        assert processor.get_itr_status("n") == "Ongoing"
        
        # Test with whitespace
        assert processor.get_itr_status(" Y ") == "Completed"
        assert processor.get_itr_status(" N ") == "Ongoing"


class TestSearchMethods:
    """Unit tests for search_subsystems and search_systems methods."""
    
    def test_search_subsystems_exact_match(self):
        """Test search_subsystems finds exact subsystem ID matches."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        result = processor.search_subsystems("7-1100-P-01-01")
        
        assert isinstance(result, dict), "search_subsystems should return a dict"
        assert "matches" in result, "Result should contain 'matches' key"
        assert len(result["matches"]) >= 1, "Should find at least one match"
        
        # Check first match has expected structure
        first_match = result["matches"][0]
        assert "id" in first_match, "Match should have 'id' field"
        assert "description" in first_match, "Match should have 'description' field"
        assert "match_type" in first_match, "Match should have 'match_type' field"
        
    def test_search_subsystems_partial_match(self):
        """Test search_subsystems finds partial matches in IDs."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        result = processor.search_subsystems("7-1100")
        
        assert isinstance(result, dict), "search_subsystems should return a dict"
        assert "matches" in result, "Result should contain 'matches' key"
        assert len(result["matches"]) >= 1, "Should find multiple matches for partial pattern"
        
        # All matches should contain the pattern
        for match in result["matches"]:
            assert "7-1100" in match["id"], f"Match {match['id']} should contain '7-1100'"
            
    def test_search_subsystems_description_match(self):
        """Test search_subsystems finds matches in descriptions."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        result = processor.search_subsystems("Alpha")
        
        assert isinstance(result, dict), "search_subsystems should return a dict"
        assert "matches" in result, "Result should contain 'matches' key"
        
        # Should find matches in descriptions
        if len(result["matches"]) > 0:
            description_matches = [m for m in result["matches"] if "Alpha" in m["description"]]
            assert len(description_matches) >= 1, "Should find at least one description match"
            
    def test_search_subsystems_case_insensitive(self):
        """Test search_subsystems is case insensitive."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        
        # Test lowercase pattern
        result_lower = processor.search_subsystems("alpha")
        result_upper = processor.search_subsystems("ALPHA")
        
        # Both should return same number of matches (if any)
        assert len(result_lower.get("matches", [])) == len(result_upper.get("matches", [])), \
            "Case insensitive search should return same results"
            
    def test_search_subsystems_no_pattern(self):
        """Test search_subsystems returns all subsystems when no pattern provided."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        result = processor.search_subsystems(None)
        
        assert isinstance(result, dict), "search_subsystems should return a dict"
        assert "subsystems" in result, "Result should contain 'subsystems' key when no pattern"
        assert len(result["subsystems"]) >= 10, "Should return multiple subsystems"
        
    def test_search_subsystems_empty_pattern(self):
        """Test search_subsystems handles empty pattern."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        result = processor.search_subsystems("")
        
        assert isinstance(result, dict), "search_subsystems should return a dict"
        # Should behave like no pattern provided
        assert "subsystems" in result, "Empty pattern should return all subsystems"
        
    def test_search_subsystems_invalid_pattern(self):
        """Test search_subsystems handles pattern that matches nothing."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        result = processor.search_subsystems("NONEXISTENT-PATTERN-XYZ-999")
        
        assert isinstance(result, dict), "search_subsystems should return a dict"
        assert "matches" in result, "Result should contain 'matches' key"
        assert len(result["matches"]) == 0, "Should find no matches for invalid pattern"
        
    def test_search_systems_exact_match(self):
        """Test search_systems finds exact system ID matches."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        result = processor.search_systems("7-1100-P-01")
        
        assert isinstance(result, dict), "search_systems should return a dict"
        assert "matches" in result, "Result should contain 'matches' key"
        assert len(result["matches"]) >= 1, "Should find at least one match"
        
        # Check first match has expected structure
        first_match = result["matches"][0]
        assert "id" in first_match, "Match should have 'id' field"
        assert "description" in first_match, "Match should have 'description' field"
        assert "subsystems" in first_match, "Match should have 'subsystems' field"
        
    def test_search_systems_partial_match(self):
        """Test search_systems finds partial matches."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        result = processor.search_systems("7-1")
        
        assert isinstance(result, dict), "search_systems should return a dict"
        assert "matches" in result, "Result should contain 'matches' key"
        assert len(result["matches"]) >= 1, "Should find multiple matches for partial pattern"
        
    def test_search_systems_no_pattern(self):
        """Test search_systems returns all systems when no pattern provided."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        result = processor.search_systems(None)
        
        assert isinstance(result, dict), "search_systems should return a dict"
        assert "systems" in result, "Result should contain 'systems' key when no pattern"
        assert len(result["systems"]) >= 5, "Should return multiple systems"


class TestToolIntegration:
    """Integration tests for the exposed tool functions."""
    
    def test_query_subsystem_itrs_returns_string(self):
        """Test query_subsystem_itrs returns a formatted string for LLM consumption."""
        # This should fail initially - testing integration with real data
        result = query_subsystem_itrs("7-1100-P-01-01")
        
        assert isinstance(result, str), "query_subsystem_itrs should return a string"
        assert len(result) > 0, "Result should not be empty"
        
        # Should contain key information for LLM extraction
        assert "ITR" in result, "Result should mention ITR"
        assert "7-1100-P-01-01" in result, "Result should contain subsystem ID"
        
    def test_query_subsystem_itrs_contains_status_info(self):
        """Test query_subsystem_itrs contains status information."""
        result = query_subsystem_itrs("7-1100-P-01-01")
        
        # Should contain status-related keywords
        status_keywords = ["Completed", "Ongoing", "Not Started", "Total", "Open"]
        found_keywords = [kw for kw in status_keywords if kw in result]
        assert len(found_keywords) >= 2, f"Result should contain status keywords, found: {found_keywords}"
        
    def test_query_subsystem_itrs_invalid_subsystem(self):
        """Test query_subsystem_itrs handles invalid subsystem gracefully."""
        result = query_subsystem_itrs("INVALID-SUBSYSTEM-XYZ")
        
        assert isinstance(result, str), "Should return string even for invalid input"
        assert len(result) > 0, "Should return helpful error message"
        assert "not found" in result.lower() or "error" in result.lower(), "Should indicate error condition"
        
    def test_search_subsystems_tool_returns_string(self):
        """Test search_subsystems tool returns a formatted string."""
        result = search_subsystems("7-1100")
        
        assert isinstance(result, str), "search_subsystems tool should return a string"
        assert len(result) > 0, "Result should not be empty"
        assert "7-1100" in result, "Result should contain the search pattern"
        
    def test_search_subsystems_tool_no_pattern(self):
        """Test search_subsystems tool with no pattern."""
        result = search_subsystems()
        
        assert isinstance(result, str), "search_subsystems tool should return a string"
        assert len(result) > 0, "Result should not be empty"
        assert "subsystem" in result.lower(), "Result should mention subsystems"
        
    def test_search_systems_tool_returns_string(self):
        """Test search_systems tool returns a formatted string."""
        result = search_systems("7-1100")
        
        assert isinstance(result, str), "search_systems tool should return a string"
        assert len(result) > 0, "Result should not be empty"
        assert "7-1100" in result, "Result should contain the search pattern"
        
    def test_manage_cache_tool_status(self):
        """Test manage_cache tool with status action."""
        result = manage_cache("status")
        
        assert isinstance(result, str), "manage_cache tool should return a string"
        assert len(result) > 0, "Result should not be empty"
        assert "cache" in result.lower(), "Result should mention cache"
        
    def test_manage_cache_tool_invalid_action(self):
        """Test manage_cache tool with invalid action."""
        result = manage_cache("invalid_action")
        
        assert isinstance(result, str), "manage_cache tool should return a string"
        assert len(result) > 0, "Result should not be empty"
        assert "valid actions" in result.lower() or "error" in result.lower(), "Should indicate invalid action"


class TestLLMDataExtraction:
    """Test that tool responses contain extractable data for LLM use."""
    
    def test_query_subsystem_extractable_counts(self):
        """Test that LLM can extract specific counts from query_subsystem_itrs."""
        result = query_subsystem_itrs("7-1100-P-01-01")
        
        # Look for numeric patterns that LLM could extract
        import re
        numbers = re.findall(r'\b\d+\b', result)
        assert len(numbers) >= 2, "Result should contain multiple numbers for LLM to extract"
        
        # Should be able to find completion-related information
        completion_patterns = ["completed", "ongoing", "not started", "total", "open"]
        found_patterns = [p for p in completion_patterns if p.lower() in result.lower()]
        assert len(found_patterns) >= 2, f"Should contain completion info, found: {found_patterns}"
        
    def test_search_results_extractable_structure(self):
        """Test that search results have structure LLM can work with."""
        result = search_subsystems("7-1100")
        
        # Should contain identifiable patterns
        assert ":" in result or "-" in result, "Result should have structured separators"
        
        # Should contain subsystem identifiers
        subsystem_pattern = r'7-\d{4}-[A-Z]-\d{2}-\d{2}'
        import re
        matches = re.findall(subsystem_pattern, result)
        assert len(matches) >= 1, "Should contain recognizable subsystem IDs"


class TestDeduplication:
    """Test deduplication functionality with composite key."""
    
    def test_composite_key_generation(self):
        """Test that _create_composite_key generates proper keys from ITEM+Rule+Test+Form."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        
        # This test should fail initially - method doesn't exist yet
        test_data = pd.DataFrame([
            {"ITEM": "P001", "Rule": "R001", "Test": "T001", "Form": "F001"},
            {"ITEM": "P002", "Rule": "R002", "Test": "T002", "Form": "F002"},
            {"ITEM": "", "Rule": "R003", "Test": "T003", "Form": "F003"},
            {"ITEM": "P004", "Rule": "", "Test": "T004", "Form": "F004"},
        ])
        
        # Test normal case
        key1 = processor._create_composite_key(test_data.iloc[0])
        assert key1 == "P001|R001|T001|F001", f"Expected 'P001|R001|T001|F001', got '{key1}'"
        
        # Test with empty values
        key2 = processor._create_composite_key(test_data.iloc[2])
        assert key2 == "|R003|T003|F003", f"Expected '|R003|T003|F003', got '{key2}'"
        
    def test_deduplication_removes_duplicates(self):
        """Test that _deduplicate_data removes rows with same composite key."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        
        # Create test data with intentional duplicates
        test_data = pd.DataFrame([
            {"System": "7-1100-P-01", "SubSystem": "7-1100-P-01-05", "ITR": "ITR-A", "ITEM": "P001", "Rule": "R001", "Test": "T001", "Form": "F001", "End Cert.": "Y"},
            {"System": "7-1100-P-01", "SubSystem": "7-1100-P-01-05", "ITR": "ITR-B", "ITEM": "P001", "Rule": "R001", "Test": "T001", "Form": "F001", "End Cert.": "N"},  # Duplicate key
            {"System": "7-1200-P-02", "SubSystem": "7-1200-P-02-01", "ITR": "ITR-A", "ITEM": "P002", "Rule": "R002", "Test": "T002", "Form": "F002", "End Cert.": "Y"},
            {"System": "7-1200-P-02", "SubSystem": "7-1200-P-02-01", "ITR": "ITR-C", "ITEM": "P003", "Rule": "R003", "Test": "T003", "Form": "F003", "End Cert.": ""},
        ])
        
        # This should fail initially - method doesn't exist yet
        deduplicated = processor._deduplicate_data(test_data)
        
        # Should have 3 unique rows (first duplicate removed)
        assert len(deduplicated) == 3, f"Expected 3 unique rows after deduplication, got {len(deduplicated)}"
        
        # Check that the first occurrence is kept
        first_row = deduplicated[deduplicated['ITEM'] == 'P001']
        assert len(first_row) == 1, "Should keep only one row with duplicate key"
        assert first_row.iloc[0]['ITR'] == 'ITR-A', "Should keep the first occurrence"
        
    def test_deduplication_handles_missing_values(self):
        """Test deduplication handles missing/null values in key fields gracefully."""
        processor = ITRProcessor("tests/test_200_rows.xlsx")
        
        # Test data with missing values
        test_data = pd.DataFrame([
            {"System": "7-1100-P-01", "SubSystem": "7-1100-P-01-05", "ITR": "ITR-A", "ITEM": "P001", "Rule": "R001", "Test": "T001", "Form": "F001", "End Cert.": "Y"},
            {"System": "7-1100-P-01", "SubSystem": "7-1100-P-01-05", "ITR": "ITR-B", "ITEM": None, "Rule": "R002", "Test": "T002", "Form": "F002", "End Cert.": "N"},
            {"System": "7-1200-P-02", "SubSystem": "7-1200-P-02-01", "ITR": "ITR-A", "ITEM": "", "Rule": "", "Test": "", "Form": "", "End Cert.": "Y"},
            {"System": "7-1200-P-02", "SubSystem": "7-1200-P-02-01", "ITR": "ITR-C", "ITEM": "", "Rule": "", "Test": "", "Form": "", "End Cert.": ""},  # Duplicate empty key
        ])
        
        # This should fail initially - method doesn't exist yet
        deduplicated = processor._deduplicate_data(test_data)
        
        # Should handle missing values and still deduplicate
        assert len(deduplicated) == 3, f"Expected 3 unique rows after deduplication with missing values, got {len(deduplicated)}"
        
        # Check that empty keys are handled properly
        empty_key_rows = deduplicated[(deduplicated['ITEM'].fillna('') == '') & 
                                     (deduplicated['Rule'].fillna('') == '') & 
                                     (deduplicated['Test'].fillna('') == '') & 
                                     (deduplicated['Form'].fillna('') == '')]
        assert len(empty_key_rows) == 1, "Should keep only one row with empty composite key"


class TestNewExcelColumns:
    """Test loading Excel files with new ITEM, Rule, Test, Form columns."""
    
    def test_load_excel_with_new_columns(self):
        """Test that ITRProcessor can load Excel files with ITEM, Rule, Test, Form columns."""
        # Create test Excel file with new columns
        test_data = pd.DataFrame([
            {"System": "7-1100-P-01", "System Descr.": "Pump System 1", "SubSystem": "7-1100-P-01-05", 
             "SubSystem Descr.": "Primary Pump", "ITR": "ITR-A", "End Cert.": "Y",
             "ITEM": "P001", "Rule": "R001", "Test": "T001", "Form": "F001"},
            {"System": "7-1100-P-01", "System Descr.": "Pump System 1", "SubSystem": "7-1100-P-01-05", 
             "SubSystem Descr.": "Primary Pump", "ITR": "ITR-B", "End Cert.": "N",
             "ITEM": "P002", "Rule": "R002", "Test": "T002", "Form": "F002"},
        ])
        
        # Save to test file
        test_file = "tests/test_new_columns.xlsx"
        test_data.to_excel(test_file, index=False)
        
        # This should fail initially - _load_data doesn't handle new columns yet
        try:
            processor = ITRProcessor(test_file)
            
            # Should successfully load data
            assert processor.data is not None, "Data should be loaded"
            assert not processor.data.empty, "Data should not be empty"
            assert len(processor.data) == 2, f"Should load 2 rows, got {len(processor.data)}"
            
            # Should have new columns
            required_new_columns = ["ITEM", "Rule", "Test", "Form"]
            for col in required_new_columns:
                assert col in processor.data.columns, f"Missing new column: {col}"
            
            # Should have correct data in new columns
            first_row = processor.data.iloc[0]
            assert first_row["ITEM"] == "P001", f"Expected ITEM='P001', got '{first_row['ITEM']}'"
            assert first_row["Rule"] == "R001", f"Expected Rule='R001', got '{first_row['Rule']}'"
            
        finally:
            # Clean up test file
            import os
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_all_required_columns_present(self):
        """Test that ITRProcessor requires all 10 columns including deduplication fields."""
        # Create test Excel file with all required columns
        test_data = pd.DataFrame([
            {"System": "7-1100-P-01", "System Descr.": "Pump System 1", "SubSystem": "7-1100-P-01-05", 
             "SubSystem Descr.": "Primary Pump", "ITR": "ITR-A", "End Cert.": "Y",
             "ITEM": "P001", "Rule": "R001", "Test": "T001", "Form": "F001"},
        ])
        
        # Save to test file
        test_file = "tests/test_all_columns.xlsx"
        test_data.to_excel(test_file, index=False)
        
        try:
            processor = ITRProcessor(test_file)
            
            # Should successfully load data
            assert processor.data is not None, "Data should be loaded"
            assert not processor.data.empty, "Data should not be empty"
            assert len(processor.data) == 1, f"Should load 1 row, got {len(processor.data)}"
            
            # Should have all required columns
            required_columns = ["System", "System Descr.", "SubSystem", "SubSystem Descr.", "ITR", "End Cert.", "ITEM", "Rule", "Test", "Form"]
            for col in required_columns:
                assert col in processor.data.columns, f"Missing required column: {col}"
            
        finally:
            # Clean up test file
            import os
            if os.path.exists(test_file):
                os.remove(test_file)


class TestDeduplicatedCounting:
    """Test that counting functions use deduplicated data."""
    
    def test_get_subsystem_data_uses_deduplicated_counts(self):
        """Test that get_subsystem_data returns counts based on deduplicated data."""
        # Create test Excel file with duplicates
        test_data = pd.DataFrame([
            {"System": "7-1100-P-01", "System Descr.": "Pump System 1", "SubSystem": "7-1100-P-01-05", 
             "SubSystem Descr.": "Primary Pump", "ITR": "ITR-A", "End Cert.": "Y",
             "ITEM": "P001", "Rule": "R001", "Test": "T001", "Form": "F001"},
            {"System": "7-1100-P-01", "System Descr.": "Pump System 1", "SubSystem": "7-1100-P-01-05", 
             "SubSystem Descr.": "Primary Pump", "ITR": "ITR-B", "End Cert.": "N",  
             "ITEM": "P001", "Rule": "R001", "Test": "T001", "Form": "F001"},  # DUPLICATE - same composite key
            {"System": "7-1100-P-01", "System Descr.": "Pump System 1", "SubSystem": "7-1100-P-01-05", 
             "SubSystem Descr.": "Primary Pump", "ITR": "ITR-C", "End Cert.": "",
             "ITEM": "P002", "Rule": "R002", "Test": "T002", "Form": "F002"},  # UNIQUE
        ])
        
        # Save to test file
        test_file = "tests/test_dedup_counts.xlsx"
        test_data.to_excel(test_file, index=False)
        
        try:
            processor = ITRProcessor(test_file)
            
            # Get subsystem data - this should fail initially as get_subsystem_data doesn't use deduplicated data yet
            result = processor.get_subsystem_data("7-1100-P-01-05")
            
            # Should return dict with correct structure
            assert isinstance(result, dict), "get_subsystem_data should return a dict"
            assert "overall" in result, "Result should contain 'overall' key"
            
            # Test the key requirement: counts should be based on deduplicated data
            # With 3 rows and 1 duplicate, we should have 2 unique ITRs after deduplication
            overall = result["overall"]
            assert overall["total"] == 2, f"Expected 2 total ITRs after deduplication, got {overall['total']}"
            
            # Should have 1 completed (first occurrence of duplicate kept) and 1 not started
            assert overall["completed"] == 1, f"Expected 1 completed ITR, got {overall['completed']}"
            assert overall["not_started"] == 1, f"Expected 1 not started ITR, got {overall['not_started']}"
            assert overall["ongoing"] == 0, f"Expected 0 ongoing ITRs, got {overall['ongoing']}"
            
            # By-type breakdown should also reflect deduplicated counts
            by_type = result["by_type"]
            assert "ITR-A" in by_type, "Should have ITR-A type"
            assert "ITR-C" in by_type, "Should have ITR-C type"
            
            # ITR-A should have 1 total (duplicate ITR-B removed)
            assert by_type["ITR-A"]["total"] == 1, f"Expected 1 ITR-A after deduplication, got {by_type['ITR-A']['total']}"
            
            # ITR-C should have 1 total 
            assert by_type["ITR-C"]["total"] == 1, f"Expected 1 ITR-C, got {by_type['ITR-C']['total']}"
            
        finally:
            # Clean up test file
            import os
            if os.path.exists(test_file):
                os.remove(test_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])