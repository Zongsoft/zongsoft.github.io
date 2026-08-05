/** @type {import('tailwindcss').Config} */
module.exports = {
	content: ['./index.html', './en/**/*.html'],
	theme: {
		extend: {
			colors: {
				brand: {
					navy: '#133A58',
					ink: '#133A58',
					red: '#FF6800',
					line: '#DFE7EE',
					mist: '#DFE7EE'
				}
			},
			fontFamily: {
				sans: ['Oswald-Regular', '-apple-system', 'BlinkMacSystemFont', 'Helvetica Neue', 'Arial', 'PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Microsoft YaHei', 'Microsoft JhengHei', 'Source Han Sans SC', 'Noto Sans CJK SC', 'Source Han Sans CN', 'Noto Sans SC', 'Source Han Sans TC', 'Noto Sans CJK TC', 'WenQuanYi Micro Hei', 'SimSun', 'sans-serif']
			},
			maxWidth: {
				page: '1440px'
			}
		}
	},
	plugins: []
};
