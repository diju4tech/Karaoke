from pathlib import Path


def test_frontend_has_required_elements():
    root = Path("frontend/index.html").read_text()
    assert "youtubeUrl" in root
    assert "startBtn" in root
    assert "stageList" in root
    assert "downloadLink" in root
