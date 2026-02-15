#!/usr/bin/env bash
# Run all example demos and report pass/fail summary
# Usage: bash scripts/run_examples.sh
#
# macOS compatible (no GNU timeout dependency)

EXAMPLES_DIR="examples"
PASS=0
FAIL=0
FAILED_LIST=""

for f in "$EXAMPLES_DIR"/*_demo.py; do
    name=$(basename "$f" .py)
    output=$(uv run python "$f" 2>&1)
    rc=$?
    if [ $rc -eq 0 ]; then
        PASS=$((PASS + 1))
        printf "  PASS  %s\n" "$name"
    else
        FAIL=$((FAIL + 1))
        err=$(echo "$output" | grep -E '(Error|Exception|Traceback)' | tail -1)
        printf "  FAIL  %s  rc=%d  %s\n" "$name" "$rc" "$err"
        FAILED_LIST="$FAILED_LIST $name"
    fi
done

echo ""
echo "Summary: $PASS passed, $FAIL failed"
if [ -n "$FAILED_LIST" ]; then
    echo "Failed:$FAILED_LIST"
fi
