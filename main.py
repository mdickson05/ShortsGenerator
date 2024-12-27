import os
from openai import OpenAI
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
            child_dict.update({"title" : child["data"]["title"].strip()})
            child_dict.update({"url" : child["data"]["url"].strip()})
            children_list.append(child_dict)

    # Write to CSV
    with open("output.csv", "w", newline="") as csvfile:
        fieldnames = ["title", "url"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(children_list)

def chatgpt_analysis():
    with open("output.csv", mode="r") as csvfile:
        input = csv.DictReader(csvfile)
        titles = list()
        for lines in input:
            titles.append(lines["title"])

    OpenAI.api_key = os.environ["OPENAI_API_KEY"]

    prompt = f"""
        You are a renowned social media algorithm expert with a deep understanding of how content performs on various platforms, including Reddit, TikTok, Instagram, and YouTube. Your task is to evaluate a list of Reddit post titles and identify the top 7 topics most likely to generate high engagement on social media platforms, while considering their potential for monetization.

        Please rank the titles based on the following criteria:
        1. Likelihood of high engagement (e.g., upvotes, comments, and shares) on social media platforms.
        2. Suitability for monetization on platforms like YouTube, TikTok, or Instagram.
        3. General virality potential across social platforms.

        Here is the format you will use to provide your ranked analysis:

        $title_1
        $title_2
        $title_3
        $title_4
        $title_5
        $title_6
        $title_7

        You must only include the titles in your response. Do not include any discussion, explanation, or additional formatting.

        Please analyze the following list:
        {titles}
    """

    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", 
            "content": prompt
            }
        ]
    )

    output = completion.choices[0].message.content
    result_titles = output.split("\n")

    with open("output.csv", mode="r") as csvfile:
        title_list = list()
        input = csv.DictReader(csvfile)
        for lines in input:
            for result_title in result_titles:
                if lines["title"] == result_title.strip():
                    title_dict = dict()
                    title_dict.update({"title" : lines["title"]})
                    title_dict.update({"url" : lines["url"]})
                    title_list.append(title_dict)

    if(len(title_list) == 7): 
        print("Generation successful, printing output...")
    # Write to CSV
    with open("chatgpt_output.csv", "w", newline="") as csvfile:
        fieldnames = ["title", "url"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(title_list)


parse_all_results()
chatgpt_analysis()





