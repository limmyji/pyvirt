# pyvirt
Python SDK for managing Windows Hyper-V virtual machines

# setup
1) install windows 10 pro or windows 11 pro on your host system (development was done on 10 pro, but in theory 11 pro will work too)
2) search hyperv in the windows search bar, turn windows features on/off -> enable hyperv (tools and platform) -> restart host
3) on reboot, open hyperv manager, click action -> virtual switch manager -> create new virtual switch -> external network -> select your network adapter -> apply
    - if this is your only network adapter, allow management os to share this network adapter too
4) set default_virtual_switch parameter in config.py to the name of this new virtual switch
5) get a windows iso file (follow steps on https://www.microsoft.com/en-ca/software-download/windows10, make sure the os matches your host os)
6) right click your computers name in the top left corner, under hyper v manager, click new -> virtual machine
    - name this virtual machine, set base_vm_name parameter in config.py to the name of this new vm
    - make sure you select generation 2
    - give the vm memory, whatever suits your hardware, i recommend atleast 8GB (8192MB), uncheck dynamic memory, update vm_memory in config.py accordingly
    - attach the previously made virtual switch to the vm
    - create a virtual hard disk, however large you need (64GB for win11, 32GB for win10), set vhdx_store in config.py to the file path shown
    - install an os, using the iso file we got previously
    - next
7) right click your newly created vm in the center panel, give it more virtual processors (i recommend atleast 4 if possible), update vm_cpu in config.py accordingly, disable checkpoints
    - for windows 11 guest, you may also have to click on security, and enable trusted platform module
8) right click your computers name in the top left corner, hyperv settings -> make sure enhanced session mode is disabled
9) right click the vm, and start it, then open up its graphical interface and go through windows setup
    - make an account offline with **no password**
    - change guest_username in config.py to the username used during setup
10) setup whatever you want in this vm, this will be the base vm image that additional guests will be cloned from

# for gpu partition support in guests

# for guests with passwords

# TODO:
- add documentation on how to get password support and gpu partitioning working
- add accessibility to server.py (ex print out the queue, and view active sessions)
- document functionality
