import importlib.metadata
from importlib import resources as rso

from click.testing import CliRunner

from asciinema_scene.sciine import cli

from .contents import SHORT_FILE_CONTENT

__version__ = importlib.metadata.version("asciinema_scene")


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
    runner = CliRunner()
    result1 = runner.invoke(cli, "cut -e 3.0", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 3.023" in result


def test_cli_copy():
    runner = CliRunner()
    result1 = runner.invoke(cli, "copy -e 1.0", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 1.163" in result


def test_cli_header():
    runner = CliRunner()
    result1 = runner.invoke(cli, "header", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result = result1.output
    assert "/bin/bash" in result


def test_cli_include():
    runner = CliRunner()
    result1 = None
    for file in rso.files("tests.files").iterdir():
        with rso.as_file(file) as path:
            if path.name != "short.cast":
                continue
            result1 = runner.invoke(
                cli, f"include 1.0 {path}", input=SHORT_FILE_CONTENT
            )
            break
    assert result1 is not None
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 12.271986" in result


def test_cli_insert():
    runner = CliRunner()
    result1 = runner.invoke(cli, "insert 1.0 5.0 message", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 11.135993" in result


def test_cli_delete():
    runner = CliRunner()
    result1 = runner.invoke(cli, "delete 1.16", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 5.835392" in result


def test_cli_replace():
    runner = CliRunner()
    result1 = runner.invoke(cli, "replace 1.16 abc", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 6.135993" in result
    result3 = runner.invoke(cli, "show -s 1.16 -l 1", input=result_cast)
    assert result3.exit_code == 0
    result = result3.output.strip()
    assert "abc" in result


def test_cli_insert_o():
    runner = CliRunner()
    result1 = runner.invoke(cli, "insert 1.0 5.0 message o", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 11.135993" in result


def test_cli_maximum():
    runner = CliRunner()
    result1 = runner.invoke(cli, "maximum 0.1", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 2.000" in result


def test_cli_minimum():
    runner = CliRunner()
    result1 = runner.invoke(cli, "minimum 10.0", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 210.000" in result


def test_cli_quantize():
    runner = CliRunner()
    result1 = runner.invoke(cli, "quantize 0.1 3.0 20.0", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 400.000" in result


def test_cli_show_1():
    runner = CliRunner()
    result1 = runner.invoke(cli, "show", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result = result1.output
    assert "0.000│ 0.89│ 'e'\n" in result


def test_cli_show_2():
    runner = CliRunner()
    result1 = runner.invoke(cli, "show --precise", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result = result1.output
    assert "0.000000│ 0.894038│ 'e'\n" in result


def test_cli_show_3():
    runner = CliRunner()
    result1 = runner.invoke(cli, "show --text", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result = result1.output
    assert "0.000│ 0.89│ e" in result


def test_cli_show_4():
    runner = CliRunner()
    result1 = runner.invoke(cli, "show --text --precise", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result = result1.output
    assert "0.000000│ 0.894038│ e\n" in result


def test_cli_show_5():
    runner = CliRunner()
    result1 = runner.invoke(cli, "show --lines 2", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result = result1.output
    assert "0.000│ 0.89│ 'e'\n" in result


def test_cli_show_6():
    runner = CliRunner()
    result1 = runner.invoke(cli, "show -s 0.0", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result = result1.output
    assert "0.000│ 0.89│ 'e'\n" in result
    assert len(result.strip().split("\n")) == 22


def test_cli_show_7():
    runner = CliRunner()
    result1 = runner.invoke(cli, "show -s 1.0", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result = result1.output
    assert "0.000│ 0.89│ 'e'\n" not in result
    assert len(result.strip().split("\n")) == 19


def test_cli_show_8():
    runner = CliRunner()
    result1 = runner.invoke(cli, "show -s 1.0 -e 2.0", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result = result1.output
    assert "0.000│ 0.89│ 'e'\n" not in result
    assert len(result.strip().split("\n")) == 3


def test_cli_speed():
    runner = CliRunner()
    result1 = runner.invoke(cli, "speed 1.0", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result_cast = result1.output
    result2 = runner.invoke(cli, "status", input=result_cast)
    assert result2.exit_code == 0
    result = result2.output
    assert "Duration: 6.135993" in result


def test_cli_status():
    runner = CliRunner()
    result1 = runner.invoke(cli, "status", input=SHORT_FILE_CONTENT)
    assert result1.exit_code == 0
    result = result1.output
    assert "Duration: 6.135993" in result
