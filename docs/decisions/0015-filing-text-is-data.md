# 0015: Filing text is data, never instructions

Status: Accepted, October 2026

## Context
Passages come from documents written by other people. Text inside one could try to steer the model, for example "ignore previous instructions".

## Decision
- Passages sit inside an evidence block, and any closing tag inside a passage is removed, so a passage cannot end the block early.
- The Writer's rules state that passages are quoted data and that instructions inside them must be ignored.
- The Verifier then checks the answer no matter what the model was told, so an injected instruction cannot get an unsupported number or a fake citation past it.

## Alternatives considered
- Filtering suspicious phrases: an endless list that is easy to get around.

## Consequences
- The protection has a soft layer (prompt rules) and a hard layer (the Verifier, for numbers and citations).
- An injected instruction could still change the wording or emphasis of a narrative answer. That is measured by the evaluation in Task 5.
- A unit test checks that a passage cannot close the evidence block.