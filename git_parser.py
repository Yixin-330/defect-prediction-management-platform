import os
from git import Repo

def clone_and_parse_repo(repo_url: str, local_dir: str = "./cloned_repos"):
    # 1. 确保本地存放仓库的文件夹存在
    os.makedirs(local_dir, exist_ok=True)
    
    # 2. 从 URL 中提取仓库名，比如 https://github.com/xxx/MyRepo.git 提取出 MyRepo
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = os.path.join(local_dir, repo_name)

    # 3. 如果本地已经有这个仓库了，就拉取更新；没有就克隆
    if os.path.exists(repo_path):
        repo = Repo(repo_path)
        origin = repo.remotes.origin
        origin.pull()
    else:
        repo = Repo.clone_from(repo_url, repo_path)

    # 4. 读取提交历史
    commits = []
    for commit in repo.iter_commits():
        commits.append({
            "hash": commit.hexsha,
            "author": commit.author.name,
            "email": commit.author.email,
            "message": commit.message.strip(),
            "date": commit.committed_datetime.isoformat()
        })
        # 为了测试速度，我们先只取最近 50 条
        if len(commits) >= 50:
            break

    return commits