import asyncio
import aiohttp
import random
import json
import os
import logging
from datetime import datetime

# Setup Logging
logging.basicConfig(filename="bot.log", level=logging.INFO, 
                    format="%(asctime)s [%(levelname)s] %(message)s")

# API Endpoints
LOGIN_URL = "https://api.blockmesh.xyz/api/get_token"
REPORT_URL = "https://app.blockmesh.xyz/api/report_uptime"
SUBMIT_BANDWIDTH_URL = "https://app.blockmesh.xyz/api/submit_bandwidth"
GET_TASK_URL = "https://app.blockmesh.xyz/api/get_task"
SUBMIT_TASK_URL = "https://app.blockmesh.xyz/api/submit_task"
POINTS_URL = "https://app.blockmesh.xyz/api/get_points"

# Headers
HEADERS = {
    "accept": "*/*",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0 Safari/537.36"
}

# Global Proxy Pool & Tokens
proxy_tokens = {}
proxy_list = []


async def load_proxies():
    """Load proxies from proxies.txt"""
    global proxy_list
    if os.path.exists("proxies.txt"):
        with open("proxies.txt", "r") as file:
            proxy_list = file.read().splitlines()
        logging.info(f"Loaded {len(proxy_list)} proxies.")
    else:
        logging.error("proxies.txt not found!")
        exit()


def format_proxy(proxy_string):
    """Format proxy from string"""
    proxy_type, address = proxy_string.split("://")
    if "@" in address:
        credentials, host_port = address.split("@")
        username, password = credentials.split(":")
        host, port = host_port.split(":")
        proxy_dict = {
            "http": f"{proxy_type}://{username}:{password}@{host}:{port}",
            "https": f"{proxy_type}://{username}:{password}@{host}:{port}"
        }
    else:
        host, port = address.split(":")
        proxy_dict = {
            "http": f"{proxy_type}://{host}:{port}",
            "https": f"{proxy_type}://{host}:{port}"
        }
    return proxy_dict, host


async def request_with_retries(url, session, method="GET", json_data=None, proxy=None, max_retries=3):
    """Make API requests with retry logic"""
    for attempt in range(max_retries):
        try:
            async with session.request(method, url, json=json_data, proxy=proxy, headers=HEADERS, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status in {429, 500, 502, 503, 504}:  # Rate limit or server errors
                    logging.warning(f"Retrying {url} (Attempt {attempt+1}) - Status {response.status}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logging.error(f"Failed {url} - Status {response.status}")
                    return None
        except Exception as e:
            logging.error(f"Request error: {e}")
    return None


async def authenticate(email, password, proxy):
    """Authenticate and get API token"""
    proxy_config, ip_address = format_proxy(proxy)
    async with aiohttp.ClientSession() as session:
        data = {"email": email, "password": password}
        response = await request_with_retries(LOGIN_URL, session, "POST", data, proxy_config["http"])
        if response and "api_token" in response:
            proxy_tokens[proxy] = response["api_token"]
            logging.info(f"Login successful for {ip_address}")
            return response["api_token"], ip_address
        logging.error(f"Login failed for {ip_address}")
    return None, None


async def submit_bandwidth(email, api_token, ip_address, proxy):
    """Submit bandwidth stats"""
    proxy_config, _ = format_proxy(proxy)
    data = {
        "email": email,
        "api_token": api_token,
        "download_speed": round(random.uniform(0.0, 10.0), 16),
        "upload_speed": round(random.uniform(0.0, 5.0), 16),
        "latency": round(random.uniform(20.0, 300.0), 16),
        "ip": ip_address
    }
    async with aiohttp.ClientSession() as session:
        response = await request_with_retries(SUBMIT_BANDWIDTH_URL, session, "POST", data, proxy_config["http"])
        if response:
            logging.info(f"Bandwidth submitted for {ip_address}")


async def get_and_submit_task(email, api_token, ip_address, proxy):
    """Fetch and submit task"""
    proxy_config, _ = format_proxy(proxy)
    data = {"email": email, "api_token": api_token}
    async with aiohttp.ClientSession() as session:
        task_response = await request_with_retries(GET_TASK_URL, session, "POST", data, proxy_config["http"])
        if task_response and "id" in task_response:
            task_id = task_response["id"]
            await asyncio.sleep(random.randint(60, 120))  # Simulate task execution
            submit_data = {
                "email": email,
                "api_token": api_token,
                "task_id": task_id,
                "response_code": 200,
                "ip": ip_address
            }
            response = await request_with_retries(SUBMIT_TASK_URL, session, "POST", submit_data, proxy_config["http"])
            if response:
                logging.info(f"Task {task_id} submitted for {ip_address}")
                await get_points(email, api_token, proxy)  # Fetch updated points after task


async def get_points(email, api_token, proxy):
    """Fetch and log user points"""
    proxy_config, _ = format_proxy(proxy)
    async with aiohttp.ClientSession() as session:
        data = {"email": email, "api_token": api_token}
        response = await request_with_retries(POINTS_URL, session, "POST", data, proxy_config["http"])
        if response and "points" in response:
            points = response["points"]
            logging.info(f"Total Points: {points}")
            print(f"[INFO] Total Points: {points}")  # Display points


async def send_uptime_report(email, api_token, ip_address, proxy):
    """Send uptime report"""
    proxy_config, _ = format_proxy(proxy)
    async with aiohttp.ClientSession() as session:
        url = f"{REPORT_URL}?email={email}&api_token={api_token}&ip={ip_address}"
        response = await request_with_retries(url, session, "POST", proxy=proxy_config["http"])
        if response:
            logging.info(f"Uptime report sent for {ip_address}")


async def process_proxy(proxy, email, password):
    """Handle tasks for a single proxy"""
    while True:
        if proxy not in proxy_tokens:
            api_token, ip_address = await authenticate(email, password, proxy)
        else:
            api_token = proxy_tokens[proxy]
            _, ip_address = format_proxy(proxy)

        if api_token:
            await submit_bandwidth(email, api_token, ip_address, proxy)
            await get_and_submit_task(email, api_token, ip_address, proxy)
            await send_uptime_report(email, api_token, ip_address, proxy)
        await asyncio.sleep(random.randint(900, 1200))  # 15-20 min delay


async def main():
    """Main function"""
    await load_proxies()
    email = input("Enter Email: ")
    password = input("Enter Password: ")
    tasks = [process_proxy(proxy, email, password) for proxy in proxy_list]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Script stopped by user.")
