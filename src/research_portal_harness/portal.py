from __future__ import annotations

import re
from dataclasses import dataclass
from email.message import Message
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

from .common import matches_any, now_iso, redact_url, safe_filename, url_allowed
from .manifest import load_manifest, manifest_path, record_download, save_manifest
from .workspace import load_brokers


DEFAULT_DOWNLOAD_SELECTORS = [
    "a[download]",
    "a[href*='download' i]",
    "a[href*='export' i]",
    "a[href*='pdf' i]",
    "a[href*='excel' i]",
    "a[href$='.pdf' i]",
    "a[href$='.xls' i]",
    "a[href$='.xlsx' i]",
    "button:has-text('Download')",
    "button:has-text('PDF')",
    "button:has-text('Excel')",
    "button:has-text('Export')",
    "[role='button']:has-text('Download')",
    "[role='button']:has-text('PDF')",
    "[role='button']:has-text('Excel')",
    "[aria-label*='download' i]",
    "[title*='download' i]",
]

DEFAULT_TEXT_HINTS = [
    "download",
    "pdf",
    "excel",
    "model",
    "valuation",
    "earnings",
    "initiation",
    "research",
    "report",
    "export",
    "transcript",
    "financial",
    "data",
]

DOWNLOAD_EXTENSIONS = {".pdf", ".xls", ".xlsx", ".xlsm", ".csv", ".zip", ".json"}


@dataclass
class PortalResult:
    downloaded: int = 0
    skipped_duplicates: int = 0
    candidates: int = 0
    errors: int = 0


def _cfg_value(config: dict[str, Any], broker: dict[str, Any], key: str, default: Any) -> Any:
    return broker.get(key, config.get(key, default))


def _is_auth_pending(page: Any, broker: dict[str, Any]) -> bool:
    if matches_any(page.url, broker.get("auth_pending_url_patterns", [])):
        return True
    for selector in broker.get("auth_pending_selectors", []):
        try:
            if page.locator(selector).first.is_visible(timeout=500):
                return True
        except Exception:
            continue
    return False


def _is_auth_success(page: Any, broker: dict[str, Any]) -> bool:
    if matches_any(page.url, broker.get("auth_pending_url_patterns", [])):
        return False
    if matches_any(page.url, broker.get("auth_success_url_patterns", [])):
        return True
    for selector in broker.get("auth_success_selectors", []):
        try:
            if page.locator(selector).first.is_visible(timeout=500):
                return True
        except Exception:
            continue
    return False


def _wait_for_manual_login(page: Any, broker: dict[str, Any], config: dict[str, Any]) -> bool:
    wait_ms = int(_cfg_value(config, broker, "manual_login_timeout_ms", 300000))
    poll_ms = int(_cfg_value(config, broker, "manual_login_poll_ms", 2000))
    print(f"[rph] complete login in the browser if prompted; waiting up to {wait_ms // 1000}s", flush=True)
    elapsed = 0
    while elapsed < wait_ms:
        if _is_auth_success(page, broker):
            print(f"[rph] login detected for {broker['name']}: {redact_url(page.url)}", flush=True)
            return True
        page.wait_for_timeout(min(poll_ms, wait_ms - elapsed))
        elapsed += poll_ms
    if _is_auth_pending(page, broker):
        print(f"[rph] login still appears pending for {broker['name']}: {redact_url(page.url)}", flush=True)
        return False
    return _is_auth_success(page, broker)


def _filename_from_headers(headers: dict[str, str], fallback_url: str, title: str) -> str:
    disposition = headers.get("content-disposition") or headers.get("Content-Disposition") or ""
    if disposition:
        star_match = re.search(r"filename\\*=(?:UTF-8'')?([^;]+)", disposition, flags=re.IGNORECASE)
        if star_match:
            filename = unquote(star_match.group(1).strip().strip('"'))
            if filename:
                return safe_filename(filename)
        msg = Message()
        msg["content-disposition"] = disposition
        filename = msg.get_filename()
        if filename:
            return safe_filename(filename)
    parsed = Path(urlparse(fallback_url).path).name
    if parsed and "." in parsed:
        return safe_filename(parsed)
    return safe_filename(title)


