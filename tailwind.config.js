/** @type {import('tailwindcss').Config} */
module.exports = {
	content: ['./index.html'],
	theme: {
		extend: {
			colors: {
				brand: {
					navy: '#05085f',
					ink: '#090d4d',
					red: '#f3232e',
					line: '#dfe2ee',
					mist: '#f6f7fb'
				}
			},
			fontFamily: {
				sans: ['Titillium Web', 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', 'sans-serif']
			},
			maxWidth: {
				page: '1440px'
			}
		}
	},
	plugins: []
};
