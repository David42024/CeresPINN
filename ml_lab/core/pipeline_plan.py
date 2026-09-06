"""Pipeline Plan - Dynamic pipeline specification.

This module defines the PipelinePlan dataclass which represents the
execution plan for an ML project. The PipelineEngine generates this plan
based on the ProjectSpecification and DatasetProfile.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class PipelineStep(Enum):
    """Available pipeline steps."""
    DATASET_ANALYSIS = "dataset_analysis"
    EDA = "eda"
    PREPROCESSING = "preprocessing"
    FEATURE_ENGINEERING = "feature_engineering"
    MODEL_TRAINING = "model_training"
    VALIDATION = "validation"
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"
    MODEL_EVALUATION = "model_evaluation"
    STATISTICAL_TESTS = "statistical_tests"
    MODEL_COMPARISON = "model_comparison"
    BEST_MODEL_SELECTION = "best_model_selection"
    EXPLAINABILITY = "explainability"
    MODEL_REGISTRY = "model_registry"
    REPORT_GENERATION = "report_generation"
    INFERENCE = "inference"


class StepStatus(Enum):
    """Status of a pipeline step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class StepDependency:
    """Dependency between pipeline steps."""
    step: PipelineStep
    depends_on: List[PipelineStep]
    invalidation_rule: Optional[str] = None  # e.g., "dataset_changed"


