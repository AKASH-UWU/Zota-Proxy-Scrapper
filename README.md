# Zota Proxy Scrapper - AkashUwU

## Description

Zota Proxy Scrapper is a Python script that scrapes proxy addresses from specified URLs, validates them, and saves working proxies to a JSON file. It uses multithreading for efficient processing and supports graceful shutdowns. The project includes functionality for checking proxy performance, such as pinging the latest proxy and providing status updates.

## Features

- Scrapes proxies from multiple URLs
- Removes duplicates from the list of proxies
- Validates proxies by testing their connectivity
- Provides status updates including proxy count, success, failures, remaining proxies, and latency
- Supports graceful shutdown with interrupt handling

## Installation

### Prerequisites

- Python 3.6 or higher

### Setup

1. **Clone the repository:**

```bash
git clone https://github.com/AKASH-UWU/Zota-Proxy-Scrapper.git
cd Zota-Proxy-Scrapper
```



2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Usage:**

- Prepare your URLs file:

- Create a urls.txt file in the root directory containing one URL per line from which proxies will be scraped.

4. **Run the script:**

```bash
python3 main.py
```

## Check the output:

- Proxies will be saved in raw.txt.
- Working proxies will be saved in working_proxies.json.


## Additional Information
- Ping Measurement: The script shows latency in milliseconds for the latest proxy.
- Graceful Shutdown: Use Ctrl + C to stop the script gracefully.
- Troubleshooting
- Errors loading configuration file: Ensure config.toml is correctly formatted.
- Errors reading proxies: Check the format of urls.txt and raw.txt.




## License

This project is using the MIT license, see in [MIT LICENSE](./LICENSE).

## Contributing

Feel free to open issues or submit pull requests. Contributions are welcome!

