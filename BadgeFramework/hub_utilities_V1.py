from hub_connection_V1 import Connection
import sys
import tty
import termios
import logging
import time


def get_logger(name):
    log_format = '%(asctime)s  %(name)8s  %(levelname)5s  %(message)s'
    logging.basicConfig(level=logging.DEBUG,
                        format=log_format,
                        filename='data_collection.log',
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter(log_format))
    logging.getLogger(name).addHandler(console)
    return logging.getLogger(name)

logger = get_logger("hub_utilities")

def choose_function(connection, input):
    chooser = {
        "help": connection.print_help,
        "status": connection.handle_status_request,
        "start_all_sensors": connection.start_recording_all_sensors,
        "stop_all_sensors": connection.stop_recording_all_sensors,
        "start_microphone": connection.handle_start_microphone_request,
        "stop_microphone": connection.handle_stop_microphone_request,
        "start_scan": connection.handle_start_scan_request,
        "stop_scan": connection.handle_stop_scan_request,
        "start_imu": connection.handle_start_imu_request,
        "stop_imu": connection.handle_stop_imu_request,
        "identify": connection.handle_identify_request,
        "restart": connection.handle_restart_request,
        "get_free_space": connection.handle_get_free_space,
    }
    logger.info(f"Following command is inputted:{input}")
    func = chooser.get(input, lambda: "Invalid command!")
    try:
        out = func()
        return out
    except Exception as error:
        logger.info(f"Following error is occurred as a result of the command {input}:"
                    + f"{error}")
        print(error)
        return


def start_recording_all_devices(df):
    for _, row in df.iterrows():
        current_participant = row["Participant Id"]
        current_mac = row["Mac Address"]
        try:
            cur_connection = Connection(current_participant, current_mac)
        except Exception as error:
            logger.info(f"Couldn't connect to the following midge:{current_participant}"
            + f" with error:{error}, sensors are not started.")
            print(str(error) + ", sensors are not started.")
            continue
        try:
            cur_connection.set_id_at_start()
            cur_connection.start_recording_all_sensors()
            cur_connection.disconnect()
        except Exception as error:
            logger.info(f"Connection established for midge:{current_participant}, but "
                        + f"following error occurred:{error}.")
            print(error)
            cur_connection.disconnect()


def stop_recording_all_devices(df):
    for _, row in df.iterrows():
        current_participant = row["Participant Id"]
        current_mac = row["Mac Address"]
        try:
            cur_connection = Connection(current_participant, current_mac)
        except Exception as error:
            logger.info(f"Couldn't connect to the following midge:{current_participant}"
            + f" with error:{error}, sensors are not stopped.")            
            print(str(error) + ", sensors are not stopped.")
            continue
        try:
            cur_connection.stop_recording_all_sensors()
            cur_connection.disconnect()
        except Exception as error:
            logger.info(f"Connection established for midge:{current_participant}, but "
                        + f"following error occurred:{error}.")            
            print(str(error))
            cur_connection.disconnect()


def synchronise_and_check_all_devices(df):
    for _, row in df.iterrows():
        current_participant = row["Participant Id"]
        current_mac = row["Mac Address"]
        try:
            cur_connection = Connection(current_participant, current_mac)
        except Exception as error:
            logger.info(f"Couldn't connect to the following midge:{current_participant}"
            + f" with error:{error}, cannot synchronise.")                   
            print(str(error) + ", cannot synchronise.")
            sys.stdout.flush()
            continue
        try:
            out = cur_connection.handle_status_request()
            logger.info(f"Status received for the following midge:{current_participant}.")               
            if out.imu_status == 0:
                print(
                    "IMU is not recording for participant " + str(current_participant)
                )
                logger.info(f"IMU is not recording for participant" 
                            + f" {current_participant}.")   
            if out.microphone_status == 0:
                print(
                    "Mic is not recording for participant " + str(current_participant)
                )
                logger.info(f"Mic is not recording for participant" 
                            + f" {current_participant}.")   
            if out.scan_status == 0:
                print(
                    "Scan is not recording for participant " + str(current_participant)
                )
                logger.info(f"Scan is not recording for participant" 
                            + f" {current_participant}.") 
            if out.clock_status == 0:
                print("Cant synch for participant " + str(current_participant))
                logger.info(f"Cant synch for participant" 
                            + f" {current_participant}.") 
            sys.stdout.flush()
            cur_connection.disconnect()
        except Exception as error:
            logger.info(f"Status check for participant {current_participant} returned " 
                + f" the following error: {error}.")     
            print(error)
            sys.stdout.flush()
            cur_connection.disconnect()


class timeout_input(object):
    def __init__(self, poll_period=0.05):
        self.poll_period = poll_period

    def _getch_nix(self):
        from select import select

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            [i, _, _] = select([sys.stdin.fileno()], [], [], self.poll_period)
            if i:
                ch = sys.stdin.read(1)
            else:
                ch = ""
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def input(
        self,
        prompt=None,
        timeout=None,
        extend_timeout_with_input=True,
        require_enter_to_confirm=True,
    ):
        prompt = prompt or ""
        sys.stdout.write(prompt)
        sys.stdout.flush()
        input_chars = []
        start_time = time.time()
        received_enter = False
        while (time.time() - start_time) < timeout:
            c = self._getch_nix()
            if c in ("\n", "\r"):
                received_enter = True
                break
            elif c:
                input_chars.append(c)
                sys.stdout.write(c)
                sys.stdout.flush()
                if extend_timeout_with_input:
                    start_time = time.time()
        sys.stdout.write("\n")
        sys.stdout.flush()
        captured_string = "".join(input_chars)
        if require_enter_to_confirm:
            return_string = captured_string if received_enter else ""
        else:
            return_string = captured_string
        return return_string
