

import json
import numpy

import tornado


def synchronize(f):
    def wrapper(*args, **kwargs):
        obj = args[0]
        if not hasattr(obj, "loop"):
            # print "Warning"
            f(*args, **kwargs)
        else:
            obj.loop.add_callback(f, *args, **kwargs)

    return wrapper


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)

class RedirectHandler(tornado.web.RequestHandler):

    def __init__(self, application, request, url):
        super(RedirectHandler, self).__init__(application, request)
        self.url = url

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def get(self):
        self.redirect(self.url, True)
        # self.finish()

class NumpyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, numpy.integer):
            return int(obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()
        else:
            return super(NumpyEncoder, self).default(obj)

class JsonHandler(tornado.web.RequestHandler):
    """Request handler where requests and responses speak JSON."""

    def prepare(self):
        self.request.json = {}
        self.response = {}
        if self.request.body:
            try:
                self.request.json = json.loads(self.request.body)
            except ValueError as e:
                print(e)
                self.write_error(400, message='Unable to parse JSON.')
                return

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')
        self.set_header('Access-Control-Allow-Origin', '*')

    def write_error(self, status_code, **kwargs):
        message = {}
        if 'exc_info' in kwargs:
            message['message'] = str(kwargs['exc_info'])
        if 'message' in kwargs:
            message['message'] = kwargs['message']
        elif status_code == 405:
            message['message'] = 'Invalid HTTP method.'
        else:
            message['message'] = 'Unknown error.'

        self.response = message
        self.write_json()

    def write_json(self):
        output = json.dumps(self.response, cls=NumpyEncoder)
        self.write(output)

    def get_current_user(self):
        return self.get_secure_cookie("user")
