## ADDED Requirements

### Requirement: AI readiness warning on startup
The interface SHALL check the configured AI API during page initialization and warn the user if it is not currently reachable.

#### Scenario: AI API is available
- **WHEN** the interface initializes and the AI readiness check succeeds
- **THEN** the log panel SHALL show a concise success or informational message indicating that the AI backend is reachable.

#### Scenario: AI API is unavailable
- **WHEN** the interface initializes and the AI readiness check fails
- **THEN** the log panel SHALL show a warning that the AI backend is unavailable and that synthesis may fail until it is started or reconfigured.

#### Scenario: AI readiness check fails but Vault loads
- **WHEN** the AI readiness check fails but Vault folder discovery succeeds
- **THEN** the interface SHALL still load available Vault folders and remain usable for retry after the backend becomes available.
