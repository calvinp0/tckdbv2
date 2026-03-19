---
name: record-decision
description: "Record the thought process and scientific justification behind a design or implementation decision, structured for future use in writing a scientific article."
user-invocable: true
allowed-tools: ["Read", "Write", "Edit", "Glob", "Bash", "Grep"]
---

Record the scientific reasoning, trade-offs, and justification behind a design or implementation decision. The output is structured so it can later feed into a methods section, supplementary material, or design-rationale appendix of a scientific paper.

## Invocation

The user will invoke this skill when a decision has just been made (or is being made) that involves meaningful scientific, algorithmic, or architectural reasoning. The user may provide a topic as an argument (e.g., `/record-decision conformer deduplication strategy`), or you may need to infer it from the current conversation context.

## Steps

1. **Gather context**: Review the current conversation for the decision being discussed. If the conversation doesn't contain enough context, ask the user concise clarifying questions. Focus on:
   - What problem or requirement prompted this decision
   - What alternatives were considered and why they were rejected
   - The scientific or technical basis for the chosen approach
   - Any relevant literature, prior art, or domain conventions
   - Known limitations or caveats of the chosen approach
   - How this connects to the broader goals of TCKDB

2. **Draft the record**: Write a structured decision record using the template below. Show the draft to the user for review before saving.

3. **Save the record**: Write the final record to `docs/decisions/NNNN-<slug>.md`, where `NNNN` is the next sequential number (check existing files in `docs/decisions/`). Create the `docs/decisions/` directory if it doesn't exist.

4. **Update the index**: Append a one-line entry to `docs/decisions/INDEX.md` (create it if missing). Format: `| NNNN | Title | YYYY-MM-DD | Status |`.

## Record Template

```markdown
# DR-NNNN: <Title>

**Date:** YYYY-MM-DD
**Status:** Accepted | Proposed | Superseded by DR-XXXX
**Authors:** <who participated in the decision>

## Context

_What situation or requirement prompted this decision? What is the scientific or engineering problem being addressed? Include references to relevant literature, standards, or domain conventions where applicable._

## Considered Alternatives

### Alternative A: <name>
- **Description:** ...
- **Pros:** ...
- **Cons / why rejected:** ...

### Alternative B: <name>
- **Description:** ...
- **Pros:** ...
- **Cons / why rejected:** ...

_(repeat as needed)_

## Decision

_State the chosen approach clearly and concisely._

## Scientific Justification

_Why is this the right choice from a scientific perspective? Reference domain knowledge, computational chemistry conventions, thermodynamic/kinetic theory, data integrity requirements, or relevant literature. This section should be written in a style suitable for adaptation into a methods or design-rationale section of a paper._

## Implementation Notes

_How does this decision manifest in the codebase? Reference specific modules, tables, schemas, or workflows affected. Keep brief — the code is the authoritative source._

## Limitations & Future Work

_Known limitations of this approach. Conditions under which this decision should be revisited. Potential improvements deferred for now._

## References

_Citations, DOIs, URLs, or pointers to related decision records._
```

## Guidelines

- **Write for a scientific audience.** Assume the reader is a computational chemist or chemical engineer who understands the domain but not necessarily this codebase.
- **Be precise about trade-offs.** Vague statements like "it's better" are not useful. Quantify where possible; cite domain conventions where relevant.
- **Keep implementation details minimal.** The record should age well — focus on the *why* not the *how*. Code changes; reasoning endures.
- **Link to related records.** If this decision builds on or supersedes a previous one, cross-reference it.
- **Status tracking.** New records start as "Accepted" (if the decision is final) or "Proposed" (if still under discussion). When a decision is later replaced, update the old record's status to "Superseded by DR-XXXX".
