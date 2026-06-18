#!/usr/bin/env python3
"""check-mermaid.py — 用真实 mermaid 引擎校验每个 ```mermaid 代码块。

为什么需要它:`mkdocs build --strict` 抓不到 mermaid 语法错误 —— mermaid 在
**浏览器端**渲染,mkdocs 只是把围栏代码原样嵌进页面。所以一个语法错误的图
能构建通过、却在页面上显示 "Syntax error in text"(见 mermaid v11)。本脚本
把每个 ```mermaid 块抽出来,交给 mermaid-cli(mmdc,与站点同一引擎/语法)解析,
任意一个块解析失败就退出非零,从而在 CI 里拦住坏图。

用法:
  python3 scripts/check-mermaid.py [路径...]      # 默认扫描全仓 *.md
依赖:
  PATH 上的 `mmdc`(`npm i -g @mermaid-js/mermaid-cli@11.15.0`),或可用的 `npx`。
  CI 里固定安装 @mermaid-js/mermaid-cli@11.15.0(= 站点 mermaid 大版本)。
退出码: 0 全部通过 / 1 有坏图或(CI 中)缺少 mmdc。
"""
import os, re, sys, json, shutil, tempfile, subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCLUDE_DIRS = {"site", "node_modules", ".git", ".worktrees", ".refactor-loop"}
# 围栏:```mermaid 起,到下一行单独的 ``` 止(非贪婪)。
FENCE = re.compile(r"(?ms)^```mermaid[^\n]*\n(.*?)^```[ \t]*$")


def find_md(paths):
    out = []
    for p in paths:
        if os.path.isfile(p) and p.endswith(".md"):
            out.append(p)
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                out += [os.path.join(root, f) for f in files if f.endswith(".md")]
    return sorted(set(out))


def mmdc_cmd():
    if shutil.which("mmdc"):
        return ["mmdc"]
    if shutil.which("npx"):
        return ["npx", "-y", "@mermaid-js/mermaid-cli@11.15.0"]
    return None


def main():
    files = find_md(sys.argv[1:] or [REPO])
    cmd = mmdc_cmd()
    if not cmd:
        msg = "check-mermaid: 找不到 mmdc/npx —— 请 `npm i -g @mermaid-js/mermaid-cli@11.15.0`"
        if os.environ.get("CI") == "true":
            print(msg, file=sys.stderr)
            sys.exit(1)
        print(msg + "  [本地无 Node:跳过]", file=sys.stderr)
        sys.exit(0)

    tmp = tempfile.mkdtemp(prefix="mmdc-")
    pcfg = os.path.join(tmp, "puppeteer.json")
    with open(pcfg, "w") as fh:
        json.dump({"args": ["--no-sandbox", "--disable-gpu"]}, fh)

    nblocks = 0
    failures = []
    for f in files:
        text = open(f, encoding="utf-8").read()
        if "```mermaid" not in text:
            continue
        for m in FENCE.finditer(text):
            nblocks += 1
            startline = text[: m.start()].count("\n") + 1
            src = os.path.join(tmp, f"b{nblocks}.mmd")
            with open(src, "w") as fh:
                fh.write(m.group(1))
            r = subprocess.run(
                cmd + ["-i", src, "-o", os.path.join(tmp, f"b{nblocks}.svg"),
                       "-p", pcfg, "-q"],
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                failures.append((f, startline, (r.stderr or r.stdout).strip()))

    shutil.rmtree(tmp, ignore_errors=True)
    rel = lambda p: os.path.relpath(p, REPO)

    if failures:
        print(f"\ncheck-mermaid: FAILED — {len(failures)}/{nblocks} 个 mermaid 块语法错误\n",
              file=sys.stderr)
        for f, ln, err in failures:
            print(f"  ✗ {rel(f)}:{ln}", file=sys.stderr)
            shown = [l for l in err.splitlines()
                     if re.search(r"error|expect|parse|exception|unknown", l, re.I)]
            for line in (shown or err.splitlines()[-12:]):
                print(f"      {line.strip()}", file=sys.stderr)
            print(file=sys.stderr)
        sys.exit(1)

    print(f"check-mermaid: OK — {nblocks} 个 mermaid 块全部解析通过(共 {len(files)} 个文件)")


if __name__ == "__main__":
    main()
