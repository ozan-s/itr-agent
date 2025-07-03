#!/usr/bin/env python3
"""
ITR Tools - 3 focused tools for Excel ITR processing.

- query_subsystem_itrs: Comprehensive ITR data for any subsystem
- search_subsystems: Find subsystems by pattern
- manage_cache: Cache management and data refresh
"""

import pandas as pd
import pickle
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional
from smolagents import tool


class ITRProcessor:
    """
    ITR processor with caching and Excel data management.
    """
    
    def __init__(self, excel_file: str = "pcos.xlsx"):
        """Initialize processor with smart caching."""
        self.excel_file = excel_file
        self.cache_dir = Path(".cache")
        self.cache_file = self.cache_dir / "pcos_cache.pkl"
        self.cache_info_file = self.cache_dir / "cache_info.pkl"
        self.data = None
        self._ensure_cache_dir()
        self._load_data()
    
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_file_modification_time(self) -> float:
        """Get the modification time of the Excel file."""
        file_path = Path(self.excel_file)
        return file_path.stat().st_mtime if file_path.exists() else 0
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is valid (newer than Excel file)."""
        if not self.cache_file.exists() or not self.cache_info_file.exists():
            return False
        
        # If Excel file doesn't exist, cache is invalid
        file_path = Path(self.excel_file)
        if not file_path.exists():
            return False
        
        try:
            with open(self.cache_info_file, 'rb') as f:
                cache_info = pickle.load(f)
            
            excel_mtime = self._get_file_modification_time()
            cache_mtime = cache_info.get('file_mtime', 0)
            
            return cache_mtime >= excel_mtime
        except Exception:
            return False
    
    def _save_cache(self, data: pd.DataFrame):
        """Save DataFrame and metadata to cache with atomic writes."""
        temp_cache_file = self.cache_file.with_suffix('.tmp')
        temp_info_file = self.cache_info_file.with_suffix('.tmp')
        
        try:
            # Write to temporary files first
            with open(temp_cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            cache_info = {
                'file_mtime': self._get_file_modification_time(),
                'cached_at': time.time(),
                'record_count': len(data)
            }
            with open(temp_info_file, 'wb') as f:
                pickle.dump(cache_info, f)
            
            # Atomic rename - both files are ready
            temp_cache_file.rename(self.cache_file)
            temp_info_file.rename(self.cache_info_file)
            
            print(f"✅ Cached {len(data)} records for faster future access")
        except Exception as e:
            # Clean up temporary files if they exist
            if temp_cache_file.exists():
                temp_cache_file.unlink()
            if temp_info_file.exists():
                temp_info_file.unlink()
            print(f"⚠️ Failed to save cache: {e}")
    
    def _load_from_cache(self) -> Optional[pd.DataFrame]:
        """Load DataFrame from cache if valid."""
        if not self._is_cache_valid():
            return None
        
        try:
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
            
            with open(self.cache_info_file, 'rb') as f:
                cache_info = pickle.load(f)
            
            print(f"⚡ Loaded {len(data)} records from cache")
            return data
        except Exception as e:
            print(f"⚠️ Failed to load cache: {e}")
            return None
    
    def _load_data(self):
        """Load Excel data with caching optimization."""
        # Try cache first
        cached_data = self._load_from_cache()
        if cached_data is not None:
            self.data = cached_data
            return
        
        # Load from Excel with optimizations
        try:
            file_path = Path(self.excel_file)
            if not file_path.exists():
                raise FileNotFoundError(f"Excel file not found: {self.excel_file}")
            
            print(f"📊 Loading Excel file: {self.excel_file}...")
            start_time = time.time()
            
            # Core required columns (must exist)
            core_required_columns = ["System", "System Descr.", "SubSystem", "ITR", "End Cert.", "SubSystem Descr."]
            
            # New deduplication columns (optional for backward compatibility)
            dedup_columns = ["ITEM", "Rule", "Test", "Form"]
            
            # Check available columns and determine what to load
            all_columns = pd.read_excel(self.excel_file, nrows=0, engine="openpyxl").columns.tolist()
            
            # Check for missing core columns
            missing_core_columns = [col for col in core_required_columns if col not in all_columns]
            if missing_core_columns:
                raise ValueError(f"Missing required columns: {missing_core_columns}. Available columns: {all_columns}")
            
            # Determine which dedup columns are available
            available_dedup_columns = [col for col in dedup_columns if col in all_columns]
            has_dedup_columns = len(available_dedup_columns) > 0
            
            # Combine columns to load
            columns_to_load = core_required_columns + available_dedup_columns
            
            # Build dtype specification
            dtype_spec = {
                "System": "string",
                "System Descr.": "string",
                "SubSystem": "string",
                "ITR": "string", 
                "End Cert.": "string",
                "SubSystem Descr.": "string"
            }
            
            # Add dtype for available dedup columns
            for col in available_dedup_columns:
                dtype_spec[col] = "string"
            
            df = pd.read_excel(
                self.excel_file,
                usecols=columns_to_load,
                dtype=dtype_spec,
                engine="openpyxl",
                na_filter=True,
            )
            
            load_time = time.time() - start_time
            
            # Data cleaning - handle NaN values before string conversion
            df["System Descr."] = df["System Descr."].fillna("")
            df["End Cert."] = df["End Cert."].fillna("")
            df["SubSystem Descr."] = df["SubSystem Descr."].fillna("")
            
            # Clean deduplication columns if they exist
            for col in available_dedup_columns:
                df[col] = df[col].fillna("")
            
            # Convert to strings and strip whitespace
            df["System"] = df["System"].astype(str).str.strip()
            df["System Descr."] = df["System Descr."].astype(str).str.strip()
            df["SubSystem"] = df["SubSystem"].astype(str).str.strip()
            df["ITR"] = df["ITR"].astype(str).str.strip()
            df["End Cert."] = df["End Cert."].astype(str).str.strip()
            df["SubSystem Descr."] = df["SubSystem Descr."].astype(str).str.strip()
            
            # Clean deduplication columns
            for col in available_dedup_columns:
                df[col] = df[col].astype(str).str.strip()
            
            # Remove rows with missing essential data
            df = df.dropna(subset=["System", "SubSystem", "ITR"], how="any")
            
            # Apply deduplication if we have the required columns
            if has_dedup_columns and len(available_dedup_columns) == 4:
                original_count = len(df)
                df = self._deduplicate_data(df)
                dedup_count = len(df)
                print(f"🔍 Deduplication: {original_count} → {dedup_count} records ({original_count - dedup_count} duplicates removed)")
            elif has_dedup_columns:
                print(f"⚠️  Partial deduplication columns found ({available_dedup_columns}). Need all 4 columns (ITEM, Rule, Test, Form) for deduplication.")
            
            self.data = df
            print(f"✅ Loaded {len(self.data)} ITR records in {load_time:.2f}s")
            self._save_cache(self.data)
            
        except Exception as e:
            print(f"❌ Error loading Excel file: {e}")
            # Try fallback to test data
            test_file = "test_pcos.xlsx"
            if Path(test_file).exists():
                print(f"🔄 Falling back to test data: {test_file}")
                try:
                    self.excel_file = test_file
                    self._load_data()
                    return
                except Exception as test_error:
                    print(f"❌ Test data also failed: {test_error}")
            else:
                print(f"❌ Test data file not found: {test_file}")
            
            self.data = pd.DataFrame()
    
    def get_itr_status(self, end_cert_value) -> str:
        """Determine ITR status from End Cert. value."""
        if end_cert_value is None or not str(end_cert_value).strip() or str(end_cert_value).strip().lower() in ["", "nan", "none"]:
            return "Not Started"
        elif str(end_cert_value).strip().upper() == "N":
            return "Ongoing"
        elif str(end_cert_value).strip().upper() == "Y":
            return "Completed"
        else:
            return "Unknown"
    
    def _create_composite_key(self, row) -> str:
        """Create composite key from ITEM+Rule+Test+Form fields."""
        item = str(row.get("ITEM", "")).strip() if pd.notna(row.get("ITEM", "")) else ""
        rule = str(row.get("Rule", "")).strip() if pd.notna(row.get("Rule", "")) else ""
        test = str(row.get("Test", "")).strip() if pd.notna(row.get("Test", "")) else ""
        form = str(row.get("Form", "")).strip() if pd.notna(row.get("Form", "")) else ""
        
        return f"{item}|{rule}|{test}|{form}"
    
    def _deduplicate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows based on composite key of ITEM+Rule+Test+Form."""
        if data.empty:
            return data
        
        # Create composite key for each row
        data = data.copy()
        data["_composite_key"] = data.apply(self._create_composite_key, axis=1)
        
        # Keep first occurrence of each unique key
        deduplicated = data.drop_duplicates(subset=["_composite_key"], keep="first")
        
        # Remove the temporary composite key column
        deduplicated = deduplicated.drop(columns=["_composite_key"])
        
        return deduplicated.reset_index(drop=True)
    
    def get_subsystem_data(self, subsystem: str) -> Dict:
        """
        THE comprehensive tool - returns all ITR data for a subsystem.
        LLM can extract whatever the user asked for from this rich response.
        """
        if self.data is None or self.data.empty:
            return {
                "error": "No data loaded",
                "guidance": "Try reloading data with manage_cache tool"
            }
        
        # Get all data for the subsystem
        subsystem_data = self.data[self.data["SubSystem"] == subsystem]
        
        if subsystem_data.empty:
            return {
                "error": f"No ITRs found for subsystem {subsystem}",
                "guidance": "Use search_subsystems() to find available subsystem IDs",
                "subsystem": subsystem
            }
        
        # Calculate overall statistics
        total_itrs = len(subsystem_data)
        status_counts = {"Not Started": 0, "Ongoing": 0, "Completed": 0, "Unknown": 0}
        
        for _, row in subsystem_data.iterrows():
            status = self.get_itr_status(row["End Cert."])
            status_counts[status] += 1
        
        open_itrs = status_counts["Not Started"] + status_counts["Ongoing"]
        
        # Calculate by-type breakdown
        by_type = {}
        for itr_type in ["ITR-A", "ITR-B", "ITR-C"]:
            type_data = subsystem_data[subsystem_data["ITR"] == itr_type]
            type_status_counts = {"Not Started": 0, "Ongoing": 0, "Completed": 0, "Unknown": 0}
            
            for _, row in type_data.iterrows():
                status = self.get_itr_status(row["End Cert."])
                type_status_counts[status] += 1
            
            type_open = type_status_counts["Not Started"] + type_status_counts["Ongoing"]
            
            by_type[itr_type] = {
                "total": len(type_data),
                "open": type_open,
                "completed": type_status_counts["Completed"],
                "not_started": type_status_counts["Not Started"],
                "ongoing": type_status_counts["Ongoing"]
            }
        
        # Create comprehensive response
        result = {
            "subsystem": subsystem,
            "overall": {
                "total": total_itrs,
                "open": open_itrs,
                "completed": status_counts["Completed"],
                "not_started": status_counts["Not Started"],
                "ongoing": status_counts["Ongoing"]
            },
            "by_type": by_type,
            "completion_rate": round(status_counts["Completed"] / total_itrs * 100, 1) if total_itrs > 0 else 0,
            "guidance": self._generate_guidance(subsystem, total_itrs, open_itrs, by_type)
        }
        
        return result
    
    def _generate_guidance(self, subsystem: str, total: int, open_count: int, by_type: Dict) -> str:
        """Generate helpful guidance for next actions based on the data."""
        suggestions = []
        
        if open_count > 0:
            suggestions.append(f"Found {open_count} open ITRs")
            
            # Find types with most open ITRs
            type_open = [(t, data["open"]) for t, data in by_type.items() if data["open"] > 0]
            type_open.sort(key=lambda x: x[1], reverse=True)
            
            if type_open:
                top_type = type_open[0]
                suggestions.append(f"Most open ITRs are {top_type[0]} ({top_type[1]} open)")
        
        if open_count == 0:
            suggestions.append("All ITRs completed! ✅")
        
        suggestions.append("Ask about specific ITR types, compare with other subsystems, or search for related subsystems")
        
        return ". ".join(suggestions)
    
    def search_subsystems(self, pattern: str = None) -> Dict:
        """
        Smart subsystem discovery and search with description support.
        Searches both subsystem IDs and descriptions for comprehensive results.
        """
        if self.data is None or self.data.empty:
            return {
                "error": "No data loaded",
                "guidance": "Try reloading data with manage_cache tool"
            }
        
        # Get unique subsystems with their descriptions
        unique_subsystems = self.data.groupby('SubSystem')['SubSystem Descr.'].first().reset_index()
        all_subsystems = sorted(unique_subsystems['SubSystem'].tolist())
        
        if pattern:
            # Case-insensitive partial matching on both ID and description
            pattern_lower = pattern.lower()
            matching_subsystems = []
            
            for _, row in unique_subsystems.iterrows():
                subsystem_id = row['SubSystem']
                description = str(row['SubSystem Descr.']) if pd.notna(row['SubSystem Descr.']) else ""
                
                # Search in both ID and description
                id_match = pattern_lower in subsystem_id.lower()
                desc_match = pattern_lower in description.lower()
                
                if id_match or desc_match:
                    # Determine match type - prefer ID match if both match
                    match_type = "id" if id_match else "description"
                    if id_match and desc_match:
                        match_type = "both"
                    
                    matching_subsystems.append({
                        "id": subsystem_id,
                        "description": description,
                        "match_type": match_type
                    })
            
            result = {
                "pattern": pattern,
                "found": len(matching_subsystems),
                "total_available": len(all_subsystems),
                "matches": matching_subsystems
            }
            
            if matching_subsystems:
                id_matches = sum(1 for m in matching_subsystems if m["match_type"] == "id")
                desc_matches = len(matching_subsystems) - id_matches
                result["guidance"] = f"Found {len(matching_subsystems)} subsystems matching '{pattern}' ({id_matches} by ID, {desc_matches} by description). Use query_subsystem_itrs() to get ITR details for any subsystem"
            else:
                result["guidance"] = f"No subsystems found matching '{pattern}' in either ID or description. Try a different pattern"
            
        else:
            # Return overview of all subsystems with descriptions
            all_with_desc = []
            for _, row in unique_subsystems.iterrows():
                all_with_desc.append({
                    "id": row['SubSystem'],
                    "description": str(row['SubSystem Descr.']) if pd.notna(row['SubSystem Descr.']) else "No description"
                })
            
            result = {
                "total_subsystems": len(all_subsystems),
                "subsystems": all_with_desc,
                "guidance": f"Found {len(all_subsystems)} total subsystems. Use search pattern to find by ID or description, or query_subsystem_itrs() for specific subsystem details"
            }
        
        return result
    
    def search_systems(self, pattern: str = None) -> Dict:
        """
        Smart system discovery and search with description support.
        Searches both system IDs and descriptions and returns connected subsystems.
        """
        if self.data is None or self.data.empty:
            return {
                "error": "No data loaded",
                "guidance": "Try reloading data with manage_cache tool"
            }
        
        # Get unique systems with their descriptions and connected subsystems
        unique_systems = self.data.groupby('System').agg({
            'System Descr.': 'first',
            'SubSystem': list
        }).reset_index()
        
        all_systems = sorted(unique_systems['System'].tolist())
        
        if pattern:
            # Case-insensitive partial matching on both ID and description
            pattern_lower = pattern.lower()
            matching_systems = []
            
            for _, row in unique_systems.iterrows():
                system_id = row['System']
                description = str(row['System Descr.']) if pd.notna(row['System Descr.']) else ""
                subsystems = sorted(list(set(row['SubSystem'])))  # Remove duplicates and sort
                
                # Search in both ID and description
                id_match = pattern_lower in system_id.lower()
                desc_match = pattern_lower in description.lower()
                
                if id_match or desc_match:
                    # Determine match type
                    match_type = "id" if id_match else "description"
                    if id_match and desc_match:
                        match_type = "both"
                    
                    matching_systems.append({
                        "id": system_id,
                        "description": description,
                        "subsystems": subsystems,
                        "total_subsystems": len(subsystems),
                        "match_type": match_type
                    })
            
            result = {
                "pattern": pattern,
                "found": len(matching_systems),
                "total_available": len(all_systems),
                "matches": matching_systems
            }
            
            if matching_systems:
                id_matches = sum(1 for m in matching_systems if m["match_type"] in ["id", "both"])
                desc_matches = sum(1 for m in matching_systems if m["match_type"] in ["description", "both"])
                result["guidance"] = f"Found {len(matching_systems)} systems matching '{pattern}' ({id_matches} by ID, {desc_matches} by description). Use query_subsystem_itrs() to get ITR details for any subsystem"
            else:
                result["guidance"] = f"No systems found matching '{pattern}' in either ID or description. Try a different pattern"
            
        else:
            # Return overview of all systems with their subsystems
            all_with_desc = []
            for _, row in unique_systems.iterrows():
                subsystems = sorted(list(set(row['SubSystem'])))  # Remove duplicates and sort
                all_with_desc.append({
                    "id": row['System'],
                    "description": str(row['System Descr.']) if pd.notna(row['System Descr.']) else "No description",
                    "subsystems": subsystems,
                    "total_subsystems": len(subsystems)
                })
            
            result = {
                "total_systems": len(all_systems),
                "systems": all_with_desc,
                "guidance": f"Found {len(all_systems)} total systems. Use search pattern to find by ID or description, or query_subsystem_itrs() for specific subsystem details"
            }
        
        return result
    
    def manage_cache(self, action: str) -> Dict:
        """
        Unified cache management tool.
        """
        if action == "status":
            try:
                if self.cache_info_file.exists():
                    with open(self.cache_info_file, 'rb') as f:
                        cache_info = pickle.load(f)
                    
                    age_mins = (time.time() - cache_info['cached_at']) / 60
                    is_valid = self._is_cache_valid()
                    
                    return {
                        "action": "status",
                        "cache_exists": True,
                        "record_count": cache_info['record_count'],
                        "age_minutes": round(age_mins, 1),
                        "is_valid": is_valid,
                        "status": "✅ Valid" if is_valid else "❌ Outdated",
                        "guidance": "Cache is current - fast queries enabled" if is_valid else "Cache outdated - will reload from Excel on next query"
                    }
                else:
                    return {
                        "action": "status",
                        "cache_exists": False,
                        "guidance": "No cache exists - data will load fresh from Excel file"
                    }
            except Exception as e:
                return {"action": "status", "error": f"Cache status error: {e}"}
        
        elif action == "reload":
            try:
                # Clear cache files
                if self.cache_file.exists():
                    self.cache_file.unlink()
                if self.cache_info_file.exists():
                    self.cache_info_file.unlink()
                
                print("🔄 Forcing reload from Excel file...")
                self._load_data()
                
                if self.data is not None and not self.data.empty:
                    return {
                        "action": "reload",
                        "success": True,
                        "record_count": len(self.data),
                        "guidance": "Data reloaded successfully - all queries now use fresh data"
                    }
                else:
                    return {
                        "action": "reload",
                        "success": False,
                        "error": "Failed to reload data",
                        "guidance": "Check if Excel file exists and is accessible"
                    }
            except Exception as e:
                return {"action": "reload", "error": f"Reload failed: {e}"}
        
        else:
            return {
                "error": f"Unknown action '{action}'",
                "guidance": "Use action='status' to check cache or action='reload' to refresh data"
            }


