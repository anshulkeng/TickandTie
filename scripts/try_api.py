"""Task 7: ask the running API a few questions and show the answers, the way the website will.

Start the server first, in another terminal:
    uvicorn tickandtie.api.app:create_app --factory --no-access-log --port 8000
then run:
    python -m scripts.try_api"""
import time

import httpx

BASE = "http://127.0.0.1:8000"
QUESTIONS = [
    "What was Apple's revenue in fiscal 2025?",
    "What changed in Pfizer's risk factors?",
    "Should I buy NVIDIA stock?",
]


def main():
    with httpx.Client(base_url=BASE, timeout=10) as client:
        print("status:", client.get("/api/status").json())
        print("health:", client.get("/api/health").json())
        for question in QUESTIONS:
            started = time.perf_counter()
            job = client.post("/api/questions", json={"question": question}).json()
            while True:
                reply = client.get(f"/api/questions/{job['id']}").json()
                if reply["status"] in ("done", "failed"):
                    break
                time.sleep(1)
            result = reply.get("result") or {}
            text = result.get("answer") or result.get("refusal") or reply.get("error") or ""
            print(f"\nQ: {question}\n   {reply['status']}, mode {result.get('mode')}, "
                  f"{time.perf_counter() - started:.1f}s\n   {text[:300]}")


if __name__ == "__main__":
    main()