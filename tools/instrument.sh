#!/bin/sh
# Wrap stableSort() with a timer so the sort phase can be measured in isolation
# from a binary the project's own build system produced. Benchmark-only; never
# part of a PR. Applies unmodified to both refs under comparison.
set -e
F="$1/lib/dictBuilder/cover.c"
[ -f "$F" ] || { echo "instrument: no such file: $F" >&2; exit 1; }
grep -q '^static void stableSort(COVER_ctx_t \*ctx)$' "$F" || {
  echo "instrument: stableSort signature not found in $F" >&2; exit 1; }
awk '
/^static void stableSort\(COVER_ctx_t \*ctx\)$/ && !done {
  print "static void stableSort_impl(COVER_ctx_t *ctx);";
  print "static void stableSort(COVER_ctx_t *ctx)";
  print "{";
  print "  clock_t const zst0 = clock();";
  print "  stableSort_impl(ctx);";
  print "  fprintf(stderr, \"SORTTIME %.3f\\n\", (double)(clock() - zst0) * 1000.0 / (double)CLOCKS_PER_SEC);";
  print "}";
  print "static void stableSort_impl(COVER_ctx_t *ctx)";
  done = 1;
  next;
}
{ print }
' "$F" > "$F.tmp"
mv "$F.tmp" "$F"
grep -q 'SORTTIME' "$F" || { echo "instrument: patch did not apply" >&2; exit 1; }
echo "instrument: applied to $F"
