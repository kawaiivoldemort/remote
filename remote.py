import os
import sys
import json
import urllib.request
import zipfile


# Script Directory
script_dir = os.path.dirname(os.path.realpath(__file__))
script_name = os.path.basename(__file__)


# Load systems
remote_systems = {}
with open("{script_dir}/systems.json".format(script_dir=script_dir), "r") as f:
    remote_systems = json.load(f)


# Converts Windows paths to WSL paths
def windows_path_to_wsl(windows_path):
    drive, wsl_path = tuple(os.path.abspath(windows_path).split(":"))
    wsl_path = wsl_path.replace("\\", "/")
    wsl_path = "/mnt/{0}{1}".format(drive.lower(), wsl_path)
    return wsl_path


# Login to a remote system via SSH
def login(args):
    # Assertions
    assert(len(args) >= 1)
    remote_name = args[0]
    assert(remote_name in remote_systems)
    remote = remote_systems[remote_name]
    # Make the CMD
    cmd = "ssh "
    if "jump" in remote:
        jump_name = remote["jump"]
        assert(jump_name in remote_systems)
        jump = remote_systems[jump_name]
        cmd += "-o ProxyCommand=\"ssh "
        if "key" in jump:
            cmd += "-i {key_dir}/{jump_key_file_name} ".format(key_dir=script_dir, jump_key_file_name=jump["key"])
        cmd += "-W %h:%p {jump_user}@{jump_host}\" ".format(jump_user=jump["user"], jump_host=jump["host"])
    if "key" in remote:
        cmd += "-i {key_dir}/{host_key_file_name} ".format(key_dir=script_dir, host_key_file_name=remote["key"])
    cmd += "{remote_user}@{remote_host} ".format(remote_user=remote["user"], remote_host=remote["host"])
    os.system(cmd)


# Transfer files to a remote system via rsync
def transfer(args):
    global script_dir
    # Assertions
    assert(len(args) >= 2)
    assert((":" in args[0]) or (":" in args[-1]))
    assert(not ((":" in args[0]) and (":" in args[-1])))
    # In windows, call via WSL
    if os.name == "nt":
        # Change all paths to WSL style
        script_dir = windows_path_to_wsl(script_dir)
        if ":" in args[-1]:
            for i in range(len(args) - 1):
                args[i] = windows_path_to_wsl(args[i])
        else:
            args[-1] = windows_path_to_wsl(args[-1])
        cmd = "bash -c \"python3 {script_dir}/{script_name} transfer ".format(script_dir=script_dir, script_name=script_name)
        cmd += " ".join(args)
        cmd += "\""
        os.system(cmd)
    else:
        # Get the Arguments
        command = 0 # Upload
        remote = None
        remote_path = None
        host_paths = None
        if ":" in args[0]:
            remote_name, remote_path = tuple(args[0].split(":"))
            assert(remote_name in remote_systems)
            remote = remote_systems[remote_name]
            host_paths = [args[-1]]
            command = 1
        else:
            remote_name, remote_path = tuple(args[-1].split(":"))
            assert(remote_name in remote_systems)
            remote = remote_systems[remote_name]
            host_paths = args[:-1]
            command = 0
        # Make the cmd
        host_path = " ".join(host_paths)
        cmd = "rsync -az --info=progress2 -e 'ssh "
        if "jump" in remote:
            jump_name = remote["jump"]
            assert(jump_name in remote_systems)
            jump = remote_systems[jump_name]
            cmd += "-o ProxyCommand=\"ssh "
            if "key" in jump:
                cmd += "-i {key_dir}/{jump_key_file_name} ".format(key_dir=script_dir, jump_key_file_name=jump["key"])
            cmd += "-A {jump_user}@{jump_host} -W %h:%p\" ".format(jump_user=jump["user"], jump_host=jump["host"])
        if "key" in remote:
            cmd += "-i {key_dir}/{host_key_file_name} ".format(key_dir=script_dir, host_key_file_name=remote["key"])
        cmd += "' "
        # Add the transfer details
        if command == 0:
            cmd += "{host_path} ".format(host_path=host_path)
            cmd += "{remote_user}@{remote_host}:{remote_path} ".format(remote_user=remote["user"], remote_host=remote["host"], remote_path=remote_path)
        elif command == 1:
            cmd += "{remote_user}@{remote_host}:{remote_path} ".format(remote_user=remote["user"], remote_host=remote["host"], remote_path=remote_path)
            cmd += "{host_path} ".format(host_path=host_path)
        print(cmd)
        os.system(cmd)


# List Systems
def list_systems():
    print(json.dumps(remote_systems, indent=2))


# Command Handler
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.argv.append(None)
    if sys.argv[1] == "login":
        login(sys.argv[2:])
    elif sys.argv[1] == "transfer":
        transfer(sys.argv[2:])
    elif sys.argv[1] == "list":
        list_systems()
    else:
        print("Usage:")
        systems = "|".join(remote_systems.keys())
        print("    list")
        print("        - lists the system config")
        print("    login <{0}>".format(systems))
        print("        - ssh login to the given node")
        print("    transfer <{0}>:remote_path host_path".format(systems))
        print("        - download files/folders from remote to host path via rsync")
        print("    transfer host_path <{0}>:remote_path".format(systems))
        print("        - upload files/folders from host path to remote via rsync")
        print()
        print("In windows, we use WSL for rsync. If you have SSH Key permission issues, see https://devblogs.microsoft.com/commandline/chmod-chown-wsl-improvements/.")
