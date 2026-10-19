#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gh_search.py — 动手前先查 GitHub 有没有现成成熟方案

用途：在任何任务开始前，先搜 GitHub 找现成的开源项目，避免重复造轮子。
凭据自动从本机读取，无需每次手动传 token。

用法:
    python scripts/gh_search.py "lyrics video generator"
    python scripts/gh_search.py "capcut draft" "auto subtitle video"
    python scripts/gh_search.py "xxx" --min-stars 2000   # 只显示 star 数达标(成熟)的项目
    python scripts/gh_search.py "xxx" --limit 10

凭据来源优先级: 环境变量 GITHUB_TOKEN > ~/.git-credentials
代理来源优先级: git config http.https://github.com.proxy > 环境变量 HTTPS_PROXY
"""
import sys
import json
import os
import re
import subprocess
import urllib.request
import urllib.parse
import urllib.error

API = "https://api.github.com/search/repositories"


def get_token():
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok.strip()
    cred = os.path.expanduser("~/.git-credentials")
    if os.path.exists(cred):
        with open(cred, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = re.search(r"https?://([^:\s]+):([^@\s]+)@github\.com", line)
                if m:
                    return m.group(2)
    return None


def get_proxy():
    try:
        p = subprocess.check_output(
            ["git", "config", "--global", "--get", "http.https://github.com.proxy"],
            text=True, stderr=subprocess.DEVNULL).strip()
        if p:
            return p
    except Exception:
        pass
    return os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")


def fmt_stars(n):
    if n >= 1000:
        return "%.1fk" % (n / 1000.0)
    return str(n)


def search(query, limit=5, min_stars=None):
    token = get_token()
    if not token:
        print("[错误] 没找到 GitHub token。请确认 ~/.git-credentials 有内容，或设置环境变量 GITHUB_TOKEN")
        return None
    proxy = get_proxy()
    opener_args = []
    if proxy:
        opener_args.append(urllib.request.ProxyHandler({"https": proxy, "http": proxy}))
    opener = urllib.request.build_opener(*opener_args)

    params = {"q": query, "sort": "stars", "order": "desc", "per_page": str(limit * 3)}
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "minyao-ip-search")

    try:
        with opener.open(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        print("[GitHub 返回 %d] %s" % (e.code, body[:200]))
        return None
    except Exception as e:
        print("[网络错误] %s  (是否忘了开 Clash 代理?)" % e)
        return None

    items = data.get("items", [])
    if min_stars is not None:
        items = [r for r in items if r.get("stargazers_count", 0) >= min_stars]
    items = items[:limit]

    print("=" * 64)
    print("查询: %s" % query)
    print("GitHub 共找到 %s 个仓库  (显示前 %d，按 star 排序)" % (
        "{:,}".format(data.get("total_count", 0)), len(items)))
    print("=" * 64)
    if not items:
        print("  没有符合条件的结果。")
        return None
    for i, r in enumerate(items, 1):
        name = r.get("full_name", "?")
        stars = r.get("stargazers_count", 0)
        pushed = (r.get("pushed_at") or "")[:10]
        desc = (r.get("description") or "").strip().replace("\n", " ")
        lang = r.get("language") or "-"
        lic = (r.get("license") or {}).get("spdx_id") or "无 license"
        arch = "  [已归档,停止维护]" if r.get("archived") else ""
        print("%d. %s   ★ %s   lang=%s   license=%s   更新于 %s%s" % (
            i, name, fmt_stars(stars), lang, lic, pushed, arch))
        print("   %s" % r.get("html_url", ""))
        if desc:
            print("   %s" % desc[:120])
        print()
    return items


def main():
    args = [a for a in sys.argv[1:]]
    limit = 5
    min_stars = None
    queries = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1]); i += 2; continue
        if a == "--min-stars" and i + 1 < len(args):
            min_stars = int(args[i + 1]); i += 2; continue
        queries.append(a); i += 1
    if not queries:
        print(__doc__)
        return
    for q in queries:
        search(q, limit=limit, min_stars=min_stars)


if __name__ == "__main__":
    main()
