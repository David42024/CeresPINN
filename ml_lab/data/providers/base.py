"""Abstract base class for data providers in ML Lab.

This module provides the base class for all data providers, ensuring a uniform
contract for data extraction, loading, and management. This is a generalized
version adapted from CeresPINN's provider_base.py for use in ML Lab.
"""
from __future__ import annotations

import abc
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


class DataProviderError(RuntimeError):
    """Raised when a provider cannot complete its data operation."""
    pass


class BaseProvider(abc.ABC):
    """Base class with common helpers for data providers.
    
    This class provides common functionality for logging, progress reporting,
    artifact saving, and manifest generation. All data providers should inherit
    from this class and implement the extract() method.
    """
    
    name: str = "base"
    
    def __init__(self, config: Any, progress: Optional[Any] = None) -> None:
        """Initialize the data provider.
        
        Args:
            config: Configuration object for the provider
            progress: Optional callback function for progress reporting
        """
        self.config = config
        self.progress = progress or (lambda *a, **k: None)
        self.log: List[Dict[str, Any]] = []
    
    # -- Helpers -------------------------------------------------------------
    def log_step(self, message: str, **kwargs: Any) -> None:
        """Log a step in the data provider operation.
        
        Args:
            message: Log message
            **kwargs: Additional key-value pairs to log
        """
        entry = {"time": datetime.now(timezone.utc).isoformat(), "message": message}
        entry.update(kwargs)
        self.log.append(entry)
        print(f"[{self.name}] {message}")
    
    def set_progress(self, step: int, total: int, stage: str) -> None:
        """Report coarse progress to a registered callback.
        
        Args:
            step: Current step number
            total: Total number of steps
            stage: Current stage name
        """
        try:
            self.progress({"step": step, "total": total, "stage": stage})
        except Exception:
            # Progress reporting must never break the operation
            pass
    
    def write_snapshot(self, path: Path, data: Any) -> None:
        """Write data to a file based on its extension.
        
        Args:
            path: Path to write the file
            data: Data to write (can be DataFrame, dict, or list)
        """
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        
        if path.suffix == ".json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, ensure_ascii=False, indent=2, default=str, f=f)
        elif path.suffix == ".csv":
            if isinstance(data, pd.DataFrame):
                data.to_csv(path, index=False)
            else:
                pd.DataFrame(data).to_csv(path, index=False)
        elif path.suffix == ".parquet":
            if isinstance(data, pd.DataFrame):
                data.to_parquet(path, index=False)
            else:
                pd.DataFrame(data).to_parquet(path, index=False)
        else:
            # Default to CSV
            if isinstance(data, pd.DataFrame):
                data.to_csv(path, index=False)
            else:
                pd.DataFrame(data).to_csv(path, index=False)
    
    def write_manifest(
        self,
        directory: Path,
        records: int,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Write a manifest file for the extracted data.
        
        Args:
            directory: Directory to write the manifest
            records: Number of records extracted
            extra: Optional additional metadata
        
        Returns:
            Path to the manifest file
        """
        manifest = {
            "provider": self.name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "records": records,
        }
        if extra:
            manifest.update(extra)
        manifest_path = directory / f"{self.name}_manifest.json"
        self.write_snapshot(manifest_path, manifest)
        return manifest_path
    
    def throttled(self, delay: float = 1.0) -> None:
        """Add a delay to be polite to public APIs.
        
        Args:
            delay: Delay in seconds
        """
        time.sleep(delay)
    
    # -- Public interface ----------------------------------------------------
    def run(self) -> Dict[str, Any]:
        """Execute the data provider operation and return a summary.
        
        Returns:
            Dictionary with operation summary
        """
        start = time.time()
        self.log_step(f"Starting {self.name} operation")
        try:
            result = self.extract()
        except DataProviderError as exc:
            self.log_step(f"Operation failed: {exc}")
            raise
        elapsed = round(time.time() - start, 2)
        summary = {"provider": self.name, "elapsed_seconds": elapsed, **result}
        self.log_step(f"Finished {self.name} in {elapsed}s")
        return summary
    
    @abc.abstractmethod
    def extract(self) -> Dict[str, Any]:
        """Perform the provider-specific data extraction.
        
        This method must be implemented by all subclasses.
        
        Returns:
            Dictionary with extraction results
        """
        pass
    
    @abc.abstractmethod
    def load(self) -> pd.DataFrame:
        """Load the data as a pandas DataFrame.
        
        This method must be implemented by all subclasses.
        
        Returns:
            DataFrame with the loaded data
        """
        pass


class GenericProvider(BaseProvider):
    """Generic provider for common file formats (CSV, Parquet, JSON, Excel).
    
    This provider can load data from various file formats without requiring
    a specialized provider implementation.
    """
    
    name = "generic"
    
    def __init__(self, config: Any, progress: Optional[Any] = None) -> None:
        """Initialize the generic provider.
        
        Args:
            config: Configuration with 'file_path' key
            progress: Optional callback for progress reporting
        """
        super().__init__(config, progress)
        self.file_path = Path(config.file_path) if hasattr(config, "file_path") else None
    
    def extract(self) -> Dict[str, Any]:
        """Extract data from the file.
        
        Returns:
            Dictionary with extraction results
        """
        if self.file_path is None or not self.file_path.exists():
            raise DataProviderError(f"File not found: {self.file_path}")
        
        self.log_step(f"Loading data from {self.file_path}")
        
        try:
            df = self.load()
            return {
                "rows": len(df),
                "columns": len(df.columns),
                "file_path": str(self.file_path),
            }
        except Exception as e:
            raise DataProviderError(f"Failed to load data: {e}")
    
    def load(self) -> pd.DataFrame:
        """Load data from file based on extension.
        
        Returns:
            DataFrame with the loaded data
        """
        if self.file_path is None:
            raise DataProviderError("No file path configured")
        
        suffix = self.file_path.suffix.lower()
        
        if suffix == ".csv":
            return pd.read_csv(self.file_path)
        elif suffix == ".parquet":
            return pd.read_parquet(self.file_path)
        elif suffix in [".xlsx", ".xls"]:
            return pd.read_excel(self.file_path)
        elif suffix == ".json":
            return pd.read_json(self.file_path)
        else:
            raise DataProviderError(f"Unsupported file format: {suffix}")
