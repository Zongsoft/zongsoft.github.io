"""Offline regression tests for the pre-publication site checker."""
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location('check_site', Path(__file__).with_name('check-site.py'))
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class SiteFixture(unittest.TestCase):
	def setUp(self):
		self.temporary = tempfile.TemporaryDirectory()
		self.addCleanup(self.temporary.cleanup)
		self.root = Path(self.temporary.name)
		self.output = self.root / 'public'
		self.output.mkdir()

	def write(self, path, text):
		path.parent.mkdir(parents=True, exist_ok=True)
		with path.open('w', encoding='utf-8', newline='\r\n') as file:
			file.write(text)

	def article(self, name='first', **changes):
		fields = {'title': 'A useful article', 'date': '2026-09-14T08:00:00+08:00',
			'type': 'post', 'url': '/blog/zh-cn/misc/' + name + '/'}
		fields.update(changes)
		text = '---\n' + '\n'.join(key + ': ' + str(value) for key, value in fields.items() if value is not None) + '\n---\n正文\n'
		self.write(self.root / 'docs' / (name + '.md'), text)
		return {'path': 'docs/' + name + '.md'}

	def check_output(self):
		return checker.check_output(self.output, 'https://zongsoft.com/')


class MetadataTests(SiteFixture):
	def test_valid_metadata_supports_dates_quotes_and_series(self):
		rows = [self.article(title='"含中文标题"', date='2018-07-10 18:00:00', lastmod='2026-09-14T00:00:00Z', series='教程', series_order=1),
			self.article('second', date='2026-09-14', series='教程', series_order=2, stats_path='/stable/article-two/')]
		rows[0]['path'] = 'docs\\first.md'
		self.assertEqual(checker.check_metadata(self.root, rows), [])

	def test_required_metadata_fields(self):
		for field in ('title', 'date', 'type', 'url'):
			for value in (None, '', '""'):
				with self.subTest(field=field, value=value):
					row = self.article(**{field: value})
					self.assertIn('docs/first.md: missing ' + field, checker.check_metadata(self.root, [row]))

	def test_invalid_dates(self):
		for field in ('date', 'lastmod'):
			for value in ('2026-02-30', 'yesterday', '2026-13-01T00:00:00'):
				with self.subTest(field=field, value=value):
					row = self.article(**{field: value})
					self.assertEqual(checker.check_metadata(self.root, [row]), ['docs/first.md: invalid ' + field + ' ' + value])

	def test_duplicate_article_urls(self):
		rows = [self.article(stats_path='/counter/one/'), self.article('second', url='/blog/zh-cn/misc/first/', stats_path='/counter/two/')]
		self.assertEqual(checker.check_metadata(self.root, rows), ['docs/second.md: duplicate URL with docs/first.md'])

	def test_duplicate_statistics_paths(self):
		for path in ('/counter/shared/', '/blog/zh-cn/misc/first/'):
			with self.subTest(path=path):
				rows = [self.article(stats_path=path if 'counter' in path else None), self.article('second', stats_path=path)]
				self.assertEqual(checker.check_metadata(self.root, rows), ['docs/second.md: duplicate statistics path with docs/first.md'])

	def test_invalid_series_order(self):
		for order in (None, '', 0, -1, '1.5', 'one'):
			with self.subTest(order=order):
				row = self.article(series='教程', series_order=order)
				self.assertEqual(checker.check_metadata(self.root, [row]), ['docs/first.md: series_order must be a positive integer'])

	def test_duplicate_series_order(self):
		rows = [self.article(series='教程', series_order=1), self.article('second', series='教程', series_order='01')]
		self.assertEqual(checker.check_metadata(self.root, rows), ['docs/second.md: duplicate order in series 教程'])

	def test_order_can_repeat_in_a_different_series(self):
		rows = [self.article(series='教程', series_order=1), self.article('second', series='其他教程', series_order=1)]
		self.assertEqual(checker.check_metadata(self.root, rows), [])

	def test_missing_front_matter(self):
		row = self.article()
		self.write(self.root / row['path'], '# Plain Markdown\n')
		self.assertEqual(checker.check_metadata(self.root, [row]), ['docs/first.md: YAML front matter is required'])

	def test_invalid_article_type_and_url(self):
		row = self.article(type='page', url='https://elsewhere.example/post/')
		self.assertEqual(checker.check_metadata(self.root, [row]), ['docs/first.md: type must be post', 'docs/first.md: invalid article URL https://elsewhere.example/post/'])

	def test_non_article_source_rows_are_ignored(self):
		self.assertEqual(checker.check_metadata(self.root, [{'path': 'content/blog/_index.md'}, {'path': 'docs/images/chart.svg'}]), [])


