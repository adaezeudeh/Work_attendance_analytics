import csv
from collections import defaultdict
from datetime import datetime, timedelta
from operator import itemgetter
import os

def get_data(file_path):
    """Reads the CSV file and returns the data."""
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        data = list(reader)
    
    """Filters data for February."""
    february_data = [entry for entry in data if entry['event_time'].startswith('2023-02')]

    return february_data


def process_time_entries(data):
    """Processes time entries to calculate time spent and days present for each user.
    Returns:
    - user_data (defaultdict): Dictionary containing user data with time spent, days present, and last action."""

    # Initialize a dictionary to store user-related information
    user_data = defaultdict(lambda: {'time': 0.0, 'days': set(), 'last_action': None})

    for entry in data:
        try:
            user_id = entry.get('user_id') 
            timestamp = datetime.strptime(entry.get('event_time'), '%Y-%m-%dT%H:%M:%S.%fZ') 

            action = entry.get('event_type').upper()  # Get and convert action to uppercase

            if user_id and timestamp and action:  # Ensure all necessary data exists
                if user_data[user_id]['last_action'] is None:
                    user_data[user_id]['last_action'] = (action, timestamp)
                else:
                    last_action, last_timestamp = user_data[user_id]['last_action']
                    if last_action == 'GATE_IN' and action == 'GATE_OUT':
                        time_spent = (timestamp - last_timestamp).total_seconds() / 3600
                        user_data[user_id]['time'] += time_spent
                        user_data[user_id]['days'].add(timestamp.date())
                    user_data[user_id]['last_action'] = (action, timestamp)
            else:
                # Handle incomplete or missing data in the entry
                print(f"Issue with entry: {entry}. Missing or incomplete data.")
        except (ValueError, KeyError) as e:
            # Handle potential errors in datetime parsing or missing keys in the entry
            print(f"Error processing entry: {entry}. Reason: {e}")

    return user_data

def calculate_average_and_rank(user_data):
    """Calculates average time per day and ranks users based on average.
    Returns:
    - ranked_result (list): List of tuples containing user ranking based on average time spent in office per day."""
    
    def calculate_average(values):
        """Calculates the average time per day for a user.
        Returns:
        - float: Average time spent in office per day."""
       
        days_present = len(values['days'])
        return round(values['time'] / days_present, 2) if days_present else 0

    # Calculate average time per day for each user
    result = []
    for user_id, values in user_data.items():
        average_per_day = calculate_average(values)
        result.append((user_id, values['time'], len(values['days']), average_per_day))

    # Rank users based on average_per_day
    result.sort(key=itemgetter(3), reverse=True)
    ranked_result = [(user[0], user[1], user[2], user[3], index + 1) for index, user in enumerate(result)]

    return ranked_result


def find_longest_work_session(data):
    """Finds the user with the longest work session and the corresponding session length.
    Returns:
    - tuple: (user_with_max_time, max_session_time)
    """
    activity_per_user = defaultdict(list)

    for entry in data:
        user_id = entry.get('user_id')
        timestamp = datetime.strptime(entry.get('event_time'), '%Y-%m-%dT%H:%M:%S.%fZ')
        action = entry.get('event_type').upper()  # Get and convert action to uppercase
        activity_per_user[user_id].append((timestamp, action))

    def calculate_sessions(timestamps_action):
        """Calculate work sessions based on user actions. Factors in condition where break is over 2 hours it counts as aa new session.
        Returns:
        - list: List of work session start and end timestamps."""

        session_lengths = []
        start_time, last_out_time = None, None

        for timestamp, action in timestamps_action:
            if action == "GATE_IN":
                if start_time is not None:
                    time_diff = timestamp - last_out_time if last_out_time else None
                    if time_diff and time_diff >= timedelta(hours=2):
                        session_lengths.append((start_time, last_out_time))
                        start_time = timestamp
                else:
                    start_time = timestamp
            elif action == "GATE_OUT":
                last_out_time = timestamp

        if start_time is not None and last_out_time is not None:
            session_lengths.append((start_time, last_out_time))

        return session_lengths

    def get_max_session_time(session_times):
        """Calculate the maximum session time from all the sessions.
        Returns:
        - float: Maximum session time in seconds."""
        return max(map(lambda x: (x[1] - x[0]).total_seconds(), session_times), default=0)

    max_session_time = 0
    user_with_max_time = None

    for user_id, timestamps_action in activity_per_user.items():
        session_lengths = calculate_sessions(timestamps_action)
        max_time_for_user = get_max_session_time(session_lengths)
        if max_time_for_user > max_session_time:
            max_session_time = max_time_for_user
            user_with_max_time = user_id

    return user_with_max_time, max_session_time


def write_to_csv(file_path, header, data):
    """Writes output data to a CSV file."""
    output_directory = 'output'
    os.makedirs(output_directory, exist_ok=True)


    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)

        if isinstance(data, list):
            writer.writerows(data)  # For multiple rows
        else:
            writer.writerow(data)


def main():
    # Step 1: Read the CSV file
    file_path = 'Data/datapao_homework_2023.csv'
    february_data = get_data(file_path)

    # Step 2: Process time entries
    user_data = process_time_entries(february_data)
    
    # Step 3: Calculate average and rank users
    ranked_result = calculate_average_and_rank(user_data)

    # Step 4: Write results to the first CSV file
    first_csv_path = 'output/first.csv'
    first_csv_header = ['user_id', 'time', 'days', 'average_per_day', 'rank']
    write_to_csv(first_csv_path, first_csv_header, ranked_result)

    # Step 5: Find the longest work session
    longest_session_user = find_longest_work_session(february_data)

    # Step 6: Write results to the second CSV file
    second_csv_path = 'output/second.csv'
    second_csv_header = ['user_id', 'session_length']
    write_to_csv(second_csv_path, second_csv_header, longest_session_user)


if __name__ == "__main__":
    main()