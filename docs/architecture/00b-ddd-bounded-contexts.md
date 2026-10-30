# 00b. DDD Bounded Contexts & Aggregates

> **Enterprise Architecture Review — New Foundation Document**
>
> Defines all bounded contexts, their aggregates, entities, value objects,
> domain events, repositories, factories, and inter-context contracts.

---

## Context Map

```mermaid
graph TB
    subgraph "Core Domain"
        AGENT["Agent Context"]
        CONV["Conversation Context"]
        VOICE["Voice Context"]
    end

    subgraph "Supporting Domain"
        PLAYBOOK["Playbook Context"]
        PROMPT["Prompt Context"]
        KNOWLEDGE["Knowledge Context"]
        EVAL["Evaluation Context"]
    end

    subgraph "Generic Domain"
        IDENTITY["Identity Context"]
        ORG["Organization Context"]
        INGEST["Ingestion Context"]
        PROC["Processing Context"]
        ANALYTICS["Analytics Context"]
    end

    ORG -->|Conformist| IDENTITY
    AGENT -->|Partnership| PLAYBOOK
    AGENT -->|Partnership| PROMPT
    AGENT -->|Partnership| KNOWLEDGE
    CONV -->|Customer-Supplier| AGENT
    CONV -->|Customer-Supplier| KNOWLEDGE
    VOICE -->|Customer-Supplier| CONV
    EVAL -->|Customer-Supplier| CONV
    PROC -->|Published Language| INGEST
    PLAYBOOK -->|Customer-Supplier| PROC
    ANALYTICS -->|Customer-Supplier| EVAL
    ANALYTICS -->|Customer-Supplier| CONV
    PROMPT -->|Customer-Supplier| PLAYBOOK
```

### Context Relationships

| Upstream | Downstream | Relationship | Integration |
|----------|-----------|-------------|-------------|
| Identity | Organization | Conformist | Shared DB |
| Ingestion | Processing | Published Language | Events |
| Processing | Playbook | Customer-Supplier | Events |
| Playbook | Prompt | Customer-Supplier | Events |
| Agent | Conversation | Customer-Supplier | Domain Service |
| Knowledge | Conversation | Customer-Supplier | Query Interface |
| Conversation | Evaluation | Customer-Supplier | Events |
| Conversation, Evaluation | Analytics | Customer-Supplier | Read Models |

---

## Bounded Context Details

---

### 1. Identity Context

**Responsibility**: Authentication, authorization, user management.

```mermaid
classDiagram
    class User {
        <<Aggregate Root>>
        -UserId id
        -Email email
        -PasswordHash passwordHash
        -UserRole role
        -TenantId tenantId
        -Timestamp lastLogin
        +changePassword(old, new) Result
        +updateRole(role) Result
    }

    class UserRole {
        <<Value Object>>
        +string value
        OWNER
        ADMIN
        MEMBER
        VIEWER
    }

    class PasswordHash {
        <<Value Object>>
        +string hash
        +string algorithm
        +verify(plain) bool
    }

    class ApiKey {
        <<Entity>>
        -EntityId id
        -UserId userId
        -string keyHash
        -string prefix
        -Timestamp expiresAt
        -list~string~ scopes
    }

    User --> UserRole
    User --> PasswordHash
    User --> ApiKey
```

| Element | Type | Notes |
|---------|------|-------|
| `User` | Aggregate Root | Only root persisted via `UserRepository` |
| `ApiKey` | Entity (child) | Owned by User aggregate |
| `Email`, `PasswordHash`, `UserRole` | Value Objects | Self-validating, immutable |
| `UserRepository` | Repository Interface | `get_by_id`, `get_by_email`, `save`, `delete` |
| `UserFactory` | Factory | Creates user with hashed password |
| `UserRegistered` | Domain Event | Published on registration |
| `UserRoleChanged` | Domain Event | Published on role change |
| `AuthenticationService` | Domain Service | Validates credentials, issues tokens |

---

### 2. Organization Context

**Responsibility**: Multi-tenancy, workspaces, billing, feature flags.

