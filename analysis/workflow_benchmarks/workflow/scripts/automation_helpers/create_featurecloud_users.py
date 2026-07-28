from pathlib import Path
import secrets
import string
import subprocess
from time import sleep



email = ''
user_range = range(1, 128 + 1)
base_local = email.split("@")[0]
domain = email.split("@")[1]

records: list[tuple[str, str, str]] = []

for index in user_range:
    email = f"{base_local}+{index:03d}@{domain}"
    password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
    site_name = f"site_{index:03d}"
    records.append((email, password, site_name))

credentials_lines = [f"{email}={password}" for email, password, _ in records]
assert not Path('.env').exists(), "there's already a .env file, won't overwrite"
Path('.env').write_text("\n".join(credentials_lines) + "\n")


for email, _, site_name in records:
    cmd = [
    "fcauto",
    "signup",
    "--email",
    email,
    "--first-name",
    "federated",
    "--last-name",
    "client",
    "--site-name",
    site_name,
    "--role",
    "user",
    ]
    print(' '.join(cmd))
    subprocess.run(cmd, check=True)
    sleep(1)
    

        
