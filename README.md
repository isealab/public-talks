# Public Talks

Source and rendered artifacts for public talks. Each talk lives in its own
folder with source files, images, styles, and final exported formats when those
outputs are useful for sharing or archiving.

## Current Talks

- `TALK_CATALOG.md` is a generated index of talk folders, source files,
  rendered outputs, assets, and known publication links.
- `20250925 Volz HAWAII Vibe Coding/` contains the R Markdown source, image
  assets, CSS, and rendered PDF/HTML outputs for the HAWAII 2025 talk on vibe
  coding and programming education. Published copy:
  <http://rpubs.com/raphaelvolz/1347548>.

## Render R Markdown Talks

Install R with `rmarkdown` and `knitr`, then run:

```sh
Rscript scripts/render_rmarkdown.R
```

The script renders every `.Rmd` file in the repository using the output format
declared in the file. Generated caches and local publishing metadata are
ignored; durable PDF/HTML exports can still be committed when they are part of
the talk archive.

Refresh the catalog after adding or rendering talks:

```sh
python3 scripts/generate_talk_catalog.py
git diff --exit-code -- TALK_CATALOG.md
```
