import os

# Stop pwntools trying to take over the terminal when modules are imported under pytest
os.environ.setdefault("PWNLIB_NOTERM", "1")
