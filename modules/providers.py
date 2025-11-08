import re

from aiohttp import ClientSession
from typing import Optional, Tuple, Type
from abc import ABC, abstractmethod
from urllib.parse import quote_plus

from modules.logger import init_logger

logger = init_logger(__name__)

# regular expressions
# during testing, the matching expressions for gitlab and github were almost identical
# GITHUB_RE = re.compile(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)")
# GITLAB_RE = re.compile(r"gitlab\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)")
# DOCKER_RE = re.compile(r"hub\.docker\.com/(?:r/)?([^/]+)/([^/]+)(?:/|$)")

# to detect only numbered versions in Docker Hub like v1.25.3 or 1.25.3 etc.
SEMVER = re.compile(r"^v?(\d+)\.(\d+)(?:\.(\d+))?(?:[-+][\w.]+)?$")


# providers configuration
class Provider(ABC):
    """Base provider class."""

    name: str
    regex: re.Pattern[str]
    url_fmt: str
    url_api: str

    registry: list[Type["Provider"]] = []

    def __init_subclass__(cls, **kwargs):
        """Automatically registers all children."""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "regex") and cls.regex:
            Provider.registry.append(cls)

    @abstractmethod
    async def fetch_latest(
        self, session: ClientSession, namespace: str, repository: str
    ) -> Optional[str] | None:
        """Returns the latest release version or tag."""
        pass

    @classmethod
    def repository_detect(
        cls, link: str
    ) -> Tuple[
        Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]
    ]:
        """
        Determines the repository provider by reference.
        Returns:
            provider, namespace, repository, fullname, url
        """

        link = link.strip().rstrip("/")
        for provider in Provider.registry:
            match = provider.regex.search(link)
            if match:
                namespace, repository = match.group(1), match.group(2).replace(
                    ".git", ""
                )
                fullname = f"{namespace}/{repository}"
                url = provider.url_fmt.format(
                    namespace=namespace, repository=repository
                )
                logger.info(f"{provider.name} repository detected: {fullname}")
                return provider.name, namespace, repository, fullname, url
        logger.warning(
            f"Unable to determine the provider for the link provided: {link}"
        )
        return (None, None, None, None, link if "/" in link else None)


class GitHubProvider(Provider):
    name = "GitHub"
    regex = re.compile(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)")
    url_fmt = "https://github.com/{namespace}/{repository}"
    url_api = "https://api.github.com/repos"

    async def fetch_latest(
        self, session: ClientSession, namespace: str, repository: str
    ) -> str | None:
        headers = {"User-Agent": "repo-watchtower"}
        url_release = f"{self.url_api}/{namespace}/{repository}/releases/latest"

        # trying to get releases first
        releases = await fetch_json(session, url_release, headers)
        if releases:
            return releases.get("tag_name") or releases.get("name")  # type: ignore

        # if there are no releases, trying to get tags
        url_tags = f"{self.url_api}/{namespace}/{repository}/tags"
        tags = await fetch_json(session, url_tags, headers)
        if tags and isinstance(tags, list):
            return tags[0].get("name")

        return None


class GitLabProvider(Provider):
    name = "GitLab"
    regex = re.compile(r"gitlab\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)")
    url_fmt = "https://gitlab.com/{namespace}/{repository}"
    url_api = "https://gitlab.com/api/v4/projects"

    async def fetch_latest(
        self, session: ClientSession, namespace: str, repository: str
    ) -> str | None:
        path = quote_plus(f"{namespace}/{repository}")
        url = f"{self.url_api}/{path}/repository/tags"

        tags = await fetch_json(session, url)
        if tags and isinstance(tags, list):
            return tags[0].get("name")

        return None


class DockerHubProvider(Provider):
    name = "Docker Hub"
    regex = re.compile(r"hub\.docker\.com/(?:r/)?([^/]+)/([^/]+)(?:/|$)")
    url_fmt = "https://hub.docker.com/r/{namespace}/{repository}"
    url_api = "https://hub.docker.com/v2/repositories"

    async def fetch_latest(
        self, session: ClientSession, namespace: str, repository: str
    ) -> str | None:
        if namespace in {"_", "", None}:
            namespace = "library"

        url = f"{self.url_api}/{namespace}/{repository}/tags?page_size=10&ordering=last_updated"
        data = await fetch_json(session, url)
        if not data:
            return None

        results = data.get("results", [])  # type: ignore
        if not results:
            return None

        tags = [r["name"] for r in results if r.get("name")]
        semver_tags = filter_semver(tags)
        return semver_tags[0] if semver_tags else tags[0]


async def fetch_json(
    session: ClientSession, url: str, headers: dict | None = None
) -> dict | list | None:
    """
    A general-purpose method for securely requesting JSON.
    """
    try:
        async with session.get(url, headers=headers) as request:
            if request.status == 200:
                return await request.json()
            logger.warning(
                f"Request to URL {url} failed with status [{request.status}]"
            )
            return None
    except Exception as e:
        logger.exception(f"Request error for URL {url}: {e}")
        return None


# tag filtering
def filter_semver(tags: list[str]) -> list[str]:
    """
    Filters and sorts tags by semantic version.
    """
    semver_tags = [t for t in tags if SEMVER.match(t)]
    return sorted(
        semver_tags,
        key=lambda t: [int(x) for x in re.findall(r"\d+", t)],
        reverse=True,
    )
