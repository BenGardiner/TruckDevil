import importlib
import os
import sys
import argparse
from pkgutil import iter_modules

# Ensure the truckdevil directory is in sys.path for internal imports
package_dir = os.path.dirname(os.path.abspath(__file__))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

from libs.device import Device
from libs.command import Command
try:
    from __init__ import __version__
except ImportError:
    from . import __version__
from prompt_toolkit.completion import NestedCompleter


class FrameworkCommands(Command):
    intro = "Welcome to the truckdevil framework v{}. Type 'help or ?' for a list of commands.".format(__version__)
    prompt = '(truckdevil) '

    def __init__(self):
        super().__init__()
        self._device = None
        module_path = os.path.join(os.path.dirname(__file__), 'modules')
        self.module_names = [name for _, name, _ in iter_modules([module_path])]

    def get_completion_dict(self):
        """
        Builds a completion dictionary that includes modules for 'run_module' 
        and known CAN interfaces for 'add_device'.
        """
        import can
        
        # Get standard base completions (help, quit, etc.)
        nested_dict = super().get_completion_dict()
        
        # Get standard CAN interfaces
        interfaces = ['m2']
        if hasattr(can, 'VALID_INTERFACES'):
            interfaces.extend(can.VALID_INTERFACES)
        elif hasattr(can.interface, 'VALID_INTERFACES'):
            interfaces.extend(can.interface.VALID_INTERFACES)
        interfaces = sorted(list(set(interfaces)))

        # Sub-commands for run_module and use
        module_completer = {name: None for name in self.module_names}
        nested_dict['run_module'] = module_completer
        nested_dict['use'] = module_completer
        
        # Sub-commands for add_device
        nested_dict['add_device'] = {iface: None for iface in interfaces}
        
        return nested_dict

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, new_device):
        self._device = new_device

    @property
    def device_added(self):
        if self._device is not None:
            return True
        return False

    def do_list_device(self, args):
        """
        List the current CAN device
        """
        print(str(self.device))

    def do_add_device(self, args):
        """
        Add a new hardware device. If one exists, replace it.

        usage: add_device <interface> <channel> <can_baud> [serial_port]

        Arguments:
            interface       The CAN interface to use. e.g. m2 or one supported by python-can
                            https://python-can.readthedocs.io/en/master/interfaces.html
            channel         CAN channel to send/receive on. e.g. can0, can1, vcan0
            can_baud        Baudrate on the CAN bus. Most common are 250000 and 500000. Use 0 for autobaud detection.
            serial_port     Serial port that the M2 is connected to, if used. For example: COM7 or /dev/ttyX.

        examples:
        add_device m2 can0 250000 COM5
        add_device socketcan vcan0 500000
        add_device pcan PCAN_USBBUS1 500000
        """
        argv = args.split()
        if len(argv) < 3:
            print("Error: expected device details")
            self.do_help("add_device")
            return
        interface = argv[0]
        channel = argv[1]
        can_baud = argv[2]
        serial_port = None
        if len(argv) >= 4:
            serial_port = argv[3]
        self.device = Device(interface, serial_port, channel, can_baud)

    def do_list_modules(self, args):
        """
        List all available modules
        """
        for name in self.module_names:
            print(name)

    def do_ls(self, args):
        """
        alias 'ls' to 'list_modules'
        """
        self.do_list_modules(args) 

    def do_run_module(self, args):
        """
        Run a module from the 'modules' directory that contains
        a 'main_mod()' function

        usage: run_module <MODULE_NAME> [MODULE_ARGS]

        example:
        run_module read_messages
        """
        argv = args.split()
        if len(argv) == 0:
            print("Error: expected module name")
            self.do_help("run_module")
            return
        module_name = argv[0]
        if module_name in self.module_names:
            mod = importlib.import_module("modules.{}".format(module_name))
            mod.main_mod(argv[1:], self.device)
        else:
            print("Error: module not found")
            self.do_help("run_module")


    def complete_run_module(self, text, line, begidx, endidx):
        if not text:
            return self.module_names
        else:
            return [n for n in self.module_names if n.startswith(text)]

    def do_use(self, args):
        """
        alias 'use' to 'run_module'
        """
        self.do_run_module(args) 

    def complete_use(self, text, line, begidx, endidx):
        return self.complete_run_module(text, line, begidx, endidx)

def main():
    parser = argparse.ArgumentParser(description="truckdevil J1939 testing framework", add_help=False)
    parser.add_argument("-c", "--commands", help="Semicolon-separated list of commands to execute and then exit")
    parser.add_argument("-V", "--version", action="store_true", help="Show version and exit")
    parser.add_argument("-h", "--help", action="store_true", help="Show help and exit")
    
    # We want to allow the existing positional commands too, so we use parse_known_args
    args, unknown = parser.parse_known_args()

    if args.version:
        print("truckdevil {}".format(__version__))
        sys.exit(0)

    if args.help and not args.commands and not unknown:
        parser.print_help()
        sys.exit(0)

    fc = FrameworkCommands()
    
    if args.commands is not None:
        if args.commands:
            commands = args.commands.split(';')
            for cmd in commands:
                cmd = cmd.strip()
                if cmd:
                    fc.onecmd(cmd)
        sys.exit(0)

    if unknown:
        if unknown[0] == "add_device" and "run_module" in unknown:
            module_index = unknown.index("run_module")
            device_args = unknown[:module_index+1] # Include 'add_device'
            module_args = unknown[module_index:] # Include 'run_module'
            fc.onecmd(' '.join(device_args))
            fc.onecmd(' '.join(module_args))
        elif unknown[0] == "add_device" and not "run_module" in unknown:
            fc.onecmd(' '.join(unknown[:5]))
            fc.onecmd(' '.join(unknown[5:]))
            fc.cmdloop()
        else:
            fc.onecmd(' '.join(unknown))
    else:
        fc.cmdloop()


if __name__ == "__main__":
    main()

