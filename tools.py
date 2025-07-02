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
        
        try:
            with open(self.cache_info_file, 'rb') as f:
                cache_info = pickle.load(f)
            
            excel_mtime = self._get_file_modification_time()
            cache_mtime = cache_info.get('file_mtime', 0)
            
            return cache_mtime >= excel_mtime
        except Exception:
            return False
    
    def _save_cache(self, data: pd.DataFrame):
        """Save DataFrame and metadata to cache."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            cache_info = {
                'file_mtime': self._get_file_modification_time(),
                'cached_at': time.time(),
                'record_count': len(data)
            }
            with open(self.cache_info_file, 'wb') as f:
                pickle.dump(cache_info, f)
            
            print(f"✅ Cached {len(data)} records for faster future access")
        except Exception as e:
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
            
            required_columns = ["SubSystem", "ITR", "End Cert."]
            
            df = pd.read_excel(
                self.excel_file,
                usecols=required_columns,
                dtype={
                    "SubSystem": "string",
                    "ITR": "string", 
                    "End Cert.": "string"
                },
                engine="openpyxl",
                na_filter=True,
            )
            
            load_time = time.time() - start_time
            
            # Data cleaning
            df["SubSystem"] = df["SubSystem"].astype(str).str.strip()
            df["ITR"] = df["ITR"].astype(str).str.strip()
            df["End Cert."] = df["End Cert."].fillna("").astype(str).str.strip()
            df = df.dropna(subset=["SubSystem", "ITR"], how="all")
            
            self.data = df
            print(f"✅ Loaded {len(self.data)} ITR records in {load_time:.2f}s")
            self._save_cache(self.data)
            
        except Exception as e:
            print(f"❌ Error loading Excel file: {e}")
            self.data = pd.DataFrame()
    
    def get_itr_status(self, end_cert_value: str) -> str:
        """Determine ITR status from End Cert. value."""
        if not end_cert_value or end_cert_value.strip() == "":
            return "not_started"
        elif end_cert_value.upper() == "N":
            return "ongoing"
        elif end_cert_value.upper() == "Y":
            return "completed"
        else:
            return "unknown"
    
    def query_comprehensive_subsystem_data(self, subsystem: str) -> Dict:
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
        status_counts = {"not_started": 0, "ongoing": 0, "completed": 0}
        
        for _, row in subsystem_data.iterrows():
            status = self.get_itr_status(row["End Cert."])
            status_counts[status] += 1
        
        open_itrs = status_counts["not_started"] + status_counts["ongoing"]
        
        # Calculate by-type breakdown
        by_type = {}
        for itr_type in ["ITR-A", "ITR-B", "ITR-C"]:
            type_data = subsystem_data[subsystem_data["ITR"] == itr_type]
            type_status_counts = {"not_started": 0, "ongoing": 0, "completed": 0}
            
            for _, row in type_data.iterrows():
                status = self.get_itr_status(row["End Cert."])
                type_status_counts[status] += 1
            
            type_open = type_status_counts["not_started"] + type_status_counts["ongoing"]
            
            by_type[itr_type] = {
                "total": len(type_data),
                "open": type_open,
                "completed": type_status_counts["completed"],
                "not_started": type_status_counts["not_started"],
                "ongoing": type_status_counts["ongoing"]
            }
        
        # Create comprehensive response
        result = {
            "subsystem": subsystem,
            "overall": {
                "total": total_itrs,
                "open": open_itrs,
                "completed": status_counts["completed"],
                "not_started": status_counts["not_started"],
                "ongoing": status_counts["ongoing"]
            },
            "by_type": by_type,
            "completion_rate": round(status_counts["completed"] / total_itrs * 100, 1) if total_itrs > 0 else 0,
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
    
    def search_subsystems(self, pattern: str = None, limit: int = 20) -> Dict:
        """
        Smart subsystem discovery and search.
        """
        if self.data is None or self.data.empty:
            return {
                "error": "No data loaded",
                "guidance": "Try reloading data with manage_cache tool"
            }
        
        all_subsystems = sorted(self.data["SubSystem"].unique())
        
        if pattern:
            # Case-insensitive partial matching
            pattern_lower = pattern.lower()
            matching = [s for s in all_subsystems if pattern_lower in s.lower()]
            
            result = {
                "pattern": pattern,
                "found": len(matching),
                "total_available": len(all_subsystems),
                "matches": matching[:limit]
            }
            
            if len(matching) > limit:
                result["truncated"] = f"Showing first {limit} of {len(matching)} matches"
            
            if matching:
                result["guidance"] = f"Found {len(matching)} subsystems matching '{pattern}'. Use query_subsystem_itrs() to get ITR details for any subsystem"
            else:
                result["guidance"] = f"No subsystems found matching '{pattern}'. Try a shorter or different pattern"
            
        else:
            # Return overview of all subsystems
            result = {
                "total_subsystems": len(all_subsystems),
                "sample": all_subsystems[:limit],
                "guidance": f"Found {len(all_subsystems)} total subsystems. Use search pattern to narrow down or query_subsystem_itrs() for specific subsystem details"
            }
            
            if len(all_subsystems) > limit:
                result["truncated"] = f"Showing first {limit} of {len(all_subsystems)} subsystems"
        
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


# Global instance
_processor = None

def get_processor() -> ITRProcessor:
    """Get the global processor instance."""
    global _processor
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
    result = processor.query_comprehensive_subsystem_data(subsystem)
    
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
    Find subsystems by name pattern or get overview of available subsystems. Use when user wants to
    find subsystems containing specific text, discover available subsystems, or get list of subsystems to query.
    
    Returns matching subsystem IDs with guidance for next steps.
    
    Args:
        pattern: Optional pattern for filtering (e.g., "7-1100", "P-01"). Leave empty to see all available subsystems.
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
            for subsystem in result['matches']:
                response += f"• {subsystem}\n"
            
            if result.get('truncated'):
                response += f"\n⚠️ {result['truncated']}"
        
    else:
        response = f"📊 Subsystem Overview:\n"
        response += f"Total Available: {result['total_subsystems']}\n\n"
        response += "📋 Sample Subsystems:\n"
        
        for subsystem in result['sample']:
            response += f"• {subsystem}\n"
        
        if result.get('truncated'):
            response += f"\n⚠️ {result['truncated']}"
    
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