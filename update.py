"""Refresh the Pages dataset and write newly found links for editorial review."""
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


def request(url, headers=None):
    with urlopen(Request(url, headers=headers or {}), timeout=20) as response:
        return response.read()


def approved_notes(repository, token):
    issues = []
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    for page in range(1, 100):
        params = urlencode({"labels": "讀者投稿,已核准", "state": "all", "per_page": 100, "page": page})
        batch = json.loads(request(f"https://api.github.com/repos/{repository}/issues?{params}", headers))
        issues.extend(issue for issue in batch if "pull_request" not in issue)
        if len(batch) < 100:
            break
    return [
        {"title": item["title"].removeprefix("[讀者投稿]").strip(),
         "body": (item["body"] or "").partition("### 公開來源")[0].removeprefix("### 投稿內容").strip(),
         "url": item["html_url"]}
        for item in issues
    ]


def discover(key):
    if not key:
        return []
    queries = [(f'{region} "RYT200" 瑜珈 師資培訓', "") for region in
               ("台北 新北", "桃園 新竹", "台中 彰化", "台南 嘉義", "高雄 屏東", "宜蘭 花蓮 台東")]
    queries += [('台灣 "RYT200" 瑜珈 師資培訓', domain) for domain in
                ("site:threads.com", "site:threads.net", "site:facebook.com")]
    links = {}
    for query, domain in queries:
        params = urlencode({"q": f"{query} {domain}".strip(), "count": 10,
                            "country": "TW", "search_lang": "zh-hant"})
        payload = json.loads(request("https://api.search.brave.com/res/v1/web/search?" + params,
                                     {"X-Subscription-Token": key, "Accept": "application/json"}))
        for result in payload.get("web", {}).get("results", []):
            url = result["url"]
            if urlsplit(url).scheme == "https":
                links[url] = {"url": url, "query": query, "source_filter": domain}
    return list(links.values())


def main():
    path = Path("site/data.json")
    data = json.loads(path.read_text())
    repository = os.environ.get("GITHUB_REPOSITORY")
    if repository:
        data["community"] = approved_notes(repository, os.environ["GH_TOKEN"])
    data["refreshed"] = datetime.now(ZoneInfo("Asia/Taipei")).isoformat(timespec="minutes")
    review = {"official_pages": [], "search_links": [], "warnings": []}
    for url in dict.fromkeys(course["url"] for course in data["courses"]):
        try:
            digest = hashlib.sha256(request(url, {"User-Agent": "TaiwanRYT200/1.0"})).hexdigest()
            review["official_pages"].append({"url": url, "sha256": digest})
        except Exception as error:
            review["warnings"].append(f"{url}：{type(error).__name__}")
    if os.environ.get("BRAVE_SEARCH_API_KEY"):
        try:
            review["search_links"] = discover(os.environ["BRAVE_SEARCH_API_KEY"])
        except Exception as error:
            review["warnings"].append(f"搜尋失敗：{type(error).__name__}")
    else:
        review["warnings"].append("未設定 BRAVE_SEARCH_API_KEY")
    Path("review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2))
    for warning in review["warnings"]:
        print(warning, file=sys.stderr)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