class OutputTests(SiteFixture):
	def test_valid_output_resolves_resources_and_encoded_anchors(self):
		self.write(self.output / 'index.html', '<a href="/post/?q=1#%E7%AB%A0%E8%8A%82">Read</a><link href="/site.css" rel="stylesheet">')
		self.write(self.output / 'post/index.html', '<h2 id="章节">Title</h2><a name="legacy"></a><a href="#legacy">Old anchor</a><img src="../images/a%20b.png" srcset="../images/a%20b.png 1x, ../images/large.png 2x"><video poster="/images/large.png"></video>')
		self.write(self.output / 'site.css', 'body { background: url("images/a%20b.png"); }')
		for name in ('a b.png', 'large.png'):
			self.write(self.output / 'images' / name, 'image fixture')
		self.assertEqual(self.check_output(), [])

	def test_missing_images_in_html_and_css(self):
		self.write(self.output / 'index.html', '<img src="/missing.png" srcset="/wide.png 2x"><video poster="/poster.png"></video><div style="background:url(/inline.png)"></div>')
		self.write(self.output / 'site.css', 'body { background: url("/background.png"); }')
		self.assertCountEqual(self.check_output(), ['index.html: missing target /' + name for name in ('missing.png', 'wide.png', 'poster.png', 'inline.png')] + ['site.css: missing target /background.png'])

	def test_broken_internal_links_and_anchors(self):
		self.write(self.output / 'index.html', '<a href="/absent/">Missing page</a><a href="/post/#wrong">Missing heading</a>')
		self.write(self.output / 'post/index.html', '<h2 id="correct">Heading</h2>')
		self.assertCountEqual(self.check_output(), ['index.html: missing target /absent/', 'index.html: missing anchor /post/#wrong'])

	def test_external_and_non_http_links_are_ignored(self):
		self.write(self.output / 'index.html', '<a href="https://external.example/missing">External</a><img src="//cdn.example/a.png"><a href="mailto:a@example.com">Mail</a><a href="tel:123">Phone</a><img src="data:image/png;base64,abc"><a href="https://zongsoft.com/missing/">Internal</a>')
		self.assertEqual(self.check_output(), ['index.html: missing target https://zongsoft.com/missing/'])

	def test_encoded_paths_cannot_escape_output(self):
		self.write(self.root / 'outside.html', 'Outside file exists')
		self.write(self.output / 'index.html', '<a href="/%2e%2e/outside.html">Escape</a>')
		self.assertEqual(self.check_output(), ['index.html: path escapes output: /%2e%2e/outside.html'])

	def test_empty_output_is_rejected(self):
		self.assertEqual(self.check_output(), ['No generated HTML found in ' + str(self.output.resolve())])


