import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class TokenStats:
    layer: str
    role: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
    model_provider: str

    def __str__(self) -> str:
        return (
            f"[{self.layer}] role={self.role} | "
            f"model={self.model} ({self.model_provider}) | "
            f"in={self.input_tokens} / out={self.output_tokens} / total={self.total_tokens}"
        )


class TokenCounter:
    def __init__(self) -> None:
        self._registry: list[TokenStats] = []

    def add(self, layer: str, role: str, response: dict[str, Any]) -> TokenStats:
        raw = response.get("raw")
        if raw is None:
            raise ValueError("response musi zawierać klucz 'raw' z obiektem AIMessage.")

        metadata: dict = getattr(raw, "response_metadata", {}) or {}
        usage: dict    = getattr(raw, "usage_metadata",   {}) or {}

        input_tokens  = _first(usage.get("input_tokens"),  metadata.get("prompt_eval_count"), 0)
        output_tokens = _first(usage.get("output_tokens"), metadata.get("eval_count"),        0)
        total_tokens  = _first(usage.get("total_tokens"),  input_tokens + output_tokens)

        stats = TokenStats(
            layer=layer,
            role=role,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            total_tokens=int(total_tokens),
            model=metadata.get("model_name") or metadata.get("model", "unknown"),
            model_provider=metadata.get("model_provider", "unknown"),
        )

        self._registry.append(stats)
        return stats


    def summary(self) -> dict[str, int]:
        return self._aggregate(self._registry)

    def summary_by_layer(self) -> dict[str, dict[str, int]]:
        layers: dict[str, list[TokenStats]] = {}
        for s in self._registry:
            layers.setdefault(s.layer, []).append(s)
        return {layer: self._aggregate(stats) for layer, stats in layers.items()}

    def _aggregate(self, stats: list[TokenStats]) -> dict[str, int]:
        return {
            "input_tokens":  sum(s.input_tokens  for s in stats),
            "output_tokens": sum(s.output_tokens for s in stats),
            "total_tokens":  sum(s.total_tokens  for s in stats),
            "calls":         len(stats),
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps([asdict(s) for s in self._registry], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self, path: str | Path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for entry in data:
            self._registry.append(TokenStats(**entry))

    def reset(self) -> None:
        self._registry.clear()

    def __len__(self) -> int:
        return len(self._registry)

    def __repr__(self) -> str:
        s = self.summary()
        return (
            f"TokenCounter(calls={s['calls']}, "
            f"in={s['input_tokens']}, out={s['output_tokens']}, total={s['total_tokens']})"
        )
    


tokens_counter = TokenCounter()

def _first(*values):
    for v in values:
        if v is not None:
            return v
    return None

