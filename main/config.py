# exact path to the base vm's .vhdx file
base_vhdx = r"G:\\Hyper-V\\Virtual Hard Disks\\22h2-base-og.vhdx"
# base vm name, so we dont delete it
base_vm_name = r"22h2-base-og"

# how much ram each guest gets, in GB
vm_memory = 8
# how many cpus each guest gets
vm_cpu = 8
# name of the virtual switch we want to assign to the sessions
default_virtual_switch = r"New Virtual Switch"

# where the virtual hard disks of each session will be cloned to
vhdx_store = r"G:\Hyper-V\Virtual Hard Disks"
# where the password text file for each session will be generated locally
vm_password_store = r"G:\Hyper-V\Passwords"
# guest username
guest_username = r"User"
# where the password text file for each session will be moved to on the guest, a script on the guest
#   will then change the guest password to the contents of these text files
guest_script_store = r"C:\Users\User\Desktop"

# enable gpu partitioning
enable_gpu_virt = False
# if we want to generate a password for each guest
guest_password = False
