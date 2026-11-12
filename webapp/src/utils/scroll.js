// The app renders routed pages inside an overflow-y: auto content pane, so
// the window itself never scrolls; reset the nearest scrollable ancestors of
// `el` as well as the window.
export const scrollToTop = (el) => {
  let node = el && el.parentElement;
  while (node && node !== document.body) {
    const overflowY = window.getComputedStyle(node).overflowY;
    if ((overflowY === 'auto' || overflowY === 'scroll') && node.scrollHeight > node.clientHeight) {
      node.scrollTop = 0;
    }
    node = node.parentElement;
  }
  window.scrollTo(0, 0);
};
