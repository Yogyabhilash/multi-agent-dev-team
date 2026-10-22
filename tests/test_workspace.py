
import pytest

from api.workspace import WorkspaceManager


def test_creates_project_workspace(tmp_path):
    manager = WorkspaceManager(tmp_path / "workspaces")

    project_dir = manager.get_project_dir(1)

    assert project_dir.is_dir()
    assert project_dir.name == "project_1"


def test_writes_file_inside_workspace(tmp_path):
    manager = WorkspaceManager(tmp_path / "workspaces")

    result = manager.write_file(1, "src/main.py", "print('Hello')")

    assert result.is_file()
    assert result.read_text(encoding="utf-8") == "print('Hello')"
    assert result.parent.name == "src"


@pytest.mark.parametrize("project_id", [0, -1, True, "1"])
def test_rejects_invalid_project_id(tmp_path, project_id):
    manager = WorkspaceManager(tmp_path / "workspaces")

    with pytest.raises(ValueError, match="Project ID"):
        manager.get_project_dir(project_id)


@pytest.mark.parametrize(
    "relative_path",
    [
        "../outside.txt",
        "..\\outside.txt",
        "",
        "   ",
        "/outside.txt",
        "C:\\outside.txt",
    ],
)
def test_rejects_unsafe_or_empty_paths(tmp_path, relative_path):
    manager = WorkspaceManager(tmp_path / "workspaces")

    with pytest.raises(ValueError):
        manager.write_file(1, relative_path, "unsafe")


def test_does_not_overwrite_existing_file_by_default(tmp_path):
    manager = WorkspaceManager(tmp_path / "workspaces")
    manager.write_file(1, "main.py", "original")

    with pytest.raises(FileExistsError):
        manager.write_file(1, "main.py", "replacement")

    assert (
        manager.get_project_dir(1) / "main.py"
    ).read_text(encoding="utf-8") == "original"


def test_allows_explicit_overwrite(tmp_path):
    manager = WorkspaceManager(tmp_path / "workspaces")
    manager.write_file(1, "main.py", "original")

    manager.write_file(1, "main.py", "updated", overwrite=True)

    assert (
        manager.get_project_dir(1) / "main.py"
    ).read_text(encoding="utf-8") == "updated"


def test_rejects_directory_as_file_destination(tmp_path):
    manager = WorkspaceManager(tmp_path / "workspaces")
    project_dir = manager.get_project_dir(1)
    (project_dir / "src").mkdir()

    with pytest.raises(ValueError, match="directory"):
        manager.write_file(1, "src", "content")
