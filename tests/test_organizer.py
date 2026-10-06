#!/usr/bin/env python3
"""
Tests for Smart File Organizer
"""
import tempfile
import shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from organizer import SmartFileOrganizer, FileInfo, CategoryConfig


def test_categorize_by_format():
    """Test format-based categorization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        organizer = SmartFileOrganizer(tmp)

        # Create test files
        (tmp / "test.jpg").write_bytes(b"fake jpg")
        (tmp / "test.png").write_bytes(b"fake png")
        (tmp / "test.pdf").write_bytes(b"fake pdf")
        (tmp / "test.mp4").write_bytes(b"fake mp4")
        (tmp / "test.mp3").write_bytes(b"fake mp3")
        (tmp / "test.zip").write_bytes(b"fake zip")
        (tmp / "test.exe").write_bytes(b"fake exe")
        (tmp / "test.py").write_bytes(b"print('hello')")
        (tmp / "unknown.xyz").write_bytes(b"unknown")

        organizer.scan_files()

        # Test categorization
        for f in organizer.files:
            cat = organizer.categorize_by_format(f)
            print(f"{f.path.name} -> {cat}")

        # Assertions
        jpg = next(f for f in organizer.files if f.path.name == "test.jpg")
        assert organizer.categorize_by_format(jpg) == "fotos"

        png = next(f for f in organizer.files if f.path.name == "test.png")
        assert organizer.categorize_by_format(png) == "fotos"

        pdf = next(f for f in organizer.files if f.path.name == "test.pdf")
        assert organizer.categorize_by_format(pdf) == "documentos"

        mp4 = next(f for f in organizer.files if f.path.name == "test.mp4")
        assert organizer.categorize_by_format(mp4) == "videos"

        mp3 = next(f for f in organizer.files if f.path.name == "test.mp3")
        assert organizer.categorize_by_format(mp3) == "audio"

        zipf = next(f for f in organizer.files if f.path.name == "test.zip")
        assert organizer.categorize_by_format(zipf) == "arquivos_compactados"

        exe = next(f for f in organizer.files if f.path.name == "test.exe")
        assert organizer.categorize_by_format(exe) == "executaveis"

        py = next(f for f in organizer.files if f.path.name == "test.py")
        assert organizer.categorize_by_format(py) == "codigo"

        unknown = next(f for f in organizer.files if f.path.name == "unknown.xyz")
        assert organizer.categorize_by_format(unknown) == "outros"

        print("✅ test_categorize_by_format passed")


def test_determine_final_category():
    """Test final category determination with semantic tags."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        organizer = SmartFileOrganizer(tmp)

        # Create a test file
        test_file = tmp / "family_photo.jpg"
        test_file.write_bytes(b"fake jpg")

        organizer.scan_files()
        f = organizer.files[0]

        # Simulate semantic analysis result
        f.metadata['main_category'] = 'fotos'
        f.metadata['subcategory'] = 'familia'

        final = organizer.determine_final_category(f)
        assert final == "fotos/familia", f"Expected fotos/familia, got {final}"

        # Test with unknown subcategory
        f.metadata['subcategory'] = 'inexistente'
        final = organizer.determine_final_category(f)
        assert final == "fotos", f"Expected fotos, got {final}"

        print("✅ test_determine_final_category passed")


def test_build_plan():
    """Test plan building."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        organizer = SmartFileOrganizer(tmp)

        # Create test files
        (tmp / "photo1.jpg").write_bytes(b"jpg1")
        (tmp / "photo2.png").write_bytes(b"png1")
        (tmp / "doc.pdf").write_bytes(b"pdf1")

        organizer.scan_files()
        for f in organizer.files:
            f.suggested_category = organizer.categorize_by_format(f)

        plan = organizer.build_plan()

        assert len(plan) == 2  # fotos and documentos
        assert str(tmp / "fotos") in plan
        assert str(tmp / "documentos") in plan
        assert len(plan[str(tmp / "fotos")]) == 2
        assert len(plan[str(tmp / "documentos")]) == 1

        print("✅ test_build_plan passed")


def test_file_hash():
    """Test file hashing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        organizer = SmartFileOrganizer(tmp)

        f1 = tmp / "a.txt"
        f2 = tmp / "b.txt"
        f1.write_text("same content")
        f2.write_text("same content")

        h1 = organizer.get_file_hash(f1)
        h2 = organizer.get_file_hash(f2)

        assert h1 == h2, "Same content should have same hash"

        f3 = tmp / "c.txt"
        f3.write_text("different content")
        h3 = organizer.get_file_hash(f3)

        assert h1 != h3, "Different content should have different hash"

        print("✅ test_file_hash passed")


def test_format_size():
    """Test size formatting."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        organizer = SmartFileOrganizer(tmp)

        assert organizer.format_size(500) == "500.0B"
        assert organizer.format_size(1024) == "1.0KB"
        assert organizer.format_size(1024 * 1024) == "1.0MB"
        assert organizer.format_size(1024 * 1024 * 1024) == "1.0GB"

        print("✅ test_format_size passed")


def test_config_save_load():
    """Test saving and loading custom config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        organizer = SmartFileOrganizer(tmp)

        config_path = tmp / "test_config.json"
        organizer.save_custom_config(config_path)

        # Verify it loads
        assert config_path.exists()

        # Load and verify structure
        import json
        with open(config_path) as f:
            loaded = json.load(f)

        assert "fotos" in loaded
        assert "videos" in loaded
        assert "documentos" in loaded
        assert "subcategories" in loaded["fotos"]

        print("✅ test_config_save_load passed")


def run_all_tests():
    """Run all tests."""
    print("Running tests...\n")
    test_categorize_by_format()
    test_determine_final_category()
    test_build_plan()
    test_file_hash()
    test_format_size()
    test_config_save_load()
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    run_all_tests()