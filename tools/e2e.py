#!/usr/bin/env python3
"""End-to-end COVER training time, base vs candidate. Benchmark-only; never part
of a PR. Both binaries carry the SORTTIME hook from tools/instrument.sh, so each
run reports whole-process wall time and the sort's share of it.

usage: e2e.py LABEL ZBASE ZCAND GENCORPUS_DIR GITHUB_DIR
Runs base and candidate alternately; reports the median of each."""
import hashlib, os, subprocess, sys, time

label, zbase, zcand, gcdir, ghdir = sys.argv[1:6]

def run(z, args, cwd, out):
    t0 = time.perf_counter()
    p = subprocess.run([z, "-q", "-f"] + args + ["-o", out], cwd=cwd,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    wall = (time.perf_counter() - t0) * 1000.0
    err = p.stderr.decode("utf-8", "replace")
    if p.returncode != 0:
        raise SystemExit("FAIL %s %s rc=%d %s" % (label, " ".join(args), p.returncode, err[-300:]))
    sort = sum(float(l.split()[1]) for l in err.splitlines() if l.startswith("SORTTIME "))
    nsort = sum(1 for l in err.splitlines() if l.startswith("SORTTIME "))
    if nsort == 0:
        raise SystemExit("FAIL %s %s: no SORTTIME emitted" % (label, " ".join(args)))
    with open(os.path.join(cwd, out), "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()[:16]
    return wall, sort, nsort, digest

def med(xs):
    xs = sorted(xs); return xs[len(xs) // 2]

CONFIGS = [
    # name, args, cwd, reps
    ("synthetic-8MB-k2048-d8",  ["--train-cover=k=2048,d=8",  "--filelist=list_8mb.txt"],  gcdir, 3),
    ("synthetic-8MB-k2048-d16", ["--train-cover=k=2048,d=16", "--filelist=list_8mb.txt"],  gcdir, 3),
    ("synthetic-32MB-k2048-d8", ["--train-cover=k=2048,d=8",  "--filelist=list_32mb.txt"], gcdir, 3),
    ("synthetic-32MB-k2048-d16",["--train-cover=k=2048,d=16", "--filelist=list_32mb.txt"], gcdir, 3),
    ("synthetic-8MB-optimizer", ["--train-cover",              "--filelist=list_8mb.txt"],  gcdir, 2),
    ("github-k1024-d8",         ["--train-cover=k=1024,d=8", "--maxdict=16384", "-r", "github"], ghdir, 5),
    ("github-optimizer",        ["--train-cover",            "--maxdict=16384", "-r", "github"], ghdir, 3),
]

if os.environ.get("E2E_SMOKE"):  # script check only: tiny inputs, one rep
    CONFIGS = [(n, a, c, 1) for n, a, c, _ in CONFIGS if n.startswith("github")]

failed = 0
for name, args, cwd, reps in CONFIGS:
    rb, rc = [], []
    for _ in range(reps):
        rb.append(run(zbase, args, cwd, "e2e_base.dict"))
        rc.append(run(zcand, args, cwd, "e2e_cand.dict"))
    ident = "IDENTICAL" if rb[-1][3] == rc[-1][3] else "DIFFER"
    if ident != "IDENTICAL":
        failed = 1
    wb, wc = med([r[0] for r in rb]), med([r[0] for r in rc])
    sb, sc = med([r[1] for r in rb]), med([r[1] for r in rc])
    print("E2E %s %s base_wall=%.1fms cand_wall=%.1fms wall_ratio=%.3f "
          "base_sort=%.1fms cand_sort=%.1fms sort_ratio=%.3f base_sort_share=%.1f%% "
          "cand_sort_share=%.1f%% sorts=%d reps=%d %s"
          % (label, name, wb, wc, wb / wc if wc else 0, sb, sc, sb / sc if sc else 0,
             100.0 * sb / wb if wb else 0, 100.0 * sc / wc if wc else 0, rb[-1][2], reps, ident),
          flush=True)
print("SUMMARY %s failed=%d" % (label, failed))
sys.exit(failed)
