from __future__ import print_function, unicode_literals
import mock
import click.testing
from twisted.trial import unittest
from ..cmd_server import MyPlugin
from ..cli import server

class FakeConfig(object):
    no_daemon = True
    blur_usage = True
    advertise_version = u"fake.version.1"
    transit = str('tcp:4321')
    rendezvous = str('tcp:1234')
    signal_error = True
    allow_list = False
    relay_database_path = "relay.sqlite"
    stats_json_path = "stats.json"


class Server(unittest.TestCase):

    def setUp(self):
        self.runner = click.testing.CliRunner()

    @mock.patch('wormhole.server.cmd_server.twistd')
    def test_server_disallow_list(self, fake_twistd):
        result = self.runner.invoke(server, ['start', '--no-daemon', '--disallow-list'])
        self.assertEqual(0, result.exit_code)

    def test_server_plugin(self):
        cfg = FakeConfig()
        plugin = MyPlugin(cfg)
        relay = plugin.makeService(None)
        self.assertEqual(False, relay._allow_list)

    @mock.patch("wormhole.server.cmd_server.start_server")
    def test_start_no_args(self, fake_start_server):
        result = self.runner.invoke(server, ['start'])
        self.assertEqual(0, result.exit_code)
        cfg = fake_start_server.mock_calls[0][1][0]
        MyPlugin(cfg).makeService(None)

    @mock.patch("wormhole.server.cmd_server.restart_server")
    def test_restart_no_args(self, fake_start_reserver):
        result = self.runner.invoke(server, ['restart'])
        self.assertEqual(0, result.exit_code)
        cfg = fake_start_reserver.mock_calls[0][1][0]
        MyPlugin(cfg).makeService(None)

    def test_state_locations(self):
        cfg = FakeConfig()
        plugin = MyPlugin(cfg)
        relay = plugin.makeService(None)
        self.assertEqual('relay.sqlite', relay._db_url)
        self.assertEqual('stats.json', relay._stats_file)