```mermaid
classDiagram
    class Organization {
        <<Aggregate Root>>
        -OrganizationId id
        -TenantId tenantId
        -OrgName name
        -Plan plan
        -BillingInfo billing
        -OrgSettings settings
        +createWorkspace(name, config) Result~Workspace~
        +changePlan(plan) Result
        +updateSettings(settings) Result
    }

    class Workspace {
        <<Entity>>
        -WorkspaceId id
        -WorkspaceName name
        -WorkspaceConfig config
        -WorkspaceStatus status
        +activate() Result
        +deactivate() Result
    }

    class Plan {
        <<Value Object>>
        +PlanTier tier
        +int maxAgents
        +int maxMinutesPerMonth
        +int maxKBDocuments
        +MoneyAmount price
    }

    class OrgSettings {
        <<Value Object>>
        +Language defaultLanguage
        +Region region
        +bool complianceMode
        +RetentionPolicy retention
    }

    Organization *-- Workspace : contains
    Organization --> Plan
    Organization --> OrgSettings
```

| Element | Type | Notes |
|---------|------|-------|
| `Organization` | Aggregate Root | Owns workspaces. Invariant: workspace count ≤ plan limit |
| `Workspace` | Entity (child) | Cannot exist without Organization |
| `Plan`, `OrgSettings` | Value Objects | Immutable config |
| `OrganizationRepository` | Repository Interface | |
| `OrganizationFactory` | Factory | Creates org with default workspace |
| `WorkspaceCreated`, `PlanChanged` | Domain Events | |

---

### 3. Agent Context

**Responsibility**: Agent lifecycle, configuration, deployment status.

```mermaid
classDiagram
    class Agent {
        <<Aggregate Root>>
        -AgentId id
        -WorkspaceId workspaceId
        -AgentName name
        -AgentType type
        -AgentStatus status
        -AgentVoiceConfig voiceConfig
        -AgentRuntimeConfig runtimeConfig
        -AgentLLMConfig llmConfig
        -AgentMemoryConfig memoryConfig
        -list~AgentTool~ tools
        -list~AgentPolicy~ policies
        +publish() Result
        +unpublish() Result
        +addTool(tool) Result
        +removeTool(toolId) Result
        +addPolicy(policy) Result
        +updateVoiceConfig(config) Result
        +updateLLMConfig(config) Result
        +clone(newName) Result~Agent~
    }

    class AgentVoiceConfig {
        <<Value Object>>
        +string ttsProvider
        +string voiceId
        +float speed
        +float pitch
        +Language language
    }

    class AgentRuntimeConfig {
        <<Value Object>>
        +int maxConcurrentSessions
        +int sessionTimeoutSeconds
        +int silenceThresholdMs
        +bool bargeInEnabled
    }

    class AgentLLMConfig {
        <<Value Object>>
        +string provider
        +string model
        +float temperature
        +int maxTokens
        +int contextWindow
    }

    class AgentMemoryConfig {
        <<Value Object>>
        +int shortTermWindowSize
        +bool longTermEnabled
        +string longTermStrategy
    }

    class AgentTool {
        <<Entity>>
        -EntityId id
        -ToolName name
        -ToolType type
        -ToolSchema schema
        -ToolConfig config
        -bool enabled
    }

    class AgentPolicy {
        <<Entity>>
        -EntityId id
        -PolicyType type
        -PolicyRule rule
        -PolicyAction violationAction
        -bool enforced
    }

    class AgentStatus {
        <<Value Object>>
        DRAFT
        TESTING
        PUBLISHED
        PAUSED
        ARCHIVED
    }

    class AgentType {
        <<Value Object>>
        SALES
        SUPPORT
        INSURANCE
        HEALTHCARE
        BANKING
        LEGAL
        HR
        BOOKING
        CUSTOM
    }

    Agent --> AgentVoiceConfig
    Agent --> AgentRuntimeConfig
    Agent --> AgentLLMConfig
    Agent --> AgentMemoryConfig
    Agent --> AgentStatus
    Agent --> AgentType
    Agent *-- AgentTool
    Agent *-- AgentPolicy
```

| Element | Type | Notes |
|---------|------|-------|
| `Agent` | Aggregate Root | Invariant: can only `publish()` if playbook + prompt exist |
| `AgentTool`, `AgentPolicy` | Entity (children) | Owned by Agent |
| `AgentVoiceConfig`, `AgentLLMConfig`, etc. | Value Objects | Replace JSON blobs |
| `AgentRepository` | Repository Interface | |
| `AgentFactory` | Factory | Creates agent with sensible defaults per type |
| `AgentPublished`, `AgentUnpublished`, `AgentCloned` | Domain Events | |

**Invariants**:
- Agent cannot be published without an active Playbook and Prompt.
- Agent tool count ≤ plan limit.
- Agent policies must contain at least one fallback policy.

