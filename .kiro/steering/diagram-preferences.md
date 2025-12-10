# Diagram Preferences

## Mermaid Over ASCII

When creating diagrams in documentation or code comments, always prefer Mermaid markdown diagrams over ASCII art diagrams.

### Why Mermaid?

- **Maintainable**: Easy to update without manual alignment
- **Readable**: Clean syntax that's easy to understand
- **Portable**: Renders in GitHub, GitLab, VS Code, and most markdown viewers
- **Accessible**: Better screen reader support than ASCII art
- **Version Control**: Meaningful diffs when diagrams change

### Diagram Types

Use appropriate Mermaid diagram types:

| Use Case | Mermaid Type |
|----------|--------------|
| Workflows, processes | `flowchart` or `graph` |
| Sequences, API calls | `sequenceDiagram` |
| State transitions | `stateDiagram-v2` |
| Class relationships | `classDiagram` |
| Entity relationships | `erDiagram` |
| Timelines | `gantt` |
| Architecture | `flowchart` with subgraphs |

### Examples

**Architecture Diagram:**
```mermaid
flowchart TB
    subgraph Frontend
        CF[CloudFront] --> S3[S3 Bucket]
    end
    subgraph API
        APIGW[API Gateway] --> Lambda
    end
    subgraph Data
        Lambda --> DynamoDB
    end
    CF --> APIGW
```

**Sequence Diagram:**
```mermaid
sequenceDiagram
    participant User
    participant API
    participant DRS
    User->>API: Start Execution
    API->>DRS: StartRecovery
    DRS-->>API: Job ID
    API-->>User: Execution Started
```

**State Diagram:**
```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> POLLING
    POLLING --> LAUNCHING
    LAUNCHING --> COMPLETED
    LAUNCHING --> FAILED
    POLLING --> CANCELLED
```

### When ASCII is Acceptable

ASCII diagrams may be used only when:
- Inline in code comments where Mermaid won't render
- Terminal output or CLI help text
- Legacy documentation being incrementally updated
