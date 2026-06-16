const NODE_TYPES = Object.freeze({
	"USER":"user",
	"FRIEND":"friend",
	"WISH_ROOT": "wish_root",
	"WISH":"wish",
	"SHARE": "share_root",
	"TRUST": "trust_btn",
	"MISTRUST" : "mistrust_btn",
	"PROFILE": "profile_root",
	"OPTIONS": "options",
	"HOME": "home",
	"GENESIS": "genesis",
	"FILTER": "filter",
	"FILTERED": "filtered",
	"INVITE": "invite",
	"MAPS": "maps"
	//"PLUS": "plus"
});

const WISHES_ROOT_ID = "WISHES_ROOT";
const ABILITIES_ROOT_ID = "ABILITIES_ROOT";
const SHARE_ID = "SHARE_ROOT";
const OPTIONS_ID = "OPTIONS_ROOT";
const TRUST_ID = "TRUST_ROOT";
const MISTRUST_ID = "MISTRUST_ROOT";
const FILTER_ID = "FILTER_ROOT";
const HOME_ID = "HOME_ROOT";
const GENESIS_ID = "GENESIS_ROOT";
const MAPS_ID = "MAPS_ROOT";
const INVITE_ID = "INVITE_ROOT";
//const PLUS_ID = "PLUS_ROOT";

const PROFILE = {
	id: '',
	nodeType: NODE_TYPES.PROFILE,
	image: '',
        base64Url: '',
	text: '',
	tabil: ' ',
	count: ''
};

var svg = d3.select('#main').attr('viewBox', `0 0 ${window.innerWidth} ${window.innerHeight}`);
svg.attr('preserveAspectRatio', 'xMidYMid meet').attr('pointer-events', 'all');
svg.attr('baseProfile', 'full');

var width = +svg.node().getBoundingClientRect().width;
var height = +svg.node().getBoundingClientRect().height;

var link, node;

var nodes = [];
var links = [];

var simulation;

// all dialog elements
var rootDialog = document.getElementById("rootDialog");

//root stuff
var rootList = document.getElementById("rootList");

//filter stuff
var filterInput = document.getElementById("filterInput");

var settings = { api: get_api_url(), url: new URL(window.location.href) };

window.onerror = (msg, file, line, col, error) => {
    const log = (stackframes) => console.error(stackframes.map(String).join('\n'));
    const errback = ({message}) => console.error(message);

    // callback is called with an Array[StackFrame]
    StackTrace.fromError(error).then(log).catch(errback);
};

setTimeout(() => {
	if(false){
    }
}, 2000)

function uuidv4() {
	return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
	  var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
	  return v.toString(16);
	});
}

initDefs();

// load the data

var url = new URL(window.location.href);

var rod = url.searchParams.get("rod") || '';
var dover = url.searchParams.get("dover") || '';
var withalone = url.searchParams.get("withalone") || '';

var userIdFrom = url.searchParams.get("id") || url.searchParams.get("user_genesis_tree");
var chat_id = url.searchParams.get("chat_id") || '';

var depth = url.searchParams.get("depth") || 10;
var up = url.searchParams.get("up") || '';
var down = url.searchParams.get("down") || '';

var count_ = url.searchParams.get("q") || '';
if (chat_id && !count_) count_ = 50;
if (!chat_id && !userIdFrom) {
    if (!rod && !dover) {
        rod = 'on'; dover = 'on';
        withalone = url.searchParams.get("withalone") || 'on';
    }
}
var from_ = url.searchParams.get("f") || 0;

if (chat_id) {
    document.querySelector('.pagination_block').style.display = 'block';
}

if (userIdFrom) {
    if (depth <= 0 || depth > 100 ) {
        depth = 100;
    }
} else if (chat_id) {
    if (depth <= 0 || depth > 10 ) {
        depth = 10;
    }
    if (count_ <= 0 || count_ > 50 ) {
        count_ = 50;
    }
}

var link = window.location.href;

        if (chat_id) {
            if(!url.searchParams.has('q') && !url.searchParams.has('f')){
                url.searchParams.append('q', 50);
                url.searchParams.append('f', 0);
                url.searchParams.append('depth', 10);
                window.history.pushState(null, null, url.search);
                window.location.href = url.href;
            }
            else{
                let selected_val = +url.searchParams.get('q');
                let head_from = +url.searchParams.get('f');
                if(head_from/selected_val == 0 || head_from/selected_val == Infinity){
                    document.querySelector('#page').innerHTML = 1;
                    let btn_prev_n = document.querySelector('#btn_prev');
                    btn_prev_n.style.background = '#aaa0a0';
                    btn_prev_n.style.cursor = 'context-menu';
                    btn_prev_n.style.pointerEvents = 'none';
                }else{
                document.querySelector('#page').innerHTML = 1 + (head_from / selected_val);
                }
            }
        }

        function nextPage() {
			let item_plus_int = +url.searchParams.get('f');
			let selected_val = +url.searchParams.get('q');
			item_plus_int += selected_val;
			url.searchParams.set('f', item_plus_int);
			url.searchParams.set('depth', depth);
            if (chat_id) {
                url.searchParams.set('q', count_);
            }
			window.location.href = url.href;
        }

        function prevPage() {
			let item_plus_int = +url.searchParams.get('f');
			let selected_val = +url.searchParams.get('q');
			item_plus_int -= selected_val;
			url.searchParams.set('f', item_plus_int);
			url.searchParams.set('depth', depth);
            if (chat_id) {
                url.searchParams.set('q', count_);
            }
			window.location.href = url.href;
        }

		document.querySelector('#btn_prev').style.background = '#6a2300;';
		document.querySelector('#btn_prev').style.cursor = 'pointer;';
		document.querySelector('.pagination_count').innerHTML = (chat_id ? count_ : url.searchParams.get('q'));
			var apiUrl;

            if (chat_id) {
                apiUrl = `${settings.api}/api/profile_genesis/?chat_id=` + chat_id + '&depth=' + depth + '&from=' + url.searchParams.get('f') + '&count=' + count_;
            } else if (userIdFrom) {
                apiUrl = `${settings.api}/api/profile_genesis/?id=` + userIdFrom + '&depth=' + depth + '&up=' + up + '&down=' + down;
            } else {
                apiUrl = `${settings.api}/api/profile_genesis/all/?rod=` + 
                    rod + '&dover=' + dover + '&withalone=' + withalone + 
                    (count_ ? '&from=' + from_ + '&number=' + count_ : '') ;
            }

document.addEventListener("popstate",function(e){
    alert('yeees!');
},false);

var isTrust;

let map_latitude;
let map_longitude;
let new_map = document.querySelector('#new_map');

// --- let it authorize  (ES) --
//
function getCookieObject(name) {

    // Полагаю, что в куке всегда объект, его и возвращаю, если
    // в строке куки имеется преобразуемый из json объект, или
    // undefined, если кука не найдена или не преобразуется в объект

    let result = undefined;
    let matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));

    if (matches) {
        let value = decodeURIComponent(matches[1]);
        if (value.match(new RegExp(`^[\"\'\`].+[\"\'\`]$`))) {
            // строка в кавычках типа:
            // "{\"provider\": \"telegram\"\054 \"user_uuid\": \"...\"\054 \"auth_token\": \"...\"}"
            value = eval (value);
        }
        try {
            result = JSON.parse(value);
        } catch (error) {
            console.log(error);
        }
    }

    return result;
}

var auth_data_ = getCookieObject('auth_data');
var auth_token_ = auth_data_ ? auth_data_.auth_token : '';
var d3_json_params = {};

if (auth_token_) {
    d3_json_params = {
        headers: new Headers({
            'Authorization': `Token ${auth_token_}`
        })
    };
}
//
// --- let it authorize --

