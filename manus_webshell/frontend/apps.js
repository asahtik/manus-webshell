
import Interface from "./interface";

import { jointWidget, fancybutton } from "./widgets";

import { publish, subscribe, uniqueIdentifier } from "./utilities";

import Storage from "./storage";

import control_template from "./templates/control.handlebars";
import poselist_template from "./templates/poselist.handlebars";

function appsList() {

    var augmentItem = function(item) {
        var container = $(item.elm);
        if (container.hasClass('pose-item'))
            return;

        container.attr("id", "app-" + item.values().identifier);

        container.addClass('apps-item');

        container.click(function () {
            if (container.hasClass("expanded")) {
                container.removeClass("expanded");
            } else {
                container.siblings().removeClass("expanded");
                container.addClass("expanded");
            }
        });

        var tools = $('<div />').addClass('list-tools').prependTo(container);

        tools.append($('<i />').addClass('tool glyphicon glyphicon-play').click(function() {
            if ($(this).hasClass('glyphicon-play')) {

                postJSON('/api/apps', {"run" : item.values().identifier},function(data) {});

            } else {

                postJSON('/api/apps', {"run" : ""},function(data) {});
                
            }
            return false;
        }).tooltip({title: "Run/Stop", delay: 1}));

    }

    var updating = false;

    var list = new List("appslist", {
        valueNames : ["name", "version", "description"],
        item: "<a class='list-group-item'><div class='name'></div><div class='version'></div><pre class='description'></pre></a>"
    }, []);

    var index = 0;

    list.on("updated", function() {

        for (var i = 0; i < list.items.length; i++) {
            augmentItem(list.items[i]);
        }

    });

    $.ajax('/api/apps').done(function(data) {
        items = [];
        for (var key in data.list) { items.push(data.list[key]); }
        list.add(items);
        changeActive(data.active);
    });

    var changeActive = function(identifier) {

        $(list.listContainer).find("i.glyphicon-stop").removeClass("glyphicon-stop").addClass("glyphicon-play");
        if (identifier)
            $("#app-" + identifier + " i.tool").removeClass("glyphicon-play").addClass("glyphicon-stop");

    }

    PubSub.subscribe("apps.active", function(msg, identifier) {changeActive(identifier)});

}


