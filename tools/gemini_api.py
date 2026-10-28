#!/usr/bin/env python3
"""Gemini API 共用呼叫（配音 Gemini TTS、配樂 Lyria 共用同一把金鑰）。

金鑰只從環境變數 GEMINI_API_KEY 讀取；沒有的話再讀專案根目錄的 .env（.env 不進版控）。
帳戶是預付制，餘額 0 時 API 會回 HTTP 402，要先到 AI Studio → Billing → Buy credits 儲值。
"""
import base64
import json
import os
import time
import urllib.error
import urllib.request

API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ApiError(RuntimeError):
    pass


def api_key():
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    env = os.path.join(ROOT, ".env")
    if not key and os.path.exists(env):
        for line in open(env, encoding="utf-8"):
            name, _, value = line.strip().partition("=")
            if name.strip() == "GEMINI_API_KEY":
                key = value.strip().strip('"').strip("'")
    if not key:
        raise ApiError("找不到 GEMINI_API_KEY：請設成環境變數，或寫進專案根目錄的 .env（不要寫進程式）")
    return key


def post(body, retries=3, timeout=300):
    """送出一次 interactions 請求，回傳解析後的 JSON；429／5xx 會自動重試。"""
    data = json.dumps(body).encode("utf-8")
    for attempt in range(retries + 1):
        req = urllib.request.Request(API_URL, data=data, method="POST", headers={
            "Content-Type": "application/json", "x-goog-api-key": api_key()})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            if e.code == 402:
                raise ApiError("HTTP 402：帳戶餘額不足，請到 AI Studio → Billing → Buy credits 儲值") from e
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
            raise ApiError(f"HTTP {e.code}：{detail}") from e
        except urllib.error.URLError as e:
            if attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
            raise ApiError(f"連線失敗：{e.reason}") from e


def find_audio(resp):
    """從回應的 steps[] 找 type=model_output，再從 content 找 type=audio，回傳 (bytes, mime)。"""
    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "audio" and node.get("data"):
                yield node
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)

    outputs = [s for s in resp.get("steps", []) if s.get("type") == "model_output"] or [resp]
    for step in outputs:
        for node in walk(step):
            mime = node.get("mime_type") or node.get("mimeType") or ""
            return base64.b64decode(node["data"]), mime
    raise ApiError("回應裡找不到音訊：" + json.dumps(resp, ensure_ascii=False)[:500])
