"""finalize.py <out_dir> <stem> <final.md> [--assets-dir assets] [--delete-raw]
After styling: move media/<stem>/* and media/<stem>.manifest.json into <out_dir>/<assets-dir>/,
rewrite image links `](media/<stem>/` -> `](<assets-dir>/` in <final.md> (removes spaces from paths),
verify every local image link resolves, optionally delete the raw <stem>.md.
Refuses to run if <assets-dir> already holds a file with the same name."""
import os, re, sys, shutil
sys.stdout.reconfigure(encoding="utf-8")
args = [a for a in sys.argv[1:] if not a.startswith("--")]
out_dir, stem, final = args[0], args[1], args[2]
assets = sys.argv[sys.argv.index("--assets-dir") + 1] if "--assets-dir" in sys.argv else "assets"
if assets in args: args.remove(assets)
src = os.path.join(out_dir, "media", stem)
dst = os.path.join(out_dir, assets)
man = os.path.join(out_dir, "media", stem + ".manifest.json")
final_p = os.path.join(out_dir, final)
os.makedirs(dst, exist_ok=True)
names = os.listdir(src) + ([os.path.basename(man)] if os.path.exists(man) else [])
clash = [n for n in names if os.path.exists(os.path.join(dst, n))]
if clash: sys.exit(f"refusing: {len(clash)} names already in {dst}: {clash[:5]}")
for n in os.listdir(src): shutil.move(os.path.join(src, n), os.path.join(dst, n))
if os.path.exists(man): shutil.move(man, dst)
os.rmdir(src)
if not os.listdir(os.path.join(out_dir, "media")): os.rmdir(os.path.join(out_dir, "media"))
md = open(final_p, encoding="utf-8").read()
md = md.replace(f"](media/{stem}/", f"]({assets}/")
open(final_p, "w", encoding="utf-8").write(md)
links = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md)
missing = [l for l in links if not l.startswith("http") and not os.path.exists(os.path.join(out_dir, l))]
print(f"moved {len(names)} files -> {dst}; links {len(links)}, missing {len(missing)} {missing[:5]}")
if "--delete-raw" in sys.argv and not missing:
    raw = os.path.join(out_dir, stem + ".md")
    if os.path.exists(raw) and os.path.abspath(raw) != os.path.abspath(final_p):
        os.remove(raw); print("deleted raw", raw)
