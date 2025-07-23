import requests
import json
import hashlib
import random
import time
import os
import requests.exceptions

class WhatsAppBalanceChecker:
    def __init__(self):
        self.base_url = "https://api.89atm.me"
        self.session = requests.Session()
        self.accounts = []
        self.password_hash = None
        self.balances = []

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
        """Load accounts and password from files"""
        try:
            with open('acc.txt', 'r') as f:
                self.accounts = [line.strip() for line in f.readlines() if line.strip()]
            
            with open('pwd.txt', 'r') as f:
                password = f.read().strip()
                self.password_hash = hashlib.md5(password.encode()).hexdigest()
            
            if os.path.exists('balance.json'):
                with open('balance.json', 'r') as f:
                    self.balances = json.load(f)
                print("✓ Loaded existing balance.json file")
            else:
                self.balances = []
                print("✓ No existing balance.json file found, starting fresh")
                
        except FileNotFoundError as e:
            print(f"Error: Required file not found - {e}")
            exit(1)

    def save_balances(self):
        """Save balances and withdrawal details to JSON file"""
        with open('balance.json', 'w') as f:
            json.dump(self.balances, f, indent=2)

    def login(self, username, max_retries=3):
        """Login to account and return token with retry logic"""
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
        
        for attempt in range(max_retries):
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
                    
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
                print(f"✗ Network error during login for {username} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return None

        print(f"✗ Max retries exceeded for login {username}")
        return None

    def check_balance(self, username, token, max_retries=3):
        """Check balance for account with retry logic"""
        url = f"{self.base_url}/member/index?token={token}"
        headers = self.get_headers()
        
        payload = {
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, headers=headers, json=payload, timeout=30)
                data = response.json()
                
                if data.get('code') == 0:
                    point = data['data'].get('point', 0)
                    balance = point / 10000  # Convert to actual balance
                    user_code = data['data'].get('user_code', 'N/A')
                    print(f"  ✓ Balance for {username}: {balance:.2f}, User Code: {user_code}")
                    return balance, user_code
                else:
                    print(f"  ✗ Failed to check balance for {username}: {data.get('msg', 'Unknown error')}")
                    return None, None
                    
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
                print(f"  ✗ Network error checking balance for {username} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return None, None

        print(f"  ✗ Max retries exceeded for checking balance {username}")
        return None, None

    def get_withdrawal_details(self, username, token, max_retries=3):
        """Get withdrawal account details for account with retry logic"""
        url = f"{self.base_url}/wealth/wealthinfo?token={token}"
        headers = self.get_headers()
        
        payload = {
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }
        
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, headers=headers, json=payload, timeout=30)
                data = response.json()
                
                if data.get('code') == 0:
                    withdrawal_data = data.get('data', {})
                    pk_bank_name = withdrawal_data.get('pk_bank_name', 'N/A')
                    pk_bank_user_name = withdrawal_data.get('pk_bank_user_name', 'N/A')
                    pk_bank_no = withdrawal_data.get('pk_bank_no', 'N/A')
                    print(f"  ✓ Withdrawal Details for {username}:")
                    print(f"     Bank Name: {pk_bank_name}")
                    print(f"     Account Holder: {pk_bank_user_name}")
                    print(f"     Account Number: {pk_bank_no}")
                    return {
                        'pk_bank_name': pk_bank_name,
                        'pk_bank_user_name': pk_bank_user_name,
                        'pk_bank_no': pk_bank_no
                    }
                else:
                    print(f"  ✗ Failed to get withdrawal details for {username}: {data.get('msg', 'Unknown error')}")
                    return None
                    
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
                print(f"  ✗ Network error getting withdrawal details for {username} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return None

        print(f"  ✗ Max retries exceeded for withdrawal details {username}")
        return None

    def update_or_append_balance(self, username, balance, user_code, withdrawal_details):
        """Update existing account data or append new data"""
        balance_data = {
            'username': username,
            'balance': balance,
            'points': int(balance * 10000),
            'user_code': user_code,
            'withdrawal_details': withdrawal_details,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        for i, existing in enumerate(self.balances):
            if existing['username'] == username:
                self.balances[i] = balance_data
                print(f"  ✓ Updated existing data for {username}")
                return
        
        self.balances.append(balance_data)
        print(f"  ✓ Added new data for {username}")

    def display_balances(self):
        """Display all saved balances in one-line format"""
        if not self.balances:
            print("No balances have been saved yet.")
            return
        
        print(f"\n{'='*80}")
        print("ALL ACCOUNT BALANCES (ONE-LINE FORMAT)")
        print(f"{'='*80}")
        
        for i, balance_data in enumerate(self.balances, 1):
            print(f"{i}. {balance_data['username']} | Balance: {balance_data['balance']:.2f} | User Code: {balance_data['user_code']} | Bank: {balance_data['withdrawal_details'].get('pk_bank_name', 'N/A')} | Holder: {balance_data['withdrawal_details'].get('pk_bank_user_name', 'N/A')} | Acc: {balance_data['withdrawal_details'].get('pk_bank_no', 'N/A')} | Time: {balance_data['timestamp']}")

    def check_single_account(self):
        """Check balance and withdrawal details for a specific account"""
        self.load_files()
        print(f"\nAvailable accounts: {', '.join(self.accounts)}")
        username = input("Enter the username to check: ").strip()
        
        if username not in self.accounts:
            print(f"Error: Username '{username}' not found in acc.txt")
            return
        
        print(f"\n{'='*50}")
        print(f"Processing account: {username}")
        print(f"{'='*50}")
        
        token = self.login(username)
        if not token:
            return
            
        balance, user_code = self.check_balance(username, token)
        if balance is None:
            return
            
        withdrawal_details = self.get_withdrawal_details(username, token)
        if withdrawal_details is None:
            withdrawal_details = {
                'pk_bank_name': 'N/A',
                'pk_bank_user_name': 'N/A',
                'pk_bank_no': 'N/A'
            }
        
        self.update_or_append_balance(username, balance, user_code, withdrawal_details)
        self.save_balances()

    def display_menu(self):
        """Display menu and handle user choices"""
        while True:
            print("\nWhatsApp Balance and Withdrawal Details Checker")
            print("=" * 45)
            print("1. Check balance for a specific account")
            print("2. Display all account balances (one-line format)")
            print("3. Exit")
            choice = input("Enter your choice (1-3): ").strip()
            
            if choice == '1':
                self.check_single_account()
            elif choice == '2':
                self.load_files()
                self.display_balances()
            elif choice == '3':
                print("Script completed. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    def run(self):
        """Main execution function"""
        print("WhatsApp Balance and Withdrawal Details Checker Script")
        print("=" * 40)
        self.display_menu()

if __name__ == "__main__":
    checker = WhatsAppBalanceChecker()
    checker.run()