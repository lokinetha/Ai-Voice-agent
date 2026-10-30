# 13. Future Roadmap — v2

> **Enterprise Architecture Review**
>
> **v1 Weaknesses**: Roadmap focused only on features. No architectural milestones.
> No mention of when to extract microservices, when to add CQRS read models,
> or when architecture debt should be addressed.
>
> **v2 Improvements**: Added architectural milestones in each phase. Added "architecture
> health" checkpoints. Marked microservice extraction triggers.

---

## Roadmap with Architectural Milestones

### Phase 1: Foundation (Months 1-3)

| Deliverable | Type |
|-------------|------|
| Shared Kernel (base classes, value objects, ports) | **Architecture** |
| DI Container + decorator chain | **Architecture** |
| PostgreSQL schema (normalized) + Alembic migrations | Data |
| Identity + Organization contexts (auth, multi-tenancy) | Feature |
| Ingestion context (upload, storage) | Feature |
| Processing context (STT via STTPort, basic analysis) | Feature |
| Architecture enforcement tests in CI | **Architecture** |
| Dashboard v1 (auth, upload, transcript view) | Feature |
| Docker Compose local development | Infra |

**Architecture Checkpoint**: All domain entities use typed IDs. Zero framework imports in domain. Repository pattern enforced.

---

### Phase 2: AI Core (Months 4-6)

| Deliverable | Type |
|-------------|------|
| Knowledge context (ChunkerFactory, EmbeddingPort, VectorStorePort) | Feature |
| Playbook context (PatternMiningService, PlaybookBuilder) | Feature |
| Prompt context (PromptCompiler, PromptBuilder) | Feature |
| Event-driven pipeline: Ingestion → Processing → Playbook → Prompt | **Architecture** |
| Transactional outbox pattern | **Architecture** |
| Anti-Corruption Layers between contexts | **Architecture** |
| Contract tests for all port implementations | **Architecture** |

**Architecture Checkpoint**: All bounded contexts communicate via domain events. ACLs prevent model leakage. Builder pattern for complex aggregates validated.

---

### Phase 3: Voice (Months 7-9)

| Deliverable | Type |
|-------------|------|
| Voice context (VoiceSession aggregate, state machine) | Feature |
| VoicePipelineOrchestrator (application service) | Feature |
| InterruptionDetector (domain service) | Feature |
| STTPort/TTSPort adapters (Deepgram, ElevenLabs) | Feature |
| TelephonyPort adapter (Twilio) | Feature |
| WebSocket + WebRTC gateways | Feature |
| Graceful session draining | **Architecture** |
| Latency monitoring + alerting | Infra |

**Architecture Checkpoint**: Voice pipeline uses only port interfaces. Session state is typed (not raw dict). Zero direct framework calls in voice domain.

---

### Phase 4: Intelligence (Months 10-12)

| Deliverable | Type |
|-------------|------|
| Evaluation context (EvaluatorFactory, ComplianceChecker) | Feature |
| Analytics context (CQRS read models, materialized views) | Feature + **Architecture** |
| Prompt optimization feedback loop | Feature |
| A/B testing framework | Feature |
| Multi-agent routing (Strategy pattern) | Feature |

**Architecture Checkpoint**: CQRS fully operational — command and query paths separated. Read models refreshed by event handlers. Evaluation scores flow into prompt improvement via events.

---

### Phase 5: Scale & Enterprise (Months 13-18)

| Deliverable | Type |
|-------------|------|
| Kubernetes (EKS) deployment | Infra |
| **Microservice extraction readiness audit** | **Architecture** |
| Enterprise SSO (SAML/OIDC) | Feature |
| SOC 2 Type II certification | Compliance |
| Client SDKs (Python, JavaScript) | Feature |
| Agent templates marketplace | Feature |

**Microservice Extraction Triggers**:

| Signal | Action |
|--------|--------|
| Processing workers need independent scaling | Extract Processing context → separate service |
| Voice pods need independent deployment cadence | Extract Voice context → separate service |
| Analytics queries impact API latency | Extract Analytics → separate read-only service |
| Team grows to 4+ squads | One context per squad boundary |

---

## Feature Roadmap (18+ Months)

*(Unchanged from v1 — multimodal agents, real-time translation, emotion-adaptive AI, voice cloning, fine-tuned models, vertical solutions. Competitive positioning retained.)*