class MainTests(SiteFixture):
	def setUp(self):
		super().setUp()
		self.article()
		file_patch = patch.object(checker, '__file__', str(self.root / 'scripts/check-site.py'))
		file_patch.start()
		self.addCleanup(file_patch.stop)

	def test_hugo_failure_reports_stderr_and_stops(self):
		with patch.object(checker.sys, 'argv', ['check-site.py']), patch.object(checker.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'Hugo failed')) as run, patch.object(checker, 'check_metadata') as metadata, patch.object(checker.sys, 'stderr', new_callable=io.StringIO) as stderr:
			self.assertEqual(checker.main(), 1)
			self.assertEqual(stderr.getvalue(), 'Hugo failed\n')
			metadata.assert_not_called()
			self.assertEqual(run.call_args.args[0], ['hugo', 'list', 'all'])

	def test_success_uses_csv_rows_and_requested_output(self):
		with patch.object(checker.sys, 'argv', ['check-site.py', '--hugo', 'custom-hugo', '--output', 'preview']), patch.object(checker.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'path,title\ndocs/first.md,Title\n', '')) as run, patch.object(checker, 'check_metadata', return_value=[]) as metadata, patch.object(checker, 'check_output', return_value=[]) as output, patch.object(checker.sys, 'stdout', new_callable=io.StringIO) as stdout:
			self.assertEqual(checker.main(), 0)
			root = Path(checker.__file__).resolve().parent.parent
			metadata.assert_called_once_with(root, [{'path': 'docs/first.md', 'title': 'Title'}])
			output.assert_called_once_with(root / 'preview', 'https://zongsoft.com/')
			self.assertEqual(run.call_args.args[0], ['custom-hugo', 'list', 'all'])
			self.assertIn('Site checks: 0 error(s);', stdout.getvalue())

	def test_failure_combines_metadata_and_output_diagnostics(self):
		with patch.object(checker.sys, 'argv', ['check-site.py']), patch.object(checker.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'path\ndocs/first.md\n', '')), patch.object(checker, 'check_metadata', return_value=['bad metadata']), patch.object(checker, 'check_output', return_value=['bad link']), patch.object(checker.sys, 'stdout', new_callable=io.StringIO) as stdout, patch.object(checker.sys, 'stderr', new_callable=io.StringIO) as stderr:
			self.assertEqual(checker.main(), 1)
			self.assertEqual(stderr.getvalue(), 'ERROR: bad metadata\nERROR: bad link\n')
			self.assertIn('Site checks: 2 error(s);', stdout.getvalue())

	def test_invalid_hugo_inventory_is_rejected_before_validation(self):
		cases = [
			('', 'Hugo article list is missing the path column'),
			('title\nTitle\n', 'Hugo article list is missing the path column'),
			('path\n', 'Hugo did not list any docs/*.md articles'),
			('path\ncontent/blog/_index.md\n', 'Article missing from Hugo list: docs/first.md'),
			('path\ndocs/first.md\ndocs/unknown.md\n', 'Hugo listed an unknown article source: docs/unknown.md'),
		]
		for csv_text, expected in cases:
			with self.subTest(csv=csv_text), patch.object(checker.sys, 'argv', ['check-site.py']), patch.object(checker.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, csv_text, '')), patch.object(checker, 'check_metadata') as metadata, patch.object(checker, 'check_output') as output, patch.object(checker.sys, 'stdout', new_callable=io.StringIO), patch.object(checker.sys, 'stderr', new_callable=io.StringIO) as stderr:
				self.assertEqual(checker.main(), 1)
				self.assertIn('ERROR: ' + expected + '\n', stderr.getvalue())
				metadata.assert_not_called()
				output.assert_not_called()

	def test_empty_source_directory_cannot_pass_with_stale_output(self):
		(self.root / 'docs/first.md').unlink()
		self.write(self.output / 'index.html', '<h1>Stale site</h1>')
		with patch.object(checker.sys, 'argv', ['check-site.py']), patch.object(checker.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'path\n', '')), patch.object(checker.sys, 'stdout', new_callable=io.StringIO), patch.object(checker.sys, 'stderr', new_callable=io.StringIO) as stderr:
			self.assertEqual(checker.main(), 1)
			self.assertIn('ERROR: No article source files found in docs\n', stderr.getvalue())

	def test_inventory_normalizes_windows_source_paths(self):
		with patch.object(checker.sys, 'argv', ['check-site.py']), patch.object(checker.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'path\ndocs\\first.md\n', '')), patch.object(checker, 'check_output', return_value=[]), patch.object(checker.sys, 'stdout', new_callable=io.StringIO):
			self.assertEqual(checker.main(), 0)


if __name__ == '__main__':
	unittest.main()
