"""Organizers' hosted CONCH service. Call ONLY from within Delta.

Verified against ncsa/ashby-hackathon-2026/example_student_usage.py.
"""
import base64
import os
import time
import requests
import numpy as np


class HostedConchClient:
    def __init__(self):
        self.endpoint = os.environ.get("CONCH_ENDPOINT", "").rstrip("/")
        self.api_key = os.environ.get("CONCH_API_KEY", "")
        if not self.endpoint or not self.api_key or "REPLACE" in self.endpoint or "REPLACE" in self.api_key:
            raise ValueError("Set CONCH_ENDPOINT and CONCH_API_KEY from #compute-issues. See .env.example")
        self.session = requests.Session()

    def health(self):
        r = self.session.get(f"{self.endpoint}/health", timeout=15)
        r.raise_for_status()
        info = r.json()
        if "conch" not in str(info.get("model", "")).lower():
            raise RuntimeError(f"Endpoint is not CONCH: {info}")
        return info

    def embed_paths(self, paths, retries=4):
        images = [base64.b64encode(open(p, "rb").read()).decode("ascii") for p in paths]
        for attempt in range(retries):
            try:
                r = self.session.post(
                    f"{self.endpoint}/embed",
                    json={"images": images},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=120,
                )
                if r.status_code in (401, 403):
                    raise RuntimeError(f"Access denied ({r.status_code}). Check organizer API key and individual CONCH approval.")
                r.raise_for_status()
                payload = r.json()
                vectors = np.asarray(payload["embeddings"], dtype=np.float32)
                if vectors.ndim != 2 or vectors.shape[0] != len(paths) or not np.isfinite(vectors).all():
                    raise ValueError("Unexpected /embed response shape or non-finite values")
                norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                if np.any(norms < 1e-12):
                    raise ValueError("Server returned zero-length embedding")
                return vectors / norms
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError):
                if attempt == retries - 1:
                    raise
                time.sleep(min(2 ** attempt, 8))
