# Screenshot Capture Checklist

These are genuine browser captures from the local application. They are demonstration evidence, not evidence of production security:

- [x] [Main dashboard / overview](dashboard-overview.png)
- [x] [Prompt injection scan result](prompt-injection-result.png)
- [x] [Viewer action denied by policy](viewer-action-blocked.png)
- [x] [Sensitive-data scan using a synthetic email](sensitive-data-scan.png)
- [x] [Security event history](security-events.png)
- [x] [Historical model performance](model-performance.png)
- [ ] Simulated-agent execution screenshot (not captured; the simulator is invoked from a terminal, not the dashboard).

The overview/event counters include synthetic/test entries present in the local SQLite database; they are not production traffic. The model page explicitly identifies its metrics as historical held-out experiment results. Only synthetic/demo data was submitted in the scanner and authorization captures.

If recapturing, use synthetic `example.test` addresses and dummy tokens only. Avoid showing real usernames, local file paths, browser profiles, secrets, or personal data. Save originals in this directory and update this list.
