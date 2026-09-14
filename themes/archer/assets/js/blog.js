(() => {
	const root = document.documentElement;
	const themeButton = document.querySelector('.theme-button');
	const syncTheme = () => themeButton.setAttribute('aria-pressed', String(root.dataset.theme === 'dark'));
	syncTheme();
	themeButton.addEventListener('click', () => {
		root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
		try { localStorage.setItem('zongsoft-theme', root.dataset.theme); } catch (_) {}
		syncTheme();
	});
	const menu = document.querySelector('#site-menu');
	const menuButton = document.querySelector('.menu-button');
	menuButton.addEventListener('click', () => {
		menu.showModal();
		menuButton.setAttribute('aria-expanded', 'true');
	});
	menu.querySelector('[data-close-menu]').addEventListener('click', () => menu.close());
	menu.addEventListener('close', () => menuButton.setAttribute('aria-expanded', 'false'));
	menu.addEventListener('click', event => { if (event.target === menu && event.offsetX > menu.clientWidth) menu.close(); });
	const topLink = document.querySelector('.back-top');
	const updateScroll = () => topLink.classList.toggle('visible', window.scrollY > 400);
	window.addEventListener('scroll', updateScroll, { passive: true });
	updateScroll();
	const copy = async (button, text, done) => {
		const original = button.textContent;
		try {
			await navigator.clipboard.writeText(text);
			button.textContent = done;
		} catch (_) {
			button.textContent = '复制失败，请手动复制';
		}
		window.setTimeout(() => { button.textContent = original; }, 2200);
	};
	document.querySelector('.share-button')?.addEventListener('click', event => copy(event.currentTarget, document.querySelector('link[rel="canonical"]').href, '链接已复制'));
	document.querySelectorAll('.article-entry h1[id], .article-entry h2[id], .article-entry h3[id], .article-entry h4[id], .article-entry h5[id], .article-entry h6[id]').forEach(heading => {
		const button = document.createElement('button');
		button.type = 'button';
		button.className = 'heading-copy';
		button.textContent = '#';
		button.setAttribute('aria-label', '复制章节链接：' + heading.textContent.trim());
		button.addEventListener('click', () => {
			const url = new URL(document.querySelector('link[rel="canonical"]').href);
			url.hash = heading.id;
			copy(button, url.href, '已复制');
		});
		heading.append(button);
	});
	document.querySelectorAll('.article-entry pre').forEach(pre => {
		const block = pre.closest('.highlight') || pre;
		const button = document.createElement('button');
		button.type = 'button';
		button.className = 'copy-code';
		button.textContent = '复制';
		button.setAttribute('aria-label', '复制代码');
		button.addEventListener('click', () => {
			const code = pre.querySelector('code').cloneNode(true);
			code.querySelectorAll('[style*="user-select"], .ln, .lnt').forEach(lineNumber => lineNumber.remove());
			copy(button, code.textContent, '已复制');
		});
		block.append(button);
	});
	const viewer = document.querySelector('.image-viewer');
	document.querySelectorAll('.article-entry img:not(a img)').forEach(img => {
		img.tabIndex = 0;
		img.setAttribute('role', 'button');
		img.setAttribute('aria-label', `放大图片：${img.alt}`);
		const show = () => {
			viewer.querySelector('img').src = img.currentSrc;
			viewer.querySelector('img').alt = img.alt;
			viewer.showModal();
		};
		img.addEventListener('click', show);
		img.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); show(); } });
	});
	viewer.addEventListener('click', () => viewer.close());
	const tocLinks = [...document.querySelectorAll('.toc a')];
	if (tocLinks.length) {
		const observer = new IntersectionObserver(entries => {
			const visible = entries.filter(entry => entry.isIntersecting);
			if (!visible.length) return;
			tocLinks.forEach(link => link.classList.toggle('active', decodeURIComponent(link.hash.slice(1)) === visible[0].target.id));
		}, { rootMargin: '-5% 0px -70% 0px' });
		document.querySelectorAll('.article-entry h1[id], .article-entry h2[id], .article-entry h3[id], .article-entry h4[id]').forEach(heading => observer.observe(heading));
	}
})();
