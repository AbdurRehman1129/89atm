import requests

import json

import time

import random

import hashlib

from datetime import datetime

import os

from playsound import playsound  # For audio notification

from plyer import notification  # For desktop notification

from dotenv import load_dotenv  # For loading .env file

import telegram  # For Telegram bot integration

import asyncio



class WhatsAppLinker:

    def __init__(self):

        self.base_url = "https://api.89atm.me"

        self.session = requests.Session()

        self.accounts = []

        self.passwords = []

        self.numbers = []

        self.sent_codes = []

        self.signed_in_accounts = {}  # Track accounts that have signed in today

        # Load .env file

        load_dotenv()

        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        self.bot = None

        self.loop = None

        if self.telegram_token and self.telegram_chat_id:

            try:

                self.bot = telegram.Bot(token=self.telegram_token)

                # Create a single event loop for async operations

                self.loop = asyncio.new_event_loop()

                asyncio.set_event_loop(self.loop)

            except Exception as e:

                print(f"✗ Failed to initialize Telegram bot: {e}")

                self.bot = None



    async def send_telegram_message(self, number, linking_code):

        """Send number and linking code to Telegram chat"""

        if not self.bot:

            print("  ⚠ Telegram bot not initialized, skipping message sending")

            return

        

        try:

            # Send number in first message

            await self.bot.send_message(

                chat_id=self.telegram_chat_id,

                text=f"Number: {number}"

            )

            # Send linking code in second message with code formatting

            await self.bot.send_message(

                chat_id=self.telegram_chat_id,

                text=f"Linking Code: `{linking_code}`",

                parse_mode='Markdown'

            )

            print("  ✓ Telegram messages sent successfully")

        except Exception as e:

            print(f"  ✗ Failed to send Telegram message: {e}")



    def run_async_task(self, coro):

        """Run an async coroutine in the event loop"""

        if self.loop and not self.loop.is_closed():

            return self.loop.run_until_complete(coro)

        else:

            print("  ✗ Event loop is closed or not initialized")

            return None



    def close_loop(self):

        """Close the event loop cleanly"""

        if self.loop and not self.loop.is_closed():

            self.loop.close()

            print("  ✓ Event loop closed")



    def generate_fake_user_agent(self):

        """Generate a fake user agent with randomized browser/engine"""

        chrome_versions = ['138.0.0.0', '137.0.0.0', '136.0.0.0', '135.0.0.0', '139.0.0.0', '140.0.0.0', '141.0.0.0', '142.0.0.0', '143.0.0.0', '144.0.0.0', '145.0.0.0', '146.0.0.0', '147.0.0.0', '148.0.0.0']

        firefox_versions = ['120.0', '119.0', '118.0', '117.0', '121.0', '122.0', '123.0', '124.0', '125.0', '126.0', '127.0', '128.0', '129.0', '130.0']

        edge_versions = ['118.0.2088.46', '117.0.2045.31', '116.0.1938.62', '119.0.2151.97', '120.0.2210.61', '121.0.2277.83', '122.0.2365.66', '123.0.2420.53', '124.0.2478.51', '125.0.2535.85', '126.0.2592.68', '127.0.2651.74', '128.0.2739.42']

        windows_versions = ['10.0', '11.0', '12.0', '13.0', '14.0', '15.0', '16.0', '17.0', '18.0', '19.0', '20.0', '21.0']

        macos_versions = ['10_15_7', '11_6', '12_6', '13_5', '14_0', '14_1', '14_2', '14_3', '14_4', '14_5', '15_0', '15_1']

        linux_versions = ['x86_64', 'i686', 'arm64', 'aarch64', 'x86', 'i386', 'ppc64le', 's390x', 'riscv64', 'loongarch64', 'mips64', 'sparc64']

        engines = [

            {

                'name': 'Chrome',

                'templates': [

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",

                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 OPR/101.0.0.0",

                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 OPR/101.0.0.0",

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64; rv:109.0) Gecko/20100101 Firefox/{random.choice(firefox_versions)} Chrome/{random.choice(chrome_versions)}",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)}",

                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 UCBrowser/13.4.0.1306",

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Vivaldi/6.2"

                ]

            },

            {

                'name': 'Firefox',

                'templates': [

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64; rv:{random.choice(firefox_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)}",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}; rv:{random.choice(firefox_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)}",

                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}; rv:{random.choice(firefox_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)}",

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; WOW64; rv:{random.choice(firefox_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)}",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)} Waterfox/102.0",

                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)} PaleMoon/32.0.0",

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) Gecko/20100101 Firefox/{random.choice(firefox_versions)} TorBrowser/12.0",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)} LibreWolf/110.0",

                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}) Gecko/20100101 Firefox/{random.choice(firefox_versions)} Iceweasel/110.0",

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) Gecko/20100101 Firefox/{random.choice(firefox_versions)} SeaMonkey/2.53.9"

                ]

            },

            {

                'name': 'Edge',

                'templates': [

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)}",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)}",

                    f"Mozilla/5.0 (OpenBSD; amd 64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)}",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 EdgA/{random.choice(edge_versions)}",

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)}",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 EdgA/{random.choice(edge_versions)}",

                    f"Mozilla/5.0 (X11; Linux {random.choice(linux_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)} OPR/101.0.0.0",

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)} UCBrowser/13.4.0.1306",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)} CocCoc/110.0.0",

                    f"Mozilla/5.0 (Windows NT {random.choice(windows_versions)}; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)} Brave/1.45.0",

                    f"Mozilla/5.0 (Macintosh; Intel Mac OS X {random.choice(macos_versions)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(chrome_versions)} Safari/537.36 Edg/{random.choice(edge_versions)} SamsungInternet/18.0"

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

            

            self.load_numbers()  # Load numbers initially

            

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

    

    def load_numbers(self):

        """Load numbers from num.txt"""

        try:

            with open('num.txt', 'r') as f:

                self.numbers = [line.strip() for line in f.readlines() if line.strip()]

        except FileNotFoundError:

            print("Error: num.txt file not found")

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

        # Use platform-safe date format

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

                    linking_data = (data.get('data', {}))

                    linking_code = linking_data.get('code')

                    print(f"    ✓ Linking code generated: {linking_code}")

                    

                    # Play notification sound

                    try:

                        sound_path = os.path.join(os.path.dirname(__file__), 'src', 'notification.mp3')

                        playsound(sound_path)

                        print("    🎵 Notification sound played")

                    except Exception as e:

                        print(f"    ⚠ Failed to play notification sound: {e}")

                    

                    # Show desktop notification

                    try:

                        notification.notify(

                            title='Linking Code Generated',

                            message=f'Code: {linking_code} for number {number}',

                            app_name='WhatsAppLinker',

                            timeout=10

                        )

                        print("    🔔 Desktop notification shown
