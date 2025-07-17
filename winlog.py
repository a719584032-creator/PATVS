import win32evtlog
import datetime
import wmi


def get_usb_devices():
    # 连接到WMI服务
    c = wmi.WMI()
    # 查询与USB相关的设备信息
    usb_devices = c.Win32_USBControllerDevice()

    result = []
    for device in usb_devices:
        # 获取设备信息
        antecedent = device.Dependent
        device_info = {
            "DeviceID": antecedent.DeviceID,
            "PNPDeviceID": antecedent.PNPDeviceID,
            "Description": antecedent.Description,
            "Name": antecedent.Name
        }
        result.append(device_info)

    return result


def read_event_log():
    # Open the "System" event log
    hand = win32evtlog.OpenEventLog(None, "System")
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

    print("Start reading event log")
    num = 0
    try:
        while True:
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            if not events:
                break  # If no more events, break the loop
            num += 1
            for event in events:
                # Print details of each event for debugging purposes
                event_id = event.EventID & 0xFFFF  # Mask the EventID to get the actual value
  #              print(f"EventID: {event_id}, Source: {event.SourceName}, TimeGenerated: {event.TimeGenerated}")

                if event_id == 1074:
                    print("Found event with ID 1074")
                    print(
                        f"Event details: EventID: {event_id}, Source: {event.SourceName}, TimeGenerated: {event.TimeGenerated}")
  #                  return  # Exit the function once the target event is found

            # Continue to the next chunk of events
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        win32evtlog.CloseEventLog(hand)
    print(num)
    print("Target event not found in the specified range.")


if __name__ == "__main__":
    read_event_log()
    # now = datetime.now()

    # devices = get_usb_devices()
    # for device in devices:
    #     print(f"DeviceID: {device['DeviceID']}")
    #     print(f"PNPDeviceID: {device['PNPDeviceID']}")
    #     print(f"Description: {device['Description']}")
    #     print(f"Name: {device['Name']}\n")