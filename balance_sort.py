import requests
import json
import time
import random
import hashlib
from datetime import datetime
import os
import shlex
import string
import logging

# Configure logging to minimize terminal clutter and log errors to a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('balance_sorter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BalanceSorter:
    def __init__(self):
        self.base_url = "https://api.89atm.me"
        self.session = requests.Session()
        self.accounts = []
        self.password_hash = ""
        self.payment_details = []
        self.payment_bindings_file = "payment_bindings.txt"
        self.max_retries = 3  # Define max_retries
        self.retry_delay = 5  # Define retry_delay
        self.setup_payment_bindings_file()

    def setup_payment_bindings_file(self):
        """Ensure the payment bindings file exists and is initialized."""
        try:
            if not os.path.exists(self.payment_bindings_file):
                with open(self.payment_bindings_file, "w") as f:
                    f.write("username,bank_name,bank_user_name,bank_no\n")
                logger.info("Created payment_bindings.txt")
        except Exception as e:
            logger.error(f"Error creating payment_bindings.txt: {e}")
            exit(1)

    def generate_fake_user_agent(self):
        """Generate a fake user agent with randomized browser/engine."""
        chrome_versions = ["138.0.0.0", "137.0.0.0", "136.0.0.0", "135.0.0.0"]
        firefox_versions = ["120.0", "119.0", "118.0", "117.0"]
        edge_versions = ["118.0.2088.46", "117.0.2045.31", "116.0.1938.62"]
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
            {
                "name": "Edge",
                "templates": [
                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)}",
                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)}",
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

    def load_files(self):
        """Load accounts, password, and payment details from files."""
        try:
            with open("acc.txt", "r") as f:
                self.accounts = [line.strip() for line in f.readlines() if line.strip()]

            with open("pwd.txt", "r") as f:
                password = f.read().strip()
                self.password_hash = hashlib.md5(password.encode()).hexdigest()

            with open("bank_details.txt", "r") as f:
                self.payment_details = []
                for line in f.readlines():
                    parts = shlex.split(line.strip())
                    if len(parts) == 3:
                        self.payment_details.append(parts)
                    else:
                        logger.warning(f"Invalid payment details format in line: {line.strip()}")
            logger.info(f"Loaded {len(self.accounts)} accounts and {len(self.payment_details)} payment methods")
        except FileNotFoundError as e:
            logger.error(f"Required file not found - {e}")
            exit(1)

    def login(self, username):
        """Login to account and return token with retry logic."""
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
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(url, headers=headers, json=payload, timeout=30)
                data = response.json()
                if data.get("code") == 0:
                    token = data["data"]["token"]
                    logger.info(f"Login successful for {username}")
                    return token
                else:
                    logger.warning(f"Login failed for {username}: {data.get('msg', 'Unknown error')}")
                    return None
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.error(f"Attempt {attempt + 1}/{self.max_retries} - Network error during login for {username}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Login error for {username}: {e}")
                return None
        logger.error(f"Failed to login for {username} after {self.max_retries} attempts")
        return None

    def check_payment_details(self, token):
        """Check if payment details are set for an account with retry logic."""
        url = f"{self.base_url}/wealth/wealthinfo?token={token}"
        headers = self.get_headers()
        payload = {"httpRequestIndex": 0, "httpRequestCount": 0}
        for attempt in range(self.max_retries):
            try:
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
                    logger.warning(f"Error checking payment details: {data.get('msg', 'Unknown error')}")
                    return None, False, None
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.error(f"Attempt {attempt + 1}/{self.max_retries} - Network error checking payment details: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Error checking payment details: {e}")
                return None, False, None
        logger.error(f"Failed to check payment details after {self.max_retries} attempts")
        return None, False, None

    def get_payment_binding_count(self, bank_no):
        """Check how many accounts a payment method is bound to in the local payment bindings file."""
        try:
            with open(self.payment_bindings_file, "r") as f:
                lines = f.readlines()[1:]  # Skip header
                count = sum(1 for line in lines if line.strip() and line.split(",")[3].strip() == bank_no)
                return count
        except Exception as e:
            logger.error(f"Error reading payment bindings for {bank_no}: {e}")
            return 0

    def update_payment_binding(self, username, bank_name, bank_user_name, bank_no):
        """Update payment bindings in the local payment bindings file."""
        try:
            # Read existing bindings
            with open(self.payment_bindings_file, "r") as f:
                lines = f.readlines()
            
            # Check if account exists and update or append
            account_exists = False
            updated_lines = [lines[0]]  # Keep header
            for line in lines[1:]:
                if line.strip() and line.split(",")[0].strip() == username:
                    updated_lines.append(f"{username},{bank_name},{bank_user_name},{bank_no}\n")
                    account_exists = True
                else:
                    updated_lines.append(line)
            
            if not account_exists:
                updated_lines.append(f"{username},{bank_name},{bank_user_name},{bank_no}\n")
            
            # Write updated bindings
            with open(self.payment_bindings_file, "w") as f:
                f.writelines(updated_lines)
            
            logger.info(f"Updated payment binding for {username}")
            return True
        except Exception as e:
            logger.error(f"Error updating payment binding for {username}: {e}")
            return False

    def clear_payment_binding(self, username):
        """Clear payment binding for an account in the local payment bindings file."""
        try:
            # Read existing bindings
            with open(self.payment_bindings_file, "r") as f:
                lines = f.readlines()
            
            # Update the specific account's binding
            updated_lines = [lines[0]]  # Keep header
            account_found = False
            for line in lines[1:]:
                if line.strip() and line.split(",")[0].strip() == username:
                    updated_lines.append(f"{username},,,\n")
                    account_found = True
                else:
                    updated_lines.append(line)
            
            if not account_found:
                return True  # No binding to clear, return True
            
            # Write updated bindings
            with open(self.payment_bindings_file, "w") as f:
                f.writelines(updated_lines)
            
            logger.info(f"Cleared payment binding for {username}")
            return True
        except Exception as e:
            logger.error(f"Error clearing payment binding for {username}: {e}")
            return False

    def generate_random_payment_details(self):
        """Generate random payment details: easypaisa, 6-digit number, 6-letter name."""
        bank_name = "easypaisa"
        bank_no = str(random.randint(100000, 999999))
        bank_user_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        return bank_name, bank_user_name, bank_no

    def set_payment_details(self, token, bank_name, bank_user_name, bank_no):
        """Set payment details for an account with retry logic."""
        url = f"{self.base_url}/member/addbank?token={token}"
        headers = self.get_headers()
        bank_zhi = "TMBKPKKA" if bank_name.lower() == "easypaisa" else "JSBLPKKA" if bank_name.lower() == "jazzcash" else ""
        if not bank_zhi and bank_name:
            logger.warning(f"Invalid bank name: {bank_name}. Must be 'easypaisa' or 'jazzcash'.")
            return False
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
            "pk_bank_no": bank_no if bank_name else "",
            "pk_bank_user_name": bank_user_name if bank_name else "",
            "pk_bank_name": bank_name.upper() if bank_name else "",
            "pk_identify_num": bank_no if bank_name else "",
            "pk_account_type": "WALLET" if bank_name else "",
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
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(url, headers=headers, json=payload, timeout=30)
                data = response.json()
                if data.get("code") == 0:
                    logger.info(f"Attempt {attempt + 1}: Set payment details")
                    balance, payment_set, account_data = self.check_payment_details(token)
                    if (
                        not bank_name or
                        (account_data.get("pk_bank_user_name") == bank_user_name
                        and account_data.get("pk_bank_no") == bank_no
                        and account_data.get("pk_bank_name") == bank_name.upper())
                    ):
                        logger.info(f"Payment details verified for {bank_no if bank_name else 'cleared'}")
                        return True
                    else:
                        logger.warning(f"Payment details incorrect, retrying...")
                        time.sleep(self.retry_delay)
                else:
                    logger.warning(f"Attempt {attempt + 1}: Failed to set payment details: {data.get('msg', 'Unknown error')}")
                    time.sleep(self.retry_delay)
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.error(f"Attempt {attempt + 1}/{self.max_retries} - Network error setting payment details: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Error setting payment details: {e}")
                time.sleep(self.retry_delay)
        logger.error("Failed to set payment details after retries")
        return False

    def sort_and_clear_low_balance_accounts(self):
        """Sort accounts by balance, clear payment details for <150, and save to respective files."""
        self.load_files()
        amount_end = []
        amount_medium = []
        amount_high = []

        for username in self.accounts[:]:
            logger.info(f"Processing {username}")
            token = self.login(username)
            if not token:
                logger.warning(f"Skipping {username} due to login failure")
                continue

            balance, payment_set, account_data = self.check_payment_details(token)
            if balance is None:
                logger.warning(f"Skipping {username} due to failure in checking payment details")
                continue

            logger.info(f"{username}: Balance {balance:.2f} units")
            if balance < 150 and payment_set:
                bank_no = account_data.get("pk_bank_no", "")
                bank_name = account_data.get("pk_bank_name", "")
                bank_user_name = account_data.get("pk_bank_user_name", "")
                if bank_no:
                    amount_end.append(f"{username}")
                random_bank_name, random_user_name, random_bank_no = self.generate_random_payment_details()
                binding_count = self.get_payment_binding_count(random_bank_no)
                max_attempts = 5
                attempt = 0
                while binding_count >= 2 and attempt < max_attempts:
                    logger.warning(f"Generated bank number {random_bank_no} is already bound to 2 accounts, regenerating...")
                    random_bank_name, random_user_name, random_bank_no = self.generate_random_payment_details()
                    binding_count = self.get_payment_binding_count(random_bank_no)
                    attempt += 1
                if binding_count >= 2:
                    logger.error(f"Could not find unique bank number for {username} after {max_attempts} attempts")
                    continue
                if self.set_payment_details(token, random_bank_name, random_user_name, random_bank_no):
                    self.clear_payment_binding(username)
                    self.payment_details = [details for details in self.payment_details if details[2] != bank_no]
                    self.accounts.remove(username)
                    logger.info(f"Cleared payment details and removed {username} from accounts list")
                else:
                    logger.error(f"Failed to clear payment details for {username}")
            elif 150 <= balance < 200:
                amount_medium.append(f"{username} {balance:.2f}")
            elif balance >= 200:
                amount_high.append(f"{username} {balance:.2f}")

            time.sleep(2)

        # Write to amount_end.txt
        try:
            with open("amount_end.txt", "a") as f:
                for entry in amount_end:
                    f.write(entry + "\n")
            logger.info(f"Wrote {len(amount_end)} usernames to amount_end.txt")
        except Exception as e:
            logger.error(f"Error writing to amount_end.txt: {e}")

        # Write to amount_medium.txt
        try:
            with open("amount_medium.txt", "a") as f:
                for entry in amount_medium:
                    f.write(entry + "\n")
            logger.info(f"Wrote {len(amount_medium)} accounts to amount_medium.txt")
        except Exception as e:
            logger.error(f"Error writing to amount_medium.txt: {e}")

        # Write to amount_high.txt
        try:
            with open("amount_high.txt", "a") as f:
                for entry in amount_high:
                    f.write(entry + "\n")
            logger.info(f"Wrote {len(amount_high)} accounts to amount_high.txt")
        except Exception as e:
            logger.error(f"Error writing to amount_high.txt: {e}")

        # Update acc.txt with remaining accounts
        try:
            with open("acc.txt", "w") as f:
                for acc in self.accounts:
                    f.write(acc + "\n")
            logger.info("Updated acc.txt with remaining accounts")
        except Exception as e:
            logger.error(f"Error updating acc.txt: {e}")

        if not amount_end and not amount_medium and not amount_high:
            logger.info("No accounts processed or categorized")

    def run(self):
        """Main execution function."""
        logger.info("Starting Balance Sorter Script")
        self.sort_and_clear_low_balance_accounts()
        logger.info("Balance Sorter Script completed")

if __name__ == "__main__":
    sorter = BalanceSorter()
    sorter.run()