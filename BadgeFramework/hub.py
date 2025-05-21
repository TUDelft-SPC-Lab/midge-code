import pandas as pd
import sys
from hub_utilities import (
    timeout_input,
    start_recording_all_devices,
    stop_recording_all_devices,
    synchronise_and_check_all_devices,
    erase_sdcard_all_devices,
    print_fw_version_all_devices,
    choose_function,
    Connection,
)

def print_hub_commands():
    print(" start_all: starts recording on all midges with all sensors")
    print(" stop_all: stops the recording on all midges")
    print(" erase_all: erase the recorded data on all midges")
    print(" fw_all: show the firmware version of all of the midges")
    print(" midge: connect to a single midge for individual management")
    print(" toggle_show_status: toggle whether to show the status of the midges after synchronisation")
    print(" exit: stop and exit the hub script")
    print(" help: prints this help message")
    sys.stdout.flush()

if __name__ == "__main__":
    sync_frequency = 10.0 # How frequent the synchronisation is triggered, defaults to every 10 seconds
    show_status_on_sync = True # Show the status of the midge after synchronisation

    df = pd.read_csv('sample_mapping_file.csv')
    do_synchronization = False
    print("Type help for a list commands")
    sys.stdout.flush()
    ti = timeout_input(poll_period=0.05)

    def ti_input(prompt):
        return ti.input(prompt=prompt, timeout=sync_frequency,
                     extend_timeout_with_input=False, require_enter_to_confirm=True)
    while True:
        command = ti_input(prompt='> ')

        if command == "start_all":
            if do_synchronization is True:
                print("Devices are already recording.")
                sys.stdout.flush()
            else:
                start_recording_all_devices(df)
                do_synchronization = True
        elif command == "stop_all":
            if do_synchronization is False:
                print("Devices are not recording.")
                sys.stdout.flush()
            else:
                do_synchronization = False
                stop_recording_all_devices(df)
        elif command == "erase_all":
            if do_synchronization is True:
                print("Devices are recording, will not erase.")
            else:
                erase_sdcard_all_devices(df)
        elif command == "fw_all":
            print_fw_version_all_devices(df)
        elif command == "help":
            print_hub_commands()
            sys.stdout.flush()
        elif command == "midge":
            print('Type the id of the Midge you want to connect or exit.')
            sys.stdout.flush()

            while True:
                command = ti_input(prompt='Midge Connection >')

                if command == "":
                    if do_synchronization is True:
                        synchronise_and_check_all_devices(df, show_status=show_status_on_sync)
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
                    print ("Connected to the midge. For available commands, type help.")
                    while True:
                        command = ti_input(prompt='Midge: ' + str(midge_id) + ' >')
                        
                        if command == "exit":
                            cur_connection.disconnect()
                            print("Midge disconnected")
                            sys.stdout.flush()
                            break
                        elif command == "":
                            if do_synchronization is True:
                                synchronise_and_check_all_devices(df,
                                                                  skip_id=midge_id,
                                                                  conn_skip_id=cur_connection,
                                                                  show_status=show_status_on_sync)
                        elif command != "":
                            try:
                                command_args = command.split(" ")
                                out = choose_function(cur_connection, command_args[0])
                                if out is not None:
                                    print (out)
                                    sys.stdout.flush()
                            except Exception as error:
                                print (str(error))
                                print("Command not found!")
                                sys.stdout.flush()
                                cur_connection.print_help()
                                continue
        elif command == "toggle_show_status":
            show_status_on_sync = not show_status_on_sync
            print("Show status on synchronisation: " + str(show_status_on_sync))
            sys.stdout.flush()
        elif command == "exit":
            print("Exit hub script.")
            sys.stdout.flush()
            if do_synchronization:
                do_synchronization = False
                stop_recording_all_devices(df)
            quit(0)
        elif command == "":
            if do_synchronization is True:
                synchronise_and_check_all_devices(df, show_status=show_status_on_sync)
        else:
            print('Unknown command. Type help for a list of valid commands.')
            sys.stdout.flush()
