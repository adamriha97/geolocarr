from dotenv import load_dotenv
import os
import requests
import json
import pandas as pd


def validateAddress(url, address):
    # Define the JSON data you want to send in the POST request
    body = {
        "address": {
            "regionCode": "CZ",
            "addressLines": [address]
        },
    }

    # Send the POST request with the JSON data
    response = requests.post(url, json=body)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        print("POST request was successful!")
        print("Response:")
        print(response.json())
        # Define the filename for the JSON response
        folder_name = 'validated_addresses'
        json_filename = os.path.join(folder_name, f'{address}.json')

        # Save the JSON response to a file
        with open(json_filename, 'w') as json_file:
            json.dump(response.json(), json_file)
        print(f"JSON response saved to {json_filename} file.")
        return response.json()
    else:
        print("POST request failed with status code:", response.status_code)

def addAddressToDF(address):
    global val_addr_df
    folder_name = 'validated_addresses'
    json_filename = os.path.join(folder_name, f'{address}.json')
    with open(json_filename, 'r') as f:
        json_data = json.load(f)
    
    new_row_data = {
        'orig_string': address
    }
    new_row_df = pd.DataFrame([new_row_data])
    val_addr_df = pd.concat([val_addr_df, new_row_df], ignore_index=True)

    val_addr_df.loc[val_addr_df['orig_string'] == address, 'latitude'] = json_data['result']['geocode']['location']['latitude']
    val_addr_df.loc[val_addr_df['orig_string'] == address, 'longitude'] = json_data['result']['geocode']['location']['longitude']

    components = json_data['result']['address']['addressComponents']
    for component in components:
        if component['confirmationLevel'] == 'CONFIRMED':
            val_addr_df.loc[val_addr_df['orig_string'] == address, component['componentType']] = component['componentName']['text']

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Access environment variables
    api_url = os.getenv('GOOGLE_MAPS_PLATFORM_API_URL')
    api_key = os.getenv('GOOGLE_MAPS_PLATFORM_API_KEY')

    # Define the endpoint URL
    api_url_with_api_key = api_url + '?key=' + api_key

    df = pd.read_csv('output.csv') # bude nutno prepsat
    df['address_for_validation'] = df['ulice'] + ' ' + df['psc'] + ' ' + df['mesto'] # bude nutno prepsat
    addresses = df['address_for_validation'].tolist()
    #addresses = addresses[:5] # bude nutno smazat

    columns = ['locality', 'route', 'street_number', 'postal_code', 'sublocality_level_1', 'neighborhood', 'country', 'latitude', 'longitude', 'orig_string']
    val_addr_df = pd.DataFrame(columns=columns)

    for address in addresses:
        response = validateAddress(url=api_url_with_api_key, address=address)
        addAddressToDF(address)
    
    csv_file = 'output_new.csv'
    val_addr_df.to_csv(csv_file, index=False)
    print(val_addr_df)