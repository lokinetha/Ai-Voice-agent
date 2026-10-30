# 3. Folder Structure — v2

> **Enterprise Architecture Review**
>
> **v1 Weaknesses**: Monolithic `domain/entities/`, `domain/repositories/` — groups by
> technical concern not bounded context. Service files mix domain and infrastructure logic.
> No separation of commands/queries. Cross-cutting concerns scattered. Shared Kernel missing.
>
> **v2 Improvements**: Each bounded context gets its own Clean Architecture structure.
> Domain at center. Shared Kernel extracted. CQRS separation. Cross-cutting via decorators.

---

## Monorepo Root

```
voiceforge-ai/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd-staging.yml
│       └── cd-production.yml
│
├── docs/
│   └── architecture/                   # This folder
│
├── infrastructure/
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── vpc/
│   │   │   ├── eks/
│   │   │   ├── rds/
│   │   │   ├── elasticache/
│   │   │   ├── s3/
│   │   │   ├── mq/
│   │   │   ├── qdrant/
│   │   │   ├── cloudfront/
│   │   │   └── monitoring/
│   │   ├── environments/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   └── main.tf
│   ├── docker/
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.worker
│   │   ├── Dockerfile.voice
│   │   └── Dockerfile.frontend
│   ├── k8s/
│   │   ├── base/
│   │   ├── overlays/
│   │   └── kustomization.yaml
│   └── docker-compose.yml
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   │
│   └── src/
│       │
│       ├── shared/                      # ─── SHARED KERNEL ───
│       │   ├── __init__.py
│       │   ├── kernel/
│       │   │   ├── __init__.py
│       │   │   ├── entity.py            # Base Entity
│       │   │   ├── aggregate_root.py    # Base AggregateRoot
│       │   │   ├── value_object.py      # Base ValueObject
│       │   │   ├── value_objects.py     # All typed IDs + domain VOs
│       │   │   ├── domain_event.py      # Base DomainEvent
│       │   │   ├── domain_service.py    # DomainService marker
│       │   │   ├── repository.py        # Repository[T] interface
│       │   │   ├── unit_of_work.py      # UnitOfWork interface
│       │   │   ├── specification.py     # Specification[T]
│       │   │   ├── result.py            # Result[T], Error
│       │   │   └── cqrs.py             # Command, Query, Handlers
│       │   │
│       │   ├── contracts/               # Hexagonal port interfaces
│       │   │   ├── __init__.py
│       │   │   ├── stt_port.py
│       │   │   ├── tts_port.py
│       │   │   ├── llm_port.py
│       │   │   ├── embedding_port.py
│       │   │   ├── vector_store_port.py
│       │   │   ├── object_storage_port.py
│       │   │   ├── event_bus_port.py
│       │   │   ├── cache_port.py
│       │   │   ├── telephony_port.py
│       │   │   ├── metrics_port.py
│       │   │   ├── authorization_port.py
│       │   │   └── feature_flag_port.py
│       │   │
│       │   └── common/                  # Cross-cutting concern base
│       │       ├── __init__.py
│       │       ├── clock.py             # Abstracted time
│       │       ├── id_generator.py      # UUID generator
│       │       └── exceptions.py        # Domain exceptions
│       │
│       ├── identity/                    # ─── IDENTITY CONTEXT ───
│       │   ├── __init__.py
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   ├── user.py          # User (AggregateRoot)
│       │   │   │   └── api_key.py       # ApiKey (Entity)
│       │   │   ├── value_objects/
│       │   │   │   ├── password_hash.py
│       │   │   │   └── user_role.py
│       │   │   ├── repositories/
│       │   │   │   └── user_repository.py
│       │   │   ├── events/
│       │   │   │   └── user_events.py
│       │   │   ├── services/
│       │   │   │   └── authentication_service.py
│       │   │   └── factories/
│       │   │       └── user_factory.py
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── register_user.py
│       │   │   │   └── change_password.py
│       │   │   ├── queries/
│       │   │   │   └── get_user.py
│       │   │   ├── dtos/
│       │   │   │   └── user_dto.py
│       │   │   └── mappers/
│       │   │       └── user_mapper.py
│       │   └── infrastructure/
│       │       ├── persistence/
│       │       │   ├── models.py        # SQLAlchemy models
│       │       │   └── pg_user_repository.py
│       │       └── services/
│       │           └── jwt_token_service.py
│       │
│       ├── organization/                # ─── ORGANIZATION CONTEXT ───
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   ├── organization.py  # Organization (AggregateRoot)
│       │   │   │   └── workspace.py     # Workspace (Entity)
│       │   │   ├── value_objects/
│       │   │   │   ├── plan.py
│       │   │   │   └── org_settings.py
│       │   │   ├── repositories/
│       │   │   │   └── organization_repository.py
│       │   │   ├── events/
│       │   │   │   └── org_events.py
│       │   │   └── factories/
│       │   │       └── organization_factory.py
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── create_workspace.py
│       │   │   │   └── change_plan.py
│       │   │   └── queries/
│       │   │       ├── get_organization.py
│       │   │       └── get_workspaces.py
│       │   └── infrastructure/
│       │       └── persistence/
│       │           ├── models.py
│       │           └── pg_organization_repository.py
│       │
│       ├── agent/                        # ─── AGENT CONTEXT ───
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   ├── agent.py         # Agent (AggregateRoot)
│       │   │   │   ├── agent_tool.py    # AgentTool (Entity)
│       │   │   │   └── agent_policy.py  # AgentPolicy (Entity)
│       │   │   ├── value_objects/
│       │   │   │   ├── agent_voice_config.py
│       │   │   │   ├── agent_runtime_config.py
│       │   │   │   ├── agent_llm_config.py
│       │   │   │   ├── agent_memory_config.py
│       │   │   │   ├── agent_status.py
│       │   │   │   └── agent_type.py
│       │   │   ├── repositories/
│       │   │   │   └── agent_repository.py
│       │   │   ├── events/
│       │   │   │   └── agent_events.py
│       │   │   ├── specifications/
│       │   │   │   ├── active_agent_spec.py
│       │   │   │   └── publishable_agent_spec.py
│       │   │   └── factories/
│       │   │       └── agent_factory.py
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── create_agent.py
│       │   │   │   ├── publish_agent.py
│       │   │   │   ├── clone_agent.py
│       │   │   │   ├── update_agent_config.py
│       │   │   │   ├── add_agent_tool.py
│       │   │   │   └── add_agent_policy.py
│       │   │   ├── queries/
│       │   │   │   ├── get_agent.py
│       │   │   │   ├── list_agents.py
│       │   │   │   └── get_agent_metrics.py
│       │   │   ├── dtos/
│       │   │   │   └── agent_dto.py
│       │   │   └── mappers/
│       │   │       └── agent_mapper.py
│       │   └── infrastructure/
│       │       └── persistence/
│       │           ├── models.py
│       │           └── pg_agent_repository.py
│       │
│       ├── ingestion/                    # ─── INGESTION CONTEXT ───
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   ├── data_source.py
│       │   │   │   ├── recording.py
│       │   │   │   └── document.py
│       │   │   ├── value_objects/
│       │   │   │   ├── storage_key.py
│       │   │   │   ├── audio_format.py
│       │   │   │   └── data_source_type.py
│       │   │   ├── repositories/
│       │   │   │   └── data_source_repository.py
│       │   │   ├── events/
│       │   │   │   └── ingestion_events.py
│       │   │   └── factories/
│       │   │       └── data_source_factory.py
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── ingest_audio.py
│       │   │   │   ├── ingest_document.py
│       │   │   │   └── ingest_website.py
│       │   │   └── queries/
│       │   │       ├── get_data_source.py
│       │   │       └── list_data_sources.py
│       │   └── infrastructure/
│       │       └── persistence/
│       │
│       ├── processing/                   # ─── PROCESSING CONTEXT ───
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   └── processing_job.py
│       │   │   ├── value_objects/
│       │   │   │   ├── transcript_segment.py
│       │   │   │   ├── sentiment_score.py
│       │   │   │   └── detected_intent.py
│       │   │   ├── repositories/
│       │   │   │   └── processing_job_repository.py
│       │   │   ├── events/
│       │   │   │   └── processing_events.py
│       │   │   └── factories/
│       │   │       └── processing_job_factory.py
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── start_transcription.py
│       │   │   │   └── analyze_call.py
│       │   │   └── queries/
│       │   │       └── get_processing_status.py
│       │   └── infrastructure/
│       │       ├── acl/                  # Anti-Corruption Layer
│       │       │   └── ingestion_acl.py
│       │       └── persistence/
│       │
│       ├── knowledge/                    # ─── KNOWLEDGE CONTEXT ───
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   ├── knowledge_base.py
│       │   │   │   └── kb_document.py
│       │   │   ├── value_objects/
│       │   │   │   ├── embedding_config.py
│       │   │   │   ├── chunking_config.py
│       │   │   │   └── chunking_strategy.py
│       │   │   ├── repositories/
│       │   │   │   └── knowledge_base_repository.py
│       │   │   ├── events/
│       │   │   │   └── knowledge_events.py
│       │   │   ├── services/
│       │   │   │   └── retrieval_service.py  # Domain Service
│       │   │   ├── specifications/
│       │   │   │   └── searchable_kb_spec.py
│       │   │   └── factories/
│       │   │       ├── knowledge_base_factory.py
│       │   │       └── chunker_factory.py    # Strategy factory
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── create_knowledge_base.py
│       │   │   │   ├── add_document.py
│       │   │   │   └── reindex_knowledge.py
│       │   │   └── queries/
│       │   │       ├── search_knowledge.py
│       │   │       └── get_knowledge_base.py
│       │   └── infrastructure/
│       │       ├── persistence/
│       │       ├── chunkers/                # Strategy implementations
│       │       │   ├── recursive_chunker.py
│       │       │   ├── semantic_chunker.py
│       │       │   ├── qa_pair_chunker.py
│       │       │   └── table_chunker.py
│       │       └── parsers/
│       │           ├── pdf_parser.py
│       │           ├── docx_parser.py
│       │           └── html_parser.py
│       │
│       ├── playbook/                     # ─── PLAYBOOK CONTEXT ───
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   ├── playbook.py
│       │   │   │   ├── conversation_stage.py
│       │   │   │   └── objection_strategy.py
│       │   │   ├── value_objects/
│       │   │   │   ├── role_definition.py
│       │   │   │   ├── persona_definition.py
│       │   │   │   ├── communication_style.py
│       │   │   │   ├── compliance_rule.py
│       │   │   │   └── fallback_behavior.py
│       │   │   ├── repositories/
│       │   │   │   └── playbook_repository.py
│       │   │   ├── events/
│       │   │   │   └── playbook_events.py
│       │   │   ├── services/
│       │   │   │   ├── pattern_mining_service.py
│       │   │   │   └── agent_clustering_service.py
│       │   │   └── factories/
│       │   │       └── playbook_builder.py   # Builder pattern
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── generate_playbook.py
│       │   │   │   ├── activate_playbook.py
│       │   │   │   └── rollback_playbook.py
│       │   │   └── queries/
│       │   │       ├── get_playbook.py
│       │   │       └── list_playbook_versions.py
│       │   └── infrastructure/
│       │       ├── persistence/
│       │       └── acl/
│       │           └── processing_acl.py
│       │
│       ├── prompt/                       # ─── PROMPT CONTEXT ───
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   └── agent_prompt.py
│       │   │   ├── value_objects/
│       │   │   │   ├── prompt_body.py
│       │   │   │   ├── guardrail.py
│       │   │   │   └── prompt_metrics.py
│       │   │   ├── repositories/
│       │   │   │   └── prompt_repository.py
│       │   │   ├── events/
│       │   │   │   └── prompt_events.py
│       │   │   ├── services/
│       │   │   │   ├── prompt_compiler.py    # Domain Service
│       │   │   │   └── prompt_optimizer.py   # Domain Service
│       │   │   └── factories/
│       │   │       └── prompt_builder.py     # Builder pattern
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── generate_prompt.py
│       │   │   │   ├── optimize_prompt.py
│       │   │   │   └── create_ab_test.py
│       │   │   └── queries/
│       │   │       ├── get_prompt.py
│       │   │       └── get_ab_test_results.py
│       │   └── infrastructure/
│       │       ├── persistence/
│       │       └── templates/
│       │           └── prompt_templates.py
│       │
│       ├── conversation/                 # ─── CONVERSATION CONTEXT ───
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   ├── conversation.py
│       │   │   │   └── message.py
│       │   │   ├── value_objects/
│       │   │   │   ├── channel.py
│       │   │   │   ├── conversation_status.py
│       │   │   │   ├── tool_call.py
│       │   │   │   └── session_memory.py
│       │   │   ├── repositories/
│       │   │   │   └── conversation_repository.py
│       │   │   ├── events/
│       │   │   │   └── conversation_events.py
│       │   │   ├── services/
│       │   │   │   └── turn_processing_service.py
│       │   │   └── factories/
│       │   │       └── conversation_factory.py
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── start_conversation.py
│       │   │   │   ├── process_turn.py
│       │   │   │   └── end_conversation.py
│       │   │   └── queries/
│       │   │       ├── get_conversation.py
│       │   │       ├── list_conversations.py
│       │   │       └── get_conversation_summary.py
│       │   └── infrastructure/
│       │       └── persistence/
│       │
│       ├── voice/                        # ─── VOICE CONTEXT ───
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   └── voice_session.py
│       │   │   ├── value_objects/
│       │   │   │   ├── audio_config.py
│       │   │   │   ├── latency_metrics.py
│       │   │   │   └── voice_channel.py
│       │   │   ├── events/
│       │   │   │   └── voice_events.py
│       │   │   └── factories/
│       │   │       └── voice_session_factory.py
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── start_voice_session.py
│       │   │   │   ├── handle_barge_in.py
│       │   │   │   └── end_voice_session.py
│       │   │   └── queries/
│       │   │       └── get_session_status.py
│       │   └── infrastructure/
│       │       ├── pipeline/
│       │       │   ├── voice_pipeline.py
│       │       │   └── interruption_detector.py
│       │       ├── gateway/
│       │       │   ├── websocket_gateway.py
│       │       │   └── webrtc_gateway.py
│       │       └── telephony/
│       │           └── twilio_handler.py
│       │
│       ├── evaluation/                   # ─── EVALUATION CONTEXT ───
│       │   ├── domain/
│       │   │   ├── entities/
│       │   │   │   └── evaluation.py
│       │   │   ├── value_objects/
│       │   │   │   ├── dimension_scores.py
│       │   │   │   ├── compliance_violation.py
│       │   │   │   └── coaching_note.py
│       │   │   ├── repositories/
│       │   │   │   └── evaluation_repository.py
│       │   │   ├── events/
│       │   │   │   └── evaluation_events.py
│       │   │   ├── specifications/
│       │   │   │   └── low_score_spec.py
│       │   │   └── factories/
│       │   │       └── evaluator_factory.py  # Strategy factory
│       │   ├── application/
│       │   │   ├── commands/
│       │   │   │   ├── evaluate_conversation.py
│       │   │   │   └── batch_evaluate.py
│       │   │   └── queries/
│       │   │       ├── get_evaluation.py
│       │   │       └── get_evaluation_report.py
│       │   └── infrastructure/
│       │       ├── persistence/
│       │       ├── strategies/              # Evaluation strategies
│       │       │   ├── llm_judge_evaluator.py
│       │       │   └── rule_based_evaluator.py
│       │       └── acl/
│       │           └── conversation_acl.py
│       │
│       ├── analytics/                    # ─── ANALYTICS CONTEXT (CQRS Read Side) ───
│       │   ├── read_models/
│       │   │   ├── agent_performance_view.py
│       │   │   ├── sentiment_timeline_view.py
│       │   │   ├── conversation_summary_view.py
│       │   │   ├── compliance_report_view.py
│       │   │   └── lead_score_view.py
│       │   ├── event_handlers/
│       │   │   ├── on_evaluation_completed.py
│       │   │   └── on_conversation_ended.py
│       │   └── queries/
│       │       ├── get_overview.py
│       │       ├── get_agent_performance.py
│       │       └── get_compliance_report.py
│       │
│       ├── presentation/                 # ─── PRESENTATION LAYER ───
│       │   ├── __init__.py
│       │   ├── main.py                   # FastAPI app entry
│       │   ├── config.py                 # Settings (pydantic-settings)
│       │   ├── container.py              # DI Container
│       │   ├── middleware/
│       │   │   ├── auth_middleware.py
│       │   │   ├── tenant_middleware.py
│       │   │   ├── rate_limit_middleware.py
│       │   │   ├── correlation_middleware.py
│       │   │   └── logging_middleware.py
│       │   ├── api/
│       │   │   └── v1/
│       │   │       ├── router.py
│       │   │       ├── agents_controller.py
│       │   │       ├── playbooks_controller.py
│       │   │       ├── prompts_controller.py
│       │   │       ├── ingestion_controller.py
│       │   │       ├── knowledge_controller.py
│       │   │       ├── conversations_controller.py
│       │   │       ├── evaluation_controller.py
│       │   │       ├── analytics_controller.py
│       │   │       └── webhooks_controller.py
│       │   ├── schemas/                   # Request/Response schemas
│       │   │   ├── agent_schemas.py
│       │   │   ├── playbook_schemas.py
│       │   │   ├── knowledge_schemas.py
│       │   │   └── conversation_schemas.py
│       │   └── websocket/
│       │       ├── voice_stream_handler.py
│       │       └── live_monitor_handler.py
│       │
│       └── cross_cutting/                # ─── CROSS-CUTTING (Infrastructure) ───
│           ├── __init__.py
│           ├── adapters/                 # External service adapters
│           │   ├── stt/
│           │   │   ├── deepgram_adapter.py
│           │   │   ├── whisper_adapter.py
│           │   │   └── assemblyai_adapter.py
│           │   ├── tts/
│           │   │   ├── elevenlabs_adapter.py
│           │   │   ├── cartesia_adapter.py
│           │   │   └── google_tts_adapter.py
│           │   ├── llm/
│           │   │   ├── gemini_adapter.py
│           │   │   ├── openai_adapter.py
│           │   │   └── claude_adapter.py
│           │   ├── storage/
│           │   │   └── s3_adapter.py
│           │   ├── vector/
│           │   │   └── qdrant_adapter.py
│           │   ├── cache/
│           │   │   └── redis_adapter.py
│           │   ├── queue/
│           │   │   └── rabbitmq_adapter.py
│           │   └── telephony/
│           │       └── twilio_adapter.py
│           ├── decorators/               # Handler decorators
│           │   ├── logging_decorator.py
│           │   ├── caching_decorator.py
│           │   ├── metrics_decorator.py
│           │   ├── authorization_decorator.py
│           │   ├── validation_decorator.py
│           │   ├── transaction_decorator.py
│           │   └── retry_decorator.py
│           ├── persistence/              # Shared DB infra
│           │   ├── database.py           # Engine, session factory
│           │   └── unit_of_work_impl.py
│           ├── observability/
│           │   ├── structured_logger.py
│           │   ├── prometheus_metrics.py
│           │   └── opentelemetry_tracer.py
│           ├── security/
│           │   ├── jwt_service.py
│           │   ├── rbac_service.py
│           │   └── pii_masker.py
│           └── resilience/
│               ├── circuit_breaker.py
│               └── retry_policy.py
│
├── frontend/                             # (unchanged from v1)
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── app/
│       ├── components/
│       ├── hooks/
│       ├── lib/
│       ├── stores/
│       └── types/
│
├── sdk/
│   ├── python/
│   └── javascript/
│
├── tests/
│   ├── unit/                             # Mirror src/ structure
│   │   ├── agent/
│   │   │   ├── domain/
│   │   │   └── application/
│   │   ├── playbook/
│   │   ├── conversation/
│   │   └── ...
│   ├── integration/
│   │   ├── persistence/
│   │   ├── adapters/
│   │   └── event_handlers/
│   ├── contract/                         # Port contract tests
│   │   ├── stt_port_contract.py
│   │   ├── tts_port_contract.py
│   │   └── llm_port_contract.py
│   ├── e2e/
│   └── conftest.py
│
└── scripts/
    ├── seed_db.py
    └── load_test.py
```

---

## Structure Rules

| Rule | Rationale |
|------|-----------|
| Every bounded context has `domain/`, `application/`, `infrastructure/` | Clean Architecture per context |
| `domain/` has zero imports from `infrastructure/` or `presentation/` | Dependency inversion |
| Commands and Queries live in separate directories | CQRS separation |
| External adapters live in `cross_cutting/adapters/`, not inside contexts | Single adapter per external service, shared across contexts |
| Each context's `infrastructure/persistence/` has its own models | Avoids a monolithic models file |
| Tests mirror `src/` structure | Easy to locate tests for any module |
| Contract tests verify port implementations | Ensures adapter substitutability |