def _ensure_extension(filename: str, content_type: str, url: str) -> str:
    if Path(filename).suffix:
        return filename
    content_type = content_type.lower()
    url = url.lower()
    if "pdf" in content_type or url.endswith(".pdf"):
        return f"{filename}.pdf"
    if "spreadsheet" in content_type or "excel" in content_type or url.endswith((".xls", ".xlsx", ".xlsm")):
        return f"{filename}.xlsx"
    if "json" in content_type:
        return f"{filename}.json"
    if "csv" in content_type or url.endswith(".csv"):
        return f"{filename}.csv"
    if "zip" in content_type or url.endswith(".zip"):
        return f"{filename}.zip"
    return filename


def _looks_like_download(headers: dict[str, str], filename: str, allowed_extensions: list[str]) -> bool:
    suffix = Path(filename).suffix.lower()
    content_type = (headers.get("content-type") or "").lower()
    disposition = (headers.get("content-disposition") or "").lower()
    if suffix in set(allowed_extensions):
        return True
    if "attachment" in disposition or "filename=" in disposition:
        return True
    return any(token in content_type for token in ["pdf", "excel", "spreadsheet", "csv", "zip", "octet-stream"])


def _extract_candidates_from_page(page: Any, broker: dict[str, Any], task: dict[str, Any] | None) -> list[dict[str, str]]:
    allowed_domains = broker.get("allowed_domains", [])
    exclude_url_patterns = broker.get("exclude_url_patterns", [])
    exclude_title_patterns = broker.get("exclude_title_patterns", [])
    text_hints = broker.get("text_hints", DEFAULT_TEXT_HINTS)
    task_terms = []
    if task:
        for key in ["tickers", "company_terms", "industry_terms", "keywords"]:
            task_terms.extend(task.get(key, []))

    links = page.eval_on_selector_all(
        "a",
        """els => els.map(el => ({
            href: el.href || "",
            text: (el.innerText || el.textContent || "").trim(),
            title: el.getAttribute("title") || "",
            aria: el.getAttribute("aria-label") || ""
        }))""",
    )
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for link in links:
        href = link.get("href") or ""
        absolute = urljoin(page.url, href)
        text = " ".join([link.get("text") or "", link.get("title") or "", link.get("aria") or ""]).strip()
        haystack = f"{absolute} {text}".lower()
        if not href or not url_allowed(absolute, allowed_domains):
            continue
        if matches_any(absolute, exclude_url_patterns) or matches_any(text, exclude_title_patterns):
            continue
        has_hint = any(hint.lower() in haystack for hint in text_hints)
        has_task_term = bool(task_terms) and any(str(term).lower() in haystack for term in task_terms)
        suffix = Path(urlparse(absolute).path).suffix.lower()
        if not (has_hint or has_task_term or suffix in DOWNLOAD_EXTENSIONS):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        candidates.append(
            {
                "url": absolute,
                "title": text or Path(urlparse(absolute).path).name or broker["name"],
                "page_url": page.url,
                "discovered_at": now_iso(),
                "reason": "task-term" if has_task_term else "download-hint",
            }
        )
    return candidates


