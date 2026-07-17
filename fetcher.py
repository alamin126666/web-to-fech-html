import re
import requests
from Crypto.Cipher import AES


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


# ── Anti-bot: AES cookie challenge (slowAES pattern) ──────────────────────────

def _solve_aes_challenge(html: str) -> str | None:
    """
    Detects the slowAES cookie challenge used by some DDoS-protection layers.
    Pattern looks like:
      var a=toNumbers("KEY"),b=toNumbers("IV"),c=toNumbers("CT");
      document.cookie="__test="+toHex(slowAES.decrypt(c,2,a,b))+...
    Returns the decrypted hex cookie value, or None if not detected.
    """
    pattern = (
        r'var\s+a\s*=\s*toNumbers\("([0-9a-f]+)"\)\s*,'
        r'\s*b\s*=\s*toNumbers\("([0-9a-f]+)"\)\s*,'
        r'\s*c\s*=\s*toNumbers\("([0-9a-f]+)"\)'
    )
    m = re.search(pattern, html)
    if not m:
        return None
    key = bytes.fromhex(m.group(1))
    iv  = bytes.fromhex(m.group(2))
    ct  = bytes.fromhex(m.group(3))
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = cipher.decrypt(ct)
    return pt.hex()


# ── Anti-bot: meta-refresh redirect ───────────────────────────────────────────

def _follow_meta_refresh(html: str, base_url: str) -> str | None:
    """Returns redirect URL from <meta http-equiv='refresh'> if present."""
    m = re.search(
        r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\'][^"\']*url=([^"\'>\s]+)',
        html, re.IGNORECASE
    )
    if m:
        loc = m.group(1).strip()
        if loc.startswith("http"):
            return loc
        from urllib.parse import urljoin
        return urljoin(base_url, loc)
    return None


# ── Main fetch function ────────────────────────────────────────────────────────

def fetch_html(url: str) -> tuple[str, str]:
    """
    Fetches the real HTML from a URL, solving common anti-bot challenges.

    Returns:
        (html_content: str, suggested_filename: str)

    Raises:
        ValueError: if fetching fails or content is unrecognisable.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    # ── Attempt 1: plain GET ──────────────────────────────────────────────────
    resp = session.get(url, timeout=30, allow_redirects=True)
    resp.raise_for_status()
    html = resp.text

    # ── Check: AES cookie challenge ───────────────────────────────────────────
    cookie_val = _solve_aes_challenge(html)
    if cookie_val:
        session.cookies.set("__test", cookie_val, domain=_domain(url))
        retry_url = _append_param(url, "i", "1")
        resp = session.get(retry_url, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
        # Second layer could be another challenge — try once more
        cookie_val2 = _solve_aes_challenge(html)
        if cookie_val2:
            session.cookies.set("__test", cookie_val2, domain=_domain(url))
            resp = session.get(retry_url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            html = resp.text

    # ── Check: meta-refresh redirect ──────────────────────────────────────────
    redirect = _follow_meta_refresh(html, resp.url)
    if redirect and redirect != url:
        resp2 = session.get(redirect, timeout=30, allow_redirects=True)
        resp2.raise_for_status()
        html = resp2.text

    # ── Check: still looks like a JS challenge page? ──────────────────────────
    if _is_challenge_page(html):
        raise ValueError(
            "⚠️ This site uses an advanced bot-protection system "
            "(e.g. Cloudflare JS Challenge) that cannot be solved without a real browser. "
            "Try fetching from a browser and sharing the HTML manually."
        )

    filename = _make_filename(url)
    return html, filename


# ── Helpers ───────────────────────────────────────────────────────────────────

def _domain(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).netloc


def _append_param(url: str, key: str, value: str) -> str:
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{key}={value}"


def _is_challenge_page(html: str) -> bool:
    """Heuristic: page is almost entirely JS with no real body content."""
    lower = html.lower()
    challenge_signals = [
        "checking your browser",
        "enable javascript",
        "cf-browser-verification",
        "just a moment",
        "ddos-guard",
        "_cf_chl_opt",
    ]
    return any(sig in lower for sig in challenge_signals)


def _make_filename(url: str) -> str:
    from urllib.parse import urlparse
    path = urlparse(url).path.rstrip("/")
    name = path.split("/")[-1] if path else "index"
    if not name.endswith(".html"):
        name += ".html"
    return name or "page.html"
