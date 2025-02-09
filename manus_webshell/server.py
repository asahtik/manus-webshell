#!/usr/bin/env python
from __future__ import absolute_import

import inspect
import json
import time
import tempfile
import logging
import logging.handlers
import os.path
import os
import signal
import traceback
from bsddb3 import db 

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.websocket

import echolib
import echolib.tornado

from .generator import AppGenerator
from .utilities import RedirectHandler, JsonHandler, NumpyEncoder

from . import frontend

from manus_webshell.manipulator import ManipulatorDescriptionHandler, \
                                       ManipulatorStateHandler, ManipulatorMoveJointHandler, \
                                       ManipulatorMoveHandler, ManipulatorMoveSafeHandler, \
                                       ManipulatorTrajectoryHandler

from manus.messages import MarkersSubscriber
import manus
from manus_webshell import PrivilegedClient, ConfigManager

__author__ = 'lukacu'

class ApplicationHandler(JsonHandler):

    def __init__(self, application, request):
        super(ApplicationHandler, self).__init__(application, request)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    def get(self):
        self.response = {
            "name" : manus.NAME,
            "version" : manus.VERSION
        }
        self.write_json()

class CameraDescriptionHandler(JsonHandler):

    def __init__(self, application, request, camera):
        super(CameraDescriptionHandler, self).__init__(application, request)
        self.camera = camera

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    def get(self):
        if getattr(self.camera, 'parameters', None) is None:
            self.clear()
            self.set_status(400)
            self.finish('Unavailable')
            return
        parameters = self.camera.parameters
        self.response = {
            "image" : {"width" : parameters.width, "height" : parameters.height},
            "intrinsics" : parameters.intrinsics,
            "distortion" : parameters.distortion
        }
        self.write_json()

class CameraLocationHandler(JsonHandler):

    def __init__(self, application, request, camera):
        super(CameraLocationHandler, self).__init__(application, request)
        self.camera = camera

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    async def get(self):
        location = await self.camera.location()

        self.set_header('X-Timestamp', location.header.timestamp.isoformat())
        self.response = CameraLocationHandler.encode_location(location)
        self.write_json()
        self.finish()

    @staticmethod
    def encode_location(location):
        return {
            "rotation" : location.rotation,
            "translation" : location.translation,
        }

    def check_etag_header(self):
        return False

class AppsHandler(JsonHandler):
    def __init__(self, application, request, apps):
        super(AppsHandler, self).__init__(application, request)
        self._apps = apps

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    def get(self):
        active = self._apps.active()
        self.response = {"list" : self._apps.list()}
        if not active is None:
            self.response["active"] = active.id
        self.write_json()

    def post(self):
        if "run" in self.request.json:
            self.response = {"result" : "ok"}
            self.write_json()
            self._apps.run(self.request.json["run"])
            return
        if "code" in self.request.json:
            try:
                generator = AppGenerator("/tmp")
                generator.generate(self.request.json[u"code"], tempfile.gettempdir())
                self.response = {
                    "status" : "ok",
                    "identifier": app_identifier("/tmp/generated_app.app")
                }
                self.write_json()
                self._apps.run("/tmp/generated_app.app")
            except Exception as e:
                self.response = {
                    "status" : "error",
                    "description" : e.message
                }        
                self.write_json()
            return

        self._apps.run("")
        self.response = {"result" : "ok"}
        self.write_json()


    def check_etag_header(self):
        return False

class LoginHandler(JsonHandler):

    def __init__(self, application, request, users):
        super(LoginHandler, self).__init__(application, request)
        self._users = users

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    def get(self):
        self.response = {"result" : False}
        self.write_json()

    def post(self):
        self.set_secure_cookie("user", self.get_argument("username"))
        self.response = {"result" : True}
        self.write_json()

class PrivilegedHandler(JsonHandler):

    def __init__(self, application, request, privileged):
        super(PrivilegedHandler, self).__init__(application, request)
        self._privileged = privileged

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    def get(self):
        operation = self.get_argument("operation")
        if operation == "shutdown":
            self._privileged.request_shutdown("")
        if operation == "restart":
            self._privileged.request_restart("")
        self.response = {"result" : True}
        self.write_json()

class StorageHandler(tornado.web.RequestHandler):
    keys = []

    def __init__(self, application, request, storage):
        super(StorageHandler, self).__init__(application, request)
        self._storage = storage
        StorageHandler.keys = set(storage.keys())

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    def get(self):
        key = self.request.arguments.get("key", [""])[0].strip()
        if not key:
            self.set_header('Content-Type', 'application/json')
            self.finish(json.dumps(list(StorageHandler.keys)))
            return
        try:
            raw = self._storage.get(key, "")
        except db.DBNotFoundError:
            self.set_status(404)
            self.finish("Unknown key")
            return
        try:
            ctype, data = raw.split(";", 1)
        except ValueError:
            ctype = 'text/plain'
            data = ''
        self.set_header('Content-Type', ctype)
        self.finish(data)

    def post(self):
        key = self.request.arguments.get("key", [""])[0].strip()
        if not key:
            self.set_status(401)
            self.finish('Illegal request')
            return
        try:
            ctype, _ = self.request.headers.get('Content-Type').split(";", 1)
        except ValueError:
            ctype = self.request.headers.get('Content-Type')
        if len(self.request.body) == 0:
            try:
                print("Deleting %s" % key)
                self._storage.delete(key)
                StorageHandler.keys.remove(key)
                ApiWebSocket.distribute_message({"channel": "storage", "action" : "delete", "key" : key})
            except db.DBNotFoundError:
                self.finish('Unknown key')
                return
        else:
            data = "%s;%s" % (ctype, self.request.body)
            self._storage.put(key, data)
            StorageHandler.keys.add(key)
            print("Updating %s, content length %d bytes" % (key, len(self.request.body)))
            ApiWebSocket.distribute_message({"channel": "storage", "action" : "update", "key" : key, "content" : ctype})
        self.finish()
        
    def check_etag_header(self):
        return False

