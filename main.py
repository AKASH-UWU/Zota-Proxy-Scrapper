import requests
import json
import logging
import sys
import re
import time as t
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import RequestException, ProxyError, ConnectTimeout
from colorama import Fore, Style, init
import tomli

# Initialize colorama
init(autoreset=True)

# Global variables for shutdown control
shutdown_flag = threading.Event()

# Load configuration
def load_config(file_path):
    try:
        with open(file_path, 'rb') as f:
            config = tomli.load(f)
        return config
    except Exception as e:
        print(f"{Fore.RED}Error loading configuration file: {e}{Style.RESET_ALL}")
        sys.exit(1)

# Setup logging based on configuration
def setup_logging(debug_mode):
    level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    return logger

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    print(f"\n{Fore.YELLOW}Interrupt received, stopping gracefully...{Style.RESET_ALL}")
    shutdown_flag.set()

# Function to get URLs from urls.txt
def get_urls(file_path):
    try:
        with open(file_path, 'r') as file:
            urls = file.read().splitlines()
        logger.info(f"Loaded {len(urls)} URLs from {file_path}")
        return urls
    except Exception as e:
        logger.error(f"Error reading URLs from {file_path}: {e}")
        return []

# Function to scrape proxies from a given URL
def scrape_proxies(url):
    proxies = set()
    try:
        logger.info(f"Scraping proxies from {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
        proxies.update(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}:\d+\b', content))
    except RequestException as e:
        logger.error(f"Error scraping proxies from {url}: {e}")
    return proxies

# Function to save proxies to raw.txt
def save_proxies_to_file(proxies, file_path):
    try:
        # Clear the file content
        open(file_path, 'w').close()
        with open(file_path, 'a') as file:
            for proxy in proxies:
                file.write(f"{proxy}\n")
        logger.info(f"Saved {len(proxies)} proxies to {file_path}")
    except Exception as e:
        logger.error(f"Error saving proxies to {file_path}: {e}")

# Function to remove duplicates from raw.txt
def remove_duplicates(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.read().splitlines()
        unique_lines = set(lines)
        with open(file_path, 'w') as file:
            for line in unique_lines:
                file.write(f"{line}\n")
        logger.info(f"Removed duplicates from {file_path}. Total unique proxies: {len(unique_lines)}")
    except Exception as e:
        logger.error(f"Error removing duplicates from {file_path}: {e}")

# Function to get raw proxies from raw.txt
def get_raw_proxies(file_path):
    try:
        with open(file_path, 'r') as file:
            raw_proxies = file.read().splitlines()
        logger.info(f"Loaded {len(raw_proxies)} proxies from {file_path}")
        return raw_proxies
    except Exception as e:
        logger.error(f"Error reading proxies from {file_path}: {e}")
        return []

# Function to check if a proxy is working
def check_proxy(proxy):
    test_url = "http://www.geoplugin.net/json.gp"
    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }
    
    # Immediately check if shutdown is requested
    if shutdown_flag.is_set():
        raise Exception("Shutdown requested")  # Trigger thread to stop

    start_time = t.time()  # Start time for latency measurement
    try:
        if debug_mode:
            logger.debug(f"Testing proxy {proxy}")
        response = requests.get(test_url, proxies=proxies, timeout=10)
        response.raise_for_status()
        geo_data = response.json()
        country = geo_data.get("geoplugin_countryName", "Unknown")
        latency = int((t.time() - start_time) * 1000)  # Calculate latency in ms
        if debug_mode:
            logger.debug(f"Proxy {proxy} is working. Country: {country}. Latency: {latency} ms")
        return {"proxy": proxy, "country": country, "latency": latency}
    except (RequestException, ProxyError, ConnectTimeout) as e:
        if debug_mode:
            logger.debug(f"Error connecting to proxy {proxy}: {e}")
        return None
    finally:
        # Avoid logging the shutdown message here
        if shutdown_flag.is_set():
            raise Exception("Shutdown requested")  # Trigger thread to stop

# Function to save the working proxies to a JSON file
def save_working_proxies(proxies, filename):
    try:
        with open(filename, 'w') as f:
            json.dump(proxies, f, indent=4)
        logger.info(f"Saved {len(proxies)} working proxies to {filename}")
    except Exception as e:
        logger.error(f"Error saving proxies to {filename}: {e}")

# Function to update status
def update_status(total, success, failed, remaining, latest_ping):
    clear_console()
    ping_display = f"Ping: {latest_ping} ms" if latest_ping is not None else "Ping: N/A"
    sys.stdout.write(f"\r{Fore.GREEN}Proxy count: {total}, Success: {success}, Failed: {failed}, Remaining: {remaining}, Thread: {thread_count}, {ping_display}{Style.RESET_ALL}")
    sys.stdout.flush()

# Function to clear the console
def clear_console():
    sys.stdout.write("\033c")
    sys.stdout.flush()

def main():
    # Load configuration and set up logging
    config = load_config("config.toml")
    global debug_mode
    debug_mode = config.get("debug_mode", False)
    global thread_count
    thread_count = config.get("thread_count", 50)
    
    global logger
    logger = setup_logging(debug_mode)

    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    urls_file_path = "urls.txt"  # Path to the file containing URLs to scrape
    proxies_file_path = "raw.txt"  # Path to the file where proxies will be saved
    
    # Step 1: Scrape proxies from URLs
    print(f"{Fore.CYAN}Starting proxy scraping...{Style.RESET_ALL}")
    t.sleep(1)
    urls = get_urls(urls_file_path)
    if not urls:
        clear_console()
        print(f"{Fore.RED}No URLs to scrape. Exiting...{Style.RESET_ALL}")
        t.sleep(3)
        return
    
    all_proxies = set()
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        future_to_url = {executor.submit(scrape_proxies, url): url for url in urls}
        for future in as_completed(future_to_url):
            proxies = future.result()
            all_proxies.update(proxies)
            if shutdown_flag.is_set():
                print(f"{Fore.YELLOW}Shutdown requested during scraping.{Style.RESET_ALL}")
                return
    
    # Clear console and show status
    clear_console()
    print(f"{Fore.GREEN}Proxies scraped successfully.{Style.RESET_ALL}")
    t.sleep(1)
    
    # Step 2: Save proxies to raw.txt
    print(f"{Fore.CYAN}Saving proxies to {proxies_file_path}...{Style.RESET_ALL}")
    save_proxies_to_file(all_proxies, proxies_file_path)
    clear_console()
    t.sleep(1)

    # Step 3: Remove duplicates from raw.txt
    print(f"{Fore.CYAN}Removing duplicates from {proxies_file_path}...{Style.RESET_ALL}")
    remove_duplicates(proxies_file_path)
    t.sleep(1)
    clear_console()
    
    # Step 4: Check proxies
    print(f"{Fore.CYAN}Checking proxies...{Style.RESET_ALL}")
    raw_proxies = get_raw_proxies(proxies_file_path)
    t.sleep(2)
    clear_console()
    
    if not raw_proxies:
        clear_console()
        print(f"{Fore.RED}No proxies to check. Exiting...{Style.RESET_ALL}")
        t.sleep(3)
        return
    
    total_proxies = len(raw_proxies)
    success_count = 0
    failed_count = 0
    working_proxies = []
    latest_ping = None
    
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        future_to_proxy = {executor.submit(check_proxy, proxy): proxy for proxy in raw_proxies}
        for future in as_completed(future_to_proxy):
            result = future.result()
            if result:
                working_proxies.append(result)
                success_count += 1
                latest_ping = result.get("latency")  # Update the latest ping
            else:
                failed_count += 1
            remaining_count = total_proxies - (success_count + failed_count)
            update_status(total_proxies, success_count, failed_count, remaining_count, latest_ping)
            t.sleep(0.1)  # Add a small delay to avoid overloading
            if shutdown_flag.is_set():
                print(f"\n{Fore.YELLOW}Shutdown requested during proxy checking.{Style.RESET_ALL}")
                break
    
    clear_console()
    print(f"{Fore.GREEN}Proxy checking completed.{Style.RESET_ALL}")
    
    # Save working proxies to file
    save_working_proxies(working_proxies, "working_proxies.json")

if __name__ == "__main__":
    main()
