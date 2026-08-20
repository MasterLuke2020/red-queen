# RC7 phase-name hotfix

This patch corrects the release metadata display from the stale
`Release Candidate 6` label to `Release Candidate 7`.

Replace:

```text
/config/custom_components/wnhf/release_candidate.py
```

with the packaged file at:

```text
custom_components/wnhf/release_candidate.py
```

Restart Home Assistant afterward and run `wnhf.release_info` again. The response
must contain both `candidate: rc7` and `phase_name: Release Candidate 7`.
