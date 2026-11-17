"""更新已核准投稿、課程列表與搜尋候選清單。"""
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


def request_json(url, headers=None):
    req = Request(url, headers=headers or {})
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def read_fields(body):
    matches = re.findall(
        r"^### ([^\n]+)\n+([\s\S]*?)(?=^### |\Z)",
        body or "",
        re.MULTILINE,
    )
    return {
        label.strip(): value.strip()
        for label, value in matches
        if value.strip() != "_No response_"
    }


def approved_submissions(repository, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    results = []
    page = 1
    while True:
        params = urlencode({
            "labels": "讀者投稿,已核准",
            "state": "all",
            "per_page": 100,
            "page": page,
        })
        batch = request_json(
            f"https://api.github.com/repos/{repository}/issues?{params}",
            headers,
        )
        results.extend(
            item for item in batch if "pull_request" not in item
        )
        if len(batch) < 100:
            break
        page += 1
    return results


def submission_course(issue, fields):
    labels = {
        "name": "課程名稱",
        "city": "縣市",
        "place": "上課地點",
        "schedule": "開課時間",
        "url": "公開來源",
    }
    course = {
        key: fields.get(label, "").strip()
        for key, label in labels.items()
    }
    if not all(course.values()):
        return None
    url = urlsplit(course["url"])
    if url.scheme != "https" or not url.hostname:
        return None
    course["city"] = course["city"].replace("台", "臺")
    return {
        "id": f"reader-{issue['number']}",
        "origin": "reader",
        "submission_url": issue["html_url"],
        **course,
    }


def discover(key):
    queries = [
        f'{region} "RYT200" 瑜珈 師資培訓'
        for region in (
            "台北 新北", "桃園 新竹", "台中 彰化",
            "台南 嘉義", "高雄 屏東", "宜蘭 花蓮 台東",
        )
    ]
    queries += [
        f'台灣 "RYT200" 瑜珈 師資培訓 site:{domain}'
        for domain in (
            "threads.com", "threads.net", "facebook.com"
        )
    ]
    links = {}
    warnings = []
    for query in queries:
        params = urlencode({
            "q": query,
            "count": 10,
            "country": "TW",
            "search_lang": "zh-hant",
        })
        try:
            payload = request_json(
                "https://api.search.brave.com/res/v1/web/search?"
                + params,
                {
                    "X-Subscription-Token": key,
                    "Accept": "application/json",
                },
            )
            for result in payload.get("web", {}).get("results", []):
                url = result.get("url", "")
                if urlsplit(url).scheme == "https":
                    links[url] = {
                        "title": result.get("title", ""),
                        "url": url,
                        "description": result.get("description", ""),
                        "query": query,
                    }
        except Exception as error:
            warnings.append(
                f"搜尋失敗：{query}：{type(error).__name__}"
            )
        time.sleep(1.1)
    return list(links.values()), warnings


def main():
    root = Path(__file__).resolve().parent
    path = root / "data.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    repository = os.environ.get("GITHUB_REPOSITORY")
    review = {
        "search_links": [],
        "warnings": [],
        "submission_warnings": [],
    }

    if repository:
        issues = approved_submissions(
            repository, os.environ["GH_TOKEN"]
        )
        courses = [
            course for course in data["courses"]
            if course.get("origin") != "reader"
        ]
        known_urls = {
            course["url"].rstrip("/") for course in courses
        }
        notes = []

        for issue in issues:
            fields = read_fields(issue.get("body"))
            notes.append({
                "title": issue["title"].removeprefix(
                    "[讀者投稿]"
                ).strip(),
                "body": fields.get("投稿內容", ""),
                "url": issue["html_url"],
            })
            course = submission_course(issue, fields)
            if course:
                url = course["url"].rstrip("/")
                if url not in known_urls:
                    courses.append(course)
                    known_urls.add(url)
            elif fields.get("課程名稱"):
                review["submission_warnings"].append({
                    "url": issue["html_url"],
                    "reason": "課程欄位不完整或公告網址不是 HTTPS",
                })

        data["courses"] = courses
        data["community"] = notes

    key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if key:
        links, warnings = discover(key)
        review["search_links"] = links
        review["warnings"].extend(warnings)
    else:
        review["warnings"].append(
            "未設定 BRAVE_SEARCH_API_KEY，略過自動搜尋；"
            "投稿同步仍正常執行。"
        )

    data["refreshed"] = datetime.now(
        ZoneInfo("Asia/Taipei")
    ).isoformat(timespec="minutes")

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "review.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"更新完成：{len(data['courses'])} 筆課程，"
        f"{len(data.get('community', []))} 筆投稿。"
    )
    for warning in review["warnings"]:
        print(warning)


if __name__ == "__main__":
    main()
