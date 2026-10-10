import type {
  ModelsResponse,
  OptionsResponse,
  ResultsResponse,
  SourceStatusResponse,
} from "./types";

export const MOCK_OPTIONS: OptionsResponse = {
  business_types: ["cafe", "restaurant", "gym", "salon", "other"],
  default_city: "Islamabad",
  areas: [
    "F-6",
    "F-7",
    "F-8",
    "F-10",
    "F-11",
    "G-9",
    "G-11",
    "E-7",
    "Blue Area",
    "DHA",
    "Bahria",
  ],
  default_competitors: [
    "Margalla Mug House",
    "Cedar & Steam",
    "Moonlit Roastery",
  ],
  sources: ["reddit", "web"],
  modes: ["cached", "live"],
  limits: { max_urls: 10, max_limit: 200 },
};

export const MOCK_MODELS: ModelsResponse = {
  max_params_rule: "Open-weight models in the ≤8B class",
  provider: "Ollama via LiteLLM",
  tiers: {
    small: {
      id: "qwen2.5:7b-instruct",
      strategy: "Fast extraction for clear English posts",
    },
    large: {
      id: "qwen2.5:7b-instruct",
      strategy: "Richer prompt and voting for ambiguous posts",
    },
  },
  models: [
    {
      id: "qwen2.5:7b-instruct",
      provider: "Ollama via LiteLLM",
      nominal_size: "7B",
      params_b: 7.62,
      license: "Apache-2.0",
      tier: "small|large",
      open_weight: true,
      eligible: true,
    },
  ],
};

export const MOCK_SOURCE_STATUS: SourceStatusResponse = {
  sources: [
    {
      source: "reddit",
      active: "snapshot",
      backends: [
        {
          name: "snapshot",
          status: "ok",
          hint: "Saved synthetic demo evidence",
        },
      ],
    },
    {
      source: "web",
      active: "snapshot",
      backends: [
        {
          name: "snapshot",
          status: "ok",
          hint: "Saved synthetic demo evidence",
        },
      ],
    },
  ],
};

