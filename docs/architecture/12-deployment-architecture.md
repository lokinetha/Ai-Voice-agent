# 12. Deployment Architecture — v2

> **Enterprise Architecture Review**
>
> **v1 Weaknesses**: No mention of how cross-cutting concerns (observability, security)
> are deployed. No health check architecture. No graceful shutdown for voice sessions.
> CI/CD doesn't enforce architecture (no lint for dependency rules).
>
> **v2 Improvements**: Added architecture enforcement in CI. Graceful voice session
> draining. Health check hierarchy. Structured deployment per bounded context.
> Otherwise v1 infrastructure was well-designed.

---

## Deployment per Bounded Context

| Deployment Unit | Bounded Contexts | Scaling Strategy |
|----------------|-----------------|-----------------|
| **API Pod** | All contexts (controllers) | HPA on CPU (3-10 replicas) |
| **Worker Pod** | Processing, Playbook, Prompt, Evaluation, Knowledge | HPA on queue depth (5-20) |
| **Voice Pod** | Voice, Conversation (real-time path) | HPA on active sessions (3-15) |
| **Frontend Pod** | N/A (Next.js) | HPA on CPU (2-5) |

In future: each bounded context can be extracted into its own microservice when scale demands it. The event-driven architecture makes this a deployment change, not a code change.

---

## Architecture Enforcement in CI

```yaml
# .github/workflows/ci.yml (additions)
- name: Architecture tests
  run: |
    # Enforce dependency rules: Domain MUST NOT import Infrastructure
    python -m pytest tests/architecture/test_dependency_rules.py

    # Enforce no framework imports in domain layer
    python -m pytest tests/architecture/test_domain_purity.py

    # Enforce aggregate invariants have tests
    python -m pytest tests/architecture/test_invariant_coverage.py
```

```python
# tests/architecture/test_dependency_rules.py
import ast, os

FORBIDDEN_IMPORTS = {
    "domain": [
        "sqlalchemy", "fastapi", "redis", "qdrant_client",
        "boto3", "celery", "pika", "httpx",
    ],
    "application": [
        "sqlalchemy", "fastapi", "redis",
    ],
}

def test_domain_has_no_infrastructure_imports():
    """Domain layer must never import framework/infrastructure packages."""
    for context_dir in get_bounded_context_dirs():
        domain_dir = os.path.join(context_dir, "domain")
        for py_file in find_python_files(domain_dir):
            imports = extract_imports(py_file)
            for pkg in FORBIDDEN_IMPORTS["domain"]:
                assert pkg not in imports, (
                    f"{py_file} imports {pkg} — FORBIDDEN in domain layer"
                )
```

---

## Graceful Voice Session Draining

```yaml
# k8s deployment for voice pods
spec:
  terminationGracePeriodSeconds: 120  # Allow active calls to finish
  containers:
    - name: voice
      lifecycle:
        preStop:
          exec:
            command:
              - /bin/sh
              - -c
              - |
                # 1. Stop accepting new sessions
                curl -X POST localhost:8080/internal/drain
                # 2. Wait for active sessions to complete (max 90s)
                sleep 90
```

```python
# voice/infrastructure/gateway/websocket_gateway.py
class WebSocketGateway:
    async def drain(self):
        """Called during graceful shutdown."""
        self._accepting_new = False
        # Wait for all active sessions to end or timeout
        while self._active_sessions > 0 and self._drain_timeout > 0:
            await asyncio.sleep(1)
            self._drain_timeout -= 1
        # Force-close remaining sessions with goodbye message
        for session in self._sessions.values():
            await session.end_session(reason="server_shutdown")
```

---

## Health Checks

```python
# presentation/api/v1/health_controller.py
@router.get("/health/live")
async def liveness():
    """K8s liveness: is the process alive?"""
    return {"status": "ok"}

@router.get("/health/ready")
async def readiness(
    db: AsyncSession = Depends(get_db),
    redis: CachePort = Depends(get_cache),
):
    """K8s readiness: can the pod serve traffic?"""
    checks = {
        "database": await check_db(db),
        "redis": await check_redis(redis),
    }
    all_healthy = all(checks.values())
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={"status": "ready" if all_healthy else "not_ready", "checks": checks}
    )

@router.get("/health/startup")
async def startup():
    """K8s startup: has the app finished initializing?"""
    return {"status": "started", "version": settings.app_version}
```

---

## Infrastructure, Terraform, Observability, Environment Matrix

*(v1 infrastructure, Terraform modules, observability stack, CI/CD pipeline, alert definitions, and environment matrix were well-designed. No changes needed — retained from v1.)*
