import requests
import json
import random
import time
from fake_useragent import UserAgent
import uuid
import os

# Initialize UserAgent for randomizing headers
ua = UserAgent()

# Headers template
def get_headers():
    return {
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "application/json, text/plain, */*",
        "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
        "Content-Type": "text/plain",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": ua.random,
        "Origin": "https://89atm.me",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://89atm.me/",
        "Accept-Encoding": "gzip, deflate, br",
        "Priority": "u=1, i"
    }

# Read numbers from a file (one per line)
def read_numbers(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: {file_path} not found")
        return []

# Read existing sent data from sent.json
def read_sent_data():
    try:
        if os.path.exists('sent.json'):
            with open('sent.json', 'r') as file:
                return json.load(file)
        return []
    except Exception as e:
        print(f"Error reading sent.json: {str(e)}")
        return []

# Write to sent.json
def write_sent_data(data):
    try:
        with open('sent.json', 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error writing to sent.json: {str(e)}")

# Main automation function
def automate_task():
    # Read account numbers and ws_account numbers
    acc_numbers = read_numbers('acc.txt')
    ws_numbers = read_numbers('num.txt')
    sent_data = read_sent_data()
    
    if not acc_numbers:
        print("No account numbers found in acc.txt")
        return
    
    if not ws_numbers:
        print("No ws_account numbers found in num.txt")
        return

    # API endpoints
    login_url = "https://api.89atm.me/login/login"
    page_url = "https://api.89atm.me/taskhosting/page"
    ws_code_url = "https://api.89atm.me/task/getwswebcode"

    for acc_number in acc_numbers:
        print(f"\nProcessing account: {acc_number}")
        
        # Step 1: Login
        login_payload = {
            "code": 86,
            "user_name": acc_number,
            "pwd": "5d766ecabec5fc44b9d14bd20e843580",
            "autologin": False,
            "lang": "",
            "device": "",
            "mac": "",
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }
        
        try:
            response = requests.post(login_url, headers=get_headers(), data=json.dumps(login_payload))
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and data.get("msg") == "success":
                    token = data["data"]["token"]
                    print(f"Login successful for {acc_number}.")
                else:
                    print(f"Login failed for {acc_number}: {data.get('msg')}")
                    continue
            else:
                print(f"Login request failed for {acc_number}: HTTP {response.status_code}")
                continue
        except Exception as e:
            print(f"Error during login for {acc_number}: {str(e)}")
            continue

        # Step 2: Check online status
        page_payload = {
            "page": 1,
            "limit": 8,
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }
        
        try:
            page_url_with_token = f"{page_url}?token={token}"
            response = requests.post(page_url_with_token, headers=get_headers(), data=json.dumps(page_payload))
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and data.get("msg") == "success":
                    for item in data["data"]["data"]:
                        if item.get("status") == 1:
                            print(f"Account {acc_number} is already online with ws_account: {item['ws_account']}")
                            break
                    else:
                        print(f"Account {acc_number} is not online. Proceeding to submit ws_account.")
                        # Step 3: Try submitting ws_account numbers
                        for ws_account in ws_numbers[:]:  # Create a copy to avoid modifying while iterating
                            ws_payload = {
                                "ws_account": ws_account,
                                "httpRequestIndex": 0,
                                "httpRequestCount": 0
                            }
                            try:
                                ws_url_with_token = f"{ws_code_url}?token={token}"
                                response = requests.post(ws_url_with_token, headers=get_headers(), data=json.dumps(ws_payload))
                                if response.status_code == 200:
                                    ws_data = response.json()
                                    if ws_data.get("code") == 0 and ws_data.get("msg") == "success":
                                        print(f"Successfully submitted ws_account {ws_account}. Code: {ws_data['data']['code']}")
                                        # Add to sent_data
                                        sent_data.append({
                                            "account": acc_number,
                                            "ws_account": ws_account,
                                            "code": ws_data['data']['code']
                                        })
                                        # Remove used number from ws_numbers
                                        ws_numbers.remove(ws_account)
                                        # Update num.txt
                                        with open('num.txt', 'w') as f:
                                            f.write('\n'.join(ws_numbers))
                                        # Update sent.json
                                        write_sent_data(sent_data)
                                        break  # Move to next account after successful submission
                                    else:
                                        print(f"Failed to submit ws_account {ws_account}: {ws_data.get('msg')}")
                                        if ws_data.get("code") == 10052:
                                            print("Waiting 5 seconds due to rate limit...")
                                            time.sleep(5)
                                else:
                                    print(f"WS request failed for {ws_account}: HTTP {response.status_code}")
                            except Exception as e:
                                print(f"Error submitting ws_account {ws_account}: {str(e)}")
                else:
                    print(f"Failed to check online status for {acc_number}: {data.get('msg')}")
            else:
                print(f"Page request failed for {acc_number}: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error checking online status for {acc_number}: {str(e)}")

if __name__ == "__main__":
    automate_task()