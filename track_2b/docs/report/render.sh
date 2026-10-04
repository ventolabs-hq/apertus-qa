#!/bin/sh
# Render technical_report.md -> VentoLabs_Report.pdf (pandoc -> HTML -> WeasyPrint). Runs inside apertus-qa-report:local.
# Usage (from track_2b/): make report      Output: VentoLabs_Report.pdf + page count; fails if > 6 pages.
set -eu
SRC=${1:-technical_report.md}; OUT=${2:-VentoLabs_Report.pdf}; MAXP=${MAXP:-6}
tmp=$(mktemp -d)
# Highlight [[PLACEHOLDERS]] so unfinished content is visible in the PDF.
sed -E 's/`?\[\[([^]]*)\]\]`?/<span class="ph">[[\1]]<\/span>/g' "$SRC" > "$tmp/report.md"
pandoc "$tmp/report.md" -f markdown-smart -t html5 -s -V document-css=false --columns=1000 --metadata title="Apertus QA technical report" \
  --css docs/report/style.css -o "$tmp/report.html"
weasyprint --base-url "$PWD" "$tmp/report.html" "$OUT"
pages=$(pdfinfo "$OUT" | awk '/^Pages:/{print $2}')
left=$(grep -o '\[\[[^]]*\]\]' "$SRC" | wc -l)
echo "$OUT: $pages page(s) A4; placeholders remaining: $left"
rm -rf "$tmp"
[ "$pages" -le "$MAXP" ] || { echo "ERROR: more than $MAXP pages"; exit 1; }
