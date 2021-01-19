// MathJax core
import { mathjax } from 'mathjax-full/js/mathjax';

// TeX input
import { TeX } from 'mathjax-full/js/input/tex';

// HTML output
import { CHTML } from 'mathjax-full/js/output/chtml';

import { browserAdaptor } from 'mathjax-full/js/adaptors/browserAdaptor';

import { TeXFont } from 'mathjax-full/js/output/chtml/fonts/tex';

import { RegisterHTMLHandler } from 'mathjax-full/js/handlers/html';

import { AllPackages } from 'mathjax-full/js/input/tex/AllPackages';

// Register the HTML document handler
RegisterHTMLHandler(browserAdaptor());

// Override dynamically generated fonts in favor
// of our font css that is picked up by webpack.
class emptyFont extends TeXFont {}
emptyFont.defaultFonts = {};

const chtml = new CHTML({
  font: new emptyFont()
});

const tex = new TeX({
  packages: AllPackages,
  inlineMath: [
    ['$', '$'],
    ['\\(', '\\)']
  ],
  displayMath: [
    ['$$', '$$'],
    ['\\[', '\\]']
  ],
  processEscapes: true,
  processEnvironments: true
});

// initialize mathjax with with the browser DOM document; other documents are possible
const html = mathjax.document(document, {
  InputJax: tex,
  OutputJax: chtml
});

export function renderMathJax() {
  html
    .findMath()
    .compile()
    .getMetrics()
    .typeset()
    .updateDocument()
    .reset();
}
