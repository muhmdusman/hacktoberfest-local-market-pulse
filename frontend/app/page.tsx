"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  createRun,
  getModels,
  getOptions,
  getRun,
  getRunResults,
  getSourcesStatus,
  isUsingMocks,
  USE_MOCKS_BY_DEFAULT,
} from "@/lib/api";
import type {
  ModelsResponse,
  OptionsResponse,
  ResultsResponse,
  RunMode,
  RunStage,
  RunStatusResponse,
  SourceName,
  SourceStatusResponse,
  TermSignal,
} from "@/lib/types";

const FALLBACK_BUSINESSES = ["cafe", "restaurant", "gym", "salon", "other"];
const RUN_STAGES: Array<{ key: RunStage; label: string }> = [
  { key: "collecting", label: "Collect" },
  { key: "analyzing", label: "Analyze" },
  { key: "trending", label: "Find trends" },
  { key: "reporting", label: "Build report" },
];

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function SignalList({ items }: { items: TermSignal[] }) {
  const max = Math.max(...items.map((item) => item.count), 1);

  return (
    <div className="signal-list">
      {items.map((item) => (
        <div className="signal" key={item.term}>
          <div className="signal-heading">
            <span>{item.term}</span>
            <strong>{item.count} mentions</strong>
          </div>
          <div className="signal-track" aria-hidden="true">
            <span style={{ width: `${(item.count / max) * 100}%` }} />
          </div>
          <small>{item.lift.toFixed(1)}x recent lift</small>
        </div>
      ))}
    </div>
  );
}

function ProgressPanel({ run }: { run: RunStatusResponse | null }) {
  const activeIndex = run
    ? run.stage === "done"
      ? RUN_STAGES.length
      : RUN_STAGES.findIndex((stage) => stage.key === run.stage)
    : 0;
  const progress = run
    ? Math.round((run.progress.done / Math.max(run.progress.total, 1)) * 100)
    : 4;

  return (
    <section className="progress-panel panel" aria-live="polite">
      <div className="section-heading-row">
        <div>
          <p className="eyebrow">Analysis in progress</p>
          <h2>{run ? RUN_STAGES[activeIndex]?.label || "Report ready" : "Starting scan"}</h2>
        </div>
        <strong className="progress-percent">{progress}%</strong>
      </div>

      <ol className="stage-list">
        {RUN_STAGES.map((stage, index) => (
          <li
            className={
              index < activeIndex
                ? "stage-complete"
                : index === activeIndex
                  ? "stage-active"
                  : ""
            }
            key={stage.key}
          >
            <span>{index + 1}</span>
            {stage.label}
          </li>
        ))}
      </ol>

      <div
        className="progress-track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progress}
      >
        <span style={{ width: `${progress}%` }} />
      </div>

      {run && (
        <div className="run-counts">
          <span>{run.counts.collected} collected</span>
          <span>{run.counts.kept} relevant</span>
          <span>{run.counts.escalated} escalated</span>
        </div>
      )}
      {run?.messages.map((message) => (
        <p className="run-message" key={message.text}>
          {message.text}
        </p>
      ))}
    </section>
  );
}

