from aiohttp import ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from datetime import datetime, timezone
from colorama import *
import asyncio, random, json, pytz, re, os

wib = pytz.timezone('Asia/Jakarta')


class Dawn:

    def __init__(self):

        self.BASE_API = "https://api.dawninternet.com"

        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.accounts = {}
        self.account_ips = {}
        self.account_user_agents = {}

        self.USER_AGENTS = [

            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36 OPR/117.0.0.0"

        ]

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):

        print(
            f"{Fore.CYAN}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def mask_email(self, email):

        if "@" not in email:
            return email

        local, domain = email.split("@")

        if len(local) <= 6:
            masked = local[0] + "***" + local[-1]
        else:
            masked = local[:3] + "***" + local[-3:]

        return f"{masked}@{domain}"

    def format_proxy(self, proxy):

        if not proxy:
            return "NoProxy"

        proxy = re.sub(r"^(http|https|socks4|socks5)://", "", proxy)

        if "@" in proxy:
            proxy = proxy.split("@")[1]

        return proxy

    def load_accounts(self):

        filename = "tokens.json"

        if not os.path.exists(filename):
            self.log("tokens.json not found")
            return []

        with open(filename) as f:
            data = json.load(f)

            if isinstance(data, list):
                return data

        return []

    def load_proxies(self):

        filename = "proxy.txt"

        if not os.path.exists(filename):
            return

        with open(filename) as f:
            self.proxies = [x.strip() for x in f if x.strip()]

        self.log(f"Loaded {len(self.proxies)} proxies")

    def check_proxy_schemes(self, proxy):

        if proxy.startswith(("http://", "https://", "socks4://", "socks5://")):
            return proxy

        return "http://" + proxy

    def get_next_proxy_for_account(self, account):

        if account not in self.account_proxies:

            if not self.proxies:
                return None

            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])

            self.account_proxies[account] = proxy

            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)

        return self.account_proxies[account]

    def build_proxy_config(self, proxy):

        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)

        if match:
            username, password, host = match.groups()
            proxy_url = f"http://{host}"
            auth = BasicAuth(username, password)
            return None, proxy_url, auth

        return None, proxy, None

    def initialize_headers(self, email):

        if email not in self.account_user_agents:

            ua = random.choice(self.USER_AGENTS)
            self.account_user_agents[email] = ua

            self.log(
                f"{self.mask_email(email)} device {ua}"
            )

        ua = self.account_user_agents[email]

        if email not in self.HEADERS:

            self.HEADERS[email] = {

                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "no-cache",
                "Authorization": f"Bearer {self.accounts[email]['session_token']}",
                "Origin": "chrome-extension://fpdkjdnhkakefebpekbdhillbhonfjjp",
                "Pragma": "no-cache",
                "User-Agent": ua

            }

        return self.HEADERS[email]

    async def get_ip(self, proxy):

        connector, proxy_url, proxy_auth = self.build_proxy_config(proxy)

        try:

            async with ClientSession(
                connector=connector,
                timeout=ClientTimeout(total=15)
            ) as session:

                async with session.get(
                    "https://api.ipify.org?format=json",
                    proxy=proxy_url,
                    proxy_auth=proxy_auth
                ) as r:

                    data = await r.json()
                    return data.get("ip")

        except:
            return None

    async def extension_ping(self, email, timestamp, proxy):

        url = f"{self.BASE_API}/ping"
        headers = self.initialize_headers(email)

        payload = {

            "user_id": self.accounts[email]["user_id"],
            "extension_id": "fpdkjdnhkakefebpekbdhillbhonfjjp",
            "timestamp": timestamp

        }

        connector, proxy_url, proxy_auth = self.build_proxy_config(proxy)

        try:

            async with ClientSession(
                connector=connector,
                timeout=ClientTimeout(total=60)
            ) as session:

                async with session.post(
                    url=url,
                    headers=headers,
                    json=payload,
                    proxy=proxy_url,
                    proxy_auth=proxy_auth
                ) as response:

                    response.raise_for_status()

                    return await response.json()

        except Exception as e:

            self.log(f"PING ERROR {self.mask_email(email)} {e}")

            return None

    async def user_point(self, email, proxy):

        url = f"{self.BASE_API}/point"
        headers = self.initialize_headers(email)

        params = {"user_id": self.accounts[email]["user_id"]}

        connector, proxy_url, proxy_auth = self.build_proxy_config(proxy)

        try:

            async with ClientSession(
                connector=connector,
                timeout=ClientTimeout(total=60)
            ) as session:

                async with session.get(
                    url=url,
                    headers=headers,
                    params=params,
                    proxy=proxy_url,
                    proxy_auth=proxy_auth
                ) as response:

                    response.raise_for_status()

                    return await response.json()

        except Exception as e:

            self.log(f"POINT ERROR {self.mask_email(email)} {e}")

            return None

    async def process_user_earning(self, email, proxy):

        while True:

            user = await self.user_point(email, proxy)

            if user:

                node_points = user.get("points", 0)
                referral_points = user.get("referral_points", 0)

                total = node_points + referral_points

                self.log(
                    f"{self.mask_email(email)} | {self.format_proxy(proxy)} | total points {total}"
                )

            await asyncio.sleep(random.randint(2700,3900))

    async def process_ping(self, email, proxy):

        while True:

            await asyncio.sleep(random.randint(2,7))

            current_ip = await self.get_ip(proxy)

            if email not in self.account_ips:

                self.account_ips[email] = current_ip

            elif current_ip != self.account_ips[email]:

                self.log(
                    f"{self.mask_email(email)} IP changed {self.account_ips[email]} -> {current_ip}"
                )

                self.account_ips[email] = current_ip

                await asyncio.sleep(random.randint(60,180))

            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

            await asyncio.sleep(random.randint(1,4))

            result = await self.extension_ping(email, timestamp, proxy)

            if result:

                self.log(
                    f"{self.mask_email(email)} | {self.format_proxy(proxy)} | ping success"
                )

            wait = random.randint(1020,1320)

            if random.random() < 0.08:

                idle = random.randint(300,1200)

                self.log(f"{self.mask_email(email)} device idle {idle} sec")

                wait += idle

            self.log(
                f"{self.mask_email(email)} | {self.format_proxy(proxy)} | next ping {wait} sec"
            )

            await asyncio.sleep(wait)

    async def process_accounts(self, email):

        await asyncio.sleep(random.randint(30,300))

        proxy = self.get_next_proxy_for_account(email)

        self.log(
            f"{self.mask_email(email)} using proxy {self.format_proxy(proxy)}"
        )

        tasks = [

            asyncio.create_task(self.process_user_earning(email, proxy)),
            asyncio.create_task(self.process_ping(email, proxy))

        ]

        await asyncio.gather(*tasks)

    async def main(self):

        accounts = self.load_accounts()

        if not accounts:
            return

        self.load_proxies()

        self.clear_terminal()

        self.log(f"Accounts loaded: {len(accounts)}")

        tasks = []

        for account in accounts:

            email = account.get("email")

            self.accounts[email] = {

                "user_id": account.get("userId"),
                "session_token": account.get("sessionToken")

            }

            tasks.append(asyncio.create_task(self.process_accounts(email)))

        await asyncio.gather(*tasks)


if __name__ == "__main__":

    try:

        bot = Dawn()

        asyncio.run(bot.main())

    except KeyboardInterrupt:

        print("EXIT Dawn BOT")
