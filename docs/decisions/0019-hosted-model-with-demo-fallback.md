# 0019: Hosted model with a spending cap, and demo mode as the fallback

Status: Accepted, October 2026. Updates decision 0001 (free, local model stack) for the public website only.

## Context
The public website needs the Router and Writer model online. Free servers cannot run a 7B model at a usable speed: Oracle's Always Free Arm allowance was halved to 2 OCPUs and 12 GB in 2026 and is often unavailable, and free Hugging Face compute Spaces are restricted. Serverless GPUs (Modal, $30 monthly credits) are cheap but wake slowly after idle periods, which is when a recruiter is likely to visit.

## Decision
- The website uses the same model family, Qwen2.5 7B Instruct, through OpenRouter at temperature 0. In October 2026 it was listed at about $0.10 per million input tokens and $0.20 per million output tokens, roughly $0.0006 per question.
- The API key has a hard spending limit, and the website applies its own rate limits.
- When the hosted model is unavailable or the limit is reached, the website switches to demo mode and says so: the risk diff stays live (no model needed), and other answers come from the evaluated questions, labelled as pre-computed.
- Local Ollama remains the default for development and evaluation. One module, `tickandtie/llm.py`, chooses the backend.
- Budget: about 1 to 5 pounds a month for the model, plus the domain.

## Deployment check, pass mark fixed before running
The evaluation was run on the local, compressed model; the hosted model is full precision. All 81 questions are run once on the hosted model (`eval/results/system_hosted.jsonl`), as a deployment check rather than a fresh result. It passes if: 0 wrong figures, at least 46 of 48 numeric questions correct, 10 of 10 should-refuse questions declined, and 3 of 3 tricky questions passed. Narrative refusals are reported but not part of the pass mark.

## Alternatives considered
- Our own model on a serverless GPU: a stronger infrastructure story, but slow first answers and more work. It can be added later.
- A free CPU server: minutes per answer.
- Demo mode only: free, but no live answers.

## Consequences
- Questions are sent to a third-party API. They are about public filings, so this is acceptable; the privacy policy will say so.
- Hosted answers can differ from the evaluated local ones, which is why the deployment check exists.
- A spending limit can stop live answers; demo mode keeps the site useful and honest when that happens.