---

### 4. Ingestion Context

**Responsibility**: Accept, validate, normalize, and store raw data.

```mermaid
classDiagram
    class DataSource {
        <<Aggregate Root>>
        -EntityId id
        -WorkspaceId workspaceId
        -DataSourceType type
        -DataSourceName name
        -DataSourceStatus status
        -DataSourceConfig config
        -IngestionMetadata metadata
        +startIngestion() Result
        +completeIngestion() Result
        +failIngestion(reason) Result
    }

    class Recording {
        <<Entity>>
        -RecordingId id
        -StorageKey s3Key
        -Duration duration
        -AudioFormat format
        -RecordingStatus status
    }

    class Document {
        <<Entity>>
        -DocumentId id
        -DocumentType type
        -StorageKey s3Key
        -DocumentTitle title
        -DocumentStatus status
    }

    class DataSourceType {
        <<Value Object>>
        AUDIO
        TRANSCRIPT
        PDF
        DOCX
        CSV
        WEBSITE
        CRM
        KNOWLEDGE_BASE
    }

    DataSource *-- Recording
    DataSource *-- Document
    DataSource --> DataSourceType
```

| Element | Type |
|---------|------|
| `DataSource` | Aggregate Root |
| `Recording`, `Document` | Entity (children) |
| `DataSourceRepository` | Repository Interface |
| `DataSourceFactory` | Factory |
| `RecordingUploaded`, `DocumentUploaded`, `IngestionCompleted`, `IngestionFailed` | Domain Events |

---

### 5. Processing Context

**Responsibility**: STT, diarization, sentiment, intent, topic segmentation.

```mermaid
classDiagram
    class ProcessingJob {
        <<Aggregate Root>>
        -EntityId id
        -RecordingId recordingId
        -ProcessingStatus status
        -ProcessingStages stages
        -ProcessingResult result
        +startTranscription() Result
        +completeDiarization(segments) Result
        +completeSentiment(timeline) Result
        +completeIntents(intents) Result
        +completeTopics(topics) Result
        +fail(stage, reason) Result
    }

    class TranscriptSegment {
        <<Value Object>>
        +Speaker speaker
        +float startTime
        +float endTime
        +string text
        +float confidence
    }

    class SentimentScore {
        <<Value Object>>
        +float polarity
        +string emotion
        +float startTime
        +float endTime
    }

    class DetectedIntent {
        <<Value Object>>
        +string category
        +string intent
        +float confidence
        +float timestamp
    }

    ProcessingJob --> TranscriptSegment
    ProcessingJob --> SentimentScore
    ProcessingJob --> DetectedIntent
```

| Element | Type |
|---------|------|
| `ProcessingJob` | Aggregate Root |
| `TranscriptSegment`, `SentimentScore`, `DetectedIntent` | Value Objects |
| `ProcessingJobRepository` | Repository Interface |
| `ProcessingJobFactory` | Factory |
| `TranscriptGenerated`, `RecordingProcessed` | Domain Events |

---

### 6. Knowledge Context

**Responsibility**: RAG — indexing, chunking, embedding, retrieval, versioning.

```mermaid
classDiagram
    class KnowledgeBase {
        <<Aggregate Root>>
        -KnowledgeBaseId id
        -WorkspaceId workspaceId
        -KBName name
        -EmbeddingConfig embeddingConfig
        -ChunkingConfig chunkingConfig
        -Version version
        -KBStatus status
        +addDocument(doc) Result
        +removeDocument(docId) Result
        +reindex() Result
        +createVersion() Result
        +rollbackToVersion(ver) Result
    }

    class KBDocument {
        <<Entity>>
        -DocumentId id
        -DocumentTitle title
        -int chunkCount
        -DocumentStatus status
        -SourceReference source
    }

    class EmbeddingConfig {
        <<Value Object>>
        +string model
        +int dimension
        +string collectionName
    }

    class ChunkingConfig {
        <<Value Object>>
        +ChunkingStrategy strategy
        +int chunkSize
        +int overlap
    }

    class ChunkingStrategy {
        <<Value Object>>
        RECURSIVE
        SEMANTIC
        QA_PAIR
        TABLE
        CONVERSATION
    }

    KnowledgeBase *-- KBDocument
    KnowledgeBase --> EmbeddingConfig
    KnowledgeBase --> ChunkingConfig
    ChunkingConfig --> ChunkingStrategy
```

