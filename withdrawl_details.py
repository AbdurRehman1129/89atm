import requests
import json
import time
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import hashlib
import shlex
import uuid
import random

class WithdrawalHistoryChecker:
    def __init__(self):
        self.base_url = "https://api.89atm.me"
        self.session = requests.Session()
        self.accounts = []
        self.password_hash = ""
        self.spreadsheet_id = "" # Replace with your Google Sheets ID
        self.credentials_file = "" # Replace with your Google Service Account credentials file
        self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        self.service = self.setup_google_sheets()

    def setup_google_sheets(self):
        """Set up Google Sheets API client and initialize headers."""
        try:
            creds = Credentials.from_service_account_file(self.credentials_file, scopes=self.scopes)
            service = build("sheets", "v4", credentials=creds)
            # Test connection
            service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Test!A1",
                valueInputOption="RAW",
                body={"values": [["Test connection at " + datetime.now().strftime("%Y-%m-%d %H:%M")]]}
            ).execute()
            print("✓ Google Sheets connection verified")
            # Initialize Withdrawals sheet headers if not present
            try:
                result = service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id, range="Withdrawals!A1:G1"
                ).execute()
                values = result.get("values", [])
                required_headers = [
                    "Username", "Account Number", "Bank Name", "Account Title",
                    "Status", "Actual Amount Withdrawn", "Amount Received"
                ]
                if not values or not all(h in values[0] for h in required_headers):
                    service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range="Withdrawals!A1:G1",
                        valueInputOption="RAW",
                        body={"values": [required_headers]}
                    ).execute()
                    print("✓ Initialized Withdrawals sheet with headers")
            except Exception as e:
                print(f"Warning: Could not initialize Withdrawals sheet headers: {e}")
            return service
        except Exception as e:
            print(f"Error setting up Google Sheets API: {e}")
            print("Please check the credentials file and ensure the spreadsheet ID is correct.")
            exit(1)

    def load_files(self):
        """Load accounts and password from files."""
        try:
            with open("acc.txt", "r") as f:
                self.accounts = [line.strip() for line in f.readlines() if line.strip()]
            with open("pwd.txt", "r") as f:
                password = f.read().strip()
                self.password_hash = hashlib.md5(password.encode()).hexdigest()
            print(f"Loaded {len(self.accounts)} accounts")
        except FileNotFoundError as e:
            print(f"Error: Required file not found - {e}")
            exit(1)

    def generate_fake_user_agent(self):
        """Generate a fake user agent."""
        browsers = [
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        ]
        return random.choice(browsers)

    def get_headers(self):
        """Get headers with fake user agent."""
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "text/plain",
            "Origin": "https://89atm.me",
            "Referer": "https://89atm.me/",
            "User-Agent": self.generate_fake_user_agent(),
            "Connection": "keep-alive",
        }

    def login(self, username):
        """Login to account and return token."""
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
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            if data.get("code") == 0:
                token = data["data"]["token"]
                print(f"✓ Login successful for {username}")
                return token
            else:
                print(f"✗ Login failed for {username}: {data.get('msg', 'Unknown error')}")
                return None
        except Exception as e:
            print(f"✗ Login error for {username}: {e}")
            return None

    def check_withdrawal_history(self, token, username, limit=1, specific_date=None):
        """Check withdrawal history for an account."""
        url = f"{self.base_url}/wealth/putlist?token={token}"
        headers = self.get_headers()
        payload = {
            "page": 1,
            "limit": limit,
            "ptype": -1,
            "stime": 0,
            "etime": 0,
            "httpRequestIndex": 0,
            "httpRequestCount": 0,
        }
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            if data.get("code") == 0 and data.get("data", {}).get("list"):
                withdrawals = data["data"]["list"]
                withdrawal_data_list = []
                for withdrawal in withdrawals:
                    status_map = {5: "In Progress", 2: "Rejected", 4: "Approved and Sent"}
                    status = status_map.get(withdrawal.get("status"), "Unknown")
                    actual_points_withdrawn = withdrawal.get("point", 0) / 10000
                    points_received = withdrawal.get("money_price", 0) / 10000
                    receiver = withdrawal.get("pk_bank_user_name", "Unknown")
                    bank_name = withdrawal.get("pk_bank_name", "Unknown")
                    account_number = withdrawal.get("pk_bank_no", "Unknown")
                    itime = withdrawal.get("itime", datetime.now().timestamp())
                    date = datetime.fromtimestamp(itime).strftime("%Y-%m-%d")
                    # Filter by specific date if provided
                    if specific_date and date != specific_date:
                        continue
                    withdrawal_data = {
                        "username": username,
                        "account_number": account_number,
                        "bank_name": bank_name,
                        "account_title": receiver,
                        "status": status,
                        "actual_amount_withdrawn": actual_points_withdrawn,
                        "amount_received": points_received,
                        "date": date,
                        "timestamp": datetime.fromtimestamp(itime).strftime("%Y-%m-%d %H:%M")
                    }
                    withdrawal_data_list.append(withdrawal_data)
                    self.update_withdrawal_record(withdrawal_data)
                    print(
                        f"Withdrawal for {username}: Date: {date}, Status: {status}, "
                        f"Actual Amount: {actual_points_withdrawn}, Received: {points_received}, "
                        f"Account Number: {account_number}, Bank: {bank_name}, Title: {receiver}"
                    )
                return withdrawal_data_list
            else:
                print(f"No withdrawal records found for {username}")
                return []
        except Exception as e:
            print(f"Error checking withdrawal history for {username}: {e}")
            return []

    def update_withdrawal_record(self, withdrawal_data):
        """Update withdrawal records in Google Sheets."""
        try:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range="Withdrawals!A:G",
                valueInputOption="RAW",
                body={
                    "values": [
                        [
                            withdrawal_data["username"],
                            withdrawal_data["account_number"],
                            withdrawal_data["bank_name"],
                            withdrawal_data["account_title"],
                            withdrawal_data["status"],
                            str(withdrawal_data["actual_amount_withdrawn"]),
                            str(withdrawal_data["amount_received"])
                        ]
                    ]
                },
            ).execute()
            print(f"✓ Saved withdrawal record for {withdrawal_data['username']} to Google Sheets")
        except Exception as e:
            print(f"Error updating withdrawal record for {withdrawal_data['username']}: {e}")

    def check_withdrawals_by_date(self):
        """Check and save withdrawals for a specific date."""
        date_input = input("Enter the date to check withdrawals (format: YYYY-MM-DD, leave blank for all): ").strip()
        if date_input:
            try:
                datetime.strptime(date_input, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD.")
                return

        withdrawals = []
        for username in self.accounts:
            print(f"\nChecking withdrawals for {username}")
            token = self.login(username)
            if not token:
                continue
            withdrawal_data_list = self.check_withdrawal_history(token, username, limit=10, specific_date=date_input or None)
            withdrawals.extend(withdrawal_data_list)
            time.sleep(2)

        if not withdrawals:
            print(f"No withdrawals found{' for ' + date_input if date_input else ''}")
            return

        print(f"\nWithdrawals{' for ' + date_input if date_input else ''}:")
        for withdrawal in withdrawals:
            print(
                f"Username: {withdrawal['username']}, Date: {withdrawal['date']}, "
                f"Status: {withdrawal['status']}, Actual Amount: {withdrawal['actual_amount_withdrawn']}, "
                f"Received: {withdrawal['amount_received']}, Account Number: {withdrawal['account_number']}, "
                f"Bank: {withdrawal['bank_name']}, Title: {withdrawal['account_title']}"
            )

    def check_last_n_withdrawals(self):
        """Check the last N withdrawal statuses for all accounts."""
        try:
            limit = int(input("Enter the number of recent withdrawals to check (1-10): "))
            if limit < 1 or limit > 10:
                print("Please enter a number between 1 and 10.")
                return
        except ValueError:
            print("Invalid input. Please enter a number.")
            return

        withdrawals = []
        for username in self.accounts:
            print(f"\nChecking last {limit} withdrawals for {username}")
            token = self.login(username)
            if not token:
                continue
            withdrawal_data_list = self.check_withdrawal_history(token, username, limit=limit)
            withdrawals.extend(withdrawal_data_list)
            time.sleep(2)

        if not withdrawals:
            print(f"No withdrawals found for the last {limit} records")
            return

        print(f"\nLast {limit} withdrawals:")
        for withdrawal in withdrawals:
            print(
                f"Username: {withdrawal['username']}, Date: {withdrawal['date']}, "
                f"Status: {withdrawal['status']}, Actual Amount: {withdrawal['actual_amount_withdrawn']}, "
                f"Received: {withdrawal['amount_received']}, Account Number: {withdrawal['account_number']}, "
                f"Bank: {withdrawal['bank_name']}, Title: {withdrawal['account_title']}"
            )

    def run(self):
        """Main execution function."""
        print("Withdrawal History Checker")
        print("=" * 40)
        self.load_files()

        while True:
            print("\nMenu:")
            print("1. Check withdrawals by date")
            print("2. Check last N withdrawals")
            print("3. Exit")
            choice = input("Select an option (1-3): ")

            if choice == "1":
                self.check_withdrawals_by_date()
            elif choice == "2":
                self.check_last_n_withdrawals()
            elif choice == "3":
                print("Script completed. Goodbye!")
                break
            else:
                print("Invalid option, please select 1-3")

if __name__ == "__main__":
    checker = WithdrawalHistoryChecker()
    checker.run()