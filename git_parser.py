import os
import logging
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)

def clone_and_parse_repo(repo_url: str, local_dir: str = "./cloned_repos"):
    # 1. 确保本地存放仓库的文件夹存在
    os.makedirs(local_dir, exist_ok=True)
    
    # 2. 从 URL 中提取仓库名，比如 https://github.com/xxx/MyRepo.git 提取出 MyRepo
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = os.path.join(local_dir, repo_name)

    # 3. 如果本地已经有这个仓库了，就拉取更新；没有就克隆
    if os.path.exists(repo_path):
        repo = Repo(repo_path)
        # 本地已有仓库：尝试 pull 更新，失败则降级使用本地版本，避免网络问题阻断解析
        try:
            repo.remotes.origin.pull()
        except GitCommandError as e:
            logger.warning("git pull 失败，降级使用本地已有仓库: %s", e)
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

def get_commit_diff(repo_url: str, commit_hash: str):
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = os.path.join("./cloned_repos", repo_name)
    if not os.path.exists(repo_path):
        return "仓库本地不存在，请先克隆"
    try:
        repo = Repo(repo_path)
        commit = repo.commit(commit_hash)
        # 获取该提交与其父提交的 diff
        if commit.parents:
            diff = commit.parents[0].diff(commit, create_patch=True)
            # 返回第一个文件的 diff 文本内容
            return diff[0].diff.decode('utf-8') if diff else "无差异内容"
        return "初始提交，无父节点差异"
    except Exception as e:
        return f"获取 diff 失败: {str(e)}"