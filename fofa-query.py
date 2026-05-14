#!/usr/bin/env python3
"""
Thin FOFA-compatible client for fofoapi.com (third-party FOFA API).

Set one of:
  FOFOAPI_KEY  or  FOFA_KEY  — your fofoapi.com API key

Endpoints:
  /api/v1/search/all   — asset search
  /api/v1/search/stats — stats aggregation
  /api/v1/search/host  — host details
"""

import base64
import os
import sys

import requests

BASE_URL = "https://fofoapi.com"

# Known API error codes → English explanation (server may still return other text).
_API_CODE_HINTS_EN: dict[str, str] = {
    "-102": "Membership expired; renew your plan in the provider's web store.",
    "-400": "Invalid request parameters.",
    "-401": "Unauthorized (check your API key).",
    "-403": "Access denied for this operation.",
    "-700": "API or authentication error (verify your key and endpoint).",
    "-701": "Insufficient permission for this data.",
    "-702": "Search permission denied.",
    "-703": "No access to this dataset.",
    "-704": "Insufficient query quota or points.",
    "-710": "Syntax error in the search query.",
}


def _format_api_errmsg(errmsg: str) -> str:
    """Turn server errmsg (often ``[-NNN] ...``) into a clearer English line."""
    s = errmsg.strip()
    if s.startswith("[") and "]" in s:
        idx = s.index("]")
        code = s[1:idx].strip()
        tail = s[idx + 1 :].strip()
        hint = _API_CODE_HINTS_EN.get(code)
        if hint:
            return f"[{code}] {hint}"
        if tail:
            return f"[{code}] {tail}"
        return f"[{code}] Unknown error."
    return s


def _api_key() -> str:
    key = os.environ.get("FOFOAPI_KEY") or os.environ.get("FOFA_KEY")
    if not key or not key.strip():
        raise RuntimeError(
            "API key not set: export FOFOAPI_KEY='your_key' (or FOFA_KEY) and try again."
        )
    return key.strip()


def _encode_query(query: str) -> str:
    return base64.b64encode(query.encode()).decode()


def search(
    query: str,
    size: int = 100,
    page: int = 1,
    fields: str = "host,title,ip,port,protocol,domain",
    full: bool = False,
) -> dict:
    """
    Run a FOFA-style search.
    fields: host,title,ip,port,protocol,domain,server,country,city,os,lastupdatetime
    full=True returns full records where supported.
    """
    params = {
        "key": _api_key(),
        "qbase64": _encode_query(query),
        "size": min(size, 10000),
        "page": page,
        "fields": fields,
    }
    if full:
        params["full"] = "true"
    resp = requests.get(f"{BASE_URL}/api/v1/search/all", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raw = data.get("errmsg", "Unknown error")
        raise RuntimeError(_format_api_errmsg(str(raw)))
    return data


def search_all(
    query: str,
    size: int = 100,
    max_pages: int = 50,
    fields: str = "host,title,ip,port,protocol",
) -> list:
    """Fetch all pages up to max_pages."""
    results = []
    for page in range(1, max_pages + 1):
        data = search(query, size=size, page=page, fields=fields)
        items = data.get("results", [])
        if not items:
            break
        results.extend(items)
        if page * size >= data.get("size", 0):
            break
    return results


def stats(query: str) -> dict:
    """Stats aggregation."""
    params = {"key": _api_key(), "qbase64": _encode_query(query)}
    resp = requests.get(f"{BASE_URL}/api/v1/search/stats", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raw = data.get("errmsg", "Unknown error")
        raise RuntimeError(_format_api_errmsg(str(raw)))
    return data


def host(ip_or_domain: str, detail: bool = True) -> dict:
    """Host details (ports, products, certs, etc.)."""
    params = {"key": _api_key(), "host": ip_or_domain, "detail": "true" if detail else "false"}
    resp = requests.get(f"{BASE_URL}/api/v1/search/host", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raw = data.get("errmsg", "Unknown error")
        raise RuntimeError(_format_api_errmsg(str(raw)))
    return data


def fmt(data: dict) -> str:
    """Pretty-print search results."""
    lines = [
        f"Total: {data.get('size', 0)}, page {data.get('page', 1)}, "
        f"returned {len(data.get('results', []))} row(s)"
    ]
    lines.append("-" * 70)
    for row in data.get("results", []):
        lines.append(" | ".join(str(c) for c in row) if isinstance(row, list) else str(row))
    return "\n".join(lines)


def _cli_main() -> int:
    if len(sys.argv) < 2:
        print("Usage: fofoapi.py '<FOFA query>' [size]")
        print('Example: fofoapi.py \'app="Grafana" && country="CN"\' 20')
        print("Environment: export FOFOAPI_KEY='your_key'")
        return 1
    q = sys.argv[1]
    try:
        size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    except ValueError:
        print("Error: size must be an integer.", file=sys.stderr)
        return 1
    try:
        print(fmt(search(q, size=size)))
    except RuntimeError as e:
        print(f"API error: {e}", file=sys.stderr)
        return 2
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli_main())
