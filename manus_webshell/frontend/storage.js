
import {subscribe} from "./utilities";

let subscriptions = {};

subscribe("storage.update", function(data, ev) {

    if (subscriptions[key] === undefined)
        return;

    for (cb in subscriptions[key]) {
        cb(msg);
    }

});

let Storage = {
    get : function(key, callback) {
        $.ajax('/api/storage?key=' + key).done(function(data) {
            callback(key, data);
        }).fail(
            function(data) {
                callback(key, {});
            }
        );

    },
    list: function(callback) {
        $.ajax('/api/storage').done(function(data) {
            callback(data);
        });
    },
    set: function(key, value) {
        $.ajax({
            'type': 'POST',
            'url': '/api/storage?key=' + key,
            'contentType': 'application/json',
            'data': JSON.stringify(value),
            'dataType': 'json'
        });
    },
    delete(key) {
        $.ajax({
            'type': 'POST',
            'url': '/api/storage?key=' + key,
            'contentType': 'application/json',
            'data': '',
            'dataType': 'json'
        });
    },
    subscribe(key, callback) {
        if (subscriptions[key] === undefined) {
            subscriptions[key] = [];
        }

        subscriptions[key].push(callback);

        Storage.get(key, callback);
    }
};

export default Storage;