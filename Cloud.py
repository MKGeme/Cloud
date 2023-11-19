import streamlit as st  # Main library for creating the Streamlit web app.
import requests  # Library for making HTTP requests.
import json  # Library for JSON manipulation.
import boto3  # AWS SDK for Python, used for accessing AWS services like CloudWatch.
import time  # Module for working with time-related functions.
from datetime import datetime, timedelta  # Modules for handling date and time operations.


aws_access_key_id = "AKIAVN57TFQOMY5BMVWG"
aws_secret_access_key = "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"
region_name = "eu-north-1"


# Initialize the boto3 client for CloudWatch
# This setup is for interacting with AWS CloudWatch service.
cloudwatch = boto3.client(
    'cloudwatch',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

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

        # Fetching and displaying AWS Lambda metrics
        st.header('AWS Lambda Metrics')
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        # Function to fetch specific Lambda metrics
        def get_lambda_metric(metric_name, statistics):
            return cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName=metric_name,
                Dimensions=[{'Name': 'FunctionName', 'Value': 'currencyandperformance'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=statistics
            )

        # Fetching various metrics
        invocations_metric = get_lambda_metric('Invocations', ['Sum'])
        errors_metric = get_lambda_metric('Errors', ['Sum'])
        throttles_metric = get_lambda_metric('Throttles', ['Sum'])

        # Calculating success rate
        total_invocations = sum(dp['Sum'] for dp in invocations_metric['Datapoints'])
        total_errors = sum(dp['Sum'] for dp in errors_metric['Datapoints'])
        success_rate = ((total_invocations - total_errors) / total_invocations) * 100 if total_invocations else 0

        # Preparing metrics data for display
        metrics_data = [
            {'Metric': 'Invocations', 'Value': total_invocations},
            {'Metric': 'Errors', 'Value': total_errors},
            {'Metric': 'Success Rate (%)', 'Value': f"{success_rate:.2f}"},
            {'Metric': 'Throttles', 'Value': sum(dp['Sum'] for dp in throttles_metric['Datapoints'])},
        ]

        # Displaying metrics in a table
        st.table(metrics_data)
        st.subheader("Metrics Legend")
        st.write("""
            - **Invocations:** Total number of times the Lambda function was invoked in the specified period.
            - **Errors:** Total number of times the Lambda function execution resulted in an error.
            - **Success Rate (%):** Percentage of successful invocations out of total invocations. Calculated as \((Total Invocations - Errors) / Total Invocations \times 100\).
            - **Throttles:** Total number of invocation requests that were throttled due to reaching AWS Lambda limits.
        """)
        st.write(f"Request duration: {request_duration:.2f} seconds")
    else:
        st.error("Error fetching data from AWS Lambda.")


