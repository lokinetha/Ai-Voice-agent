# 6. Data Flow — v2

> **Enterprise Architecture Review**
>
> **v1 Weaknesses**: Data flows described in terms of services, not domain events.
> No aggregate boundaries shown. No command/query distinction in flows. Missing
> anti-corruption layers between contexts.
>
> **v2 Improvements**: All flows expressed as Command → Aggregate → Event → Handler chains.
> ACL boundaries shown. CQRS read/write paths distinguished.

---

## Master Data Flow: Domain Event Chain

```mermaid
graph TB
    subgraph "Ingestion Context"
        CMD1["IngestAudioCommand"]
        AGG1["DataSource Aggregate"]
        EVT1["RecordingUploaded"]
    end

    subgraph "Processing Context"
        ACL1["Ingestion ACL<br/>(translate event → command)"]
        CMD2["StartTranscriptionCommand"]
        AGG2["ProcessingJob Aggregate"]
        EVT2["TranscriptGenerated"]
        EVT3["RecordingProcessed"]
    end

    subgraph "Knowledge Context"
        ACL2["Processing ACL"]
        CMD3["IndexTranscriptCommand"]
        AGG3["KnowledgeBase Aggregate"]
        EVT4["KnowledgeIndexed"]
    end

    subgraph "Playbook Context"
        ACL3["Processing ACL"]
        CMD4["ExtractPatternsCommand"]
        CMD5["GeneratePlaybookCommand"]
        AGG4["Playbook Aggregate"]
        EVT5["PlaybookGenerated"]
    end

    subgraph "Prompt Context"
        ACL4["Playbook ACL"]
        CMD6["GeneratePromptCommand"]
        AGG5["AgentPrompt Aggregate"]
        EVT6["PromptGenerated"]
    end

    subgraph "Agent Context"
        CMD7["PublishAgentCommand"]
        AGG6["Agent Aggregate"]
        EVT7["AgentPublished"]
    end

    CMD1 --> AGG1 --> EVT1
    EVT1 -->|async| ACL1 --> CMD2 --> AGG2
    AGG2 --> EVT2
    AGG2 --> EVT3

    EVT2 -->|async| ACL2 --> CMD3 --> AGG3 --> EVT4
    EVT3 -->|async| ACL3 --> CMD4
    CMD4 --> CMD5 --> AGG4 --> EVT5
    EVT5 -->|async| ACL4 --> CMD6 --> AGG5 --> EVT6
    EVT6 -->|manual trigger| CMD7 --> AGG6 --> EVT7
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Every arrow between contexts goes through an **ACL** | Prevents domain model leakage |
| Every context boundary is **async** (event-driven) | Temporal decoupling, independent deployment |
| Aggregates own their events | Events are raised within aggregate methods, dispatched after commit |
| Final step (Publish) is **manual** | Human-in-the-loop before agent goes live |

---

## Write Path: Agent Cloning Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Ctrl as Controller
    participant Bus as Command Bus
    participant Handler
    participant Agg as Aggregate
    participant UoW as Unit of Work
    participant DB
    participant Events as Event Bus
    participant ACL as Anti-Corruption Layer
    participant NextHandler as Next Context Handler

    User->>Ctrl: POST /ingestion/audio
    Ctrl->>Bus: dispatch(IngestAudioCommand)
    Bus->>Handler: IngestAudioHandler.handle()
    Handler->>Handler: validate, upload to S3
    Handler->>Agg: DataSource.addRecording()
    Agg->>Agg: _raise_event(RecordingUploaded)
    Handler->>UoW: commit()
    UoW->>DB: persist
    UoW->>Events: publish(RecordingUploaded)

    Events->>ACL: RecordingUploaded event
    ACL->>ACL: translate → StartTranscriptionCommand
    ACL->>Bus: dispatch(StartTranscriptionCommand)
    Bus->>NextHandler: StartTranscriptionHandler.handle()
    NextHandler->>NextHandler: STT via STTPort
    NextHandler->>Agg: ProcessingJob.completeTranscription()
    Agg->>Agg: _raise_event(TranscriptGenerated)
    NextHandler->>UoW: commit()
    UoW->>Events: publish(TranscriptGenerated)

    Note over Events: Chain continues through<br/>Knowledge → Playbook → Prompt
```

---

## Read Path: Live Conversation (CQRS Query Side)

