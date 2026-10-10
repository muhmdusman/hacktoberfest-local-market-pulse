export type SourceName = "reddit" | "web";
export type RunMode = "cached" | "live";
export type RunStatus = "queued" | "running" | "done" | "failed";
export type RunStage =
  | "collecting"
  | "analyzing"
  | "trending"
  | "reporting"
  | "done";

export interface OptionsResponse {
  business_types: string[];
  default_city: string;
  areas: string[];
  default_competitors: string[];
  sources: SourceName[];
  modes: RunMode[];
  limits: {
    max_urls: number;
    max_limit: number;
  };
}

export interface ModelDefinition {
  id: string;
  provider: string;
  nominal_size: string;
  params_b: number;
  license: string;
  tier: string;
  open_weight: boolean;
  eligible: boolean;
}

export interface ModelsResponse {
  max_params_rule: string;
  provider: string;
  tiers: Record<
    string,
    {
      id: string;
      strategy: string;
    }
  >;
  models: ModelDefinition[];
}

export type SourceBackendStatus =
  | "ok"
  | "missing"
  | "broken"
  | "timeout"
  | "error";

export interface SourceStatusResponse {
  sources: Array<{
    source: SourceName;
    active: string;
    backends: Array<{
      name: string;
      status: SourceBackendStatus;
      hint: string;
    }>;
  }>;
}

export interface CreateRunRequest {
  business: string;
  city: string;
  areas: string[];
  competitors: string[];
  sources: SourceName[];
  mode: RunMode;
  urls: string[];
  limit: number;
  provider: string | null;
  votes: number;
}

export interface CreateRunResponse {
  run_id: string;
  status: RunStatus;
}

export interface RunStatusResponse {
  run_id: string;
  status: RunStatus;
  stage: RunStage;
  progress: {
    done: number;
    total: number;
  };
  counts: {
    collected: number;
    deduped: number;
    kept: number;
    filtered: number;
    escalated: number;
    failed: number;
  };
  messages: Array<{
    level: "info" | "warn" | "error";
    text: string;
  }>;
  created_at: string;
  finished_at: string | null;
  error: {
    message: string;
  } | null;
}

export interface TermSignal {
  term: string;
  count: number;
  recent: number;
  baseline: number;
  lift: number;
  z: number;
  score: number;
}

export interface ResultsResponse {
  run_id: string;
  provenance: {
    synthetic: boolean;
    mock: boolean;
    sources_used: Record<string, string>;
    provider: string;
    models: string[];
    generated_at: string;
  };
  overview: {
    posts_analysed: number;
    relevant_pct: number;
    sentiment: {
      pos: number;
      neg: number;
      neutral: number;
      mixed: number;
    };
    top_rising: {
      term: string;
      lift: number;
    };
    escalation_rate: number;
    top_actions: string[];
  };
  keywords: Array<
    TermSignal & {
      example: {
        record_id: string;
        url: string;
      };
    }
  >;
  voice: {
    pain_points: TermSignal[];
    requests: TermSignal[];
    questions: Array<{
      record_id: string;
      source: SourceName;
      text: string;
      url: string;
    }>;
  };
  competitors: Array<{
    name: string;
    mentions: number;
    pos: number;
    neg: number;
    neutral: number;
    mixed: number;
    negativity: number;
    top_complaints: string[];
  }>;
  gaps: Array<{
    theme: string;
    demand: number;
    negativity: number;
    gap: number;
  }>;
  content: {
    briefs: Array<{
      title: string;
      target_keyword: string;
      outline: string[];
      competitor_weakness: string;
    }>;
    faqs: Array<{
      question: string;
      source_record_ids: string[];
    }>;
    faq_jsonld: string;
  };
  threads: Array<{
    record_id: string;
    title: string;
    subreddit: string;
    url: string;
    created_at: string;
    question: string;
    relevance: number;
  }>;
  participation_note: string;
  metrics: {
    calls_by_tier: {
      small: number;
      large: number;
    };
    cache_hits: number;
    escalations: number;
    escalation_rate: number;
    repairs: number;
    schema_failures: number;
    schema_failure_rate: number;
    filtered: number;
    failed: number;
    tokens: {
      prompt: number;
      completion: number;
    };
    latency_ms: {
      p50: number;
      p95: number;
    };
  };
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
  };
}
