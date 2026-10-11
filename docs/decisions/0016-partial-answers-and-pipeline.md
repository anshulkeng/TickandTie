# 0016: Keep verified sentences, remove failed ones, and say so

Status: Accepted, October 2026

## Context
After one rewrite, a draft can still contain a sentence the Verifier rejects. In the first live runs, NVIDIA's six-sentence answer had one mis-cited figure. Refusing the whole answer would throw away five verified sentences.

## Decision
- The pipeline is a LangGraph graph: route, gather, write, verify, one rewrite, finalise.
- If the final draft still fails, each sentence is checked on its own. Verified sentences are kept, the rest are removed, and the answer says how many were removed. If nothing verified remains apart from a "Not covered:" sentence, the question is refused.
- Removed sentences and their reasons go to the trace, never to the user, because they contain unverified figures.
- Figures that are not reported become known gaps, which the Writer must state in its "Not covered:" sentence.
- When the chosen sections return fewer than two passages, all sections are searched and a note says so. JPMorgan's Item 7A, for example, only points to Item 7.
- Every run writes a trace (plan, evidence, drafts, Verifier results, timings) to `data/traces`.

## Alternatives considered
- Refuse the whole answer: strict, but wastes verified content.
- Let code repair citations, for example by moving a figure to the passage that contains it: this would hide the model's mistakes instead of measuring them.
- More rewrites: slower, and a 7B model gains little from a third attempt.

## Consequences
- No unverified sentence reaches the user.
- A partial answer can read less smoothly, for example an "Additionally" after a removed sentence.
- Trace files grow with use. They live in `data/` and are not committed.