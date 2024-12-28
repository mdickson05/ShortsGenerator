""" This file is the program to execute reddit short generation """
import os
import json
import csv
from enum import Enum
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from openai import OpenAI

OpenAI.api_key = os.environ["OPENAI_API_KEY"]


class ScriptType(Enum):
    """Class for menu options"""
    ASK_REDDIT = "1"


def parse_all_results():
    """Parse all results from Reddit JSON link"""
    # Load and process URL from CLI
    url = input("PLease enter your url: ").strip()
    # If empty...
    if not url:
        print("Error: URL cannot be empty.")
        return
    try:
        # Open URL
        response = urlopen(url)
    # If error in URL...
    except HTTPError as e:
        print(f"HTTPError: {e.code} - {e.reason}")
        return
    except URLError as e:
        print(f"URLError: {e.reason}")
        return
    try:
        # Load the JSON
        response_json = json.loads(response.read())
    # If error in processing JSON...
    except json.decoder.JSONDecodeError as e:
        print(f"Error parsing JSON. Check URL and try again: {str(e)}")
        return

    # Access the data within each child
    children_json = response_json["data"]["children"]

    # Convert json response to list for CSV writing
    children_list = list()
    for child in children_json:
        # Filter out NSFW content
        if child["data"]["over_18"] is False:
            child_dict = dict()
            child_dict.update({"title": child["data"]["title"].strip()})
            child_dict.update({"url": child["data"]["url"].strip()})
            children_list.append(child_dict)

    # Write to CSV
    with open("parse_output.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["title", "url"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(children_list)
    print("Parsing successful! Filtering titles...")


def chatgpt_title_filtering():
    """Filter titles with ChatGPT API based on engagement"""
    # Read the parsed output, extract title
    with open("parse_output.csv", mode="r", encoding="utf-8") as csvfile:
        parsed_content = csv.DictReader(csvfile)
        titles = list()
        for lines in parsed_content:
            titles.append(lines["title"])

    # Prompt for filtering
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
    # Give ChatGPT the prompt
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user",
             "content": prompt
             }
        ]
    )
    # Process the response
    output = completion.choices[0].message.content
    result_titles = output.split("\n")

    # Ensure that title is actually real and exists in the parsed titles
    with open("parse_output.csv", mode="r", encoding="utf-8") as csvfile:
        title_list = list()
        parsed_content = csv.DictReader(csvfile)
        for lines in parsed_content:
            for result_title in result_titles:
                if lines["title"] == result_title.strip():
                    title_dict = dict()
                    title_dict.update({"title": lines["title"]})
                    title_dict.update({"url": lines["url"]})
                    title_list.append(title_dict)

    # If the title_list has the correct amount of titles...
    if len(title_list) == 7:
        print("Generation successful, printing output...")
        # Write to CSV
        with open("chatgpt_output.csv", "w", newline="", encoding="UTF-8") as csvfile:
            fieldnames = ["title", "url"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(title_list)
    # Else run chatgpt filtering again
    else:
        print("Did not generate seven titles, trying again...")
        chatgpt_title_filtering()


def ask_reddit_script():
    """Generates a script for an AskReddit link"""
    # Clear the existing script
    with open("script.txt", "w", encoding="UTF-8") as script:
        script.write("")
    # Open ChatGPT title output
    with open("chatgpt_output.csv", "r", encoding="UTF-8") as csvfile:
        selected_titles = csv.DictReader(csvfile)
        # Convert processed link to filter for top 20 comments
        for lines in selected_titles:
            title = lines["title"]
            url = lines["url"]
            json_url = url[:-1] + ".json?limit=20"
            print(f"Url: {json_url}")
            response = urlopen(json_url)
            # Load the JSON
            response_json = json.loads(response.read())
            # Access the data within each child
            for listing in response_json:
                children_json = listing["data"]["children"]
                # Convert json response to list
                children_list = list()
                for child in children_json:
                    # Filter out the post itself
                    if child["kind"] != "t3":
                        # Safely get "body" if it exists
                        body = child["data"].get("body")
                        if body:  # Ensure "body" is not None
                            children_list.append(body.strip())
            # Prompt for generating script with AskReddit comments
            prompt = f"""

                You are a renowned social media algorithm expert, recognized for your mastery in creating viral short-form video content. Your task is to evaluate a list of 20 potential responses to a given question and craft a single, engaging 25-40 second script tailored for platforms such as TikTok, Instagram Reels, and YouTube Shorts. Make sure to present the information as a series of different comments, or as a larger, single comment. Do not take any creative liberties; leave the comment/s as is. Remember, each comment comes from a separate individual

                ### Instructions:  
                1. Analyze the 20 responses to find the most impactful response/s based on emotional resonance, relatability, novelty, humor, and shareability.  
                2. Collate the chosen response/s into a 25-40 second plain text script (~100 words), putting each response on a new line. Do not include any discussion, explanation, or additional formatting.
                
                ### Information:
                Here is the question asked:
                {title}

                Here is the list of 20 potential responses:  
                {children_list}
                
                ### Response Format:              
                $final_script
            """

            # Give prompt to ChatGPT
            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user",
                     "content": prompt
                     }
                ]
            )

            # Write ChatGPT response to file
            output = completion.choices[0].message.content
            with open("script.txt", "a", encoding="UTF-8") as script:
                script.write(title + '\n')
                script.write(output + '\n')
                script.write("\n")


# Parse and filter title list
parse_all_results()
chatgpt_title_filtering()

# Print menu for use to select option
MENU = """
Select from the following options: 
1. Generate Ask Reddit Script
"""
print(MENU)
selected_script = input("Enter your response: ").strip()
if selected_script == ScriptType.ASK_REDDIT.value:
    ask_reddit_script()
else:
    print("Invalid option. Closing app...")
