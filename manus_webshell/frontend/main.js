
import Interface from "./interface";
import Storage from "./storage";

import {postJSON, publish, subscribe} from "./utilities"

import {ControlPanel} from "./apps.js";

$(function() {

    Interface.overlay("Loading ...", "Please wait, the interface is loading.");

    $.ajax('/api/info').done(function(data) {

        $('#appname').text(data.name);
        $('#appversion').text(data.version);

    });

    Interface.action("User", "bi-person", function() {
    });

    Interface.action("Shutdown", "bi-power", function() {

        Interface.dialog("Shutdown", "Do you really want to shutdown the manipulator?",
            { "Cancel" : function() { return true; },
              "Shutdown" : function() { $.ajax('/api/privileged?operation=shutdown').done(function(data) { }); return true; },
              "Restart" : function() { $.ajax('/api/privileged?operation=restart').done(function(data) { }); return true; }
            }
        );

    });


    /* Websocket events connection */

    var loc = window.location, new_uri;
    if (loc.protocol === "https:") { new_uri = "wss:"; } else { new_uri = "ws:"; }
    new_uri += "//" + loc.host;
    var socket = new WebSocket(new_uri + "/api/websocket");

    function waitForConnection() {

        $.ajax('/api/info').done(function(data) {

            location.reload();

        }).fail(function () {

            setTimeout(waitForConnection, 1000);

        });

    }

    var reconnect = true;

    $(window).on('beforeunload', function(){
          reconnect = false;
    });

    socket.onopen = function(event) {
        Interface.overlay();
    }

    socket.onerror = function(event) {
        if (!reconnect) return;
        Interface.overlay("Connection lost", "Unable to communicate with the system.");
        waitForConnection();
    }

    socket.onclose = function(event) {
        if (!reconnect) return;
        Interface.overlay("Connection lost", "Unable to communicate with the system.");
        waitForConnection();
    }

    socket.onmessage = function (event) {
        var msg = JSON.parse(event.data);

        if (msg.channel == "camera") {

            publish("camera.update", msg.data);

        } else if (msg.channel == "manipulator") {

            publish("manipulator.update", msg.data);

        } else if (msg.channel == "storage") {

            if (msg.action == "update") {
                publish("storage.update", msg.key);
            } else if (msg.action == "delete") {
                publish("storage.delete", msg.key);
            }

        } else if (msg.channel == "apps") {

            if (msg.action == "activated") {
                publish("apps.active", msg.identifier);
            } else if (msg.action == "deactivated") {
                publish("apps.active", undefined);
            } else if (msg.action == "output") {
                publish("apps.console", {identifier: msg.identifier, lines: msg.lines, source: "output"});
            } else if (msg.action == "input") {
                publish("apps.console", {identifier: msg.identifier, lines: msg.lines, source: "input"});
            }

        } else if (msg.channel == "markers") {

            markers.clear();
            for (i in msg.markers) {
                var marker = msg.markers[i];
                markers.add(marker.location, marker.rotation, marker.size, marker.color);
            }

        }

    }

    subscribe("apps.send", function(data, ev) {

        socket.send(JSON.stringify({"channel" : "apps", "action": "input", "identifier" : data.identifier, "lines" : data.lines}));

    });

    subscribe("manipulator.move_joint", function(data, ev) {

        var data = {"id" : data.id, "goal" : data.position, "speed" : data.speed};

        postJSON('/api/manipulator/joint', data);

    });


    $.ajax('/api/manipulator/describe').done(function(data) {

        $.ajax('/api/manipulator/state').done(function(data) {
            publish("manipulator.update", data);
        });

        ControlPanel();

        publish("manipulator.initialize", data);

    }).fail(function () {});



});