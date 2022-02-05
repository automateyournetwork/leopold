import requests
import json

# -------------------------
# Jinja2
# -------------------------
from jinja2 import Environment, FileSystemLoader
template_dir = 'Templates/'
env = Environment(loader=FileSystemLoader(template_dir))

# -------------------------
# Headers
# -------------------------
headers = {
  'Accept': 'application/yang-data+json',
  'Content-Type': 'application/yang-data+json',
  'Authorization': 'Basic ZGV2ZWxvcGVyOlNlcnZpY2VzNEV2ZXI='
}

nso = "sandbox-nso-1.cisco.com"

# -------------------------
# Get All Device Groups
# -------------------------

deviceGroup = requests.request("GET", f"https://{ nso }/restconf/data/tailf-ncs:devices/device-group", headers=headers, verify=False)
deviceGroupJSON = deviceGroup.json()
deviceGroupTailF = deviceGroupJSON['tailf-ncs:device-group'][0]['device-group']

# -------------------------
# Get All Device Group Members
# -------------------------

device_group_member_template = env.get_template('device_group_members.j2')
device_template = env.get_template('device.j2')
for member in deviceGroupTailF:
    groupMember = requests.request("GET", f"https://{ nso }/restconf/data/tailf-ncs:devices/device-group={ member }", headers=headers, verify=False)
    groupMemberJSON = groupMember.json()
    groupMemberTailF = groupMemberJSON['tailf-ncs:device-group']

# -------------------------
# Pass to Jinja2 Template 
# -------------------------

    parsed_output = device_group_member_template.render(member = groupMemberTailF)

# # -------------------------
# # Save the markdown file
# # -------------------------

    with open(f"Leopold/{ member }/{ member.replace('-','_') }.md", "w") as fh:
        fh.write(parsed_output)               
        fh.close()
    print("saved group file")

# -------------------------
# Single Device
# -------------------------

    for single in groupMemberTailF[0]['member']:
        singleDevice = requests.request("GET", f"https://{ nso }/restconf/data/tailf-ncs:devices/device={ single }", headers=headers, verify=False)
        print(single)
        singleDeviceJSON = singleDevice.json()
        singleDeviceTailF = singleDeviceJSON['tailf-ncs:device']

# -------------------------
# Pass to Jinja2 Template 
# -------------------------

        parsed_output = device_template.render(device = singleDeviceTailF)

# -------------------------
# Save the markdown file
# -------------------------

        with open(f"Leopold/{ member }/{ singleDeviceTailF[0]['name'].replace('-','_') }.md", "w") as fh:
            fh.write(parsed_output)               
            fh.close()
            print("saved single file")            