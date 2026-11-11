// npm install --no-save marked playwright (если библиотеки еще не доступны).
// NODE_PATH может указывать на каталог готовых Node.js-зависимостей.
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

async function main() {
  const { marked } = await import(pathToFileURL(require.resolve('marked')).href);
  const { chromium } = require('playwright');
  const root = __dirname;
  const body = marked.parse(fs.readFileSync(path.join(root, 'README.md'), 'utf8')).replace(
    /<img src="([^"]+\.svg)" alt="([^"]*)"\s*\/?\s*>/g,
    (_, source, alt) => {
      // В печатной версии сохраняем векторные графы, заменяя цвета на черный/белый.
      const svg = fs.readFileSync(path.join(root, source), 'utf8')
        .replace(/<\?xml[^>]*\?>/, '')
        .replace(/#[0-9a-fA-F]{6}\b/g, color => {
          const rgb = [1, 3, 5].map(offset => parseInt(color.slice(offset, offset + 2), 16));
          return rgb.reduce((sum, value) => sum + value, 0) / 3 > 180 ? '#FFFFFF' : '#000000';
        });
      return `<span class="graph" role="img" aria-label="${alt}">${svg}</span>`;
    });
  const html = `<!doctype html><html lang="ru"><meta charset="utf-8"><title>Workbook2 — Вариант 22</title>
  <style>
  @page {size:A4; margin:16mm 15mm 18mm}
  body {font:10.5pt/1.45 'Arial',sans-serif; color:#000; background:#fff; max-width:1000px; margin:28px auto}
  h1 {font-size:25pt;line-height:1.15;color:#000} h2{font-size:16pt;color:#000;margin-top:24px}
  h1,h2,h3 {break-after:avoid} p,li{orphans:3;widows:3}
  pre {font:9pt/1.4 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#fff;border:1px solid #000;padding:12px;break-inside:avoid}
  code {font-family:Consolas,monospace;font-size:9pt;overflow-wrap:anywhere}
  table{border-collapse:collapse;width:100%;font-size:9pt;margin:14px 0} th,td{border:1px solid #000;padding:6px;text-align:left;overflow-wrap:anywhere}
  th{background:#fff} tr{break-inside:avoid} thead{display:table-header-group}
  img{display:block;max-width:100%;max-height:225mm;margin:12px auto;break-inside:avoid}
  .graph{display:block;break-inside:avoid;margin:12px auto;text-align:center}
  .graph>svg{display:block;max-width:100%;max-height:225mm;margin:auto}
  a,a:visited{color:#000;overflow-wrap:anywhere} @media print{body{margin:0;max-width:none}}
  </style><body>${body}</body></html>`;
  fs.writeFileSync(path.join(root,'README.html'), html);
  const browser = await chromium.launch({headless:true, executablePath:process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(path.join(root,'README.html')).href, {waitUntil:'networkidle'});
    await page.pdf({path:path.join(root,'README.pdf'),format:'A4',printBackground:true,preferCSSPageSize:true,
      displayHeaderFooter:true,headerTemplate:'<span></span>',
      footerTemplate:'<div style="font:9px Arial;width:100%;text-align:center;color:#000">ИКБО-70-25 · Вариант 22 · <span class="pageNumber"></span> / <span class="totalPages"></span></div>'});
  } finally { await browser.close(); }
  console.log('README.html and README.pdf created');
}
main().catch(error => {console.error(error);process.exitCode=1});