function nodeType({uuid, username, is_in_page}) {
    let nodeType = NODE_TYPES.FRIEND;

    if (chat_id && !is_in_page) {
        nodeType = NODE_TYPES.FILTERED;
    } else if (chat_id && is_in_page) {
        nodeType = NODE_TYPES.USER;
    // Здесь надо бы изменить USER -> FRIEND,
    // т.к при увеличенной картинке "центрального" юзера
    // стрелки перекрывались картинкой
    // но из-за этого не идет экспорт в svg!
    } else if (uuid == userIdFrom) {
        nodeType = NODE_TYPES.USER;
    } else if (username == userIdFrom) {
        nodeType = NODE_TYPES.USER;
    }

    return nodeType;
}

function nodeTextDecoration(uuid, username) {
    // text-decoration для текста под узлом
    let result = 'none';
    let underline = 'underline';

    if (!chat_id) {
        if (uuid == userIdFrom) {
            result = underline;
        } else if (username == userIdFrom) {
            result = underline;
        }
    }
    return result;
}


function no_photo({gender, is_dead}) {
    const leftPattern = 'no-photo-gender';

    let sex = 'none';

    switch (gender) {
        case 'm':
            sex = 'male';
            break;
        case 'f':
            sex = 'female';
            break;
    }

    let result = `${leftPattern}-${sex}${is_dead ? '-dead' : ''}.jpg`;
    result = `${settings.api}/media/images/${result}`;

    return result;
}

const image = d => d.photo || no_photo(d);

function cacheBase64Url(afunc) {
    const cache = new Map();

    async function awrapper(url, callback) {
        if (cache.has(url)) {
            const cached = cache.get(url);

            return callback ? callback(cached) : cached;
        }

        const base64Url = await afunc(url, callback);

        cache.set(url, base64Url);

        return base64Url;
    }

    return awrapper;
}

const noPhotoBase64Url = cacheBase64Url(urlAsBase64);

d3.json(apiUrl, d3_json_params)
    .then(async data => {
	//добавить пользователей в вершины
        const filterUser = ({uuid}) => !nodes.some(({id}) => id === uuid);
        const updateUrl = node => dataUrl => (node.base64Url = dataUrl);
	data.users.filter(filterUser).forEach(d => {
            const node = {
                id: d.uuid,
                username: d.username,
                nodeType: nodeType(d),
                image: image(d),
                base64Url: '',
                text: `${d.first_name} `,
                is_dead: d.is_dead
            };

            const base64UrlSetter = d.photo ? urlAsBase64 : noPhotoBase64Url;

            base64UrlSetter(node.image, updateUrl(node));

            nodes.push(node);
	});

	if (!window.location.href.includes('gen')) {
            let selected_val_num = +url.searchParams.get('q');
            let but_next = document.querySelector('#btn_next');

            // Если chat_id, то число юзеров на странице может быть больше,
            // чем заказано участников группы в выпадающем списке.
            // Сколько всего, есть в ответе от апи: data.participants_on_page

            data_users_length = chat_id ? data.participants_on_page : data.users.length;

            if (data_users_length == selected_val_num) {
                but_next.style.background = '#8b0000';
                but_next.style.cursor = 'pointer';
                but_next.style.pointerEvents = 'all';
            }
            else if (data_users_length < selected_val_num){
                but_next.style.background = '#aaa0a0';
                but_next.style.cursor = 'context-menu';
                but_next.style.pointerEvents = 'none';
            }
	}

	data.connections.forEach(d => {
            d.is_trust = true;
            let reverse_is_trust = d.is_trust;

            data.connections.forEach(dd => {
                if (d.source == dd.target && d.target == dd.source && dd.is_trust != null){
                    reverse_is_trust = dd.is_trust;
                }
            });

            links.push({
                source: d.source,
                target: d.target,
                is_trust: d.is_trust,
                reverse_is_trust: reverse_is_trust
            });
	});

	//зафиксировать вершины пользователя, желаний и ключей

	nodes.forEach(function(d) {
        if (d.username == userIdFrom) {
//			d.fx = width / 2;
//			d.fy = height / 2;
        } else {
            switch(d.id){
            case userIdFrom:
//                d.fx = width / 2;
//                d.fy = height / 2;
                break;
            case WISHES_ROOT_ID:
                d.fx = width<900 ? width / 2+150 : width / 2 + 400;
                d.fy = width<900 ? height/2+50 : height / 2 + 200;
                break;
            case ABILITIES_ROOT_ID:
                d.fx = width<900 ? width / 2+150 : width / 2 + 400;
                d.fy = width<900 ? height/2-10 : height / 2;
                break;
            case SHARE_ID:
                d.fx = width<900 ? width/2+80 : width / 2 + 300;
                d.fy = height / 2 - 300;
                break;
            case FILTER_ID:
                d.fx = width<900 ? width/2+170 : width / 2 + 400;
                d.fy = height / 2 - 300;
                break;
            case OPTIONS_ID:
                d.fx = width<900 ? 10 : width / 2 - 400;
                d.fy = height / 2 - 300;
                break;
            case INVITE_ID:w
                            d.fx = width<900 ? width/2-20 : width / 2 - 200;
                            d.fy = height / 2 - 300;
                            break;
            case HOME_ID:
                d.fx = width<900 ? width/2-81 :width / 2 - 300;
                d.fy = height / 2 - 300;
                break;
            /*
                    case GENESIS_ID:
                if (document.location.includes('gen')) return;
                d.fx = width<900 ? 20 :width / 2+100;
                d.fy = height / 2 - 250;
                break;
                    */
            case MAPS_ID:
                d.fx = width<900 ? width/2+30 : width / 2 - 50;
                d.fy = height / 2 - 300;
                break;
            /*
                    case PLUS_ID:
                d.fx = width<900 ? width/2+50 : width/2+80;
                d.fy = height/2;
                break;
                    */
            case TRUST_ID:
                d.fx = width<900 ? width / 2 + 30 :  width / 2 + 50;
                d.fy = width<900 ? height/2+65 : height / 2 + 120;
                break;
            case MISTRUST_ID:
                d.fx = width<900 ? width / 2 - 30 :  width / 2 - 50;
                d.fy = width<900 ? height/2+65 : height / 2 + 120;
                break;
            case PROFILE.id:
                if (userIdFrom && userIdFrom != PROFILE.id) {
                                d.fx = width < 900 ? width / 2 - 100 : width / 2 - 200;
                                d.fy = height / 2;
                }
                            else {
                                d.fx = width / 2;
                                d.fy = height / 2;
                }
                break;
            }
        }
	});

    simulation = d3.forceSimulation(nodes);
    simulation.force('link', d3.forceLink(links).id(({id}) => id).strength(0.1)); // .distance()
    simulation.force('charge', d3.forceManyBody().strength(-7000));
    simulation.force("collide", d3.forceCollide().radius(200));//.strength(1).radius(300))//.iterations(1))
    simulation.force('x', d3.forceX(width / 2).strength(0.006));
    simulation.force('y', d3.forceY(height / 2).strength(0.012));
//    simulation.alpha(1).alphaTarget(1).alphaMin(0.001).alphaDecay(.001).velocityDecay(0.01).restart();
    simulation.alpha(1).alphaTarget(1).alphaMin(0.001).alphaDecay(0.01).velocityDecay(0.01).restart();

	initializeDisplay();
	initializeSimulation();
});

var layoutWorker = new Worker('staticlayout.worker.js');

const css = (el, styles) => Object.assign(el.style, styles);

