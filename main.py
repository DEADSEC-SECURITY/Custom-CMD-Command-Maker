import os, re, sys
from winreg import OpenKey, EnumValue, SetValueEx, CloseKey
from winreg import HKEY_LOCAL_MACHINE, KEY_SET_VALUE, REG_SZ

class CMDCommandMaker():
    """
        Manages all logic for adding, removing,
        listing commands and registries so it works
        properly
    """

    REG_PATH = r'SOFTWARE\Microsoft\Command Processor'
    KEY_NAME = 'AutoRun'

    APP_DATA = os.getenv('APPDATA')
    COMMAND_FILE = os.path.join(APP_DATA, 'commands.bat')

    def __init__(self):
        self.key_edit_only = OpenKey(
            HKEY_LOCAL_MACHINE,
            r'SOFTWARE\Microsoft\Command Processor',
            0,
            KEY_SET_VALUE)

        self.key = OpenKey(
            HKEY_LOCAL_MACHINE,
            r'SOFTWARE\Microsoft\Command Processor')

    def __exit__(self, exc_type, exc_val, exc_tb):
        CloseKey(self.key)

    def get_registry(self):
        """
            Cycles through the registry if it
            finds a key with name <KEY_NAME> it
            will return its keys, value, type if
            it doesnt find it it will return False

            :return: (KEY, VALUE, TYPE) or False
        """

        for index in range(0, 1024):
            try:
                if EnumValue(self.key, index)[0] == self.KEY_NAME:
                    return EnumValue(self.key, index)
            except (WindowsError, OSError):
                return False

    def update_registry_key(self, file_path):
        """

            :param file_path: str
            :return: void
        """
        SetValueEx(self.key_edit_only, self.KEY_NAME, 1, REG_SZ, file_path)

    def create_start_file(self):
        """

            :return: void
        """

        with open(self.COMMAND_FILE, 'w') as file:
            file.write(
f"""@echo off

:: This file was auto generated
:: An entry to the registry under HKEY_LOCAL_MACHINE\{self.REG_PATH} should be created too

:: CUSTOM COMMANDS --\n
"""
            )

    def get_file_path(self):
        """

            :return: str
        """

        registry_path = self.get_registry()

        if not registry_path:
            # Create file
            self.create_start_file()
            self.update_registry_key(self.COMMAND_FILE)
            return self.COMMAND_FILE

        return registry_path[1]

    def get_commands(self):
        """

            :return: dict
        """

        file_path = self.get_file_path()
        regex = r'DOSKEY .*'
        with open(file_path, 'r') as file:
            file = file.read()
            commands = re.findall(regex, file)

        commands_clean = {}
        for x in commands:
            command = x.replace('DOSKEY', '').replace(' ', '').split('=')[0]
            value = x.split('=')[1]
            commands_clean[command] = value

        return commands_clean

    def add_command(self, command):
        """

            :param command: (COMMAND, VALUE)
            :return: "changed" or "not_changed"
        """

        file_path = self.get_file_path()

        current_commands = self.get_commands()

        if command[0] not in current_commands:
            with open(file_path, 'a') as file:
                file.write(f'DOSKEY {command[0]}={command[1]}\n')

            return 'changed'

        return 'not_changed'

    def remove_command(self, command):
        """

            :param command: str
            :return: "changed" or "not_changed"
        """

        file_path = self.get_file_path()

        current_commands = self.get_commands()

        if command in current_commands:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            with open(file_path, 'w') as file:
                for n, l in enumerate(lines):
                    if command not in l:
                        file.write(l)

            return 'changed'

        return 'not_changed'

class TerminalMenus():
    """
        Handles the connection between the user and
        CMDCommandMaker class. Displays a user friendly
        menu for the user to decide what he wants to do
    """

    def __init__(self):
        self.maker = CMDCommandMaker()
        self.main_menu()

    def main_menu(self):
        """

            :return: func
        """

        commands = self.maker.get_commands()
        print('Current commands:')
        for index, index_value in enumerate(commands):
            print(f'{index_value} -> {commands[index_value]}')
        print('---------------')
        print('1) Add command')
        print('2) Remove command')
        print('00) Exit')
        n = str(input())

        if n == '00':
            sys.exit()
        elif n == '1':
            return self.add_command_menu()
        elif n == '2':
            return self.remove_command_menu()
        else:
            print('PLEASE SELECT A VALID NUMBER')
            input('PRESS ENTER TO CONTINUE')
            return self.main_menu()

    def add_command_menu(self):
        """

            :return: func
        """

        command_name = input('What should your command be named? ')
        command_action = input('What should it do? ')

        if command_action == '' and command_name == '':
            return self.main_menu()

        self.maker.add_command((command_name, command_action))
        print('Command created ...')
        return self.main_menu()

    def remove_command_menu(self):
        """

            :return: func
        """

        commands = self.maker.get_commands()
        print('Current commands:')
        for index, index_value in enumerate(commands):
            print(f'{index}) {index_value} -> {commands[index_value]}')
        print('00) Exit')
        command = int(input())

        if command == 00:
            return self.main_menu()

        self.maker.remove_command(list(commands.keys())[command])
        print('Command removed')
        return self.main_menu()

if __name__ == '__main__':
    terminal_menu = TerminalMenus()
