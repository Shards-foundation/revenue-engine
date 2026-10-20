"""Regression tests for GitHub Actions workflow files.

The default-branch CI workflow failed in zero seconds with no jobs because
.github/workflows/ci.yml was not valid workflow YAML. ``steps`` was a mapping
instead of a sequence, and ``with`` was indented as a sibling of ``runs-on``,
so the file did not parse and GitHub never applied ``name: CI``.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"


class WorkflowValidationError(Exception):
    """A workflow file GitHub Actions would reject before starting jobs."""


def validate_workflow(text, source="<workflow>"):
    """Parse workflow YAML and require a runnable ``jobs.*.steps`` list."""
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise WorkflowValidationError(
            f"{source} is not valid YAML: {exc}"
        ) from exc

    if not isinstance(document, dict):
        raise WorkflowValidationError(f"{source} must be a mapping")

    jobs = document.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        raise WorkflowValidationError(f"{source} must define jobs")

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            raise WorkflowValidationError(
                f"{source} job {job_name} must be a mapping"
            )
        steps = job.get("steps")
        if not isinstance(steps, list) or not steps:
            raise WorkflowValidationError(
                f"{source} job {job_name} steps must be a non-empty list"
            )
        saw_checkout = False
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                raise WorkflowValidationError(
                    f"{source} job {job_name} step {index} must be a mapping"
                )
            if "uses" not in step and "run" not in step:
                raise WorkflowValidationError(
                    f"{source} job {job_name} step {index} needs uses or run"
                )
            uses = step.get("uses") or ""
            if uses.startswith("actions/checkout@"):
                saw_checkout = True
            if "markdownlint-cli2-action" in uses and not saw_checkout:
                raise WorkflowValidationError(
                    f"{source} job {job_name} must checkout before markdownlint"
                )
    return document


HISTORICAL_CI = """\
name: CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      uses: DavidAnson/markdownlint-cli2-action@v16
     with:
       globs: "**/*.md"
"""

STEPS_NOT_A_LIST = """\
name: CI
on: push
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      uses: DavidAnson/markdownlint-cli2-action@v16
      with:
        globs: "**/*.md"
"""


def test_historical_ci_workflow_is_rejected():
    """The file that failed on main is rejected by the same validator CI uses."""
    try:
        validate_workflow(HISTORICAL_CI, source="historical ci.yml")
    except WorkflowValidationError:
        return
    raise AssertionError("historical ci.yml should be rejected")


def test_steps_mapping_is_rejected():
    """A parsed ``steps`` mapping is still invalid GitHub Actions schema."""
    try:
        validate_workflow(STEPS_NOT_A_LIST, source="steps-as-mapping")
    except WorkflowValidationError as exc:
        assert "steps must be a non-empty list" in str(exc)
        return
    raise AssertionError("steps mapping should be rejected")


def test_checked_in_workflows_are_valid():
    files = sorted(WORKFLOW_DIR.glob("*.yml"))
    assert files, "expected workflow files under .github/workflows"
    for path in files:
        validate_workflow(path.read_text(encoding="utf-8"), source=path.name)


def test_ci_yml_lints_markdown_after_checkout():
    document = validate_workflow(
        (WORKFLOW_DIR / "ci.yml").read_text(encoding="utf-8"),
        source="ci.yml",
    )
    uses = [
        step["uses"]
        for job in document["jobs"].values()
        for step in job["steps"]
        if "uses" in step
    ]
    assert any(item.startswith("actions/checkout@") for item in uses)
    assert any("markdownlint-cli2-action" in item for item in uses)
