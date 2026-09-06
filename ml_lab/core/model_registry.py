"""Model Registry - Database integration for ML Lab models.

This module extends the CeresPINN database pattern to support ML Lab's
model registry, experiment tracking, and project management.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


class DatabaseUnavailable(Exception):
    """Raised when the database is not configured or cannot be reached."""


_engine: Optional[Engine] = None
_checked = False


def get_engine() -> Optional[Engine]:
    """Return a lazy, cached SQLAlchemy engine, or None if DB not configured."""
    global _engine, _checked
    if _checked:
        return _engine
    _checked = True
    if not _DATABASE_URL:
        return None
    try:
        _engine = create_engine(_DATABASE_URL, pool_pre_ping=True, pool_recycle=600)
        with _engine.connect():
            pass
    except SQLAlchemyError:
        _engine = None
    return _engine


def available() -> bool:
    return get_engine() is not None


@contextmanager
def _connect() -> Iterator[Any]:
    engine = get_engine()
    if engine is None:
        raise DatabaseUnavailable("DATABASE_URL no configurada o BD inalcanzable.")
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# ML Lab Schema Extension
# ---------------------------------------------------------------------------
_ML_LAB_SCHEMA = """
-- ML Lab Projects Table
CREATE TABLE IF NOT EXISTS ml_lab_projects (
    id TEXT PRIMARY KEY,
    project_name TEXT NOT NULL,
    description TEXT NOT NULL,
    domain TEXT NOT NULL,
    problem_type TEXT NOT NULL,
    data_type TEXT NOT NULL,
    objective TEXT NOT NULL,
    target_variable TEXT,
    business_objective TEXT NOT NULL,
    constraints TEXT NOT NULL DEFAULT '[]',
    dataset_path TEXT,
    dataset_source TEXT NOT NULL DEFAULT 'upload',
    dataset_version TEXT NOT NULL DEFAULT 'v1',
    status TEXT NOT NULL DEFAULT 'planned',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    specification TEXT NOT NULL DEFAULT '{}'
);

-- ML Lab Datasets Table
CREATE TABLE IF NOT EXISTS ml_lab_datasets (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    rows INT NOT NULL,
    columns INT NOT NULL,
    memory_mb DOUBLE PRECISION NOT NULL,
    numerical_features INT NOT NULL DEFAULT 0,
    categorical_features INT NOT NULL DEFAULT 0,
    temporal_features INT NOT NULL DEFAULT 0,
    total_missing_count INT NOT NULL DEFAULT 0,
    total_missing_percentage DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    has_duplicates BOOLEAN NOT NULL DEFAULT FALSE,
    has_outliers BOOLEAN NOT NULL DEFAULT FALSE,
    target_column TEXT,
    target_type TEXT,
    profile TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES ml_lab_projects(id) ON DELETE CASCADE
);

-- ML Lab Experiments Table
CREATE TABLE IF NOT EXISTS ml_lab_experiments (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    models TEXT NOT NULL DEFAULT '[]',
    hyperparameters TEXT NOT NULL DEFAULT '{}',
    validation_strategy TEXT NOT NULL,
    n_splits INT NOT NULL DEFAULT 5,
    test_size DOUBLE PRECISION NOT NULL DEFAULT 0.2,
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    results TEXT NOT NULL DEFAULT '{}',
    metrics TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES ml_lab_projects(id) ON DELETE CASCADE
);

-- ML Lab Models Table (Generalized)
CREATE TABLE IF NOT EXISTS ml_lab_models (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    experiment_id TEXT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    version TEXT NOT NULL,
    architecture TEXT NOT NULL,
    framework TEXT,
    parameters TEXT NOT NULL DEFAULT '{}',
    training_config TEXT NOT NULL DEFAULT '{}',
    metrics_global TEXT NOT NULL DEFAULT '{}',
    metrics_cv TEXT NOT NULL DEFAULT '{}',
    model_path TEXT,
    model_size_bytes BIGINT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    is_production BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'training',
    trained_at TEXT,
    registered_at TEXT NOT NULL,
    description TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (project_id) REFERENCES ml_lab_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (experiment_id) REFERENCES ml_lab_experiments(id) ON DELETE SET NULL
);

