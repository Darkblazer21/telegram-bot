import json
from pathlib import Path

import requests

currencies = ("USD", "EUR", "XOF")
BASE_URL = "https://api.frankfurter.dev"  # Base URL to the Frankfurter API
RATES_ENDPOINT = BASE_URL + "/v2/rates"  # Rates endpoint to the Frankfurter API

r = requests.get(RATES_ENDPOINT)  # Store the rates response in the variable


contents = r.json()  # Converts the response in Json format
list_of_contents = list(contents)  # Converts the response into a list

path = Path("exchange_rates.txt")  # The path to the exchange rates file

# Check if the path exists
if not path.exists():
    data = json.dumps(list_of_contents)  # Store the data in Json format
    path.write_text(data)  # Write the data content in the file
