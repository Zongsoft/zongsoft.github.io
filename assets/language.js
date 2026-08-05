(() => {
	const preferenceKey = 'zongsoft-language';
	const currentLanguage = document.documentElement.lang.toLowerCase().startsWith('zh') ? 'zh-CN' : 'en';
	const rootPath = window.location.pathname.replace(/\/+$/, '') || '/';
	let savedLanguage = null;

	try {
		savedLanguage = window.localStorage.getItem(preferenceKey);
	} catch {
		savedLanguage = null;
	}

	if (rootPath === '/') {
		const browserLanguage = (navigator.languages?.[0] || navigator.language || '').toLowerCase();
		const preferredLanguage = savedLanguage || (browserLanguage.startsWith('zh') ? 'zh-CN' : 'en');

		if (preferredLanguage === 'en' && currentLanguage !== 'en') {
			window.location.replace(`/en/${window.location.search}${window.location.hash}`);
			return;
		}
	}

	const bindLanguageLinks = () => {
		document.querySelectorAll('[data-language]').forEach((link) => {
			link.addEventListener('click', () => {
				try {
					window.localStorage.setItem(preferenceKey, link.dataset.language);
				} catch {
					// Language switching still works when storage is unavailable.
				}
			});
		});
	};

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', bindLanguageLinks, { once: true });
	} else {
		bindLanguageLinks();
	}
})();