-- ML Lab Artifacts Table
CREATE TABLE IF NOT EXISTS ml_lab_artifacts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    experiment_id TEXT,
    model_id TEXT,
    artifact_type TEXT NOT NULL,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    size_bytes BIGINT,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES ml_lab_projects(id) ON DELETE CASCADE,
    FOREIGN KEY (experiment_id) REFERENCES ml_lab_experiments(id) ON DELETE SET NULL,
    FOREIGN KEY (model_id) REFERENCES ml_lab_models(id) ON DELETE SET NULL
);

-- ML Lab Reports Table
CREATE TABLE IF NOT EXISTS ml_lab_reports (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    report_type TEXT NOT NULL,
    format TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES ml_lab_projects(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ml_lab_projects_status ON ml_lab_projects(status);
CREATE INDEX IF NOT EXISTS idx_ml_lab_projects_created ON ml_lab_projects(created_at);
CREATE INDEX IF NOT EXISTS idx_ml_lab_experiments_project ON ml_lab_experiments(project_id);
CREATE INDEX IF NOT EXISTS idx_ml_lab_experiments_status ON ml_lab_experiments(status);
CREATE INDEX IF NOT EXISTS idx_ml_lab_models_project ON ml_lab_models(project_id);
CREATE INDEX IF NOT EXISTS idx_ml_lab_models_active ON ml_lab_models(is_active);
CREATE INDEX IF NOT EXISTS idx_ml_lab_models_production ON ml_lab_models(is_production);
CREATE INDEX IF NOT EXISTS idx_ml_lab_artifacts_project ON ml_lab_artifacts(project_id);
CREATE INDEX IF NOT EXISTS idx_ml_lab_artifacts_type ON ml_lab_artifacts(artifact_type);
"""


def init_ml_lab_db() -> None:
    """Create ML Lab tables if the database is configured. Never raises."""
    if not available():
        return
    try:
        with _connect() as conn:
            conn.execute(text(_ML_LAB_SCHEMA))
            conn.commit()
    except (SQLAlchemyError, DatabaseUnavailable):
        pass


# ---------------------------------------------------------------------------
# Project Operations
# ---------------------------------------------------------------------------
def save_project(project: Dict[str, Any]) -> bool:
    """Save or update a project in the database."""
    if not available():
        return False
    try:
        with _connect() as conn:
            conn.execute(
                text(
                    """INSERT INTO ml_lab_projects
                       (id, project_name, description, domain, problem_type, data_type,
                        objective, target_variable, business_objective, constraints,
                        dataset_path, dataset_source, dataset_version, status,
                        created_at, updated_at, specification)
                       VALUES (:id, :project_name, :description, :domain, :problem_type,
                               :data_type, :objective, :target_variable, :business_objective,
                               :constraints, :dataset_path, :dataset_source, :dataset_version,
                               :status, :created_at, :updated_at, :specification)
                       ON CONFLICT (id) DO UPDATE SET
                         project_name = EXCLUDED.project_name,
                         description = EXCLUDED.description,
                         domain = EXCLUDED.domain,
                         problem_type = EXCLUDED.problem_type,
                         data_type = EXCLUDED.data_type,
                         objective = EXCLUDED.objective,
                         target_variable = EXCLUDED.target_variable,
                         business_objective = EXCLUDED.business_objective,
                         constraints = EXCLUDED.constraints,
                         dataset_path = EXCLUDED.dataset_path,
                         dataset_source = EXCLUDED.dataset_source,
                         dataset_version = EXCLUDED.dataset_version,
                         status = EXCLUDED.status,
                         updated_at = EXCLUDED.updated_at,
                         specification = EXCLUDED.specification"""
                ),
                {
                    "id": project["id"],
                    "project_name": project["project_name"],
                    "description": project["description"],
                    "domain": project["domain"],
                    "problem_type": project["problem_type"],
                    "data_type": project["data_type"],
                    "objective": project["objective"],
                    "target_variable": project.get("target_variable"),
                    "business_objective": project["business_objective"],
                    "constraints": json.dumps(project.get("constraints", [])),
                    "dataset_path": str(project.get("dataset_path")) if project.get("dataset_path") else None,
                    "dataset_source": project.get("dataset_source", "upload"),
                    "dataset_version": project.get("dataset_version", "v1"),
                    "status": project.get("status", "planned"),
                    "created_at": project["created_at"],
                    "updated_at": project["updated_at"],
                    "specification": json.dumps(project.get("specification", {})),
                },
            )
            conn.commit()
            return True
    except (SQLAlchemyError, DatabaseUnavailable):
        return False


def list_projects(status: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """List all projects, optionally filtered by status."""
    if not available():
        return None
    try:
        with _connect() as conn:
            if status:
                rows = conn.execute(
                    text("SELECT * FROM ml_lab_projects WHERE status = :status ORDER BY created_at DESC"),
                    {"status": status}
                ).mappings().all()
            else:
                rows = conn.execute(
                    text("SELECT * FROM ml_lab_projects ORDER BY created_at DESC")
                ).mappings().all()
            
            return [
                {
                    "id": r["id"],
                    "project_name": r["project_name"],
                    "description": r["description"],
                    "domain": r["domain"],
                    "problem_type": r["problem_type"],
                    "data_type": r["data_type"],
                    "objective": r["objective"],
                    "target_variable": r["target_variable"],
                    "business_objective": r["business_objective"],
                    "constraints": json.loads(r["constraints"]) if r["constraints"] else [],
                    "dataset_path": r["dataset_path"],
                    "status": r["status"],
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                    "specification": json.loads(r["specification"]) if r["specification"] else {},
                }
                for r in rows
            ]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Get a single project by ID."""
    if not available():
        return None
    try:
        with _connect() as conn:
            row = conn.execute(
                text("SELECT * FROM ml_lab_projects WHERE id = :id"),
                {"id": project_id}
            ).mappings().first()
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "project_name": row["project_name"],
                "description": row["description"],
                "domain": row["domain"],
                "problem_type": row["problem_type"],
                "data_type": row["data_type"],
                "objective": row["objective"],
                "target_variable": row["target_variable"],
                "business_objective": row["business_objective"],
                "constraints": json.loads(row["constraints"]) if row["constraints"] else [],
                "dataset_path": row["dataset_path"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "specification": json.loads(row["specification"]) if row["specification"] else {},
            }
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def delete_project(project_id: str) -> bool:
    """Delete a project and all related data."""
    if not available():
        return False
    try:
        with _connect() as conn:
            conn.execute(
                text("DELETE FROM ml_lab_projects WHERE id = :id"),
                {"id": project_id}
            )
            conn.commit()
            return True
    except (SQLAlchemyError, DatabaseUnavailable):
        return False


# ---------------------------------------------------------------------------
# Experiment Operations
# ---------------------------------------------------------------------------
def save_experiment(experiment: Dict[str, Any]) -> bool:
    """Save or update an experiment in the database."""
    if not available():
        return False
    try:
        with _connect() as conn:
            conn.execute(
                text(
                    """INSERT INTO ml_lab_experiments
                       (id, project_id, name, description, models, hyperparameters,
                        validation_strategy, n_splits, test_size, status,
                        started_at, completed_at, error_message, results, metrics, created_at)
                       VALUES (:id, :project_id, :name, :description, :models, :hyperparameters,
                               :validation_strategy, :n_splits, :test_size, :status,
                               :started_at, :completed_at, :error_message, :results, :metrics, :created_at)
                       ON CONFLICT (id) DO UPDATE SET
                         name = EXCLUDED.name,
                         description = EXCLUDED.description,
                         models = EXCLUDED.models,
                         hyperparameters = EXCLUDED.hyperparameters,
                         validation_strategy = EXCLUDED.validation_strategy,
                         n_splits = EXCLUDED.n_splits,
                         test_size = EXCLUDED.test_size,
                         status = EXCLUDED.status,
                         started_at = EXCLUDED.started_at,
                         completed_at = EXCLUDED.completed_at,
                         error_message = EXCLUDED.error_message,
                         results = EXCLUDED.results,
                         metrics = EXCLUDED.metrics"""
                ),
                {
                    "id": experiment["id"],
                    "project_id": experiment["project_id"],
                    "name": experiment["name"],
                    "description": experiment.get("description"),
                    "models": json.dumps(experiment.get("models", [])),
                    "hyperparameters": json.dumps(experiment.get("hyperparameters", {})),
                    "validation_strategy": experiment.get("validation_strategy", "k_fold"),
                    "n_splits": experiment.get("n_splits", 5),
                    "test_size": experiment.get("test_size", 0.2),
                    "status": experiment.get("status", "pending"),
                    "started_at": experiment.get("started_at"),
                    "completed_at": experiment.get("completed_at"),
                    "error_message": experiment.get("error_message"),
                    "results": json.dumps(experiment.get("results", {})),
                    "metrics": json.dumps(experiment.get("metrics", {})),
                    "created_at": experiment["created_at"],
                },
            )
            conn.commit()
            return True
    except (SQLAlchemyError, DatabaseUnavailable):
        return False


def list_experiments(project_id: str, status: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """List experiments for a project, optionally filtered by status."""
    if not available():
        return None
    try:
        with _connect() as conn:
            if status:
                rows = conn.execute(
                    text("""SELECT * FROM ml_lab_experiments 
                           WHERE project_id = :project_id AND status = :status 
                           ORDER BY created_at DESC"""),
                    {"project_id": project_id, "status": status}
                ).mappings().all()
            else:
                rows = conn.execute(
                    text("""SELECT * FROM ml_lab_experiments 
                           WHERE project_id = :project_id 
                           ORDER BY created_at DESC"""),
                    {"project_id": project_id}
                ).mappings().all()
            
            return [
                {
                    "id": r["id"],
                    "project_id": r["project_id"],
                    "name": r["name"],
                    "description": r["description"],
                    "models": json.loads(r["models"]) if r["models"] else [],
                    "hyperparameters": json.loads(r["hyperparameters"]) if r["hyperparameters"] else {},
                    "validation_strategy": r["validation_strategy"],
                    "n_splits": r["n_splits"],
                    "test_size": r["test_size"],
                    "status": r["status"],
                    "started_at": r["started_at"],
                    "completed_at": r["completed_at"],
                    "error_message": r["error_message"],
                    "results": json.loads(r["results"]) if r["results"] else {},
                    "metrics": json.loads(r["metrics"]) if r["metrics"] else {},
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


# ---------------------------------------------------------------------------
# Model Operations
# ---------------------------------------------------------------------------
def save_model(model: Dict[str, Any]) -> bool:
    """Save or update a model in the database."""
    if not available():
        return False
    try:
        with _connect() as conn:
            conn.execute(
                text(
                    """INSERT INTO ml_lab_models
                       (id, project_id, experiment_id, name, type, category, version,
                        architecture, framework, parameters, training_config,
                        metrics_global, metrics_cv, model_path, model_size_bytes,
                        is_active, is_production, status, trained_at, registered_at,
                        description, tags)
                       VALUES (:id, :project_id, :experiment_id, :name, :type, :category,
                               :version, :architecture, :framework, :parameters, :training_config,
                               :metrics_global, :metrics_cv, :model_path, :model_size_bytes,
                               :is_active, :is_production, :status, :trained_at, :registered_at,
                               :description, :tags)
                       ON CONFLICT (id) DO UPDATE SET
                         name = EXCLUDED.name,
                         type = EXCLUDED.type,
                         category = EXCLUDED.category,
                         version = EXCLUDED.version,
                         architecture = EXCLUDED.architecture,
                         framework = EXCLUDED.framework,
                         parameters = EXCLUDED.parameters,
                         training_config = EXCLUDED.training_config,
                         metrics_global = EXCLUDED.metrics_global,
                         metrics_cv = EXCLUDED.metrics_cv,
                         model_path = EXCLUDED.model_path,
                         model_size_bytes = EXCLUDED.model_size_bytes,
                         is_active = EXCLUDED.is_active,
                         is_production = EXCLUDED.is_production,
                         status = EXCLUDED.status,
                         trained_at = EXCLUDED.trained_at,
                         description = EXCLUDED.description,
                         tags = EXCLUDED.tags"""
                ),
                {
                    "id": model["id"],
                    "project_id": model["project_id"],
                    "experiment_id": model.get("experiment_id"),
                    "name": model["name"],
                    "type": model["type"],
                    "category": model["category"],
                    "version": model["version"],
                    "architecture": model["architecture"],
                    "framework": model.get("framework"),
                    "parameters": json.dumps(model.get("parameters", {})),
                    "training_config": json.dumps(model.get("training_config", {})),
                    "metrics_global": json.dumps(model.get("metrics_global", {})),
                    "metrics_cv": json.dumps(model.get("metrics_cv", {})),
                    "model_path": model.get("model_path"),
                    "model_size_bytes": model.get("model_size_bytes"),
                    "is_active": model.get("is_active", False),
                    "is_production": model.get("is_production", False),
                    "status": model.get("status", "training"),
                    "trained_at": model.get("trained_at"),
                    "registered_at": model["registered_at"],
                    "description": model.get("description"),
                    "tags": json.dumps(model.get("tags", [])),
                },
            )
            conn.commit()
            return True
    except (SQLAlchemyError, DatabaseUnavailable):
        return False


def list_models(project_id: str, is_active: Optional[bool] = None) -> Optional[List[Dict[str, Any]]]:
    """List models for a project, optionally filtered by active status."""
    if not available():
        return None
    try:
        with _connect() as conn:
            if is_active is not None:
                rows = conn.execute(
                    text("""SELECT * FROM ml_lab_models 
                           WHERE project_id = :project_id AND is_active = :is_active 
                           ORDER BY registered_at DESC"""),
                    {"project_id": project_id, "is_active": is_active}
                ).mappings().all()
            else:
                rows = conn.execute(
                    text("""SELECT * FROM ml_lab_models 
                           WHERE project_id = :project_id 
                           ORDER BY registered_at DESC"""),
                    {"project_id": project_id}
                ).mappings().all()
            
            return [
                {
                    "id": r["id"],
                    "project_id": r["project_id"],
                    "experiment_id": r["experiment_id"],
                    "name": r["name"],
                    "type": r["type"],
                    "category": r["category"],
                    "version": r["version"],
                    "architecture": r["architecture"],
                    "framework": r["framework"],
                    "parameters": json.loads(r["parameters"]) if r["parameters"] else {},
                    "training_config": json.loads(r["training_config"]) if r["training_config"] else {},
                    "metrics_global": json.loads(r["metrics_global"]) if r["metrics_global"] else {},
                    "metrics_cv": json.loads(r["metrics_cv"]) if r["metrics_cv"] else {},
                    "model_path": r["model_path"],
                    "model_size_bytes": r["model_size_bytes"],
                    "is_active": r["is_active"],
                    "is_production": r["is_production"],
                    "status": r["status"],
                    "trained_at": r["trained_at"],
                    "registered_at": r["registered_at"],
                    "description": r["description"],
                    "tags": json.loads(r["tags"]) if r["tags"] else [],
                }
                for r in rows
            ]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def set_production_model(model_id: str) -> bool:
    """Set a model as the production model for its project."""
    if not available():
        return False
    try:
        with _connect() as conn:
            # First, get the model to find its project_id
            model = conn.execute(
                text("SELECT project_id FROM ml_lab_models WHERE id = :id"),
                {"id": model_id}
            ).fetchone()
            
            if not model:
                return False
            
            project_id = model[0]
            
            # Set all models in project to non-production
            conn.execute(
                text("UPDATE ml_lab_models SET is_production = FALSE WHERE project_id = :project_id"),
                {"project_id": project_id}
            )
            
            # Set selected model to production
            conn.execute(
                text("UPDATE ml_lab_models SET is_production = TRUE WHERE id = :id"),
                {"id": model_id}
            )
            
            conn.commit()
            return True
    except (SQLAlchemyError, DatabaseUnavailable):
        return False


# ---------------------------------------------------------------------------
# Backup/Restore Operations
# ---------------------------------------------------------------------------
def export_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Export a complete project with all related data."""
    if not available():
        return None
    try:
        with _connect() as conn:
            # Get project
            project = get_project(project_id)
            if not project:
                return None
            
            # Get experiments
            experiments = list_experiments(project_id)
            
            # Get models
            models = list_models(project_id)
            
            # Get artifacts
            artifacts = conn.execute(
                text("SELECT * FROM ml_lab_artifacts WHERE project_id = :project_id"),
                {"project_id": project_id}
            ).mappings().all()
            
            return {
                "project": project,
                "experiments": experiments or [],
                "models": models or [],
                "artifacts": [dict(a) for a in artifacts] if artifacts else [],
                "exported_at": now_utc(),
            }
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def import_project(export_data: Dict[str, Any]) -> bool:
    """Import a project from export data."""
    if not available():
        return False
    try:
        with _connect() as conn:
            # Import project
            project = export_data["project"]
            save_project(project)
            
            # Import experiments
            for exp in export_data.get("experiments", []):
                save_experiment(exp)
            
            # Import models
            for model in export_data.get("models", []):
                save_model(model)
            
            conn.commit()
            return True
    except (SQLAlchemyError, DatabaseUnavailable):
        return False


# ---------------------------------------------------------------------------
# Query Functions for UI
# ---------------------------------------------------------------------------
def get_project_statistics(project_id: str) -> Optional[Dict[str, Any]]:
    """Get statistics for a project for dashboard display."""
    if not available():
        return None
    try:
        with _connect() as conn:
            # Count experiments
            exp_count = conn.execute(
                text("SELECT COUNT(*) FROM ml_lab_experiments WHERE project_id = :project_id"),
                {"project_id": project_id}
            ).scalar() or 0
            
            # Count models
            model_count = conn.execute(
                text("SELECT COUNT(*) FROM ml_lab_models WHERE project_id = :project_id"),
                {"project_id": project_id}
            ).scalar() or 0
            
            # Count active models
            active_count = conn.execute(
                text("SELECT COUNT(*) FROM ml_lab_models WHERE project_id = :project_id AND is_active = TRUE"),
                {"project_id": project_id}
            ).scalar() or 0
            
            # Count production models
            production_count = conn.execute(
                text("SELECT COUNT(*) FROM ml_lab_models WHERE project_id = :project_id AND is_production = TRUE"),
                {"project_id": project_id}
            ).scalar() or 0
            
            # Get latest experiment
            latest_exp = conn.execute(
                text("SELECT created_at FROM ml_lab_experiments WHERE project_id = :project_id ORDER BY created_at DESC LIMIT 1"),
                {"project_id": project_id}
            ).scalar()
            
            return {
                "experiment_count": exp_count,
                "model_count": model_count,
                "active_model_count": active_count,
                "production_model_count": production_count,
                "latest_experiment": latest_exp,
            }
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def get_recent_experiments(limit: int = 10) -> Optional[List[Dict[str, Any]]]:
    """Get recent experiments across all projects."""
    if not available():
        return None
    try:
        with _connect() as conn:
            rows = conn.execute(
                text("""SELECT e.*, p.project_name 
                       FROM ml_lab_experiments e
                       JOIN ml_lab_projects p ON e.project_id = p.id
                       ORDER BY e.created_at DESC
                       LIMIT :limit"""),
                {"limit": limit}
            ).mappings().all()
            
            return [
                {
                    "id": r["id"],
                    "project_id": r["project_id"],
                    "project_name": r["project_name"],
                    "name": r["name"],
                    "status": r["status"],
                    "created_at": r["created_at"],
                    "completed_at": r["completed_at"],
                }
                for r in rows
            ]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def get_best_models_by_project(limit: int = 20) -> Optional[List[Dict[str, Any]]]:
    """Get best performing models by project."""
    if not available():
        return None
    try:
        with _connect() as conn:
            rows = conn.execute(
                text("""SELECT m.*, p.project_name 
                       FROM ml_lab_models m
                       JOIN ml_lab_projects p ON m.project_id = p.id
                       WHERE m.is_active = TRUE
                       ORDER BY m.registered_at DESC
                       LIMIT :limit"""),
                {"limit": limit}
            ).mappings().all()
            
            return [
                {
                    "id": r["id"],
                    "project_id": r["project_id"],
                    "project_name": r["project_name"],
                    "name": r["name"],
                    "type": r["type"],
                    "version": r["version"],
                    "is_production": r["is_production"],
                    "status": r["status"],
                    "registered_at": r["registered_at"],
                    "metrics_global": json.loads(r["metrics_global"]) if r["metrics_global"] else {},
                }
                for r in rows
            ]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None


def search_projects(query: str, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
    """Search projects by name or description."""
    if not available():
        return None
    try:
        with _connect() as conn:
            rows = conn.execute(
                text("""SELECT * FROM ml_lab_projects 
                       WHERE project_name ILIKE :query OR description ILIKE :query
                       ORDER BY created_at DESC
                       LIMIT :limit"""),
                {"query": f"%{query}%", "limit": limit}
            ).mappings().all()
            
            return [
                {
                    "id": r["id"],
                    "project_name": r["project_name"],
                    "description": r["description"],
                    "domain": r["domain"],
                    "problem_type": r["problem_type"],
                    "status": r["status"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
    except (SQLAlchemyError, DatabaseUnavailable):
        return None
