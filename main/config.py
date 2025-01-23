# name of the virtual switch we want to assign to the sessions
default_virtual_switch = r"New Virtual Switch"
# base vm name
base_vm_name = r"22h2-base-og"
# how much ram each guest gets, in GB
vm_memory = 8
# where the virtual hard disks of each session will be stored
vhdx_store = r"G:\Hyper-V\Virtual Hard Disks"
# exact path to the base vm's .vhdx file, adjust if needed
base_vhdx = vhdx_store + "\\" + base_vm_name + ".vhdx"
# how many cpus each guest gets
vm_cpu = 8
# guest username
guest_username = r"User"

# enable gpu partitioning
enable_gpu_virt = False

# if we want to generate a password for each guest
guest_password = False
# where the password text file for each session will be generated on host
vm_password_store = r"G:\Hyper-V\Passwords"
# where the password text file for each session will be moved to on the guest, a script on the guest
#   will then change the guest password to the contents of these text files
guest_script_store = r"C:\Users\User\Desktop"
