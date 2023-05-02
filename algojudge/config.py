from algojudge.sandbox import SandboxConfig


# A tuple (host, port) specifying the address which the site is hosted on.
SERVER_ADDRESS = ('127.0.0.1', 1337)

# Access token provided by the server to authenticate the judge (keep secret!).
# Generate a random key with `secrets.token_urlsafe()`.
JUDGE_ACCESS_TOKEN = '*******************************************'

# The root folder where the sandbox files reside.
BOX_ROOT = '/var/local/lib/algojudge/sandbox'

# The root folder where all problem data are held.
PROBLEM_DATA_ROOT = '/var/local/lib/algojudge/testdata'

# The default Sandbox configuration for judging submissions in the compilation step.
SANDBOX_COMPILE_CONFIG = SandboxConfig(
    cpu_time_limit=5000,   # 5 seconds
    real_time_limit=5000,  # 5 seconds
    memory_limit=1048576,  # 1 GiB
    max_fsize=64,          # 64 KiB
    max_pids=1024
)

# Load local config from `local_config.py`
try:
    from algojudge.local_config import *
except ModuleNotFoundError:
    pass
