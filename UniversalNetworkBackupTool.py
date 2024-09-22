import os
import csv
import configparser
from datetime import datetime

import netmiko

from Device import Device

try:
    from netmiko.ssh_dispatcher import CLASS_MAPPER_BASE
except Exception:
    print('Error during import of netmiko library. Please make sure it\'s present on your workstation.')

NOW = datetime.now()
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INVENTORY_PATH = ROOT_DIR + '/inventory.csv'
CONFIG_PATH = ROOT_DIR + '/config.cfg'
TOOL_VERSION = '2.0'
LAST_UPDATE = '05.02.2022'


def print_supported_types():
    """
    Function that prints available OS types for this version of netmiko. Used for documentation purposes.
    """
    types = CLASS_MAPPER_BASE
    for os in types:
        print(os)


class UniversalNetworkBackupTool:
    _csv_columns = ['Hostname', 'IP', 'Device type', 'Backup command']
    _credentials = {
        'username': '',
        'password': '',
        'secret': ''
    }
    _port = ''
    _path = ''

    def __init__(self):
        banner = ['********************************************************************************\n',
                  'Thanks for using Universal Network Backup Tool by Radoslaw Kochman',
                  'Current version: {version}, last update: {last_update}\n'.format(version=TOOL_VERSION,
                                                                                    last_update=LAST_UPDATE),
                  'For more information about the tool, please visit https://garzum.net/\n',
                  'Latest version can be downloaded from git repository at',
                  'https://gitlab.com/garzum/universalnetworkbackuptool\n',

                  'Contributors:',
                  'Ali Farhani\n',
                  '********************************************************************************\n']

        for line in banner:
            print('{: ^80s}'.format(line))
        csv_dictionary = self._load_csv()
        self._load_config()
        inventory = self._build_inventory(csv_dictionary)

        if len(inventory) > 0:
            self._backup_configs(inventory)
        else:
            print('Inventory is empty.')

        self.quit(0)

    def _load_config(self):
        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read(CONFIG_PATH)
            self._credentials = {
                'username': config['Credentials']['username'],
                'password': config['Credentials']['password'],
                'secret': config['Credentials']['secret']
            }
            self._port = config['Connection']['port']

            if config['Path']['path']:
                self._path = config['Path']['path']
                if not os.path.isdir(self._path):
                    raise FileNotFoundError()

            if not self._credentials['username']:
                raise ValueError('username')
            elif not self._credentials['password']:
                raise ValueError('password')

            self._autoexit = config['Options']['autoexit']

            if self._autoexit == 'True':
                self._autoexit = True
            elif self._autoexit == 'False':
                self._autoexit = False
            else:
                print(f'Unrecognized value for autoexit: {self._autoexit}, assuming False')
                self._autoexit = False
            pass

        except ValueError as e:
            print('Error: {error} parameter is empty in the config.cfg file'.format(error=e))
            self.quit(1)
        except KeyError as e:
            print('Error: Cannot find {error} in the config.cfg file'.format(error=e))
            self.quit(1)
        except FileNotFoundError:
            print('Error: Cannot find directory path specified in the config.cfg file')
            self.quit(1)
        except Exception as e:
            print('Error: Cannot read config from the config.cfg file, {error}'.format(error=e))
            self.quit(1)

    def _load_csv(self):
        try:
            with open(INVENTORY_PATH, mode='r') as f:
                reader = csv.DictReader(f, delimiter=';')

                for column in self._csv_columns:
                    if column not in reader.fieldnames:
                        print('Error: Column {column} not found in the inventory.csv file, '
                              'please reefer to the example. Exiting.'.format(column=column))
                        self.quit(1)

                return list(reader)
        except FileNotFoundError:
            print('Error: inventory.csv file not found in project directory.')
            self.quit(1)

    def _build_inventory(self, csv_dictionary):
        inventory = []

        print('Loading inventory...')
        for row in csv_dictionary:
            try:
                inventory.append(Device(row, self._credentials, self._port))
            except KeyError:
                print('Error: read data from row {row}'.format(row=row))
            except ValueError as e:
                print(e)

        return inventory

    def _backup_configs(self, inventory):
        dt_string = NOW.strftime("%d-%m-%Y_%H-%M-%S")
        dir_name = 'task_{date_time}'.format(date_time=dt_string)

        if self._path:
            dir_path = self._path + '/{dir_name}'.format(dir_name=dir_name)
        else:
            dir_path = ROOT_DIR + '/{dir_name}'.format(dir_name=dir_name)

        print('\nConnecting to the devices...')
        for device in inventory:
            try:
                output = device.get_config()

                if not output:
                    print(
                        'Error: Empty output from {hostname}, IP: {IP}'.format(hostname=device.hostname, IP=device.IP))
                    continue
                else:
                    print('Successfully gathered command output from {hostname}, IP: {IP}'.format(
                        hostname=device.hostname, IP=device.IP))

                if not os.path.isdir(dir_path):
                    os.mkdir(dir_path)

                with open('{directory}/{hostname}.txt'.format(directory=dir_path, hostname=device.hostname), 'w') as f:
                    f.write(output)
            except netmiko.ssh_exception.NetmikoTimeoutException:
                print('Error: Connection timed-out to {hostname}, IP: {IP}'.format(hostname=device.hostname,
                                                                                   IP=device.IP))
            except netmiko.ssh_exception.NetmikoAuthenticationException:
                print('Error: Authentication failed to {hostname}, IP: {IP}'.format(hostname=device.hostname,
                                                                                    IP=device.IP))
            except ValueError:
                print(
                    'Error: Failed to enter enable mode on {hostname}, {IP}. Check if secret password is correct in '
                    'the config.cfg file.'.format(
                        hostname=device.hostname, IP=device.IP))
            except Exception as e:
                print('Error: Unknown exception - {exception}'.format(exception=e))

        if os.path.isdir(dir_path):
            print('\nCommands output saved to the {dir}'.format(dir=dir_path))

    def quit(self, exit_code):
        if self._autoexit is False:
            input('Press enter to exit...')
            exit(exit_code)


UniversalNetworkBackupTool()
