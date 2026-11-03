"""Regression tests for bugs fixed in the modernisation pass."""
import datetime
import json

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.x509.oid import NameOID

from dahua import DahuaFunctions, x509_name
from net import Network


# --- method_banned: a missing comma used to merge two entries into "magicBox.configglobal.login" ---

def test_global_login_is_banned():
    assert DahuaFunctions.method_banned("global.login") is True


def test_magicbox_config_is_banned():
    assert DahuaFunctions.method_banned("magicBox.config") is True


def test_merged_string_is_not_banned():
    assert DahuaFunctions.method_banned("magicBox.configglobal.login") is False


def test_normal_method_not_banned():
    assert DahuaFunctions.method_banned("magicBox.getSerialNo") is False


# --- client_notify: used to drop every message after the first in a batched packet ---

class _FakeNetwork:
    udp_server = False
    rhost = "192.0.2.1"

    def __init__(self):
        self.console = []
        self.discovered = []

    def console_result(self, msg, callback=False):
        self.console.append(msg)

    def device_discovery(self, msg, callback=False):
        self.discovered.append(msg)


def test_client_notify_handles_every_batched_message():
    fake = _FakeNetwork()
    packet = "\n".join([
        json.dumps({"method": "client.notifyConsoleResult", "params": {"info": ["one"]}}),
        json.dumps({"method": "client.notifyConsoleAsyncResult", "params": {"info": ["two"]}}),
        json.dumps({"method": "client.notifyDeviceInfo", "params": {"deviceInfo": []}}),
    ])
    assert Network.client_notify(fake, packet) is True
    assert [m["params"]["info"][0] for m in fake.console] == ["one", "two"]
    assert len(fake.discovered) == 1


def test_client_notify_skips_malformed_lines_and_bytes_input():
    fake = _FakeNetwork()
    packet = b'garbage{\n' + json.dumps({"method": "client.notifyConsoleResult"}).encode() + b"\n\n"
    assert Network.client_notify(fake, packet) is True
    assert len(fake.console) == 1


# --- certificate handling moved from pyOpenSSL to cryptography ---

def _self_signed(key):
    name = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Dahua"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Root"),
    ])
    now = datetime.datetime.now(datetime.timezone.utc)
    return (
        x509.CertificateBuilder()
        .subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(1).not_valid_before(now).not_valid_after(now + datetime.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )


def test_x509_name_matches_openssl_oneline_format():
    cert = _self_signed(rsa.generate_private_key(public_exponent=65537, key_size=2048))
    assert x509_name(cert.subject) == "/C=CN/O=Dahua/CN=Root"


def test_ec_certificate_parses():
    """Newer firmware may ship EC certificates, which have no RSA modulus to print."""
    cert = _self_signed(ec.generate_private_key(ec.SECP256R1()))
    pem = cert.public_bytes(serialization.Encoding.PEM)
    loaded = x509.load_pem_x509_certificate(pem)
    assert not isinstance(loaded.public_key(), rsa.RSAPublicKey)
