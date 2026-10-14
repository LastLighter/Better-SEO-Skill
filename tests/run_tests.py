#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/run_tests.py — seo_audit.py 回归测试

零依赖，直接运行：

    python tests/run_tests.py

断言：
  1) fixtures/bad-page.html            必须检出 headings / image-alt / canvas-text 三项 FAIL
  2) assets/templates/*.html           必须 0 FAIL（正常模板不应被误报）
  3) assets/templates/react-components.tsx 必须 0 FAIL、0 WARN（组件片段按 N/A 处理）
  4) fixtures/bad-page.html 的 JSON 输出结构完整（summary + files[].checks）
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "seo_audit.py"
BAD = ROOT / "tests" / "fixtures" / "bad-page.html"
GOOD_HTML = ROOT / "assets" / "templates" / "head-and-structure.html"
GOOD_TSX = ROOT / "assets" / "templates" / "react-components.tsx"

failures: list[str] = []


def run(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  [PASS] {name}")
    else:
        print(f"  [FAIL] {name} {detail}")
        failures.append(name)


def main() -> int:
    print("seo_audit.py 回归测试")
    print("=" * 60)

    # 1) 反面样例必须被检出
    print("\n[1] 反面样例检出能力")
    code, out = run(str(BAD), "--json")
    check("退出码为 1（存在 FAIL）", code == 1, f"(实际 {code})")
    try:
        data = json.loads(out)
        checks = {c["name"]: c["status"] for c in data["files"][0]["checks"]}
        summary = data["summary"]
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        check("JSON 输出可解析且结构完整", False, f"({exc})")
        checks, summary = {}, {}

    check("JSON 输出可解析且结构完整", bool(checks) and "verdict" in summary)
    for expected in ("headings", "image-alt", "canvas-text"):
        check(f"检出 {expected} = FAIL", checks.get(expected) == "FAIL", f"(实际 {checks.get(expected)})")
    for expected in ("image-dimensions", "image-lazy", "image-format", "keyword-stuffing", "footer-matrix"):
        check(f"提示 {expected}", checks.get(expected) in ("WARN", "FAIL"), f"(实际 {checks.get(expected)})")

    # 2) 正面 HTML 模板不应有 FAIL
    print("\n[2] HTML 模板无误报")
    code, out = run(str(GOOD_HTML), "--json")
    data = json.loads(out)
    check("HTML 模板 0 FAIL", data["summary"]["checks"]["FAIL"] == 0,
          f"(FAIL={data['summary']['checks']['FAIL']})")
    check("HTML 模板退出码为 0", code == 0, f"(实际 {code})")

    # 3) 组件片段按 N/A 降级
    print("\n[3] 组件片段降级处理")
    code, out = run(str(GOOD_TSX), "--json")
    data = json.loads(out)
    check("TSX 片段 0 FAIL", data["summary"]["checks"]["FAIL"] == 0)
    check("TSX 片段 0 WARN", data["summary"]["checks"]["WARN"] == 0,
          f"(WARN={data['summary']['checks']['WARN']})")
    check("TSX 片段存在 N/A 项", data["summary"]["checks"]["NA"] > 0)
    check("TSX 片段退出码为 0", code == 0, f"(实际 {code})")

    # 4) 目录递归扫描
    print("\n[4] 目录递归扫描")
    code, out = run(str(ROOT / "assets"), "--quiet")
    check("目录参数可递归扫描", "个文件" in out and "can't find" not in out, f"({out.strip()[:80]})")

    print("\n" + "=" * 60)
    if failures:
        print(f"结果：{len(failures)} 项失败 -> " + "；".join(failures))
        return 1
    print("结果：全部通过 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