function wavy(text, {letterWrap, tag='h1', delay=500}={}) {
    letterWrap ||= letter => `<span>${letter}</span>`;

    const keyframes = {
        top: [0, '-1.5em']
    };

    const animationOptions = {
        duration: 600,
        direction: 'alternate',
        easing: 'ease-in-out',
        iterations: Infinity
    };

    const animatedText = document.createElement(tag);

    animatedText.innerHTML = text.split('').map(letterWrap).join('');

    Array.from(animatedText.children).forEach((wavyLetter, i) => {
        css(wavyLetter, { position: 'relative', left: 0 });

        wavyLetter.animate(keyframes, { ...animationOptions, delay: i * 60 + delay });
    });

    return animatedText;
}

function* loadingScreen(caption) {
    const wavyText = wavy(caption);

    const screen = document.createElement('div');
    screen.setAttribute('class', `container-fluid d-flex 
        justify-content-center align-items-center h-100
    `);
    css(screen, { position: 'absolute', background: 'white' });
    screen.append(wavyText);

    yield document.body.append(screen);

    return screen.remove();
}

const loading = loadingScreen('Загрузка');

function simStarted() {
    loading.next();
    simulation.nodes(nodes);
    simulation.on('tick', ticked);
    simulation.alpha(1).velocityDecay(0.05).restart();
}

const simEnded = ({ nTicks }) => setTimeout(() => loading.next(), nTicks * 10);

const MESSAGE_HANDLES = Object.freeze({
    'start': simStarted,
    'end': simEnded
});

function simTickCount(simulation) {
    const alphaMinLog = Math.log(simulation.alphaMin());
    const alphaDecayLog = Math.log(1 - simulation.alphaDecay());

    return Math.ceil(alphaMinLog / alphaDecayLog);
};

function initializeSimulation() {
  layoutWorker.postMessage({
    nTicks: simTickCount(simulation)
  });

  layoutWorker.onmessage = ({ data }) => (MESSAGE_HANDLES[data.type] || (() => {}))(data);
}

const ZOOM_MIN = 0.01;
const ZOOM_MAX = 1.5;

var zoom = d3.zoom().scaleExtent([ZOOM_MIN, ZOOM_MAX]);
zoom.on('zoom', ({transform: {x, y, k}}) => svg.attr('transform', `translate(${x}, ${y}) scale(${k})`));

function drag(simulation) {
	function dragstarted(e, d) {
//		!e.active && simulation.alphaTarget(0.01).velocityDecay(0.01).restart();
	}
	
	const dragged = ({x, y}, d) => { d.fx = x; d.fy = y; };
	
	const dragended = (e, d) => { 
//		if (!e.active) simulation.stop();
//		d.fx = e.x;
//		d.fy = e.y;		
		d.fx = null;
		d.fy = null;		
	};

	let behavior = d3.drag();
	behavior.on('start', dragstarted);
	behavior.on('drag', dragged);
	behavior.on('end', dragended);

	return behavior;
}

const EXPORT_ID = 'export';

const EXPORT_FORMATS = Object.freeze({
    SVG: 'svg'
});

const selectSvg = (id) => d3.select(`#${id}`);

const asBase64 = (string, {unescape=true}={}) => {
    let encoded = encodeURIComponent(string);

    unescape && (encoded = window.unescape(encoded));

    return btoa(encoded);
};

const fromBase64 = (base64, {escape=true}={}) => {
    let string = atob(base64);

    escape && (string = window.escape(string));

    return decodeURIComponent(string);
};

async function blobAsBase64(blob, callback) {
    const arrayBuffer = await blob.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);

    const base64 = btoa(String.fromCharCode(...uint8Array));
    const base64DataUrl = `data:${blob.type};base64,${base64}`;

    return callback ? callback(base64DataUrl) : base64DataUrl;
}

async function urlAsBase64(url, callback) {
    const response = await fetch(url);
    const blob = await response.blob();

    return await blobAsBase64(blob, callback);
}

function encodeSvg(svgXML, toHex) {
    const hexer = char => `%${char.charCodeAt(0).toString(16)}`;

    Array.isArray(toHex) && (toHex = toHex.join(''));

    svgXML = svgXML.replaceAll(new RegExp(`[${toHex}]`, 'g'), hexer);
    svgXML = svgXML.replaceAll(/\s+/g, ' ');

    //  The maybe list (add on documented fail)
    //  svgXML = svgXML.replaceAll('&', '%26');
    //  svgXML = svgXML.replaceAll('|', '%7C');
    //  svgXML = svgXML.replaceAll('[', '%5B');
    //  svgXML = svgXML.replaceAll(']', '%5D');
    //  svgXML = svgXML.replaceAll('^', '%5E');
    //  svgXML = svgXML.replaceAll('`', '%60');
    //  svgXML = svgXML.replaceAll(';', '%3B');
    //  svgXML = svgXML.replaceAll('?', '%3F');
    //  svgXML = svgXML.replaceAll(':', '%3A');
    //  svgXML = svgXML.replaceAll('@', '%40');
    //  svgXML = svgXML.replaceAll('=', '%3D');

    return svgXML;
}

function serializeSvg(repr, {encode=true, toBase64=false}={}) {
    const VERSION = 1.1;
    const XMLNS = 'http://www.w3.org/2000/xmlns/';
    const SVGNS = 'http://www.w3.org/2000/svg';
    const XLINKNS = 'http://www.w3.org/1999/xlink';
    const EVNS = 'http://www.w3.org/2001/xml-events';

    const FRAGMENT = `${window.location.href}#`;

    const TO_HEX = [/* '<', '>', '"', */ '%', '{', '}'];

    const replaceFragments = true;

    function replacingFragments(walker, fragment) {
        while (walker.nextNode())
            for (const attr of walker.currentNode.attributes) {
                if (!attr.value.includes(fragment)) continue;

                attr.value = attr.value.replace(fragment, '#');
            }
    }

    const isSvgId = typeof repr === 'string';
    const isXmlDoc = repr instanceof XMLDocument;

    const node = isSvgId ? selectSvg(repr).node() : isXmlDoc ? repr.rootElement : repr.node();

    const walker = document.createTreeWalker(node, NodeFilter.SHOW_ELEMENT);

    replaceFragments && replacingFragments(walker, FRAGMENT);

    node.setAttribute('version', VERSION);
    node.setAttributeNS(XMLNS, 'xmlns', SVGNS);
    node.setAttributeNS(XMLNS, 'xmlns:xlink', XLINKNS);
    node.setAttributeNS(XMLNS, 'xmlns:ev', EVNS);

    let serialized = new XMLSerializer().serializeToString(node);

    serialized = serialized.replace(' display="none" ', ' ').replaceAll(' href', ' xlink:href');

    encode && (serialized = encodeSvg(serialized, toBase64 ? TO_HEX : [...TO_HEX, '#']));

    toBase64 && (serialized = asBase64(serialized));

    return serialized;
}

const deserializeSvg = svgXML => new DOMParser().parseFromString(svgXML, 'image/svg+xml');

SVGRect.prototype.toString = function() {
    return `${this.x} ${this.y} ${this.width} ${this.height}`;
};

