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
            with open('check.txt', 'r') as f:
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
        
        # Check if username already exists in balances
        for i, existing in enumerate(self.balances):
            if existing['username'] == username:
                self.balances[i] = balance_data  # Update existing entry
                print(f"  ✓ Updated existing data for {username}")
                return
        
        # If not found, append new entry
        self.balances.append(balance_data)
        print(f"  ✓ Added new data for {username}")

    def display_balances(self):
        """Display all saved balances and withdrawal details"""
        if not self.balances:
            print("No balances have been saved yet.")
            return
        
        print(f"\n{'='*60}")
        print("ACCOUNT BALANCES AND WITHDRAWAL DETAILS")
        print(f"{'='*60}")
        
        for i, balance_data in enumerate(self.balances, 1):
            print(f"{i}. Username: {balance_data['username']}")
            print(f"   Balance: {balance_data['balance']:.2f}")
            print(f"   Points: {balance_data['points']}")
            print(f"   User Code: {balance_data['user_code']}")
            print(f"   Bank Name: {balance_data['withdrawal_details'].get('pk_bank_name', 'N/A')}")
            print(f"   Account Holder: {balance_data['withdrawal_details'].get('pk_bank_user_name', 'N/A')}")
            print(f"   Account Number: {balance_data['withdrawal_details'].get('pk_bank_no', 'N/A')}")
            print(f"   Time: {balance_data['timestamp']}")
            print("-" * 40)

    def find_accounts_by_balance(self):
        """Find and display accounts with balance equal to or higher than user input"""
        try:
            target_balance = float(input("\nEnter the minimum balance to search for: "))
        except ValueError:
            print("Please enter a valid number for balance.")
            return

        matching_accounts = [
            account for account in self.balances
            if account['balance'] >= target_balance
        ]

        if not matching_accounts:
            print(f"\nNo accounts found with balance >= {target_balance:.2f}")
            return

        print(f"\n{'='*60}")
        print(f"ACCOUNTS WITH BALANCE >= {target_balance:.2f}")
        print(f"{'='*60}")
        
        for i, account in enumerate(matching_accounts, 1):
            print(f"{i}. Username: {account['username']}")
            print(f"   Balance: {account['balance']:.2f}")
            print(f"   User Code: {account['user_code']}")
            print(f"   Bank Name: {account['withdrawal_details'].get('pk_bank_name', 'N/A')}")
            print(f"   Account Holder: {account['withdrawal_details'].get('pk_bank_user_name', 'N/A')}")
            print(f"   Account Number: {account['withdrawal_details'].get('pk_bank_no', 'N/A')}")
            print(f"   Time: {account['timestamp']}")
            print("-" * 40)

    def run(self):
        """Main execution function"""
        print("WhatsApp Balance and Withdrawal Details Checker Script")
        print("=" * 40)
        
        # Load files
        self.load_files()
        print(f"Loaded {len(self.accounts)} accounts")
        
        # Process all accounts
        for username in self.accounts:
            print(f"\n{'='*50}")
            print(f"Processing account: {username}")
            print(f"{'='*50}")
            
            # Login
            token = self.login(username)
            if not token:
                continue
                
            # Check balance
            balance, user_code = self.check_balance(username, token)
            if balance is None:
                continue
                
            # Get withdrawal details
            withdrawal_details = self.get_withdrawal_details(username, token)
            if withdrawal_details is None:
                withdrawal_details = {
                    'pk_bank_name': 'N/A',
                    'pk_bank_user_name': 'N/A',
                    'pk_bank_no': 'N/A'
                }
            
            # Update or append balance and withdrawal details
            self.update_or_append_balance(username, balance, user_code, withdrawal_details)
            self.save_balances()
            time.sleep(2)  # Short delay between accounts
        
        # Display all balances and withdrawal details
        self.display_balances()
        
        # Ask if user wants to search for accounts by balance
        while True:
            choice = input("\nDo you want to search for accounts by minimum balance? (y/n): ").lower()
            if choice in ['y', 'yes']:
                self.find_accounts_by_balance()
                break
            elif choice in ['n', 'no']:
                print("Script completed. Goodbye!")
                break
            else:
                print("Please enter 'y' or 'n'")

if __name__ == "__main__":
    checker = WhatsAppBalanceChecker()
    checker.run()