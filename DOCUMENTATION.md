# Smart Financial Coach

## Agent-Oriented Architecture Specification

### Version

v1.0

---

## 1. Problem Statement

Modern AI-powered applications increasingly rely on Large Language Models (LLMs) to generate insights, explanations, and recommendations. However, integrating LLMs safely into decision-adjacent systems (e.g. finance, security, risk analysis) presents several challenges:

* LLM outputs are probabilistic and may hallucinate
* External APIs introduce availability, rate-limit, and security risks
* Public, runnable codebases must not embed secrets
* Systems must degrade gracefully when AI capabilities are unavailable

This project demonstrates how to design a **secure, agent-based orchestration system** that integrates LLMs responsibly while keeping deterministic logic, validation, and trust boundaries explicit.

The financial domain is used as a **representative example**, not as the core focus.

---

## 2. Design Goals

### Primary Goals

* Demonstrate **agent orchestration** rather than feature breadth
* Integrate LLMs in a **capability-gated and secure** manner
* Ensure the system is **public, runnable, and secret-free**
* Show **graceful degradation** when AI capabilities are unavailable
* Emphasize **trust, validation, and error handling**

### Non-Goals (Explicitly Out of Scope)

* User accounts, authentication, or persistence
* Real financial data ingestion or banking APIs
* Production-grade databases or RAG infrastructure
* Prescriptive financial advice or automated actions

---

## 3. High-Level Architecture Overview

The system is structured as a **set of independently degradable agents** coordinated by a central orchestrator.

```
┌──────────────────────┐
│  Agent Orchestrator  │
└─────────┬────────────┘
          │
 ┌────────┼───────────────┐
 │        │               │
 ▼        ▼               ▼
Rule   Education       Validation
Agent    Agent           Agent
 │        │               │
 └────────┼──────┬────────┘
          ▼      ▼
       LLM Augmentation
        (Optional)
```

Key architectural principle:

> **No single agent is required for system execution.
> All agents degrade independently based on capability availability.**

---

## 4. Agent Responsibilities

### 4.1 Rule Agent

* Performs deterministic financial risk analysis
* Uses a small, hardcoded ruleset (intentional for scope control)
* Produces structured, explainable outputs

**Key Properties**

* Fully deterministic
* Always auditable
* LLM may *augment explanations*, but **never override rule outcomes**

Example Output:

```json
{
  "dimension": "Savings",
  "risk_level": "high",
  "reason": "Savings rate below 10%"
}
```

---

### 4.2 Education Agent

* Provides contextual financial education related to detected risks
* Uses a static, hardcoded knowledge base in v1

**Design Rationale**
Hardcoded education content is an intentional placeholder to demonstrate:

* Agent boundaries
* Interface-based extensibility
* Future replacement by RAG / vector databases

The Education Agent may optionally use LLMs to:

* Paraphrase
* Contextualize
* Adjust tone

It **must not introduce new factual claims**.

---

### 4.3 LLM Augmentation Layer

LLMs are treated as **optional capability providers**, not as authoritative decision-makers.

LLMs may be used to:

* Generate summaries
* Rephrase education content
* Produce reflective (non-prescriptive) coaching questions

LLMs are explicitly prohibited from:

* Making financial recommendations
* Introducing external knowledge
* Producing actionable instructions

---

### 4.4 Validation Agent

Any LLM-generated output passes through a validation step.

Validation checks include:

* Presence of prohibited advice language
* Hallucinated facts outside provided context
* Structural integrity of responses

Validation may be:

* Rule-based (primary)
* LLM-assisted (optional, secondary)

Invalid outputs trigger retries or graceful fallback.

---

## 5. Capability Gating & Degradation Model

Capabilities are enabled dynamically based on:

* Environment variables
* Runtime availability
* Provider health

Example capability flags:

```json
{
  "llm": true,
  "education": true,
  "retry": true,
  "fallback": true
}
```

Degradation behavior:

* If LLM unavailable → deterministic + static output
* If validation fails → retry with backoff
* If retries exhausted → best-effort output or structured error

This ensures the system **always runs**, even with zero AI access.

---

## 6. LLM Provider Strategy

The system supports **pluggable LLM providers** via a shared interface.

