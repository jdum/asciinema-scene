import importlib.metadata
import shlex
import subprocess
import sys
import time
from importlib import resources as rso

from click.testing import CliRunner

from asciinema_scene.sciine import cli

from .contents import SHORT_FILE_CONTENT

__version__ = importlib.metadata.version("asciinema_scene")

if sys.platform == "win32":
    CR = "\r\n"
else:
    CR = "\n"


def my_invoke(command: str, input_content: str):
    cmd = "sciine " + command
    if sys.platform == "win32":
        args = cmd
    else:
        args = shlex.split(cmd)
    proc = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    proc.stdin.write(input_content.encode())
    proc.stdin.close()
    proc.wait()
    return proc.returncode, proc.stdout.read().decode()


def test_version_0():
    assert isinstance(__version__, str)


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, "--version")
    assert result.exit_code == 0
    assert result.output.strip().endswith(f"version {__version__}")


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, "--help")
    assert result.exit_code == 0
    for text in (
        "copy      Copy content",
        "cut       Cut content",
        "header    Print the header",
        "include   Include the content",
        "insert    Insert a frame",
        "maximum   Set maximum",
        "minimum   Set minimum",
        "quantize  Set the duration",
        "show      Print detail",
        "speed     Change the speed",
        "status    Print information",
    ):
        assert text in result.output


def test_cli_cut():
    code, output = my_invoke("cut -e 3.0", SHORT_FILE_CONTENT)
    assert code == 0
    code2, output2 = my_invoke("status", output)
    assert code2 == 0
    assert "Duration: 3.023" in output2


def test_cli_copy():
    code, output = my_invoke("copy -e 1.0", SHORT_FILE_CONTENT)
    assert code == 0
    code2, output2 = my_invoke("status", output)
    assert code2 == 0
    assert "Duration: 1.163" in output2


def test_cli_header():
    code, output = my_invoke("header", SHORT_FILE_CONTENT)
    assert code == 0
    assert "/bin/bash" in output


def test_cli_include():
    code = output = None
    for file in rso.files("tests.files").iterdir():
        with rso.as_file(file) as path:
            if path.name != "short.cast":
                continue
            code, output = my_invoke(f"include 1.0 {path}", SHORT_FILE_CONTENT)
            break

    assert output is not None
    assert code == 0
    code2, output2 = my_invoke("status", output)
    assert code2 == 0
    assert "Duration: 12.271986" in output2


def test_cli_insert():
    code, output = my_invoke("insert 1.0 5.0 message", SHORT_FILE_CONTENT)
    assert code == 0
    code2, output2 = my_invoke("status", output)
    assert code2 == 0
    assert "Duration: 11.135993" in output2


def test_cli_delete():
    code, output = my_invoke("delete 1.16", SHORT_FILE_CONTENT)
    assert code == 0
    code2, output2 = my_invoke("status", output)
    assert code2 == 0
    assert "Duration: 5.835392" in output2


def test_cli_replace():
    code, output = my_invoke("replace 1.16 abc", SHORT_FILE_CONTENT)
    assert code == 0
    code2, output2 = my_invoke("status", output)
    assert code2 == 0
    assert "Duration: 6.135993" in output2
    code3, output3 = my_invoke("show -s 1.16 -l 1", output)
    assert code3 == 0
    assert "abc" in output3.strip()


def test_cli_insert_o():
    code, output = my_invoke("insert 1.0 5.0 message o", SHORT_FILE_CONTENT)
    assert code == 0
    code2, output2 = my_invoke("status", output)
    assert code2 == 0
    assert "Duration: 11.135993" in output2


def test_cli_maximum():
    code, output = my_invoke("maximum 0.1", SHORT_FILE_CONTENT)
    assert code == 0
    code2, output2 = my_invoke("status", output)
    assert code2 == 0
    assert "Duration: 2.000" in output2


def test_cli_minimum():
    code, output = my_invoke("minimum 10.0", SHORT_FILE_CONTENT)
    assert code == 0
    code2, output2 = my_invoke("status", output)
    assert code2 == 0
    assert "Duration: 210.000" in output2


def test_cli_quantize():
    code, output = my_invoke("quantize 0.1 3.0 20.0", SHORT_FILE_CONTENT)
    assert code == 0
    code2, output2 = my_invoke("status", output)
    assert code2 == 0
    assert "Duration: 400.000" in output2


def test_cli_show_1():
    code, output = my_invoke("show", SHORT_FILE_CONTENT)
    assert code == 0
    assert f"0.000│ 0.89│ 'e'{CR}" in output


def test_cli_show_2():
    code, output = my_invoke("show --precise", SHORT_FILE_CONTENT)
    assert code == 0
    assert f"0.000000│ 0.894038│ 'e'{CR}" in output


def test_cli_show_3():
    code, output = my_invoke("show --text", SHORT_FILE_CONTENT)
    assert code == 0
    assert "0.000│ 0.89│ e" in output


def test_cli_show_4():
    code, output = my_invoke("show --text --precise", SHORT_FILE_CONTENT)
    assert code == 0
    assert f"0.000000│ 0.894038│ e{CR}" in output


def test_cli_show_5():
    code, output = my_invoke("show --lines 2", SHORT_FILE_CONTENT)
    assert code == 0
    assert f"0.000│ 0.89│ 'e'{CR}" in output


def test_cli_show_6():
    code, output = my_invoke("show -s 0.0", SHORT_FILE_CONTENT)
    assert code == 0
    assert f"0.000│ 0.89│ 'e'{CR}" in output
    assert len(output.strip().split(CR)) == 22


def test_cli_show_7():
    code, output = my_invoke("show -s 1.0", SHORT_FILE_CONTENT)
    assert code == 0
    assert f"0.000│ 0.89│ 'e'{CR}" not in output
    assert len(output.strip().split(CR)) == 19


def test_cli_show_8():
    code, output = my_invoke("show -s 1.0 -e 2.0", SHORT_FILE_CONTENT)
    assert code == 0
    assert f"0.000│ 0.89│ 'e'{CR}" not in output
    assert len(output.strip().split(CR)) == 3


def test_cli_speed():
    code, output = my_invoke("speed 1.0", SHORT_FILE_CONTENT)
    assert code == 0
    result_cast = output
    code2, output2 = my_invoke("status ", result_cast)
    assert code2 == 0
    assert "Duration: 6.135993" in output2


def test_cli_status():
    code, output = my_invoke("status", SHORT_FILE_CONTENT)
    assert code == 0
    assert "Duration: 6.135993" in output


def test_timeout():
    command = "status"
    proc = subprocess.Popen(
        shlex.split("sciine " + command),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    time.sleep(2)
    proc.stdin.close()
    proc.wait()
    assert proc.returncode == 0
    if sys.platform != "win32":
        output = proc.stdout.read().decode()
        assert "Timeout while waiting" in output
