
from pathlib import Path


class WorkspaceManager:
    """Safely manage generated files inside project workspaces."""

    def __init__(self, root_dir: str | Path = "workspaces"):
        self.root_dir = Path(root_dir).resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get_project_dir(self, project_id: int) -> Path:
        """Return the workspace directory for a valid project ID."""

        if isinstance(project_id, bool) or not isinstance(project_id, int):
            raise ValueError("Project ID must be a positive integer.")

        if project_id <= 0:
            raise ValueError("Project ID must be a positive integer.")

        project_dir = (self.root_dir / f"project_{project_id}").resolve()

        if not project_dir.is_relative_to(self.root_dir):
            raise ValueError("Project workspace path is invalid.")

        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def write_file(
        self,
        project_id: int,
        relative_path: str,
        content: str,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Write a file without allowing paths outside the project workspace."""

        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("File path cannot be empty.")

        if not isinstance(content, str):
            raise ValueError("File content must be a string.")

        requested_path = Path(relative_path)

        if requested_path.is_absolute() or requested_path.drive:
            raise ValueError("Absolute file paths are not allowed.")

        project_dir = self.get_project_dir(project_id)
        destination = (project_dir / requested_path).resolve()

        if not destination.is_relative_to(project_dir):
            raise ValueError("File path must remain inside the project workspace.")

        if destination == project_dir:
            raise ValueError("A file path is required.")

        if destination.exists() and destination.is_dir():
            raise ValueError("The destination is a directory.")

        if destination.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {relative_path}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        return destination
