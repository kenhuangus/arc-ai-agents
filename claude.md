---
version: 1.1
agent: Claude Code
description: >
  Combined configuration and execution guide for Claude Code.
  Includes behavior governance for context engineering and a complete technical roadmap
  for building and operating a real-time coordination system on the Arc Layer-1 blockchain
  with AP2-based payments and settlement mechanisms using Python.
default_roles:
  - Research Assistant
  - Report Writer
required_tools:
  - list_files
  - read_file
  - write_file
  - search_directory
default_memory:
  - lm.txt
  - temp_files/
---

# SECTION 1 — Context Engineering Behavior (for Claude Code)

Follow these operational conventions to manage reasoning and outputs efficiently.

## 1. Offloading
Behavior: Store large outputs externally, summarize inline.
Prompts:
- Summarize key findings from any document in bullet points.
- Extract only relevant sections and provide file paths or URLs.
- Save long outputs to `temp_files/` via `write_file()`, then return a summary and storage path.
Tools: `write_file(path, content)`, `read_file(path)`

## 2. Context Reduction (Pruning)
Behavior: Keep only essential data for the active step.
Prompts:
- Keep responses focused on the current action.
- After sub-tasks, generate short summaries.
- When reporting errors, give a short description and recovery plan, not full tracebacks.
Caution: Do not remove details required later for debugging or audit trails.

## 3. Retrieval (RAG)
Behavior: Retrieve only relevant documentation using reference files.
Prompts:
- Consult `lm.txt` before solving complex problems.
- Use `search_directory(term)` for keyword-based discovery.
Tools: `list_files(directory)`, `read_file(path)`, `search_directory(term)`
`lm.txt` should describe all available docs and datasets with LLM-generated summaries.

## 4. Context Isolation (Multi-Agent Simulation)
Behavior: Separate reasoning tasks into isolated personas.
Roles:
- Research Assistant: Collect, verify, and store data. No final synthesis.
- Report Writer: Summarize findings into structured output.
Prompts:
- Switch roles explicitly: “Act as Research Assistant…” or “Now act as Report Writer…”
Maintain independent temporary context between modes.

## 5. Caching
Behavior: Use Claude API’s implicit caching for continuity.
Prompts:
- Only include essential contextual snippets.
- Let API manage prior memory automatically.

## 6. Operating Principles
When executing:
1. Offload heavy or peripheral data.
2. Prune unnecessary details.
3. Retrieve from on-disk context.
4. Isolate role-based reasoning.
5. Trust built-in cache for prior context.

---

# SECTION 2 — Arc Layer-1 Coordination System Plan

This section defines a comprehensive, actionable plan for a real-time coordination system built on the Arc Layer-1 blockchain.
using Python code, solidity for smart contract, https://github.com/foundry-rs/foundry for smart contract development
## Objective
Design, build, test, and operate a decentralized coordination system enabling autonomous agents to post structured intents, discover counter-intents, and settle matches via verifiable payment credentials using the Agent Payments Protocol (AP2). The goal is a minimal, auditable on-chain footprint that preserves privacy and scalability.

Reference:
[Arc Docs](https://docs.arc.network/arc/tutorials/deploy-on-arc),  
[AP2 Protocol](https://ap2-protocol.org/specification/?utm_source=chatgpt.com)

---

## System Architecture Overview

- **On-chain Layer:**  
  Intent Registry, Matching Escrow, Payment Router, and Dispute/Arbitration contracts form the immutable audit and enforcement core.

- **Off-chain Layer:**  
  Intent Indexer, Matching Engine, AP2 Gateway, and Relayer/Sequencer perform high-frequency operations and verification.

- **Client Interfaces:**  
  WebSocket stream for real-time matching; RESTful API for historical access; SDKs in TypeScript and Python for intent lifecycle management.

---

## Intent and AP2 Design

- An **Intent** is a signed, timestamped JSON object including actor identity, constraints, settlement asset, validity, and AP2 mandate references.  
- Each Intent is hashed, and only the compact hash and metadata are recorded on-chain.  
- The **AP2 Mandate** acts as a Verifiable Digital Credential proving authorization; identifiers and proofs are referenced on-chain while full data stays off-chain.  
- All submissions follow Arc’s policy for compact, private anchors and AP2 authentication flow.

---

## Settlement Modes

**Hybrid Settlement:**  
High throughput, low gas. Matching Engine creates match bundles signed by all parties. Payment verified by AP2 Gateway receipts anchored to Arc.

**Atomic On-Chain Settlement:**  
High assurance, higher cost. Parties pre-fund escrow. Escrow releases funds only upon verified AP2 proof or valid token transfer.

---

## AP2 Integration

- **At Intent Creation:** AP2 Gateway validates attached Mandate for trust, scope, and freshness.
- **At Settlement:** Submitters provide AP2 proof envelopes (off-chain or on-chain) verifying funds or attested value transfer.  
- The AP2 Gateway verifies credentials, supports multiple payment rails, and emits compact proofs anchored back to Arc.

---

## Operational Models

- **Default Mode:** Off-chain Matching Engine for hybrid operations with minimal on-chain footprint.
- **Alternate Mode:** Fully on-chain matching ensuring atomic transparency.
- Support commit-reveal or ZK schemes for private matching.

---

## Security and Governance

### Cryptographic Controls
- Sign all authoritative objects; include nonces and timestamps.  
- Anchor compact commitments; store payloads encrypted off-chain.  

### Attestation Controls
- Enforce AP2 mandate validity and verifier revocation.  

### Economic Controls
- Relayer bonding, anti-spam deposits, and misbehavior slashing.  
- Dispute resolution windows with deterministic arbitration.

[CSA AP2 Security Guide](https://cloudsecurityalliance.org/blog/2025/10/06/secure-use-of-the-agent-payments-protocol-ap2-a-framework-for-trustworthy-ai-driven-transactions?utm_source=chatgpt.com)

---

## Privacy and Data Minimization

Keep full payloads encrypted off-chain. Anchor only hashes and metadata.
For confidential intents, use ZK-based proofs to hide constraints while confirming validity.
Implement mandate revocation and rotation for PII minimization and lawful use tracking.

---

## Testing and Deployment

**Testing Phases:**
1. **Unit:** Smart contracts and APIs  
2. **Integration:** Arc testnet; AP2 sandbox verification  
3. **Adversarial:** Chaos simulations, network partitions  
4. **Audit:** Static and dynamic analysis; formal verification for Escrow and Payment Router.

Establish CI/CD flow per Arc’s deployment guidelines with deterministic artifacts and reproducible test vectors.

---

## Operations and Monitoring

Instrument all components for metrics such as:
- Intent publish latency  
- Match and escrow lock times  
- Verification failure rates

Define SLOs and build monitoring alerts. Maintain incident playbooks for stuck transactions and escrow disputes.

---

## Governance and Upgrade Path

Use conservative, transparent upgrade procedures controlled by multisig with public timelocks.  
Document change proposals and maintain regression gates before every upgrade.  
Transition from project multisig to DAO once verifier certification programs mature.

---

## Repository Structure