export const MOCK_RESULTS: ResultsResponse = {
  run_id: "demo_islamabad_cafes",
  provenance: {
    synthetic: true,
    mock: true,
    sources_used: { reddit: "snapshot", web: "snapshot" },
    provider: "Ollama via LiteLLM",
    models: ["qwen2.5:7b-instruct"],
    generated_at: "2025-10-12T14:22:00Z",
  },
  overview: {
    posts_analysed: 68,
    relevant_pct: 0.84,
    sentiment: { pos: 21, neg: 25, neutral: 16, mixed: 6 },
    top_rising: { term: "late-night study cafés", lift: 3.7 },
    escalation_rate: 0.13,
    top_actions: [
      "Test midnight closing on Thursday to Saturday and publish the hours clearly.",
      "Create a quiet-work page covering Wi-Fi, charging sockets, and backup power.",
      "Add two sugar-free cold drinks and ask regulars for feedback before expanding.",
    ],
  },
  keywords: [
    {
      term: "late night cafe islamabad",
      count: 14,
      recent: 10,
      baseline: 4,
      lift: 3.7,
      z: 2.4,
      score: 51.8,
      example: {
        record_id: "demo-014",
        url: "https://www.reddit.com/r/islamabad/",
      },
    },
    {
      term: "quiet cafe with wifi f-7",
      count: 11,
      recent: 7,
      baseline: 4,
      lift: 2.1,
      z: 1.8,
      score: 23.1,
      example: {
        record_id: "demo-026",
        url: "https://www.reddit.com/r/islamabad/",
      },
    },
    {
      term: "sugar free coffee islamabad",
      count: 7,
      recent: 5,
      baseline: 2,
      lift: 2.8,
      z: 1.6,
      score: 19.6,
      example: {
        record_id: "demo-041",
        url: "https://www.reddit.com/r/islamabad/",
      },
    },
    {
      term: "cafe with charging sockets",
      count: 6,
      recent: 4,
      baseline: 2,
      lift: 2.2,
      z: 1.3,
      score: 13.2,
      example: {
        record_id: "demo-053",
        url: "https://www.reddit.com/r/islamabad/",
      },
    },
  ],
  voice: {
    pain_points: [
      {
        term: "unreliable Wi-Fi",
        count: 13,
        recent: 7,
        baseline: 6,
        lift: 1.4,
        z: 1.1,
        score: 18.2,
      },
      {
        term: "closes too early",
        count: 12,
        recent: 9,
        baseline: 3,
        lift: 3.5,
        z: 2.2,
        score: 42,
      },
      {
        term: "limited quiet seating",
        count: 9,
        recent: 5,
        baseline: 4,
        lift: 1.6,
        z: 1.2,
        score: 14.4,
      },
      {
        term: "unclear parking options",
        count: 6,
        recent: 3,
        baseline: 3,
        lift: 1.2,
        z: 0.7,
        score: 7.2,
      },
    ],
    requests: [
      {
        term: "open after midnight",
        count: 12,
        recent: 9,
        baseline: 3,
        lift: 3.5,
        z: 2.2,
        score: 42,
      },
      {
        term: "more charging sockets",
        count: 8,
        recent: 5,
        baseline: 3,
        lift: 2,
        z: 1.5,
        score: 16,
      },
      {
        term: "sugar-free drinks",
        count: 7,
        recent: 5,
        baseline: 2,
        lift: 2.8,
        z: 1.6,
        score: 19.6,
      },
      {
        term: "backup power updates",
        count: 5,
        recent: 4,
        baseline: 1,
        lift: 3.1,
        z: 1.7,
        score: 15.5,
      },
    ],
    questions: [
      {
        record_id: "demo-014",
        source: "reddit",
        text: "Is there a quiet café around F-7 that stays open after midnight and has reliable Wi-Fi?",
        url: "https://www.reddit.com/r/islamabad/",
      },
      {
        record_id: "demo-041",
        source: "web",
        text: "Which Islamabad coffee shops have genuinely sugar-free cold drinks?",
        url: "https://example.com/islamabad-cafe-question",
      },
    ],
  },
  competitors: [
    {
      name: "Margalla Mug House",
      mentions: 15,
      pos: 5,
      neg: 7,
      neutral: 2,
      mixed: 1,
      negativity: 0.47,
      top_complaints: ["slow evening service", "few power sockets"],
    },
    {
      name: "Cedar & Steam",
      mentions: 12,
      pos: 6,
      neg: 3,
      neutral: 2,
      mixed: 1,
      negativity: 0.25,
      top_complaints: ["closes before midnight", "limited quiet tables"],
    },
    {
      name: "Moonlit Roastery",
      mentions: 9,
      pos: 2,
      neg: 5,
      neutral: 2,
      mixed: 0,
      negativity: 0.56,
      top_complaints: ["inconsistent Wi-Fi", "unclear parking"],
    },
  ],
  gaps: [
    {
      theme: "late-night quiet workspace",
      demand: 12,
      negativity: 0.58,
      gap: 7.0,
    },
    {
      theme: "sugar-free cold menu",
      demand: 7,
      negativity: 0.44,
      gap: 3.1,
    },
  ],
  content: {
    briefs: [
      {
        title: "A practical guide to late-night study cafés in Islamabad",
        target_keyword: "late night cafe islamabad",
        outline: [
          "Hours by neighbourhood",
          "Wi-Fi and backup power checklist",
          "Quiet seating and charging access",
        ],
        competitor_weakness:
          "People cannot confirm late hours or workspace facilities before visiting.",
      },
      {
        title: "Where to work with reliable Wi-Fi around F-7",
        target_keyword: "quiet cafe with wifi f-7",
        outline: [
          "Best times for quiet seating",
          "Internet and socket availability",
          "Parking and public transport notes",
        ],
        competitor_weakness:
          "Existing pages list cafés but rarely answer practical work-session questions.",
      },
    ],
    faqs: [
      {
        question: "Which cafés in Islamabad stay open after midnight?",
        source_record_ids: ["demo-014", "demo-019"],
      },
      {
        question: "Where can I find a quiet café with charging sockets in F-7?",
        source_record_ids: ["demo-026", "demo-053"],
      },
    ],
    faq_jsonld: JSON.stringify({
      "@context": "https://schema.org",
      "@type": "FAQPage",
      mainEntity: [],
    }),
  },
  threads: [
    {
      record_id: "demo-014",
      title: "Quiet late-night café for a study session?",
      subreddit: "r/islamabad",
      url: "https://www.reddit.com/r/islamabad/",
      created_at: "2025-10-08T20:15:00Z",
      question:
        "Is there a quiet café around F-7 that stays open after midnight and has reliable Wi-Fi?",
      relevance: 0.94,
    },
    {
      record_id: "demo-026",
      title: "Coffee shop with sockets near Blue Area",
      subreddit: "r/islamabad",
      url: "https://www.reddit.com/r/islamabad/",
      created_at: "2025-10-06T11:40:00Z",
      question:
        "Need somewhere near Blue Area for a three-hour call. Any café with stable internet and sockets?",
      relevance: 0.89,
    },
    {
      record_id: "demo-053",
      title: "Cafés with sugar-free options",
      subreddit: "r/islamabad",
      url: "https://www.reddit.com/r/islamabad/",
      created_at: "2025-10-03T16:05:00Z",
      question:
        "Most menus only show regular syrups. Has anyone found good sugar-free cold coffee?",
      relevance: 0.83,
    },
  ],
  participation_note:
    "Use this evidence to understand customers. If you join a thread, answer helpfully, disclose your connection to the business, and follow community rules. Nothing is posted automatically.",
  metrics: {
    calls_by_tier: { small: 55, large: 17 },
    cache_hits: 8,
    escalations: 9,
    escalation_rate: 0.13,
    repairs: 4,
    schema_failures: 2,
    schema_failure_rate: 0.03,
    filtered: 13,
    failed: 0,
    tokens: { prompt: 48720, completion: 8120 },
    latency_ms: { p50: 390, p95: 1180 },
  },
};
