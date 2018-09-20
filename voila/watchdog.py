import asyncio
import logging

import watchdog.events
import watchdog.observers

import tornado.websocket
import tornado.ioloop
import tornado.autoreload

from .paths import ROOT

# We cache event handlers for watchdogs not to waste resources
event_handlers = {}

logger = logging.getLogger('Voila.watchdog')


class WatchDogEventHandler(watchdog.events.RegexMatchingEventHandler):
    def __init__(self, *args, **kwargs):
        super(WatchDogEventHandler, self).__init__(*args, **kwargs)
        self.listeners = []

    def on_any_event(self, event):
        logger.debug('trigger: %r', event)
        try:
            logger.debug('check event loop')
            asyncio.get_event_loop()
            logger.debug('event loop was good')
        except RuntimeError:
            logger.debug('install event loop')
            asyncio.set_event_loop(asyncio.new_event_loop())
        for listener in self.listeners:
            listener()


class WatchDogHandler(tornado.websocket.WebSocketHandler):
    #@tornado.gen.coroutine
    def open(self, path=''):
        self.callback = tornado.ioloop.PeriodicCallback(lambda: self.ping(''), 6000)
        path = path.strip('/') + '.ipynb'
        if path not in event_handlers:
            handlers = []
            watchdog_observer = watchdog.observers.Observer()
            # sometimes useful to add this when triggering does not work
            from watchdog.events import LoggingEventHandler
            logging_handler = LoggingEventHandler()
            watchdog_observer.schedule(logging_handler, '.', recursive=True)

            notebook_handler = WatchDogEventHandler(regexes=['\\./' + path])
            watchdog_observer.schedule(notebook_handler, '.', recursive=True)
            handlers.append(notebook_handler)

            misc_handler = WatchDogEventHandler(regexes=[str(ROOT) + r'/templates/.*', str(ROOT / 'static/main.js'), str(ROOT / 'static/dist/libwidgets.js')])
            watchdog_observer.schedule(misc_handler, str(ROOT), recursive=True)
            handlers.append(misc_handler)

            watchdog_observer.start()
            event_handlers[path] = handlers

            tornado.autoreload.add_reload_hook(self._on_reload)

        self.handlers = event_handlers[path]
        for handler in self.handlers:
            handler.listeners.append(self)

    def __call__(self):
        logger.info('Reload triggered')
        self.write_message({'type': 'reload', 'delay': 'no'})

    def on_close(self):
        for handler in self.handlers:
            handler.listeners.remove(self)

    def _on_reload(self):
        logger.info('Reload triggered (by tornado restart)')
        try:
            self.write_message({'type': 'reload', 'delay': 'long'})
        except tornado.websocket.WebSocketClosedError:
            logger.error('The websocket was already closed, could not send reload message')


    def check_origin(self, origin):
        return True
