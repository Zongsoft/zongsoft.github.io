"""Validate Hugo content and generated internal links using the Python standard library."""
import argparse
import csv
import io
import re
import subprocess
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


class Document(HTMLParser):
	def __init__(self, text):
		super().__init__(convert_charrefs=True)
		self.links = []
		self.anchors = set()
		self.feed(text)

	def handle_starttag(self, tag, attrs):
		attrs = dict(attrs)
		for name in ('id', 'name' if tag == 'a' else 'id'):
			if attrs.get(name):
				self.anchors.add(attrs[name])
		for name in ('href', 'src', 'poster'):
			if attrs.get(name):
				self.links.append(attrs[name])
		if attrs.get('srcset'):
			self.links.extend(item.strip().split()[0] for item in attrs['srcset'].split(',') if item.strip())
		if attrs.get('style'):
			self.links.extend(css_links(attrs['style']))


def css_links(text):
	return re.findall(r'url\(\s*[\'"]?([^\s\)\'\"]+)', text)


def scalar(frontmatter, name):
	match = re.search(r'^' + re.escape(name) + r':[ \t]*(.*)$', frontmatter, re.M)
	return match.group(1).strip().strip('\'"') if match else ''


def check_metadata(root, rows):
	errors, urls, counters, series = [], {}, {}, {}
	for row in rows:
		source = row['path'].replace('\\', '/')
		if not source.startswith('docs/') or not source.endswith('.md'):
			continue
		text = (root / source).read_text(encoding='utf-8-sig')
		parts = re.split(r'^---\s*$', text, maxsplit=2, flags=re.M)
		if len(parts) != 3:
			errors.append(source + ': YAML front matter is required')
			continue
		meta = parts[1]
		for name in ('title', 'date', 'url', 'type'):
			if not scalar(meta, name):
				errors.append(source + ': missing ' + name)
		if scalar(meta, 'type') != 'post':
			errors.append(source + ': type must be post')
		url = scalar(meta, 'url')
		if not re.fullmatch(r'/blog/zh-cn/[a-z0-9/_-]+/', url):
			errors.append(source + ': invalid article URL ' + url)
		for value, seen, label in ((url, urls, 'URL'), (scalar(meta, 'stats_path') or url, counters, 'statistics path')):
			if value in seen:
				errors.append(source + ': duplicate ' + label + ' with ' + seen[value])
			seen[value] = source
		for name in ('date', 'lastmod'):
			value = scalar(meta, name)
			if value:
				try:
					datetime.fromisoformat(value.replace('Z', '+00:00'))
				except ValueError:
					errors.append(source + ': invalid ' + name + ' ' + value)
		name = scalar(meta, 'series')
		if name:
			order = scalar(meta, 'series_order')
			if not order.isdigit() or int(order) < 1:
				errors.append(source + ': series_order must be a positive integer')
			elif (name, int(order)) in series:
				errors.append(source + ': duplicate order in series ' + name)
			else:
				series[name, int(order)] = source
	return errors


def check_output(output, base_url):
	output = output.resolve()
	documents = {path: Document(path.read_text(encoding='utf-8')) for path in output.rglob('*.html')}
	errors = []
	if not documents:
		return ['No generated HTML found in ' + str(output)]
	resources = [(path, doc.links) for path, doc in documents.items()]
	resources += [(path, css_links(path.read_text(encoding='utf-8'))) for path in output.rglob('*.css')]
	for source, links in resources:
		page_url = urljoin(base_url, source.relative_to(output).as_posix())
		for link in set(links):
			url = urlsplit(urljoin(page_url, link))
			if url.scheme not in ('http', 'https') or url.netloc != urlsplit(base_url).netloc:
				continue
			target = (output / unquote(url.path).lstrip('/')).resolve()
			if not target.is_relative_to(output):
				errors.append(str(source.relative_to(output)) + ': path escapes output: ' + link)
				continue
			if target.is_dir():
				target /= 'index.html'
			if not target.is_file():
				errors.append(str(source.relative_to(output)) + ': missing target ' + link)
			elif url.fragment and target in documents and unquote(url.fragment) not in documents[target].anchors:
				errors.append(str(source.relative_to(output)) + ': missing anchor ' + link)
	return errors


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--hugo', default='hugo')
	parser.add_argument('--output', default='public')
	args = parser.parse_args()
	root = Path(__file__).resolve().parent.parent
	result = subprocess.run([args.hugo, 'list', 'all'], cwd=root, capture_output=True, text=True, encoding='utf-8')
	if result.returncode:
		print(result.stderr, file=sys.stderr)
		return 1
	reader = csv.DictReader(io.StringIO(result.stdout))
	rows = list(reader)
	errors = []
	if not reader.fieldnames or 'path' not in reader.fieldnames:
		errors.append('Hugo article list is missing the path column')
	sources = {path.relative_to(root).as_posix() for path in (root / 'docs').glob('*.md')}
	listed = {(row.get('path') or '').replace('\\', '/') for row in rows}
	listed = {path for path in listed if path.startswith('docs/') and path.endswith('.md')}
	if not sources:
		errors.append('No article source files found in docs')
	if not listed:
		errors.append('Hugo did not list any docs/*.md articles')
	for source in sorted(sources - listed):
		errors.append('Article missing from Hugo list: ' + source)
	for source in sorted(listed - sources):
		errors.append('Hugo listed an unknown article source: ' + source)
	if not errors:
		errors = check_metadata(root, rows) + check_output(root / args.output, 'https://zongsoft.com/')
	for error in errors:
		print('ERROR: ' + error, file=sys.stderr)
	print('Site checks: ' + str(len(errors)) + ' error(s); metadata, article URLs, series, images, links and anchors checked.')
	return bool(errors)


if __name__ == '__main__':
	sys.exit(main())
