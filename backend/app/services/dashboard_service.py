"""Translate persisted scan data into the frontend dashboard/report contract."""

import json
import math
from collections import Counter
from datetime import UTC, datetime
from html import escape
from statistics import median
from typing import Any
from urllib.parse import urlparse

from app.llm.registry import resolve_model
from app.models.scan import Scan, ScanResult


def frontend_stage(stage: str, status: str) -> str:
    if status in ("done", "failed"):
        return "done"
    return {
        "queued": "collecting", "planning": "collecting", "searching": "collecting", "collecting": "collecting",
        "evaluating": "analyzing", "summarizing": "trending", "saving": "reporting",
    }.get(stage, "collecting")


def status_payload(scan: Scan, results: list[ScanResult]) -> dict[str, Any]:
    total = max(scan.max_results, len(results))
    done = len(results) if scan.status == "done" else 0
    relevant = sum(r.relevant is True for r in results)
    failed = sum(r.status == "failed" for r in results)
    stage = frontend_stage(scan.stage, scan.status)
    if stage in ("trending", "reporting"):
        done = total
    message = "Searching Reddit via site:reddit.com and the public web with DDGS; evaluating with the configured open-weight model."
    return {
        "run_id": scan.id, "status": scan.status, "stage": stage,
        "progress": {"done": done, "total": total},
        "counts": {"collected": len(results), "deduped": len(results), "kept": relevant, "filtered": max(0, len(results)-relevant-failed), "escalated": 0, "failed": failed},
        "messages": [{"level": "error" if scan.status == "failed" else "info", "text": scan.error or message}],
        "created_at": scan.created_at, "finished_at": scan.finished_at,
        "error": {"message": scan.error} if scan.error else None,
    }


def _signal(item: dict[str, Any], example: ScanResult | None = None) -> dict[str, Any]:
    count = int(item.get("count", 0))
    signal = {"term": item.get("term", ""), "count": count, "recent": count, "baseline": 0, "lift": 1.0, "z": 0.0, "score": float(count)}
    if example:
        signal["example"] = {"record_id": str(example.id), "url": example.url}
    return signal


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    values = sorted(values)
    return values[min(len(values)-1, math.ceil(percentile * len(values))-1)]


