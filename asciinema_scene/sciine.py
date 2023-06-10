import importlib.metadata
from collections.abc import Callable
from functools import wraps
from pprint import pformat
from typing import Any

import click

from .scenelib.scene import Scene
from .scenelib.utils import SceneStdinError

__version__ = importlib.metadata.version("asciinema_scene")

input_option = click.option(
    "--input",
    "-i",
    "input_file",
    type=click.Path(exists=True),
    help="Input .cast file, default is stdin.",
)
output_option = click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    help="Output .cast file, default is stdout.",
)
start_option = click.option(
    "--start",
    "-s",
    type=float,
    help="Start timecode (sec), default is 0.0.",
)
end_option = click.option(
    "--end",
    "-e",
    type=float,
    help="End timecode (sec), default is EOF.",
)
adjust_option = click.option(
    "--adjust",
    "-a",
    is_flag=True,
    default=False,
    help="Adjust durations of frames at precise cut values.",
)


def stdin_timeout_handler(function: Callable) -> Callable:
    @wraps(function)
    def wrapped(*args: list[Any], **kwargs: dict[str, Any]) -> Any:
        try:
            function(*args, **kwargs)
        except SceneStdinError:
            print("Timeout while waiting for STDIN input.\n")
            ctx = click.get_current_context()
            click.echo(ctx.get_help())
            ctx.exit()

    return wrapped


@click.group(invoke_without_command=True, no_args_is_help=True)
@click.version_option(version=__version__)
def cli() -> None:
    pass


@cli.command("status")
@stdin_timeout_handler
@input_option
def info_cmd(input_file: str | None) -> None:
    """Print informations about the content (duration, ...)."""
    scene = Scene.parse(input_file)
    print(scene.info)


@cli.command("header")
@stdin_timeout_handler
@input_option
def header_cmd(input_file: str | None) -> None:
    """Print the header field of the content."""
    scene = Scene.parse(input_file)
    print(pformat(scene.header))


@cli.command("show")
@stdin_timeout_handler
@start_option
@end_option
@click.option(
    "--lines",
    "-l",
    type=int,
    help="Number of lines to show.",
)
@click.option(
    "--precise",
    "-p",
    is_flag=True,
    default=False,
    help="Show all digits of time codes.",
)
@click.option(
    "--text",
    "-t",
    "as_str",
    is_flag=True,
    default=False,
    help="Show message field as plain text.",
)
@input_option
def show_cmd(
    start: float | None,
    end: float | None,
    lines: int | None,
    precise: bool,
    as_str: bool,
    input_file: str | None,
) -> None:
    """Print detail of frames, from START to END (max LINES).

    Each line prints the timecode, duration and text of the frame.
    If no START timecode is provided, start from the beginning.
    If no END timecode is provided, display all lines until the end,
    or LINES lines
    """
    scene = Scene.parse(input_file)
    scene.show(
        start=start,
        end=end,
        max_lines=lines,
        precise=precise,
        as_str=as_str,
    )


