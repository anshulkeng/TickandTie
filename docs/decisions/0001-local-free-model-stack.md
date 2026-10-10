# 0001: Free, local model stack

Status: Accepted, October 2026

## Context
The budget is zero, and answers have to be reproducible. Paid APIs charge per question and can change behaviour without notice when the provider updates a model.

## Decision
Run language models locally through Ollama: qwen2.5:7b writes answers and llama3.2:3b grades them during evaluation. Embeddings use BAAI/bge-small-en-v1.5 on the CPU.

## Alternatives considered
- Hosted APIs (including free tiers): better quality, but cost or rate limits, and results drift as providers update their models.
- A larger local model: does not fit well on a 4 GB GPU.

## Consequences
- Nothing leaves my machine, and runs repeat at temperature 0.
- Quality and speed are limited by a 4 GB GTX 1650. Both are measured in Task 5.
- Hosting a 7B model publicly for free is hard. This is an open question for Task 9.
- The judge comes from a different model family than the generator, so the system does not grade its own work.