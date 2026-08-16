"""轻量冒烟测试：不依赖运行中的 TradingAgents-CN。"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml


def _write_cfg(tmp_path: Path, overrides: dict | None = None) -> Path:
    cfg = {
        "api": {"base_url": "http://localhost", "username": "admin", "password": "x"},
        "llm": {"base_url": "https://example/v4", "api_key": "k", "model": "m"},
        "cron": {"jobs": [{"name": "t", "schedule": "0 9 * * 1-5", "symbol": "000001"}]},
    }
    if overrides:
        for k, v in overrides.items():
            cfg.setdefault(k, {}).update(v)
    p = tmp_path / "studio.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def test_config_defaults_and_env_override(tmp_path, monkeypatch):
    from studio.core.config import Config

    cfg = Config.load(_write_cfg(tmp_path))
    assert cfg.get("api.username") == "admin"
    assert cfg.get("compare.defaults.depth") == "标准"  # 默认值生效
    monkeypatch.setenv("STUDIO__API__USERNAME", "bot")
    cfg2 = Config.load(_write_cfg(tmp_path))
    assert cfg2.get("api.username") == "bot"


def test_config_env_expansion(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_SECRET", "s3cret")
    p = _write_cfg(tmp_path)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    raw["api"]["password"] = "${MY_SECRET}"
    p.write_text(yaml.safe_dump(raw), encoding="utf-8")
    from studio.core.config import Config
    assert Config.load(p).get("api.password") == "s3cret"


def test_store_roundtrip(tmp_path):
    from studio.core.store import Store

    store = Store(tmp_path / "s.db")
    store.upsert_run("t1", symbol="002594", depth="标准", status="completed", wall_s=12.5)
    assert store.get_run("t1")["symbol"] == "002594"
    store.add_event("t1", "2026-01-01T00:00:00", "分析师", "市场分析师", "内容")
    assert len(store.events("t1")) == 1
    store.save_digest("t1", "002594", "m", 6000, "简报")
    store.close()


def test_sse_to_event():
    from studio.core.events import sse_to_event

    ev = sse_to_event("t1", {"event": "progress", "current_step": {"name": "📊 市场分析师"}, "progress": 42})
    assert ev is not None and ev.phase == "分析师" and ev.agent == "📊 市场分析师"


def test_feishu_sign_shape():
    """签名函数可调用且输出 base64 —— 不校验具体值（依赖时间戳）。"""
    from studio.notify.channels.feishu import _sign
    s = _sign("secret", 1700000000)
    assert isinstance(s, str) and len(s) > 10


def test_cron_expressions_valid():
    import croniter
    for expr in ["30 9 * * 1-5", "*/10 * * * *", "0 6 * * *"]:
        assert croniter.croniter.is_valid(expr)


def test_condenser_clips_long_input():
    from studio.digest.condenser import _clip
    text = "字" * 50000
    clipped = _clip(text)
    assert len(clipped) < 26000 and "省略" in clipped
