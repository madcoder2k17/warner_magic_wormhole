# no unicode_literals untill twisted update
import sys, socket
from twisted.application import service
from twisted.internet import defer, task, reactor
from twisted.python import log
from twisted.python.runtime import platformType
from ..server import RelayServer

def allocate_tcp_port():
    """Return an (integer) available TCP port on localhost. This briefly
    listens on the port in question, then closes it right away."""
    # We want to bind() the socket but not listen(). Twisted (in
    # tcp.Port.createInternetSocket) would do several other things:
    # non-blocking, close-on-exec, and SO_REUSEADDR. We don't need
    # non-blocking because we never listen on it, and we don't need
    # close-on-exec because we close it right away. So just add SO_REUSEADDR.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if platformType == "posix" and sys.platform != "cygwin":
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port

class ServerBase:
    def setUp(self):
        self._setup_relay(None)

    def _setup_relay(self, error, advertise_version=None):
        self.sp = service.MultiService()
        self.sp.startService()
        self.relayport = allocate_tcp_port()
        # need to talk to twisted team about only using unicode in
        # endpoints.serverFromString
        s = RelayServer("tcp:%d:interface=127.0.0.1" % self.relayport,
                        advertise_version=advertise_version,
                        signal_error=error)
        s.setServiceParent(self.sp)
        self._relay_server = s
        self._rendezvous = s._rendezvous
        self.relayurl = u"ws://127.0.0.1:%d/v1" % self.relayport
        self.rdv_ws_port = self.relayport
        # ws://127.0.0.1:%d/wormhole-relay/ws

    def tearDown(self):
        # Unit tests that spawn a (blocking) client in a thread might still
        # have threads running at this point, if one is stuck waiting for a
        # message from a companion which has exited with an error. Our
        # relay's .stopService() drops all connections, which ought to
        # encourage those threads to terminate soon. If they don't, print a
        # warning to ease debugging.

        # XXX FIXME there's something in _noclobber test that's not
        # waiting for a close, I think -- was pretty relieably getting
        # unclean-reactor, but adding a slight pause here stops it...
        from twisted.internet import reactor

        tp = reactor.getThreadPool()
        if not tp.working:
            d = defer.succeed(None)
            d.addCallback(lambda _: self.sp.stopService())
            d.addCallback(lambda _: task.deferLater(reactor, 0.1, lambda: None))
            return d
            return self.sp.stopService()
        # disconnect all callers
        d = defer.maybeDeferred(self.sp.stopService)
        wait_d = defer.Deferred()
        # wait a second, then check to see if it worked
        reactor.callLater(1.0, wait_d.callback, None)
        def _later(res):
            if len(tp.working):
                log.msg("wormhole.test.common.ServerBase.tearDown:"
                        " I was unable to convince all threads to exit.")
                tp.dumpStats()
                print("tearDown warning: threads are still active")
                print("This test will probably hang until one of the"
                      " clients gives up of their own accord.")
            else:
                log.msg("wormhole.test.common.ServerBase.tearDown:"
                        " I convinced all threads to exit.")
            return d
        wait_d.addCallback(_later)
        return wait_d

@defer.inlineCallbacks
def poll_until(predicate):
    # return a Deferred that won't fire until the predicate is True
    while not predicate():
        d = defer.Deferred()
        reactor.callLater(0.001, d.callback, None)
        yield d

@defer.inlineCallbacks
def pause_one_tick():
    # return a Deferred that won't fire until at least the next reactor tick
    d = defer.Deferred()
    reactor.callLater(0.001, d.callback, None)
    yield d
