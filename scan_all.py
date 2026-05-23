"""scan_all.py — Multi-source schema discovery.

Loops over sources defined in sources.yaml, runs scan_source per source,
and merges the outputs into one unified source_schema.{json,md}.

Usage:
    python scan_all.py
    python scan_all.py --config sources.yaml
    python scan_all.py --validate     # quick row-count + FK counts per source
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

import yaml

import scan_source

ROOT = Path(__file__).parent
DEFAULT_CONFIG = ROOT / "sources.yaml"
OUT_JSON = ROOT / "source_schema.json"
OUT_MD = ROOT / "source_schema.md"


def run_one_source(source_cfg: dict) -> list[scan_source.Table]:
    """Set env from cfg, then call the matching driver. Returns table list with name prefixed."""
    name = source_cfg["name"]
    src_type = source_cfg["type"]
    driver = scan_source.DRIVERS.get(src_type)
    if driver is None:
        raise SystemExit(f"Unknown source type '{src_type}' for source '{name}'. Available: {sorted(scan_source.DRIVERS)}")
    # Push env vars from cfg
    saved_env: dict[str, str | None] = {}
    for k, v in source_cfg.get("env", {}).items():
        saved_env[k] = os.environ.get(k)
        os.environ[k] = str(v)
    try:
        tables = driver()
    finally:
        # Restore env
        for k, prev in saved_env.items():
            if prev is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = prev
    # Prefix table names with source name for disambiguation
    for t in tables:
        t.name = f"{name}::{t.name}"
    return tables


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(DEFAULT_CONFIG), help="sources.yaml path")
    ap.add_argument("--validate", action="store_true", help="Skip md output, just print per-source counts")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        raise SystemExit(f"Config not found: {cfg_path}. Copy sources.yaml.example to sources.yaml and edit.")

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    sources = cfg.get("sources", [])
    if not sources:
        raise SystemExit(f"No `sources:` in {cfg_path}")

    print(f"Scanning {len(sources)} source(s)...")
    all_tables: list[scan_source.Table] = []
    for src in sources:
        print(f"\n[{src['name']}] type={src['type']}")
        try:
            tables = run_one_source(src)
            print(f"  -> {len(tables)} tables")
            all_tables.extend(tables)
        except Exception as e:
            print(f"  ERROR: {e}")
            if args.validate:
                continue
            raise

    # Cross-source FK detection (e.g. bc::Customers.No <-> crm::companies.bc_customer_number)
    scan_source.enrich(all_tables)

    if args.validate:
        in_scope = [t for t in all_tables if not t.skip_reason]
        fks = sum(1 for t in in_scope for c in t.columns if c.fk_hint)
        print(f"\nTotal: {len(in_scope)} tables in scope, {fks} FK candidates")
        return

    OUT_JSON.write_text(json.dumps([asdict(t) for t in all_tables], default=str, indent=2), encoding="utf-8")
    scan_source.write_md(all_tables)
    print(f"\nWrote {OUT_JSON.name} and {OUT_MD.name} -- {len(all_tables)} tables across {len(sources)} sources")


if __name__ == "__main__":
    main()
