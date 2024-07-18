import http.client
import json
import os
import urllib

import boto3
from google.cloud import storage
from google.oauth2 import service_account
from notion_client import Client

PROMPTS = """You have been tasked with improving a prompt (to be used with ChatGPT). I will provide you with a draft version of a prompt below, and your job is to produce a json formatted output of the following (I've included the example json format):
{
    "PROMPT_PURPOSE": "What is the purpose of the prompt and what is the author trying to accomplish? For example, you could conclude the purpose is to 'refactor python code to follow best practices for python development'.",
    "PROMPT_AGENT":"Based on the purpose of the prompt, describe the ideal agent to perform the task. If the purpose is to refactor python code, the ideal agent could be described/written as: 'Let's pretend that you are a senior python engineer at Google who excels at refactoring python code.'",
    "REWRITTEN_PROMPT": "This is your final rewritten prompt. It should be clear, concise, and easily understood by you. The final prompt should be a well written combination of the purpose and agent sections.",
}

With that in mind, please provide me with your json formatted response. Do not respond with any further questions or clarifications, as you are free to make your own assumptions. Here is the original prompt draft:

PROMPT_DRAFT_HERE"""
PROMPT_SYSTEM = """You are a Large-language model Prompt engineer. Your goal is to help me craft the best possible prompt for my needs, which will be used by you, ChatGPT"""

JUNE = """As the CEO of June, you regularly write down notes for ideas regarding your startup's app. I will provide you with a draft version of one of your notes below, and your job is to produce a json formatted output of the following (I've included the example json format):
{
    "NOTE_PURPOSE": "What is the purpose of the note and what were you trying to accomplish?",
    "NEXT_STEPS": "In regards to your startup's app, what next steps would you take to to move forward with the central idea/theme of your note?",
    "IMPROVED_NOTE": "This is your final rewritten note. It should be clear, concise, and easily understood by you. The final note should be an enhanced combination of the other sections of your response, and can include any ideas or info you think are missing that could help your startup become a unicorn startup.",
    "PROMPT":"Based on the other sections of your response, you should create a prompt (to be used with ChatGPT)  to solicit a response from ChatGPT to help accomplish the note's next steps. For this entry, pretend that you are a Prompt engineer and your goal is to help craft the best possible prompt."
}
With that in mind, please provide me with your json formatted response. Do not respond with any further questions or clarifications, as you are free to make your own assumptions. Here is the original prompt draft:

JUNE_DRAFT_HERE"""
JUNE_SYSTEM = """You are the CEO of a tech startup named June. June is an innovative iOS app and web app that revolutionizes the use of Large Language Models (LLMs) by seamlessly integrating them into everyday note-taking. Unlike traditional tools that require complex prompt engineering, June offers a user-friendly "push" approach. As you jot down notes, the app intuitively suggests actions and recommendations, optimizing itself for specific, niche use cases based on your interactions. This unique approach not only simplifies the AI experience for the average user but also continually enhances its efficiency through user feedback."""

VIDEO_SUMMARY_PROMPT = """Imagine yourself as a visionary leader in the field of technology and innovation, akin to well-known figures like Sam Altman. Your expertise is in identifying and interpreting emerging trends in technology, startups, and global developments. You have recently viewed a short video that you find particularly insightful in terms of its implications for the future. Your task is to create a comprehensive summary of this video that includes:
- a creative title that captures the essence of the video
- 3-5 bullet points highlighting the key takeaways
- a 3-5 sentence summary offering a deeper analysis of how these points relate to broader trends and their potential impact on startups and the world at large. 
- 0-3 one-word tags that you choose to label the video as (so that you can categorize and analyze at a later time)

Please format your response using HTML tags as follows:

<TITLE> [Your creative title here] </TITLE>
<KEYPOINTS>
- [Key point 1]
- [Key point 2]
- [Key point 3]
</KEYPOINTS>
<SUMMARY> [Your analytical summary here, encompassing the key insights and their wider implications] </SUMMARY>
<TAGS> [comma seperated 1-word tags that you choose to label the video as] </TAGS>"""


def get_secrets():
    secret_name = "notionGPT"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session(os.environ["AWSKEY"], os.environ["AWSSECRET"])
    client = session.client(service_name="secretsmanager", region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    secret = get_secret_value_response["SecretString"]

    return json.loads(secret)


def send_notification(message):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request(
        "POST",
        "/1/messages.json",
        urllib.parse.urlencode(
            {
                "token": SECRETS["PUSHOVER_APP"],
                "user": SECRETS["PUSHOVER_USER"],
                "message": message,
            }
        ),
        {"Content-type": "application/x-www-form-urlencoded"},
    )
    conn.getresponse()
    return 200


SECRETS = get_secrets()
GITHUB_REPO_URL = "git@github.com:takline/automation.git"
S3_CLIENT = boto3.client(
    "s3",
    aws_access_key_id=SECRETS["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=SECRETS["AWS_SECRET"],
)
S3_RESOURCE = boto3.resource(
    "s3",
    "us-east-1",
    aws_access_key_id=SECRETS["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=SECRETS["AWS_SECRET"],
)
NOTION_CLIENT = Client(auth=SECRETS["NOTION"])
GCS_CREDENTIALS = service_account.Credentials.from_service_account_file(
    "google_auth.json"
)
GCS_CLIENT = storage.Client(credentials=GCS_CREDENTIALS)
GCS_MAX_FILE_SIZE = 9.5
GCS_VIDEO_FOLDER = "gs://notion3000/"
GCS_VIDEO_DEST = "gs://notion3000/video.mp4"
S3_NOTIONGPT_LOG_FILE = "notionGPT.log"
S3_TIKTOK_LOG_FILE = "tikTok.log"
S3_FFMPEG = "ffmpeg-git-amd64-static.tar.xz"
S3_LOG_PATH = "s3://%s/uploadMedia.log" % SECRETS["S3_BUCKET_NAME"]
