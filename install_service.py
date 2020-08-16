"""Install DHT MQTT as a service."""
import argparse
import os


if __name__ == "__main__":
    # Project folder
    folder = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Install DHT MQTT as a service"
    )

    parser.add_argument(
        "--filepath-pattern",
        default="%{filepath}",
        help="Pattern to fill in the file path of the main script"
    )
    parser.add_argument("--main-script", help="Location of the main script")
    parser.add_argument(
        "--python-executable-pattern",
        default="%{python}",
        help="Pattern to fill in the python executable to use"
    )
    parser.add_argument(
        "--python-executable",
        default="python3",
        help="Python executable to use"
    )
    parser.add_argument(
        "--service-file",
        default=os.path.join(folder, "dht_mqtt.service"),
        help="Location of the service file"
    )
    parser.add_argument(
        "--service-file-destination",
        default="/etc/systemd/system/",
        help="Place to put the service file"
    )
    args = parser.parse_args()
    if args.main_script is None:
        main_file = os.path.join(folder, "main.py")
    else:
        main_file = os.path.abspath(args.main_script)

    # Load the service file and replace the python executable and path
    with open(args.service_file) as fp:
        service_content = fp.read()
    service_content = service_content\
        .replace(args.filepath_pattern, main_file)\
        .replace(args.python_executable_pattern, args.python_executable)

    # Write the filled in service file to the correct destination
    if os.path.isdir(args.service_file_destination):
        service_filename = os.path.basename(args.service_file)
        destination = os.path.join(
            args.service_file_destination,
            service_filename
        )
    else:
        destination = args.service_file_destination
    with open(destination, "w") as fp:
        fp.write(service_content)