function prepareSvg(id) {
    // hide context menu
    d3.select('body').node().click();

    const full = svg.node().getBBox();

    const prepared = selectSvg(id).clone([true])
        .attr('id', EXPORT_ID).attr('display', 'none');

    prepared.attr('viewBox', String(full));
    prepared.select('g').attr('transform', '');

    // stackoverflow.com/a/28692538
    prepared.attr('width', full.width);
    prepared.attr('height', full.height);

    const svg_elem = prepared.selectAll('.svg_elem').data(nodes);

    svg_elem.select('image').attr('href', ({base64Url}) => base64Url);

/*    const userXY = width < 900 ? '-32px' : '-64px';
    const userWH = width < 900 ? '64px' : '128px';
    const friendXY = width < 900 ? '-18px' : '-32px';
    const friendWH = width < 900 ? '35px' : '64px';
*/
    const userXY = '-32px';
    const userWH = '64px';
    const friendXY = '-32px';
    const friendWH = '64px';
	
	svg_elem.select('.userPortrait')
        .attr('x', userXY).attr('y', userXY)
        .attr('width', userWH).attr('height', userWH);

    svg_elem.selectAll('.friendPortrait')
        .attr('x', friendXY).attr('y', friendXY)
        .attr('width', friendWH).attr('height', friendWH);

    svg_elem.selectAll('text').attr('text-anchor', 'middle');

    return prepared;
}

function context2d(w, h, options={}) {
    const {
        dpi = devicePixelRatio,
        scale = true
    } = options;

    let canvas = document.createElement('canvas');

    Object.defineProperty(canvas, 'blank', {
        writable: true,
        enumerable: false
    });

    canvas.isEmpty = () => canvas.toDataURL() === canvas.blank;

    canvas.width = w * dpi;
    canvas.height = h * dpi;
    canvas.style.width = `${canvas.width}px`;

    const context = canvas.getContext('2d');
    scale && context.scale(dpi, dpi);

    return context;
}

function validateSVG(svgXML) {
    const xmlDoc = new DOMParser().parseFromString(svgXML, 'image/svg+xml');

    let errors = xmlDoc.querySelectorAll('parsererror div');

    const dispatch = (resolve, reject) => {
        if (errors.length === 0)
            return resolve();

        errors = Array.from(errors);
        errors = errors.map(({innerText}) => innerText);

        return reject(errors);
    };

    return new Promise(dispatch);
}

const validateBase64SVG = base64SVG => validateSVG(fromBase64(base64SVG));

const DATA_URL_PREFIX = /^data:[a-z]+\/[a-z\d\+\-\.]+,?/;
const dataFromDataURL = (dataURL) => dataURL.replace(DATA_URL_PREFIX, '')

const BASE64_DATA_URL_PREFIX = new RegExp(`${DATA_URL_PREFIX.source};base64,`);

const base64FromDataURL = (dataURL) => dataURL.replace(BASE64_DATA_URL_PREFIX, '');
const validateBase64 = (base64) => validator.isBase64(base64);

const isStr = param => typeof param === 'string';
const isObj = param => typeof param === 'object';
const isFunc = param => typeof param === 'function';

class StyledConsole {
    #content;
    #styles;
    #styler;

    constructor(content, styles, styler) {
        this.#content = content;
        this.#styles = isStr(styles) ? [styles] : styles;
        this.#styler = styler;
    }

    static SCHEMA = Object.freeze({
        styles: styles => Array.isArray(styles) && styles.every(isStr),
        styler: styler => !styler || isFunc(styler)
    });

    static isStyledConsole(object) {
        const schemaFields = Object.keys(StyledConsole.SCHEMA);

        return schemaFields.some(prop => prop in object);
    };

    static validate(object) {
        const invalidField = field => new Error(`${field} is invalid.`);

        const schema = StyledConsole.SCHEMA;
        const isValid = field => schema[field](object[field]);

        const schemaFields = Object.keys(schema);
        const invalid = schemaFields.filter(field => !isValid(field));

        const dispatch = (resolve, reject) => {
            if (invalid.length === 0)
                return resolve();

            const errors = invalid.map(invalidField);

            return reject(errors);
        };

        return new Promise(dispatch);
    }

    static withDirective = arg => arg.startsWith('%c') ? arg : `%c${arg}`;

    styled() {
        let [first, ...rest] = this.#content;

        if (this.#styles) {
            first = StyledConsole.withDirective(first);
            first = [first, ...this.#styles];
        } else {
            first = styler(first);
        }

        return console.log(...first, ...rest);
    }

    static #make = (...args) => new StyledConsole(...args);

    static #withStyle(...content) {
        const { styles, styler } = content.pop();

        return StyledConsole.#make(content, styles, styler);
    }

    static SUCCESS_STYLE = 'color: green;';
    static WARNING_STYLE = 'color: orange;';
    static ERROR_STYLE = 'color: red;';

    static success = (...content) => StyledConsole.#make(content, StyledConsole.SUCCESS_STYLE).styler();
    static warning = (...content) => StyledConsole.#make(content, StyledConsole.WARNING_STYLE).styled();
    static error = (...content) => StyledConsole.#make(content, StyledConsole.ERROR_STYLE).styled();

    static successStyled(...content) {
        const lastArg = content.pop();

        lastArg.styles = [StyledConsole.SUCCESS_STYLE, ...lastArg.styles];

        return StyledConsole.#withStyle(...content, lastArg).styled();
    }

    static warningStyled(...content) {
        const lastArg = content.pop();

        lastArg.styles = [StyledConsole.WARNING_STYLE, ...lastArg.styles];

        return StyledConsole.#withStyle(...content, lastArg).styled();
    }

    static errorStyled(...content) {
        const lastArg = content.pop();

        lastArg.styles = [StyledConsole.ERROR_STYLE, ...lastArg.styles];

        return StyledConsole.#withStyle(...content, lastArg).styled();
    }
};

const svgValid = ({isBase64=false}={}) => {
    const msg = `The${isBase64 ? ' Base64 ' : ' '}SVG is valid`;

    return StyledConsole.success(msg);
};

const svgInvalid = (errors, {isBase64=false}={}) => {
    StyledConsole.error(`The${isBase64 ? ' Base64 ' : ' '}SVG is invalid`);

    errors.forEach(error => StyledConsole.error(error));
};

function message(text, {id='', cssClass='', delay=2000, duration=5000}={}) {
    const msg = d3.select('body').append('div').attr('id', id)
        .attr('class', 'container-fluid d-flex justify-content-center')
        .style('position', 'absolute');

    msg.append('div').attr('class', cssClass).text(text);

    msg.transition().style('opacity', 0).delay(delay).duration(duration)
        .remove();
}

const success = (text, id='export-success') => message(text, {id: id, cssClass: 'alert alert-success mt-5'});
const warning = (text, id='export-empty') => message(text, {id: id, cssClass: 'alert alert-warning mt-5'});
const error = (text, id='export-invalid') => message(text, {id: id, cssClass: 'alert alert-danger mt-5'});

function makeSvgBlob(callback, options={}) {
    const XMLHEADER = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>';

    const {
        toBase64,
        monitor
    } = options;

    const prepared = prepareSvg('main');
    const serialized = serializeSvg(prepared, { encode: false });
    const content = `${XMLHEADER}${serialized}`;

    const svgBlob = new Blob([content], { type: 'image/svg+xml' });

    monitor && monitor(svgBlob);

    callback && callback(svgBlob);

    return svgBlob;
}

function suggestFilename(extension) {
    const project = 'blagoroda';

    let userName = d3.select('.userName').text();
    userName = userName.trimRight().replaceAll(' ', '_');

    const url = new URL(document.location);
    const userId = `id${url.searchParams.get('id')}`;

    return `${project}-${userName}-${userId}.${extension}`;
}

function download(object, format, callback, suggestedName=suggestFilename) {
    const extension = format.toLowerCase();

    const link = document.createElement('a');
    link.href = object instanceof Blob ? URL.createObjectURL(object) : object;
    link.download = isFunc(suggestedName) ? suggestedName(extension) : suggestedName;
    link.target = '_blank';

    // some browser needs the anchor to be in the doc
    document.body.append(link);

    link.click();

    // in case the Blob uses a lot of memory
    setTimeout(() => { URL.revokeObjectURL(object); link.remove(); }, 7000);

    return callback && callback(object);
}

