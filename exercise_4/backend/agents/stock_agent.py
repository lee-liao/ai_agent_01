import os
from typing import Optional, Dict, List
import requests
from openai import OpenAI


def _require_env(name: str) -> str:
    val = os.getenv(name) 
    if not val:
        raise RuntimeError(f"Missing env: {name}")
    return val


def fetch_stock_price_from_alpha(symbol: str) -> Optional[Dict]:
    try:
        api = _require_env("ALPHA_VANTAGE_KEY")
    except RuntimeError:
        return None
    try:
        r = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        q = data.get("Global Quote") or data.get("GlobalQuote")
        if not q:
            return None
        price = float(q.get("05. price") or q.get("price"))
        change_pct = float(str(q.get("10. change percent") or "0").replace("%", ""))
        return {"symbol": symbol.upper(), "price": price, "change_percent": change_pct}
    except Exception:
        return None


def fetch_stock_price_from_yahoo(symbol: str) -> Optional[Dict]:
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        info = t.fast_info
        price = getattr(info, "last_price", None) if info is not None else None
        if price is None:
            price = (getattr(t, "info", {}) or {}).get("regularMarketPrice")
        change_pct = None
        try:
            hist = t.history(period="2d")
            if not hist.empty and len(hist["Close"]) >= 2:
                today = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2])
                if prev:
                    change_pct = ((today - prev) / prev) * 100.0
        except Exception:
            pass
        if price is None:
            return None
        return {"symbol": symbol.upper(), "price": float(price), "change_percent": float(change_pct or 0.0)}
    except Exception:
        return None

def fetch_stock_price(symbol: str) -> Optional[Dict]:
    return fetch_stock_price_from_alpha(symbol) or fetch_stock_price_from_yahoo(symbol)

def screen_symbols(symbols: List[str]) -> List[Dict]:
    out: List[Dict] = []
    for s in symbols:
        d = fetch_stock_price(s)
        if d:
            out.append(d)
    return out

def get_openai_client():
    api_key = _require_env("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)

def answer_question_with_llm(question: str, stocks: List[Dict]) -> str:
    """Answer an arbitrary question with optional stock context."""
    client = get_openai_client()

    stock_lines = [
        f"{s['symbol']}: Price={s['price']}, Change%={s['change_percent']}" for s in stocks
    ]
    stock_summary = "\n".join(stock_lines) if stocks else "(no context)"

    prompt = f"""You are a helpful stock assistant. You are not a financial advisor and you must not give financial advice.
Your role is to provide information and analysis based on the data provided.
If stock context is provided, use it. Otherwise, answer generally.

Context:
{stock_summary}

Question: {question}
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return completion.choices[0].message.content or ""



