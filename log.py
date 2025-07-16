import requests
import json
import time
import random
import hashlib
import os

class AccountStatusChecker:
    def __init__(self):
        self.base_url = "https://api.89atm.me"
        self.session = requests.Session()
        self.accounts = []
        self.password_hash = ""
        self.online_accounts = []
        self.offline_accounts = []

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
        try:
            with open('acc.txt', 'r') as f:
                self.accounts = [line.strip() for line in f.readlines() if line.strip()]
            
            with open('pwd.txt', 'r') as f:
                password = f.read().strip()
                self.password_hash = hashlib.md5(password.encode()).hexdigest()
                
        except FileNotFoundError as e:
            print(f"Error: Required file not found - {e}")
            exit(1)

    def save_results(self):
        """Save online and offline accounts to respective files"""
        with open('online.txt', 'w') as f:
            for account in self.online_accounts:
                f.write(account + '\n')
        
        with open('offline.txt', 'w') as f:
            for account in self.offline_accounts:
                f.write(account + '\n')

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

    def check_account_status(self, token, username):
        """Check if any numbers are online for the account"""
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
                    print(f"  No numbers linked to {username} - marking as offline")
                    return False
                
                online_count = sum(1 for num in numbers_data if num.get('status') == 1)
                
                if online_count > 0:
                    print(f"  ✓ {username} has {online_count} online number(s)")
                    return True
                else:
                    print(f"  ✗ {username} has {len(numbers_data)} number(s), all offline")
                    return False
            else:
                print(f"  Error checking {username}: {data.get('msg', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"  Error checking {username}: {e}")
            return False

    def process_account(self, username):
        """Process a single account and check its status"""
        print(f"\n{'='*50}")
        print(f"Processing account: {username}")
        print(f"{'='*50}")
        
        token = self.login(username)
        if not token:
            print(f"  ✗ Failed to login, marking {username} as offline")
            self.offline_accounts.append(username)
            return False
        
        is_online = self.check_account_status(token, username)
        if is_online:
            self.online_accounts.append(username)
        else:
            self.offline_accounts.append(username)
        
        return is_online

    def run(self):
        """Main execution function"""
        print("Account Status Checker Script")
        print("=" * 40)
        
        # Delete existing online.txt and offline.txt if they exist
        for file in ['online.txt', 'offline.txt']:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    print(f"✓ Deleted previous {file}")
                except Exception as e:
                    print(f"✗ Failed to delete {file}: {e}")
        
        # Load accounts and password
        self.load_files()
        print(f"Loaded {len(self.accounts)} accounts")
        
        # Process all accounts
        for username in self.accounts:
            self.process_account(username)
            time.sleep(2)  # Short delay between accounts
        
        # Save results
        self.save_results()
        print(f"\n{'='*50}")
        print(f"Results: {len(self.online_accounts)} online, {len(self.offline_accounts)} offline")
        print(f"Online accounts saved to online.txt")
        print(f"Offline accounts saved to offline.txt")
        
        # Display results
        if self.online_accounts:
            print("\nOnline Accounts:")
            for acc in self.online_accounts:
                print(f"  - {acc}")
        
        if self.offline_accounts:
            print("\nOffline Accounts:")
            for acc in self.offline_accounts:
                print(f"  - {acc}")

if __name__ == "__main__":
    checker = AccountStatusChecker()
    checker.run()