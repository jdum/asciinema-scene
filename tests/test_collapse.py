from asciinema_scene.scenelib.collapse import detect_collapse_regions
from asciinema_scene.scenelib.constants import PRECISION
from asciinema_scene.scenelib.frame import Frame


def _make_frame(timecode: float, duration: float, text: str) -> Frame:
    """Create a frame with explicit timecode and duration."""
    frame = Frame()
    frame.timecode = round(timecode * PRECISION)
    frame.duration = round(duration * PRECISION)
    frame.tpe = "o"
    frame.text = text
    return frame


def test_detect_no_similar_frames() -> None:
    """Frames with completely different content produce no regions."""
    # Each line fills most of the 80-col width so consecutive frames
    # differ by well over the 5% threshold on an 80x24 screen.
    line_a = "A" * 78 + "\n"
    line_b = "B" * 78 + "\n"
    line_c = "C" * 78 + "\n"
    frames = [
        _make_frame(0.0, 1.0, line_a * 12),
        _make_frame(1.0, 1.0, line_b * 12),
        _make_frame(2.0, 1.0, line_c * 12),
    ]
    regions = detect_collapse_regions(frames, cols=80, rows=24)
    assert regions == []


def test_detect_identical_frames() -> None:
    """Identical consecutive frames form a collapse region."""
    frames = [
        _make_frame(0.0, 1.0, "\rloading..."),
        _make_frame(1.0, 1.0, "\rloading..."),
        _make_frame(2.0, 1.0, "\rloading..."),
        _make_frame(3.0, 1.0, "\rloading..."),
    ]
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=2.0,
    )
    assert len(regions) == 1
    assert regions[0].start_idx == 1
    assert regions[0].end_idx == 4


def test_detect_spinner_pattern() -> None:
    """Frames differing by only a spinner char are detected."""
    spinner = ["|", "/", "-", "\\"]
    frames = []
    for i in range(12):
        char = spinner[i % 4]
        frames.append(
            _make_frame(i * 0.5, 0.5, f"\r{char} Processing...")
        )
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=2.0,
    )
    assert len(regions) == 1


def test_detect_below_min_duration() -> None:
    """Short similar runs below min_duration are not collapsed."""
    frames = [
        _make_frame(0.0, 0.5, "\rloading..."),
        _make_frame(0.5, 0.5, "\rloading..."),
        # Different enough to break the run (fill most of the screen)
        _make_frame(1.0, 1.0, ("X" * 78 + "\n") * 12),
    ]
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=2.0,
    )
    assert regions == []


def test_detect_multiple_regions() -> None:
    """Multiple separate similar runs are detected independently."""
    # Use content that fills enough of the screen to create clear breaks
    different_content = ("D" * 78 + "\n") * 12
    frames = [
        # Region 1: spinner
        _make_frame(0.0, 1.0, "\rspinning |"),
        _make_frame(1.0, 1.0, "\rspinning /"),
        _make_frame(2.0, 1.0, "\rspinning -"),
        # Different content — fills half the screen to break the run
        _make_frame(3.0, 1.0, different_content),
        # Region 2: another spinner
        _make_frame(4.0, 1.0, "\rwaiting |"),
        _make_frame(5.0, 1.0, "\rwaiting /"),
        _make_frame(6.0, 1.0, "\rwaiting -"),
    ]
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=1.5,
    )
    assert len(regions) == 2


def test_detect_respects_threshold() -> None:
    """Higher threshold allows more change, lower threshold is stricter."""
    frames = [
        _make_frame(0.0, 1.0, "\rprogress: 10%"),
        _make_frame(1.0, 1.0, "\rprogress: 20%"),
        _make_frame(2.0, 1.0, "\rprogress: 30%"),
        _make_frame(3.0, 1.0, "\rprogress: 40%"),
    ]
    # With default threshold (0.05) - small change relative to active content
    regions_default = detect_collapse_regions(
        frames, cols=80, rows=24, min_duration=1.5,
    )
    assert len(regions_default) == 1

    # With very strict threshold (0.0) - no change allowed
    regions_strict = detect_collapse_regions(
        frames, cols=80, rows=24, threshold=0.0, min_duration=1.5,
    )
    assert regions_strict == []


def test_detect_index_range() -> None:
    """start_idx and end_idx limit detection to a subset of frames."""
    frames = [
        _make_frame(0.0, 1.0, "\rkeep this original content"),
        _make_frame(1.0, 1.0, "\rloading...                "),
        _make_frame(2.0, 1.0, "\rloading...                "),
        _make_frame(3.0, 1.0, "\rloading...                "),
        _make_frame(4.0, 1.0, "\rkeep this too different end"),
    ]
    regions = detect_collapse_regions(
        frames, cols=80, rows=24, start_idx=1, end_idx=4, min_duration=1.5,
    )
    assert len(regions) == 1
    assert regions[0].start_idx == 2
    assert regions[0].end_idx == 4
