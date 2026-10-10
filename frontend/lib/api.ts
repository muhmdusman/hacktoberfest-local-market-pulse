import {
  MOCK_MODELS,
  MOCK_OPTIONS,
  MOCK_RESULTS,
  MOCK_SOURCE_STATUS,
} from "./mock-data";
import type {
  ApiErrorResponse,
  CreateRunRequest,
  CreateRunResponse,
  ModelsResponse,
  OptionsResponse,
  RunStage,
  RunStatusResponse,
  SourceStatusResponse,
  ResultsResponse,
} from "./types";

const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
const configuredMocks = process.env.NEXT_PUBLIC_USE_MOCKS;

export const API_BASE_URL = (
  configuredBaseUrl || "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

export const USE_MOCKS_BY_DEFAULT =
  configuredMocks === undefined || configuredMocks.toLowerCase() !== "false";

export interface ApiRequestOptions {
  forceMock?: boolean;
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

let mockStartedAt = Date.now();

function delay(milliseconds: number) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

export function isUsingMocks(forceMock = false) {
  if (forceMock) return true;

  if (typeof window !== "undefined") {
    const query = new URLSearchParams(window.location.search);
    if (query.get("mock") === "1") return true;
  }

  return USE_MOCKS_BY_DEFAULT;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiRequestError(
      `Could not reach the API at ${API_BASE_URL}. Check that the backend is running.`,
    );
  }

  if (!response.ok) {
    const payload = (await response
      .json()
      .catch(() => null)) as ApiErrorResponse | null;
    throw new ApiRequestError(
      payload?.error?.message || `API request failed (${response.status}).`,
      response.status,
    );
  }

  return (await response.json()) as T;
}

function getMockRunStatus(): RunStatusResponse {
  const elapsed = Date.now() - mockStartedAt;
  let stage: RunStage = "collecting";
  let done = 8;
  let counts = {
    collected: 18,
    deduped: 17,
    kept: 0,
    filtered: 0,
    escalated: 0,
    failed: 0,
  };

  if (elapsed >= 500 && elapsed < 1_000) {
    stage = "analyzing";
    done = 34;
    counts = {
      collected: 81,
      deduped: 79,
      kept: 34,
      filtered: 7,
      escalated: 4,
      failed: 0,
    };
  } else if (elapsed >= 1_000 && elapsed < 1_500) {
    stage = "trending";
    done = 59;
    counts = {
      collected: 81,
      deduped: 79,
      kept: 68,
      filtered: 11,
      escalated: 9,
      failed: 0,
    };
  } else if (elapsed >= 1_500 && elapsed < 2_000) {
    stage = "reporting";
    done = 68;
    counts = {
      collected: 81,
      deduped: 79,
      kept: 68,
      filtered: 11,
      escalated: 9,
      failed: 0,
    };
  } else if (elapsed >= 2_000) {
    stage = "done";
    done = 68;
    counts = {
      collected: 81,
      deduped: 79,
      kept: 68,
      filtered: 11,
      escalated: 9,
      failed: 0,
    };
  }

  const finished = stage === "done";

  return {
    run_id: "demo_islamabad_cafes",
    status: finished ? "done" : "running",
    stage,
    progress: { done, total: 68 },
    counts,
    messages: [
      {
        level: "info",
        text: "Using a saved synthetic Reddit and web snapshot for this demo.",
      },
    ],
    created_at: new Date(mockStartedAt).toISOString(),
    finished_at: finished ? new Date().toISOString() : null,
    error: null,
  };
}

export async function getOptions(
  options?: ApiRequestOptions,
): Promise<OptionsResponse> {
  if (isUsingMocks(options?.forceMock)) {
    await delay(80);
    return MOCK_OPTIONS;
  }
  return request<OptionsResponse>("/options");
}

export async function getModels(
  options?: ApiRequestOptions,
): Promise<ModelsResponse> {
  if (isUsingMocks(options?.forceMock)) {
    await delay(80);
    return MOCK_MODELS;
  }
  return request<ModelsResponse>("/models");
}

export async function getSourcesStatus(
  options?: ApiRequestOptions,
): Promise<SourceStatusResponse> {
  if (isUsingMocks(options?.forceMock)) {
    await delay(80);
    return MOCK_SOURCE_STATUS;
  }
  return request<SourceStatusResponse>("/sources/status");
}

export async function createRun(
  payload: CreateRunRequest,
  options?: ApiRequestOptions,
): Promise<CreateRunResponse> {
  if (isUsingMocks(options?.forceMock)) {
    mockStartedAt = Date.now();
    await delay(120);
    return { run_id: "demo_islamabad_cafes", status: "queued" };
  }
  return request<CreateRunResponse>("/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getRun(
  runId: string,
  options?: ApiRequestOptions,
): Promise<RunStatusResponse> {
  if (isUsingMocks(options?.forceMock)) {
    await delay(80);
    return getMockRunStatus();
  }
  return request<RunStatusResponse>(`/runs/${encodeURIComponent(runId)}`);
}

export async function getRunResults(
  runId: string,
  options?: ApiRequestOptions,
): Promise<ResultsResponse> {
  if (isUsingMocks(options?.forceMock)) {
    await delay(140);
    return MOCK_RESULTS;
  }
  return request<ResultsResponse>(
    `/runs/${encodeURIComponent(runId)}/results`,
  );
}