# Global instance with thread safety
_processor = None
_processor_lock = threading.Lock()

def get_processor() -> ITRProcessor:
    """Get the global processor instance with thread safety."""
    global _processor
    if _processor is None:
        with _processor_lock:
            # Double-check pattern to avoid race condition
            if _processor is None:
                _processor = ITRProcessor()
    return _processor


@tool
def query_subsystem_itrs(subsystem: str) -> str:
    """
    Get comprehensive ITR status information for any subsystem. Use when user asks about ITR counts, 
    status, completion rates, specific types (ITR-A/B/C), or analysis for a subsystem.
    
    Returns complete breakdown including overall counts, type-specific breakdown, completion rates,
    and guidance for next actions. LLM should extract and present only what user requested.
    
    Args:
        subsystem: The SubSystem ID to query (e.g., "7-1100-P-01-05")
    """
    processor = get_processor()
    result = processor.get_subsystem_data(subsystem)
    
    if "error" in result:
        return f"❌ Error: {result['error']}\n💡 {result['guidance']}"
    
    # Format comprehensive response
    overall = result['overall']
    by_type = result['by_type']
    
    response = f"""📊 ITR Status for SubSystem: {result['subsystem']}

📈 OVERALL SUMMARY:
• Total ITRs: {overall['total']}
• Open ITRs: {overall['open']} ({overall['not_started']} not started, {overall['ongoing']} ongoing)
• Completed ITRs: {overall['completed']}
• Completion Rate: {result['completion_rate']}%

🔍 BREAKDOWN BY TYPE:"""
    
    for itr_type, data in by_type.items():
        response += f"""
• {itr_type}: {data['total']} total | {data['open']} open | {data['completed']} completed"""
    
    response += f"\n\n💡 {result['guidance']}"
    
    return response


