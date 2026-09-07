#!/bin/sh
# Emits the 2 scenario cells for ONE code variant. Same script on every platform.
# No `set -e`: failures are the observation.
: "${ZSTD_BIN:=./zstd.exe}"
: "${VARIANT:=unknown}"
PLAT=$(uname -s 2>/dev/null || echo unknown)

printf 'aaa\n' > a.txt
printf 'bbb\n' > b.txt

# ---- Scenario 1: file list using CRLF line endings ----
printf 'a.txt\r\nb.txt\r\n' > s1.list
echo "--- bytes of the CRLF list, as written on this platform:"
od -c s1.list
rm -f a.txt.zst b.txt.zst
"$ZSTD_BIN" -q -f --filelist=s1.list; s1rc=$?
n=0
[ -f a.txt.zst ] && n=$((n+1))
[ -f b.txt.zst ] && n=$((n+1))
if [ "$n" = 2 ]; then S1=WORKS; else S1=FAILS; fi

# ---- Scenario 2: a filename that legitimately ends in CR ----
CRNAME=$(printf 'weird\r')
CREATED=no
printf 'data\n' > "$CRNAME" 2>/dev/null
[ -e "$CRNAME" ] && CREATED=yes
if [ "$CREATED" = yes ]; then
  printf 'weird\r\n' > s2.list
  rm -f "$CRNAME.zst" weird.zst
  "$ZSTD_BIN" -q -f --filelist=s2.list; s2rc=$?
  if [ -f "$CRNAME.zst" ]; then S2=WORKS; else S2=FAILS; fi
else
  s2rc=na
  S2=NA_OS_FORBIDS_CR_IN_FILENAME
fi
rm -f "$CRNAME" "$CRNAME.zst" weird.zst s1.list s2.list

echo "CELL plat=$PLAT variant=$VARIANT scenario=1_crlf_list   result=$S1 rc=$s1rc"
echo "CELL plat=$PLAT variant=$VARIANT scenario=2_cr_filename result=$S2 rc=$s2rc created=$CREATED"
