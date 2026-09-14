(() => {
	const counter = document.querySelector('[data-counter-site]');
	if (!counter || location.protocol !== 'https:' || location.hostname !== 'zongsoft.com') return;
	const endpoint = counter.dataset.counterSite;
	const path = counter.dataset.counterPath;
	const script = document.createElement('script');
	script.src = 'https://gc.zgo.at/count.js';
	script.async = true;
	script.dataset.goatcounter = endpoint + '/count';
	script.dataset.goatcounterSettings = JSON.stringify({path, no_events: true});
	document.head.append(script);
	const controller = new AbortController();
	const timeout = setTimeout(() => controller.abort(), 6000);
	fetch(endpoint + '/counter/' + encodeURIComponent(path) + '.json', {signal: controller.signal, credentials: 'omit'})
		.then(response => { if (!response.ok) throw new Error('Counter unavailable'); return response.json(); })
		.then(data => {
			const value = String(data.count ?? '');
			if (!/^\d[\d,]*$/.test(value)) return;
			counter.textContent = value + ' 次浏览';
			counter.hidden = false;
		})
		.catch(() => {})
		.finally(() => clearTimeout(timeout));
})();
