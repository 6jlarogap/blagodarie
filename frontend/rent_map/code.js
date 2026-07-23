(function () {
  'use strict';

  var SEARCH_LIMIT = 50;
  var MOSCOW = [55.75222, 37.61556];
  var FILTER_KEYS = [
    'rental_query',
    'rental_equipment_type',
    'rental_date_from',
    'rental_date_to',
    'rental_price_max',
    'rental_trusted_only',
    'rental_uuid'
  ];
  var BOUNDS_KEYS = ['lat_south', 'lat_north', 'lng_west', 'lng_east'];

  // SUBJECT_VISUALS_START
  var SUBJECT_VISUALS = Object.freeze({
    person: Object.freeze({ shape: 'circle', badge: '', label: 'Человек' }),
    organization: Object.freeze({ shape: 'rounded-square', badge: '🏢', label: 'Организация' }),
    bot: Object.freeze({ shape: 'square', badge: '⚙', label: 'Бот' }),
    group: Object.freeze({ shape: 'hexagon', badge: '👥', label: 'Группа' }),
    channel: Object.freeze({ shape: 'diamond', badge: '📣', label: 'Канал' }),
    unknown: Object.freeze({ shape: 'circle', badge: '?', label: 'Неизвестно' })
  });

  function subjectVisualFor(subject) {
    var rawKind = subject && subject.subject_kind;
    var kind = Object.prototype.hasOwnProperty.call(SUBJECT_VISUALS, rawKind) ? rawKind : 'person';
    if (!rawKind && subject && subject.is_org) kind = 'organization';
    var visual = SUBJECT_VISUALS[kind];
    return Object.assign({ kind: kind || 'person', confirmed: subject && subject.subject_kind_confirmed !== false }, visual);
  }

  if (typeof window !== 'undefined') {
    window.DoverabotSubjectVisuals = { SUBJECT_VISUALS: SUBJECT_VISUALS, subjectVisualFor: subjectVisualFor };
  }
  // SUBJECT_VISUALS_END

  var el = {};
  var state = {
    auth: null,
    botUsername: 'DoveraBot',
    map: null,
    markers: {},
    points: [],
    offers: [],
    selectedUuid: '',
    viewportBounds: null,
    sheetExpanded: false
  };

  function $(id) {
    return document.getElementById(id);
  }

  function setText(node, value) {
    node.textContent = value == null ? '' : String(value);
  }

  function value(id) {
    return ($(id).value || '').trim();
  }

  function isTruthy(value) {
    return value && !/^(0|false|off|no|нет)$/i.test(String(value));
  }

  function apiUrl(path) {
    return new URL(path, window.get_api_url());
  }

  function apiGet(path, params) {
    return window.api_request(apiUrl(path), { params: params });
  }

  function currentFilters() {
    return {
      rental_query: value('filterQuery'),
      rental_equipment_type: value('filterEquipment'),
      rental_date_from: value('filterDateFrom'),
      rental_date_to: value('filterDateTo'),
      rental_price_max: value('filterPriceMax'),
      rental_trusted_only: $('filterTrustedOnly').checked ? 'on' : '',
      rental_uuid: state.selectedUuid || ''
    };
  }

  function boundsParams() {
    var params = {};
    if (!state.viewportBounds) return params;
    BOUNDS_KEYS.forEach(function (key) {
      if (state.viewportBounds[key] !== undefined && state.viewportBounds[key] !== null) {
        params[key] = state.viewportBounds[key];
      }
    });
    return params;
  }

  function viewerParams() {
    var params = {};
    if (state.auth && state.auth.user_uuid) params.user_uuid = state.auth.user_uuid;
    if (state.auth && state.auth.auth_token) params.auth_token = state.auth.auth_token;
    return params;
  }

  function searchParams() {
    var filters = currentFilters();
    var params = viewerParams();
    params.number = SEARCH_LIMIT;
    if (filters.rental_query) params.query = filters.rental_query;
    if (filters.rental_equipment_type) params.equipment_type = filters.rental_equipment_type;
    if (filters.rental_date_from) params.date_from = filters.rental_date_from;
    if (filters.rental_date_to) params.date_to = filters.rental_date_to;
    if (filters.rental_price_max) params.price_max = filters.rental_price_max;
    if (filters.rental_trusted_only) params.trusted_only = filters.rental_trusted_only;
    return Object.assign(params, boundsParams());
  }

  function pointParams() {
    var filters = currentFilters();
    var params = viewerParams();
    params.rental = 'on';
    FILTER_KEYS.forEach(function (key) {
      if (filters[key]) params[key] = filters[key];
    });
    return Object.assign(params, boundsParams());
  }

  function initFiltersFromUrl() {
    var params = new URLSearchParams(window.location.search);
    $('filterQuery').value = params.get('rental_query') || '';
    $('filterEquipment').value = params.get('rental_equipment_type') || '';
    $('filterDateFrom').value = params.get('rental_date_from') || '';
    $('filterDateTo').value = params.get('rental_date_to') || '';
    $('filterPriceMax').value = params.get('rental_price_max') || '';
    $('filterTrustedOnly').checked = isTruthy(params.get('rental_trusted_only'));
    state.selectedUuid = params.get('rental_uuid') || '';
    var bounds = {};
    var hasBounds = BOUNDS_KEYS.every(function (key) {
      var raw = params.get(key);
      if (raw === null || raw === '') return false;
      var parsed = Number(raw);
      if (!Number.isFinite(parsed)) return false;
      bounds[key] = parsed;
      return true;
    });
    state.viewportBounds = hasBounds ? bounds : null;
  }

  function updateUrlState() {
    if (!window.history || !window.history.replaceState) return;
    var url = new URL(window.location.href);
    var filters = currentFilters();
    FILTER_KEYS.forEach(function (key) {
      if (filters[key]) url.searchParams.set(key, filters[key]);
      else url.searchParams.delete(key);
    });
    if (state.viewportBounds) {
      BOUNDS_KEYS.forEach(function (key) {
        url.searchParams.set(key, state.viewportBounds[key]);
      });
    } else {
      BOUNDS_KEYS.forEach(function (key) {
        url.searchParams.delete(key);
      });
    }
    window.history.replaceState(window.history.state, document.title, url.toString());
    window.DOCUMENT_URL = new URL(window.location.href);
  }

  function setMessage(message, isError) {
    setText(el.stateMessage, message || '');
    el.stateMessage.classList.toggle('is-error', Boolean(isError));
  }

  function setMapStatus(message) {
    setText(el.mapStatus, message || '');
  }

  function setLoading(isLoading) {
    el.filterForm.classList.toggle('is-loading', Boolean(isLoading));
    el.filterForm.querySelectorAll('button, input, select').forEach(function (node) {
      node.disabled = Boolean(isLoading);
    });
  }

  function renderLoading() {
    el.listingList.innerHTML = '';
    for (var i = 0; i < 3; i += 1) {
      var item = document.createElement('div');
      item.className = 'listing-card skeleton-card';
      item.innerHTML = '<span></span><span></span><span></span>';
      el.listingList.appendChild(item);
    }
  }

  function formatPrice(offer) {
    if (offer.price_text) return offer.price_text;
    if (offer.price_amount) {
      return [offer.price_amount, offer.price_currency, offer.price_period].filter(Boolean).join(' ');
    }
    return 'Цена не указана';
  }

  function formatAvailability(offer) {
    var parts = [];
    if (offer.availability_text) parts.push(offer.availability_text);
    if (offer.available_from || offer.available_to) {
      parts.push((offer.available_from || '?') + ' - ' + (offer.available_to || '?'));
    }
    return parts.join(' · ') || 'Даты не указаны';
  }

  function equipmentLabel(type) {
    var labels = type.labels || {};
    if (labels.ru && labels.ru.length) return labels.ru[0];
    if (labels.en && labels.en.length) return labels.en[0];
    return type.canonical_name || type.slug || '';
  }

  function titleOf(offer) {
    return offer.title || offer.item_text || 'Прокат';
  }

  function telegramUrl(offer) {
    return 'https://t.me/' + encodeURIComponent(state.botUsername) + '?start=rent-' + encodeURIComponent(offer.uuid);
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (char) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char];
    });
  }

  function subjectLabel(point) {
    var visual = subjectVisualFor(point);
    return point.subject_kind_label || visual.label;
  }

  function mediaItems(offer) {
    return (offer.media || []).filter(function (item) {
      return item && (item.thumbnail_url || item.file_type);
    });
  }

  function renderMedia(offer, card) {
    var media = mediaItems(offer);
    if (!media.length) return;
    var strip = document.createElement('div');
    strip.className = 'media-strip';
    media.slice(0, 4).forEach(function (item, index) {
      var thumb = document.createElement('div');
      thumb.className = 'media-thumb';
      if (item.thumbnail_url) {
        var image = document.createElement('img');
        image.src = item.thumbnail_url;
        image.loading = 'lazy';
        image.alt = item.caption || titleOf(offer);
        image.addEventListener('error', function () {
          thumb.classList.add('is-placeholder');
          thumb.textContent = item.file_type || 'media';
          image.remove();
        });
        thumb.appendChild(image);
      } else {
        thumb.classList.add('is-placeholder');
        thumb.textContent = item.file_type || 'media';
      }
      if (index === 3 && media.length > 4) {
        var more = document.createElement('span');
        more.className = 'media-more';
        more.textContent = '+' + String(media.length - 4);
        thumb.appendChild(more);
      }
      strip.appendChild(thumb);
    });
    card.appendChild(strip);
  }

  function markerHtml(point, selected) {
    var visual = subjectVisualFor(point);
    var classes = [
      'rent-marker',
      'subject-marker',
      'subject-kind-' + visual.kind,
      selected ? 'is-selected' : '',
      visual.confirmed ? '' : 'is-unconfirmed'
    ].filter(Boolean).join(' ');
    var badge = visual.badge ? '<span class="subject-marker-badge">' + escapeHtml(visual.badge) + '</span>' : '';
    var label = escapeHtml((point.title || 'Прокат') + ': ' + subjectLabel(point));
    return (
      '<div class="' + classes + '" role="img" aria-label="' + label + '" title="' + label + '">' +
      '<span class="rent-marker-frame subject-shape-' + visual.shape + '"><span>R</span></span>' +
      badge +
      '</div>'
    );
  }

  function appendFallbackSubject(button, point) {
    var visual = subjectVisualFor(point);
    var marker = document.createElement('span');
    marker.className = 'fallback-subject subject-shape-' + visual.shape + (visual.confirmed ? '' : ' is-unconfirmed');
    marker.textContent = visual.badge || '';
    marker.setAttribute('aria-hidden', 'true');
    button.appendChild(marker);
  }

  function makeMarkerIcon(point, selected) {
    if (!window.L) return null;
    return window.L.divIcon({
      className: '',
      html: markerHtml(point, selected),
      iconSize: [34, 34],
      iconAnchor: [17, 17],
      popupAnchor: [0, -18]
    });
  }

  function initMap() {
    if (!window.L) {
      el.map.className = 'fallback-map';
      setMapStatus('Карта недоступна, список точек открыт ниже.');
      return;
    }
    state.map = window.L.map(el.map, {
      zoomControl: true,
      scrollWheelZoom: true
    }).setView(MOSCOW, 10);
    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }).addTo(state.map);
  }

  function clearMarkers() {
    Object.keys(state.markers).forEach(function (uuid) {
      if (state.map) state.map.removeLayer(state.markers[uuid]);
    });
    state.markers = {};
    if (!state.map) el.map.innerHTML = '';
  }

  function renderMap(points, center) {
    clearMarkers();
    var rentalPoints = points.filter(function (point) {
      return point.is_rental && point.rental_uuid && point.latitude && point.longitude;
    });
    if (state.viewportBounds) {
      rentalPoints = rentalPoints.filter(function (point) {
        var lat = Number(point.latitude);
        var lng = Number(point.longitude);
        return lat >= state.viewportBounds.lat_south &&
          lat <= state.viewportBounds.lat_north &&
          lng >= state.viewportBounds.lng_west &&
          lng <= state.viewportBounds.lng_east;
      });
    }
    if (!state.map) {
      rentalPoints.forEach(function (point) {
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'fallback-marker';
        button.dataset.uuid = point.rental_uuid;
        button.setAttribute('aria-label', (point.title || 'Прокат') + ': ' + subjectLabel(point));
        appendFallbackSubject(button, point);
        button.appendChild(document.createTextNode(point.title || 'Прокат'));
        button.addEventListener('click', function () {
          selectOffer(point.rental_uuid, true);
        });
        el.map.appendChild(button);
      });
      return;
    }

    var bounds = [];
    rentalPoints.forEach(function (point) {
      var latLng = [Number(point.latitude), Number(point.longitude)];
      var marker = window.L.marker(latLng, {
        title: (point.title || 'Прокат') + ': ' + subjectLabel(point),
        icon: makeMarkerIcon(point, point.rental_uuid === state.selectedUuid)
      });
      marker.addTo(state.map);
      if (point.popup) marker.bindPopup(point.popup);
      marker.on('click', function () {
        selectOffer(point.rental_uuid, true);
      });
      state.markers[point.rental_uuid] = marker;
      bounds.push(latLng);
    });
    if (bounds.length) {
      state.map.fitBounds(bounds, { padding: [36, 36], maxZoom: 14 });
    } else if (center && center.length === 2) {
      state.map.setView(center, 10);
    }
  }

  function renderTags(offer, card) {
    var types = offer.equipment_types || [];
    if (!types.length) return;
    var row = document.createElement('div');
    row.className = 'tag-row';
    types.forEach(function (type) {
      var tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = equipmentLabel(type);
      row.appendChild(tag);
    });
    card.appendChild(row);
  }

  function appendMeta(grid, label, valueText) {
    var node = document.createElement('div');
    node.className = 'meta';
    var strong = document.createElement('strong');
    strong.textContent = label + ': ';
    node.appendChild(strong);
    node.appendChild(document.createTextNode(valueText || ''));
    grid.appendChild(node);
  }

  function renderListings(offers) {
    el.listingList.innerHTML = '';
    el.resultCount.textContent = String(offers.length);
    offers.forEach(function (offer) {
      var card = document.createElement('article');
      card.className = 'listing-card';
      card.dataset.uuid = offer.uuid;
      card.tabIndex = 0;

      renderMedia(offer, card);

      var title = document.createElement('h3');
      title.textContent = titleOf(offer);
      card.appendChild(title);

      if (offer.description_text) {
        var description = document.createElement('p');
        description.className = 'meta';
        description.textContent = offer.description_text;
        card.appendChild(description);
      }

      var meta = document.createElement('div');
      meta.className = 'meta-grid';
      appendMeta(meta, 'Цена', formatPrice(offer));
      appendMeta(meta, 'Доступность', formatAvailability(offer));
      appendMeta(meta, 'Адрес', offer.address || 'Не указан');
      appendMeta(meta, 'Владелец', (offer.owner && offer.owner.first_name) || 'Doverabot');
      card.appendChild(meta);
      renderTags(offer, card);

      var actions = document.createElement('div');
      actions.className = 'card-actions';
      var book = document.createElement('a');
      book.className = 'card-link';
      book.href = telegramUrl(offer);
      book.target = '_blank';
      book.rel = 'noopener';
      book.textContent = 'Забронировать';
      var contact = document.createElement('a');
      contact.className = 'card-link secondary';
      contact.href = telegramUrl(offer);
      contact.target = '_blank';
      contact.rel = 'noopener';
      contact.textContent = 'Написать';
      actions.appendChild(book);
      actions.appendChild(contact);
      card.appendChild(actions);

      card.addEventListener('click', function (event) {
        if (event.target.closest && event.target.closest('a')) return;
        selectOffer(offer.uuid, true);
      });
      card.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          selectOffer(offer.uuid, true);
        }
      });
      el.listingList.appendChild(card);
    });
  }

  function selectOffer(uuid, fromUser) {
    state.selectedUuid = uuid || '';
    updateUrlState();
    document.querySelectorAll('.listing-card').forEach(function (card) {
      var selected = card.dataset.uuid === state.selectedUuid;
      card.classList.toggle('is-selected', selected);
      if (selected && fromUser) card.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    });
    document.querySelectorAll('.fallback-marker').forEach(function (marker) {
      marker.classList.toggle('is-selected', marker.dataset.uuid === state.selectedUuid);
    });
    Object.keys(state.markers).forEach(function (markerUuid) {
      var point = state.points.find(function (item) {
        return item.rental_uuid === markerUuid;
      }) || {};
      state.markers[markerUuid].setIcon(makeMarkerIcon(point, markerUuid === state.selectedUuid));
    });
    var marker = state.markers[state.selectedUuid];
    if (marker && fromUser) {
      marker.openPopup();
      state.map.panTo(marker.getLatLng());
    }
    if (fromUser) setSheetExpanded(true);
  }

  function offerMatchesSelected(offers) {
    if (!state.selectedUuid) return true;
    return offers.some(function (offer) {
      return offer.uuid === state.selectedUuid;
    });
  }

  async function ensureSelectedOffer(offers) {
    if (!state.selectedUuid || offerMatchesSelected(offers)) return offers;
    var params = viewerParams();
    params.uuid = state.selectedUuid;
    var response = await apiGet('/api/rental/offer/', params);
    if (!response.ok || !response.data || !response.data.offer) return offers;
    return [response.data.offer].concat(offers);
  }

  function currentMapBounds() {
    if (!state.map) return null;
    var bounds = state.map.getBounds();
    return {
      lat_south: Number(bounds.getSouth().toFixed(6)),
      lat_north: Number(bounds.getNorth().toFixed(6)),
      lng_west: Number(bounds.getWest().toFixed(6)),
      lng_east: Number(bounds.getEast().toFixed(6))
    };
  }

  function setSheetExpanded(expanded) {
    state.sheetExpanded = Boolean(expanded);
    el.listPane.classList.toggle('is-expanded', state.sheetExpanded);
    el.listPane.classList.toggle('is-collapsed', !state.sheetExpanded);
    el.sheetToggle.setAttribute('aria-expanded', state.sheetExpanded ? 'true' : 'false');
    el.sheetToggle.textContent = state.sheetExpanded ? 'Свернуть' : 'Список';
  }

  function responseMessage(response, fallback) {
    if (!response) return fallback;
    if (response.data && response.data.message) return response.data.message;
    if (response.status) return fallback + ' (' + response.status + ')';
    return fallback;
  }

  async function loadRentals() {
    setLoading(true);
    setMessage('Загрузка объявлений...', false);
    setMapStatus('');
    renderLoading();
    updateUrlState();
    try {
      var results = await Promise.all([
        apiGet('/api/rental/search/', searchParams()),
        apiGet('/api/user/points/', pointParams())
      ]);
      var search = results[0];
      var points = results[1];
      if (!search.ok) throw new Error(responseMessage(search, 'Не удалось загрузить объявления'));
      if (!points.ok) throw new Error(responseMessage(points, 'Не удалось загрузить точки на карте'));

      state.offers = await ensureSelectedOffer((search.data && search.data.offers) || []);
      state.points = (points.data && points.data.points) || [];
      renderListings(state.offers);
      renderMap(state.points, [
        Number(points.data && points.data.lat_avg) || MOSCOW[0],
        Number(points.data && points.data.lng_avg) || MOSCOW[1]
      ]);
      if (state.offers.length) {
        setMessage('', false);
        if (!state.selectedUuid) state.selectedUuid = state.offers[0].uuid;
        selectOffer(state.selectedUuid, false);
        if (state.viewportBounds) setMapStatus('Показана выбранная область карты.');
      } else if (state.auth && state.auth.user_uuid) {
        setMessage('По этим фильтрам объявлений нет.', false);
        setMapStatus('Нет точек в выбранной области.');
      } else {
        setMessage('Авторизуйтесь через Telegram, чтобы увидеть доступные объявления.', false);
      }
      if (search.data && search.data.clarification) {
        setMessage('Уточните тип снаряжения в фильтре.', false);
      }
    } catch (error) {
      setMessage(error && error.message ? error.message : 'Не удалось загрузить прокат.', true);
      setMapStatus('Ошибка загрузки карты проката.');
      renderListings([]);
      renderMap([], MOSCOW);
    } finally {
      setLoading(false);
    }
  }

  async function loadBotData() {
    var response = await apiGet('/api/get_bot_data/', {});
    if (response.ok && response.data && response.data.username) {
      state.botUsername = response.data.username;
      el.botLink.href = 'https://t.me/' + encodeURIComponent(state.botUsername);
    }
  }

  function bindEvents() {
    el.filterForm.addEventListener('submit', function (event) {
      event.preventDefault();
      state.selectedUuid = '';
      state.viewportBounds = null;
      loadRentals();
    });
    $('viewportButton').addEventListener('click', function () {
      var bounds = currentMapBounds();
      if (!bounds) {
        setMapStatus('Карта еще не готова.');
        return;
      }
      state.viewportBounds = bounds;
      state.selectedUuid = '';
      loadRentals();
    });
    $('resetButton').addEventListener('click', function () {
      el.filterForm.reset();
      state.selectedUuid = '';
      state.viewportBounds = null;
      loadRentals();
    });
    el.sheetToggle.addEventListener('click', function () {
      setSheetExpanded(!state.sheetExpanded);
    });
  }

  async function init() {
    el.filterForm = $('filterForm');
    el.map = $('map');
    el.mapStatus = $('mapStatus');
    el.listingList = $('listingList');
    el.listPane = $('listPane');
    el.resultCount = $('resultCount');
    el.stateMessage = $('stateMessage');
    el.botLink = $('botLink');
    el.sheetToggle = $('sheetToggle');

    initFiltersFromUrl();
    initMap();
    bindEvents();
    state.auth = await window.check_auth(false);
    await loadBotData();
    await loadRentals();
  }

  window.addEventListener('DOMContentLoaded', init);
})();