```mermaid
sequenceDiagram
    participant Caller
    participant Gateway as Voice Gateway
    participant Brain as Turn Processing Service
    participant Cache as Cache (Redis)
    participant RAG as Retrieval Service
    participant Vector as VectorStorePort
    participant LLM as LLMPort
    participant ReadModel as Agent Config Read Model

    Caller->>Gateway: Audio stream
    Gateway->>Gateway: STT (via STTPort)
    Gateway->>Brain: user utterance

    Brain->>Cache: load session memory
    Brain->>ReadModel: get agent config (cached)
    Brain->>RAG: search knowledge
    RAG->>Vector: hybrid search (dense + sparse)
    Vector-->>RAG: ranked chunks with citations
    RAG-->>Brain: knowledge context

    Brain->>LLM: system prompt + memory + knowledge + utterance
    LLM-->>Brain: response (streamed)

    Brain->>Cache: update session memory
    Brain->>Gateway: response text
    Gateway->>Gateway: TTS (via TTSPort)
    Gateway-->>Caller: audio response (streamed)
```

**Note**: The live conversation path is read-heavy (no aggregate mutations during the conversation). Conversation persistence happens asynchronously after the conversation ends, via `ConversationEndedEvent`.

---

## Event Dispatch: Transactional Outbox Pattern

```mermaid
graph LR
    subgraph "Within Transaction"
        AGG["Aggregate<br/>raises events"]
        DB_WRITE["Write to<br/>domain table"]
        OUTBOX["Write to<br/>outbox table"]
    end

    subgraph "After Transaction"
        POLLER["Outbox Poller<br/>(background)"]
        BUS["RabbitMQ"]
        MARK["Mark as<br/>dispatched"]
    end

    AGG --> DB_WRITE
    AGG --> OUTBOX
    OUTBOX --> POLLER
    POLLER --> BUS
    POLLER --> MARK
```

```sql
CREATE TABLE outbox (
    id          UUID PRIMARY KEY,
    event_type  VARCHAR NOT NULL,
    payload     JSONB NOT NULL,
    tenant_id   UUID NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    dispatched  BOOLEAN NOT NULL DEFAULT FALSE,
    dispatched_at TIMESTAMP
);

CREATE INDEX idx_outbox_undispatched
    ON outbox (created_at) WHERE dispatched = FALSE;
```

This ensures **exactly-once semantics**: events survive application crashes and are reliably delivered.

---

## Knowledge Indexing Flow

```mermaid
graph LR
    subgraph "Command"
        DOC["AddDocumentCommand"]
    end

    subgraph "Handler Pipeline"
        PARSE["DocumentParser<br/>(strategy by type)"]
        CLEAN["TextPreprocessor"]
        CHUNK["Chunker<br/>(strategy by config)"]
        EMBED["EmbeddingPort<br/>(adapter)"]
        INDEX["VectorStorePort<br/>(adapter)"]
    end

    subgraph "Aggregate"
        KB["KnowledgeBase<br/>aggregate updates"]
        EVT["KnowledgeIndexed<br/>event"]
    end

    DOC --> PARSE --> CLEAN --> CHUNK --> EMBED --> INDEX
    INDEX --> KB --> EVT
```

---

## Evaluation Flow

```mermaid
graph LR
    subgraph "Trigger"
        EVT_IN["ConversationEnded<br/>event"]
    end

    subgraph "ACL"
        CONV_ACL["Conversation ACL<br/>(translate event)"]
    end

    subgraph "Handler"
        CMD["EvaluateConversationCommand"]
        EVAL_H["EvaluateConversationHandler"]
        FACTORY["EvaluatorFactory<br/>(strategy selection)"]
        JUDGE["LLMJudgeEvaluator<br/>or RuleBasedEvaluator"]
    end

    subgraph "Aggregate"
        EVAL_AGG["Evaluation aggregate"]
        EVT_OUT["EvaluationCompleted<br/>event"]
    end

    subgraph "Read Model Update"
        ANALYTICS["Analytics Event Handler<br/>(refresh materialized views)"]
    end

    EVT_IN --> CONV_ACL --> CMD --> EVAL_H
    EVAL_H --> FACTORY --> JUDGE
    JUDGE --> EVAL_AGG --> EVT_OUT
    EVT_OUT --> ANALYTICS
```
