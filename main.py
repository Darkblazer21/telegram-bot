import requests
import json 
from pathlib import Path


currencies = ("USD", "EUR", "XOF")
BASE_URL = "https://api.frankfurter.dev"
RATES_ENDPOINT = BASE_URL + "/v2/rates"

r = requests.get(RATES_ENDPOINT)


contents = r.json()
list_of_contents = list(contents)

path = Path("exchange_rates.txt")

if not path.exists():
    data = json.dumps(list_of_contents)
    path.write_text(data)
