import json
import sys

"""
Extracting the hostnames of biosphere VMs.
Go to the myVM overview, open devtools and copy the json response of the periodic API request.
Then run this command to generate a file of hostnames:

echo '<json>' | python workflow/scripts/automation_helpers/get_hostnames.py > workflow/config/hostnames.txt

"""

data = json.loads(sys.stdin.read())
order = data.pop("order", None)

hostnames = [k.get("main_hostname", None) for k in data.values()]

for hostname in hostnames:
    print(hostname)

