/** Печать README в PDF через Chromium; зависимости: marked, playwright. */
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

const root = __dirname;
const imagePattern = /<img src="([^"]+\.svg)" alt="([^"]*)"\s*\/?\s*>/g;
const footer = [
  '<div style="font:9px Arial;width:100%;text-align:center;color:#000">',
  'ИКБО-70-25 · Вариант 22 · <span class="pageNumber"></span> / ',
  '<span class="totalPages"></span></div>',
].join('');

/** Встроить существующий векторный граф в HTML без растеризации. */
function embedDiagram(match, source, alt) {
  const svg = fs.readFileSync(path.join(root, source), 'utf8')
    .replace(/<\?xml[^>]*\?>/, '');
  return `<span class="graph" role="img" aria-label="${alt}">${svg}</span>`;
}

/** Создать печатный HTML из Markdown и отдельного файла стилей. */
async function createHtml() {
  const moduleUrl = pathToFileURL(require.resolve('marked')).href;
  const { marked } = await import(moduleUrl);
  const markdown = fs.readFileSync(path.join(root, 'README.md'), 'utf8');
  const body = marked.parse(markdown).replace(imagePattern, embedDiagram);
  const css = fs.readFileSync(path.join(root, 'report.css'), 'utf8');
  const html = [
    '<!doctype html><html lang="ru"><meta charset="utf-8">',
    '<title>Workbook2 — Вариант 22</title>',
    `<style>${css}</style><body>${body}</body></html>`,
  ].join('\n');
  fs.writeFileSync(path.join(root, 'README.html'), html);
}

/** Сохранить загруженную страницу как документ A4 с нумерацией страниц. */
async function printPage(page) {
  const url = pathToFileURL(path.join(root, 'README.html')).href;
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.pdf({
    path: path.join(root, 'README.pdf'),
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: footer,
  });
}

/** Выполнить генерацию и гарантированно закрыть браузер после печати. */
async function main() {
  await createHtml();
  const executablePath = process.env.CHROME_PATH
    || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
  const browser = await chromium.launch({ headless: true, executablePath });
  try {
    await printPage(await browser.newPage());
  } finally {
    await browser.close();
  }
  console.log('README.html and README.pdf created');
}

/** Сообщить ошибку генерации и вернуть ненулевой код завершения. */
function reportFailure(error) {
  console.error(error);
  process.exitCode = 1;
}

main().catch(reportFailure);
