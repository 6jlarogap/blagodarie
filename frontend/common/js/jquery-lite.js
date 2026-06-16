(function () {
  'use strict';

  if (window.jQuery && window.$) return;

  function toArray(value) {
    if (!value) return [];
    if (value instanceof LiteQuery) return value.toArray();
    if (typeof value === 'string') return Array.prototype.slice.call(document.querySelectorAll(value));
    if (value === window || value === document || value.nodeType) return [value];
    if (typeof value.length === 'number') return Array.prototype.slice.call(value);
    return [value];
  }

  function cssName(name) {
    return String(name).replace(/-([a-z])/g, function (_, letter) {
      return letter.toUpperCase();
    });
  }

  var defaultDisplays = {};

  function defaultDisplay(tagName) {
    var name = String(tagName).toLowerCase();
    if (defaultDisplays[name]) return defaultDisplays[name];

    var element = document.createElement(name);
    document.body.appendChild(element);
    var display = window.getComputedStyle(element).display;
    document.body.removeChild(element);

    defaultDisplays[name] = display === 'none' ? 'block' : display;
    return defaultDisplays[name];
  }

  function LiteQuery(value) {
    var nodes = toArray(value);
    this.length = nodes.length;
    for (var i = 0; i < nodes.length; i += 1) this[i] = nodes[i];
  }

  LiteQuery.prototype.toArray = function () {
    var result = [];
    for (var i = 0; i < this.length; i += 1) result.push(this[i]);
    return result;
  };

  LiteQuery.prototype.each = function (callback) {
    for (var i = 0; i < this.length; i += 1) callback.call(this[i], i, this[i]);
    return this;
  };

  LiteQuery.prototype.css = function (name, value) {
    if (typeof name === 'object') {
      return this.each(function () {
        for (var key in name) this.style[cssName(key)] = name[key];
      });
    }
    if (value === undefined) {
      if (!this[0]) return undefined;
      return window.getComputedStyle(this[0]).getPropertyValue(name) || this[0].style[cssName(name)];
    }
    return this.each(function () {
      this.style[cssName(name)] = value;
    });
  };

  LiteQuery.prototype.show = function () {
    return this.each(function () {
      this.style.display = '';
      if (window.getComputedStyle(this).display === 'none') this.style.display = defaultDisplay(this.tagName);
    });
  };

  LiteQuery.prototype.hide = function () {
    return this.css('display', 'none');
  };

  LiteQuery.prototype.val = function (value) {
    if (value === undefined) return this[0] ? this[0].value : undefined;
    return this.each(function () {
      this.value = value;
    });
  };

  LiteQuery.prototype.html = function (value) {
    if (value === undefined) return this[0] ? this[0].innerHTML : undefined;
    return this.each(function () {
      this.innerHTML = value;
    });
  };

  LiteQuery.prototype.text = function (value) {
    if (value === undefined) return this[0] ? this[0].textContent : undefined;
    return this.each(function () {
      this.textContent = value;
    });
  };

  LiteQuery.prototype.prop = function (name, value) {
    if (value === undefined) return this[0] ? this[0][name] : undefined;
    return this.each(function () {
      this[name] = value;
    });
  };

  LiteQuery.prototype.attr = function (name, value) {
    if (value === undefined) return this[0] ? this[0].getAttribute(name) : undefined;
    return this.each(function () {
      this.setAttribute(name, value);
    });
  };

  LiteQuery.prototype.addClass = function (className) {
    return this.each(function () {
      this.classList.add(className);
    });
  };

  LiteQuery.prototype.removeClass = function (className) {
    return this.each(function () {
      this.classList.remove(className);
    });
  };

  LiteQuery.prototype.on = function (events, handler) {
    var names = String(events).split(/\s+/);
    return this.each(function () {
      var element = this;
      names.forEach(function (name) {
        if (name) element.addEventListener(name, handler);
      });
    });
  };

  LiteQuery.prototype.click = function (handler) {
    if (handler) return this.on('click', handler);
    return this.each(function () {
      this.click();
    });
  };

  LiteQuery.prototype.change = function (handler) {
    if (handler) return this.on('change', handler);
    return this.each(function () {
      this.dispatchEvent(new Event('change', { bubbles: true }));
    });
  };

  LiteQuery.prototype.remove = function () {
    return this.each(function () {
      if (this.parentNode) this.parentNode.removeChild(this);
    });
  };

  function $(value) {
    if (typeof value === 'function') {
      if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', value);
      else value();
      return new LiteQuery([]);
    }
    return new LiteQuery(value);
  }

  $.fn = LiteQuery.prototype;
  window.jQuery = window.$ = $;
})();
