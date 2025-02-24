import shared
import config
import time

from shared import SUCCESS
from shared import FAILURE

class instance:
    def __init__(self, name, user, sesion_length, callback, sleep_func):
        # name of the vm, time allocation of the session in seconds, user of the vm
        self.vm_name = name
        self.end_time = sesion_length
        self.user = user
        # login details will be fetched upon startup
        self.login_details = None
        # if the vm is done posting
        self.posted = False
        # callback function to return session details
        self.callback = callback
        # function used to wait, passed on from server
        self.sleep_func = sleep_func

    def is_on(self):
        # see if vm is stil alive
        return shared._isOn(self.vm_name)


    def start(self, callback_array=None):
        # start session, create vm with name self.vm_name, get login details
        # self.login_details = [self.vm_name, ip, guest_username, password]
        print("[INFO]:        attempting to start session %s" % (self.vm_name))

        # create vm
        create_result = shared._createVM(self.vm_name)
        if not create_result:
            print("[ERROR]:       error when creating vm %s" % (self.vm_name))
            return FAILURE
        
        if config.enable_gpu_virt:
            # assign vf
            assign_result = shared._assignVF(self.vm_name)
            if not assign_result:
                print("[ERROR]:       error when assigning vf to vm %s" % (self.vm_name))
                return FAILURE

        # power on vm
        start_result = shared._startVM(self.vm_name, sleep_func=self.sleep_func)
        if not start_result:
            print("[ERROR]:       error when starting vm %s" % (self.vm_name))
            return FAILURE

        # connect to vm, get login details
        connect_result = shared._connectToVm(self.vm_name, sleep_func=self.sleep_func)
        if not connect_result:
            print("[ERROR]:       error when connecting to vm %s" % (self.vm_name))
            return FAILURE

        self.login_details = connect_result
        self.login_details.append(self.user)
        # done posting, send result via callback function
        self.posted = True
        self.end_time += time.time()
        callback_result = self.callback(self.login_details)
        if callback_array is not None:
            callback_array[0] = SUCCESS
        return callback_result


    def end(self, callback_array=None):
        # end session, clear all flags
        if not isinstance(self.vm_name, str):
            return self.end(self.vm_name[0])
        print("[INFO]:        attempting to stop session %s..." % (self.vm_name))

        # stop vm
        stop_result = shared._stopVM(self.vm_name, sleep_func=self.sleep_func)
        if not stop_result:
            print("[ERROR]:       error when stopping vm %s" % (self.vm_name))
            return FAILURE

        if config.enable_gpu_virt:
            # remove vf
            remove_result = shared._removeVF(self.vm_name)
            if not remove_result:
                print("[ERROR]:       error when removing vf from vm %s" % (self.vm_name))
                return FAILURE

        # delete vm
        delete_result = shared._deleteVM(self.vm_name)
        if not delete_result:
            print("[ERROR]:       error when deleting vm %s" % (self.vm_name))
            return FAILURE

        # clear details
        self.login_details = None
        self.end_time = None
        self.user = None
        self.posted = False
        # ret
        if callback_array is not None:
            callback_array[0] = SUCCESS
        return SUCCESS
