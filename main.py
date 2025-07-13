import requests
import json
import random
import string
import time
import ssl
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def generate_random_phone():
    phone = "0345" + ''.join(random.choices(string.digits, k=7))
    return phone

def generate_random_user_agent():
    browsers = [
        'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{0}.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 11; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{0}.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 12; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{0}.0.0.0 Mobile Safari/537.36'
    ]
    chrome_version = random.randint(100, 120)
    browser = random.choice(browsers)
    return browser.format(chrome_version)

def create_account(user_code, pwd, desired_successful_accounts):
    url = "https://api.89atm.me/login/register"
    success_count = 0
    output_file = f"{user_code}.txt"
    
    while success_count < desired_successful_accounts:
        phone = generate_random_phone()
        headers = {
            "Host": "api.89atm.me",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": generate_random_user_agent(),
            "Origin": "https://89atm.me",
            "Referer": "https://89atm.me/"
        }
        
        payload = {
            "user_name": phone,
            "mobile": "+234",
            "pwd": pwd,
            "user_code": user_code,
            "autologin": False,
            "os": 2
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("code") == 0 and response_data.get("msg") == "success":
                    success_count += 1
                    with open(output_file, "a") as f:
                        f.write(f"{phone}\n")
                    print(f"Account created with username {phone} (Success {success_count}/{desired_successful_accounts})")
            
            time.sleep(random.uniform(2, 4))
                
        except Exception:
            time.sleep(random.uniform(1, 3))
    
    print(f"\nCompleted: {success_count} accounts created successfully")
    print(f"Accounts saved to: {output_file}")

def main():
    user_code = input("Enter referral code (user_code): ").strip()
    try:
        desired_successful_accounts = int(input("Enter number of successful accounts desired: "))
        if desired_successful_accounts <= 0:
            print("Please enter a positive number")
            return
    except ValueError:
        print("Please enter a valid number")
        return
    
    pwd = "34a5a022276e193232f3d9791726c88d"
    
    create_account(user_code, pwd, desired_successful_accounts)

if __name__ == "__main__":
    main()