def build_results(scan: Scan, results: list[ScanResult]) -> dict[str, Any]:
    summary = scan.summary or {}
    totals = summary.get("totals", {})
    relevant_rows = [r for r in results if r.relevant is True and r.insight]
    example = relevant_rows[0] if relevant_rows else (results[0] if results else None)
    sentiment = {key: 0 for key in ("pos", "neg", "neutral", "mixed")}
    for row in relevant_rows:
        if row.sentiment in sentiment:
            sentiment[row.sentiment] += 1

    keywords = [_signal(item, example) for item in summary.get("keywords", [])]
    pains = [_signal(item) for item in summary.get("pain_points", [])]
    requests = [_signal(item) for item in summary.get("requests", [])]
    by_url = {r.url: r for r in results}
    questions = [
        {"record_id": str(by_url[q["url"]].id) if q.get("url") in by_url else "", "source": q.get("source", "web"), "text": q.get("question", ""), "url": q.get("url", "")}
        for q in summary.get("questions", [])
    ]

    competitors = []
    for item in summary.get("competitors", []):
        name = item["name"]
        matched = [r for r in relevant_rows if any(n.lower() == name.lower() for n in (r.insight or {}).get("competitors", []))]
        split = Counter(r.sentiment for r in matched)
        complaints = Counter(p for r in matched for p in (r.insight or {}).get("pain_points", []))
        competitors.append({"name": name, "mentions": item["mentions"], "pos": split["pos"], "neg": split["neg"], "neutral": split["neutral"], "mixed": split["mixed"], "negativity": item.get("negativity", 0.5), "top_complaints": [x for x, _ in complaints.most_common(3)]})

    negative = sentiment["neg"] + sentiment["mixed"]
    overall_negativity = round((negative + 1) / (len(relevant_rows) + 2), 2)
    gaps = [{"theme": r["term"], "demand": r["count"], "negativity": overall_negativity, "gap": round(r["count"] * overall_negativity, 2)} for r in requests]
    faq_items = [{"question": q["text"], "source_record_ids": [q["record_id"]]} for q in questions[:8]]
    faq_jsonld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q["question"], "acceptedAnswer": {"@type": "Answer", "text": "Draft your answer here — verify facts before publishing."}} for q in faq_items]}, ensure_ascii=False)

    actions = summary.get("actions", [])
    briefs = []
    for i, action in enumerate(actions[:3]):
        keyword = keywords[i % len(keywords)]["term"] if keywords else f"{scan.business} {scan.city}"
        briefs.append({"title": action.rstrip("."), "target_keyword": keyword, "outline": ["What local customers are asking", "How the business can respond", "Practical details and next step"], "competitor_weakness": pains[0]["term"] if pains else "Unmet local demand"})

    threads = []
    for q in summary.get("threads_to_answer", []):
        row = by_url.get(q.get("url", ""))
        path = urlparse(q.get("url", "")).path.split("/")
        subreddit = f"r/{path[2]}" if len(path) > 2 and path[1] == "r" else "Reddit"
        threads.append({"record_id": str(row.id) if row else "", "title": q.get("title", ""), "subreddit": subreddit, "url": q.get("url", ""), "created_at": scan.created_at.isoformat(), "question": q.get("question", ""), "relevance": (row.confidence if row else None) or 0.0})

    latencies = [r.latency_ms for r in results]
    repairs = sum(r.repairs for r in results)
    failures = sum(r.status == "failed" for r in results)
    spec = resolve_model(scan.model)
    analysed = int(totals.get("evaluated", len(results)))
    relevant = int(totals.get("relevant", len(relevant_rows)))
    top = keywords[0] if keywords else {"term": "No signal yet", "lift": 0.0}

    return {
        "run_id": scan.id,
        "provenance": {"synthetic": False, "mock": False, "sources_used": {s: "ddgs-site-search" if s == "reddit" else "ddgs" for s in scan.sources}, "provider": spec.provider, "models": [scan.model], "generated_at": (scan.finished_at or datetime.now(UTC)).isoformat()},
        "overview": {"posts_analysed": analysed, "relevant_pct": round(relevant / analysed, 2) if analysed else 0.0, "sentiment": sentiment, "top_rising": {"term": top["term"], "lift": top["lift"]}, "escalation_rate": 0.0, "top_actions": actions},
        "keywords": keywords,
        "voice": {"pain_points": pains, "requests": requests, "questions": questions},
        "competitors": competitors, "gaps": gaps,
        "content": {"briefs": briefs, "faqs": faq_items, "faq_jsonld": faq_jsonld},
        "threads": threads,
        "participation_note": "Answer helpfully, disclose that you own/work at the business, and follow each subreddit's rules. Nothing is posted automatically.",
        "metrics": {"calls_by_tier": {"small": 0, "large": sum(r.attempts for r in results)+1}, "cache_hits": 0, "escalations": 0, "escalation_rate": 0.0, "repairs": repairs, "schema_failures": failures, "schema_failure_rate": round(failures/len(results), 2) if results else 0.0, "filtered": max(0, len(results)-relevant-failures), "failed": failures, "tokens": {"prompt": 0, "completion": 0}, "latency_ms": {"p50": int(median(latencies)) if latencies else 0, "p95": _percentile(latencies, 0.95)}},
    }


def render_markdown(scan: Scan, payload: dict[str, Any]) -> str:
    voice = payload["voice"]
    lines = [f"# Local Market Pulse — {scan.business.title()} in {scan.city}", "", f"Generated with `{scan.model}` ({payload['provenance']['provider']}).", "", "## Actions this week"]
    lines += [f"- {x}" for x in payload["overview"]["top_actions"]] or ["- Collect more local evidence."]
    for title, items in (("Keyword opportunities", payload["keywords"]), ("Pain points", voice["pain_points"]), ("Customer requests", voice["requests"])):
        lines += ["", f"## {title}"] + ([f"- **{x['term']}** — {x['count']} mentions" for x in items] or ["- No strong signal yet."])
    lines += ["", "## Reddit threads worth answering", "", payload["participation_note"]]
    lines += [f"- [{x['title']}]({x['url']}) — {x['question']}" for x in payload["threads"]] or ["- No matching question thread found."]
    return "\n".join(lines) + "\n"


def render_html(scan: Scan, payload: dict[str, Any]) -> str:
    md = render_markdown(scan, payload)
    body = "\n".join(f"<p>{escape(line)}</p>" if line else "" for line in md.splitlines())
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Local Market Pulse</title><style>body{{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 20px;color:#17233d}}p{{line-height:1.5}}</style></head><body>{body}</body></html>"