function makeSvg(cb) {
    const blobIsNull = () => StyledConsole.error('The SVG image is empty');

    const monitor = blob => {
        if (!blob) return blobIsNull();
    };

    const options = {
        monitor: monitor
    };

    return makeSvgBlob(cb, options);
}

const EXPORTS = {
    [EXPORT_FORMATS.SVG]: makeSvg
};

function makeBlob(format, callback) {
    if (!EXPORTS.hasOwnProperty(format))
        throw new Error('Unknown format');

    return EXPORTS[format](callback);
}

function exporting(to) {
    const logger = (func) => (...args) => console.log(func(...args));

    const formatUpperCase = to.toUpperCase();

    let exportStarted = () => `${formatUpperCase} export started`;
    let downloading = () => `${formatUpperCase} download`;
    let exportComplete = () => `${formatUpperCase} export complete`;

    exportStarted = logger(exportStarted);
    downloading = logger(downloading);
    exportComplete = logger(exportComplete);

    const afterDownload = () => {
        selectSvg(EXPORT_ID).remove();
        exportComplete();

        return success('Проверьте папку загрузок');
    }

    const callDownload = blob => {
        const resolved = blob => download(blob, to, afterDownload);

        const blobIsEmpty = () => {
            StyledConsole.error('The Blob is empty');

            error('Ошибка загрузки');
        };

        const dispatch = (resolve, reject) => blob ? resolve(blob) : reject();

        downloading();

        return new Promise(dispatch).then(resolved).catch(blobIsEmpty);
    };

    exportStarted();

    return makeBlob(to, callDownload);
}

const export2svg = () => exporting(EXPORT_FORMATS.SVG);
const stopsim = () => {simulation.stop()};
// unlim const startsim1 = () => {simulation.alpha(1).alphaTarget(1).alphaMin(0.001).alphaDecay(.001).velocityDecay(0.01).restart()};
// slow decay const startsim1 = () => {simulation.alpha(1).alphaTarget(0).alphaMin(0.001).alphaDecay(.001).velocityDecay(0.01).restart()};
// fast decay const startsim5 = () => {simulation.alpha(1).alphaTarget(0).alphaMin(0.001).alphaDecay(.061).velocityDecay(0.01).restart()};
const startsim = () => {simulation.alpha(1).alphaTarget(1).alphaMin(0.001).alphaDecay(.001).velocityDecay(0.01).restart()};
const slowsim = () => {simulation.alpha(1).alphaTarget(0).alphaMin(0.001).alphaDecay(.001).velocityDecay(0.05).restart()};
const alf1 = () => {simulation.alpha(1).alphaTarget(0).alphaMin(0.001).alphaDecay(.001).velocityDecay(0.5).restart()};
const alf2 = () => {simulation.alpha(1).alphaTarget(0).alphaMin(0.001).alphaDecay(.001).velocityDecay(0.7).restart()};
const alf3 = () => {simulation.alpha(1).alphaTarget(0).alphaMin(0.001).alphaDecay(.001).velocityDecay(1).restart()};
const fMb1 = () => {simulation.force('charge', d3.forceManyBody().strength(-4000))};
const fMb2 = () => {simulation.force('charge', d3.forceManyBody().strength(-3000))};
const fMb3 = () => {simulation.force('charge', d3.forceManyBody().strength(-2500))};
const fclde1 = () => {simulation.force("collide", d3.forceCollide().radius(160))};
const fclde2 = () => {simulation.force("collide", d3.forceCollide().radius(140))};
const fclde3 = () => {simulation.force("collide", d3.forceCollide().radius(130))};
const flink1 = () => {simulation.force('link', d3.forceLink(links).id(({id}) => id).strength(0.13))};
const flink2 = () => {simulation.force('link', d3.forceLink(links).id(({id}) => id).strength(0.20))};
const flink3 = () => {simulation.force('link', d3.forceLink(links).id(({id}) => id).strength(0.25))};
const fx1 = () => {simulation.force('x', d3.forceX(width / 2).strength(0.008))};
const fx2 = () => {simulation.force('x', d3.forceX(width / 2).strength(0.015))};
const fx3 = () => {simulation.force('x', d3.forceX(width / 2).strength(0.025))};
const fy1 = () => {simulation.force('y', d3.forceY(height / 2).strength(0.020))};
const fy2 = () => {simulation.force('y', d3.forceY(height / 2).strength(0.070))};
const fy3 = () => {simulation.force('y', d3.forceY(height / 2).strength(0.090))};


const menuItems = [
    {
        id: 'svg-export',
        title: 'Экспорт в SVG',
        action: export2svg
    },
    {
        id: 'stopSim',
        title: 'Стоп симуляции',
        action: stopsim
    },
    {
        id: 'startSim',
        title: 'Старт симуляции',
        action: startsim
    },
    {
        id: 'slowsim',
        title: 'slow симуляции',
        action: slowsim
    },
    {
        id: 'alf1',
        title: 'alf1',
        action: alf1
    },
    {
        id: 'alf2',
        title: 'alf2',
        action: alf2
    },
    {
        id: 'alf3',
        title: 'alf3',
        action: alf3
    },
    {
        id: 'fMb1',
        title: 'fMb1',
        action: fMb1
    },
    {
        id: 'fMb2',
        title: 'fMb2',
        action: fMb2
    },
    {
        id: 'fMb3',
        title: 'fMb3',
        action: fMb3
    },
    {
        id: 'fclde1',
        title: 'fclde1',
        action: fclde1
    },
    {
        id: 'fclde2',
        title: 'fclde2',
        action: fclde2
    },
    {
        id: 'fclde3',
        title: 'fclde3',
        action: fclde3
    },
    {
        id: 'flink1',
        title: 'flink1',
        action: flink1
    },
    {
        id: 'flink2',
        title: 'flink2',
        action: flink2
    },
    {
        id: 'flink3',
        title: 'flink3',
        action: flink3
    },
    {
        id: 'fx1',
        title: 'fx1',
        action: fx1
    },
    {
        id: 'fx2',
        title: 'fx2',
        action: fx2
    },
    {
        id: 'fx3',
        title: 'fx3',
        action: fx3
    },
    {
        id: 'fy1',
        title: 'fy1',
        action: fy1
    },
    {
        id: 'fy2',
        title: 'fy2',
        action: fy2
    },
    {
        id: 'fy3',
        title: 'fy3',
        action: fy3
    }
];

const MENU_LAYOUT = Object.freeze({
    FILL: 'white',
    STROKE: '#00557d',
    BORDERRADIUS: '2px',
    ENTRY: {
        WIDTH: 158,
        HEIGHT: 30,
        OFFSET: {
            RX: 2,
            X: 0,
            Y: 30
        },
        CURSOR: 'pointer'
    },
    TEXT: {
        FILL: '#00557d',
        STROKE: '#00557d',
        FONTSIZE: '20px',
        DX: 11,
        DY: 21,
        OFFSET: {
            X: 0,
            Y: 30
        },
        CURSOR: 'pointer'
    }
});

