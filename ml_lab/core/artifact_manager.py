"""Artifact Manager - Organizes and manages project artifacts.

This module implements the ArtifactManager which organizes artifacts by project
and manages their storage, retrieval, and cleanup. Artifacts include datasets,
EDA results, preprocessing objects, trained models, validation results, reports,
and other outputs from the ML pipeline.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .project import ProjectSpecification


class ArtifactManager:
    """Manages project artifacts with organized directory structure.
    
    The ArtifactManager creates and maintains a structured directory layout
    for each project, organizing artifacts by type (dataset, eda, preprocessing,
    experiments, validation, tuning, statistics, comparison, models, reports, inference).
    """
    
    def __init__(self, base_dir: Path):
        """Initialize the artifact manager.
        
        Args:
            base_dir: Base directory for all projects
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_project_structure(self, project_id: str) -> Path:
        """Create the directory structure for a project.
        
        Args:
            project_id: Unique project identifier
        
        Returns:
            Path to the project directory
        """
        project_dir = self.base_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different artifact types
        (project_dir / "dataset").mkdir(exist_ok=True)
        (project_dir / "eda").mkdir(exist_ok=True)
        (project_dir / "preprocessing").mkdir(exist_ok=True)
        (project_dir / "experiments").mkdir(exist_ok=True)
        (project_dir / "validation").mkdir(exist_ok=True)
        (project_dir / "tuning").mkdir(exist_ok=True)
        (project_dir / "statistics").mkdir(exist_ok=True)
        (project_dir / "comparison").mkdir(exist_ok=True)
        (project_dir / "models").mkdir(exist_ok=True)
        (project_dir / "reports").mkdir(exist_ok=True)
        (project_dir / "inference").mkdir(exist_ok=True)
        
        return project_dir
    
    def get_project_dir(self, project_id: str) -> Path:
        """Get the project directory.
        
        Args:
            project_id: Unique project identifier
        
        Returns:
            Path to the project directory
        """
        return self.base_dir / project_id
    
    def get_artifact_dir(self, project_id: str, artifact_type: str) -> Path:
        """Get the directory for a specific artifact type.
        
        Args:
            project_id: Unique project identifier
            artifact_type: Type of artifact (dataset, eda, preprocessing, etc.)
        
        Returns:
            Path to the artifact directory
        """
        project_dir = self.get_project_dir(project_id)
        return project_dir / artifact_type
    
    def save_artifact(
        self,
        project_id: str,
        artifact_type: str,
        artifact_name: str,
        data: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Save an artifact to the appropriate directory.
        
        Args:
            project_id: Unique project identifier
            artifact_type: Type of artifact
            artifact_name: Name of the artifact
            data: Artifact data (can be dict, list, or any serializable object)
            metadata: Optional metadata to save alongside the artifact
        
        Returns:
            Path to the saved artifact
        """
        artifact_dir = self.get_artifact_dir(project_id, artifact_type)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        artifact_path = artifact_dir / artifact_name
        
        # Save based on file extension
        if artifact_name.endswith(".json"):
            artifact_dict = {"data": data, "metadata": metadata or {}}
            with open(artifact_path, "w", encoding="utf-8") as f:
                json.dump(artifact_dict, f, indent=2, default=str)
        elif artifact_name.endswith(".csv"):
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                data.to_csv(artifact_path, index=False)
            else:
                pd.DataFrame(data).to_csv(artifact_path, index=False)
        elif artifact_name.endswith(".parquet"):
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                data.to_parquet(artifact_path, index=False)
            else:
                pd.DataFrame(data).to_parquet(artifact_path, index=False)
        elif artifact_name.endswith(".pkl"):
            import pickle
            with open(artifact_path, "wb") as f:
                pickle.dump(data, f)
        elif artifact_name.endswith(".pt"):
            import torch
            torch.save(data, artifact_path)
        elif artifact_name.endswith(".html") or artifact_name.endswith(".md"):
            with open(artifact_path, "w", encoding="utf-8") as f:
                f.write(str(data))
        else:
            # Default to JSON
            artifact_dict = {"data": data, "metadata": metadata or {}}
            with open(artifact_path.with_suffix(".json"), "w", encoding="utf-8") as f:
                json.dump(artifact_dict, f, indent=2, default=str)
        
        return artifact_path
    
    def load_artifact(
        self,
        project_id: str,
        artifact_type: str,
        artifact_name: str,
    ) -> Any:
        """Load an artifact from the appropriate directory.
        
        Args:
            project_id: Unique project identifier
            artifact_type: Type of artifact
            artifact_name: Name of the artifact
        
        Returns:
            Loaded artifact data
        """
        artifact_dir = self.get_artifact_dir(project_id, artifact_type)
        artifact_path = artifact_dir / artifact_name
        
        if not artifact_path.exists():
            raise FileNotFoundError(f"Artifact not found: {artifact_path}")
        
        # Load based on file extension
        if artifact_name.endswith(".json"):
            with open(artifact_path, "r", encoding="utf-8") as f:
                artifact_dict = json.load(f)
            if isinstance(artifact_dict, dict):
                return artifact_dict.get("data", artifact_dict)
            return artifact_dict
        elif artifact_name.endswith(".csv"):
            import pandas as pd
            return pd.read_csv(artifact_path)
        elif artifact_name.endswith(".parquet"):
            import pandas as pd
            return pd.read_parquet(artifact_path)
        elif artifact_name.endswith(".pkl"):
            import pickle
            with open(artifact_path, "rb") as f:
                return pickle.load(f)
        elif artifact_name.endswith(".pt"):
            import torch
            return torch.load(artifact_path, map_location="cpu")
        elif artifact_name.endswith(".html") or artifact_name.endswith(".md"):
            with open(artifact_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            # Try to load as JSON
            with open(artifact_path, "r", encoding="utf-8") as f:
                artifact_dict = json.load(f)
            return artifact_dict.get("data", artifact_dict)
    
    def list_artifacts(
        self, project_id: str, artifact_type: Optional[str] = None
    ) -> List[Path]:
        """List artifacts for a project.
        
        Args:
            project_id: Unique project identifier
            artifact_type: Optional artifact type to filter by
        
        Returns:
            List of artifact paths
        """
        if artifact_type:
            artifact_dir = self.get_artifact_dir(project_id, artifact_type)
        else:
            artifact_dir = self.get_project_dir(project_id)
        
        if not artifact_dir.exists():
            return []
        
        return list(artifact_dir.glob("*"))
    
    def get_artifact_metadata(
        self, project_id: str, artifact_type: str, artifact_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get metadata for an artifact."""
        try:
            artifact_dir = self.get_artifact_dir(project_id, artifact_type)
            if artifact_name.endswith(".json"):
                artifact_path = artifact_dir / artifact_name
                if artifact_path.exists():
                    with open(artifact_path, "r", encoding="utf-8") as f:
                        content = json.load(f)
                        return content.get("data", content)
            else:
                meta_path = artifact_dir / f"{Path(artifact_name).stem}_metadata.json"
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        content = json.load(f)
                        return content.get("data", content)
            return None
        except Exception:
            return None

    def delete_artifact(
        self, project_id: str, artifact_type: str, artifact_name: str
    ) -> None:
        """Delete an artifact.
        
        Args:
            project_id: Unique project identifier
            artifact_type: Type of artifact
            artifact_name: Name of the artifact
        """
        artifact_dir = self.get_artifact_dir(project_id, artifact_type)
        artifact_path = artifact_dir / artifact_name
        
        if artifact_path.exists():
            artifact_path.unlink()
    
    def delete_artifact_type(self, project_id: str, artifact_type: str) -> None:
        """Delete all artifacts of a specific type.
        
        Args:
            project_id: Unique project identifier
            artifact_type: Type of artifact to delete
        """
        artifact_dir = self.get_artifact_dir(project_id, artifact_type)
        if artifact_dir.exists():
            shutil.rmtree(artifact_dir)
            artifact_dir.mkdir(exist_ok=True)
    
    def delete_project(self, project_id: str) -> None:
        """Delete all artifacts for a project.
        
        Args:
            project_id: Unique project identifier
        """
        project_dir = self.get_project_dir(project_id)
        if project_dir.exists():
            shutil.rmtree(project_dir)
    
    def save_project_specification(
        self, spec: ProjectSpecification
    ) -> Path:
        """Save the project specification.
        
        Args:
            spec: Project specification
        
        Returns:
            Path to the saved specification
        """
        project_dir = self.create_project_structure(spec.project_id)
        spec_path = project_dir / "project_specification.json"
        spec.save(spec_path)
        
        # Update spec with artifact paths
        spec.project_dir = project_dir
        spec.artifacts_dir = project_dir
        spec.models_dir = project_dir / "models"
        spec.reports_dir = project_dir / "reports"
        
        return spec_path
    
    def load_project_specification(self, project_id: str) -> ProjectSpecification:
        """Load the project specification.
        
        Args:
            project_id: Unique project identifier
        
        Returns:
            Loaded project specification
        """
        from .project import ProjectSpecification
        project_dir = self.get_project_dir(project_id)
        spec_path = project_dir / "project_specification.json"
        return ProjectSpecification.load(spec_path)
    
    def get_artifact_metadata(
        self, project_id: str, artifact_type: str, artifact_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get metadata for an artifact.
        
        Args:
            project_id: Unique project identifier
            artifact_type: Type of artifact
            artifact_name: Name of the artifact
        
        Returns:
            Metadata dictionary or None if not available
        """
        artifact_dir = self.get_artifact_dir(project_id, artifact_type)
        artifact_path = artifact_dir / artifact_name
        
        if not artifact_path.exists():
            return None
        
        if artifact_name.endswith(".json"):
            with open(artifact_path, "r", encoding="utf-8") as f:
                artifact_dict = json.load(f)
            return artifact_dict.get("metadata")
        
        return None
    
    def get_project_size(self, project_id: str) -> Dict[str, float]:
        """Get the size of a project in bytes.
        
        Args:
            project_id: Unique project identifier
        
        Returns:
            Dictionary with total size and sizes by artifact type
        """
        project_dir = self.get_project_dir(project_id)
        
        if not project_dir.exists():
            return {"total": 0.0}
        
        total_size = 0.0
        sizes_by_type = {}
        
        for item in project_dir.rglob("*"):
            if item.is_file():
                size = item.stat().st_size
                total_size += size
                
                # Categorize by parent directory
                artifact_type = item.parent.name
                if artifact_type not in sizes_by_type:
                    sizes_by_type[artifact_type] = 0.0
                sizes_by_type[artifact_type] += size
        
        sizes_by_type["total"] = total_size
        return sizes_by_type
    
    def list_projects(self) -> List[str]:
        """List all project IDs.
        
        Returns:
            List of project IDs
        """
        if not self.base_dir.exists():
            return []
        
        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]


# Global artifact manager instance
_artifact_manager: Optional[ArtifactManager] = None


def get_artifact_manager(base_dir: Optional[Path] = None) -> ArtifactManager:
    """Get the global artifact manager instance.
    
    Args:
        base_dir: Optional base directory (uses default if not provided)
    
    Returns:
        ArtifactManager instance
    """
    global _artifact_manager
    if _artifact_manager is None:
        if base_dir is None:
            base_dir = Path.cwd() / "projects"
        _artifact_manager = ArtifactManager(base_dir)
    return _artifact_manager
