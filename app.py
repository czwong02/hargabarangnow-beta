from flask import Flask, render_template, request, redirect, url_for
import csv
import random
from collections import defaultdict
from urllib.parse import unquote, quote
import os
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    # Redirect to the /index route
    return redirect(url_for("index"))


@app.route("/index")
def index():
    # Read the CSV file and aggregate items
    aggregated_items = {}

    with open("dataset/latest_prices_by_item_and_state.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item_name = row["item_name"]
            state = row["state"]
            price = float(row["latest_price"])

            if item_name not in aggregated_items:
                aggregated_items[item_name] = {"latest_price": price, "States": {}}

            # Update the state price
            aggregated_items[item_name]["States"][state] = price

    # Convert aggregated items to a list of dictionaries with sorted states
    processed_items = [
        {
            "item_name": item_name,
            "latest_price": data["latest_price"],
            "state": sorted(
                data["States"].items(), key=lambda x: x[1]
            ),  # Sort states by price
        }
        for item_name, data in aggregated_items.items()
    ]

    # Randomly select 20 items from processed_items
    if len(processed_items) > 30:
        processed_items = random.sample(processed_items, 20)

    # Read the CSV file for percentage increments
    percentage_increments = {}
    with open("dataset/percentage_increments.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        # Store percentage increments for each item in a dictionary
        for row in reader:
            item_name = row["Item"]
            increment = float(row["Percentage Increment"])
            percentage_increments[item_name] = increment

    itemAll = []
    with open("dataset/all premise latest price.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            item = row["item"]
            price = float(row["price"])
            state = row["state"]
            premise = row["premise"]

            itemAll.append(
                {"item": item, "price": price, "state": state, "premise": premise}
            )

    raw_food_items = []
    processed_food_items = []
    item_groups = defaultdict(list)

    # Read the CSV file and classify food items as raw or processed
    with open("dataset/all premise latest price.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            item = row["item"]
            price = float(row["price"])
            state = row["state"]
            premise = row["premise"]
            item_category = row[
                "item_group"
            ]  # Assuming there's a column for item category
            growth = float(row.get("growth", 0))  # Get growth percentage if available

            item_data = {
                "item": item,
                "price": price,
                "state": state,
                "premise": premise,
                "growth": growth,
            }

            # Group items by item name for random selection later
            item_groups[item].append(item_data)

            # Classify into raw food and processed food
            if item_category == "BARANGAN SEGAR":  # Example category for raw food
                raw_food_items.append(item_data)
            elif (
                item_category == "BARANGAN BERBUNGKUS"
            ):  # Processed food or other categories
                processed_food_items.append(item_data)

    def select_unique_items(item_list):
        selected_items = []
        grouped_by_item = defaultdict(list)

        # Group items by their names and premises
        for item_data in item_list:
            item_name = item_data["item"]
            grouped_by_item[item_name].append(item_data)

        # For each item, select up to 5 unique items with different premises
        for item_name, group in grouped_by_item.items():
            unique_premises = {
                item["premise"]: item for item in group
            }  # Remove duplicates by premise
            selected_items += random.sample(
                list(unique_premises.values()), min(5, len(unique_premises))
            )

        return selected_items

    # Select random 5 items with unique premises for itemAll, raw_food_items, and processed_food_items
    itemAll = select_unique_items(itemAll)
    raw_food_items = select_unique_items(raw_food_items)
    processed_food_items = select_unique_items(processed_food_items)

    # Remove the 5-item limit for all_unique_items
    all_unique_items = list(
        set([item["item"] for item in raw_food_items + processed_food_items])
    )

    # Render the HTML page with both processed items and percentage increments
    return render_template(
        "index.html",
        items=processed_items,
        increments=percentage_increments,
        itemAll=itemAll,
        raw_food_items=raw_food_items,
        processed_food_items=processed_food_items,
        all_unique_items=all_unique_items,
    )


@app.route("/item")
def item():
    raw_items = []
    processed_items = []

    # Reading data from the CSV file
    with open("dataset/100 raw food list.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            raw_items.append(
                {
                    "name": row["item_name"],
                    "url": "/product/" + quote(row["item_name"]) + "/Johor",
                }
            )  # Assuming 'item_name' is the column storing item names

    # Reading data from the CSV file
    with open("dataset/52 processed food list.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            processed_items.append(
                {"name": row["item"], "url": "/product/" + quote(row["item"]) + "/Johor"}
            )  # Assuming 'item_name' is the column storing item names

    # Get 'show_all' parameters from the query string for both raw and processed items
    raw_food_list_show_all = request.args.get("raw_show_all", "false") == "true"
    processed_food_list_show_all = (
        request.args.get("processed_show_all", "false") == "true"
    )

    # Check if the raw food list should show all items or only the first 9
    if raw_food_list_show_all:
        limited_raw_items = raw_items  # Show all raw items
    else:
        limited_raw_items = raw_items[:9]  # Limit to the first 9 raw items

    # Check if the processed food list should show all items or only the first 9
    if processed_food_list_show_all:
        limited_processed_items = processed_items  # Show all processed items
    else:
        limited_processed_items = processed_items[
            :9
        ]  # Limit to the first 9 processed items

    # Pass the relevant data to the template
    return render_template(
        "item.html",
        raw_items=limited_raw_items,
        processed_items=limited_processed_items,
        raw_show_all=raw_food_list_show_all,
        processed_show_all=processed_food_list_show_all,
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/dataset")
def dataset():
    return render_template("dataset.html")


@app.route("/product/<food_item>/<state>")
def product_details(food_item, state):
    # Decode URL-encoded parameters to ensure they are properly decoded
    food_item = unquote(food_item)
    state = unquote(state)

    # Example data retrieval from database or API
    product_data = get_product_data(food_item, state)
    
    return render_template("product.html", product=product_data)

def get_product_data(food_item, state):
    product_data = None

    # Open the CSV file that contains product data
    with open("dataset/product_details.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item_name_modified = food_item.replace(" ", "%20")
            item_name_modified = item_name_modified.replace(",", "%2C")

            if row["item_group"] == "1":

                if (
                    row["item_name"].lower() == food_item.lower()
                    and row["state"].lower() == state.lower()
                ):
                    # Fetch best model accuracy for future trend and unusual trend charts
                    accuracy_file_path = f'dataset/raw food/anomalies_accuracy/{food_item}_accuracy_summary.csv'
                    prediction_accuracy_path = f'dataset/raw food/prediction_accuracy/{food_item}_accuracy_summary.csv'

                    # Initialize empty accuracy data
                    future_trend_accuracy = None
                    unusual_trend_accuracy = None

                    # Check if the accuracy file exists, if yes, load it
                    if os.path.exists(prediction_accuracy_path):
                        accuracy_df = pd.read_csv(prediction_accuracy_path)
                        future_trend_accuracy = accuracy_df[(accuracy_df['item_name'] == food_item) & (accuracy_df['state'] == state)]
                        if not future_trend_accuracy.empty:
                            future_trend_accuracy = future_trend_accuracy.iloc[0].to_dict()

                    if os.path.exists(accuracy_file_path):
                        prediction_accuracy_df = pd.read_csv(accuracy_file_path)
                        unusual_trend_accuracy = prediction_accuracy_df[(prediction_accuracy_df['item_name'] == food_item) & (prediction_accuracy_df['state'] == state)]
                        if not unusual_trend_accuracy.empty:
                            unusual_trend_accuracy = unusual_trend_accuracy.iloc[0].to_dict()

                    product_data = {
                        "name": row["item_name"].replace("%20", " "),
                        "state": row["state"],
                        "price": row["latest_price"],
                        "price_change": row.get(
                            "price_change", "N/A"
                        ),  # Add price change if available
                        "highest_price": row.get(
                            "highest_price", "N/A"
                        ),  # Add highest price if available
                        "lowest_price": row.get(
                            "lowest_price", "N/A"
                        ),  # Add lowest price if available
                        "unusual_prices": get_raw_unusual_prices(
                            food_item, state
                        ),  # Add logic for unusual prices if available
                        "future_trend_chart": f"https://raw.githubusercontent.com/czwong02/hargabarangnow-model/main/raw%20food/prediction/{item_name_modified}/prediction_{state}.png",
                        "unusual_trend_chart": f"https://raw.githubusercontent.com/czwong02/hargabarangnow-model/main/raw%20food/anomaly/{item_name_modified}/anomalies_{state}.png",
                        "price_comparison_chart": f"https://raw.githubusercontent.com/czwong02/hargabarangnow-model/main/raw%20food/average%20price/{item_name_modified}.png",
                        "future_trend_chart_model": future_trend_accuracy.get('best_model'),
                        "future_trend_chart_rmse": future_trend_accuracy.get('best_model_rmse'),
                        "future_trend_chart_accuracy": future_trend_accuracy.get('best_model_accuracy'),
                        "unusual_trend_chart_model": unusual_trend_accuracy.get('best_model'),
                        "unusual_trend_chart_rmse": unusual_trend_accuracy.get('best_model_rmse'),
                        "unusual_trend_chart_accuracy": unusual_trend_accuracy.get('best_model_accuracy'),
                    }
                    break
            else:

                if (
                    row["item_name"].lower() == food_item.lower()
                    and row["state"].lower() == state.lower()
                ):

                    # Fetch best model accuracy for future trend and unusual trend charts
                    accuracy_file_path = f'dataset/processed food/anomalies_accuracy/{food_item}_accuracy_summary.csv'
                    prediction_accuracy_path = f'dataset/processed food/prediction_accuracy/{food_item}_accuracy_summary.csv'

                    # Initialize empty accuracy data
                    future_trend_accuracy = None
                    unusual_trend_accuracy = None

                    # Check if the accuracy file exists, if yes, load it
                    if os.path.exists(prediction_accuracy_path):
                        accuracy_df = pd.read_csv(prediction_accuracy_path)
                        future_trend_accuracy = accuracy_df[(accuracy_df['item_name'] == food_item) & (accuracy_df['state'] == state)]
                        if not future_trend_accuracy.empty:
                            future_trend_accuracy = future_trend_accuracy.iloc[0].to_dict()

                    if os.path.exists(accuracy_file_path):
                        prediction_accuracy_df = pd.read_csv(accuracy_file_path)
                        unusual_trend_accuracy = prediction_accuracy_df[(prediction_accuracy_df['item_name'] == food_item) & (prediction_accuracy_df['state'] == state)]
                        if not unusual_trend_accuracy.empty:
                            unusual_trend_accuracy = unusual_trend_accuracy.iloc[0].to_dict()

                    product_data = {
                        "name": row["item_name"],
                        "state": row["state"],
                        "price": row["latest_price"],
                        "price_change": row.get(
                            "price_change", "N/A"
                        ),  # Add price change if available
                        "highest_price": row.get(
                            "highest_price", "N/A"
                        ),  # Add highest price if available
                        "lowest_price": row.get(
                            "lowest_price", "N/A"
                        ),  # Add lowest price if available
                        "unusual_prices": get_processed_unusual_prices(
                            food_item, state
                        ),  # Add logic for unusual prices if available
                        "future_trend_chart": f"https://raw.githubusercontent.com/czwong02/hargabarangnow-model/main/processed%20food/prediction/{item_name_modified}/prediction_{state}.png",
                        "unusual_trend_chart": f"https://raw.githubusercontent.com/czwong02/hargabarangnow-model/main/processed%20food/anomaly/{item_name_modified}/anomalies_{state}.png",
                        "price_comparison_chart": f"https://raw.githubusercontent.com/czwong02/hargabarangnow-model/main/processed%20food/average%20price/{item_name_modified}.png",
                        "future_trend_chart_model": future_trend_accuracy.get('best_model'),
                        "future_trend_chart_rmse": future_trend_accuracy.get('best_model_rmse'),
                        "future_trend_chart_accuracy": future_trend_accuracy.get('best_model_accuracy'),
                        "unusual_trend_chart_model": unusual_trend_accuracy.get('best_model'),
                        "unusual_trend_chart_rmse": unusual_trend_accuracy.get('best_model_rmse'),
                        "unusual_trend_chart_accuracy": unusual_trend_accuracy.get('best_model_accuracy'),
                    }
                    break

    # If product_data is None, return a default or error message
    if not product_data:
        product_data = {
            "name": food_item,
            "state": state,
            "price": "Data not found",
            "price_change": "N/A",
            "highest_price": "N/A",
            "lowest_price": "N/A",
            "unusual_prices": [],
            "future_trend_chart": "",
            "unusual_trend_chart": "",
            "price_comparison_chart": "",
            "future_trend_chart_model": "",
            "future_trend_chart_rmse": "",
            "future_trend_chart_accuracy": "",
            "unusual_trend_chart_model": "",
            "unusual_trend_chart_rmse": "",
            "unusual_trend_chart_accuracy": "",
     
        }

    return product_data


def get_raw_unusual_prices(food_item, state):

    try:
        # Custom logic to identify unusual prices using your anomaly detection models
        # This function could load a model and apply it to detect anomalies
        # For now, we'll return an empty list
        # Check if the file exists before attempting to open it

        unusual_prices = []

        with open(
            f"dataset/raw food/anomalies/{food_item}/anomalies_{state}.csv", newline=""
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                unusual_prices.append({"date": row["date"], "price": row["price"]})
    except Exception as e:
        print(f"An error occurred: {e}")  # Catch any other exception

    return unusual_prices


def get_processed_unusual_prices(food_item, state):
    try:
        # Custom logic to identify unusual prices using your anomaly detection models
        # This function could load a model and apply it to detect anomalies
        # For now, we'll return an empty list
        unusual_prices = []

        with open(
            f"dataset/processed food/anomalies/{food_item}/anomalies_{state}.csv",
            newline="",
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                unusual_prices.append({"date": row["date"], "price": row["price"]})
    except Exception as e:
        print(f"An error occurred: {e}")  # Catch any other exception
        
    return unusual_prices


if __name__ == "__main__":
    app.run(debug=True)