function menuFactory(svgId, x, y, items) {
    const hide = () => d3.select('#contextMenu').remove();
    const callAction = (d, {action}) => action();

    const offset = (src, value) => (d, i) => src + i * value;

    hide();

    const menuEntry = selectSvg(svgId)
        .append('g').attr('id', 'contextMenu')
        .attr('fill', MENU_LAYOUT.FILL)
        .attr('stroke', MENU_LAYOUT.STROKE)
        .attr('border-radius', MENU_LAYOUT.BORDERRADIUS)
        .selectAll('tmp')
        .data(items).enter()
        .append('g').attr('id', ({id}) => id).attr('class', 'menuEntry');

    menuEntry.append('rect')
        .attr('x', offset(x, MENU_LAYOUT.ENTRY.OFFSET.X))
        .attr('y', offset(y, MENU_LAYOUT.ENTRY.OFFSET.Y))
        .attr('rx', MENU_LAYOUT.ENTRY.OFFSET.RX)
        .attr('width', MENU_LAYOUT.ENTRY.WIDTH)
        .attr('height', MENU_LAYOUT.ENTRY.HEIGHT)
        .attr('cursor', MENU_LAYOUT.ENTRY.CURSOR)
        .on('click', callAction);

    menuEntry.append('text')
        .text(({title}) => title)
        .attr('x', offset(x, MENU_LAYOUT.TEXT.OFFSET.X))
        .attr('y', offset(y, MENU_LAYOUT.TEXT.OFFSET.Y))
        .attr('dx', MENU_LAYOUT.TEXT.DX)
        .attr('dy', MENU_LAYOUT.TEXT.DY)
        .attr('fill', MENU_LAYOUT.TEXT.FILL)
        .attr('stroke', MENU_LAYOUT.TEXT.STROKE)
        .attr('font-size', MENU_LAYOUT.TEXT.FONTSIZE)
        .attr('cursor', MENU_LAYOUT.TEXT.CURSOR)
        .on('click', callAction);

    d3.select('body').on('click', hide);
}

function createContextMenu(d, svgId, items) {
    d.preventDefault();

    return menuFactory(svgId, d.pageX, d.pageY, items);
}

function initializeDisplay() {
        svg = svg.call(zoom)
                .on('contextmenu', (d) => createContextMenu(d, 'main', menuItems))
                .append('g');

	link = svg.append("g")
		.selectAll("g")
		.data(links)
		.join("g")
		.attr("x1", calcX1)
		.attr("y1", calcY1)
		.attr("x2", calcX2)
		.attr("y2", calcY2);

	link.append("svg:defs")
		.append("linearGradient")
		.attr('id', d => `grad_from_${d.source.id}_to_${d.target.id}`)
		.attr("gradientUnits", "userSpaceOnUse")
		.attr("stroke-width", "5px")
		.attr("x1", calcX1)
		.attr("y1", calcY1)
		.attr("x2", calcX2)
		.attr("y2", calcY2)
		.selectAll("stop")
		.data(d => [[1, d.reverse_is_trust], [2, d.is_trust]])
		.join("stop")
		.attr('offset', d => d[0] == 1 ? '0%' : '100%')
		.attr('style', d => {
                    const color = d[1] || d[3] ? 'green' : 'red';

                    return `stop-color: ${color}; stop-opacity: 1`;
		});

	link.append("svg:line")
		.attr("class", "link")
		.attr("x1", calcX1)
		.attr("y1", calcY1)
		.attr("x2", calcX2)
		.attr("y2", calcY2)
		.attr("stroke-width", "1.5px")
		.attr("stroke", d => {
			if (d.target.nodeType == NODE_TYPES.USER || d.target.nodeType == NODE_TYPES.FRIEND || d.target.nodeType == NODE_TYPES.PROFILE || d.source.nodeType == NODE_TYPES.TRUST || d.source.nodeType == NODE_TYPES.MISTRUST || d.target.nodeType == NODE_TYPES.FILTERED){
				if (d.is_trust == d.reverse_is_trust || d.source.nodeType == NODE_TYPES.TRUST || d.source.nodeType == NODE_TYPES.MISTRUST){
					if(d.is_trust || d.source.nodeType == NODE_TYPES.TRUST){
						if(!window.location.href.includes('gen')){
						return "#1c8401";
						}else{
							return "#3548db";
						}
					} else{
						return "#ff0000";
					}
				} else {
					return `url(#grad_from_${d.source.id}_to_${d.target.id})`;
				}
			} else {
				return "#345334";
			}
		})
		.attr("marker-end", d => {
			if (d.target.nodeType == NODE_TYPES.USER || d.target.nodeType == NODE_TYPES.FRIEND || d.target.nodeType == NODE_TYPES.PROFILE || d.source.nodeType == NODE_TYPES.PROFILE || d.source.nodeType == NODE_TYPES.TRUST || d.source.nodeType == NODE_TYPES.MISTRUST || d.target.nodeType == NODE_TYPES.FILTERED){
				if (d.is_trust || d.source.nodeType == NODE_TYPES.TRUST){
					if(!window.location.href.includes('gen')){
					return "url(#arrow-trust)";
					}else{
						return "url(#arrow-gen)";
					}
				} else{
					return "url(#arrow-mistrust)";
				}
			} else {
				return "url(#arrow-to-other)";
			}
		});

	node = svg.append('g')
		.selectAll('g')
		.data(nodes)
		.join('g')
		.attr('onclick', d => `onNodeClick('${d.username}', '${d.nodeType}')`)
	        .attr('class', 'svg_elem')
		.attr('style', 'cursor: pointer')
        	.call(drag(simulation));

	const defs = node.append('defs').attr('id', 'imgdefs');

        initDefClipPaths(defs, node);

	node.append('image').attr('href', ({image}) => image)
		.attr('class', ({nodeType}) => imageClass(nodeType))
		.attr('style', 'z-index: 1; position: relative;')
		.attr('clip-path', ({nodeType, is_dead}) => {
                    let size = '';

                    (nodeType == NODE_TYPES.FILTERED) && (size = 'small');

                    switch (nodeType) {
                        case NODE_TYPES.FRIEND: {
                            size = width < 900 ? 'small' : 'medium';
                            break;
                        }
                        case NODE_TYPES.USER:
                        case NODE_TYPES.PROFILE: {
//                            size = width < 900 ? 'medium': 'large';
                            size = 'medium';
                            break;
                        }
                    }

                    return is_dead ? '' : `url(#clip-circle-${size})`;
        	});

    node.each(function(d) {
        // 1. Сплитим на «всё кроме последнего слова» и «последнее слово»
        const parts = d.text.trim().split(/\s+/);
        const last = parts.length > 1 ? parts.pop() : "";
        const first = parts.join(" ") || last;

        // 2. Добавляем <text> один раз
        const textEl = d3.select(this)
            .append("text")
            .attr("y", 50)
            .attr("font-size", 35)
            .attr("font-weight", 400) // bold
            .attr("class", [NODE_TYPES.USER, NODE_TYPES.PROFILE].includes(d.nodeType)
                ? "userName"
                : "friendName"
            )
            .attr("text-anchor", "middle");

        // 3. Первая строка
        textEl.append("tspan")
            .attr("x", 0)
            .attr("dy", "0em")
            .text(first);

        // 4. Вторая строка (если есть)
        if (last) {
            textEl.append("tspan")
            .attr("x", 0)
            .attr("dy", "1em")
            .text(last);
        }
    });
}

const isUserOrProfile = (nodeType) => nodeType === NODE_TYPES.USER || nodeType === NODE_TYPES.PROFILE;

// расстояние от линии до узла:
// const degree = (nodeType) => width < 900 && isUserOrProfile(nodeType) ? 30 : isUserOrProfile(nodeType) ? 64 : nodeType === NODE_TYPES.FILTERED && width < 900 ? 16 : 32;
const degree = (nodeType) => 50;
const length = (lWidth, lHeight) => Math.sqrt(lWidth * lWidth + lHeight * lHeight);

function relativeX({source: {nodeType}, source, target}) {
  const sourceX = source.x, targetX = target.x;
  
  const lWidth = Math.abs(targetX - sourceX);
  const lLength = length(lWidth, Math.abs(target.y - source.y));
  
  if (!lLength) return [sourceX, targetX, 0, 0];
  
  const cosA = lWidth / lLength;
  const relX = cosA * degree(nodeType);
  
  return [sourceX, targetX, lLength, relX];
}

