#!/usr/bin/env python3
"""Gemini API 共用呼叫（配音 Gemini TTS、配樂 Lyria 共用同一把金鑰）。

金鑰只從環境變數 GEMINI_API_KEY 讀取；沒有的話再讀專案根目錄的 .env（.env 不進版控）。
雲端環境用「網路密鑰」時，金鑰由網路代理在連到 generativelanguage.googleapis.com 時自動加上
（header x-goog-api-key），程式讀不到金鑰是正常的，照樣送出即可。
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
    return key  # 空字串：交給網路代理加金鑰


def post(body, retries=3, timeout=300):
    """送出一次 interactions 請求，回傳解析後的 JSON；429／5xx 會自動重試。"""
    data = json.dumps(body).encode("utf-8")
    for attempt in range(retries + 1):
        headers = {"Content-Type": "application/json"}
        if api_key():
            headers["x-goog-api-key"] = api_key()
        req = urllib.request.Request(API_URL, data=data, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            if e.code == 402:
                raise ApiError("HTTP 402：帳戶餘額不足，請到 AI Studio → Billing → Buy credits 儲值") from e
            if e.code == 403 and "unregistered callers" in detail:
                raise ApiError("HTTP 403：請求沒有帶到金鑰。請設定環境變數 GEMINI_API_KEY、專案根目錄的 .env，"
                               "或雲端環境的網路密鑰（主機 generativelanguage.googleapis.com、"
                               "header x-goog-api-key）") from e
            if e.code == 429 and "limit: 0" in detail:
                raise ApiError("HTTP 429：免費額度不能用這個模型（每天 0 次）。請到 AI Studio 的 API 金鑰列表，"
                               "按「Set up billing」設定付款並儲值") from e
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
