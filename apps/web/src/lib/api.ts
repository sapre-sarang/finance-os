import type { z } from "zod";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly problems: string[],
  ) {
    super(problems.join("; "));
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function describeProblems(body: unknown, status: number): string[] {
  if (isRecord(body)) {
    const detail = body["detail"];
    if (typeof detail === "string") return [detail];
    if (isRecord(detail) && Array.isArray(detail["problems"])) {
      return detail["problems"].filter((p): p is string => typeof p === "string");
    }
    if (Array.isArray(detail)) {
      return detail.map((item) => {
        if (!isRecord(item)) return "Invalid input";
        const where = Array.isArray(item["loc"]) ? item["loc"].slice(1).join(".") : "";
        const message = typeof item["msg"] === "string" ? item["msg"] : "Invalid input";
        return where ? `${where}: ${message}` : message;
      });
    }
  }
  return [`Request failed (${status})`];
}

async function send(path: string, init: RequestInit): Promise<Response> {
  try {
    return await fetch(`/api${path}`, { credentials: "same-origin", ...init });
  } catch {
    throw new ApiError(0, ["Cannot reach the server. Check that the API is running."]);
  }
}

async function parse(response: Response): Promise<unknown> {
  if (response.ok) return response.status === 204 ? undefined : await response.json();
  const body: unknown = await response.json().catch(() => null);
  throw new ApiError(response.status, describeProblems(body, response.status));
}

export async function get<S extends z.ZodTypeAny>(path: string, schema: S): Promise<z.infer<S>> {
  return schema.parse(await parse(await send(path, {})));
}

export async function sendJson<S extends z.ZodTypeAny>(
  method: "POST" | "PUT",
  path: string,
  body: unknown,
  schema: S,
): Promise<z.infer<S>> {
  const response = await send(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return schema.parse(await parse(response));
}

export async function sendForm<S extends z.ZodTypeAny>(
  path: string,
  form: FormData,
  schema: S,
): Promise<z.infer<S>> {
  return schema.parse(await parse(await send(path, { method: "POST", body: form })));
}

export async function remove(path: string): Promise<void> {
  await parse(await send(path, { method: "DELETE" }));
}

export async function postNoContent(path: string): Promise<void> {
  await parse(await send(path, { method: "POST" }));
}
