(function () {
  'use strict';

  if (window.ClipboardJS) return;

  function ClipboardJS(selector, options) {
    this.selector = selector;
    this.options = options || {};
  }

  ClipboardJS.prototype.on = function () {
    return this;
  };

  ClipboardJS.prototype.destroy = function () {};

  window.ClipboardJS = ClipboardJS;
})();
