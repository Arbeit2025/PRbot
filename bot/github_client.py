"""Minimal GitHub client with submission guards.

Submitting a PR to someone else's repository is the one irreversible,
outward-facing step in PRbot, so it is refused by default. All of these
must hold before submit_pull_request() will even attempt a request:

- environment SUBMIT_ENABLED is exactly "true"
- the caller passes confirm="SUBMIT" (typed by a human, not a default)
- a token is present in environment GITHUB_TOKEN (never stored in files)

Even then, this starter client only validates the guards and raises
NotImplementedError: the actual submission flow (fork, push branch,
open PR) is done manually by the user following docs/workflow.md until
a later, separately reviewed version implements it.
"""
from __future__ import annotations

import os


class SubmissionRefused(RuntimeError):
    pass


def check_submission_guards(confirm: str | None) -> None:
    if os.environ.get("SUBMIT_ENABLED") != "true":
        raise SubmissionRefused("SUBMIT_ENABLED is not 'true'; submission is disabled by default")
    if confirm != "SUBMIT":
        raise SubmissionRefused("human confirmation phrase 'SUBMIT' was not given")
    if not os.environ.get("GITHUB_TOKEN"):
        raise SubmissionRefused("GITHUB_TOKEN is not set")


def submit_pull_request(*, repo: str, branch: str, title: str, body: str, confirm: str | None = None) -> None:
    check_submission_guards(confirm)
    raise NotImplementedError(
        "Automated submission is not implemented in the starter kit. "
        "Follow docs/workflow.md and open the PR manually after reviewing the diff."
    )
