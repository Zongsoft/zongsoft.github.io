# Zongsoft website and blog

English | [简体中文](README.zh-Hans.md)

[Website](https://zongsoft.com/) · [Blog](https://zongsoft.com/blog/)

The blog uses Hugo and the local `themes/zongsoft` theme. It preserves the site's backgrounds, original Oswald title font, and avatar, using plain CSS and vanilla JavaScript. Go, Node.js, npm, Sass, and remote theme modules are not required.

## Write and preview

Keep Markdown posts in `docs/_posts/` and images in `docs/images/`. Posts need `title`, `type: post`, `date`, and a stable `url` such as `/blog/zh-cn/misc/my-post/`. Categories and tags are optional. Use `draft: true` while writing and remove it before publishing. Set `lastmod` explicitly when needed; filesystem modification times are not used.

On Windows, run `preview.cmd` and open <http://127.0.0.1:1313/blog/>. The first run downloads the official Hugo binary pinned in `.hugo-version`, verifies its SHA-256, and caches it in `.tools/`. Subsequent runs can work offline. No PATH changes or global installation are needed.

Run `build.cmd` to generate production files in `public/`. Do not commit generated output. On other platforms, install the same Hugo version and run `hugo server -D` or `hugo --minify` in the repository root.

## Deployment

Set Settings → Pages → Source to **GitHub Actions** and retain the custom domain `zongsoft.com`. `.github/workflows/pages.yml` builds the complete website on pushes to `main` and publishes the Pages artifact. Pull requests build without deploying. The root website, English pages, shared assets, and blog are included in one artifact.

Only source files and assets are versioned. The previous generator, third-party theme dependencies, and generated pages have been removed. Git history remains available for restoring the previous site.

## Theme customization

- `hugo.toml`: site configuration, local content mounts, taxonomy URLs.
- `themes/zongsoft/layouts/`: templates for posts, lists, archives, navigation, and table of contents.
- `themes/zongsoft/assets/css/blog.css`: ordinary CSS, typography, colors, and responsive layout.
- `themes/zongsoft/assets/js/blog.js`: navigation, theme switch, clipboard actions, image viewer, and active table of contents.
- `themes/zongsoft/static/blog/`: original title/code fonts and background images.
- `assets/avatar.jpg`: the original avatar.

The 10 existing articles retain their URLs. The [site setup tutorial](https://zongsoft.com/blog/zh-cn/misc/github-site/) now describes Hugo and GitHub Actions, retaining its original publication date and recording the revision in `lastmod`. The article footer retains the site's custom BY-NC-SA 4.0 notice.

Text files use CRLF, code indentation uses tabs, YAML indentation uses the spaces required by YAML, and shell scripts use LF. Original font/image binaries and the Archer MIT notice are preserved.
