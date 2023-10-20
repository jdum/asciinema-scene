import gzip
from importlib import resources as rso

LONG_FILE_CONTENT = gzip.decompress(
    rso.files("tests.files").joinpath("long.cast.gz").read_bytes()
).decode()

SHORT_FILE_CONTENT = (
    rso.files("tests.files").joinpath("short.cast").read_text(encoding="utf8")
)