| Element | Type |
|---------|------|
| `KnowledgeBase` | Aggregate Root |
| `KBDocument` | Entity (child) |
| `KnowledgeBaseRepository` | Repository Interface |
| `KnowledgeBaseFactory` | Factory |
| `ChunkingStrategyResolver` | Strategy (selects chunker by doc type) |
| `RetrievalService` | Domain Service (hybrid search orchestration) |
| `KnowledgeIndexed`, `KnowledgeUpdated`, `KnowledgeVersionCreated` | Domain Events |

---

### 7. Playbook Context

**Responsibility**: Generate and version structured behavioral playbooks.

```mermaid
classDiagram
    class Playbook {
        <<Aggregate Root>>
        -PlaybookId id
        -AgentId agentId
        -PlaybookVersion version
        -PlaybookStatus status
        -RoleDefinition role
        -PersonaDefinition persona
        -list~ConversationStage~ stages
        -list~ObjectionStrategy~ objectionHandlers
        -list~ComplianceRule~ complianceRules
        -list~BusinessPolicy~ policies
        -ConversationConstraints constraints
        -list~FallbackBehavior~ fallbacks
        +activate() Result
        +deactivate() Result
        +createNewVersion() Result~Playbook~
    }

    class RoleDefinition {
        <<Value Object>>
        +string title
        +string company
        +string department
    }

    class PersonaDefinition {
        <<Value Object>>
        +string name
        +string personality
        +CommunicationStyle style
    }

    class CommunicationStyle {
        <<Value Object>>
        +string tone
        +string pace
        +string vocabularyLevel
        +string energyLevel
        +string empathyLevel
    }

    class ConversationStage {
        <<Entity>>
        -EntityId id
        -string stageName
        -string objective
        -Duration duration
        -list~string~ techniques
        -list~string~ exampleUtterances
        -StageTransition transition
        -int orderIndex
    }

    class ObjectionStrategy {
        <<Entity>>
        -EntityId id
        -ObjectionType type
        -string strategy
        -string responsePattern
        -list~string~ examples
    }

    class ComplianceRule {
        <<Value Object>>
        +string rule
        +Severity severity
        +string violationAction
    }

    Playbook --> RoleDefinition
    Playbook --> PersonaDefinition
    PersonaDefinition --> CommunicationStyle
    Playbook *-- ConversationStage
    Playbook *-- ObjectionStrategy
    Playbook --> ComplianceRule
```

| Element | Type |
|---------|------|
| `Playbook` | Aggregate Root |
| `ConversationStage`, `ObjectionStrategy` | Entity (children) |
| `RoleDefinition`, `PersonaDefinition`, `ComplianceRule` | Value Objects |
| `PlaybookRepository` | Repository Interface |
| `PlaybookFactory`, `PlaybookBuilder` | Factory + Builder |
| `PlaybookMiningService` | Domain Service (LLM-powered extraction) |
| `PlaybookGenerated`, `PlaybookActivated` | Domain Events |

---

### 8. Prompt Context

**Responsibility**: Compile playbook into production system prompts.

```mermaid
classDiagram
    class AgentPrompt {
        <<Aggregate Root>>
        -PromptId id
        -AgentId agentId
        -PlaybookId sourcePlaybookId
        -PromptVersion version
        -PromptBody body
        -list~Guardrail~ guardrails
        -list~PromptExample~ examples
        -PromptStatus status
        -PromptMetrics metrics
        +activate() Result
        +deactivate() Result
        +createOptimizedVersion(feedback) Result~AgentPrompt~
    }

    class PromptBody {
        <<Value Object>>
        +string roleSection
        +string objectivesSection
        +string personaSection
        +string flowSection
        +string knowledgeSection
        +string dosSection
        +string dontsSection
        +string objectionSection
        +string policiesSection
        +string examplesSection
        +string guardrailsSection
        +string successSection
        +int tokenCount
        +compile() string
    }

    class Guardrail {
        <<Value Object>>
        +GuardrailType type
        +string rule
        +string action
    }

    class PromptMetrics {
        <<Value Object>>
        +int conversationCount
        +Score avgEvaluationScore
        +float conversionRate
    }

    AgentPrompt --> PromptBody
    AgentPrompt --> Guardrail
    AgentPrompt --> PromptMetrics
```

