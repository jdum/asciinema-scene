#!/usr/bin/env bash
# Usage: contrib/quantize_cast.sh <input_v3.cast>
# Converts asciicast v3 → v2, then quantizes with sciine, outputting <name>_quantized.cast

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <input_file.cast>" >&2
  exit 1
fi

INPUT="$1"

if [[ ! -f "$INPUT" ]]; then
  echo "Error: file not found: $INPUT" >&2
  exit 1
fi

# Derive output filename: strip extension, append _quantized, re-add extension
BASENAME="${INPUT%.*}"
EXT="${INPUT##*.}"
OUTPUT="${BASENAME}_quantized.${EXT}"

# Temp file for intermediate v2 cast
TMP_V2="$(mktemp -t castXXXXXX).cast"
trap 'rm -f "$TMP_V2"' EXIT

echo "→ Converting v3 → v2: $INPUT"
asciinema convert -f asciicast-v2 "$INPUT" "$TMP_V2"

echo "→ Quantizing: $TMP_V2"
PROJECT_ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
uv run --project "$PROJECT_ROOT" sciine quantize 3 3600 3 -i "$TMP_V2" > "$OUTPUT"

echo "✓ Done: $OUTPUT"
