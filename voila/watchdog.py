import asyncio

import watchdog.events
import watchdog.observers

import tornado.websocket
import tornado.ioloop

from .paths import ROOT

# we cache event handler for watchdogs not to waste resources
event_handlers = {}

class WatchDogEventHandler(watchdog.events.RegexMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        super(WatchDogEventHandler, self).__init__(*args, **kwargs)
        self.listeners = []

    def on_any_event(self, event):
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        for listener in self.listeners:
            listener()



class WatchDogHandler(tornado.websocket.WebSocketHandler):
    #@tornado.gen.coroutine
    def open(self, path=''):
        self.callback = tornado.ioloop.PeriodicCallback(lambda: self.ping(''), 6000)
        path = path.strip('/') + '.ipynb'
        if path not in event_handlers:
            watchdog_observer = watchdog.observers.Observer()
            # sometimes useful to add this when triggering does not work
            # from watchdog.events import LoggingEventHandler
            # logging_handler = LoggingEventHandler()
            # watchdog_observer.schedule(logging_handler, '.', recursive=True)
            
            handler = WatchDogEventHandler(regexes=['\\./' + path])
            watchdog_observer.schedule(handler, '.', recursive=True)
            
            handler = WatchDogEventHandler(regexes=[str(ROOT) +r'/templates/.*', str(ROOT / 'static/main.js'), str(ROOT / 'static/dist/libwidgets.js')])
            watchdog_observer.schedule(handler, str(ROOT), recursive=True)
            
            watchdog_observer.start()
            event_handlers[path] = handler
            
            tornado.autoreload.add_reload_hook(self._on_reload)
        self.handler = event_handlers[path]
        self.handler.listeners.append(self)

    def __call__(self):
        self.write_message({'type': 'reload', 'delay': 'no'})

    def on_close(self):
        self.handler.listeners.remove(self)

    def _on_reload(self):
        try:
            self.write_message({'type': 'reload', 'delay': 'long'})
        except tornado.websocket.WebSocketClosedError:
            print('a websocket was already closed')


    def check_origin(self, origin):
        return True