| Element | Type |
|---------|------|
| `AgentPrompt` | Aggregate Root |
| `PromptBody`, `Guardrail`, `PromptMetrics` | Value Objects |
| `AgentPromptRepository` | Repository Interface |
| `PromptCompiler` | Domain Service (playbook → prompt sections) |
| `PromptOptimizer` | Domain Service (evaluation → improvements) |
| `PromptFactory`, `PromptBuilder` | Factory + Builder |
| `PromptGenerated`, `PromptOptimized`, `PromptActivated` | Domain Events |

---

### 9. Conversation Context

**Responsibility**: Conversation lifecycle, turns, memory, real-time state.

```mermaid
classDiagram
    class Conversation {
        <<Aggregate Root>>
        -ConversationId id
        -AgentId agentId
        -CustomerId customerId
        -Channel channel
        -ConversationStatus status
        -ConversationStage currentStage
        -list~Message~ messages
        -SessionMemory memory
        -Duration duration
        +addMessage(msg) Result
        +changeStage(stage) Result
        +end(reason) Result
        +addToolCallResult(result) Result
    }

    class Message {
        <<Entity>>
        -MessageId id
        -MessageRole role
        -MessageContent content
        -list~ToolCall~ toolCalls
        -Latency latency
        -Timestamp createdAt
    }

    class ToolCall {
        <<Value Object>>
        +string functionName
        +dict arguments
        +dict result
        +Duration executionTime
    }

    class SessionMemory {
        <<Value Object>>
        +list~dict~ shortTermWindow
        +dict customerContext
        +dict ragCache
        +dict toolResults
    }

    class Channel {
        <<Value Object>>
        TWILIO
        WEBRTC
        WEBSOCKET
        SIP
        BROWSER
    }

    class ConversationStatus {
        <<Value Object>>
        ACTIVE
        PAUSED
        ENDED_NORMAL
        ENDED_TIMEOUT
        ENDED_ERROR
        TRANSFERRED
    }

    Conversation *-- Message
    Conversation --> SessionMemory
    Conversation --> Channel
    Conversation --> ConversationStatus
    Message --> ToolCall
```

| Element | Type |
|---------|------|
| `Conversation` | Aggregate Root |
| `Message` | Entity (child) |
| `ToolCall`, `SessionMemory`, `Channel` | Value Objects |
| `ConversationRepository` | Repository Interface |
| `ConversationFactory` | Factory |
| `TurnProcessingService` | Domain Service (context + RAG + LLM) |
| `ConversationStarted`, `ConversationEnded`, `ToolExecuted` | Domain Events |

---

### 10. Voice Context

**Responsibility**: Real-time audio streaming, session management, media routing.

```mermaid
classDiagram
    class VoiceSession {
        <<Aggregate Root>>
        -SessionId id
        -ConversationId conversationId
        -VoiceChannel channel
        -VoiceSessionStatus status
        -AudioConfig audioConfig
        -LatencyMetrics latencies
        +startStreaming() Result
        +handleBargeIn() Result
        +handleSilence(duration) Result
        +endSession() Result
    }

    class AudioConfig {
        <<Value Object>>
        +AudioFormat inputFormat
        +AudioFormat outputFormat
        +int sampleRate
        +int channels
    }

    class LatencyMetrics {
        <<Value Object>>
        +float avgSttMs
        +float avgLlmTtftMs
        +float avgTtsMs
        +float avgE2eMs
    }

    class VoiceChannel {
        <<Value Object>>
        TWILIO_MEDIA_STREAM
        WEBRTC_PEER
        WEBSOCKET_RAW
    }

    VoiceSession --> AudioConfig
    VoiceSession --> LatencyMetrics
    VoiceSession --> VoiceChannel
```

---

### 11. Evaluation Context

**Responsibility**: Score conversations, compliance, coaching feedback.

```mermaid
classDiagram
    class Evaluation {
        <<Aggregate Root>>
        -EvaluationId id
        -ConversationId conversationId
        -AgentId agentId
        -DimensionScores scores
        -Score overallScore
        -list~ComplianceViolation~ violations
        -list~CoachingNote~ coachingNotes
        -EvaluationStatus status
        +complete(scores) Result
        +addViolation(violation) Result
    }

    class DimensionScores {
        <<Value Object>>
        +Score greeting
        +Score empathy
        +Score knowledge
        +Score accuracy
        +Score salesmanship
        +Score objectionHandling
        +Score conversationControl
        +Score closing
        +Score compliance
        +Score customerSatisfaction
        +computeOverall() Score
    }

    class ComplianceViolation {
        <<Value Object>>
        +string rule
        +Severity severity
        +string evidence
        +Timestamp occurredAt
    }

    class CoachingNote {
        <<Value Object>>
        +string dimension
        +string observation
        +string suggestion
    }

    Evaluation --> DimensionScores
    Evaluation --> ComplianceViolation
    Evaluation --> CoachingNote
```

