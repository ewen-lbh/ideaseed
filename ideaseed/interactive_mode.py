from github.AuthenticatedUser import AuthenticatedUser
from github.Membership import Membership
from github.Project import Project
from github.Repository import Repository
from ideaseed.utils import get_token_cache_filepath
import os
from typing import *
from github.MainClass import Github
import inquirer as q
import json
import ideaseed.github

# from ideaseed.github import find_project
import ideaseed.gkeep


def get_all_repos_full_names(gh: Github) -> List[str]:
    if os.path.exists(get_token_cache_filepath("interactive-mode")):
        with open(
            get_token_cache_filepath("interactive-mode"), encoding="utf8"
        ) as file:
            repos = json.load(file)["repos"]
        return repos

    names: List[str] = []
    for repo in gh.get_user().get_repos():
        if repo.archived:
            continue
        names += [repo.full_name]

    with open(
        get_token_cache_filepath("interactive-mode"), "w", encoding="utf8"
    ) as file:
        json.dump({"repos": names}, file)

    return names


# def get_all_columns_of_user(gh: Github, args: Dict[str, Any]) -> List[str]:
#     names: List[str] = []
#     project = find_project(gh, args, args['--user-project'])


def validate_repo_exists(gh: Github, name: str, username: str) -> bool:
    if "/" not in name:
        name = f"{username}/{name}"
    if name not in get_all_repos_full_names(gh):
        raise q.errors.ValidationError("", reason=f"Repository {name!r} not found")
        return False
    return True


def run(args: Dict[str, Any]):
    gh = ideaseed.github.login(args)
    username = gh.get_user().login

    def get_choices_question_project(ans: Dict[str, Any]) -> List[str]:
        if "/" not in ans["repo"]:
            ans["repo"] = username + "/" + ans["repo"]
        if ans["service"] == "Github project":
            ans["projects"] = gh.get_user(username).get_projects()
        else:
            ans["projects"] = gh.get_repo(ans["repo"]).get_projects()
        return [p.name for p in ans["projects"]]

    def get_choices_question_column(ans: Dict[str, Any]) -> List[str]:
        if "/" not in ans["repo"]:
            ans["repo"] = username + "/" + ans["repo"]

        project: Project = [p for p in ans["projects"] if p.name == ans["project"]][0]

        ans["columns"] = project.get_columns()
        return [c.name for c in ans["columns"]]

    questions = [
        q.List(
            "service",
            message="Where do you want to upload this idea?",
            choices=["GitHub repository", "Google Keep", "GitHub user profile"],
            default="Google Keep",
        ),
        q.Text(
            "repo",
            message="Choose a repository...",
            ignore=lambda ans: ans["service"] != "GitHub repository",
            validate=lambda _, current: validate_repo_exists(gh, current, username)
            # TODO: autocomplete (going to need a different library), q.List shits itself with so much items (I have >70 repos)
        ),
        q.Confirm(
            "create_issue",
            message="Create an issue?",
            ignore=lambda ans: ans["service"] != "GitHub repository",
        ),
        q.Text(
            "issue_title",
            message="Enter the issue's title (leave blank to use the idea as the title)",
            ignore=lambda ans: ans["create_issue"],
        ),
        q.List(
            "project",
            message="Choose a project",
            ignore=lambda ans: ans["service"] == "Google Keep",
            choices=get_choices_question_project,
        ),
        q.List(
            "column",
            ignore=lambda ans: ans["service"] == "Google Keep",
            choices=get_choices_question_column,
        ),
    ]

    q.prompt(questions)