@tool
def search_subsystems(pattern: str = None) -> str:
    """
    Find subsystems by ID pattern or description content. Use when user wants to find subsystems
    containing specific text in either the subsystem ID or description (e.g., "nitrogen", "pump", "valve").
    
    Returns matching subsystem IDs with descriptions and guidance for next steps.
    
    Args:
        pattern: Optional pattern for filtering by ID or description (e.g., "7-1100", "nitrogen", "pump"). Leave empty to see all available subsystems.
    """
    processor = get_processor()
    result = processor.search_subsystems(pattern)
    
    if "error" in result:
        return f"❌ Error: {result['error']}\n💡 {result['guidance']}"
    
    if pattern:
        response = f"🔍 Search Results for '{result['pattern']}':\n"
        response += f"Found {result['found']} of {result['total_available']} subsystems\n\n"
        
        if result.get('matches'):
            response += "📋 Matching Subsystems:\n"
            for match in result['matches']:
                if isinstance(match, dict):
                    match_indicator = "🆔" if match['match_type'] == 'id' else "📝"
                    response += f"• {match_indicator} {match['id']}\n"
                    if match['description']:
                        response += f"   Description: {match['description']}\n"
                else:
                    # Backward compatibility for old format
                    response += f"• {match}\n"
            
        
    else:
        response = f"📊 Subsystem Overview:\n"
        response += f"Total Available: {result['total_subsystems']}\n\n"
        response += "📋 All Subsystems:\n"
        
        for item in result['subsystems']:
            if isinstance(item, dict):
                response += f"• {item['id']}\n"
                if item['description'] and item['description'] != "No description":
                    response += f"   Description: {item['description']}\n"
            else:
                # Backward compatibility for old format
                response += f"• {item}\n"
    
    response += f"\n💡 {result['guidance']}"
    
    return response