---

### 12. Analytics Context

**Responsibility**: Read models, dashboards, reports. CQRS query side.

This context is **read-only** — it consumes events from Conversation, Evaluation, and Agent contexts to build denormalized read models / materialized views.

| Read Model | Source Events | Purpose |
|------------|--------------|---------|
| `AgentPerformanceView` | `EvaluationCompleted`, `ConversationEnded` | Agent KPI dashboard |
| `SentimentTimelineView` | `RecordingProcessed` | Sentiment trends |
| `ConversationSummaryView` | `ConversationEnded` | Call summaries |
| `ComplianceReportView` | `EvaluationCompleted` | Compliance dashboard |
| `LeadScoreView` | `ConversationEnded` | Lead scoring |

---

## Domain Events — Full Registry

| Event | Publisher Context | Subscriber Context(s) | Payload |
|-------|------------------|----------------------|---------|
| `UserRegistered` | Identity | Organization | `userId, email` |
| `RecordingUploaded` | Ingestion | Processing | `recordingId, s3Key, workspaceId` |
| `DocumentUploaded` | Ingestion | Knowledge | `documentId, type, s3Key` |
| `IngestionCompleted` | Ingestion | — | `dataSourceId, stats` |
| `TranscriptGenerated` | Processing | Knowledge, Playbook | `recordingId, transcript` |
| `RecordingProcessed` | Processing | Playbook, Analytics | `recordingId, analysisId` |
| `PatternsExtracted` | Playbook | Prompt | `agentId, patternsSummary` |
| `PlaybookGenerated` | Playbook | Prompt, Agent | `playbookId, agentId, version` |
| `PlaybookActivated` | Playbook | Agent | `playbookId, agentId` |
| `PromptGenerated` | Prompt | Agent | `promptId, agentId, version` |
| `PromptOptimized` | Prompt | Agent | `promptId, newVersion` |
| `PromptActivated` | Prompt | Agent | `promptId, agentId` |
| `AgentPublished` | Agent | Voice, Analytics | `agentId, config` |
| `AgentUnpublished` | Agent | Voice | `agentId` |
| `KnowledgeIndexed` | Knowledge | Agent | `kbId, documentCount` |
| `KnowledgeUpdated` | Knowledge | Agent | `kbId, version` |
| `ConversationStarted` | Conversation | Analytics | `conversationId, agentId` |
| `ConversationEnded` | Conversation | Evaluation, Analytics | `conversationId, messages, duration` |
| `ToolExecuted` | Conversation | Analytics | `conversationId, toolName, result` |
| `EvaluationCompleted` | Evaluation | Analytics, Prompt | `evaluationId, scores` |
| `CustomerCreated` | Conversation | Analytics | `customerId, orgId` |

### Event Infrastructure Contract

```python
@dataclass(frozen=True)
class RecordingUploaded(DomainEvent):
    recording_id: str = ""
    workspace_id: str = ""
    s3_key: str = ""
    format: str = ""
    duration_seconds: float = 0.0

    # Infrastructure config (not domain)
    class Meta:
        exchange = "ingestion"
        routing_key = "recording.uploaded"
        retry_policy = RetryPolicy(max_retries=3, backoff="exponential")
        dead_letter_queue = "dlq.ingestion"
```

---

## Aggregate Invariant Summary

| Aggregate | Key Invariants |
|-----------|---------------|
| **Organization** | Workspace count ≤ plan.maxWorkspaces |
| **Agent** | Cannot publish without active Playbook + Prompt; Tools ≤ plan limit |
| **Playbook** | Must have ≥ 1 ConversationStage; Must have ≥ 1 FallbackBehavior |
| **AgentPrompt** | Token count ≤ LLM context window; Must pass safety scan |
| **KnowledgeBase** | Document count ≤ plan limit; Embedding dim = configured dim |
| **Conversation** | Cannot add messages after ENDED; Turn alternation enforced |
| **Evaluation** | All 10 dimension scores must be present; Overall = weighted avg |
| **VoiceSession** | Cannot barge-in during SILENCE state |
