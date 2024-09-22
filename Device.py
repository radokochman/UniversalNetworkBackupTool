import os

import netmiko

try:
    from netmiko import ConnectHandler
    from netmiko.ssh_dispatcher import CLASS_MAPPER_BASE
except Exception:
    print('Error during import of netmiko library. Please make sure it\'s present on your workstation.')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class Device:
    hostname = ''
    IP = ''
    device_type = ''
    backup_command = ''
    username = ''
    password = ''
    secret = ''
    port = ''

    def __init__(self, info, credentials, port):
        self.hostname = info['Hostname']
        self.IP = info['IP']

        if not info['Device type'] in list(CLASS_MAPPER_BASE.keys()):
            raise ValueError('Error: Device\'s {hostname} type {device_type} not recognised, skipping...\n'
                             'Supported network device types: {device_types}.'
                             ''.format(hostname = info['Hostname'],device_type=info['Device type'],device_types=list(CLASS_MAPPER_BASE.keys())))

        self.device_type = info['Device type']
        self.backup_command = info['Backup command']

        self.username = credentials['username']
        self.password = credentials['password']
        self.secret = credentials['secret']

        self._netmiko_data = {
            'device_type': self.device_type,
            'host': self.IP,
            'username': self.username,
            'password': self.password,
            'port': port,
            'secret': self.secret
        }

        print('{hostname} loaded successfully'.format(hostname = self.hostname))

    def get_config(self):
        net_connect = ConnectHandler(**self._netmiko_data)
        if net_connect.check_enable_mode() is False:
            net_connect.enable()
        output = net_connect.send_command_expect(self.backup_command)
        net_connect.disconnect()
        return output


