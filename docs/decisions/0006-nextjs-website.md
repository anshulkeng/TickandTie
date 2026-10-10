# 0006: Next.js for the website, not Streamlit

Status: Accepted, October 2026

## Context
The site must not look generated. It has strict design rules, and it needs a favicon, a custom domain, and Privacy Policy and Terms pages.

## Decision
Build the website in Next.js with Tailwind CSS, calling the FastAPI backend.

## Alternatives considered
- Streamlit: fastest to build, but it shows its own branding and default look and gives little control over layout.

## Consequences
- More frontend work in Task 8.
- Same stack as my portfolio site.
- The Python backend stays separate, behind an API.