@cli.command("cut")
@stdin_timeout_handler
@start_option
@end_option
@adjust_option
@input_option
@output_option
def cut_cmd(
    start: float | None,
    end: float | None,
    adjust: bool,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Cut content between START and END timecodes.

    If no START timecode is provided, cut from the beginning.
    If no END timecode is provided, cut until the end.
    """
    scene = Scene.parse(input_file)
    scene.cut_frames(start=start, end=end, adjust=adjust)
    scene.dump(output_file)


@cli.command("copy")
@stdin_timeout_handler
@start_option
@end_option
@input_option
@output_option
def copy_cmd(
    start: float | None,
    end: float | None,
    input_file: str | None,
    output_file: str | None,
    adjust: bool = False,
) -> None:
    """Copy content between START and END timecodes."""
    scene = Scene.parse(input_file)
    scene.copy(start=start, end=end, adjust=adjust)
    scene.dump(output_file)


@cli.command("speed")
@stdin_timeout_handler
@click.argument("speed", required=True, type=float)
@start_option
@end_option
@input_option
@output_option
def speed_cmd(
    speed: float,
    start: float | None,
    end: float | None,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Change the speed of the screen cast.

    SPEED is the factor of acceleration. Use number below 1.0
    to to slow down.
    If no START timecode is provided, modify speed from the beginning.
    If no END timecode is provided, modify speed until the end.
    """
    scene = Scene.parse(input_file)
    scene.speed(speed, start=start, end=end)
    scene.dump(output_file)


@cli.command("maximum")
@stdin_timeout_handler
@click.argument("duration", required=True, type=float)
@start_option
@end_option
@input_option
@output_option
def maximum_cmd(
    duration: float,
    start: float | None,
    end: float | None,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Set maximum duration of each frame.

    The duration of frames will be limited to DURATION seconds,
    the timecodes will be adjusted accordingly.
    If no START timecode is provided, apply from the beginning.
    If no END timecode is provided, apply until the end.
    """
    scene = Scene.parse(input_file)
    scene.maximum(duration, start=start, end=end)
    scene.dump(output_file)


@cli.command("minimum")
@stdin_timeout_handler
@click.argument("duration", required=True, type=float)
@start_option
@end_option
@input_option
@output_option
def minimum_cmd(
    duration: float,
    start: float | None,
    end: float | None,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Set minimum duration of each frame.

    The minimum duration of frames will be set to DURATION seconds,
    the timecodes will be adjusted accordingly.
    If no START timecode is provided, apply from the beginning.
    If no END timecode is provided, apply until the end.
    """
    scene = Scene.parse(input_file)
    scene.minimum(duration, start=start, end=end)
    scene.dump(output_file)


@cli.command("quantize")
@stdin_timeout_handler
@click.argument("range_min", required=True, type=float)
@click.argument("range_max", required=True, type=float)
@click.argument("duration", required=True, type=float)
@start_option
@end_option
@input_option
@output_option
def quantize_cmd(
    range_min: float,
    range_max: float,
    duration: float,
    start: float | None,
    end: float | None,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Set the duration of frames in duration range to DURATION.

    Set the duration of frames to DURATION if their current
    duration is between RANGE_MIN and RANGE_MAX.
    If no START timecode is provided, apply from the beginning.
    If no END timecode is provided, apply until the end.
    """
    scene = Scene.parse(input_file)
    scene.quantize(range_min, range_max, duration, start=start, end=end)
    scene.dump(output_file)


@cli.command("insert")
@stdin_timeout_handler
@click.argument("timecode", required=True, type=float)
@click.argument("duration", required=True, type=float)
@click.argument("text", required=True, type=str)
@click.argument("etype", required=False, type=str)
@input_option
@output_option
def insert_cmd(
    timecode: float,
    duration: float,
    text: str,
    etype: str,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Insert a frame at the TIMECODE position.

    The frame will display TEXT during DURATION seconds. By default
    the event type ETYPE is set to "o".
    """
    scene = Scene.parse(input_file)
    if not etype:
        etype = "o"
    scene.insert(timecode, duration, text, etype)
    scene.dump(output_file)


@cli.command("delete")
@stdin_timeout_handler
@click.argument("timecode", required=True, type=float)
@input_option
@output_option
def delete_cmd(
    timecode: float,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Delete the frame with timecode >= TIMECODE."""
    scene = Scene.parse(input_file)
    scene.delete(timecode)
    scene.dump(output_file)


@cli.command("replace")
@stdin_timeout_handler
@click.argument("timecode", required=True, type=float)
@click.argument("text", required=True, type=str)
@input_option
@output_option
def replace_cmd(
    timecode: float,
    text: str,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Replace the text of frame with timecode >= TIMECODE by TEXT."""
    scene = Scene.parse(input_file)
    scene.replace(timecode, text)
    scene.dump(output_file)


@cli.command("include")
@stdin_timeout_handler
@click.argument("timecode", required=True, type=float)
@click.argument("include_file", type=click.Path(exists=True), required=True)
@input_option
@output_option
def include_cmd(
    timecode: float,
    include_file: str,
    input_file: str | None,
    output_file: str | None,
) -> None:
    """Include the content of a .cast file at the timecode position.

    All frames of the INCLUDE_FILE .cast file will be copied in the
    current screen cast. The timecodes will be adjusted as required.
    """
    scene = Scene.parse(input_file)
    scene.include(timecode, include_file)
    scene.dump(output_file)
