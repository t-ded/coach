// Scroll the messages container to the bottom after action button clicks.
// Chainlit's built-in autoscroll only fires during streaming; action callbacks
// send discrete messages that don't trigger it when the user has scrolled up.
(function () {
  function getScrollableAncestor(el) {
    while (el && el !== document.documentElement) {
      const style = window.getComputedStyle(el);
      if (
        (style.overflowY === 'auto' || style.overflowY === 'scroll') &&
        el.scrollHeight > el.clientHeight
      ) {
        return el;
      }
      el = el.parentElement;
    }
    return document.documentElement;
  }

  document.addEventListener(
    'click',
    function (e) {
      var btn = e.target.closest('button');
      if (!btn) return;

      var container = getScrollableAncestor(btn);

      // Attempt at increasing delays to catch the message as it renders
      [150, 400, 800, 1500].forEach(function (delay) {
        setTimeout(function () {
          container.scrollTop = container.scrollHeight;
        }, delay);
      });
    },
    true,
  );
})();
