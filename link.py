import requests
import json
import time
import random
import hashlib
from datetime import datetime
import os

class WhatsAppLinker:
    def __init__(self):
        self.base_url = "https://api.89atm.me"
        self.session = requests.Session()
        self.accounts = []
        self.passwords = []
        self.numbers = []
        self.sent_codes = []
        self.signed_in_accounts = {}  # Track accounts that have signed in today
        
    def generate_fake_user_agent(self):
        """Generate a fake user agent with randomized browser/engine"""
        chrome_versions = ['138.0.0.0', '137.0.0.0', '136.0.0.0', '135.0.0.0']
        firefox_versions = ['120.0', '119.0', '118.0', '117.0']
        edge_versions = ['118.0.2088.46', '117.0.2045.31', '116.0.1938.62']
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
            },
            {
                'name': 'Firefox',
                'templates': [
                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64; rv:{random.choice(firefox_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)}",
                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}; rv:{random.choice(firefox_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)}",
                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}; rv:{random.choice(firefox_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)}"
                ]
            },
            {
                'name': 'Edge',
                'templates': [
                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)}",
                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)}"
                ]
            }
        ]
        selected_browser = random.choice(engines)
        return random.choice(selected_browser['templates'])

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
    
    def load_files(self):
        """Load accounts, passwords, numbers, and signed-in accounts from files"""
        try:
            with open('acc.txt', 'r') as f:
                self.accounts = [line.strip() for line in f.readlines() if line.strip()]
            
            with open('pwd.txt', 'r') as f:
                password = f.read().strip()
                self.password_hash = hashlib.md5(password.encode()).hexdigest()
            
            with open('num.txt', 'r') as f:
                self.numbers = [line.strip() for line in f.readlines() if line.strip()]
            
            if os.path.exists('send.json'):
                with open('send.json', 'r') as f:
                    self.sent_codes = json.load(f)
            else:
                self.sent_codes = []
                
            # Load signed-in accounts if file exists
            if os.path.exists('signed_in.json'):
                with open('signed_in.json', 'r') as f:
                    self.signed_in_accounts = json.load(f)
            else:
                self.signed_in_accounts = {}
                
        except FileNotFoundError as e:
            print(f"Error: Required file not found - {e}")
            exit(1)
    
    def save_sent_codes(self):
        """Save sent codes to JSON file"""
        with open('send.json', 'w') as f:
            json.dump(self.sent_codes, f, indent=2)
    
    def save_signed_in_accounts(self):
        """Save signed-in accounts to JSON file"""
        with open('signed_in.json', 'w') as f:
            json.dump(self.signed_in_accounts, f, indent=2)
    
    def save_numbers_to_file(self):
        """Save updated numbers list back to file"""
        with open('num.txt', 'w') as f:
            for number in self.numbers:
                f.write(number + '\n')
    
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
                uid = data['data']['uid']
                print(f"✓ Login successful for {username}")
                return token, uid
            else:
                print(f"✗ Login failed for {username}: {data.get('msg', 'Unknown error')}")
                return None, None
                
        except Exception as e:
            print(f"✗ Login error for {username}: {e}")
            return None, None
    
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
                
                if online_count > 0:
                    return "has_online"
                else:
                    return "all_offline"
            else:
                print(f"  Error checking numbers: {data.get('msg', 'Unknown error')}")
                return "error"
                
        except Exception as e:
            print(f"  Error checking numbers: {e}")
            return "error"
    
    def sign_in_for_reward(self, token, username):
        """Attempt to sign in for daily reward"""
        # Check if account already signed in today
        current_date = datetime.now().strftime('%Y-%m-%d')
        if username in self.signed_in_accounts and self.signed_in_accounts[username] == current_date:
            print(f"  ℹ Account {username} already signed in today")
            return True
        
        url = f"{self.base_url}/activity/signin?token={token}"
        headers = self.get_headers()
        
        payload = {
            "year": datetime.now().year,
            "month": datetime.now().month,
            "day": datetime.now().day,
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            if data.get('code') == 0:
                print(f"  ✓ Successfully signed in for daily reward for {username}")
                self.signed_in_accounts[username] = current_date
                self.save_signed_in_accounts()
                return True
            elif data.get('code') == 10072:
                print(f"  ℹ Account {username} already signed in today.")
                self.signed_in_accounts[username] = current_date
                self.save_signed_in_accounts()
                return True
            else:
                print(f"  ✗ Failed to sign in for daily reward for {username}: {data.get('msg', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"  ✗ Error signing in for daily reward for {username}: {e}")
            return False
    
    def get_linking_code(self, token, number, max_retries=10):
        """Get linking code for a number"""
        url = f"{self.base_url}/task/getwswebcode?token={token}"
        headers = self.get_headers()
        
        payload = {
            "ws_account": number,
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }
        
        for attempt in range(max_retries):
            try:
                print(f"    Attempt {attempt + 1}/{max_retries} for number {number}")
                response = self.session.post(url, headers=headers, json=payload, timeout=30)
                data = response.json()
                
                code = data.get('code')
                msg = data.get('msg', '')
                
                if code == 0:
                    linking_data = data.get('data', {})
                    linking_code = linking_data.get('code')
                    print(f"    ✓ Linking code generated: {linking_code}")
                    return 'success', linking_code
                
                elif code == 2008:
                    print(f"    ✗ Number {number} already linked to another account")
                    return 'already_linked', None
                
                elif code == 30000:
                    print(f"    ✗ Failed to get linking code for {number}")
                    return 'failed', None
                
                elif code == 10052:
                    print(f"    ⏳ Rate limit hit, waiting 20 seconds...")
                    time.sleep(20)
                    continue
                
                else:
                    print(f"    ⚠ Unknown response code {code}: {msg}")
                    time.sleep(5)
                    continue
                    
            except Exception as e:
                print(f"    ✗ Request error: {e}")
                time.sleep(5)
                continue
        
        print(f"    ✗ Max retries exceeded for {number}")
        return 'max_retries', None
    
    def process_account(self, username, account_number, total_accounts):
        """Process a single account"""
        print(f"\n{'='*50}")
        print(f"Processing account {account_number}/{total_accounts}: {username}")
        print(f"{'='*50}")
        
        token, uid = self.login(username)
        if not token:
            return False
        
        status = self.check_numbers_status(token)
        
        if status == "has_online":
            print(f"  ✓ Account {username} has online numbers")
            self.sign_in_for_reward(token, username)
            return True
        
        elif status == "no_numbers" or status == "all_offline":
            print(f"  → Account {username} needs number linking")
            return self.link_number_to_account(username, token)
        
        else:
            print(f"  ✗ Error checking account {username}")
            return False
    
    def link_number_to_account(self, username, token):
        """Link a number to account"""
        numbers_to_try = self.numbers.copy()
        
        while numbers_to_try:
            for i, number in enumerate(numbers_to_try):
                print(f"\n  Trying number: {number}")
                
                result, linking_code = self.get_linking_code(token, number)
                
                if result == 'success':
                    code_data = {
                        'username': username,
                        'number': number,
                        'linking_code': linking_code,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.sent_codes.append(code_data)
                    self.save_sent_codes()
                    
                    self.numbers.remove(number)
                    self.save_numbers_to_file()
                    
                    print(f"  ✓ Code sent successfully for {username}")
                    print(f"  📱 Number: {number}")
                    print(f"  🔑 Linking Code: {linking_code}")
                    time.sleep(5)
                    return True
                
                elif result == 'already_linked':
                    self.numbers.remove(number)
                    numbers_to_try.remove(number)
                    self.save_numbers_to_file()
                    time.sleep(5)
                    continue
                
                elif result == 'failed':
                    numbers_to_try.remove(number)
                    time.sleep(5)
                    continue
                
                elif result == 'max_retries':
                    numbers_to_try.remove(number)
                    time.sleep(2)
                    continue
            
            if not numbers_to_try:
                print(f"  ⚠ All numbers tried for {username}, restarting number list...")
                numbers_to_try = self.numbers.copy()
                time.sleep(10)
        
        return False
    
    def display_sent_codes(self):
        """Display all sent codes"""
        if not self.sent_codes:
            print("No linking codes have been sent yet.")
            return
        
        print(f"\n{'='*60}")
        print("SENT LINKING CODES")
        print(f"{'='*60}")
        
        for i, code_data in enumerate(self.sent_codes, 1):
            print(f"{i}. Username: {code_data['username']}")
            print(f"   Number: {code_data['number']}")
            print(f"   Code: {code_data['linking_code']}")
            print(f"   Time: {code_data['timestamp']}")
            print("-" * 40)
    
    def check_remaining_accounts(self):
        """Check which accounts still need linking"""
        remaining = []
        total_accounts = len(self.accounts)
        
        for index, account in enumerate(self.accounts, 1):
            print(f"\nChecking account {index}/{total_accounts}: {account}")
            token, uid = self.login(account)
            if token:
                status = self.check_numbers_status(token)
                if status != "has_online":
                    remaining.append(account)
                else:
                    self.sign_in_for_reward(token, account)
        
        return remaining
    
    def run(self):
        """Main execution function"""
        print("WhatsApp Number Linking Script")
        print("=" * 40)
        if os.path.exists("send.json"):
            try:
                os.remove("send.json")
                print("✓ Deleted previous send.json file")
            except Exception as e:
                print(f"✗ Failed to delete send.json: {e}")
        
        self.load_files()
        print(f"Loaded {len(self.accounts)} accounts and {len(self.numbers)} numbers")
        
        total_accounts = len(self.accounts)
        for index, username in enumerate(self.accounts, 1):
            success = self.process_account(username, index, total_accounts)
            if success:
                print(f"✓ Completed processing for {username}")
                time.sleep(10)
            else:
                print(f"✗ Failed to process {username}")
            
            time.sleep(2)
        
        print(f"\n{'='*50}")
        print("CHECKING FOR REMAINING ACCOUNTS")
        print(f"{'='*50}")
        
        remaining = self.check_remaining_accounts()
        
        if remaining:
            print(f"Found {len(remaining)} accounts still needing linking:")
            for acc in remaining:
                print(f"  - {acc}")
            
            self.display_sent_codes()
            
            while True:
                choice = input("\nDo you want to generate new codes for remaining accounts? (y/n): ").lower()
                if choice in ['y', 'yes']:
                    for index, acc in enumerate(remaining, 1):
                        self.process_account(acc, index, len(remaining))
                    break
                elif choice in ['n', 'no']:
                    break
                else:
                    print("Please enter 'y' or 'n'")
        
        else:
            print("✓ All accounts have been processed successfully!")
        
        while True:
            choice = input("\nDo you want to start the process again? (y/n): ").lower()
            if choice in ['y', 'yes']:
                self.run()
                break
            elif choice in ['n', 'no']:
                print("Script completed. Goodbye!")
                break
            else:
                print("Please enter 'y' or 'n'")

if __name__ == "__main__":
    linker = WhatsAppLinker()
    linker.run()