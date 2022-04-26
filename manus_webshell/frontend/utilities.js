

import PubSub from "PubSub";

let hub = new PubSub();

function publish(topic, data) {
  hub.publish(topic, data);
}

function subscribe(topic, callback) {
  hub.subscribe(topic, callback);
}

function uniqueIdentifier() {
  return Math.round(new Date().getTime() + (Math.random() * 100));
}


function nameIdentifier(name) {
  return name.toLowerCase().replace(/[^_0-9a-z]/gi, '_');
}

function formatDateTime(date) {
  var monthNames = [
    "January", "February", "March",
    "April", "May", "June", "July",
    "August", "September", "October",
    "November", "December"
  ];

  var day = date.getDate();
  var monthIndex = date.getMonth();
  var year = date.getFullYear();

  return day + ' ' + monthNames[monthIndex] + ' ' + year + " " + date.getHours() + ":" + date.getMinutes();
}

function postJSON(url, data, callback) {
  return jQuery.ajax({
    'type': 'POST',
    'url': url,
    'contentType': 'application/json',
    'data': JSON.stringify(data),
    'dataType': 'json',
    'success': callback
  });
};

function getJSON(url, data, callback) {
  return jQuery.ajax({
    'type': 'GET',
    'url': url,
    'contentType': 'application/json',
    'data': JSON.stringify(data),
    'dataType': 'json',
    'success': callback
  });
};


export { postJSON, getJSON, formatDateTime, uniqueIdentifier, nameIdentifier, publish, subscribe };