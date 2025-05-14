import pandas as pd
import sys
from hub_utilities_V1 import *

def print_hub_commands():
    print(" start_all: starts recording on all midges with all sensors")
    print(" stop_all: stops the recording on all midges")
    print(" midge: connect to a single midge for individual management and checks")
    print(" exit: stop and exit the hub script")
    print(" help: prints this help message")
    sys.stdout.flush()

if __name__ == "__main__":
    sync_frequency = 10.0 # How frequent the synchronisation is triggered, defaults to every 10 seconds

    df = pd.read_csv('sample_mapping_file.csv')
    do_synchronization = False
    print("Type help for a list commands")
    sys.stdout.flush()
    ti = timeout_input(poll_period=0.05)
    while True:
        command = ti.input(prompt='> ', timeout=sync_frequency,
                     extend_timeout_with_input=False, require_enter_to_confirm=True)

        if command == "start_all":
            if do_synchronization is True:
                print("Devices are already recording.")
                sys.stdout.flush()
            else:
                print("Start recording of all devices.")
                sys.stdout.flush()
                start_recording_all_devices(df)
                do_synchronization = True
                print("Devices are recording.")
                sys.stdout.flush()
        elif command == "stop_all":
            if do_synchronization is False:
                print("Devices are not recording.")
                sys.stdout.flush()
            else:
                print("Stopping the recording of all devices.")
                sys.stdout.flush()
                do_synchronization = False
                stop_recording_all_devices(df)
                print("Devices are stopped.")
                sys.stdout.flush()
        elif command == "help":
            print_hub_commands()
            sys.stdout.flush()
        elif command == "midge":
            print('Please type the id of the Midge you want to connect or exit.')
            sys.stdout.flush()

            while True:
                command = ti.input(prompt=' >', timeout=sync_frequency,
                                   extend_timeout_with_input=False, require_enter_to_confirm=True)

                if command == "":
                    print("Sync in single midge selection")
                    if do_synchronization is True:
                        print('Synchronisation is starting. Please wait until it ends.')
                        synchronise_and_check_all_devices(df)
                        print('Synchronisation is finished.')
                        sys.stdout.flush()
                elif command == "exit":
                    print("Exited single midge management")
                    sys.stdout.flush()
                    break
                else:
                    try:
                        midge_id = int(command)
                        current_mac_addr = (df.loc[df['Participant Id'] == midge_id]['Mac Address']).values[0]
                        cur_connection = Connection(midge_id, current_mac_addr)
                    except Exception as error:
                        print (str(error))
                        sys.stdout.flush()
                        continue
                    print ("Connected to the badge. For available commands, please type help.")
                    while True:
                        command = ti.input(prompt=' >', timeout=sync_frequency,
                                   extend_timeout_with_input=False, require_enter_to_confirm=True)
                        command_args = command.split(" ")
                        if command == "exit":
                            cur_connection.disconnect()
                            print(" Midge disconnected")
                            sys.stdout.flush()
                            break
                        if command != "":
                            try:
                                out = choose_function(cur_connection, command_args[0])
                                if out != None:
                                    print (out)
                                    sys.stdout.flush()
                            except Exception as error:
                                print (str(error))
                                print(" Command not found!")
                                sys.stdout.flush()
                                cur_connection.print_help()
                                continue
                        elif command == "":
                            print("Sync in single midge connected")
                            if do_synchronization is True:
                                print('Synchronisation is starting. Please wait till it ends.')
                                synchronise_and_check_all_devices(df, skip_id=midge_id, conn_skip_id=cur_connection)
                                print('Synchronisation is finished.')
                                sys.stdout.flush()
        elif command == "":
            if do_synchronization is True:
                print('Synchronisation is starting. Please wait till it ends.')
                synchronise_and_check_all_devices(df)
                print('Synchronisation is finished.')
                sys.stdout.flush()
        elif command == "exit":
            print("Exit hub script.")
            sys.stdout.flush()
            if do_synchronization:
                print("Stopping the recording of all devices.")
                sys.stdout.flush()
                do_synchronization = False
                stop_recording_all_devices(df)
                print("Devices are stopped.")
            quit(0)
        else:
            print('Unknown command.')
            sys.stdout.flush()
