import subprocess
import time
import glob
import random
import string
import re

import config
# documentation for each of these params can be found in config.py
base_vm_name = config.base_vm_name
base_vhdx = config.base_vhdx
virtual_switch = config.default_virtual_switch
vhdx_store = config.vhdx_store
vm_password_store = config.vm_password_store
guest_username = config.guest_username
guest_script_store = config.guest_script_store
enable_password = config.guest_password
vm_memory = config.vm_memory
vm_cpu = config.vm_cpu

SUCCESS = 0
FAILURE = 1

# run shell command, returns an object with the stdout and stderr
def _runShellCommand(command):
    p = subprocess.run(
        ["powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Unrestricted",
        "-Command", command],
        capture_output=True, text=True
    )
    return p


# check if a VM currently exists
def _isExist(vm_name):
    cmd = "Get-VM"
    result = _runShellCommand(cmd)
    if vm_name not in result.stdout:
        print("a VM with the name %s doesn't exist" % (vm_name))
        return False
    print("found VM with name %s!" % (vm_name))
    return True


# checks if a VM is on or off
def _isOn(vm_name):
    cmd = "Get-VM"
    result = _runShellCommand(cmd)
    result = result.stdout.split('\n')
    for line in result:
        if vm_name in line:
            if "Off" not in line:
                print("%s is on!" % (vm_name))
                return True
    print("%s is off" % (vm_name))
    return False


# gets external ip addr of VM, returns as a string
# requires that vm exists and is on
def _getIp(vm_name):
    cmd = "(Get-VMNetworkAdapter \"%s\").IPAddresses" % (vm_name)
    result = _runShellCommand(cmd)
    result = result.stdout.split("\n")
    for line in result:
        if re.search("^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", line):
            return line
    print("ERROR WHEN TRYING TO FIND IP of %s!" % (vm_name))
    return None


# copy file from host to guest
# requires that vm exists and is on
def _copyFileToVm(vm_name, host_path, guest_path):
    cmd = "Copy-VMFile %s -SourcePath %s -DestinationPath %s -CreateFullPath -FileSource Host" % (vm_name, host_path, guest_path)
    result = _runShellCommand(cmd)
    if result.stderr != "" or result.stdout != "":
        print("ERROR COPYING %s ON HOST TO %s on %s!" % (host_path, guest_path, vm_name))
        print("command: %s" % (cmd))
        print(result.stderr)
        print(result.stdout)
        return False
    return True


# gets vmname/ip/username/password combo for rdp
# return: [vm name, ip, guest username, guest password]
def _connectToVm(vm_name):
    print("########## _connectToVm(%s) ##########" % (vm_name))
    if not _isExist(vm_name):
        print("%s does not exist, cannot connect" % (vm_name))
        return None
    if not _isOn(vm_name):
        print("%s is off, cannot get connection details" % (vm_name))
        return None

    # if we want to generate unique passkey
    password = ""
    if enable_password:
        # generate password if enabled in config
        print("generating password...")
        password = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
        host_path = "%s\\%s\\password.txt" % (vm_password_store, vm_name)
        print("password will be: %s" % (password))
        create_cmd = "New-Item \"%s\" -Force" % (host_path)
        create_result = _runShellCommand(create_cmd)
        if "password.txt" not in create_result.stdout or create_result.stderr != "":
            print("ERROR WHEN GENERATING PASSWORD")
            print("command: %s" % (create_cmd))
            print(create_result.stderr)
            print(create_result.stdout)
            return None
        set_pass_cmd = "Set-Content \"%s\" %s" % (host_path, password)
        set_pass_result = _runShellCommand(set_pass_cmd)
        if set_pass_result.stdout != "" or set_pass_result.stderr != "":
            print("ERROR WHEN GENERATING PASSWORD")
            print("command: %s" % (set_pass_cmd))
            print(set_pass_result.stderr)
            print(set_pass_result.stdout)
            return None
        print("generated password!")
        # copying password to guest, a script on the guest will then set the guest password to
        #   the contents of this text file
        print("copying password to guest...")
        if not _copyFileToVm(vm_name, host_path, "%s\\password.txt" % (guest_script_store)):
            return None
        print("copied password to %s" % (vm_name))
        time.sleep(30)
    
    # get ip, return these results
    ip = _getIp(vm_name)
    print("name: %s\nip: %s\nuser: %s\npass: %s" % (vm_name, ip, guest_username,password))
    return [vm_name, ip, guest_username, password]


