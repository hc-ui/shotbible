from pathlib import Path

from shotbible.check import check_bible
from shotbible.store import save

from conftest import make_sample_bible, write_dummy_png


def test_check_rejects_relative_path_escape(tmp_path: Path) -> None:
    root = tmp_path / "escape"
    root.mkdir()
    outside = tmp_path / "outside.png"
    write_dummy_png(outside)
    bible = make_sample_bible(with_ref=False)
    bible.characters["mei"].refs = ["../outside.png"]
    save(root, bible)

    issues = check_bible(root, bible)
    assert any(getattr(issue, "code", None) == "MISSING_REF" for issue in issues)
