import os
import json
import aiohttp
import asyncio
import aiofiles
import rich_click as click
import yaml
import urllib3
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

urllib3.disable_warnings()

class Leopold():
    def __init__(self,
                url,
                username,
                password):
        self.nso = url
        self.username = username
        self.password = password

    def leopold(self):
        self.make_directories()
        asyncio.run(self.main())

    def make_directories(self):
        folder_list = ["Device Groups",
                       "Devices",
                       "Devices Config Cisco IOS Call Home",
                       "Devices Config Cisco IOS Crypto PKI",
                       "Devices Config Cisco IOS Diagnostic",
                       "Devices Config Cisco IOS Enable Password",
                       "Devices Config Cisco IOS Hostname",
                       "Devices Config Cisco IOS Interface",
                       "Devices Config Cisco IOS IP",
                       "Devices Config Cisco IOS Line",
                       "Devices Config Cisco IOS Logging",                       
                       "Devices Config Cisco IOS Login",
                       "Devices Config YANG Modules State",
                       "Devices Config YANG Library",                      
                       "Devices Live Status YANG Modules State",
                       "Devices Live Status YANG Library",
        ]
        current_directory = os.getcwd()
        for folder in folder_list:
            final_directory = os.path.join(current_directory, rf'{ folder }/JSON')
            os.makedirs(final_directory, exist_ok=True)
            final_directory = os.path.join(current_directory, rf'{ folder }/YAML')
            os.makedirs(final_directory, exist_ok=True)
            final_directory = os.path.join(current_directory, rf'{ folder }/CSV')
            os.makedirs(final_directory, exist_ok=True)
            final_directory = os.path.join(current_directory, rf'{ folder }/HTML')
            os.makedirs(final_directory, exist_ok=True)
            final_directory = os.path.join(current_directory, rf'{ folder }/Markdown')
            os.makedirs(final_directory, exist_ok=True)
            final_directory = os.path.join(current_directory, rf'{ folder }/Mindmap')
            os.makedirs(final_directory, exist_ok=True)

    def nso_api_list(self):
        self.list = ["/restconf/data/tailf-ncs:devices/device",
                     "/restconf/data/tailf-ncs:devices/device-group",
    ]
        return self.list

    async def get_api(self, api_url):
        headers = {
            'Accept': 'application/yang-data+json',
            'Content-Type': 'application/yang-data+json'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.nso}{api_url}",headers=headers, auth=aiohttp.BasicAuth(self.username, self.password), verify_ssl=False) as resp:
                self.api_count += 1
                if api_url == "/restconf/data/tailf-ncs:devices/device":
                    raw_text = await resp.text()
                    formatted_text = raw_text + "}]}"
                    response_dict = json.loads(formatted_text)
                else:
                    response_dict = await resp.json()
                print(f"{api_url} Status Code {resp.status}")
                return (api_url,response_dict)

    async def main(self):
        self.api_count = 0
        api_list = self.nso_api_list()
        results = await asyncio.gather(*(self.get_api(api_url) for api_url in api_list))
        await self.all_files(json.dumps(results, indent=4, sort_keys=True))
        print(f"Leopold gathered data from { self.api_count } Cisco Network Services Orchestrator APIs")

    async def json_file(self, parsed_json):
        for api, payload in json.loads(parsed_json):
            if api == "/restconf/data/tailf-ncs:devices/device":
                async with aiofiles.open('Devices/JSON/Devices.json', mode='w') as f:
                    await f.write(json.dumps(payload, indent=4, sort_keys=True))

                config_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_module_state.append(device_name | device['config']['ietf-yang-library:modules-state'])
                async with aiofiles.open('Devices Config YANG Modules State/JSON/Devices Config YANG Modules State.json', mode='w') as f:
                    await f.write(json.dumps(config_yang_module_state, indent=4, sort_keys=True))

                config_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_library_datastore.append(device_name | device['config']['ietf-yang-library:yang-library'])
                async with aiofiles.open('Devices Config YANG Library/JSON/Devices Config YANG Library.json', mode='w') as f:
                    await f.write(json.dumps(config_yang_library_datastore, indent=4, sort_keys=True))

                live_status_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:
                        device_name = {"device_name": device['name']}
                        live_status_yang_module_state.append(device_name | device['live-status']['ietf-yang-library:modules-state'])
                    async with aiofiles.open('Devices Live Status YANG Modules State/JSON/Devices Live Status YANG Modules State.json', mode='w') as f:
                        await f.write(json.dumps(live_status_yang_module_state, indent=4, sort_keys=True))

                live_status_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                    
                        device_name = {"device_name": device['name']}
                        live_status_yang_library_datastore.append(device_name | device['live-status']['ietf-yang-library:yang-library'])
                    async with aiofiles.open('Devices Live Status YANG Library/JSON/Devices Live Status YANG Library.json', mode='w') as f:
                        await f.write(json.dumps(live_status_yang_library_datastore, indent=4, sort_keys=True))

                cisco_ios_call_home = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:call-home' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_call_home.append(device_name | device['config']['tailf-ned-cisco-ios:call-home'])
                async with aiofiles.open('Devices Config Cisco IOS Call Home/JSON/Devices Config Cisco IOS Call Home.json', mode='w') as f:
                    await f.write(json.dumps(cisco_ios_call_home, indent=4, sort_keys=True))

                cisco_ios_crypto = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:crypto' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_crypto.append(device_name | device['config']['tailf-ned-cisco-ios:crypto'])
                async with aiofiles.open('Devices Config Cisco IOS Crypto PKI/JSON/Devices Config Cisco IOS Crypto PKI.json', mode='w') as f:
                    await f.write(json.dumps(cisco_ios_crypto, indent=4, sort_keys=True))

                cisco_ios_diags = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:diagnostic' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_diags.append(device_name | device['config']['tailf-ned-cisco-ios:diagnostic'])
                async with aiofiles.open('Devices Config Cisco IOS Diagnostic/JSON/Devices Config Cisco IOS Diagnostic.json', mode='w') as f:
                    await f.write(json.dumps(cisco_ios_diags, indent=4, sort_keys=True))
    
                cisco_ios_enable = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:enable' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_enable.append(device_name | device['config']['tailf-ned-cisco-ios:enable'])
                async with aiofiles.open('Devices Config Cisco IOS Enable Password/JSON/Devices Config Cisco IOS Enable Password.json', mode='w') as f:
                    await f.write(json.dumps(cisco_ios_enable, indent=4, sort_keys=True))
    
                cisco_ios_hostname = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:hostname' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_hostname.append(device['config']['tailf-ned-cisco-ios:hostname'])
                async with aiofiles.open('Devices Config Cisco IOS Hostname/JSON/Devices Config Cisco IOS Hostname.json', mode='w') as f:
                    await f.write(json.dumps(cisco_ios_hostname, indent=4, sort_keys=True))
    
                cisco_ios_interface = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:interface' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_interface.append(device_name | device['config']['tailf-ned-cisco-ios:interface'])
                async with aiofiles.open('Devices Config Cisco IOS Interface/JSON/Devices Config Cisco IOS Interface.json', mode='w') as f:
                    await f.write(json.dumps(cisco_ios_interface, indent=4, sort_keys=True))

                cisco_ios_ip = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:ip' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_ip.append(device_name | device['config']['tailf-ned-cisco-ios:ip'])
                async with aiofiles.open('Devices Config Cisco IOS IP/JSON/Devices Config Cisco IOS IP.json', mode='w') as f:
                    await f.write(json.dumps(cisco_ios_ip, indent=4, sort_keys=True))

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                async with aiofiles.open('Devices Config Cisco IOS Line/JSON/Devices Config Cisco IOS Line.json', mode='w') as f:
                    await f.write(json.dumps(cisco_ios_line, indent=4, sort_keys=True))

                cisco_ios_logging = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:logging' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_logging.append(device_name | device['config']['tailf-ned-cisco-ios:logging'])
                async with aiofiles.open('Devices Config Cisco IOS Logging/JSON/Devices Config Cisco IOS Logging.json', mode='w') as f:
                    await f.write(json.dumps(cisco_ios_logging, indent=4, sort_keys=True))

                cisco_ios_login = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:login' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_login.append(device_name | device['config']['tailf-ned-cisco-ios:login'])
                async with aiofiles.open('Devices Config Cisco IOS Login/JSON/Devices Config Cisco IOS Login.json', mode='w') as f:
                    await f.write(json.dumps(cisco_ios_login, indent=4, sort_keys=True))

            if api == "/restconf/data/tailf-ncs:devices/device-group":
                async with aiofiles.open('Device Groups/JSON/Device Groups.json', mode='w') as f:
                    await f.write(json.dumps(payload, indent=4, sort_keys=True))

    async def yaml_file(self, parsed_json):
        for api, payload in json.loads(parsed_json):
            clean_yaml = yaml.dump(payload, default_flow_style=False)
            if api == "/restconf/data/tailf-ncs:devices/device":
                async with aiofiles.open('Devices/YAML/Devices.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                config_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_module_state.append(device_name | device['config']['ietf-yang-library:modules-state'])
                clean_yaml = yaml.dump(config_yang_module_state, default_flow_style=False)                    
                async with aiofiles.open('Devices Config YANG Modules State/YAML/Devices Config YANG Modules State.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                config_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_library_datastore.append(device_name | device['config']['ietf-yang-library:yang-library'])
                clean_yaml = yaml.dump(config_yang_library_datastore, default_flow_style=False)                     
                async with aiofiles.open('Devices Config YANG Library/YAML/Devices Config YANG Library.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                live_status_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                    
                        device_name = {"device_name": device['name']}
                        live_status_yang_module_state.append(device_name | device['live-status']['ietf-yang-library:modules-state'])
                    clean_yaml = yaml.dump(live_status_yang_module_state, default_flow_style=False)                    
                    async with aiofiles.open('Devices Live Status YANG Modules State/YAML/Devices Live Status YANG Modules State.yaml', mode='w') as f:
                        await f.write(clean_yaml)

                live_status_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                        
                        device_name = {"device_name": device['name']}
                        live_status_yang_library_datastore.append(device_name | device['live-status']['ietf-yang-library:yang-library'])
                    clean_yaml = yaml.dump(live_status_yang_library_datastore, default_flow_style=False)                     
                    async with aiofiles.open('Devices Live Status YANG Library/YAML/Devices Live Status YANG Library.yaml', mode='w') as f:
                        await f.write(clean_yaml)

                cisco_ios_call_home = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:call-home' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_call_home.append(device_name | device['config']['tailf-ned-cisco-ios:call-home'])
                clean_yaml = yaml.dump(cisco_ios_call_home, default_flow_style=False)
                async with aiofiles.open('Devices Config Cisco IOS Call Home/YAML/Devices Config Cisco IOS Call Home.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                cisco_ios_crypto = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:crypto' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_crypto.append(device_name | device['config']['tailf-ned-cisco-ios:crypto'])
                clean_yaml = yaml.dump(cisco_ios_crypto, default_flow_style=False)                        
                async with aiofiles.open('Devices Config Cisco IOS Crypto PKI/YAML/Devices Config Cisco IOS Crypto PKI.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                cisco_ios_diags = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:diagnostic' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_diags.append(device_name | device['config']['tailf-ned-cisco-ios:diagnostic'])
                clean_yaml = yaml.dump(cisco_ios_diags, default_flow_style=False)                        
                async with aiofiles.open('Devices Config Cisco IOS Diagnostic/YAML/Devices Config Cisco IOS Diagnostic.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                cisco_ios_enable = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:enable' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_enable.append(device_name | device['config']['tailf-ned-cisco-ios:enable'])
                clean_yaml = yaml.dump(cisco_ios_enable, default_flow_style=False)                        
                async with aiofiles.open('Devices Config Cisco IOS Enable Password/YAML/Devices Config Cisco IOS Enable Password.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                cisco_ios_hostname = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:hostname' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_hostname.append(device['config']['tailf-ned-cisco-ios:hostname'])
                clean_yaml = yaml.dump(cisco_ios_hostname, default_flow_style=False)                        
                async with aiofiles.open('Devices Config Cisco IOS Hostname/YAML/Devices Config Cisco IOS Hostname.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                cisco_ios_interface = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:interface' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_interface.append(device_name | device['config']['tailf-ned-cisco-ios:interface'])
                clean_yaml = yaml.dump(cisco_ios_interface, default_flow_style=False)                        
                async with aiofiles.open('Devices Config Cisco IOS Interface/YAML/Devices Config Cisco IOS Interface.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                cisco_ios_ip = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:ip' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_ip.append(device_name | device['config']['tailf-ned-cisco-ios:ip'])
                clean_yaml = yaml.dump(cisco_ios_ip, default_flow_style=False)                        
                async with aiofiles.open('Devices Config Cisco IOS IP/YAML/Devices Config Cisco IOS IP.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                clean_yaml = yaml.dump(cisco_ios_line, default_flow_style=False)                        
                async with aiofiles.open('Devices Config Cisco IOS Line/YAML/Devices Config Cisco IOS Line.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                cisco_ios_logging = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:logging' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_logging.append(device_name | device['config']['tailf-ned-cisco-ios:logging'])
                clean_yaml = yaml.dump(cisco_ios_logging, default_flow_style=False)                        
                async with aiofiles.open('Devices Config Cisco IOS Logging/YAML/Devices Config Cisco IOS Logging.yaml', mode='w') as f:
                    await f.write(clean_yaml)

                cisco_ios_login = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:login' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_login.append(device_name | device['config']['tailf-ned-cisco-ios:login'])
                clean_yaml = yaml.dump(cisco_ios_login, default_flow_style=False)                        
                async with aiofiles.open('Devices Config Cisco IOS Login/YAML/Devices Config Cisco IOS Login.yaml', mode='w') as f:
                    await f.write(clean_yaml)

            if api == "/restconf/data/tailf-ncs:devices/device-group":
                async with aiofiles.open('Device Groups/YAML/Device Groups.yaml', mode='w') as f:
                    await f.write(clean_yaml)

    async def csv_file(self, parsed_json):
        template_dir = Path(__file__).resolve().parent
        env = Environment(loader=FileSystemLoader(str(template_dir)), enable_async=True)
        csv_template = env.get_template('nso_csv.j2')
        for api, payload in json.loads(parsed_json):        
            csv_output = await csv_template.render_async(api = api,
                                         data_to_template = payload)
            if api == "/restconf/data/tailf-ncs:devices/device":
                async with aiofiles.open('Devices/CSV/Devices.csv', mode='w') as f:
                    await f.write(csv_output)

                csv_output = await csv_template.render_async(api = "device_capability",
                                         data_to_template = payload)            
                async with aiofiles.open('Devices/CSV/Devices Capabilities.csv', mode='w') as f:
                    await f.write(csv_output)

                csv_output = await csv_template.render_async(api = "device_module",
                                         data_to_template = payload)            
                async with aiofiles.open('Devices/CSV/Devices Modules.csv', mode='w') as f:
                    await f.write(csv_output)

                config_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_module_state.append(device_name | device['config']['ietf-yang-library:modules-state'])
                csv_output = await csv_template.render_async(api = 'config_yang_module_state',
                                             data_to_template = config_yang_module_state)
                async with aiofiles.open('Devices Config YANG Modules State/CSV/Devices Config YANG Modules State.csv', mode='w') as f:
                    await f.write(csv_output)   

                config_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_library_datastore.append(device_name | device['config']['ietf-yang-library:yang-library'])
                csv_output = await csv_template.render_async(api = 'config_yang_Library_datastore',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/CSV/Devices Config YANG Library Data Store.csv', mode='w') as f:
                    await f.write(csv_output)

                csv_output = await csv_template.render_async(api = 'config_yang_Library_module_set_import_only',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/CSV/Devices Config YANG Library Module Set Import Only Modules.csv', mode='w') as f:
                    await f.write(csv_output)

                csv_output = await csv_template.render_async(api = 'config_yang_Library_module_set_module',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/CSV/Devices Config YANG Library Module Set Modules.csv', mode='w') as f:
                    await f.write(csv_output)

                csv_output = await csv_template.render_async(api = 'config_yang_Library_schema',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/CSV/Devices Config YANG Library Schema.csv', mode='w') as f:
                    await f.write(csv_output)

                live_status_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                    
                        device_name = {"device_name": device['name']}
                        live_status_yang_module_state.append(device_name | device['live-status']['ietf-yang-library:modules-state'])
                    csv_output = await csv_template.render_async(api = 'live_status_yang_module_state',
                                                 data_to_template = live_status_yang_module_state)
                    async with aiofiles.open('Devices Live Status YANG Modules State/CSV/Devices Live Status YANG Modules State.csv', mode='w') as f:
                        await f.write(csv_output)   

                live_status_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                    
                        device_name = {"device_name": device['name']}
                        live_status_yang_library_datastore.append(device_name | device['live-status']['ietf-yang-library:yang-library'])
                    csv_output = await csv_template.render_async(api = 'live_status_yang_library_datastore',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/CSV/Devices Live Status YANG Library Data Store.csv', mode='w') as f:
                        await f.write(csv_output)

                    csv_output = await csv_template.render_async(api = 'live_status_yang_library_module_set_import_only',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/CSV/Devices Live Status YANG Library Module Set Import Only Modules.csv', mode='w') as f:
                        await f.write(csv_output)

                    csv_output = await csv_template.render_async(api = 'live_status_yang_library_module_set_module',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/CSV/Devices Live Status YANG Library Module Set Modules.csv', mode='w') as f:
                        await f.write(csv_output)

                    csv_output = await csv_template.render_async(api = 'live_status_yang_library_schema',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/CSV/Devices Live Status YANG Library Schema.csv', mode='w') as f:
                        await f.write(csv_output)

                cisco_ios_call_home = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:call-home' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_call_home.append(device_name | device['config']['tailf-ned-cisco-ios:call-home'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_call_home',
                                            data_to_template = cisco_ios_call_home)                         
                async with aiofiles.open('Devices Config Cisco IOS Call Home/CSV/Devices Config Cisco IOS Call Home.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_crypto = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:crypto' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_crypto.append(device_name | device['config']['tailf-ned-cisco-ios:crypto'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_crypto_pki_certificates',
                                            data_to_template = cisco_ios_crypto)                       
                async with aiofiles.open('Devices Config Cisco IOS Crypto PKI/CSV/Devices Config Cisco IOS Crypto PKI Certificates.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_crypto = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:crypto' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_crypto.append(device_name | device['config']['tailf-ned-cisco-ios:crypto'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_crypto_pki_trust_points',
                                            data_to_template = cisco_ios_crypto)                       
                async with aiofiles.open('Devices Config Cisco IOS Crypto PKI/CSV/Devices Config Cisco IOS Crypto PKI Trust Points.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_diags = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:diagnostic' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_diags.append(device_name | device['config']['tailf-ned-cisco-ios:diagnostic'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_diagnostic',
                                            data_to_template = cisco_ios_diags)                       
                async with aiofiles.open('Devices Config Cisco IOS Diagnostic/CSV/Devices Config Cisco IOS Diagnostic.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_enable = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:enable' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_enable.append(device_name | device['config']['tailf-ned-cisco-ios:enable'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_enable_password',
                                            data_to_template = cisco_ios_enable)                       
                async with aiofiles.open('Devices Config Cisco IOS Enable Password/CSV/Devices Config Cisco IOS Enable Password.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_hostname = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:hostname' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_hostname.append(device['config']['tailf-ned-cisco-ios:hostname'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_hostname',
                                            data_to_template = cisco_ios_hostname)                       
                async with aiofiles.open('Devices Config Cisco IOS Hostname/CSV/Devices Config Cisco IOS Hostname.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_interface = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:interface' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_interface.append(device_name | device['config']['tailf-ned-cisco-ios:interface'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_interface',
                                            data_to_template = cisco_ios_interface)                       
                async with aiofiles.open('Devices Config Cisco IOS Interface/CSV/Devices Config Cisco IOS Interface.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_ip = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:ip' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_ip.append(device_name | device['config']['tailf-ned-cisco-ios:ip'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_ip',
                                            data_to_template = cisco_ios_ip)                       
                async with aiofiles.open('Devices Config Cisco IOS IP/CSV/Devices Config Cisco IOS IP.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_ip_route_vrf = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:ip' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_ip_route_vrf.append(device_name | device['config']['tailf-ned-cisco-ios:ip'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_ip_route_vrf',
                                            data_to_template = cisco_ios_ip_route_vrf)                       
                async with aiofiles.open('Devices Config Cisco IOS IP/CSV/Devices Config Cisco IOS IP Route VRF.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_line_console',
                                            data_to_template = cisco_ios_line)                       
                async with aiofiles.open('Devices Config Cisco IOS Line/CSV/Devices Config Cisco IOS Line Console.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_line_vty',
                                            data_to_template = cisco_ios_line)                       
                async with aiofiles.open('Devices Config Cisco IOS Line/CSV/Devices Config Cisco IOS Line VTY.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_logging = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:logging' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_logging.append(device_name | device['config']['tailf-ned-cisco-ios:logging'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_logging',
                                            data_to_template = cisco_ios_logging)                       
                async with aiofiles.open('Devices Config Cisco IOS Logging/CSV/Devices Config Cisco IOS Logging.csv', mode='w') as f:
                    await f.write(csv_output)

                cisco_ios_login = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:login' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_login.append(device_name | device['config']['tailf-ned-cisco-ios:login'])
                csv_output = await csv_template.render_async(api = 'cisco_ios_login',
                                            data_to_template = cisco_ios_login)                       
                async with aiofiles.open('Devices Config Cisco IOS Login/CSV/Devices Config Cisco IOS Login.csv', mode='w') as f:
                    await f.write(csv_output)

            if api == "/restconf/data/tailf-ncs:devices/device-group":
                async with aiofiles.open('Device Groups/CSV/Device Groups.csv', mode='w') as f:
                    await f.write(csv_output)                    

    async def markdown_file(self, parsed_json):
        template_dir = Path(__file__).resolve().parent
        env = Environment(loader=FileSystemLoader(str(template_dir)), enable_async=True)
        markdown_template = env.get_template('nso_markdown.j2')
        for api, payload in json.loads(parsed_json):        
            markdown_output = await markdown_template.render_async(api = api,
                                         data_to_template = payload)
            if api == "/restconf/data/tailf-ncs:devices/device":
                async with aiofiles.open('Devices/Markdown/Devices.md', mode='w') as f:
                    await f.write(markdown_output)

                markdown_output = await markdown_template.render_async(api = "device_capability",
                                         data_to_template = payload)            
                async with aiofiles.open('Devices/Markdown/Devices Capabilities.md', mode='w') as f:
                    await f.write(markdown_output)

                markdown_output = await markdown_template.render_async(api = "device_module",
                                         data_to_template = payload)            
                async with aiofiles.open('Devices/Markdown/Devices Modules.md', mode='w') as f:
                    await f.write(markdown_output)

                config_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_module_state.append(device_name | device['config']['ietf-yang-library:modules-state'])
                markdown_output = await markdown_template.render_async(api = 'config_yang_module_state',
                                             data_to_template = config_yang_module_state)
                async with aiofiles.open('Devices Config YANG Modules State/Markdown/Devices Config YANG Modules State.md', mode='w') as f:
                    await f.write(markdown_output)   

                config_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_library_datastore.append(device_name | device['config']['ietf-yang-library:yang-library'])
                markdown_output = await markdown_template.render_async(api = 'config_yang_library_datastore',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/Markdown/Devices Config YANG Library Data Store.md', mode='w') as f:
                    await f.write(markdown_output)

                markdown_output = await markdown_template.render_async(api = 'config_yang_library_module_set_import_only',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/Markdown/Devices Config YANG Library Module Set Import Only Modules.md', mode='w') as f:
                    await f.write(markdown_output)

                markdown_output = await markdown_template.render_async(api = 'config_yang_library_module_set_module',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/Markdown/Devices Config YANG Library Module Set Modules.md', mode='w') as f:
                    await f.write(markdown_output)

                markdown_output = await markdown_template.render_async(api = 'config_yang_library_schema',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/Markdown/Devices Config YANG Library Schema.md', mode='w') as f:
                    await f.write(markdown_output)

                live_status_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                    
                        device_name = {"device_name": device['name']}
                        live_status_yang_module_state.append(device_name | device['live-status']['ietf-yang-library:modules-state'])
                    markdown_output = await markdown_template.render_async(api = 'live_status_yang_module_state',
                                                 data_to_template = live_status_yang_module_state)
                    async with aiofiles.open('Devices Live Status YANG Modules State/Markdown/Devices Live Status YANG Modules State.md', mode='w') as f:
                        await f.write(markdown_output)   

                live_status_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                    
                        device_name = {"device_name": device['name']}
                        live_status_yang_library_datastore.append(device_name | device['live-status']['ietf-yang-library:yang-library'])
                    markdown_output = await markdown_template.render_async(api = 'live_status_yang_library_datastore',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/Markdown/Devices Live Status YANG Library Data Store.md', mode='w') as f:
                        await f.write(markdown_output)

                    markdown_output = await markdown_template.render_async(api = 'live_status_yang_library_module_set_import_only',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/Markdown/Devices Live Status YANG Library Module Set Import Only Modules.md', mode='w') as f:
                        await f.write(markdown_output)

                    markdown_output = await markdown_template.render_async(api = 'live_status_yang_library_module_set_module',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/Markdown/Devices Live Status YANG Library Module Set Modules.md', mode='w') as f:
                        await f.write(markdown_output)

                    markdown_output = await markdown_template.render_async(api = 'live_status_yang_library_schema',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/Markdown/Devices Live Status YANG Library Schema.md', mode='w') as f:
                        await f.write(markdown_output)

                cisco_ios_call_home = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:call-home' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_call_home.append(device_name | device['config']['tailf-ned-cisco-ios:call-home'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_call_home',
                                            data_to_template = cisco_ios_call_home)                         
                async with aiofiles.open('Devices Config Cisco IOS Call Home/Markdown/Devices Config Cisco IOS Call Home.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_crypto = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:crypto' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_crypto.append(device_name | device['config']['tailf-ned-cisco-ios:crypto'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_crypto_pki_certificates',
                                            data_to_template = cisco_ios_crypto)                       
                async with aiofiles.open('Devices Config Cisco IOS Crypto PKI/Markdown/Devices Config Cisco IOS Crypto PKI Certificates.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_crypto = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:crypto' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_crypto.append(device_name | device['config']['tailf-ned-cisco-ios:crypto'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_crypto_pki_trust_points',
                                            data_to_template = cisco_ios_crypto)                       
                async with aiofiles.open('Devices Config Cisco IOS Crypto PKI/Markdown/Devices Config Cisco IOS Crypto PKI Trust Points.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_diags = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:diagnostic' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_diags.append(device_name | device['config']['tailf-ned-cisco-ios:diagnostic'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_diagnostic',
                                            data_to_template = cisco_ios_diags)                       
                async with aiofiles.open('Devices Config Cisco IOS Diagnostic/Markdown/Devices Config Cisco IOS Diagnostic.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_enable = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:enable' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_enable.append(device_name | device['config']['tailf-ned-cisco-ios:enable'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_enable_password',
                                            data_to_template = cisco_ios_enable)                       
                async with aiofiles.open('Devices Config Cisco IOS Enable Password/Markdown/Devices Config Cisco IOS Enable Password.md', mode='w') as f:
                    await f.write(markdown_output)                    

                cisco_ios_hostname = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:hostname' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_hostname.append(device['config']['tailf-ned-cisco-ios:hostname'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_hostname',
                                            data_to_template = cisco_ios_hostname)                       
                async with aiofiles.open('Devices Config Cisco IOS Hostname/Markdown/Devices Config Cisco IOS Hostname.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_interface = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:interface' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_interface.append(device_name | device['config']['tailf-ned-cisco-ios:interface'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_interface',
                                            data_to_template = cisco_ios_interface)                       
                async with aiofiles.open('Devices Config Cisco IOS Interface/Markdown/Devices Config Cisco IOS Interface.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_ip = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:ip' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_ip.append(device_name | device['config']['tailf-ned-cisco-ios:ip'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_ip',
                                            data_to_template = cisco_ios_ip)                       
                async with aiofiles.open('Devices Config Cisco IOS IP/Markdown/Devices Config Cisco IOS IP.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_ip_route_vrf = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:ip' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_ip_route_vrf.append(device_name | device['config']['tailf-ned-cisco-ios:ip'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_ip_route_vrf',
                                            data_to_template = cisco_ios_ip_route_vrf)                       
                async with aiofiles.open('Devices Config Cisco IOS IP/Markdown/Devices Config Cisco IOS IP Route VRF.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_line_console',
                                            data_to_template = cisco_ios_line)                       
                async with aiofiles.open('Devices Config Cisco IOS Line/Markdown/Devices Config Cisco IOS Console.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_line_vty',
                                            data_to_template = cisco_ios_line)                       
                async with aiofiles.open('Devices Config Cisco IOS Line/Markdown/Devices Config Cisco IOS Line VTY.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_logging = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:logging' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_logging.append(device_name | device['config']['tailf-ned-cisco-ios:logging'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_logging',
                                            data_to_template = cisco_ios_logging)                       
                async with aiofiles.open('Devices Config Cisco IOS Logging/Markdown/Devices Config Cisco IOS Logging.md', mode='w') as f:
                    await f.write(markdown_output)

                cisco_ios_login = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:login' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_login.append(device_name | device['config']['tailf-ned-cisco-ios:login'])
                markdown_output = await markdown_template.render_async(api = 'cisco_ios_login',
                                            data_to_template = cisco_ios_login)                       
                async with aiofiles.open('Devices Config Cisco IOS Login/Markdown/Devices Config Cisco IOS Login.md', mode='w') as f:
                    await f.write(markdown_output)

            if api == "/restconf/data/tailf-ncs:devices/device-group":
                async with aiofiles.open('Device Groups/Markdown/Device Groups.md', mode='w') as f:
                    await f.write(markdown_output)

    async def html_file(self, parsed_json):
        template_dir = Path(__file__).resolve().parent
        env = Environment(loader=FileSystemLoader(str(template_dir)), enable_async=True)
        html_template = env.get_template('nso_html.j2')
        for api, payload in json.loads(parsed_json):
            html_output = await html_template.render_async(api = api,
                                             data_to_template = payload)
            if api == "/restconf/data/tailf-ncs:devices/device":
                async with aiofiles.open('Devices/HTML/Devices.html', mode='w') as f:
                    await f.write(html_output)

                html_output = await html_template.render_async(api = "device_capability",
                                         data_to_template = payload)            
                async with aiofiles.open('Devices/HTML/Devices Capabilities.html', mode='w') as f:
                    await f.write(html_output)

                html_output = await html_template.render_async(api = "device_module",
                                         data_to_template = payload)            
                async with aiofiles.open('Devices/HTML/Devices Modules.html', mode='w') as f:
                    await f.write(html_output)

                config_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_module_state.append(device_name | device['config']['ietf-yang-library:modules-state'])
                html_output = await html_template.render_async(api = 'config_yang_module_state',
                                             data_to_template = config_yang_module_state)
                async with aiofiles.open('Devices Config YANG Modules State/HTML/Devices Config YANG Modules State.html', mode='w') as f:
                    await f.write(html_output)

                config_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_library_datastore.append(device_name | device['config']['ietf-yang-library:yang-library'])
                html_output = await html_template.render_async(api = 'config_yang_library_datastore',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/HTML/Devices Config YANG Library Data Store.html', mode='w') as f:
                    await f.write(html_output)

                html_output = await html_template.render_async(api = 'config_yang_library_module_set_import_only',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/HTML/Devices Config YANG Library Module Set Import Only Modules.html', mode='w') as f:
                    await f.write(html_output)

                html_output = await html_template.render_async(api = 'config_yang_library_module_set_module',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/HTML/Devices Config YANG Library Module Set Modules.html', mode='w') as f:
                    await f.write(html_output)

                html_output = await html_template.render_async(api = 'config_yang_library_schema',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/HTML/Devices Config YANG Library Schema.html', mode='w') as f:
                    await f.write(html_output)

                live_status_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                    
                        device_name = {"device_name": device['name']}
                        live_status_yang_module_state.append(device_name | device['live-status']['ietf-yang-library:modules-state'])
                    html_output = await html_template.render_async(api = 'live_status_yang_module_state',
                                                 data_to_template = live_status_yang_module_state)
                    async with aiofiles.open('Devices Live Status YANG Modules State/HTML/Devices Live Status YANG Modules State.html', mode='w') as f:
                        await f.write(html_output)

                live_status_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                    
                        device_name = {"device_name": device['name']}
                        live_status_yang_library_datastore.append(device_name | device['live-status']['ietf-yang-library:yang-library'])
                    html_output = await html_template.render_async(api = 'live_status_yang_library_datastore',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/HTML/Devices Live Status YANG Library Data Store.html', mode='w') as f:
                        await f.write(html_output)

                    html_output = await html_template.render_async(api = 'live_status_yang_library_module_set_import_only',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/HTML/Devices Live Status YANG Library Module Set Import Only Modules.html', mode='w') as f:
                        await f.write(html_output)

                    html_output = await html_template.render_async(api = 'live_status_yang_library_module_set_module',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Config YANG Library/HTML/Devices Config YANG Library Module Set Modules.html', mode='w') as f:
                        await f.write(html_output)

                    html_output = await html_template.render_async(api = 'live_status_yang_library_schema',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/HTML/Devices Live Status YANG Library Schema.html', mode='w') as f:
                        await f.write(html_output)

                cisco_ios_call_home = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:call-home' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_call_home.append(device_name | device['config']['tailf-ned-cisco-ios:call-home'])
                html_output = await html_template.render_async(api = 'cisco_ios_call_home',
                                            data_to_template = cisco_ios_call_home)                         
                async with aiofiles.open('Devices Config Cisco IOS Call Home/HTML/Devices Config Cisco IOS Call Home.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_crypto = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:crypto' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_crypto.append(device_name | device['config']['tailf-ned-cisco-ios:crypto'])
                html_output = await html_template.render_async(api = 'cisco_ios_crypto_pki_certificates',
                                            data_to_template = cisco_ios_crypto)                       
                async with aiofiles.open('Devices Config Cisco IOS Crypto PKI/HTML/Devices Config Cisco IOS Crypto PKI Certificates.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_crypto = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:crypto' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_crypto.append(device_name | device['config']['tailf-ned-cisco-ios:crypto'])
                html_output = await html_template.render_async(api = 'cisco_ios_crypto_pki_trust_points',
                                            data_to_template = cisco_ios_crypto)                       
                async with aiofiles.open('Devices Config Cisco IOS Crypto PKI/HTML/Devices Config Cisco IOS Crypto PKI Trust Points.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_diags = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:diagnostic' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_diags.append(device_name | device['config']['tailf-ned-cisco-ios:diagnostic'])
                html_output = await html_template.render_async(api = 'cisco_ios_diagnostic',
                                            data_to_template = cisco_ios_diags)                       
                async with aiofiles.open('Devices Config Cisco IOS Diagnostic/HTML/Devices Config Cisco IOS Diagnostic.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_enable = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:enable' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_enable.append(device_name | device['config']['tailf-ned-cisco-ios:enable'])
                html_output = await html_template.render_async(api = 'cisco_ios_enable_password',
                                            data_to_template = cisco_ios_enable)                       
                async with aiofiles.open('Devices Config Cisco IOS Enable Password/HTML/Devices Config Cisco IOS Enable Password.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_hostname = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:hostname' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_hostname.append(device['config']['tailf-ned-cisco-ios:hostname'])
                html_output = await html_template.render_async(api = 'cisco_ios_hostname',
                                            data_to_template = cisco_ios_hostname)                       
                async with aiofiles.open('Devices Config Cisco IOS Hostname/HTML/Devices Config Cisco IOS Hostname.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_interface = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:interface' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_interface.append(device_name | device['config']['tailf-ned-cisco-ios:interface'])
                html_output = await html_template.render_async(api = 'cisco_ios_interface',
                                            data_to_template = cisco_ios_interface)                       
                async with aiofiles.open('Devices Config Cisco IOS Interface/HTML/Devices Config Cisco IOS Interface.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_ip = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:ip' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_ip.append(device_name | device['config']['tailf-ned-cisco-ios:ip'])
                html_output = await html_template.render_async(api = 'cisco_ios_ip',
                                            data_to_template = cisco_ios_ip)                       
                async with aiofiles.open('Devices Config Cisco IOS IP/HTML/Devices Config Cisco IOS IP.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_ip_route_vrf = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:ip' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_ip_route_vrf.append(device_name | device['config']['tailf-ned-cisco-ios:ip'])
                html_output = await html_template.render_async(api = 'cisco_ios_ip_route_vrf',
                                            data_to_template = cisco_ios_ip_route_vrf)                       
                async with aiofiles.open('Devices Config Cisco IOS IP/HTML/Devices Config Cisco IOS IP Route VRF.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                html_output = await html_template.render_async(api = 'cisco_ios_line_console',
                                            data_to_template = cisco_ios_line)                       
                async with aiofiles.open('Devices Config Cisco IOS Line/HTML/Devices Config Cisco IOS Line Console.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                html_output = await html_template.render_async(api = 'cisco_ios_line_vty',
                                            data_to_template = cisco_ios_line)                       
                async with aiofiles.open('Devices Config Cisco IOS Line/HTML/Devices Config Cisco IOS Line VTY.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_logging = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:logging' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_logging.append(device_name | device['config']['tailf-ned-cisco-ios:logging'])
                html_output = await html_template.render_async(api = 'cisco_ios_logging',
                                            data_to_template = cisco_ios_logging)                       
                async with aiofiles.open('Devices Config Cisco IOS Logging/HTML/Devices Config Cisco IOS Logging.html', mode='w') as f:
                    await f.write(html_output)

                cisco_ios_login = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:login' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_login.append(device_name | device['config']['tailf-ned-cisco-ios:login'])
                html_output = await html_template.render_async(api = 'cisco_ios_login',
                                            data_to_template = cisco_ios_login)                       
                async with aiofiles.open('Devices Config Cisco IOS Login/HTML/Devices Config Cisco IOS Login.html', mode='w') as f:
                    await f.write(html_output)

            if api == "/restconf/data/tailf-ncs:devices/device-group":
                async with aiofiles.open('Device Groups/HTML/Device Groups.html', mode='w') as f:
                    await f.write(html_output)                    

    async def mindmap_file(self, parsed_json):
        template_dir = Path(__file__).resolve().parent
        env = Environment(loader=FileSystemLoader(str(template_dir)), enable_async=True)
        mindmap_template = env.get_template('nso_mindmap.j2')
        for api, payload in json.loads(parsed_json):
            mindmap_output = await mindmap_template.render_async(api = api,
                                             data_to_template = payload)
            if api == "/restconf/data/tailf-ncs:devices/device":
                async with aiofiles.open('Devices/Mindmap/Devices.md', mode='w') as f:
                    await f.write(mindmap_output)

                mindmap_output = await mindmap_template.render_async(api = "device_capability",
                                         data_to_template = payload)            
                async with aiofiles.open('Devices/Mindmap/Devices Capabilities.md', mode='w') as f:
                    await f.write(mindmap_output)

                mindmap_output = await mindmap_template.render_async(api = "device_module",
                                         data_to_template = payload)            
                async with aiofiles.open('Devices/Mindmap/Devices Modules.md', mode='w') as f:
                    await f.write(mindmap_output)

                config_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_module_state.append(device_name | device['config']['ietf-yang-library:modules-state'])
                mindmap_output = await mindmap_template.render_async(api = 'config_yang_module_state',
                                             data_to_template = config_yang_module_state)
                async with aiofiles.open('Devices Config YANG Modules State/Mindmap/Devices Config YANG Modules State.md', mode='w') as f:
                    await f.write(mindmap_output)   

                config_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    device_name = {"device_name": device['name']}
                    config_yang_library_datastore.append(device_name | device['config']['ietf-yang-library:yang-library'])
                mindmap_output = await mindmap_template.render_async(api = 'config_yang_library_datastore',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/Mindmap/Devices Config YANG Library Data Store.md', mode='w') as f:
                    await f.write(mindmap_output)

                mindmap_output = await mindmap_template.render_async(api = 'config_yang_library_module_set_import_only',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/Mindmap/Devices Config YANG Library Module Set Import Only Modules.md', mode='w') as f:
                    await f.write(mindmap_output)

                mindmap_output = await mindmap_template.render_async(api = 'config_yang_library_module_set_module',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/Mindmap/Devices Config YANG Library Module Set Modules.md', mode='w') as f:
                    await f.write(mindmap_output)

                mindmap_output = await mindmap_template.render_async(api = 'config_yang_library_schema',
                                             data_to_template = config_yang_library_datastore)                    
                async with aiofiles.open('Devices Config YANG Library/Mindmap/Devices Config YANG Library Schema.md', mode='w') as f:
                    await f.write(mindmap_output)

                live_status_yang_module_state = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                    
                        device_name = {"device_name": device['name']}
                        live_status_yang_module_state.append(device_name | device['live-status']['ietf-yang-library:modules-state'])
                    mindmap_output = await mindmap_template.render_async(api = 'live_status_yang_module_state',
                                                 data_to_template = live_status_yang_module_state)
                    async with aiofiles.open('Devices Live Status YANG Modules State/Mindmap/Devices Live Status YANG Modules State.md', mode='w') as f:
                        await f.write(mindmap_output)   

                live_status_yang_library_datastore = []
                for device in payload['tailf-ncs:device']:
                    if "live-status" in device:                    
                        device_name = {"device_name": device['name']}
                        live_status_yang_library_datastore.append(device_name | device['live-status']['ietf-yang-library:yang-library'])
                    mindmap_output = await mindmap_template.render_async(api = 'live_status_yang_library_datastore',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/Mindmap/Devices Live Status YANG Library Data Store.md', mode='w') as f:
                        await f.write(mindmap_output)

                    mindmap_output = await mindmap_template.render_async(api = 'live_status_yang_library_module_set_import_only',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/Mindmap/Devices Live Status YANG Library Module Set Import Only Modules.md', mode='w') as f:
                        await f.write(mindmap_output)

                    mindmap_output = await mindmap_template.render_async(api = 'live_status_yang_library_module_set_module',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/Mindmap/Devices Live Status YANG Library Module Set Modules.md', mode='w') as f:
                        await f.write(mindmap_output)

                    mindmap_output = await mindmap_template.render_async(api = 'live_status_yang_library_schema',
                                                 data_to_template = live_status_yang_library_datastore)                    
                    async with aiofiles.open('Devices Live Status YANG Library/Mindmap/Devices Live Status YANG Library Schema.md', mode='w') as f:
                        await f.write(mindmap_output)

                cisco_ios_call_home = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:call-home' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_call_home.append(device_name | device['config']['tailf-ned-cisco-ios:call-home'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_call_home',
                                            data_to_template = cisco_ios_call_home)                         
                async with aiofiles.open('Devices Config Cisco IOS Call Home/Mindmap/Devices Config Cisco IOS Call Home.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_crypto = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:crypto' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_crypto.append(device_name | device['config']['tailf-ned-cisco-ios:crypto'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_crypto_pki_certificates',
                                            data_to_template = cisco_ios_crypto)                       
                async with aiofiles.open('Devices Config Cisco IOS Crypto PKI/Mindmap/Devices Config Cisco IOS Crypto PKI Certificates.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_crypto = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:crypto' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_crypto.append(device_name | device['config']['tailf-ned-cisco-ios:crypto'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_crypto_pki_trust_points',
                                            data_to_template = cisco_ios_crypto)                       
                async with aiofiles.open('Devices Config Cisco IOS Crypto PKI/Mindmap/Devices Config Cisco IOS Crypto PKI Trust Points.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_diags = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:diagnostic' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_diags.append(device_name | device['config']['tailf-ned-cisco-ios:diagnostic'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_diagnostic',
                                            data_to_template = cisco_ios_diags)                       
                async with aiofiles.open('Devices Config Cisco IOS Diagnostic/Mindmap/Devices Config Cisco IOS Diagnostic.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_enable = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:enable' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_enable.append(device_name | device['config']['tailf-ned-cisco-ios:enable'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_enable_password',
                                            data_to_template = cisco_ios_enable)                       
                async with aiofiles.open('Devices Config Cisco IOS Enable Password/Mindmap/Devices Config Cisco IOS Enable Password.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_hostname = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:hostname' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_hostname.append(device['config']['tailf-ned-cisco-ios:hostname'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_hostname',
                                            data_to_template = cisco_ios_hostname)                       
                async with aiofiles.open('Devices Config Cisco IOS Hostname/Mindmap/Devices Config Cisco IOS Hostname.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_interface = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:interface' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_interface.append(device_name | device['config']['tailf-ned-cisco-ios:interface'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_interface',
                                            data_to_template = cisco_ios_interface)                       
                async with aiofiles.open('Devices Config Cisco IOS Interface/Mindmap/Devices Config Cisco IOS Interface.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_ip = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:ip' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_ip.append(device_name | device['config']['tailf-ned-cisco-ios:ip'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_ip',
                                            data_to_template = cisco_ios_ip)                       
                async with aiofiles.open('Devices Config Cisco IOS IP/Mindmap/Devices Config Cisco IOS IP.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_ip_route_vrf = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:ip' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_ip_route_vrf.append(device_name | device['config']['tailf-ned-cisco-ios:ip'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_ip_route_vrf',
                                            data_to_template = cisco_ios_ip_route_vrf)                       
                async with aiofiles.open('Devices Config Cisco IOS IP/Mindmap/Devices Config Cisco IOS IP Route VRF.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_line_console',
                                            data_to_template = cisco_ios_line)                       
                async with aiofiles.open('Devices Config Cisco IOS Line/Mindmap/Devices Config Cisco IOS Line Console.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_line_vty',
                                            data_to_template = cisco_ios_line)                       
                async with aiofiles.open('Devices Config Cisco IOS Line/Mindmap/Devices Config Cisco IOS Line VTY.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_line = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:line' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_line.append(device_name | device['config']['tailf-ned-cisco-ios:line'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_line_vty',
                                            data_to_template = cisco_ios_line)                       
                async with aiofiles.open('Devices Config Cisco IOS Line/Mindmap/Devices Config Cisco IOS Line VTY.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_logging = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:logging' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_logging.append(device_name | device['config']['tailf-ned-cisco-ios:logging'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_logging',
                                            data_to_template = cisco_ios_logging)                       
                async with aiofiles.open('Devices Config Cisco IOS Logging/Mindmap/Devices Config Cisco IOS Logging.md', mode='w') as f:
                    await f.write(mindmap_output)

                cisco_ios_login = []
                for device in payload['tailf-ncs:device']:
                    if 'tailf-ned-cisco-ios:login' in device['config']:
                        device_name = {"device_name": device['name']}
                        cisco_ios_login.append(device_name | device['config']['tailf-ned-cisco-ios:login'])
                mindmap_output = await mindmap_template.render_async(api = 'cisco_ios_login',
                                            data_to_template = cisco_ios_login)                       
                async with aiofiles.open('Devices Config Cisco IOS Login/Mindmap/Devices Config Cisco IOS Login.md', mode='w') as f:
                    await f.write(mindmap_output)

            if api == "/restconf/data/tailf-ncs:devices/device-group":
                async with aiofiles.open('Device Groups/Mindmap/Device Groups.md', mode='w') as f:
                    await f.write(mindmap_output)

    async def all_files(self, parsed_json):
        await asyncio.gather(self.json_file(parsed_json), self.yaml_file(parsed_json), self.csv_file(parsed_json), self.markdown_file(parsed_json), self.html_file(parsed_json), self.mindmap_file(parsed_json))

@click.command()
@click.option('--url',
    prompt="NSO URL",
    help="NSO URL",
    required=True,envvar="URL")
@click.option('--username',
    prompt="NSO Username",
    help="NSO Username",
    required=True,envvar="USERNAME")
@click.option('--password',
    prompt="NSO Password",
    help="NSO Password",
    required=True, hide_input=True,envvar="PASSWORD")
def cli(url,username,password):
    invoke_class = Leopold(url,username,password)
    invoke_class.leopold()

if __name__ == "__main__":
    cli()