function ResultsDashboard({
  results,
  models,
}: {
  results: ResultsResponse;
  models: ModelsResponse | null;
}) {
  const sentiment = results.overview.sentiment;
  const sentimentTotal =
    sentiment.pos + sentiment.neg + sentiment.neutral + sentiment.mixed;
  const activeModel = models?.models.find((model) => model.eligible);

  return (
    <div className="results-stack">
      <div className="provenance-banner">
        <div>
          <strong>
            {results.provenance.synthetic
              ? "Synthetic demo data"
              : "Live market data"}
          </strong>
          <span>
            Sources: {Object.entries(results.provenance.sources_used)
              .map(([source, adapter]) => `${source} via ${adapter}`)
              .join(" · ")}
          </span>
        </div>
        <span className="run-id">Run {results.run_id}</span>
      </div>

      <nav className="result-nav" aria-label="Report sections">
        <a href="#overview">Overview</a>
        <a href="#customer-voice">Customer voice</a>
        <a href="#competitors">Competitors</a>
        <a href="#keywords">Keywords</a>
        <a href="#recommendations">Actions</a>
        <a href="#evidence">Evidence</a>
      </nav>

      <section className="result-section panel" id="overview">
        <div className="section-heading-row">
          <div>
            <p className="eyebrow">Overview</p>
            <h2>What the market is saying</h2>
          </div>
          <span className="section-note">Islamabad cafés</span>
        </div>

        <div className="kpi-grid">
          <article className="kpi-card">
            <span>Posts analyzed</span>
            <strong>{results.overview.posts_analysed}</strong>
            <small>{formatPercent(results.overview.relevant_pct)} relevant</small>
          </article>
          <article className="kpi-card">
            <span>Top rising trend</span>
            <strong className="kpi-text">{results.overview.top_rising.term}</strong>
            <small>{results.overview.top_rising.lift.toFixed(1)}x lift</small>
          </article>
          <article className="kpi-card">
            <span>Negative signals</span>
            <strong>{sentiment.neg}</strong>
            <small>of {sentimentTotal} analyzed posts</small>
          </article>
        </div>

        <div className="sentiment-block">
          <div className="subheading-row">
            <h3>Sentiment mix</h3>
            <span>{sentimentTotal} signals</span>
          </div>
          <div
            className="sentiment-bar"
            role="img"
            aria-label={`${sentiment.pos} positive, ${sentiment.neg} negative, ${sentiment.neutral} neutral, and ${sentiment.mixed} mixed posts`}
          >
            <span
              className="sentiment-positive"
              style={{ width: `${(sentiment.pos / sentimentTotal) * 100}%` }}
            />
            <span
              className="sentiment-negative"
              style={{ width: `${(sentiment.neg / sentimentTotal) * 100}%` }}
            />
            <span
              className="sentiment-neutral"
              style={{ width: `${(sentiment.neutral / sentimentTotal) * 100}%` }}
            />
            <span
              className="sentiment-mixed"
              style={{ width: `${(sentiment.mixed / sentimentTotal) * 100}%` }}
            />
          </div>
          <div className="sentiment-legend">
            <span><i className="positive-dot" />Positive {sentiment.pos}</span>
            <span><i className="negative-dot" />Negative {sentiment.neg}</span>
            <span><i className="neutral-dot" />Neutral {sentiment.neutral}</span>
            <span><i className="mixed-dot" />Mixed {sentiment.mixed}</span>
          </div>
        </div>
      </section>

      <section className="result-section panel" id="customer-voice">
        <p className="eyebrow">Customer voice</p>
        <h2>Pain points &amp; unmet needs</h2>
        <div className="two-column-section">
          <div>
            <h3>Pain points</h3>
            <SignalList items={results.voice.pain_points} />
          </div>
          <div>
            <h3>Unmet needs</h3>
            <SignalList items={results.voice.requests} />
          </div>
        </div>
      </section>

      <section className="result-section panel" id="competitors">
        <div className="section-heading-row">
          <div>
            <p className="eyebrow">Competitor pulse</p>
            <h2>Where nearby options fall short</h2>
          </div>
          {results.provenance.synthetic && (
            <span className="section-note">Demo names are fictional</span>
          )}
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Competitor</th>
                <th scope="col">Mentions</th>
                <th scope="col">Negative</th>
                <th scope="col">Common complaints</th>
              </tr>
            </thead>
            <tbody>
              {results.competitors.map((competitor) => (
                <tr key={competitor.name}>
                  <th scope="row">{competitor.name}</th>
                  <td>{competitor.mentions}</td>
                  <td>{formatPercent(competitor.negativity)}</td>
                  <td>{competitor.top_complaints.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="gap-list">
          {results.gaps.map((gap) => (
            <div key={gap.theme}>
              <span>Market gap</span>
              <strong>{gap.theme}</strong>
              <small>Opportunity score {gap.gap.toFixed(1)}</small>
            </div>
          ))}
        </div>
      </section>

      <section className="result-section panel" id="keywords">
        <p className="eyebrow">Search language</p>
        <h2>Local keywords</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Phrase</th>
                <th scope="col">Mentions</th>
                <th scope="col">Trend</th>
                <th scope="col">Score</th>
              </tr>
            </thead>
            <tbody>
              {results.keywords.map((keyword) => (
                <tr key={keyword.term}>
                  <th scope="row">{keyword.term}</th>
                  <td>{keyword.count}</td>
                  <td>
                    <span className="trend-badge">
                      {keyword.lift > 1.5 ? "Rising" : "Steady"} · {keyword.lift.toFixed(1)}x
                    </span>
                  </td>
                  <td>{keyword.score.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="result-section panel" id="recommendations">
        <p className="eyebrow">Next steps</p>
        <h2>Recommended actions &amp; content ideas</h2>
        <div className="recommendation-grid">
          <div className="action-card">
            <h3>Actions this week</h3>
            <ol>
              {results.overview.top_actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ol>
          </div>
          <div className="brief-list">
            {results.content.briefs.map((brief) => (
              <article className="brief-card" key={brief.title}>
                <span>Content idea</span>
                <h3>{brief.title}</h3>
                <p><strong>Target:</strong> {brief.target_keyword}</p>
                <ul>
                  {brief.outline.map((point) => <li key={point}>{point}</li>)}
                </ul>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="result-section panel" id="evidence">
        <p className="eyebrow">Source evidence</p>
        <h2>Reddit threads &amp; evidence</h2>
        <div className="thread-list">
          {results.threads.map((thread) => (
            <article className="thread-card" key={thread.record_id}>
              <div className="thread-meta">
                <span>{thread.subreddit}</span>
                <span>{formatPercent(thread.relevance)} relevant</span>
              </div>
              <h3>{thread.title}</h3>
              <blockquote>{thread.question}</blockquote>
              <a href={thread.url} target="_blank" rel="noreferrer">
                Open source thread
              </a>
            </article>
          ))}
        </div>
        <p className="participation-note">{results.participation_note}</p>
      </section>

      <aside className="ai-box" aria-label="How the AI worked">
        <div>
          <p className="eyebrow">How the AI worked</p>
          <h2>Small-model routing, visible</h2>
        </div>
        <dl className="ai-grid">
          <div>
            <dt>Model</dt>
            <dd>{activeModel?.id || results.provenance.models.join(", ")}</dd>
          </div>
          <div>
            <dt>Provider</dt>
            <dd>{activeModel?.provider || results.provenance.provider}</dd>
          </div>
          <div>
            <dt>Size policy</dt>
            <dd>{activeModel ? `${activeModel.nominal_size} · ≤8B verified` : "≤8B verified"}</dd>
          </div>
          <div>
            <dt>Routed calls</dt>
            <dd>{results.metrics.calls_by_tier.small} fast / {results.metrics.calls_by_tier.large} deep</dd>
          </div>
          <div>
            <dt>Repairs</dt>
            <dd>{results.metrics.repairs}</dd>
          </div>
          <div>
            <dt>Escalations</dt>
            <dd>{results.metrics.escalations} ({formatPercent(results.metrics.escalation_rate)})</dd>
          </div>
        </dl>
      </aside>
    </div>
  );
}

export default function Home() {
  const [options, setOptions] = useState<OptionsResponse | null>(null);
  const [models, setModels] = useState<ModelsResponse | null>(null);
  const [sourceStatus, setSourceStatus] = useState<SourceStatusResponse | null>(null);
  const [business, setBusiness] = useState("cafe");
  const [city, setCity] = useState("Islamabad");
  const [competitors, setCompetitors] = useState(
    "Margalla Mug House, Cedar & Steam",
  );
  const [sources, setSources] = useState<Record<SourceName, boolean>>({
    reddit: true,
    web: true,
  });
  const [mode, setMode] = useState<RunMode>("cached");
  const [run, setRun] = useState<RunStatusResponse | null>(null);
  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forceMock, setForceMock] = useState(false);
  const [usingMocks, setUsingMocks] = useState(USE_MOCKS_BY_DEFAULT);

  useEffect(() => {
    let cancelled = false;

    async function loadSetup() {
      try {
        const [nextOptions, nextModels, nextSources] = await Promise.all([
          getOptions(),
          getModels(),
          getSourcesStatus(),
        ]);
        if (cancelled) return;
        setOptions(nextOptions);
        setModels(nextModels);
        setSourceStatus(nextSources);
        setUsingMocks(isUsingMocks());
      } catch (setupError) {
        if (!cancelled) setError(errorMessage(setupError));
      }
    }

    void loadSetup();
    return () => {
      cancelled = true;
    };
  }, []);

  async function runAnalysis(forceDemo = false) {
    const selectedSources = (Object.entries(sources) as Array<[SourceName, boolean]>)
      .filter(([, selected]) => selected)
      .map(([source]) => source);

    if (selectedSources.length === 0) {
      setError("Select Reddit, Web, or both before starting the analysis.");
      return;
    }

    const requestOptions = forceDemo || forceMock ? { forceMock: true } : undefined;

    setLoading(true);
    setError(null);
    setResults(null);
    setRun(null);

    if (forceDemo) {
      setForceMock(true);
      setUsingMocks(true);
      setMode("cached");
    } else {
      setUsingMocks(isUsingMocks(forceMock));
    }

    try {
      if (forceDemo) {
        const [demoOptions, demoModels, demoSources] = await Promise.all([
          getOptions(requestOptions),
          getModels(requestOptions),
          getSourcesStatus(requestOptions),
        ]);
        setOptions(demoOptions);
        setModels(demoModels);
        setSourceStatus(demoSources);
      }

      const started = await createRun(
        {
          business,
          city: city.trim(),
          areas: [],
          competitors: competitors
            .split(",")
            .map((name) => name.trim())
            .filter(Boolean),
          sources: selectedSources,
          mode: forceDemo ? "cached" : mode,
          urls: [],
          limit: 100,
          provider: null,
          votes: 3,
        },
        requestOptions,
      );

      let nextRun = await getRun(started.run_id, requestOptions);
      setRun(nextRun);

      while (nextRun.status !== "done") {
        if (nextRun.status === "failed") {
          throw new Error(nextRun.error?.message || "The analysis run failed.");
        }
        await new Promise((resolve) => window.setTimeout(resolve, 320));
        nextRun = await getRun(started.run_id, requestOptions);
        setRun(nextRun);
      }

      setResults(await getRunResults(started.run_id, requestOptions));
    } catch (runError) {
      setError(errorMessage(runError));
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runAnalysis();
  }

  const model = models?.models.find((item) => item.eligible);

  return (
    <div className="dashboard-page">
      <header className="site-header">
        <div className="header-inner">
          <div className="brand-block">
            <span className="brand-mark" aria-hidden="true">LM</span>
            <div>
              <h1>Local Market Pulse</h1>
              <p>Give your agent eyes on the local market</p>
            </div>
          </div>
          <span className={`transport-badge ${usingMocks ? "demo" : "live"}`}>
            {usingMocks ? "Local demo adapter" : "Live API"}
          </span>
        </div>
      </header>

      <main className="page-grid">
        <aside className="scan-panel panel">
          <div className="scan-heading">
            <p className="eyebrow">New market scan</p>
            <h2>Choose what to listen for</h2>
            <p>Turn public conversations into a practical local-market report.</p>
          </div>

          <form onSubmit={handleSubmit}>
            <label className="field">
              <span>Business</span>
              <select value={business} onChange={(event) => setBusiness(event.target.value)}>
                {(options?.business_types || FALLBACK_BUSINESSES).map((type) => (
                  <option value={type} key={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>City</span>
              <input
                value={city}
                onChange={(event) => setCity(event.target.value)}
                required
                placeholder="Islamabad"
              />
            </label>

            <label className="field">
              <span>Competitors</span>
              <input
                value={competitors}
                onChange={(event) => setCompetitors(event.target.value)}
                placeholder="Separate names with commas"
              />
              <small>Comma-separated. Demo competitor names are fictional.</small>
            </label>

            <fieldset className="field-group">
              <legend>Where should we listen?</legend>
              <div className="choice-grid">
                <label className="source-choice">
                  <input
                    type="checkbox"
                    checked={sources.reddit}
                    onChange={(event) =>
                      setSources((current) => ({
                        ...current,
                        reddit: event.target.checked,
                      }))
                    }
                  />
                  <span><strong>Reddit</strong><small>Questions and local discussions</small></span>
                </label>
                <label className="source-choice">
                  <input
                    type="checkbox"
                    checked={sources.web}
                    onChange={(event) =>
                      setSources((current) => ({
                        ...current,
                        web: event.target.checked,
                      }))
                    }
                  />
                  <span><strong>Web</strong><small>Public pages and search results</small></span>
                </label>
              </div>
            </fieldset>

            <fieldset className="field-group">
              <legend>Scan mode</legend>
              <div className="mode-grid">
                <label className={mode === "cached" ? "mode-choice selected" : "mode-choice"}>
                  <input
                    type="radio"
                    name="mode"
                    value="cached"
                    checked={mode === "cached"}
                    onChange={() => setMode("cached")}
                  />
                  <span><strong>Cached demo</strong><small>Fast, saved data</small></span>
                </label>
                <label className={mode === "live" ? "mode-choice selected" : "mode-choice"}>
                  <input
                    type="radio"
                    name="mode"
                    value="live"
                    checked={mode === "live"}
                    onChange={() => setMode("live")}
                  />
                  <span><strong>Live mode</strong><small>Uses connected API</small></span>
                </label>
              </div>
            </fieldset>

            <div className="adapter-status" aria-label="Connected data sources">
              {sourceStatus ? sourceStatus.sources.map((source) => (
                <span key={source.source}>
                  <i />{source.source}: {source.active}
                </span>
              )) : <span>Checking source adapters...</span>}
            </div>

            {model && (
              <p className="model-note">
                AI: {model.id} via {model.provider} · {model.nominal_size}
              </p>
            )}

            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? "Analyzing market..." : "Analyze market"}
            </button>
            {usingMocks && (
              <p className="form-note">Runs locally with synthetic data; no backend is required.</p>
            )}
          </form>
        </aside>

        <div className="report-column">
          {error ? (
            <section className="error-panel panel" role="alert">
              <p className="eyebrow">Analysis unavailable</p>
              <h2>We could not complete this scan</h2>
              <p>{error}</p>
              <div className="error-actions">
                <button type="button" onClick={() => void runAnalysis()} disabled={loading}>
                  Retry
                </button>
                <button type="button" className="secondary-button" onClick={() => void runAnalysis(true)} disabled={loading}>
                  Use demo data
                </button>
              </div>
            </section>
          ) : loading ? (
            <ProgressPanel run={run} />
          ) : results ? (
            <ResultsDashboard results={results} models={models} />
          ) : (
            <section className="empty-state panel">
              <div className="empty-state-copy">
                <p className="eyebrow">Ready to listen</p>
                <h2>Your market report will appear here</h2>
                <p>
                  Run a scan to see customer pain points, local demand, competitors,
                  keywords, recommended actions, and the evidence behind them.
                </p>
              </div>
              <div className="preview-grid" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
