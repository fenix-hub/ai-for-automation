import os
import curses
import xml.etree.ElementTree as ET

def update_route_file():
    # Read the XML file
    tree = ET.parse('sim.sumocfg')
    root = tree.getroot()

    def get_cluster_number():
        def menu(stdscr):
            curses.curs_set(0)
            curses.echo()
            stdscr.addstr("Enter the cluster number: ")
            cluster_number = stdscr.getstr().decode('utf-8')
            return int(cluster_number)

        return curses.wrapper(menu)

    cluster = get_cluster_number()

    def get_user_choice(options):
        def menu(stdscr):
            curses.curs_set(0)
            current_row = 0

            while True:
                stdscr.clear()
                stdscr.addstr("Select a time range:\n")
                for idx, (key, value) in enumerate(options.items()):
                    if idx == current_row:
                        stdscr.addstr(f"> {key}: {value}\n", curses.A_REVERSE)
                    else:
                        stdscr.addstr(f"  {key}: {value}\n")
                stdscr.refresh()

                key = stdscr.getch()

                if key == curses.KEY_UP and current_row > 0:
                    current_row -= 1
                elif key == curses.KEY_DOWN and current_row < len(options) - 1:
                    current_row += 1
                elif key == curses.KEY_ENTER or key in [10, 13]:
                    return list(options.keys())[current_row]

        return curses.wrapper(menu)

    # Display options to the user and get user input
    options = {
        "1": "07:00-10:00",
        "2": "13:00-15:00",
        "3": "18:00-21:00"
    }
    choice = get_user_choice(options)

    # Validate user input
    if choice not in options:
        print("Invalid choice. Exiting.")
        return

    # Get the selected time range
    selected_range = options[choice]
    start_time, end_time = selected_range.split('-')
    start_time = start_time.replace(':', '-')
    end_time = end_time.replace(':', '-')
    route_file_value = f"traffic_flows_data/cluster_{cluster}/route_{start_time}_{end_time}.xml"

    # Update the <route-files> value
    for route_files in root.findall(".//route-files"):
        route_files.set('value', route_file_value)

    # Save the modified XML file
    tree.write('sim.sumocfg', encoding='utf-8', xml_declaration=True)
    print(f"Updated <route-files> value to '{route_file_value}'")

# Run the function
update_route_file()

# run this command from shell 'sumo-gui -c sim.sumocfg --max-depart-delay 1000 --ignore-route-errors'
os.system('sumo-gui -c sim.sumocfg --max-depart-delay 1000 --ignore-route-errors')