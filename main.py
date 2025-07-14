import requests
import json
import time
import os
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fake_useragent import UserAgent

# Initialize UserAgent for randomizing headers
ua = UserAgent()

# Set up logging without timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

class ATMChecker:
    def __init__(self):
        self.session = self._create_session()
        self.headers = self._get_headers()
        self.api_urls = {
            "login": "https://api.89atm.me/login/login",
            "page": "https://api.89atm.me/taskhosting/page",
            "ws_code": "https://api.89atm.me/task/getwswebcode"
        }
        self.max_retries = 3
        self.retry_delay = 5
        self.password = self._read_password()

    def _create_session(self):
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    def _get_headers(self):
        return {
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept": "application/json, text/plain, */*",
            "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
            "Content-Type": "application/json",
            "Sec-Ch-Ua-Mobile": "?0",
            "User-Agent": ua.random,
            "Origin": "https://89atm.me",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://89atm.me/",
            "Priority": "u=1, i"
        }

    def _read_password(self):
        try:
            with open('pwd.txt', 'r', encoding='utf-8') as file:
                password = file.read().strip()
                if not password:
                    logging.error("Password file (pwd.txt) is empty")
                    exit(1)
                return password
        except FileNotFoundError:
            logging.error("Password file (pwd.txt) not found")
            exit(1)
        except Exception as e:
            logging.error(f"Error reading pwd.txt: {str(e)}")
            exit(1)

    def _read_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            logging.error(f"{file_path} not found")
            return []
        except Exception as e:
            logging.error(f"Error reading {file_path}: {str(e)}")
            return []

    def _read_sent_data(self):
        try:
            if os.path.exists('sent.json'):
                with open('sent.json', 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    return data if isinstance(data, list) else []
            return []
        except Exception as e:
            logging.error(f"Error reading sent.json: {str(e)}")
            return []

    def _write_sent_data(self, data):
        try:
            with open('sent.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            logging.error(f"Error writing to sent.json: {str(e)}")

    def _update_num_file(self, ws_numbers):
        try:
            with open('num.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(ws_numbers))
        except Exception as e:
            logging.error(f"Error updating num.txt: {str(e)}")

    def _api_request(self, url, payload, token=None):
        full_url = f"{url}?token={token}" if token else url
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    full_url,
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=20
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == 30000:  # Skip this number
                        logging.info(f"Skipping due to code 30000 for URL: {url}")
                        return None
                    return data
                logging.error(f"API request failed for {url}: HTTP {response.status_code} - Response: {response.text}")
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay*0.2)
                    continue
                logging.error(f"API request error for {url}: {str(e)}")
            except Exception as e:
                logging.error(f"Unexpected error for {url}: {str(e)}")
            return None

    def _process_account(self, acc_number, ws_numbers, sent_data):
        # Step 1: Login
        logging.info(f"\nTrying account: {acc_number}")
        login_payload = {
            "code": 86,
            "user_name": acc_number,
            "pwd": self.password,
            "autologin": False,
            "lang": "",
            "device": "",
            "mac": "",
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }

        login_data = self._api_request(self.api_urls["login"], login_payload)
        if not login_data:
            return False
        if login_data.get("code") != 0:
            logging.error(f"Login failed: {login_data.get('msg', 'Unknown error')}")
            return False

        token = login_data["data"]["token"]
        logging.info(f"Login successful")

        # Step 2: Check online status
        page_payload = {
            "page": 1,
            "limit": 8,
            "httpRequestIndex": 0,
            "httpRequestCount": 0
        }

        page_data = self._api_request(self.api_urls["page"], page_payload, token)
        if not page_data:
            return False
        if page_data.get("code") != 0:
            logging.error(f"Status check failed: {page_data.get('msg', 'Unknown error')}")
            return False

        # Check if account has active ws_account
        if page_data["data"]["data"]:
            for item in page_data["data"]["data"]:
                if item.get("status") == 1:
                    logging.info(f"Already online with ws_account: {item['ws_account']}")
                    return True
            logging.info(f"Account has inactive ws_accounts")

        # Step 3: Submit ws_account
        for ws_account in ws_numbers[:]:
            logging.info(f"Trying ws_account: {ws_account}")
            ws_payload = {
                "ws_account": ws_account,
                "httpRequestIndex": 0,
                "httpRequestCount": 0
            }

            for attempt in range(self.max_retries):  # Retry loop for rate limit and timeouts
                ws_data = self._api_request(self.api_urls["ws_code"], ws_payload, token)
                if not ws_data:
                    if attempt < self.max_retries - 1:
                        logging.info(f"Retrying ws_account {ws_account} in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay*0.2)
                        continue
                    logging.error(f"Failed to process ws_account {ws_account} after {self.max_retries} attempts")
                    break

                if ws_data.get("code") == 0:
                    logging.info(f"Success! Code: {ws_data['data']['code']}")
                    # Remove used ws_account and update files
                    ws_numbers.remove(ws_account)
                    self._update_num_file(ws_numbers)
                    
                    # Add to sent_data and update sent.json
                    sent_data.append({
                        "account": acc_number,
                        "ws_account": ws_account,
                        "code": ws_data['data']['code']
                    })
                    self._write_sent_data(sent_data)
                    return True
                elif ws_data.get("code") == 10052:
                    logging.info(f"Rate limit reached for ws_account {ws_account}, waiting 1 seconds...")
                    time.sleep(5)
                    continue  # Retry same ws_account
                elif ws_data.get("code") == 30000:
                    logging.info("Skipping to next account due to code 30000")
                    return False
                else:
                    logging.error(f"Failed: {ws_data.get('msg', 'Unknown error')}")
                    break  # Move to next ws_account on other errors

        return False

    def run(self):
        acc_numbers = self._read_file('acc.txt')
        ws_numbers = self._read_file('num.txt')
        sent_data = self._read_sent_data()

        if not acc_numbers:
            logging.error("No account numbers found in acc.txt")
            return

        if not ws_numbers:
            logging.error("No ws_account numbers found in num.txt")
            return

        # Filter out used ws_accounts
        used_ws_accounts = {entry['ws_account'] for entry in sent_data}
        ws_numbers = [ws for ws in ws_numbers if ws not in used_ws_accounts]
        
        if not ws_numbers:
            logging.error("No unused ws_account numbers available")
            return

        for acc_number in acc_numbers:
            success = False
            for attempt in range(self.max_retries):
                if self._process_account(acc_number, ws_numbers, sent_data):
                    success = True
                    break
                if attempt < self.max_retries - 1:
                    logging.info(f"Retrying account {acc_number} due to failure... (Attempt {attempt + 1})")
                    time.sleep(self.retry_delay*0.2)

            # Update headers with new User-Agent for next account
            self.headers["User-Agent"] = ua.random

if __name__ == "__main__":
    checker = ATMChecker()
    checker.run()