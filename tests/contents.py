import gzip
from importlib import resources as rso

LONG_FILE_CONTENT = gzip.decompress(
    rso.read_binary("tests.files", "long.cast.gz")
).decode()

SHORT_FILE_CONTENT = rso.read_text("tests.files", "short.cast", encoding="utf8")
