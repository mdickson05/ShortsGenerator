from urllib.request import urlopen 
from urllib.error import URLError, HTTPError
import json
import csv

def parse_all_results():
    # Load and process URL from CLI
    url = input("PLease enter your url: ").strip()
    
    # If empty...
    if not url:
        print("Error: URL cannot be empty.")
        return
    
    # If error in URL...
    try:
        response = urlopen(url)
    except HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}")
        return
    except URLError as e:
        print(f"URLError: {e.reason}")
        return
    except Exception as e:
        print(f"Unexpected error while accessing URL: {str(e)}")
        return
    
    # Load the JSON
    response_json = json.loads(response.read())

    # Access the data within each child
    children_json = response_json["data"]["children"]

    # Convert json response to list for CSV writing
    children_list = list()
    for child in children_json:
        # Filter out NSFW content
        if(child["data"]["over_18"] == False):
            child_dict = dict()
            child_dict.update({"title" : child["data"]["title"]})
            child_dict.update({"url" : child["data"]["url"]})
            children_list.append(child_dict)

    # Write to CSV
    with open("output.csv", "w", newline="") as csvfile:
        fieldnames = ["title", "url"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(children_list)

parse_all_results()