class ConfigHandler(tornado.web.RequestHandler):

    def initialize(self, config):
        self._config = config

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    def get(self):
        key = self.request.arguments.get("key", [""])[0].strip()
        if not key:
            self.set_status(404)
            self.finish("Unknown key")
            return
        value = self._config.get(key)
        self.set_header('Content-Type', "text/plain")
        self.finish(value)

    def post(self):
        key = self.request.arguments.get("key", [""])[0].strip()
        if not key:
            self.set_status(401)
            self.finish('Illegal request')
            return
        self._config.set(key, self.request.body)
        self.finish()
        
    def check_etag_header(self):
        return False


class ApiWebSocket(tornado.websocket.WebSocketHandler):
    connections = []

    def initialize(self, cameras=None, manipulators=None, apps=None, config=None):
        self.cameras = cameras
        self.manipulators = manipulators
        #self.apps = apps
        self.config = config

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    def open(self, *args, **kwargs):
        ApiWebSocket.connections.append(self)
        for c in self.cameras:
            c.listen_location(self.on_camera_location)
        for m in self.manipulators:
            m.listen(self)
        #self.apps.listen(self)
        self.config.listen(self.on_config_change)

    def on_message(self, message):
        decoded = json.loads(message)
        channel = decoded.get("channel", "")
        action = decoded.get("action", "")
        #if channel == "apps":
        #    if action == "input" and not self.apps.active() is None:
        #        if decoded.get("identifier", "") == self.apps.active().id:
        #            self.apps.input(decoded.get("lines", []))

        # can request info about the device?

    def on_close(self):
        ApiWebSocket.connections.remove(self)
        for c in self.cameras:
            c.unlisten_location(self.on_camera_location)
        for m in self.manipulators:
            m.unlisten(self)
        #self.apps.unlisten(self)
        self.config.unlisten(self.on_config_change)

    def send_message(self, message):
        message = json.dumps(message, cls=NumpyEncoder)
        self.write_message(message)

    @staticmethod
    def distribute_message(message):
        message = json.dumps(message, cls=NumpyEncoder)
        for c in ApiWebSocket.connections:
            c.write_message(message)

    def on_camera_location(self, camera, location):
        self.send_message({"channel": "camera", "action" : "update", "data" : CameraLocationHandler.encode_location(location)})

    def on_manipulator_state(self, manipulator, state):
        self.send_message({"channel": "manipulator", "action" : "update", "data" : ManipulatorStateHandler.encode_state(state)})

    def on_planner_state(self, manipulator, state):
        pass

    def on_app_active(self, app):
        if app is None:
            self.send_message({"channel": "apps", "action" : "deactivated" })
        else:
            self.send_message({"channel": "apps", "action" : "activated", "identifier" : app.id})

    def on_app_output(self, identifier, lines):
        self.send_message({"channel": "apps", "action" : "output", "identifier": identifier, "lines" : lines})

    def on_app_input(self, identifier, lines):
        self.send_message({"channel": "apps", "action" : "input", "identifier": identifier, "lines" : lines})

    def on_config_change(self, manager, keys):
        for key in keys:
            self.send_message({"channel": "config", "action" : "updated", "key": key, "value" : manager.get(key)})

def on_shutdown():
    tornado.ioloop.IOLoop.instance().stop()
    print("Stopping gracefully")

