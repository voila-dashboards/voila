// This is more or less copied from the nbconvert reveal template
import Reveal from 'reveal.js';
// @ts-expect-error should probably look it up
import Notes from 'reveal.js/plugin/notes';

// @ts-expect-error It's provided by the template
const MathJax = window.MathJax;

// @ts-expect-error It's provided by the template
const reveal_transition = window.reveal_transition;
// @ts-expect-error It's provided by the template
const reveal_number = window.reveal_number;
// @ts-expect-error It's provided by the template
const reveal_width = window.reveal_width;
// @ts-expect-error It's provided by the template
const reveal_height = window.reveal_height;
// @ts-expect-error It's provided by the template
const reveal_scroll = window.reveal_scroll;
// @ts-expect-error It's provided by the template
const $ = window.$;

// Full list of configuration options available here: https://github.com/hakimel/reveal.js#configuration
Reveal.initialize({
  controls: true,
  progress: true,
  history: true,
  transition: reveal_transition,
  slideNumber: reveal_number,
  plugins: [Notes],
  width: reveal_width,
  height: reveal_height
});

const update = function () {
  if (MathJax.Hub.getAllJax(Reveal.getCurrentSlide())) {
    MathJax.Hub.Rerender(Reveal.getCurrentSlide());
  }
};

Reveal.addEventListener('slidechanged', update);

function setScrollingSlide() {
  const scroll = reveal_scroll;
  if (scroll === true) {
    const h = ($('.reveal').height() ?? 0) * 0.95;
    $('section.present')
      .find('section')
      .filter(function () {
        // @ts-expect-error hey
        return $(this).height() > h;
      })
      .css('height', 'calc(95vh)')
      .css('overflow-y', 'scroll')
      .css('margin-top', '20px');
  }
}

// check and set the scrolling slide every time the slide change
Reveal.addEventListener('slidechanged', setScrollingSlide);
