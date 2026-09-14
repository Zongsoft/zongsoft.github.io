(() => {
	const input = document.querySelector('#search-query');
	const status = document.querySelector('#search-status');
	const results = document.querySelector('#search-results');
	const entries = JSON.parse(document.querySelector('#search-data').textContent).map(entry => ({
		...entry,
		normalized: (entry.title + ' ' + entry.tags.join(' ') + ' ' + entry.text).normalize('NFKC').toLocaleLowerCase(),
	}));
	const render = () => {
		const query = input.value.trim().normalize('NFKC').toLocaleLowerCase();
		const terms = [...new Set(query.split(/\s+/).filter(Boolean))];
		results.replaceChildren();
		if (!terms.length) {
			status.textContent = '输入关键词开始搜索，多个关键词以空格分隔。';
			return;
		}
		const matches = entries.filter(entry => terms.every(term => entry.normalized.includes(term)))
			.map(entry => ({...entry, score: terms.filter(term => entry.title.normalize('NFKC').toLocaleLowerCase().includes(term)).length}))
			.sort((a, b) => b.score - a.score);
		status.textContent = matches.length ? '找到 ' + matches.length + ' 篇文章' : '没有找到匹配文章，请尝试其他关键词。';
		for (const entry of matches) {
			const article = document.createElement('article');
			article.className = 'search-result';
			const heading = document.createElement('h2');
			const link = document.createElement('a');
			link.href = entry.url;
			link.textContent = entry.title;
			heading.append(link);
			const date = document.createElement('time');
			date.textContent = entry.date;
			const snippet = document.createElement('p');
			const text = entry.text.replace(/\s+/g, ' ');
			const firstMatch = text.toLocaleLowerCase().indexOf(terms[0]);
			const start = Math.max(0, firstMatch - 50);
			snippet.textContent = (start ? '…' : '') + text.slice(start, start + 240) + (text.length > start + 240 ? '…' : '');
			article.append(heading, date, snippet);
			results.append(article);
		}
	};
	let timer;
	input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(render, 120); });
})();
