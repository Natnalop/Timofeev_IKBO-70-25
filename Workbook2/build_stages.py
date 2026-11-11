"""Обновление автономных снимков без перезаписи модульной структуры."""

from pathlib import Path
from shutil import copytree, ignore_patterns

ROOT = Path(__file__).resolve().parent


def copy_modular_stage():
    """Скопировать общую реализацию этапа 5 в автономную папку этапа 4."""
    source = ROOT / "stage5/src/apkgraph5"
    target = ROOT / "stage4/src/apkgraph4"
    copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=ignore_patterns("__pycache__"),
    )
    for module in target.glob("*.py"):
        text = module.read_text(encoding="utf-8")
        module.write_text(
            text.replace("для этапа 5", "для этапа 4"), encoding="utf-8"
        )
    wrapper = (ROOT / "stage5/depgraph.py").read_text(encoding="utf-8")
    wrapper = wrapper.replace("apkgraph5", "apkgraph4")
    wrapper = wrapper.replace("STAGE = 5", "STAGE = 4")
    wrapper = wrapper.replace("этапа 5", "этапа 4")
    (ROOT / "stage4/depgraph.py").write_text(wrapper, encoding="utf-8")


def main():
    """Обновить ранние снимки и код двух модульных этапов."""
    source = (ROOT / "stage3/depgraph.py").read_text(encoding="utf-8")
    for stage in (1, 2):
        text = source.replace("STAGE = 3", f"STAGE = {stage}")
        target = ROOT / f"stage{stage}/depgraph.py"
        target.write_text(text, encoding="utf-8")
    copy_modular_stage()


if __name__ == "__main__":
    main()
