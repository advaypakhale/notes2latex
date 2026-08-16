"""Resolved configuration for a single pipeline run."""

from __future__ import annotations

from notes2latex.core.config import RunOptions, Settings
from notes2latex.core.outputs import JobOutputs
from notes2latex.agent.prompts import DEFAULT_PREAMBLE


class RunConfig(RunOptions):
    api_key: str | None = None
    preamble: str = DEFAULT_PREAMBLE

    @property
    def outputs(self) -> JobOutputs:
        return JobOutputs(self.output_dir)

    @classmethod
    def from_settings(cls, settings: Settings, **overrides: object) -> RunConfig:
        """Build a config from app settings, applying overrides on top.

        The include= filter drops settings a run does not take, such as data_dir.
        """
        return cls(**(settings.model_dump(include=set(cls.model_fields)) | overrides))
