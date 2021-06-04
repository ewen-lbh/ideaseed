import subprocess
from ideaseed.github_cards import Idea

def using() -> bool:
    """
    Tries to subprocess.run `git bug`.
    If status code is non-zero, assume git-bug is not installed.
    Tries to subprocess.run `git bug user ls`
    If stdout is empty, no user is configured, thus the repo does not use git bug.
    """

    return (
        _run_command([]).returncode == 0
        and _run_command(['user', 'ls'], check=True).stdout != ""
    )

def create(idea: Idea) -> str:
    """
    Creates a git bug. Returns its short sha.
    """
    # TODO: set subprocess.run's cwd to add git bug when not in corresponding git repo.
    # this 
    short_sha = _run_command(['add', '--title', idea.title, '--message', idea.body]).stdout.replace(' created', '')

    # Add label
    _run_command(['label', short_sha, 'add', *idea.labels])

    return short_sha


def _run_command(cmd_args, *args, **kwargs):
    if 'check' not in kwargs:
        kwargs['check'] = True
    
    return subprocess.run(['git', 'bug'] + cmd_args, cwd= *args, **kwargs)
