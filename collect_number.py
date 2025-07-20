import os
import re

# Define the pattern for 11-digit phone numbers starting with 0345
phone_pattern = r'0345\d{7}\b'

# Set to store unique phone numbers
unique_numbers = set()

# Get the current working directory
folder_path = os.getcwd()

# Iterate through all files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.txt') and filename != 'acc.txt':
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Find all matches in the file
                matches = re.findall(phone_pattern, content)
                # Add matches to the set
                unique_numbers.update(matches)
        except Exception as e:
            print(f"Error reading {filename}: {e}")

# Write unique phone numbers to acc.txt
try:
    with open('acc.txt', 'w', encoding='utf-8') as output_file:
        for number in sorted(unique_numbers):
            output_file.write(number + '\n')
    print(f"Found {len(unique_numbers)} unique phone numbers. Saved to acc.txt")
except Exception as e:
    print(f"Error writing to acc.txt: {e}")