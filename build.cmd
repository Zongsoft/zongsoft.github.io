@echo off

echo Initialize the site.
hexo init site

del /Q site\.gitignore
move /Y site\*.* .
move /Y site\node_modules node_modules
move /Y site\scaffolds scaffolds
rmdir /S /Q site

echo Install the plugins for Hexo and the Archer theme.
npm i hexo-generator-json-content --save && npm i hexo-wordcount --save && git clone https://github.com/fi3ework/hexo-theme-archer.git themes/archer

echo Replace the Hexo default configuration file.
copy /Y hexo.config.yml _config.yml

echo Replace the Archer theme default configuration file.
copy /Y hexo.config-theme.archer.yml themes\archer\_config.yml

echo Install the site
npm install
