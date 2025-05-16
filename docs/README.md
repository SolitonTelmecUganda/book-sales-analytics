# Book Sales Analytics Architecture Diagrams

This directory contains Mermaid diagrams that illustrate the architecture and data flow of our Book Sales Analytics platform.

## What is Mermaid?

[Mermaid](https://mermaid.js.org/) is a JavaScript-based diagramming and charting tool that renders Markdown-inspired text definitions to create and modify diagrams dynamically. It's supported by many platforms including GitHub, GitLab, and various documentation systems.

## Diagrams in this Directory

1. [Architecture Diagram](architecture-diagram.md) - Complete system architecture
2. [Data Flow Diagram](data-flow-diagram.md) - Data movement through the system
3. [Database Schema](database-schema.md) - Database schema for both transactional and analytical databases

## Viewing the Diagrams

### Option 1: GitHub Rendering (Recommended)

GitHub automatically renders Mermaid diagrams in Markdown files. Simply view the .md files directly on GitHub.

### Option 2: Mermaid Live Editor

1. Go to [Mermaid Live Editor](https://mermaid.live/)
2. Copy the contents of any diagram file (without the markdown backticks)
3. Paste into the editor to view and modify the diagram

### Option 3: VSCode with Mermaid Extension

1. Install the [Mermaid extension for VSCode](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid)
2. Open any of the .md files
3. Use the preview mode to view the rendered diagrams

### Option 4: Include in Documentation

To include these diagrams in HTML documentation, use the following approach:

```html
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({ startOnLoad: true });
</script>

<div class="mermaid">
  <!-- Paste diagram code here -->
</div>
```

## Modifying the Diagrams

1. Open the corresponding .md file
2. Edit the Mermaid syntax between the backticks
3. Use one of the viewing options above to preview your changes
4. Commit the updated file to the repository

## Diagram Syntax Reference

### Flowchart (Architecture & Data Flow Diagrams)

```
flowchart TB  # TB = top to bottom, LR = left to right
    A[Node A] --> B[Node B]
    B --> C{Decision}
    C -->|Yes| D[Result 1]
    C -->|No| E[Result 2]
    
    subgraph Section
        D
        E
    end
```

### Entity Relationship Diagram (Database Schema)

```
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
    CUSTOMER {
        string name
        string email
    }
    ORDER {
        int id
        date created_at
    }
```

For more detailed syntax reference, visit the [Mermaid Documentation](https://mermaid.js.org/syntax/flowchart.html).

## Design Principles

When modifying the diagrams, please follow these principles:

1. **Clarity**: The diagram should be easy to understand at a glance
2. **Consistency**: Use consistent naming and styling
3. **Completeness**: Include all relevant components and connections
4. **Conciseness**: Avoid unnecessary details that clutter the diagram

## Regenerating Diagram Images

If you need static images of these diagrams:

1. Use the Mermaid Live Editor's PNG export feature
2. Place the exported images in the `images` directory
3. Reference them in documentation as needed:
   ```markdown
   ![Architecture Diagram](images/architecture-diagram.png)
   ```