function ControlPanel() {

    var emergency;
    var viewer;
    var manipulator;
    var markers;
/*
    function queryMarkerStatus() {

        $.ajax('/api/markers/get', {timeout : 300}).done(function(data) {

            markers.clear();
            for (var m in data) {
                markers.add(data[m]["position"], data[m]["orientation"], data[m]["color"]);
            }

            setTimeout(queryMarkerStatus, 250);

        }).fail(function () {

            setTimeout(queryMarkerStatus, 1000);

        });

    }
*/
    /* Camera stuff */
/*
    var viewer = $.manus.world.viewer({});
    $('#viewer').append(viewer.wrapper);
    $.manus.world.grid(viewer, 40, 27, 10, vec3.fromValues(230, 0, 0));

    var updateViewer = function() {
        viewer.zoom($('#viewer').width() / viewer.width());
    }

    var markers = $.manus.world.markers(viewer);

    $( window ).on("resize", updateViewer);
    updateViewer();

    var viewbar_left = $("#world .toolbar.left");
    var viewbar_right = $("#world .toolbar.right");

    viewbar_left.append($.manus.widgets.fancybutton({icon : "globe", tooltip: "Free view", callback: function(e) {
                    viewer.view(null);
                    updateViewer();
                }}));

    $.ajax('/api/camera/describe').done(function(data) {

        cameraView = $.manus.world.views.camera('camera', '/api/camera/video', data);

        $.ajax('/api/camera/position').done(function(data) {
            PubSub.publish("camera.update", data);
        });

        viewbar_left.append($.manus.widgets.fancybutton({icon : "facetime-video", tooltip: "Camera view", callback: function(e) {
                if (cameraView) { 
                    viewer.view(cameraView);
                    updateViewer();
                }
            }}));

    }).fail(function () {});

    viewbar_right.append($.manus.widgets.fancybutton({icon : "camera", tooltip: "Take snapshot",callback: function(e) {
        $(this).attr({href: viewer.snapshot(), download: 'snapshot.png'});
    }}));
*/
    /* Manipulator stuff */

    var joints = [];

    var container = $(control_template());

    //$.manus.world.manipulator(viewer, "manipulator", data);

    //markers = $.manus.world.markers(viewer);
    //markers.clear();

    var augmentItem = function(item) {
        var container = $(item.elm);
        if (container.hasClass('pose-item'))
            return;

        container.addClass('pose-item');
        var tools = $('<div />').addClass('list-tools').prependTo(container);

        container.on("click", function () {

            var data = item.values().pose;

            var goals = [];
            for (var i = 0; i < data.joints.length; i++)
                goals.push(data.joints[i].position);
            postJSON('/api/manipulator/move', [{"goals": goals, "speed" : 1.0}]);

        });

        tools.append($('<i />').addClass('tool glyphicon glyphicon-pencil').click(function() {

            if (container.hasClass('editable'))
                return;

            container.addClass('editable');
            var textbox = container.children(".name");
            textbox.text(item.values().name);
            textbox.attr('contenteditable', 'true');

            var sel = window.getSelection();

            textbox.on('blur', function() {
                textbox.attr('contenteditable', 'false');
                container.removeClass('editable');
            }).trigger();

            var sel = window.getSelection();
            var range = document.createRange();
            range.setStart(textbox[0], 1);
            range.collapse(true);
            sel.removeAllRanges();
            sel.addRange(range);

            textbox.on('keyup', function(event) {
                if(event.key === 'Enter') {
                    container.removeClass('editable');
                    item.values({"name": textbox.text()});
                    list.update();
                    event.stopPropagation();
                } else if (event.keyCode == 27) {
                    textbox.attr('contenteditable', 'false');
                    container.removeClass('editable');
                    textbox.text(item.values().name);
                    container.trigger();
                    event.stopPropagation();
                }
                return true;
            });

            return false;
        }));

        tools.append($('<i />').addClass('tool glyphicon glyphicon-trash').click(function() {
            list.remove("identifier", item.values().identifier);
            return false;
        }));

    }

    var currentPose = null;
    var updating = false;

    Storage.subscribe("poses", function(key, data) {

        console.log(data);

        let poselist = $(poselist_template({poses: data}));

        poselist.find(".list-group-item").each(function(i, element) {
            augmentItem(element);
        })

        container.find(".poselist").replaceAll(poselist);

    });

    subscribe("manipulator.initialize", function(data, ev) {

        let controls = container.find(".controls");

        controls.text(data.name + " (version: " + data.version + ")");

        var id = 1;
        for (var v in data["joints"]) {
            if (data["joints"][v].type.toLowerCase() == "fixed")
                continue;
            joints[v] = jointWidget(controls, "manipulator", parseInt(v), "Joint " + id, data["joints"][v]);
            id = id + 1;
        }

    });

    subscribe("manipulator.update", function(data, ev) {

        currentPose = data;
        
    });

    var uniqueIndex = 0;

    container.filter(".right").append(fancybutton({
        icon: "bi-bookmark-plus", tooltip: "Add current pose",
        callback: function() {
            if (!currentPose) return;

            Storage.get("poses", function(list) {
                uniqueIndex++;
                list.push([{
                    identifier : uniqueIdentifier(),
                    name : "New pose " + uniqueIndex,
                    pose: currentPose
                }]);
                Storage.set("poses", list);
            });
        }
    }));

    console.log(container.filter("div.left"));

    container.filter(".left").append(fancybutton({
        icon: "bi-house", tooltip: "Safe position",
        callback: function() {
            postJSON('/api/manipulator/safe', []);
        }
    }));

    Interface.tab('Control', 'controller', container);

}

export {ControlPanel};