```python
class LLMProvider:
    def generate(prompt) -> str
```

Supported providers (v1):

* OpenAI (primary implementation)
* Anthropic / Gemini (stubs or fallback-ready)

Provider selection supports:

* Ordered fallback
* Runtime failure detection
* Configurable retry policies

---

## 7. Retry, Backoff, and Fallback

LLM calls are wrapped with:

* Exponential backoff (1s → 2s → 4s)
* Maximum retry limits (configurable)
* Provider-level fallback

Failure modes are:

* Logged
* Reported via structured error messages
* Never crash the system silently

---

## 8. API Design

The system exposes a single agent-oriented API.

### POST `/agent/run`

```json
{
  "input": {
    "monthly_income": 8000,
    "monthly_expenses": 5500,
    "current_savings": 15000,
    "risk_tolerance": "medium"
  },
  "capabilities": {
    "llm": true,
    "retry": true,
    "fallback": true
  },
  "llm_config": {
    "providers": ["openai", "anthropic", "gemini"],
    "max_retries": 3
  }
}
```

Response:

```json
{
  "analysis": {...},
  "education": {...},
  "generation": "...",
  "validation": {...},
  "errors": []
}
```

---

## 9. Security & Trust Considerations

* No API keys are stored or committed
* All secrets are injected via environment variables
* Public repository is safe to clone and run
* Deterministic logic remains independent of LLMs
* LLM outputs are validated and never blindly trusted

---

## 10. Future Extensions (Not Implemented)

* Replace static education with RAG (e.g. Weaviate)
* Persist agent outputs for longitudinal analysis
* Add multiple domain-specific agent pipelines
* Introduce model-based evaluators

---

## 11. Summary

This project focuses on **how to safely orchestrate AI agents**, not on maximizing application features.
It demonstrates a production-relevant pattern for integrating LLMs into systems that require trust, explainability, and resilience—principles central to modern security and platform engineering.

---

## 12. Agent Tooling & Capability Policy

### 12.1 Design Principle

Agents in this system do **not** have unrestricted tool access.

All tool usage follows three principles:

1. **Explicit Invocation** – tools are called only by the orchestrator, not autonomously by agents
2. **Capability Gating** – tool access depends on runtime configuration and availability
3. **Least Privilege** – agents receive only the minimum context required for their task

This design prevents uncontrolled agent behavior and aligns with security-first system design.

---

### 12.2 Supported Tool Categories (v1)

In the current implementation, agents may access the following tool categories:

#### 1. Deterministic Computation Tools

* Rule evaluation logic
* Static education lookup
* Input validation utilities

These tools are always safe, deterministic, and side-effect free.

---

#### 2. LLM Generation Tools (Optional)

LLM providers are treated as **external, untrusted services**.

LLMs may be used **only** for:

* Natural language summarization
* Educational paraphrasing
* Reflective (non-prescriptive) coaching questions

LLMs are explicitly **not allowed** to:

* Execute code
* Access external data sources
* Perform financial calculations
* Make decisions or recommendations

---

#### 3. Validation Tools

Validation tools may include:

* Rule-based validators
* Secondary LLM validators (optional)

Validation tools operate **after generation** and cannot modify upstream deterministic outputs.

---

### 12.3 Explicitly Disallowed Tools

To maintain a clear trust boundary, the following tools are **intentionally excluded** in v1:

* External web search or browsing
* Database write access
* File system mutation
* Network calls beyond configured LLM providers
* Autonomous tool selection by agents

This ensures that agents cannot introduce unverified information or side effects.

---

### 12.4 Orchestrator-Mediated Tool Access

Agents do not directly invoke tools.

Instead, the **Agent Orchestrator**:

* Determines which tools are available
* Injects tool outputs as immutable context
* Enforces execution order and retries
* Handles failures and fallbacks

This separation ensures that agents remain **pure reasoning components**, while the orchestrator enforces system policy.

---

### 12.5 Future Extensions (Not Implemented)

Future versions may introduce additional tools, such as:

* Retrieval tools backed by vector databases (RAG)
* Persistent storage adapters
* Domain-specific calculators

All future tools would follow the same capability-gated, orchestrator-controlled model demonstrated in this project.

