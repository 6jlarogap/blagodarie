const Message = (type, data) => ({ type: type, ...data });

onmessage = function({ data }) {
    postMessage(Message('start'));

    for (let tick = 0; tick < data.nTicks; ++tick) {
        postMessage(Message('tick'));
    }

    postMessage(Message('end', data));
};
