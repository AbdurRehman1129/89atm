import requests
import json
import time
import random
import hashlib
import string

class PaymentManager:
    def __init__(self):
        self.base_url = "https://api.89atm.me"
        self.session = requests.Session()
        self.accounts = []
        self.password_hash = ""

    def generate_fake_user_agent(self):
        """Generate a fake user agent with randomized browser/engine."""
        chrome_versions = ["138.0.0.0", "137.0.0.0", "136.0.0.0", "135.0.0.0"]
        firefox_versions = ["120.0", "119.0", "118.0", "117.0"]
        windows_versions = ["10.0", "11.0"]
        macos_versions = ["10_15_7", "11_6", "12_6", "13_5"]
        linux_versions = ["x86_64", "i686"]
        
        engines = [
            {
                "name": "Chrome",
                "templates": [
                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",
                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",
                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",
                ],
            },
            {
                "name": "Firefox",
                "templates": [
                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64; rv:{random.choice(firefox_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)}",
                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}; rv:{random.choice(firefox_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)}",
                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}; rv:{random.choice(firefox_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)}",
                ],
            },
        ]
        selected_browser = random.choice(engines)
        return random.choice(selected_browser["templates"])

    def get_headers(self):
        """Get headers with fake user agent."""
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "text/plain",
            "Origin": "https://89atm.me",
            "Referer": "https://89atm.me/",
            "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.generate_fake_user_agent(),
            "Connection": "keep-alive",
            "Priority": "u=1, i",
        }

    def load_accounts(self):
        """Load accounts from acc.txt file."""
        try:
            with open("acc.txt", "r") as f:
                self.accounts = [line.strip() for line in f.readlines() if line.strip()]
            print(f"✓ Loaded {len(self.accounts)} accounts")
        except FileNotFoundError as e:
            print(f"Error: acc.txt file not found - {e}")
            exit(1)

    def load_password(self):
        """Load password from pwd.txt file."""
        try:
            with open("pwd.txt", "r") as f:
                password = f.read().strip()
                self.password_hash = hashlib.md5(password.encode()).hexdigest()
            print("✓ Password loaded and hashed")
        except FileNotFoundError as e:
            print(f"Error: pwd.txt file not found - {e}")
            exit(1)

    def retry_on_error(self, func, *args, **kwargs):
        """Retry function on internet/connection errors."""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout) as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print(f"Failed after {max_retries} attempts")
                    return None
                time.sleep(3)
        return None

    def login(self, username):
        """Login to account and return token with retry mechanism."""
        def _login():
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
                "httpRequestCount": 0,
            }
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            if data.get("code") == 0:
                token = data["data"]["token"]
                print(f"✓ Login successful for {username}")
                return token
            else:
                raise Exception(f"Login failed: {data.get('msg', 'Unknown error')}")

        return self.retry_on_error(_login)

    def check_payment_details(self, token):
        """Check current payment details and balance."""
        def _check():
            url = f"{self.base_url}/wealth/wealthinfo?token={token}"
            headers = self.get_headers()
            payload = {"httpRequestIndex": 0, "httpRequestCount": 0}
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            if data.get("code") == 0:
                account_data = data["data"]
                balance = account_data["point"] / 10000
                payment_set = (
                    account_data.get("pk_bank_no") != ""
                    and account_data.get("pk_bank_user_name") != ""
                    and account_data.get("pk_bank_name") != ""
                )
                return balance, payment_set, account_data
            else:
                raise Exception(f"Error checking payment details: {data.get('msg', 'Unknown error')}")

        return self.retry_on_error(_check)

    def generate_random_payment_details(self):
        """Generate random payment details for clearing existing ones."""
        bank_name = "EASYPAISA"
        bank_no = str(random.randint(100000, 999999))
        bank_user_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        return bank_name, bank_user_name, bank_no

    def set_payment_details(self, token, bank_name, bank_user_name, bank_no):
        """Set payment details for an account with verification."""
        def _set_payment_once():
            url = f"{self.base_url}/member/addbank?token={token}"
            headers = self.get_headers()
            bank_zhi = "TMBKPKKA" if bank_name.lower() == "easypaisa" else "JSBLPKKA" if bank_name.lower() == "jazzcash" else ""
            
            payload = {
                "point": 0,
                "wealth_point": 0,
                "total_point": 0,
                "bank_name": "",
                "bank_no": "",
                "bank_user_name": "",
                "bank_zhi": bank_zhi,
                "bank_phone": "",
                "ali_no": "",
                "ali_user_name": "",
                "min_point": 200,
                "new_user": True,
                "fee_type": 1,
                "fee": 10,
                "max_point": 50000,
                "put_count": 1,
                "open_time": "",
                "end_time": "",
                "day_list": ["1", "2", "3", "4", "5", "6", "7"],
                "min_point_ali": 3300,
                "fee_type_ali": 0,
                "fee_ali": 0,
                "max_point_ali": 10000,
                "put_type": "14,13,4",
                "put_desc": "Brazilian Real \nExchange Rate = 0.025\n\nPakistani Rupee\nExchange Rate = 0.6\n\nNigeria\nExchange Rate = 0.025\n\n",
                "hundred": 100,
                "trx_price": 0,
                "ngn_price": 2,
                "fcfa_price": 0,
                "bank_min": 200,
                "usdt_min": 3000,
                "fcfa_min": 0,
                "mxn_min": 0,
                "bdt_min": 0,
                "brl_min": 250,
                "pkr_min": 200,
                "idr_min": 0,
                "thb_min": 0,
                "kes_min": 0,
                "with_draw": True,
                "s_time": 0,
                "e_time": 24,
                "tng_wallet_no": "",
                "tng_wallet_name": "",
                "th_bank_no": "",
                "th_bank_user_name": "",
                "th_bank_name": "",
                "xf_bank_no": "",
                "xf_bank_user_name": "",
                "xf_bank_name": "",
                "mx_bank_no": "",
                "mx_bank_user_name": "",
                "mx_bank_name": "",
                "md_bank_no": "",
                "md_bank_user_name": "",
                "md_bank_name": "",
                "br_bank_no": "",
                "br_bank_user_name": "",
                "br_bank_name": "",
                "identify_type": "",
                "identify_number": "",
                "usdt_trc": "",
                "pk_bank_no": bank_no,
                "pk_bank_user_name": bank_user_name,
                "pk_bank_name": bank_name.upper(),
                "pk_identify_num": bank_no,
                "pk_account_type": "WALLET",
                "id_bank_no": "",
                "id_bank_user_name": "",
                "id_bank_name": "",
                "kes_bank_no": "",
                "kes_bank_user_name": "",
                "kes_bank_name": "",
                "my_bank_no": "",
                "my_bank_user_name": "",
                "my_bank_name": "",
                "ifsc": "",
                "account_type": "",
                "captcha": self.password_hash,
                "httpRequestIndex": 0,
                "httpRequestCount": 0,
            }
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            if data.get("code") != 0:
                if data.get("code") == 10041:
                    raise Exception("Bank binding limit exceeded")
                raise Exception(f"Failed to set payment details: {data.get('msg', 'Unknown error')}")
            time.sleep(2)  # Wait for server to process
            return True

        # Try to set payment details with one attempt and verify
        try:
            result = _set_payment_once()
            if result:
                print(f"✓ Attempt 1: Set payment details")
                time.sleep(2)
                
                # Verify the details were set correctly
                balance, payment_set, account_data = self.check_payment_details(token)
                if (account_data and 
                    account_data.get("pk_bank_user_name") == bank_user_name and
                    account_data.get("pk_bank_no") == bank_no and
                    account_data.get("pk_bank_name") == bank_name.upper()):
                    print(f"✓ Payment details verified")
                    return True
                else:
                    print(f"✗ Payment details not verified")
                    return False
            else:
                print(f"✗ Attempt 1: Failed to set payment details")
                return False
        except Exception as e:
            print(f"✗ Attempt 1: Failed to set payment details: {e}")
            if "Bank binding limit exceeded" in str(e):
                raise Exception("Bank binding limit exceeded")
            time.sleep(5)
            return False

    def clear_payment_methods_from_all_accounts(self):
        """Clear payment methods from all accounts by setting random details."""
        print("\n" + "="*60)
        print("CLEARING PAYMENT METHODS FROM ALL ACCOUNTS")
        print("="*60)
        
        for index, username in enumerate(self.accounts, 1):
            print(f"\nProcessing account {index}/{len(self.accounts)}: {username}")
            
            token = self.login(username)
            if not token:
                print(f"✗ Failed to login to {username}")
                continue
            
            balance, payment_set, account_data = self.check_payment_details(token)
            if balance is None:
                print(f"✗ Failed to check payment details for {username}")
                continue
            
            if not payment_set:
                print(f"ℹ {username} has no payment details set")
                continue
            
            # Generate random details to clear existing ones
            bank_name, bank_user_name, bank_no = self.generate_random_payment_details()
            
            if self.set_payment_details(token, bank_name, bank_user_name, bank_no):
                print(f"✓ Cleared payment details for {username}")
            else:
                print(f"✗ Failed to clear payment details for {username}")
            
            time.sleep(2)

    def run(self):
        """Main execution function."""
        print("89ATM Payment Clearer")
        print("=" * 50)
        
        # Load required data
        self.load_accounts()
        self.load_password()
        
        # Clear payment methods
        self.clear_payment_methods_from_all_accounts()
        
        print("\n" + "="*60)
        print("PAYMENT CLEARING COMPLETED")
        print("="*60)

if __name__ == "__main__":
    manager = PaymentManager()
    manager.run()