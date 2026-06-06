just run:

```bash
python3 generate_hocbigg_curriculum.py "$REPO_DIR"
python3 generate_sitemap.py "$REPO_DIR"
```

check the `out/` output folder in the root folder (where u put the scripts)

push to github:

```bash
./deploy-gh-pages.sh curriculum/
```