def main():

    logging_level = logging.DEBUG

    logger = logging.getLogger("manus")
    logger.propagate = False

    log_storage = logging.StreamHandler()
    log_storage.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(log_storage)
    logger.setLevel(logging_level)

    client = echolib.Client(name="webshell")
    storage = db.DB()

    try:

        storagefile = os.getenv('MANUS_STORAGE', "/tmp/manus_storage.db")
        if os.path.exists(storagefile):
            logger.info("Opening storage database from %s" % storagefile)
            storage.open(storagefile, None, db.DB_HASH)
        else:
            logger.info("Creating storage database in %s" % storagefile)
            storage.open(storagefile, None, db.DB_HASH, db.DB_CREATE)
            defaults_storage = os.getenv('MANUS_STORAGE_DEFAULTS', None)
            if defaults_storage and os.path.exists(defaults_storage):
                for root, dirs, files in os.walk(defaults_storage):
                    for file in files:
                        if file.endswith(".json"):
                            key = os.path.splitext(file)[0]
                            with open(os.path.join(defaults_storage, file), 'r') as fd:
                                data = "%s;%s" % ("text/json", fd.read())
                                storage.put(key, data)
                                logger.info("Restoring initial data from: %s" % file)
 
        handlers = []
        cameras = []
        manipulators = []

        try:
            camera = echolib.tornado.Camera(client, "camera0")
            handlers.append((r'/api/camera/video', echolib.tornado.VideoHandler, {"camera": camera}))
            handlers.append((r'/api/camera/image', echolib.tornado.ImageHandler, {"camera": camera}))
            handlers.append((r'/api/camera/describe', CameraDescriptionHandler, {"camera": camera}))
            handlers.append((r'/api/camera/position', CameraLocationHandler, {"camera": camera}))
            cameras.append(camera)
        except Exception as e:
            print(traceback.format_exc())

        try:
            manipulator = manus.Manipulator(client, "manipulator0")
            handlers.append((r'/api/manipulator/describe', ManipulatorDescriptionHandler, {"manipulator": manipulator}))
            handlers.append((r'/api/manipulator/state', ManipulatorStateHandler, {"manipulator": manipulator}))
            handlers.append((r'/api/manipulator/joint', ManipulatorMoveJointHandler, {"manipulator": manipulator}))
            handlers.append((r'/api/manipulator/move', ManipulatorMoveHandler, {"manipulator": manipulator}))
            handlers.append((r'/api/manipulator/safe', ManipulatorMoveSafeHandler, {"manipulator": manipulator}))
            handlers.append((r'/api/manipulator/trajectory', ManipulatorTrajectoryHandler, {"manipulator": manipulator}))
            manipulators.append(manipulator)
        except Exception as e:  
            print(traceback.format_exc())
    
        #handlers.append((r'/api/markers', MarkersStorageHandler))
        #apps = AppsManager(client)
        privileged = PrivilegedClient(client)
        config = ConfigManager(client)

        #handlers.append((r'/api/login', LoginHandler, {"users" : None}))
        #handlers.append((r'/api/apps', AppsHandler, {"apps" : apps}))
        handlers.append((r'/api/privileged', PrivilegedHandler, {"privileged": privileged}))
        handlers.append((r'/api/storage', StorageHandler, {"storage" : storage}))
        handlers.append((r'/api/websocket', ApiWebSocket, {"cameras" : cameras, "manipulators": manipulators, "config": config}))
        handlers.append((r'/api/config', ConfigHandler, {"config" : config}))
        handlers.append((r'/api/info', ApplicationHandler))
        handlers.append((r'/', RedirectHandler, {'url' : '/index.html'}))

        frontend_root = os.path.dirname(frontend.__file__)

        print(os.path.isfile(os.path.join(frontend_root, "main.js")))

        if os.path.isfile(os.path.join(frontend_root, "main.js")):
            frontend.DevelopmentStaticFileHandler._setup()
            handlers.append((r'/(.*)', frontend.DevelopmentStaticFileHandler))
        else:
            handlers.append((r'/(.*)', tornado.web.StaticFileHandler, {'path': os.path.dirname(frontend.__file__)}))

        def markers_callback(markers):
            data = {m.id : {"location": [m.location.x, m.location.y, m.location.z], \
                "rotation": [m.rotation.x, m.rotation.y, m.rotation.z], \
                "size": [m.size.x, m.size.y, m.size.z], \
                "color": [m.color.red, m.color.green, m.color.blue]} for m in markers.markers}
            ApiWebSocket.distribute_message({"channel": "markers", "action" : "overwrite", "markers" : data, "overlay" : markers.owner})

        markers_subscriber = MarkersSubscriber(client, "markers", markers_callback)

        application = tornado.web.Application(handlers, cookie_secret=os.getenv('MANUS_COOKIE_SECRET', "manus"), debug=bool(os.getenv('MANUS_DEBUG', "false")))

        server = tornado.httpserver.HTTPServer(application)
        server.listen(int(os.getenv('MANUS_PORT', "8080")))

        tornado_loop = tornado.ioloop.IOLoop.instance()

        signal.signal(signal.SIGINT, lambda sig, frame: tornado_loop.add_callback_from_signal(on_shutdown))
        signal.signal(signal.SIGTERM, lambda sig, frame: tornado_loop.add_callback_from_signal(on_shutdown))

        def on_disconnect(client):
            tornado_loop.stop()

        echolib.tornado.install_client(tornado_loop, client, on_disconnect)

        logger.info("Starting %s webshell" % manus.NAME)

        def flush_database():
            # Flush every 5 seconds
            storage.sync()
            tornado_loop.add_timeout(time.time() + 5, flush_database)

        flush_database()

        try:
            tornado_loop.start()
        except KeyboardInterrupt:
            pass
        except Exception as err:
            print(traceback.format_exc())

        echolib.tornado.uninstall_client(tornado_loop, client)

        flush_database()

    except Exception as e:
        print(traceback.format_exc())

    logger.info("Stopping %s webshell" % manus.NAME)
    storage.close()

