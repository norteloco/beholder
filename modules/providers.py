import re
from modules.logger import init_logger
from typing import Optional, Tuple

logger = init_logger(__name__)

# regular expressions
# during testing, the matching expressions for gitlab and github were almost identical
GITHUB_RE = re.compile(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)")
GITLAB_RE = re.compile(r"gitlab\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)")
DOCKER_RE = re.compile(r"hub\.docker\.com/(?:r/)?([^/]+)/([^/]+)(?:/|$)")

# provider configuration
PROVIDERS = {
    "github.com": {
        "name": "GitHub",
        "regex": GITHUB_RE,
        "url_fmt": "https://github.com/{namespace}/{repository}",
    },
    "gitlab.com": {
        "name": "GitLab",
        "regex": GITLAB_RE,
        "url_fmt": "https://gitlab.com/{namespace}/{repository}",
    },
    "hub.docker.com": {
        "name": "Docker Hub",
        "regex": DOCKER_RE,
        "url_fmt": "https://hub.docker.com/r/{namespace}/{repository}",
    },
}


def repository_detect(
    link: str,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Determines the repository provider by reference.
    Returns:
        provider, namespace, repository, full_name, url
    """

    link = link.strip().rstrip("/")
    for key, provider in PROVIDERS.items():
        if key in link:
            data = provider["regex"].search(link)
            if not data:
                continue

            namespace, repository = data.group(1), data.group(2).replace(".git", "")
            fullname = f"{namespace}/{repository}"
            url = provider["url_fmt"].format(namespace=namespace, repository=repository)

            logger.info(f'{provider["name"]} repository detected: {fullname}')
            return (provider["name"], namespace, repository, fullname, url)

    logger.warning(f"Unable to determine the provider for the link provided: {link}")
    return (None, None, None, None, link if "/" in link else None)
