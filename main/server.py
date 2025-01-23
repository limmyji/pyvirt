import threading
import time
import instance
import uuid
from collections import deque

from shared import SUCCESS
from shared import FAILURE

SCAN_STOP = 0
SCAN_START = 1


def test_callback(session_details):
    print(session_details)


class server:
    def scanQueue(self):
        while (1):
            time.sleep(30)
            # if it is itme to stop scanning
            if self.scaning == SCAN_STOP:
                return
            
            print("[INFO]:        start scan")
            # check all current active sessions, see if it is time to end them
            cur_time = time.time()
            end_thread_list = []
            for i in range(len(self.active_sessions)):
                session = self.active_sessions[i]
                if session.end_time < cur_time or not session.posted or not session.is_on():
                    callback_array = [FAILURE]
                    end_thread = threading.Thread(target=session.end, args=(callback_array,)) # thread for each instance we need to end
                    end_thread_list.append([end_thread, callback_array, i])
                    end_thread.start()
            # make sure all start threads ran properly
            for thread in end_thread_list[::-1]:
                thread[0].join()
                if thread[1][0] == FAILURE:
                    print("[ERROR]:       error when ending expired sessions")
                self.active_sessions.pop(thread[2])
                self.active_count -= 1
            
            # then try to allocate vms to next users in queue
            start_thread_list = []
            num_to_allocate = self.vm_count - self.active_count
            while num_to_allocate and self.queue_count:
                next_user = self.user_queue.popleft()
                self.queue_count -= 1
                new_instance = instance.instance(name="VM-%s" % (uuid.uuid4()), user=next_user[0], callback=next_user[1], sesion_length=300)
                callback_array = [FAILURE]
                start_thread = threading.Thread(target=new_instance.start, args=(callback_array,)) # thread for each instance we need to start
                start_thread_list.append([start_thread, callback_array, new_instance])
                start_thread.start()
                num_to_allocate -= 1
            # make sure all start threads ran properly
            for thread in start_thread_list:
                thread[0].join()
                if thread[1][0] == FAILURE:
                    print("[ERROR]:       error when starting new session")
                self.active_count += 1
                self.active_sessions.append(thread[2])
            # done
            print("[INFO]:        done scan")


    def __init__(self, vm_max, callback=test_callback):
        self.vm_count = vm_max  # max number of active vms we can have at a time
        
        self.scan_thread = threading.Thread(target=self.scanQueue, args=())  # thread where function for scanning the queue is looped over and over
        self.scaning = SCAN_START # flag indicating status of scanning (SCAN_STOP = stop scanning, SCAN_ACTIVE = scanning rn, SCAN_IDLE = not scanning rn)

        self.user_queue = deque()  # queue of users who requested a vm (.append(item) and .pop())
        self.queue_count = 0  # num of users in queue

        self.active_sessions = []  # set of the active sessions, each element is a instance
        self.active_count = 0  # number of active sessions

        # callback function used to send connection details to those who requested them (connection details = [vm name, ip, guest username, guest password])
        #   default is the above test_callback function, which just prints these details out
        self.callback = callback

        # start scanning
        self.scan_thread.start()


    def fini(self):
        # set flag to stop scanning, wait for scanning thread to end
        self.scaning = SCAN_STOP
        self.scan_thread.join()
        # force end all active sessions
        for session in self.active_sessions:
            end_result = session.end()
            if end_result == FAILURE:
                print("[ERROR]:       error when fini server")
                return FAILURE
        return SUCCESS


    # full reset of server, reset to original starting state
    def reset(self, intentional):
        if intentional:
            print("[INFO]:        starting server reset")
        else:
            print("[ERROR]:       force server reset")
        self.fini()
        self.__init__(vm_max=self.vm_count)
    

    ### assume user is a unique string identifier for each user
    # when a user requests a session, add them to the queue 
    def requestVM(self, user):
        print("[INFO]:        session requested by user %s" % (user))
        if self.user_queue.count((user, self.callback)):
            print("[INFO]:        not adding user %s, they are already in queue" % (user))
            return SUCCESS
        self.user_queue.append((user, self.callback))
        self.queue_count += 1
        return SUCCESS
    

    # if a user leaves the queue
    def removeFromQueue(self, user):
        print("[INFO]:        removing user from queue: %s" % (user))
        if not self.user_queue.count((user, self.callback)):
            print("[INFO]:        cant remove, user %s is not in queue" % (user))
            return SUCCESS
        self.user_queue.remove((user, self.callback))
        self.queue_count -= 1
        return SUCCESS
    

    # end a session
    def forceEndSession(self, user):
        print("[INFO]:        ending session of user %s" % (user))
        for i in range(len(self.active_sessions)):
            session = self.active_sessions[i]
            if session.user == user and session.posted:
                end_result = session.end()
                if end_result == FAILURE:
                    print("[ERROR]:       error when ending sessions of user %s" % (user))
                    return FAILURE
                self.active_sessions.pop(i)
                self.active_count -= 1
                break
        return SUCCESS
