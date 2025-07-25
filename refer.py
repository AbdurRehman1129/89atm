import requests
import json
import random
import string
import time
import hashlib
import os
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class WhatsAppAccountManager:
    def __init__(self):
        self.base_url = "https://api.89atm.me"
        self.session = requests.Session()
        self.password_hash = None

    def generate_fake_user_agent(self):
        """Generate a fake user agent with randomized browser/engine"""
        chrome_versions = ['138.0.0.0', '137.0.0.0', '136.0.0.0', '135.0.0.0']
        windows_versions = ['10.0', '11.0']
        macos_versions = ['10_15_7', '11_6', '12_6', '13_5']
        linux_versions = ['x86_64', 'i686']

        engines = [
            {
                'name': 'Chrome',
                'templates': [
                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",
                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",
                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36"
                ]
            }
        ]
        return random.choice(engines[0]['templates'])

    def get_headers(self):
        """Get headers with fake user agent"""
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'text/plain',
            'Origin': 'https://89atm.me',
            'Referer': 'https://89atm.me/',
            'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.generate_fake_user_agent(),
            'Connection': 'keep-alive',
            'Priority': 'u=1, i'
        }

    def load_password(self):
        """Load password from pwd.txt"""
        try:
            with open('pwd.txt', 'r') as f:
                password = f.read().strip()
                self.password_hash = hashlib.md5(password.encode()).hexdigest()
                if not password:
                    raise ValueError("Password file is empty")
                return True
        except FileNotFoundError:
            print("Error: pwd.txt file not found")
            return False
        except Exception as e:
            print(f"Error reading password: {e}")
            return False

    def login(self, username):
        """Login to account and return token"""
        url = f"{self.base_url}/login/login"
        headers = self.get_headers()
        
        payload = {
            "code": 86,
            "user_name": username,
            "pwd": self.password_hash,
            "autologin": False,
            "lang": "",
            "device": "",
            "mac": "",
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if data.get('code') == 0:
                token = data['data']['token']
                print(f"✓ Login successful for {username}")
                return token
            else:
                print(f"✗ Login failed for {username}: {data.get('msg', 'Unknown error')}")
                return None
        except Exception as e:
            print(f"✗ Login error for {username}: {e}")
            return None

    def check_numbers_status(self, token):
        """Check if any numbers are online"""
        url = f"{self.base_url}/taskhosting/page?token={token}"
        headers = self.get_headers()
        
        payload = {
            "page": 1,
            "limit": 8,
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if data.get('code') == 0:
                numbers_data = data.get('data', {}).get('data', [])
                
                if not numbers_data:
                    print("  No numbers linked to this account")
                    return "no_numbers"
                
                online_count = sum(1 for num in numbers_data if num.get('status') == 1)
                offline_count = sum(1 for num in numbers_data if num.get('status') == 2)
                
                print(f"  Found {len(numbers_data)} numbers: {online_count} online, {offline_count} offline")
                
                return "has_online" if online_count > 0 else "all_offline"
            else:
                print(f"  Error checking numbers: {data.get('msg', 'Unknown error')}")
                return "error"
        except Exception as e:
            print(f"  Error checking numbers: {e}")
            return "error"

    def check_balance(self, username, token):
        """Check balance for account"""
        url = f"{self.base_url}/member/index?token={token}"
        headers = self.get_headers()
        
        payload = {
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if data.get('code') == 0:
                point = data['data'].get('point', 0)
                balance = point / 10000
                user_code = data['data'].get('user_code', 'N/A')
                print(f"  ✓ Balance for {username}: {balance:.2f}")
                print(f"  ✓ Referral Code: {user_code}")
                return balance, user_code
            else:
                print(f"  ✗ Failed to check balance for {username}: {data.get('msg', 'Unknown error')}")
                return None, None
        except Exception as e:
            print(f"  ✗ Error checking balance for {username}: {e}")
            return None, None

    def check_referral_stats(self, token):
        """Check referral statistics including number of referred accounts"""
        url = f"{self.base_url}/agent/share?token={token}"
        headers = self.get_headers()
        
        payload = {
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if data.get('code') == 0:
                under_num = data['data'].get('under_num', 0)
                team_num = data['data'].get('team_num', 0)
                print(f"  ✓ Current referrals: {under_num} direct referrals, {team_num} total team members")
                return under_num, team_num
            else:
                print(f"  ✗ Failed to check referral stats: {data.get('msg', 'Unknown error')}")
                return None, None
        except Exception as e:
            print(f"  ✗ Error checking referral stats: {e}")
            return None, None

    def check_existing_accounts_file(self, user_code):
        """Check if accounts file exists for the given referral code"""
        account_folder = "accounts"
        output_file = os.path.join(account_folder, f"{user_code}.txt")
        
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    lines = f.readlines()
                    print(f"  ✓ Existing accounts file found: {output_file} with {len(lines)} accounts")
                    return True, len(lines)
            except Exception as e:
                print(f"  ✗ Error reading existing accounts file: {e}")
                return True, 0
        return False, 0

    def generate_random_phone(self):
        """Generate random phone number"""
        return "0345" + ''.join(random.choices(string.digits, k=7))

    def create_account(self, user_code, desired_successful_accounts):
        """Create accounts using referral code"""
        url = f"{self.base_url}/login/register"
        success_count = 0
        account_folder = "accounts"
        if not os.path.exists(account_folder):
            os.makedirs(account_folder)
        
        output_file = os.path.join(account_folder, f"{user_code}.txt")
        
        while success_count < desired_successful_accounts:
            phone = self.generate_random_phone()
            headers = self.get_headers()
            
            payload = {
                "user_name": phone,
                "mobile": "+234",
                "pwd": self.password_hash,
                "user_code": user_code,
                "autologin": False,
                "os": 2
            }
            
            try:
                response = self.session.post(
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
                    
            except Exception as e:
                print(f"Error creating account: {e}")
                time.sleep(random.uniform(1, 3))
        
        print(f"\nCompleted: {success_count} accounts created successfully")
        print(f"Accounts saved to: {output_file}")

    def run(self):
        """Main execution function"""
        print("WhatsApp Account Manager")
        print("=" * 40)
        
        if not self.load_password():
            return
        
        username = input("Enter username: ").strip()
        token = self.login(username)
        if not token:
            print("Exiting due to login failure")
            return
        
        status = self.check_numbers_status(token)
        print(f"Account status: {status}")
        
        balance, user_code = self.check_balance(username, token)
        if balance is None:
            print("Exiting due to balance check failure")
            return
        
        # Check referral stats
        under_num, team_num = self.check_referral_stats(token)
        if under_num is None:
            print("Exiting due to referral stats check failure")
            return
        
        # Check for existing accounts file
        file_exists, existing_count = self.check_existing_accounts_file(user_code)
        
        while True:
            choice = input("\nDo you want to create accounts using this referral code? (y/n): ").lower()
            if choice in ['y', 'yes']:
                try:
                    num_accounts = int(input("Enter number of accounts to create: "))
                    if num_accounts <= 0:
                        print("Please enter a positive number")
                        continue
                    self.create_account(user_code, num_accounts)
                    break
                except ValueError:
                    print("Please enter a valid number")
                    continue
            elif choice in ['n', 'no']:
                print("Script completed. Goodbye!")
                break
            else:
                print("Please enter 'y' or 'n'")

if __name__ == "__main__":
    manager = WhatsAppAccountManager()
    manager.run()