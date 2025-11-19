import requests, base64
from urllib.parse import urlparse

class GitHubRepository:
    """
    Represents a GitHub repository and provides methods to interact with
    its contents via the GitHub REST API. 
    """
    def __init__(self, repo_url: str, token: str | None = None):
        """
        Initialize a GitHubRepository instance.

        Args:
            repo_url (str): Full GitHub repository URL, e.g. "https://github.com/user/repo"
            token (str, optional): A GitHub Personal Access Token (PAT) for higher rate limits.
        """
        self.repo_url = repo_url.rstrip("/") # Normalize the URL (remove trailing slash)
        self.owner, self.repo_name = self._parse_repo_url(repo_url)
        self.api_base = f"https://api.github.com/repos/{self.owner}/{self.repo_name}"

        # Initialize a persistent session
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/vnd.github.v3+json"})
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})


    def _parse_repo_url(self, repo_url: str) -> tuple[str, str]:
        """
        Extract the owner and repo name from the GitHub URL.

        Args:
            repo_url (str): The GitHub repository URL.
    
        Returns:
            tuple[str, str]: A tuple containing (owner, repo_name).
        
        Raises:
            ValueError: If the URL is not in a valid GitHub repo format.
        """
        path_parts = urlparse(repo_url).path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub repository URL. Expected format: https://github.com/<owner>/<repo>")
        return path_parts[0], path_parts[1]



    def get_files(self):
        """
        Fetch all files (recursively) from the repository and return their names,
        paths, and contents.

        Returns:
            list[dict]: A list of file metadata with structure:
                {
                    "name": str,     # filename
                    "path": str,     # file path in repo
                    "content": str   # raw file content
                }

        Raises:
            Exception: If any API call fails.
        """
        files = []

        def add_to_list(content_item: dict):
            """
            Fetch the actual content of a file and append it to the results list.

            For each file, fetch content (Base64 encoded) from GitHub API
            """
            file_resp = self.session.get(content_item.get('url'))
            if file_resp.status_code != 200:
                raise Exception(f"Failed to fetch content for {content_item.get('path')}: {file_resp.status_code}")
        
            data = file_resp.json()
            if data.get("encoding") == "base64":
                decoded_content = base64.b64decode(data.get('content')).decode("utf-8", errors="ignore")
            else:
                decoded_content = data.get("content", "")
            
            files.append({
                "name": content_item.get('name'),
                "path": content_item.get('path'),
                "content": decoded_content
            })

        # Recursively process all files and directories
        self._process_content_items(add_to_list)
        return files


    def _process_content_items(self, handle_content_item, content_path=""):
        """
        Recursively process content items in the repository.

        Args:
            handle_content_item (callable): Function that takes a content item dict
                and handles it (e.g. adds it to a list).
            content_path (str, optional): Subdirectory path within the repo.
                Defaults to the repo root.

        Raises:
            Exception: If an API request fails.
        """
        baseurl = f"{self.api_base}/contents"
        url = f"{baseurl}/{content_path}"

        # Fetch directory contents from GitHub API
        response = self.session.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to list filepaths: {response.status_code} - {response.text}")
        
        contents = response.json()

        # GitHub API returns a single dict if the path is a file, not a list
        if isinstance(contents, dict):
            contents = [contents]

        # Iterate over all items (files or directories)
        for content in contents:
            if content.get('type') == 'file':
                handle_content_item(content)
            elif content.get('type') == 'dir':
                self._process_content_items(handle_content_item, content.get('path'),)


    def get_repo_details(self):
        """
        Fetch general repository metadata such as name, description, stars, forks, etc.

        Returns:
            dict: Repository metadata as returned by the GitHub API.

        Raises:
            Exception: If the API request fails.
        """
        response = self.session.get(self.api_base)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repository details: {response.status_code} - {response.text}")
        return response.json()

    def __repr__(self):
        """Human-readable representation of the repository instance."""
        return f"<GitHubRepository {self.owner}/{self.repo_name}>"