# create VM from base vm, with specified name
def _createVM(vm_name):
    print("########## _createVM(%s) ##########" % (vm_name))
    if _isExist(vm_name):
        print("%s already exists, doing nothing." % (vm_name))
        return True

    # clone vhdx
    new_vhdx_path = "%s\\%s.vhdx" % (vhdx_store, vm_name)
    clone_cmd = "Copy-Item -Path \"%s\" -Destination \"%s\"" %(base_vhdx, new_vhdx_path)
    clone_result = _runShellCommand(clone_cmd)
    if clone_result.stdout != "" or clone_result.stderr != "":
        print("ERROR WHEN CLONING VHDX!")
        print("command: %s" % (clone_result))
        print(clone_result.stderr)
        print(clone_result.stdout)
        return False

    # create new vm, associate with recently cloned vhdx
    creation_cmd = "New-VM -Name \"%s\" -Generation 2 -VHDPath \"%s\"" % (vm_name, new_vhdx_path)
    creation_result = _runShellCommand(creation_cmd)
    if vm_name not in creation_result.stdout or creation_result.stderr != "":
        print("ERROR WHEN CREATING VM!")
        print("command: %s" % (creation_cmd))
        print(creation_result.stderr)
        print(creation_result.stdout)
        return False

    # configure some settings of this vm
    config_cmd = "Set-VM -Name \"%s\" -CheckpointType Disabled -StaticMemory -MemoryStartupBytes %dGB -ProcessorCount %d" % (vm_name, vm_memory, vm_cpu)
    config_result = _runShellCommand(config_cmd)
    if config_result.stdout != "" or config_result.stderr != "":
        print("ERROR WHEN CONFIG VM!")
        print("command: %s" % (config_result))
        print(config_result.stderr)
        print(config_result.stdout)
        return False
    
    # attatch the specified virtual switch in config to this vm
    virtual_switch_cmd = "Connect-VMNetworkAdapter -VMName \"%s\" -Name \"Network Adapter\" -SwitchName \"%s\"" % (vm_name, virtual_switch)
    virtual_switch_result = _runShellCommand(virtual_switch_cmd)
    if virtual_switch_result.stdout != "" or virtual_switch_result.stderr != "":
        print("ERROR WHEN ASSIGNING virtual switch!")
        print("command: %s" % (virtual_switch_cmd))
        print(virtual_switch_result.stderr)
        print(virtual_switch_result.stdout)

    # done
    print("created vm %s!" % (vm_name))
    return True


# delete a VM and its .vhdx
def _deleteVM(vm_name):
    print("########## _deleteVM(%s) ##########" % (vm_name))
    if vm_name == base_vm_name:
        print("ERROR CANNOT DELETE BASE VM")
        return False
    if not _isExist(vm_name):
        print("%s does not exist, doing nothing")
        return True
    if _isOn(vm_name):
        print("ERROR, %s IS ON, CANNOT DELETE IN THIS STATE" % (vm_name))
        return False

    # delete VM and its config files
    delete_cmd = "Remove-VM -Name \"%s\" -Force" % (vm_name)
    delete_result = _runShellCommand(delete_cmd)
    if delete_result.stderr != "" or delete_result.stdout != "":
        print("ERROR WHEN DELETING CONFIG OF %s!" % (vm_name))
        print("command: %s" % (delete_cmd))
        print(delete_result.stderr)
        print(delete_result.stdout)
        return False

    # delete .vhdx
    vhdx_delete_cmd = "Remove-Item \"%s\\%s.vhdx\"" % (vhdx_store, vm_name)
    vhdx_delete_result = _runShellCommand(vhdx_delete_cmd)
    if vhdx_delete_result.stderr != "" or vhdx_delete_result.stdout != "":
        print("ERROR WHEN DELETING .vhdx OF %s!" % (vm_name))
        print("command: %s" % (vhdx_delete_cmd))
        print(vhdx_delete_result.stderr)
        print(vhdx_delete_result.stdout)
        return False
    print("deleted vm %s." % (vm_name))
    return True


# power on a VM
def _startVM(vm_name):
    print("########## _startVM(%s) ##########" % (vm_name))
    if not _isExist(vm_name):
        return False
    if _isOn(vm_name):
        print("%s is already on, doing nothing" % (vm_name))
        return True

    # send power
    cmd = "Start-VM \"%s\"" % (vm_name)
    result = _runShellCommand(cmd)
    if result.stderr != "" or result.stdout != "":
        print("ERROR WHEN POWERING ON %s!" % (vm_name))
        print("command: %s" % (cmd))
        print(result.stderr)
        print(result.stdout)
        return False

    time.sleep(20)
    # check if power has been sent
    if _isOn(vm_name):
        print("powered on %s!" % (vm_name))
        return True
    print("ERROR, WAS NOT ABLE TO POWER ON %s" % (vm_name))
    return False