def _open_context(root: Path, broker: dict[str, Any], config: dict[str, Any], headless: bool | None = None) -> tuple[Any, Any, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is required. Run: python3 -m pip install -e . && python3 -m playwright install chromium") from exc

    profile_root = root / config.get("browser_profile_dir", "data/state/browser_profiles")
    profile_dir = profile_root / broker["id"]
    profile_dir.mkdir(parents=True, exist_ok=True)
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch_persistent_context(
        str(profile_dir),
        headless=bool(config.get("headless", False) if headless is None else headless),
        accept_downloads=True,
    )
    page = browser.pages[0] if browser.pages else browser.new_page()
    return playwright, browser, page


def login(root: Path, broker: dict[str, Any], headless: bool | None = None) -> bool:
    config = load_brokers(root)
    if not broker.get("allowed_domains"):
        raise ValueError(f"{broker['id']} has no allowed_domains. Add the observed portal domains first.")
    start_urls = broker.get("start_urls") or []
    if not start_urls:
        raise ValueError(f"{broker['id']} has no start_urls.")

    playwright, browser, page = _open_context(root, broker, config, headless=headless)
    try:
        page.goto(start_urls[0], wait_until=broker.get("wait_until", "domcontentloaded"))
        page.wait_for_timeout(int(broker.get("wait_after_load_ms", 3000)))
        return _wait_for_manual_login(page, broker, config)
    finally:
        browser.close()
        playwright.stop()


def discover(root: Path, broker: dict[str, Any], task: dict[str, Any] | None = None, headless: bool | None = None) -> list[dict[str, str]]:
    config = load_brokers(root)
    start_urls = broker.get("start_urls") or []
    if not broker.get("allowed_domains"):
        raise ValueError(f"{broker['id']} has no allowed_domains.")
    if not start_urls:
        raise ValueError(f"{broker['id']} has no start_urls.")

    playwright, browser, page = _open_context(root, broker, config, headless=headless)
    try:
        candidates: list[dict[str, str]] = []
        for url in start_urls:
            if not url_allowed(url, broker.get("allowed_domains", [])):
                raise ValueError(f"start_url is outside allowed_domains: {redact_url(url)}")
            page.goto(url, wait_until=broker.get("wait_until", "domcontentloaded"))
            page.wait_for_timeout(int(broker.get("wait_after_load_ms", 3000)))
            if broker.get("manual_login", True) and not _is_auth_success(page, broker):
                _wait_for_manual_login(page, broker, config)
            candidates.extend(_extract_candidates_from_page(page, broker, task))
        return candidates
    finally:
        browser.close()
        playwright.stop()


def fetch(
    root: Path,
    broker: dict[str, Any],
    task: dict[str, Any] | None = None,
    dry_run: bool = False,
    max_downloads: int | None = None,
    headless: bool | None = None,
) -> PortalResult:
    config = load_brokers(root)
    candidates = discover(root, broker, task, headless=headless)
    result = PortalResult(candidates=len(candidates))
    if dry_run:
        return result

    allowed_extensions = config.get("file_extensions", list(DOWNLOAD_EXTENSIONS))
    limit = max_downloads or int(task.get("max_downloads_per_portal", 0) if task else 0) or int(config.get("max_downloads_per_run", 50))
    manifest_file = manifest_path(root, config)
    manifest = load_manifest(manifest_file)

    playwright, browser, page = _open_context(root, broker, config, headless=headless)
    try:
        out_dir = root / "data" / "raw" / (task.get("id") if task else "manual") / broker["id"]
        for candidate in candidates[:limit]:
            href = candidate["url"]
            if not url_allowed(href, broker.get("allowed_domains", [])):
                result.errors += 1
                continue
            try:
                response = page.request.get(href, timeout=60000)
                if not response.ok:
                    result.errors += 1
                    continue
                content_type = response.headers.get("content-type", "")
                filename = _ensure_extension(_filename_from_headers(response.headers, href, candidate["title"]), content_type, href)
                if not _looks_like_download(response.headers, filename, allowed_extensions):
                    continue
                local_path = out_dir / safe_filename(filename)
                local_path.parent.mkdir(parents=True, exist_ok=True)
                local_path.write_bytes(response.body())
                added, _ = record_download(manifest, href, local_path, broker, candidate["title"], "download", candidate)
                if added:
                    result.downloaded += 1
                    print(f"[rph] downloaded {local_path}", flush=True)
                else:
                    result.skipped_duplicates += 1
            except Exception as exc:
                result.errors += 1
                print(f"[rph] failed to download {redact_url(href)}: {exc}", flush=True)
        save_manifest(manifest_file, manifest)
        return result
    finally:
        browser.close()
        playwright.stop()

