# NO unicode_literals or static.Data() will break, because it demands
# a str on Python 2
from __future__ import print_function
import os, time, json
from twisted.python import log
from twisted.internet import reactor, endpoints
from twisted.application import service, internet
from .database import get_db
from .transit_server import Transit

SECONDS = 1.0
MINUTE = 60*SECONDS

EXPIRATION_CHECK_PERIOD = 10*MINUTE

class RelayServer(service.MultiService):

    def __init__(self, transit_port,
                 db_url=":memory:", blur_usage=None,
                 stats_file=None):
        service.MultiService.__init__(self)
        self._blur_usage = blur_usage
        self._db_url = db_url

        db = get_db(db_url)

        transit = Transit(db, blur_usage)
        transit.setServiceParent(self) # for the timer
        t = endpoints.serverFromString(reactor, transit_port)
        transit_service = internet.StreamServerEndpointService(t, transit)
        transit_service.setServiceParent(self)

        self._stats_file = stats_file
        if self._stats_file and os.path.exists(self._stats_file):
            os.unlink(self._stats_file)
            # this will be regenerated immediately, but if something goes
            # wrong in dump_stats(), it's better to have a missing file than
            # a stale one

        # make some things accessible for tests
        self._db = db
        self._transit = transit
        self._transit_service = transit_service

    def startService(self):
        service.MultiService.startService(self)
        log.msg("Wormhole Transit Server running")
        if self._blur_usage:
            log.msg("blurring access times to %d seconds" % self._blur_usage)
            log.msg("not logging Transit connections")
        else:
            log.msg("not blurring access times")

    def timer(self):
        now = time.time()
        self.dump_stats(now, validity=EXPIRATION_CHECK_PERIOD+60)

    def dump_stats(self, now, validity):
        if not self._stats_file:
            return
        tmpfn = self._stats_file + ".tmp"

        data = {}
        data["created"] = now
        data["valid_until"] = now + validity

        start = time.time()
        data["transit"] = self._transit.get_stats()
        log.msg("get_stats took:", time.time() - start)

        with open(tmpfn, "wb") as f:
            # json.dump(f) has str-vs-unicode issues on py2-vs-py3
            f.write(json.dumps(data, indent=1).encode("utf-8"))
            f.write(b"\n")
        os.rename(tmpfn, self._stats_file)