@tool
def search_systems(pattern: str = None) -> str:
    """
    Find systems by ID pattern or description content. Use when user wants to find systems
    containing specific text in either the system ID or description. Returns system info
    with connected subsystem IDs.
    
    Returns matching system IDs with descriptions, connected subsystems, and guidance for next steps.
    
    Args:
        pattern: Optional pattern for filtering by ID or description (e.g., "7-1100", "pump", "valve"). Leave empty to see all available systems.
    """
    processor = get_processor()
    result = processor.search_systems(pattern)
    
    if "error" in result:
        return f"❌ Error: {result['error']}\n💡 {result['guidance']}"
    
    if pattern:
        response = f"🔍 System Search Results for '{result['pattern']}':\n"
        response += f"Found {result['found']} of {result['total_available']} systems\n\n"
        
        if result.get('matches'):
            response += "📋 Matching Systems:\n"
            for match in result['matches']:
                if isinstance(match, dict):
                    match_indicator = {"id": "🆔", "description": "📝", "both": "🔗"}.get(match['match_type'], "🔍")
                    response += f"• {match_indicator} {match['id']}\n"
                    if match['description']:
                        response += f"   Description: {match['description']}\n"
                    response += f"   Connected SubSystems ({match['total_subsystems']}): {', '.join(match['subsystems'])}\n"
                else:
                    # Backward compatibility for old format
                    response += f"• {match}\n"
        
    else:
        response = f"📊 System Overview:\n"
        response += f"Total Available: {result['total_systems']}\n\n"
        response += "📋 All Systems:\n"
        
        for item in result['systems']:
            if isinstance(item, dict):
                response += f"• {item['id']}\n"
                if item['description'] and item['description'] != "No description":
                    response += f"   Description: {item['description']}\n"
                response += f"   Connected SubSystems ({item['total_subsystems']}): {', '.join(item['subsystems'])}\n"
            else:
                # Backward compatibility for old format
                response += f"• {item}\n"
    
    response += f"\n💡 {result['guidance']}"
    
    return response


@tool  
def manage_cache(action: str) -> str:
    """
    Manage Excel data cache for performance. Use to check cache status or force data refresh.
    Common actions: check current cache state, reload data after Excel file changes.
    
    Returns cache information and guidance for optimization.
    
    Args:
        action: Action to perform - "status" to check cache age and validity, "reload" to force refresh from Excel file
    """
    processor = get_processor()
    result = processor.manage_cache(action)
    
    if "error" in result:
        return f"❌ Error: {result['error']}\n💡 {result.get('guidance', 'Try action=\"status\" or action=\"reload\"')}"
    
    if action == "status":
        if result['cache_exists']:
            response = f"💾 Cache Status: {result['status']}\n"
            response += f"📊 Records: {result['record_count']:,}\n"
            response += f"⏰ Age: {result['age_minutes']} minutes\n"
        else:
            response = "💾 Cache Status: No cache exists\n"
        
        response += f"💡 {result['guidance']}"
        
    elif action == "reload":
        if result['success']:
            response = f"✅ Data Reloaded Successfully\n"
            response += f"📊 Loaded: {result['record_count']:,} records\n"
        else:
            response = f"❌ Reload Failed\n"
        
        response += f"💡 {result['guidance']}"
    
    return response