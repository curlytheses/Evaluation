import json
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass
class GeminiJsonProvider:
    api_key: str
    temperature: float = 0.0

    def complete_json(self, model: str, prompt: str) -> dict:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?"
            + urllib.parse.urlencode({"key": self.api_key})
        )
        payload = json.dumps(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": self.temperature,
                    "responseMimeType": "application/json",
                },
            }
        ).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST", headers={"content-type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        text = raw["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text or "{}")