function relativeY({source: {nodeType}, source, target}) {
  const sourceY = source.y, targetY = target.y;
  
  const lHeight = Math.abs(targetY - sourceY);
  const lLength = length(Math.abs(target.x - source.x), lHeight);
  
  if (!lLength) return [sourceY, targetY, 0, 0];
  
  const sinA = lHeight / lLength;
  const relY = sinA * degree(nodeType);
  
  return [sourceY, targetY, lLength, relY];
}

const sign = (left, right) => left > right ? 1 : -1;

function fullTransform() {
  node.attr('transform', ({x, y}) => `translate(${x}, ${y})`);

  const x1 = (d) => {
    const [sourceX, targetX, lLength, relX] = relativeX(d);

    if (!lLength) return 0;

    const x1 = sourceX + sign(targetX, sourceX) * relX;

    return x1;
  };

  const y1 = (d) => {
    const [sourceY, targetY, lLength, relY] = relativeY(d);

    if (!lLength) return 0;

    const y1 = sourceY + sign(targetY, sourceY) * relY;

    return y1;
  };

  const x2 = (d) => {
    const [sourceX, targetX, lLength, relX] = relativeX(d);

    if (!lLength) return 0;

    const x2 = targetX + -sign(targetX, sourceX) * relX;

    return x2;
  };

  const y2 = (d) => {
    const [sourceY, targetY, lLength, relY] = relativeY(d);

    if (!lLength) return 0;

    const y2 = targetY + -sign(targetY, sourceY) * relY;

    return y2;
  };

  let g = link.selectAll('g');
  g.attr('x1', x1);
  g.attr('y1', y1);
  g.attr('x2', x2);
  g.attr('y2', y2);

  let linearGradient = link.selectAll('linearGradient');
  linearGradient.attr('x1', x1);
  linearGradient.attr('y1', y1);
  linearGradient.attr('x2', x2);
  linearGradient.attr('y2', y2);

  let line = link.selectAll('line');
  line.attr('x1', x1);
  line.attr('y1', y1);
  line.attr('x2', x2);
  line.attr('y2', y2);

  let newLink = link.selectAll('line');
  newLink.attr('x1', x1);
  newLink.attr('y1', y1);
  newLink.attr('x2', x2);
  newLink.attr('y2', y2);
}

function boundedNodeTransform({nodeType, x, y}) {
  const newX = Math.min(Math.max(30, x), width - 30);
  const newY = y < 15 && width < 900 ? 15 : y < 0 ? 0 : (y > height - 20 && width < 900 ? height - 20 : y > height - 70 && width > 900 ? height - 70 : y);
  return `translate(${newX}, ${newY})`;

/*  if (isUserOrProfile(nodeType)) {
    simulation.force('x').x(newX);
    simulation.force('y').y(newY);
  }
*/ // no need to change forces
}

function boundedTransform() {
  node.attr('transform', boundedNodeTransform);

  let g = link.selectAll('g');
  g.attr('x1', calcX1);
  g.attr('y1', calcY1);
  g.attr('x2', calcX2);
  g.attr('y2', calcY2);

  let linearGradient = link.selectAll('linearGradient');
  linearGradient.attr('x1', calcX1);
  linearGradient.attr('y1', calcY1);
  linearGradient.attr('x2', calcX2);
  linearGradient.attr('y2', calcY2);

  let line = link.selectAll("line");
  line.attr('x1', calcX1);
  line.attr('y1', calcY1);
  line.attr('x2', calcX2);
  line.attr('y2', calcY2);
}

const ticked = fullTransform;

function calcX1(d) {
	const sourceX = (d.source.x < 30 && width<900 ? 30 : d.source.x < 0 ? 0 : (d.source.x > width-30 && width<900 ? width-30 : d.source.x > width ? width : d.source.x)); //везде нули
	const targetX = (d.target.x < 30 && width<900 ? 30 : d.target.x < 0 ? 0 : (d.target.x > width-30 && width<900 ? width-30 : d.target.x > width ? width : d.target.x));
	const sourceY = (d.source.y < 15 && width<900 ? 15 : d.source.y < 0 ? 0 : (d.source.y > height-20 && width<900 ? height-20 : d.source.y > height ? height : d.source.y));
	const targetY = (d.target.y < 15 && width<900 ? 15 : d.target.y < 0 ? 0 : (d.target.y > height-20 && width<900 ? height-20 : d.target.y > height ? height : d.target.y));
	var lWidth = Math.abs(targetX - sourceX);
	var lHeight = Math.abs(targetY - sourceY);
        var lLength = Math.sqrt(lWidth * lWidth + lHeight * lHeight);

        if (!lLength) return 0;

	var cosA = lWidth / lLength;
	var relX = (d.source.nodeType == NODE_TYPES.USER && width<900 || d.source.nodeType == NODE_TYPES.PROFILE && width<900 ? 30 : d.source.nodeType == NODE_TYPES.USER || d.source.nodeType == NODE_TYPES.PROFILE ? 64 : d.source.nodeType == NODE_TYPES.FILTERED ? 16 : width<900 ? 16 :  32) * cosA;//64
	var x = targetX > sourceX ? sourceX + relX : sourceX - relX;

	return x;
}

function calcY1(d) {
	const sourceX = (d.source.x < 30 && width<900 ? 30 : d.source.x < 0 ? 0 : (d.source.x > width-30 && width<900 ? width-30 : d.source.x > width ? width : d.source.x)); //везде нули
	const targetX = (d.target.x < 30 && width<900 ? 30 : d.target.x < 0 ? 0 : (d.target.x > width-30 && width<900 ? width-30 : d.target.x > width ? width : d.target.x));
	const sourceY = (d.source.y < 15 && width<900 ? 15 : d.source.y < 0 ? 0 : (d.source.y > height-20 && width<900 ? height-20 : d.source.y > height ? height : d.source.y));
	const targetY = (d.target.y < 15 && width<900 ? 15 : d.target.y < 0 ? 0 : (d.target.y > height-20 && width<900 ? height-20 : d.target.y > height ? height : d.target.y));
	var lWidth = Math.abs(targetX - sourceX);
	var lHeight = Math.abs(targetY - sourceY);
        var lLength = Math.sqrt(lWidth * lWidth + lHeight * lHeight);

        if (!lLength) return 0;

	var sinA = lHeight / lLength;
	var relY = (d.source.nodeType == NODE_TYPES.USER && width<900 || d.source.nodeType == NODE_TYPES.PROFILE && width<900 ? 30 : d.source.nodeType == NODE_TYPES.USER || d.source.nodeType == NODE_TYPES.PROFILE  ? 64 : d.source.nodeType == NODE_TYPES.FILTERED ? 16 : width<900 ? 16 : 32) * sinA;
        var y = targetY > sourceY ? sourceY + relY : sourceY - relY;

	return y;
}

