# Zongsoft website and blog

English | [简体中文](README.zh-Hans.md)

[Website](https://zongsoft.com/) · [Blog](https://zongsoft.com/blog/)

The blog uses Hugo and the local `themes/archer` theme. It preserves the site's backgrounds, original Oswald title font, and avatar, using plain CSS and vanilla JavaScript. Go, Node.js, npm, Sass, and remote theme modules are not required.

## Write and preview

Keep Markdown posts in `docs/` and images in `docs/images/`. Posts need `title`, `type: post`, `date`, and a stable `url` such as `/blog/zh-cn/misc/my-post/`. Categories and tags are optional. Use `draft: true` while writing and remove it before publishing. Set `lastmod` explicitly when needed; filesystem modification times are not used.

On Windows, run `preview.cmd` and open <http://127.0.0.1:1313/blog/>. The first run downloads the official Hugo binary pinned in `.hugo-version`, verifies its SHA-256, and caches it in `.tools/`. Subsequent runs can work offline. No PATH changes or global installation are needed.

Run `build.cmd` to generate production files in `public/`. Do not commit generated output. On other platforms, install the same Hugo version and run `hugo server -D` or `hugo --minify` in the repository root.

## Deployment

Set Settings → Pages → Source to **GitHub Actions** and retain the custom domain `zongsoft.com`. `.github/workflows/pages.yml` builds the complete website on pushes to `main` and publishes the Pages artifact. Pull requests build without deploying. The root website, English pages, shared assets, and blog are included in one artifact.

Only source files and assets are versioned. The previous generator, third-party theme dependencies, and generated pages have been removed. Git history remains available for restoring the previous site.

## Theme customization

- `hugo.toml`: site configuration, local content mounts, taxonomy URLs.
- `themes/archer/layouts/`: templates for posts, lists, archives, navigation, and table of contents.
- `themes/archer/assets/css/blog.css`: ordinary CSS, typography, colors, and responsive layout.
- `themes/archer/assets/js/blog.js`: navigation, theme switch, clipboard actions, image viewer, and active table of contents.
- `themes/archer/static/blog/`: original title/code fonts and background images.
- `assets/avatar.jpg`: the original avatar.

Text files use CRLF, code indentation uses tabs, YAML indentation uses the spaces required by YAML, and shell scripts use LF. Original font/image binaries and the Archer MIT notice are preserved.

## Reading, search, and feedback

Article views use GoatCounter at `https://zongsoft.goatcounter.com/`, enabled only on production article pages hosted at `https://zongsoft.com`. Preview, search, and corporate pages do not send visits. The public endpoint has returned stale responses older than four hours. Counters therefore request a cumulative range from 1970-01-01 through the next UTC date, changing the range daily and bypassing browser caching. This includes the full visit history of all current articles, not just today. Server caching can still delay updates within a day; counts are not real-time. HTTP 200 with zero displays zero; HTTP 404 with zero displays a pending-statistics label. Failed or invalid responses remain hidden. Keep each article's `stats_path` unchanged after publication, even if its file or URL changes, and retain redirects with `aliases`. Set `params.goatcounter` to an empty string to disable analytics. The official GoatCounter script sends visitor statistics to that service; no password or API token belongs in the site source.

The [search page](https://zongsoft.com/blog/search/) uses a Hugo-generated full-text index and vanilla JavaScript. All space-separated terms must match; title matches rank first. It searches titles, tags, prose, and code without a search server or an additional build tool. JavaScript is required; fuzzy matching and semantic search are not included.

Set `series` and a positive `series_order` on related articles to render an ordered series navigator. Heading `#` buttons copy canonical section links. Article footers link to a prefilled GitHub issue form and the source editor; readers review and submit feedback themselves with a GitHub account.

## Publishing checks

After building, Actions runs `python3 scripts/check-site.py` and the checker's standard-library unit tests. Missing metadata, invalid dates, duplicate URLs/statistics paths, invalid series positions, and broken generated internal links, fragments, images, or CSS assets block deployment. Draft/future metadata is included; link checks cover generated pages. External sites are not checked as a deployment gate.

Python 3.9+ is already available on the Actions runner; no npm dependencies or additional local Hugo build requirements are introduced. With Python installed, run `python scripts/check-site.py --hugo .tools/hugo/0.166.0/amd64/hugo.exe` and `python -m unittest discover -s scripts -p 'test_*.py'`. Required post fields and the `stats_path`, `series`, and `series_order` fields must use top-level, single-line YAML values. Browser screenshots and temporary reports stay outside version control.
