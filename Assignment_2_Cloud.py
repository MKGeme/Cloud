import streamlit as st  # Main library for creating the Streamlit web app.
import requests  # Library for making HTTP requests.
import json  # Library for JSON manipulation.
import time  # Module for working with time-related functions.

# Title of the Streamlit web app
st.title('Weather and Currency Exchange App')

# Displaying a static weather widget for Limassol
st.header('Weather in Limassol')
weather_url = 'http://api.openweathermap.org/data/2.5/weather?q=Limassol&appid=74cb3ddf21cf4ddf676f3e693fef7b6a'
weather_data = requests.get(weather_url).json()  # Fetching weather data using requests
temp_celsius = weather_data['main']['temp'] - 273.15  # Converting temperature from Kelvin to Celsius
st.write(f"Temperature: {temp_celsius:.2f}°C")
st.write(f"Weather: {weather_data['weather'][0]['description']}")

# Displaying a static exchange rate widget for EUR to USD, JPY, GBP
st.header('Exchange Rate (EUR to USD, JPY, GBP)')
exchange_url = 'https://open.er-api.com/v6/latest/EUR'
exchange_data = requests.get(exchange_url).json()  # Fetching exchange rates using requests
st.write(f"USD: {exchange_data['rates']['USD']}")
st.write(f"JPY: {exchange_data['rates']['JPY']}")
st.write(f"GBP: {exchange_data['rates']['GBP']}")

# Dynamic weather widget to input and display weather for a different city
city = st.text_input("Enter a city:")
if city:
    weather_url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid=74cb3ddf21cf4ddf676f3e693fef7b6a'
    weather_data = requests.get(weather_url).json()  # Fetching weather data for the input city
    temp_celsius = weather_data['main']['temp'] - 273.15
    st.write(f"Temperature in {city}: {temp_celsius:.2f}°C")

# Dropdown for currency selection
currencies = ['USD', 'JPY', 'GBP', 'EUR']
base_currency = st.selectbox("Select base currency:", currencies)
target_currencies = st.multiselect("Select target currencies:", currencies, default=['USD'])

# Displaying dynamic exchange rates based on selected currency
exchange_url = f'https://open.er-api.com/v6/latest/{base_currency}'
exchange_data = requests.get(exchange_url).json()
for currency in target_currencies:
    if currency != base_currency:
        st.write(f"{base_currency} to {currency}: {exchange_data['rates'][currency]}")
st.header('AWS Lambda Weather Data')
city_lambda = st.text_input("Enter a city for Lambda Weather:", key='city_lambda')

if st.button("Fetch Weather from AWS Lambda"):
    if city_lambda:
        weather_payload = {
            "weather_city": city_lambda
        }

        # Start time for calculating the request duration
        weather_request_start_time = time.time()

        # Send request to Lambda
        lambda_weather_response = requests.post("https://x0bxdl2bmg.execute-api.eu-north-1.amazonaws.com/prod/rates", json=weather_payload)

        # End time for request duration calculation
        weather_request_end_time = time.time()
        weather_request_duration = weather_request_end_time - weather_request_start_time

        if lambda_weather_response.status_code == 200:
            # Parse the JSON string from the response body
            lambda_response_body = json.loads(lambda_weather_response.json()['body'])

            # Check if the expected keys are in the parsed data
            if 'main' in lambda_response_body and 'temp' in lambda_response_body['main']:
                temp_celsius = lambda_response_body['main']['temp'] - 273.15
                st.write(f"Temperature in {city_lambda}: {temp_celsius:.2f}°C")
                st.write(f"Weather: {lambda_response_body['weather'][0]['description']}")
                st.write(f"Request duration: {weather_request_duration:.2f} seconds")
            else:
                st.error("Weather data not found in the response.")
        else:
            st.error("Error fetching weather data from AWS Lambda.")
    else:
        st.error("Please enter a city name.")
# Section for AWS Lambda Exchange Rate
st.header('AWS Lambda Exchange Rate')
base_currency_lambda = st.selectbox("Select base currency for Lambda:", currencies, key='base_lambda')
target_currencies_lambda = st.multiselect("Select target currencies for Lambda:", currencies, default=['USD'], key='target_lambda')

# Button to fetch data from AWS Lambda
if st.button("Fetch Rate from AWS Lambda"):
    payload = {
        "base": base_currency_lambda,
        "targets": target_currencies_lambda
    }

    # Start time for calculating the request duration
    request_start_time = time.time()  

    lambda_response = requests.post("https://x0bxdl2bmg.execute-api.eu-north-1.amazonaws.com/prod/rates", json=payload)
    
    # End time for request duration calculation
    request_end_time = time.time()    
    request_duration = request_end_time - request_start_time  # Calculating the request duration

    if lambda_response.status_code == 200:
        lambda_data = lambda_response.json()
        st.header('Exchange Rates')
        body_data = json.loads(lambda_data['body']) if isinstance(lambda_data['body'], str) else lambda_data['body']
        rates = body_data.get('rates', {})
        for currency, rate in rates.items():
            st.write(f"{base_currency_lambda} to {currency}: {rate}")

        # Displaying the request duration
        st.write(f"Request duration: {request_duration:.2f} seconds")
    else:
        st.error("Error fetching data from AWS Lambda.")
