"""Tests for the read-only 'rpc' console command."""
from types import SimpleNamespace

from dahua import DahuaFunctions


class _FakeDevice:
    def __init__(self, force=False, plain_reply=None, instance_reply=None, has_instance=True):
        self.args = SimpleNamespace(force=force)
        self.calls = []
        self.plain_reply = plain_reply
        self.instance_reply = instance_reply
        self.has_instance = has_instance
        self.stopped = []

    method_banned = staticmethod(DahuaFunctions.method_banned)

    def send_call(self, query_args, errorcodes=False):
        self.calls.append(query_args)
        return self.instance_reply if "object" in query_args else self.plain_reply

    def instance_service(self, service, start=False, pull=None, stop=False):
        if start:
            return self.has_instance
        if pull == "object":
            return 1234
        if stop:
            self.stopped.append(service)
        return True


def test_read_only_call_is_sent_with_params():
    dev = _FakeDevice(plain_reply={"result": True, "params": {"caps": 1}})
    assert DahuaFunctions.rpc(dev, 'rpc devVideoAnalyse.getCaps {"channel":0}') is True
    assert dev.calls == [{"method": "devVideoAnalyse.getCaps", "params": {"channel": 0}}]


def test_write_call_refused_without_force():
    dev = _FakeDevice(plain_reply={"result": True})
    assert DahuaFunctions.rpc(dev, "rpc magicBox.reboot") is False
    assert dev.calls == []


def test_write_call_allowed_with_force():
    dev = _FakeDevice(force=True, plain_reply={"result": True})
    assert DahuaFunctions.rpc(dev, 'rpc magicBox.setDeviceParam {"a":1}') is True
    assert len(dev.calls) == 1


def test_banned_method_refused_even_with_force():
    dev = _FakeDevice(force=True, plain_reply={"result": True})
    assert DahuaFunctions.rpc(dev, "rpc magicBox.resetSystem") is False
    assert dev.calls == []


def test_bad_json_params_refused():
    dev = _FakeDevice(plain_reply={"result": True})
    assert DahuaFunctions.rpc(dev, "rpc magicBox.getSystemInfo {not json") is False
    assert dev.calls == []


def test_retries_through_instance_when_plain_call_fails():
    dev = _FakeDevice(
        plain_reply={"result": False, "error": {"code": 268632064}},
        instance_reply={"result": True, "params": {"caps": "ok"}},
    )
    assert DahuaFunctions.rpc(dev, "rpc devVideoInput.getCapsEx") is True
    assert dev.calls[-1]["object"] == 1234
    assert dev.stopped == ["devVideoInput"]
