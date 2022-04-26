
import {Modal} from "bootstrap";

import "./assets/manus.css";
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';

import body_template from "./templates/body.handlebars";
import dialog_template from "./templates/dialog.handlebars";
import overlay_template from "./templates/overlay.handlebars";
import about_template from "./templates/about.handlebars";
import tab_menu_template from "./templates/tab_menu.handlebars";

import {makeIcon} from "./widgets";

import {uniqueIdentifier} from "./utilities";

$(function() {

    $("body").empty().append(body_template());

    $("#logo").on("click", function() {

        $.ajax('/api/info').done(function(data) {

            Interface.notification("About Manus", $(about_template({manus_version: data.version})));

        });
    

    });

});

let _overlay = undefined;
let _dialog = undefined;

let Interface = {

    overlay: function (title, message) {

        if (title === undefined) {
            if (_overlay) {
                _overlay.hide();
                _overlay = undefined;
            }
        } else {
            if (_overlay) {
                Interface.overlay();
            }

            _overlay = new Modal($(overlay_template({title, message}))[0], {backdrop: 'static', keyboard : false, show: false});
            $("body").append(_overlay);
            _overlay.show();
        }

    },

    dialog: function (title, message, buttons) {

        if (title === undefined) {
            if (_dialog != null) {
                _dialog.hide();
                _dialog = null;
            }
            return;
        }

        _dialog = new Modal($(dialog_template({
                title,
                message: (typeof message == 'string') ? message : ""}))[0], {backdrop: 'static', keyboard : false, show: false});

        let element = $(_dialog._element);

        if (typeof message == 'function') {
            message(element.find(".modal-body").empty());
        } else {
            element.find(".modal-body").empty().append(message.clone());
        }

        let footer = $(element).find(".modal-footer");
        footer.empty();

        if (typeof buttons == 'string') {
            footer.append($("<button/>")
                .addClass("btn btn-default").text(buttons)
                .on("click", function() { Interface.dialog(); }));
        } else {
            function create_button(name, callback) {
                return $("<button/>").addClass("btn btn-default").text(name)
                    .on("click", function() {
                        if (callback()) 
                            Interface.dialog();
                    });
            }
            for (var b in buttons) {
                footer.append(create_button(b, buttons[b]));
            }
        }

        Interface.overlay();

        $('body').append(_dialog);
        _dialog.show();
    },

    confirmation: function (title, message, callback) {

        Interface.dialog(title, message, {
            "Cancel" : function() { return true; },
            "Confirm": function() { callback(); return true; }
        });

    },

    notification: function (title, message) {

        Interface.dialog(title, message, "Close");

    },

    tab: function (name, icon, body) {

        let id = id

        $('body').find("#tabs").append($('<div class="tab-pane active"></div>').data("tab-name", name).append(body));        

        $('body').find("#menu").append($(tab_menu_template({name, icon})));
    },

    action: function(name, icon, callback) {

        let button = $("<li>").append($("<a>").attr("href", "#").append(makeIcon(icon)));

        button.attr("title", name);

        button.on("click", function(e) {
            callback();
            return false;
        })

        $("body").find("#actions").append(button);

    }

};

export default Interface;