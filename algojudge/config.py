from algojudge.sandbox import SandboxConfig


# A tuple (host, port) specifying the address which the site is hosted on.
SERVER_ADDRESS = ('127.0.0.1', 1337)

# Access token provided by the server to authenticate the judge (keep secret!)
JUDGE_ACCESS_TOKEN = 'gStYfO3MOFRpLvM3XuZvbYKEgtRojgdEUCXQgOCTC98'

# The root folder where all problem data is held.
PROBLEM_DATA_ROOT = '/var/local/lib/algojudge/testdata'

# The default Sandbox configuration for judging submissions in the compilation step.
SANDBOX_COMPILE_CONFIG = SandboxConfig(
    cpu_time_limit=5000,  # 5 seconds
    real_time_limit=5000,  # 5 seconds
    memory_limit=1048576,  # 1 GiB
    max_fsize=64,  # 64 KiB
    max_pids=1024
)
