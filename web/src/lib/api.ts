/** The Tick & Tie API (decision 0020): submit a question, then check back for the answer. */
import { messages } from "@/content/copy";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type Result = {
  answer: string | null;
  refusal: string | null;
  sources: Record<string, string>;
  periods: string[];
  notes: string[];
  removed: number;
  seconds: number;
  mode: "live" | "demo";
  saved: boolean;
  suggestions?: string[];
};

export type Job = {
  id: string;
  status: "queued" | "running" | "done" | "failed";
  question: string;
  position?: number;
  result?: Result;
  error?: string;
};

export type Status = { mode: "live" | "demo"; reason?: string; retry_after?: number };

type ErrorBody = { error?: { code?: string; message?: string } };

export class ApiError extends Error {
  status: number;
  code: string;
  retryAfter?: number;

  constructor(status: number, code: string, message: string, retryAfter?: number) {
    super(message);
    this.status = status;
    this.code = code;
    this.retryAfter = retryAfter;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(0, "unreachable", messages.unreachable);
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const error = (body as ErrorBody | null)?.error;
    const retryAfter = Number(response.headers.get("Retry-After")) || undefined;
    throw new ApiError(response.status, error?.code ?? "error", error?.message ?? messages.unexpected, retryAfter);
  }
  return body as T;
}

export function submitQuestion(question: string) {
  return request<{ id: string; status: string; position: number | null }>("/api/questions", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export function getJob(id: string) {
  return request<Job>(`/api/questions/${encodeURIComponent(id)}`);
}

export function getStatus() {
  return request<Status>("/api/status");
}