#!/usr/bin/env python3
"""
DrillBit Academic Dual-Compliance Verifier v2 (Third-Person Academic Edition)
Audits text against DrillBit, Turnitin, & ShodhShuddhi inspection standards:
1. Strict Third-Person Perspective Audit (Absolute Zero 'I', 'we', 'our', etc.)
2. Academic Tampering & Fraud Detection (Homoglyphs, Zero-width characters)
3. Structural & Statistical Markers (Burstiness CV > 0.45, 3-25 Cadence Rule)
4. Academic Cliché, Sequential Markers & Hallmark Phrasing Audit
5. Absolute Dash Enforcement (Strictly 0 em/en dashes)
6. Markdown Pipe Table Avoidance (Auto-intercepts pipe tables that trigger 100% AI flags)
7. Dual-Engine Live ZeroGPT Verification (Direct Ultra-Fast API ~1.2s + Headless Playwright Fallback)
"""

import sys
import os
import re
import math
import json
import asyncio
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Strict First-Person Pronoun Filter (Mandatory Third-Person Compliance)
FIRST_PERSON_PATTERNS = [
    (r"\bI\b", "I"),
    (r"\bme\b", "me"),
    (r"\bmy\b", "my"),
    (r"\bmine\b", "mine"),
    (r"\bmyself\b", "myself"),
    (r"\bwe\b", "we"),
    (r"\bus\b", "us"),
    (r"\bour\b", "our"),
    (r"\bours\b", "ours"),
    (r"\bourselves\b", "ourselves")
]

# Academic hallmark phrases heavily flagged by DrillBit & Turnitin
DRILLBIT_AI_CLICHES = [
    r"\bdelve into\b", r"\btapestry of\b", r"\btestament to\b", r"\bpivotal role\b",
    r"\bunderscores the\b", r"\bserves as a\b", r"\bstands as a\b", r"\bparamount importance\b",
    r"\bholistic approach\b", r"\bnavigating the complexities\b", r"\bmultifaceted nature\b",
    r"\bvibrant\b", r"\bat its core\b", r"\bin reality\b", r"\bwhat really matters\b",
    r"\bnot only .* but also\b", r"\bit is crucial to note\b", r"\bit is important to remember\b",
    r"\bmarked by a profound\b", r"\bplays a vital role\b", r"\bfosters a\b", r"\binterplay between\b",
    r"\bmoreover\b", r"\bfurthermore\b", r"\bin conclusion\b"
]

SEQUENTIAL_MARKERS = [
    r"\bfirst,\b", r"\bsecondly,\b", r"\bthirdly,\b", r"\bnext,\b",
    r"\bfrom there,\b", r"\bsubsequently,\b", r"\bthereafter,\b"
]

# Common Cyrillic homoglyphs swapped for Latin letters (DrillBit explicitly flags this as fraud)
HOMOGLYPH_MAP = {
    '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
    '\u0441': 'c', '\u0443': 'y', '\u0445': 'x', '\u0456': 'i',
    '\u0410': 'A', '\u0412': 'B', '\u0415': 'E', '\u041e': 'O',
    '\u0420': 'P', '\u0421': 'C', '\u0422': 'T', '\u0425': 'X'
}

INVISIBLE_CHARS = [
    '\u200b', '\u200c', '\u200d', '\ufeff', '\u00a0', '\u200e', '\u200f'
]

def split_sentences(text: str) -> List[str]:
    raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw_sentences if len(s.strip()) > 3]