# shutdown a VM
def _stopVM(vm_name):
    print("########## _stopVM(%s) ##########" % (vm_name))
    if not _isExist(vm_name):
        return False
    if not _isOn(vm_name):
        print("%s is already off, doing nothing" % (vm_name))
        return True
    
    # send poweroff
    cmd = "Stop-VM -Name %s -TurnOff" % (vm_name)
    result = _runShellCommand(cmd)
    if result.stderr != "" or result.stdout != "":
        print("ERROR WHEN SHUTTING DOWN %s!" % (vm_name))
        print("command: %s" % (cmd))
        print(result.stderr)
        print(result.stdout)
        return False

    time.sleep(10)
    # check if VM is shutdown
    if not _isOn(vm_name):
        print("shutdown %s!" % (vm_name))
        return True
    print("ERROR, WAS NOT ABLE TO SHUTDOWN %s" % (vm_name))
    return False


# removes all VFs from a VM, requires the VM to be shutoff
def _removeVF(vm_name):
    print("########## _removeVF(%s) ##########" % (vm_name))
    if not _isExist(vm_name):
        return False
    if _isOn(vm_name):
        print("ERROR, %s IS CURRENTLY ON, CANT REMOVE VF" % (vm_name))
        return False
    
    # remove parition
    cmd = "Remove-VMGpuPartitionAdapter \"%s\"" % (vm_name)
    result = _runShellCommand(cmd)
    if result.stdout != "":
        print("ERROR WHEN REMOVING VF FROM %s!" % (vm_name))
        print("command: %s" % (cmd))
        print(result.stderr)
        print(result.stdout)
        return False
    if result.stderr != "":
        if "Unable to find a Gpu partition adapter matching the given criteria." in result.stderr:
            print("no VFs were assigned to %s, doing nothing" % (vm_name))
            return True
        print("ERROR WHEN REMOVING VF FROM %s!" % (vm_name))
        print("command: %s" % (cmd))
        print(result.stderr)
        print(result.stdout)
        return False
    print("removed VFs from %s!" % (vm_name))
    return True


# assigns a VF to a VM, requires the VM to be shutoff
def _assignVF(vm_name):
    print("########## _assignVF(%s) ##########" % (vm_name))
    if not _isExist(vm_name):
        return False
    if _isOn(vm_name):
        print("ERROR, %s IS CURRENTLY ON, CANT ASSIGN VF" % (vm_name))
        return False
    
    # get partition adapter stats of host gpu
    get_gpu_cmd = "Get-VMPartitionableGpu"
    gpu_result = _runShellCommand(get_gpu_cmd)
    if gpu_result.stdout != "":
        print("ERROR WHEN FETCHING GPU PARTITION DETAILS!")
        print("command: %s" % (get_gpu_cmd))
        print(gpu_result.stderr)
        print(gpu_result.stdout)

    # dict with partition adapter stats of GPU
    specs_dict = {}
    gpu_result.stdout.replace(' ', '')
    gpu_result.stdout.split('\n')
    for line in gpu_result.stdout:
        split = line.split(':')
        specs_dict[split[0]] = specs_dict[split[1]]

    # cmds to configure the partition
    cmd_list = [
        "Add-VMGpuPartitionAdapter -VMName \"%s\"" % (vm_name),
        # get the values from first running Get-VMPartitionableGpu
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -MinPartitionVRAM %s" % (vm_name, specs_dict["MinPartitionVRAM"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -MaxPartitionVRAM %s" % (vm_name, specs_dict["MaxPartitionVRAM"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -OptimalPartitionVRAM %s" % (vm_name, specs_dict["OptimalPartitionVRAM"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -MinPartitionEncode %s" % (vm_name, specs_dict["MinPartitionEncode"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -MaxPartitionEncode %s" % (vm_name, specs_dict["MaxPartitionEncode"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -OptimalPartitionEncode %s" % (vm_name, specs_dict["OptimalPartitionEncode"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -MinPartitionDecode %s" % (vm_name, specs_dict["MinPartitionDecode"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -MaxPartitionDecode %s" % (vm_name, specs_dict["MaxPartitionDecode"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -OptimalPartitionDecode %s" % (vm_name, specs_dict["OptimalPartitionDecode"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -MinPartitionCompute %s" % (vm_name, specs_dict["MinPartitionCompute"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -MaxPartitionCompute %s" % (vm_name, specs_dict["MaxPartitionCompute"]),
        "Set-VMGpuPartitionAdapter -VMName \"%s\" -OptimalPartitionCompute %s" % (vm_name, specs_dict["OptimalPartitionCompute"]),
        "Set-VM -GuestControlledCacheTypes $true -VMName \"%s\"" % (vm_name),
        "Set-VM -LowMemoryMappedIoSpace 1Gb -VMName \"%s\"" % (vm_name),
        "Set-VM -HighMemoryMappedIoSpace 32Gb -VMName \"%s\"" % (vm_name)
    ]
    for cmd in cmd_list:
        result = _runShellCommand(cmd)
        if result.stderr != "" or result.stdout != "":
            print("ERROR WHEN ASSIGNING VF TO %s!" % (vm_name))
            print("command: %s" % (cmd))
            print(result.stderr)
            print(result.stdout)
            return False
    print("assigned VF to %s!" % (vm_name))
    return True