@dataclass
class StepExecution:
    """Execution information for a pipeline step."""
    step: PipelineStep
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    elapsed_seconds: Optional[float] = None
    error_message: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    artifacts: List[Path] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelinePlan:
    """Execution plan for an ML project.
    
    The PipelineEngine generates this plan based on the ProjectSpecification
    and DatasetProfile. The plan defines which steps to execute, in what order,
    and what dependencies exist between steps.
    """
    project_id: str
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Pipeline Steps
    steps: List[PipelineStep] = field(default_factory=list)
    step_executions: Dict[PipelineStep, StepExecution] = field(default_factory=dict)
    dependencies: List[StepDependency] = field(default_factory=list)
    
    # Pipeline Configuration
    enable_eda: bool = True
    enable_preprocessing: bool = True
    enable_feature_engineering: bool = False
    enable_validation: bool = True
    enable_hyperparameter_tuning: bool = False
    enable_statistical_tests: bool = True
    enable_explainability: bool = True
    enable_model_comparison: bool = True
    enable_report_generation: bool = True
    
    # Execution Options
    parallel_execution: bool = False
    max_parallel_steps: int = 2
    cache_intermediate_results: bool = True
    
    # Status
    status: str = "planned"  # "planned", "running", "completed", "failed"
    current_step: Optional[PipelineStep] = None
    progress_percentage: float = 0.0
    
    def add_step(self, step: PipelineStep) -> None:
        """Add a step to the pipeline."""
        if step not in self.steps:
            self.steps.append(step)
            self.step_executions[step] = StepExecution(step=step)
    
    def add_dependency(self, step: PipelineStep, depends_on: List[PipelineStep]) -> None:
        """Add a dependency between steps."""
        dependency = StepDependency(step=step, depends_on=depends_on)
        self.dependencies.append(dependency)
    
    def get_step_status(self, step: PipelineStep) -> StepStatus:
        """Get the status of a step."""
        if step in self.step_executions:
            return self.step_executions[step].status
        return StepStatus.NOT_APPLICABLE
    
    def update_step_status(
        self,
        step: PipelineStep,
        status: StepStatus,
        error_message: Optional[str] = None,
        artifacts: Optional[List[Path]] = None,
    ) -> None:
        """Update the status of a step."""
        if step not in self.step_executions:
            self.step_executions[step] = StepExecution(step=step)
        
        execution = self.step_executions[step]
        execution.status = status
        
        if status == StepStatus.RUNNING and execution.started_at is None:
            execution.started_at = datetime.utcnow()
        elif status in (StepStatus.COMPLETED, StepStatus.FAILED):
            execution.completed_at = datetime.utcnow()
            if execution.started_at:
                execution.elapsed_seconds = (
                    execution.completed_at - execution.started_at
                ).total_seconds()
        
        if error_message:
            execution.error_message = error_message
        
        if artifacts:
            execution.artifacts.extend(artifacts)
        
        self._update_progress()
    
    def _update_progress(self) -> None:
        """Update overall progress percentage."""
        if not self.steps:
            self.progress_percentage = 0.0
            return
        
        completed = sum(
            1 for step in self.steps
            if self.get_step_status(step) == StepStatus.COMPLETED
        )
        self.progress_percentage = (completed / len(self.steps)) * 100
    
    def get_next_step(self) -> Optional[PipelineStep]:
        """Get the next step to execute."""
        for step in self.steps:
            status = self.get_step_status(step)
            if status == StepStatus.PENDING:
                # Check if dependencies are satisfied
                deps_satisfied = True
                for dep in self.dependencies:
                    if dep.step == step:
                        for dep_step in dep.depends_on:
                            if self.get_step_status(dep_step) != StepStatus.COMPLETED:
                                deps_satisfied = False
                                break
                if deps_satisfied:
                    return step
        return None
    
    def get_failed_steps(self) -> List[PipelineStep]:
        """Get all failed steps."""
        return [
            step for step in self.steps
            if self.get_step_status(step) == StepStatus.FAILED
        ]
    
    def can_execute_step(self, step: PipelineStep) -> bool:
        """Check if a step can be executed (dependencies satisfied)."""
        for dep in self.dependencies:
            if dep.step == step:
                for dep_step in dep.depends_on:
                    if self.get_step_status(dep_step) != StepStatus.COMPLETED:
                        return False
        return True
    
    def invalidate_step(self, step: PipelineStep) -> None:
        """Invalidate a step and all steps that depend on it."""
        self.update_step_status(step, StepStatus.PENDING)
        
        # Find and invalidate dependent steps
        for dep in self.dependencies:
            if step in dep.depends_on:
                self.invalidate_step(dep.step)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary."""
        from dataclasses import asdict
        data = asdict(self)
        # Convert enums to strings
        data["steps"] = [s.value for s in self.steps]
        for step, execution in self.step_executions.items():
            data["step_executions"][step.value] = {
                **asdict(execution),
                "step": execution.step.value,
                "status": execution.status.value,
            }
        for i, dep in enumerate(self.dependencies):
            data["dependencies"][i] = {
                "step": dep.step.value,
                "depends_on": [d.value for d in dep.depends_on],
                "invalidation_rule": dep.invalidation_rule,
            }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelinePlan":
        """Create plan from dictionary."""
        # Convert enum strings back to enums
        data["steps"] = [PipelineStep(s) for s in data["steps"]]
        
        step_executions = {}
        for step_str, exec_data in data["step_executions"].items():
            step = PipelineStep(step_str)
            exec_data["step"] = step
            exec_data["status"] = StepStatus(exec_data["status"])
            # Convert datetime strings
            if exec_data.get("started_at"):
                exec_data["started_at"] = datetime.fromisoformat(exec_data["started_at"])
            if exec_data.get("completed_at"):
                exec_data["completed_at"] = datetime.fromisoformat(exec_data["completed_at"])
            # Convert Path strings
            if exec_data.get("artifacts"):
                exec_data["artifacts"] = [Path(a) for a in exec_data["artifacts"]]
            step_executions[step] = StepExecution(**exec_data)
        data["step_executions"] = step_executions
        
        dependencies = []
        for dep_data in data["dependencies"]:
            dependencies.append(StepDependency(
                step=PipelineStep(dep_data["step"]),
                depends_on=[PipelineStep(d) for d in dep_data["depends_on"]],
                invalidation_rule=dep_data.get("invalidation_rule"),
            ))
        data["dependencies"] = dependencies
        
        if "generated_at" in data and isinstance(data["generated_at"], str):
            data["generated_at"] = datetime.fromisoformat(data["generated_at"])
        
        return cls(**data)
    
    def save(self, path: Path) -> None:
        """Save plan to JSON file."""
        import json
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load(cls, path: Path) -> "PipelinePlan":
        """Load plan from JSON file."""
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
