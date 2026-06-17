(function () {
  'use strict';

  window.DOCUMENT_URL = new URL(window.location.href);

  window.get_root_domain = function get_root_domain() {
    var parts = window.location.hostname.split('.');
    return parts.length > 2 ? parts.slice(-2).join('.') : window.location.hostname;
  };

  window.get_parm = function get_parm(name) {
    return new URLSearchParams(window.location.search).get(name) || '';
  };

  window.url_path = function url_path() {
    return window.location.origin + window.location.pathname;
  };

  window.get_api_url = function get_api_url() {
    return window.DOVERABOT_API_URL || 'https://api.doverabot.ru';
  };

  function write_auth_cookie(raw) {
    var cookie = 'auth_data=' + encodeURIComponent(raw) + '; Max-Age=2592000; Path=/; SameSite=Lax';
    if (window.location.protocol === 'https:') cookie += '; Secure';
    if (window.location.hostname === 'doverabot.ru' || window.location.hostname.endsWith('.doverabot.ru')) {
      cookie += '; Domain=.doverabot.ru';
    }
    document.cookie = cookie;
  }

  function store_auth_data(authData) {
    var raw = JSON.stringify(authData);
    try {
      window.localStorage.setItem('auth_data', raw);
      window.localStorage.setItem('doverabot_auth', raw);
    } catch (e) {
      // localStorage can be unavailable in restricted browser contexts.
    }
    try {
      write_auth_cookie(raw);
    } catch (e) {
      // Cookie storage is a compatibility path; auth still works from localStorage.
    }
    return raw;
  }

  function get_auth_cookie_raw() {
    var matches = document.cookie.match(new RegExp('(?:^|; )auth_data=([^;]*)'));
    return matches ? decodeURIComponent(matches[1]) : '';
  }

  function get_stored_auth_raw() {
    try {
      var localRaw = window.localStorage.getItem('auth_data') ||
        window.localStorage.getItem('doverabot_auth');
      if (localRaw) return localRaw;
    } catch (e) {
      // Continue to sessionStorage/cookie fallback.
    }
    try {
      var sessionRaw = window.sessionStorage.getItem('auth_data') ||
        window.sessionStorage.getItem('doverabot_auth');
      if (sessionRaw) return sessionRaw;
    } catch (e) {
      // Continue to cookie fallback.
    }
    return get_auth_cookie_raw();
  }

  function remove_authdata_token_from_url() {
    if (!window.history || !window.history.replaceState) return;
    var url = new URL(window.location.href);
    url.searchParams.delete('authdata_token');
    window.history.replaceState(window.history.state, document.title, url.toString());
    window.DOCUMENT_URL = new URL(window.location.href);
  }

  async function redeem_authdata_token() {
    var token = new URLSearchParams(window.location.search).get('authdata_token');
    if (!token) return null;

    var url = new URL('/api/token/authdata/', window.get_api_url());
    url.searchParams.set('token', token);

    try {
      var response = await fetch(url.toString(), {
        method: 'GET',
        credentials: 'omit'
      });
      if (!response.ok) return null;
      var data = await response.json();
      if (!data || typeof data !== 'object' || Array.isArray(data) || !data.auth_token) return null;
      store_auth_data(data);
      remove_authdata_token_from_url();
      return data;
    } catch (e) {
      return null;
    }
  }

  var authdata_token_promise = redeem_authdata_token();

  window.redeem_authdata_token = function redeem_authdata_token_once() {
    return authdata_token_promise;
  };

  window.check_auth = async function check_auth(required) {
    var redeemedAuthData = await window.redeem_authdata_token();
    if (redeemedAuthData) return redeemedAuthData;

    var raw = get_stored_auth_raw();
    if (!raw) {
      if (required) {
        var modal = document.getElementById('dialogModal');
        var text = document.getElementById('dialogText');
        if (text) text.textContent = 'Требуется авторизация через Telegram.';
        if (modal) modal.style.display = 'block';
      }
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch (e) {
      return null;
    }
  };

  window.api_request = async function api_request(url, options) {
    options = options || {};
    var requestUrl = url instanceof URL ? url : new URL(String(url), window.location.origin);
    if (options.params) {
      Object.keys(options.params).forEach(function (key) {
        var value = options.params[key];
        if (value !== undefined && value !== null) requestUrl.searchParams.set(key, value);
      });
    }

    var init = {
      method: options.method || 'GET',
      headers: {},
      credentials: 'omit'
    };

    if (options.auth_token) {
      init.headers.Authorization = 'Token ' + options.auth_token;
    }
    if (options.json) {
      init.headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(options.json);
    } else if (options.form_data) {
      var form = new FormData();
      Object.keys(options.form_data).forEach(function (key) {
        var value = options.form_data[key];
        if (value !== undefined && value !== null) form.append(key, value);
      });
      init.body = form;
    }

    try {
      var response = await fetch(requestUrl.toString(), init);
      var contentType = response.headers.get('content-type') || '';
      var data = contentType.indexOf('application/json') >= 0
        ? await response.json()
        : await response.text();
      return { ok: response.ok, status: response.status, data: data };
    } catch (e) {
      return { ok: false, status: 0, data: { message: e && e.message ? e.message : String(e) } };
    }
  };

  window.api_alert = function api_alert(response, prefix) {
    if (response && response.ok) return false;
    var message = prefix || 'Ошибка доступа к системе';
    if (response && response.data) {
      if (typeof response.data === 'string') message += ': ' + response.data;
      else if (response.data.message) message += ': ' + response.data.message;
      else if (response.data.detail) message += ': ' + response.data.detail;
    }
    alert(message);
    return true;
  };

  document.addEventListener('click', function (event) {
    if (event.target && event.target.classList && event.target.classList.contains('d-modal-close')) {
      var modal = document.getElementById('dialogModal');
      if (modal) modal.style.display = 'none';
    }
  });
})();
