import json
from .ollama_client import generate_text

SYSTEM_PROMPT = """
You are an expert Senior Software Architect and Technical Writer.
Your task is to analyze the provided "Evidence Package" of a software repository and generate a comprehensive Technical Documentation.
You MUST output the result in strict Markdown format.
Do NOT invent features that are not present. If you are unsure, state that it is "inferred" or "not found".
Use a professional, technical tone.
"""

USER_PROMPT_TEMPLATE = """
Here is the Evidence Package for the repository:
{evidence_json}

Please generate the following documentation:

# 1. Functional Requirements
List the main features and functionalities based on the README and code structure.

# 2. Non-Functional Requirements
Infer security, performance, scalability, and observability requirements based on the libraries and configurations found.

# 3. Architecture (C4 & Principles)
- Describe the likely Architecture (MVC, Layered, Microservices).
- Provide a Mermaid.js C4 Context diagram in a code block marked with `mermaid`.
  Example:
  ```mermaid
  C4Context
    title System Context diagram for System
    ...
  ```
- Provide a Mermaid.js C4 Container diagram in a code block marked with `mermaid`.

# 4. Stack & Technologies
List languages, frameworks, databases, and build tools detected.

# 5. Project Summary
A brief executive summary of what the project does.

"""

async def generate_documentation(evidence: dict) -> str:
    """
    Orchestrates the LLM generation.
    """
    evidence_str = json.dumps(evidence, indent=2)
    
    # We might need to truncate if too large, but for now passing it all
    # A real world app would check token counts.
    
    prompt = USER_PROMPT_TEMPLATE.format(evidence_json=evidence_str)
    
    doc_markdown = await generate_text(prompt, SYSTEM_PROMPT)
    
    return doc_markdown