function calcX2(d) {
	const sourceX = (d.source.x < 30 && width<900 ? 30 : d.source.x < 0 ? 0 : (d.source.x > width-30 && width<900 ? width-30 : d.source.x > width ? width : d.source.x)); //везде нули
	const targetX = (d.target.x < 30 && width<900 ? 30 : d.target.x < 0 ? 0 : (d.target.x > width-30 && width<900 ? width-30 : d.target.x > width ? width : d.target.x));
	const sourceY = (d.source.y < 15 && width<900 ? 15 : d.source.y < 0 ? 0 : (d.source.y > height-20 && width<900 ? height-20 : d.source.y > height ? height : d.source.y));
	const targetY = (d.target.y < 15 && width<900 ? 15 : d.target.y < 0 ? 0 : (d.target.y > height-20 && width<900 ? height-20 : d.target.y > height ? height : d.target.y));
	var lWidth = Math.abs(targetX - sourceX);
	var lHeight = Math.abs(targetY - sourceY);
	var lLength = Math.sqrt(lWidth * lWidth + lHeight * lHeight);

        if (!lLength) return 0;

	var cosA = lWidth / lLength;
	var relX = (d.target.nodeType == NODE_TYPES.USER && width<900 || d.target.nodeType == NODE_TYPES.PROFILE && width<900 ? 30 : d.target.nodeType == NODE_TYPES.USER || d.target.nodeType == NODE_TYPES.PROFILE ? 64 : d.target.nodeType == NODE_TYPES.FILTERED ? 16 : width<900 ? 16 : 32) * cosA;
        var x = targetX > sourceX ? targetX - relX : targetX + relX;

	return x;
}

function calcY2(d) {
	const sourceX = (d.source.x < 30 && width<900 ? 30 : d.source.x < 0 ? 0 : (d.source.x > width-30 && width<900 ? width-30 : d.source.x > width ? width : d.source.x)); //везде нули
	const targetX = (d.target.x < 30 && width<900 ? 30 : d.target.x < 0 ? 0 : (d.target.x > width-30 && width<900 ? width-30 : d.target.x > width ? width : d.target.x));
	const sourceY = (d.source.y < 15 && width<900 ? 15 : d.source.y < 0 ? 0 : (d.source.y > height-20 && width<900 ? height-20 : d.source.y > height ? height : d.source.y));
	const targetY = (d.target.y < 15 && width<900 ? 15 : d.target.y < 0 ? 0 : (d.target.y > height-20 && width<900 ? height-20 : d.target.y > height ? height : d.target.y));
	var lWidth = Math.abs(targetX - sourceX);
	var lHeight = Math.abs(targetY - sourceY);
        var lLength = Math.sqrt(lWidth * lWidth + lHeight * lHeight);

        if (!lLength) return 0;

	var sinA = lHeight / lLength;
	var relY = (d.target.nodeType == NODE_TYPES.USER && width<900 || d.target.nodeType == NODE_TYPES.PROFILE && width<900 ? 30 : d.target.nodeType == NODE_TYPES.USER || d.target.nodeType == NODE_TYPES.PROFILE ? 64 : d.target.nodeType == NODE_TYPES.FILTERED ? 16 : width<900 ? 16 : 32) * sinA;
	var y = targetY > sourceY ? targetY - relY : targetY + relY;

	return y;
} 

d3.select(window).on('resize', () => {
    width = +svg.node().getBoundingClientRect().width;
    height = +svg.node().getBoundingClientRect().height;
    simulation.restart();
//  simulation.alpha(1).velocityDecay(0.07).restart(); // added velocityDelay(0.01)
});

function initDefs() {
	const defs = svg.append("defs");

	defs.append("marker")
		.attr("xmlns", "http://www.w3.org/2000/svg")
		.attr("id", "arrow-to-other")
		.attr("viewBox", "0 -5 10 20")
		.attr("refX", "10")
		.attr("refY", "0")
		.attr("markerWidth", "20")
		.attr("markerHeight", "20")
		.attr("orient", "auto")
		.append("path")
		.attr("fill", "#345334")
		.attr("d", "M0,-5 L10,0 L0,5");

	defs.append("marker")
		.attr("xmlns", "http://www.w3.org/2000/svg")
		.attr("id", "arrow-trust")
		.attr("viewBox", "0 -5 10 20")
		.attr("refX", "10")
		.attr("refY", "0")
		.attr("markerWidth", "20")
		.attr("markerHeight", "20")
		.attr("orient", "auto")
		.append("path")
		.attr("fill", "#1c8401")
		.attr("d", "M0,-5 L10,0 L0,5");

	defs.append("marker")
		.attr("xmlns", "http://www.w3.org/2000/svg")
		.attr("id", "arrow-gen")
		.attr("viewBox", "0 -5 10 20")
		.attr("refX", "10")
		.attr("refY", "0")
		.attr("markerWidth", "20")
		.attr("markerHeight", "20")
		.attr("orient", "auto")
		.append("path")
		.attr("fill", "#3b59d6")
		.attr("d", "M0,-5 L10,0 L0,5");

	defs.append("marker")
		.attr("xmlns", "http://www.w3.org/2000/svg")
		.attr("id", "arrow-mistrust")
		.attr("viewBox", "0 -5 10 20")
		.attr("refX", "10")
		.attr("refY", "0")
		.attr("markerWidth", "20")
		.attr("markerHeight", "20")
		.attr("orient", "auto")
		.append("path")
		.attr("fill", "#ff0000")
		.attr("d", "M0,-5 L10,0 L0,5");

	defs.append("marker")
		.attr("xmlns", "http://www.w3.org/2000/svg")
		.attr("id", "arrow-other")
		.attr("viewBox", "0 -5 10 20")
		.attr("refX", "10")
		.attr("refY", "0")
		.attr("markerWidth", "20")
		.attr("markerHeight", "20")
		.attr("orient", "auto")
		.append("path")
		.attr("fill", "#345334")
		.attr("d", "M0,-5 L10,0 L0,5");

	defs.append("clipPath")
		.attr("id", "friendCircle")
		.append("circle")
		.attr("cx", "0")
		.attr("cy", "0")
		.attr("r", "32")
		.attr("fill", "#ff0000");

	defs.append("clipPath")
		.attr("id", "userCircle")
		.append("circle")
		.attr("cx", "0")
		.attr("cy", "0")
		.attr("r", "64")
		.attr("fill", "#ff0000");

	defs.append("clipPath")
		.attr("id", "filteredCircle")
		.append("circle")
		.attr("cx", "0")
		.attr("cy", "0")
		.attr("r", "16")
		.attr("fill", "#ff0000");
}

function initDefClipPaths(defs, node) {
    const sizes = ['small', 'medium', 'large'];
    let radius = 16;
    const idPattern = 'clip-circle-';

    for (const size of sizes) {
        const id = `${idPattern}${size}`;

        const clipPath = defs.append('clipPath').attr('id', id);
        clipPath.append('circle').attr('r', radius);

        node.append('use').attr('href', `#${id}`);

        radius *= 2;
    }
}

function imageClass(nodeType) {
    const hasFilter = localStorage.getItem('filter');

    let nodeClass = 'friendPortrait';

    switch (nodeType) {
        case NODE_TYPES.USER:
        case NODE_TYPES.PROFILE: {
            nodeClass = 'userPortrait';
            break;
        }
        case NODE_TYPES.FILTERED: {
            nodeClass = 'filtered';
            break;
        }
        case NODE_TYPES.FRIEND: {
            hasFilter && (nodeClass += ' friend');
            break;
        }
        case NODE_TYPES.FILTER: {
            hasFilter && (nodeClass += ' active_filer_icon');
            break;
        }
    }

    return nodeClass;
}

function onNodeClick(username, nodeType) {
    const allowed = [NODE_TYPES.PROFILE, NODE_TYPES.FRIEND, NODE_TYPES.FILTERED];
    if (!allowed.includes(nodeType)) return;

    const protocol = settings.url.protocol;
    const host = settings.url.host;
    const pathname = settings.url.pathname;

    const newUrl = new URL(`${protocol}//${host}${pathname}`);

    newUrl.searchParams.append('id', username);
    newUrl.searchParams.append('depth', chat_id ? 1 : 2);
    newUrl.searchParams.append('up', up);
    newUrl.searchParams.append('down', down);

    window.location.href = newUrl.href;
}
