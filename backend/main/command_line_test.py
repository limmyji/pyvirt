import server

host = server.server(vm_max=2)

while (1):
    cmd = input("Enter command (1 to req, 2 to leave queue, 3 to force off session, 4 to fini server, 5 to reset server): ")
    if cmd == "1":
        user = input("Enter username: ")
        host.requestVM(user)
    elif cmd == "2":
        user = input("Enter username: ")
        host.removeFromQueue(user)
    elif cmd == "3":
        user = input("Enter username: ")
        host.forceEndSession(user)
    elif cmd == "4":
        host.fini()
    elif cmd == "5":
        intentional = input("Enter 1 for intentional, 0 for not intentional")
        if intentional == "1":
            host.reset(intentional=True)
        elif intentional == "0":
            host.reset(intentional=False)
        else:
            print("not a valid input!")
    else:
        print("enter a valid command!")