def audit_academic_integrity(text: str) -> Dict[str, Any]:
    """Audits document for perspective, tampering, burstiness, clichés, sequential markers, pipe tables, and punctuation rules."""
    issues = []
    warnings = []

    # 1. Perspective Audit: 100% Third-Person (Zero First-Person Pronouns)
    found_first_person = []
    for pattern, name in FIRST_PERSON_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            found_first_person.extend([name] * len(matches))
    
    if found_first_person:
        unique_fp = list(set(found_first_person))
        issues.append(
            f"CRITICAL: Found {len(found_first_person)} first-person pronoun occurrence(s) ({', '.join(unique_fp)}). "
            f"drillbit-humanizer-v2 strictly enforces a 100% objective third-person student voice. Remove all 'I', 'we', 'our'."
        )

    # 2. Tampering & Character Manipulation Audit
    homoglyphs_found = []
    for char in text:
        if char in HOMOGLYPH_MAP:
            homoglyphs_found.append(f"Cyrillic '{char}' (looks like '{HOMOGLYPH_MAP[char]}')")
    
    invisibles_found = []
    for char in text:
        if char in INVISIBLE_CHARS:
            invisibles_found.append(f"Unicode {hex(ord(char))}")

    if homoglyphs_found:
        issues.append(f"CRITICAL: Found {len(homoglyphs_found)} homoglyphs. DrillBit flags this as Character Manipulation Fraud!")
    if invisibles_found:
        issues.append(f"CRITICAL: Found {len(invisibles_found)} zero-width/invisible characters. DrillBit flags this as Document Tampering!")

    # 3. Dash Audit (Rule: Absolute Zero em/en dashes)
    em_dashes = text.count('—')
    en_dashes = text.count('–')
    total_dashes = em_dashes + en_dashes
    if total_dashes > 0:
        issues.append(f"CRITICAL: Found {em_dashes} em-dashes and {en_dashes} en-dashes. High-weight AI signature across DrillBit and Turnitin. Replace with commas, colons, or periods.")

    # 4. AI Hallmark Clichés & Sequential Markers Audit
    found_cliches = []
    text_lower = text.lower()
    for pattern in DRILLBIT_AI_CLICHES:
        matches = re.findall(pattern, text_lower)
        if matches:
            found_cliches.extend(matches)
    
    found_seq = []
    for pat in SEQUENTIAL_MARKERS:
        if re.search(pat, text_lower):
            found_seq.append(pat.replace(r"\b", ""))

    if found_cliches:
        issues.append(f"Found {len(found_cliches)} AI hallmark phrases: {list(set(found_cliches))}")
    if found_seq:
        warnings.append(f"Sequential discourse markers detected ({', '.join(found_seq)}). These trigger ZeroGPT/DrillBit sequence flags.")

    # 5. Markdown Pipe Table Detection
    pipe_lines = [line for line in text.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(pipe_lines) >= 2:
        warnings.append(
            f"Markdown pipe table detected ({len(pipe_lines)} pipe lines). "
            "ZeroGPT/DrillBit penalizes markdown pipe tables (| col | col |) at up to 100% AI, "
            "contaminating surrounding text. Convert to plain tab-aligned text or narrative comparisons."
        )

    # 6. Statistical Burstiness & Cadence (3-25 Rule)
    sentences = split_sentences(text)
    total_words = len(text.split())

    if not sentences or total_words == 0:
        return {
            "academic_passed": False,
            "error": "Document too short or empty.",
            "issues": ["Document too short or empty."]
        }

    lengths = [len(s.split()) for s in sentences]
    mean_len = sum(lengths) / len(lengths)
    variance = sum((x - mean_len) ** 2 for x in lengths) / len(lengths)
    std_dev = math.sqrt(variance)
    cv = std_dev / (mean_len + 1e-6)

    # Human academic writing exhibits CV >= 0.45. LLMs typically have CV < 0.35.
    if cv < 0.45:
        warnings.append(f"Low sentence burstiness (CV: {cv:.2f} < 0.45, Mean: {mean_len:.1f} words). Sentences are too uniform in length; apply the 3-25 rule: alternate 2-5 word punchy statements with 25-35 word complex sentences.")

    # Continuous Span / Monotony Audit (N-gram continuous length)
    long_sentences = [s for s in sentences if len(s.split()) > 45]
    if long_sentences:
        warnings.append(f"Found {len(long_sentences)} excessively long continuous sentences (> 45 words without periods). Risk of run-on or unreadable academic structure.")

    academic_passed = (
        (len(issues) == 0) and 
        not homoglyphs_found and 
        not invisibles_found and 
        (total_dashes == 0) and 
        (len(found_first_person) == 0)
    )

    return {
        "academic_passed": academic_passed,
        "first_person_count": len(found_first_person),
        "first_person_detected": len(found_first_person) > 0,
        "total_words": total_words,
        "sentence_count": len(sentences),
        "mean_sentence_length": round(mean_len, 1),
        "burstiness_cv": round(cv, 2),
        "em_dash_count": total_dashes,
        "cliches_found": list(set(found_cliches)),
        "sequential_markers_found": found_seq,
        "pipe_table_detected": len(pipe_lines) >= 2,
        "tampering_detected": bool(homoglyphs_found or invisibles_found),
        "critical_issues": issues,
        "quality_warnings": warnings
    }

async def run_fast_api_detect(text: str, timeout_seconds: float = 12.0) -> Optional[Dict[str, Any]]:
    """Ultra-fast direct HTTP API check against ZeroGPT (~800ms - 1.5s)."""
    try:
        import httpx
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Origin": "https://www.zerogpt.com",
            "Referer": "https://www.zerogpt.com/",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        payload = {"input_text": text.strip()}
        async with httpx.AsyncClient(headers=headers, timeout=timeout_seconds, follow_redirects=True) as client:
            resp = await client.post("https://api.zerogpt.com/api/detect/detectText", json=payload)
            if resp.status_code == 200:
                res_json = resp.json()
                if res_json.get("success"):
                    data = res_json.get("data", {})
                    fake_pct = float(data.get("fakePercentage", 0.0))
                    flagged = data.get("h", [])
                    total_words = data.get("textWords", len(text.split()))
                    ai_words = data.get("aiWords", 0)
                    return {
                        "live_verified": True,
                        "ai_score_percent": round(fake_pct, 1),
                        "is_below_10": fake_pct < 10.0,
                        "verdict": data.get("feedback", "Human Written" if fake_pct < 10.0 else "AI Detected"),
                        "ai_words": ai_words,
                        "flagged_sentences": flagged,
                        "engine": "live_zerogpt_api",
                        "latency_mode": "ultra_fast_api"
                    }
    except Exception:
        pass
    return None

async def _single_playwright_attempt(text: str, timeout_ms: int = 30000) -> Optional[Dict[str, Any]]:
    """Executes live headless Playwright check against ZeroGPT with ad/tracker route-blocking."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None

    detected_data = {}
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu"
                ]
            )
            try:
                page = await browser.new_page(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800}
                )

                await page.route(
                    re.compile(r"(\.png|\.jpg|\.jpeg|\.gif|\.webp|\.woff|\.ttf|google-analytics|doubleclick|criteo|amazon-adsystem|googlesyndication|adservice|quantserve|taboola|outbrain)"),
                    lambda route: route.abort()
                )

                async def handle_response(response):
                    nonlocal detected_data
                    if "detectText" in response.url:
                        try:
                            res_json = await response.json()
                            if res_json.get("success"):
                                detected_data = res_json.get("data", {})
                        except Exception:
                            pass

                page.on("response", handle_response)
                await page.goto("https://www.zerogpt.com/", wait_until="domcontentloaded", timeout=timeout_ms)

                textarea = await page.wait_for_selector("textarea", timeout=12000)
                await page.evaluate("""() => {
                    const ta = document.querySelector('textarea');
                    if (ta) {
                        ta.value = '';
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                        ta.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }""")
                await textarea.fill(text)

                btn = await page.wait_for_selector("button:has-text('Detect Text')", timeout=8000)
                await btn.click()

                for _ in range(40):
                    if detected_data:
                        break
                    await page.wait_for_timeout(400)

                return detected_data if detected_data else None

            finally:
                await browser.close()
    except Exception:
        return None

async def run_live_zerogpt(text: str, retries: int = 2, timeout_sec: int = 30) -> Dict[str, Any]:
    """Dual-engine ZeroGPT check: Fast HTTP API first (~1.2s), Playwright browser fallback if blocked."""
    # 1. Primary: Fast HTTP API (~800ms - 1.5s)
    api_res = await run_fast_api_detect(text, timeout_seconds=12.0)
    if api_res and api_res.get("live_verified"):
        return api_res

    # 2. Fallback: Headless Playwright browser
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            detected_data = await _single_playwright_attempt(text, timeout_ms=timeout_sec * 1000)
            if detected_data:
                fake_pct = float(detected_data.get("fakePercentage", 0.0))
                flagged = detected_data.get("h", [])
                ai_words = detected_data.get("aiWords", 0)

                return {
                    "live_verified": True,
                    "ai_score_percent": round(fake_pct, 1),
                    "is_below_10": fake_pct < 10.0,
                    "verdict": detected_data.get("feedback", "Completed"),
                    "ai_words": ai_words,
                    "flagged_sentences": flagged,
                    "engine": "live_zerogpt_browser",
                    "latency_mode": "browser_fallback",
                    "attempt": attempt
                }
        except Exception as e:
            last_error = str(e)
            if attempt < retries:
                await asyncio.sleep(2)

    return {
        "live_verified": False,
        "error": f"Live ZeroGPT verification failed across dual engines: {last_error or 'No response captured'}",
        "is_below_10": False
    }

def audit_document(text: str, live_zerogpt: bool = False, timeout_sec: int = 30) -> Dict[str, Any]:
    academic_audit = audit_academic_integrity(text)
    
    result = {
        "compliant": False,
        "academic_audit_passed": academic_audit.get("academic_passed", False),
        "first_person_detected": academic_audit.get("first_person_detected", False),
        "first_person_count": academic_audit.get("first_person_count", 0),
        "live_zerogpt_verified": False,
        "zerogpt_score_percent": None,
        "zerogpt_verdict": None,
        "zerogpt_ai_words": None,
        "zerogpt_flagged_sentences": [],
        "burstiness_cv": academic_audit.get("burstiness_cv"),
        "mean_sentence_length": academic_audit.get("mean_sentence_length"),
        "total_words": academic_audit.get("total_words"),
        "sentence_count": academic_audit.get("sentence_count"),
        "em_dash_count": academic_audit.get("em_dash_count", 0),
        "cliches_found": academic_audit.get("cliches_found", []),
        "sequential_markers_found": academic_audit.get("sequential_markers_found", []),
        "pipe_table_detected": academic_audit.get("pipe_table_detected", False),
        "tampering_detected": academic_audit.get("tampering_detected", False),
        "critical_issues": list(academic_audit.get("critical_issues", [])),
        "quality_warnings": list(academic_audit.get("quality_warnings", []))
    }

    if live_zerogpt:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                zg_res = pool.submit(asyncio.run, run_live_zerogpt(text, timeout_sec=timeout_sec)).result()
        else:
            zg_res = asyncio.run(run_live_zerogpt(text, timeout_sec=timeout_sec))
        result["live_zerogpt_verified"] = zg_res.get("live_verified", False)
        
        if zg_res.get("live_verified"):
            fake_pct = zg_res.get("ai_score_percent", 100.0)
            result["zerogpt_score_percent"] = fake_pct
            result["zerogpt_verdict"] = zg_res.get("verdict")
            result["zerogpt_ai_words"] = zg_res.get("ai_words")
            result["zerogpt_flagged_sentences"] = zg_res.get("flagged_sentences", [])
            result["engine_used"] = zg_res.get("engine", "live_zerogpt")
            result["latency_mode"] = zg_res.get("latency_mode", "unknown")
            
            # Dual Compliance: DrillBit Academic rules (including 0 first person) AND Live ZeroGPT < 10%
            is_compliant = (
                academic_audit.get("academic_passed", False) and 
                (fake_pct < 10.0) and 
                (academic_audit.get("em_dash_count", 0) == 0) and
                not academic_audit.get("tampering_detected", False) and
                not academic_audit.get("first_person_detected", False)
            )
            result["compliant"] = is_compliant
            if fake_pct >= 10.0:
                result["critical_issues"].append(f"AI Score {fake_pct}% exceeds 10% threshold on live ZeroGPT. Apply radical n-gram shattering on flagged sentences.")
        else:
            # Under Zero-False-Pass policy: If live check fails, CANNOT certify compliance!
            result["compliant"] = False
            result["zerogpt_score_percent"] = None
            result["critical_issues"].append(f"CRITICAL: {zg_res.get('error', 'Live ZeroGPT verification failed')}. Heuristic fallback is blocked under the Zero-False-Pass policy.")
    else:
        # Offline heuristic proxy estimate (clearly flagged as unverified)
        result["quality_warnings"].append("Live ZeroGPT check was not requested (--live-zerogpt). AI score is unverified by live detector.")
        fp_penalty = 50.0 if academic_audit.get("first_person_detected", False) else 0.0
        cliche_penalty = min(len(academic_audit.get("cliches_found", [])) * 8.0, 40.0)
        cv = academic_audit.get("burstiness_cv", 0.5)
        burst_penalty = 35.0 if cv < 0.25 else (20.0 if cv < 0.40 else (5.0 if cv < 0.50 else 0.0))
        dash_penalty = min(academic_audit.get("em_dash_count", 0) * 10.0, 25.0)
        tamper_penalty = 50.0 if academic_audit.get("tampering_detected", False) else 0.0
        pipe_penalty = 40.0 if academic_audit.get("pipe_table_detected", False) else 0.0
        heuristic_score = round(max(2.0, min(99.0, fp_penalty + cliche_penalty + burst_penalty + dash_penalty + tamper_penalty + pipe_penalty)), 1)
        result["heuristic_ai_estimate"] = heuristic_score
        result["compliant"] = academic_audit.get("academic_passed", False) and (heuristic_score < 10.0)

    return result

def main():
    parser = argparse.ArgumentParser(description="DrillBit Academic Dual-Compliance Verifier v2 (Third-Person Edition)")
    parser.add_argument("--file", type=str, help="Path to text or markdown file to audit")
    parser.add_argument("--text", type=str, help="Raw text string to audit")
    parser.add_argument("--live-zerogpt", action="store_true", help="Execute live ZeroGPT verification (< 10%% mandatory)")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds for live ZeroGPT check (default: 30s)")
    args = parser.parse_args()

    content = ""
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    elif args.text:
        content = args.text
    else:
        if not sys.stdin.isatty():
            content = sys.stdin.read()

    content = content.strip()
    if not content:
        print(json.dumps({
            "compliant": False,
            "error": "No content provided. Pass --file or --text."
        }, indent=2))
        sys.exit(1)

    result = audit_document(content, live_zerogpt=args.live_zerogpt, timeout_sec=args.timeout)
    print(json.dumps(result, indent=2))

    # Exit code: 0 if compliant, 2 if non-compliant or live verification failed
    if not result.get("compliant"):
        sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
