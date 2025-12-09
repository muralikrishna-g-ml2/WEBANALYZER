# Mermaid Test

## Simple Diagram

```mermaid
graph LR
    A[Start] --> B[Process]
    B --> C[End]
```

## System Architecture (Simplified)

```mermaid
graph TB
    USER[User] --> HOST[Host Agent]
    HOST --> BROWSER[Browser MCP]
    HOST --> FS[File System MCP]
    
    style HOST fill:#4CAF50,color:#fff
    style BROWSER fill:#2196F3,color:#fff
    style FS fill:#FF9800,color:#fff
```

If you can see diagrams above, Mermaid is working! If not, your markdown preview may not support Mermaid.

**To enable Mermaid in VS Code:**
1. Install "Markdown Preview Mermaid Support" extension
2. Or use "Markdown Preview Enhanced" extension

**To view on GitHub:**
- GitHub natively supports Mermaid in markdown files
- Just push and view on GitHub.com
