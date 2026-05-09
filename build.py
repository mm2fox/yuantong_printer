import subprocess
import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

def find_git():
    git_path = shutil.which("git")
    if git_path:
        return git_path
    common_paths = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe"),
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    return None

GIT_PATH = find_git()

def run_git(args):
    if not GIT_PATH:
        return ""
    try:
        result = subprocess.run(
            [GIT_PATH] + args,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return result.stdout.strip()
    except Exception:
        return ""

def get_git_info():
    commit = run_git(["rev-parse", "HEAD"])
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    author = run_git(["log", "-1", "--format=%an"])
    message = run_git(["log", "-1", "--format=%s"])
    date = run_git(["log", "-1", "--format=%ai"])
    return {
        "git_commit": commit,
        "git_branch": branch,
        "git_author": author,
        "git_message": message,
        "git_date": date,
    }

def get_change_summary():
    last_tag = run_git(["describe", "--tags", "--abbrev=0"])
    if not last_tag:
        last_tag = run_git(["rev-list", "--max-parents=0", "HEAD"])

    if last_tag:
        log = run_git(["log", f"{last_tag}..HEAD", "--oneline"])
    else:
        log = run_git(["log", "-10", "--oneline"])

    return log

def has_changes():
    status = run_git(["status", "--porcelain"])
    return bool(status.strip())

def main():
    print("=" * 50)
    print("收集构建信息...")
    print("=" * 50)

    git_info = get_git_info()

    if not git_info["git_commit"]:
        print("警告: 未检测到 git 仓库，将使用默认值")
        git_info = {
            "git_commit": "unknown",
            "git_branch": "unknown",
            "git_author": "unknown",
            "git_message": "unknown",
            "git_date": "unknown",
        }

    change_summary = get_change_summary()
    version = run_git(["describe", "--tags", "--always"])
    if not version:
        version = datetime.now().strftime("%Y%m%d.%H%M")

    build_info = {
        **git_info,
        "version": version,
        "build_time": datetime.now().isoformat(),
        "change_summary": change_summary,
    }

    output_path = PROJECT_ROOT / "build_info.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(build_info, f, ensure_ascii=False, indent=2)

    print(f"版本号: {version}")
    print(f"Git Commit: {git_info['git_commit'][:8] if git_info['git_commit'] != 'unknown' else 'unknown'}")
    print(f"Git Branch: {git_info['git_branch']}")
    print(f"Git Author: {git_info['git_author']}")
    print(f"Git Message: {git_info['git_message']}")
    print(f"Git Date: {git_info['git_date']}")
    print(f"变更摘要:\n{change_summary}")
    print(f"\n构建信息已保存到: {output_path}")

    return build_info

if __name__ == "__main__":
    main()
