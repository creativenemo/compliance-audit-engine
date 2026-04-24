from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepResult:
    status: str  # complete | failed | skipped
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    error: str | None = None


class BasePipelineStep(ABC):
    step_number: int
    step_name: str

    @abstractmethod
    async def run(self, intake: dict[str, Any], job_id: str) -> StepResult:
        ...

    def _skipped(self, sprint: int) -> StepResult:
        return StepResult(
            status="skipped",
            data={},
            message=f"Not yet implemented — Sprint {sprint}",
        )
