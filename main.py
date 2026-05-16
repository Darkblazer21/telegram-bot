import json
from pathlib import Path
from time import localtime, strftime

import requests

currencies = ("USD", "EUR", "XOF")
euro, dollar, xof = currencies

BASE_URL = "https://api.frankfurter.dev"  # Base URL to the Frankfurter API
RATES_ENDPOINT = BASE_URL + "/v2/rates"  # Rates endpoint to the Frankfurter API
EUR_USD_ENDPOINT = RATES_ENDPOINT + f"/{euro}/{dollar}"

r = requests.get(EUR_USD_ENDPOINT)  # Store the rates response in the variable


contents = r.json()  # Converts the response in Json format
list_of_contents = list(contents)  # Converts the response into a list

path = Path("exchange_rates.txt")  # The path to the exchange rates file

# Check if the path exists
if not path.exists():
    data = json.dumps(list_of_contents)  # Store the data in Json format
    path.write_text(data)  # Write the data content in the file


current_time = strftime("%Y-%m-%d", localtime())
print(current_time)

print(euro, dollar, xof)

contents = path.read_text()
data = json.loads(contents)
print(type(data))

relevant_data = []

for item in data:
    if (
        item.get("date") == current_time
        and item.get("base") == dollar
        and item.get("quote") == euro
    ) or (
        item.get("date") == current_time
        and item.get("base") == euro
        and item.get("quote") == dollar
    ):
        relevant_data.append(item)

print(relevant_data)
print(len(relevant_data))
