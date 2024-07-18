import json
import logging
import os
import re
import time
from datetime import datetime

import dropbox
import ffmpeg
from vertexai import init as vertexai_init
from vertexai.preview.generative_models import GenerativeModel, Part

import config

logging.getLogger().setLevel(logging.INFO)


def create_notion_page(summary_content):
    """Create a new page in Notion"""
    response = config.NOTION_CLIENT.pages.create(
        parent={"database_id": config.SECRETS["MEDIA_SAVES_DB"]},
        properties={
            "Name": {"title": [{"text": {"content": summary_content["TITLE"]}}]},
            "Key points": {
                "rich_text": [{"text": {"content": summary_content["KEYPOINTS"]}}]
            },
            "Summary": {
                "rich_text": [{"text": {"content": summary_content["SUMMARY"]}}]
            },
            "Tags": {
                "multi_select": [{"name": tag} for tag in summary_content["TAGS"]]
            },
        },
    )
    logging.info(
        "%s Created Notion page: %s",
        datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
        summary_content["TITLE"],
    )

    config.send_notification(
        "Notion video summary: {}".format(summary_content["TITLE"])
    )

    return response["url"]


def compress_video(
    video_full_path, size_upper_bound, two_pass=True, filename_suffix="cps_"
):
    """
    Compress video file to max-supported size.
    :param video_full_path: the video you want to compress.
    :param size_upper_bound: Max video size in KB.
    :param two_pass: Set to True to enable two-pass calculation.
    :param filename_suffix: Add a suffix for new video.
    :return: out_put_name or error
    """
    output_file_name = video_full_path

    # Adjust them to meet your minimum requirements (in bps), or maybe this function will refuse your video!
    total_bitrate_lower_bound = 11000
    min_audio_bitrate = 32000
    max_audio_bitrate = 256000
    min_video_bitrate = 100000
    logging.info(
        "%s Compressing video: %s",
        datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
        video_full_path,
    )

    try:
        # Bitrate reference: https://en.wikipedia.org/wiki/Bit_rate#Encoding_bit_rate
        probe = ffmpeg.probe(video_full_path)
        # Video duration, in s.
        duration = float(probe["format"]["duration"])
        # Audio bitrate, in bps.
        audio_bitrate = float(
            next((s for s in probe["streams"] if s["codec_type"] == "audio"), None)[
                "bit_rate"
            ]
        )
        # Target total bitrate, in bps.
        target_total_bitrate = (size_upper_bound * 1024 * 8) / (1.073741824 * duration)
        if target_total_bitrate < total_bitrate_lower_bound:
            logging.info(
                "%s Bitrate is extremely low! Stop compress!",
                datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
            )
            return False

        # Best min size, in kB.
        best_min_size = (
            (min_audio_bitrate + min_video_bitrate)
            * (1.073741824 * duration)
            / (8 * 1024)
        )
        if size_upper_bound < best_min_size:
            logging.info(
                "%s Quality not good! Recommended minimum size: %s KB.",
                datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
                "{:,}".format(int(best_min_size)),
            )
            # return False

        # target audio bitrate, in bps
        if 10 * audio_bitrate > target_total_bitrate:
            audio_bitrate = target_total_bitrate / 10
            if audio_bitrate < min_audio_bitrate < target_total_bitrate:
                audio_bitrate = min_audio_bitrate
            elif audio_bitrate > max_audio_bitrate:
                audio_bitrate = max_audio_bitrate

        # Target video bitrate, in bps.
        video_bitrate = target_total_bitrate - audio_bitrate
        if video_bitrate < 1000:
            logging.info(
                "%s Bitrate %s is extremely low! Stop compress.",
                datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
                video_bitrate,
            )
            return False

        i = ffmpeg.input(video_full_path)
        if two_pass:
            ffmpeg.output(
                i,
                os.devnull,
                **{"c:v": "libx264", "b:v": video_bitrate, "pass": 1, "f": "mp4"},
            ).overwrite_output().run()
            ffmpeg.output(
                i,
                output_file_name,
                **{
                    "c:v": "libx264",
                    "b:v": video_bitrate,
                    "pass": 2,
                    "c:a": "aac",
                    "b:a": audio_bitrate,
                },
            ).overwrite_output().run()
        else:
            ffmpeg.output(
                i,
                output_file_name,
                **{
                    "c:v": "libx264",
                    "b:v": video_bitrate,
                    "c:a": "aac",
                    "b:a": audio_bitrate,
                },
            ).overwrite_output().run()

        if os.path.getsize(output_file_name) <= size_upper_bound * 1024:
            logging.info(
                "%s Compressed video: %s",
                datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
                output_file_name,
            )
            return output_file_name
        elif os.path.getsize(output_file_name) < os.path.getsize(
            video_full_path
        ):  # Do it again
            logging.info(
                "%s Compressed video: %s",
                datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
                output_file_name,
            )
            return compress_video(output_file_name, size_upper_bound)
        else:
            return False
    except FileNotFoundError:
        logging.info(
            "%s You do not have ffmpeg installed!",
            datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
        )
        logging.info(
            "%s You can install ffmpeg by reading https://github.com/kkroening/ffmpeg-python/issues/251",
            datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
        )
        return False


def upload_to_gcs(local_file):
    """Uploads a file to the Google Cloud Blob bucket."""
    bucket = config.GCS_CLIENT.bucket(config.SECRETS["GCS_BUCKET_NAME"])
    blob = bucket.blob(os.path.basename(local_file))
    blob.upload_from_filename(local_file)

    logging.info(
        datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S")
        + " - Uploaded file: "
        + local_file
    )


def compress_and_upload(filename):
    """Compress and upload video to GCS"""

    original_size_MB = os.path.getsize(filename) / (1024 * 1024)

    if original_size_MB <= config.GCS_MAX_FILE_SIZE:
        logging.info(
            "%s File size is already under 9MB, no need to compress.",
            datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
        )
    else:
        compress_video(filename, config.GCS_MAX_FILE_SIZE)

    upload_to_gcs(local_file=filename)
    # Return data for use in future steps
    return filename


def get_video_summary(video_file_name):
    """Generate video summary"""
    vertexai_init(
        credentials=config.GCS_CREDENTIALS,
        project=config.SECRETS["GOOGLE_PROJECT_ID"],
        location=config.SECRETS["GOOGLE_LOCATION"],
    )
    logging.info(
        "%s Generating video summary...",
        datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
    )
    gemini_pro_vision_model = GenerativeModel("gemini-pro-vision")
    response = gemini_pro_vision_model.generate_content(
        [
            config.VIDEO_SUMMARY_PROMPT,
            Part.from_uri(
                config.GCS_VIDEO_FOLDER + video_file_name, mime_type="video/mp4"
            ),
        ],
        stream=True,
    )
    final = ""
    for chunk in response:
        final += chunk.text
    logging.info(
        "%s Video summary generated: %s...",
        datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S"),
        final[: min(len(final), 100)],
    )
    return final


def parse_html_tags(input_string):
    """Extract content from HTML tags"""
    # Define a dictionary to hold the parsed content
    parsed_content = {"TITLE": "", "KEYPOINTS": "", "SUMMARY": "", "TAGS": []}

    # Define regular expression patterns for each tag
    title_pattern = r"<TITLE>(.*?)</TITLE>"
    keypoints_pattern = r"<KEYPOINTS>(.*?)</KEYPOINTS>"
    summary_pattern = r"<SUMMARY>(.*?)</SUMMARY>"
    tags_pattern = r"<TAGS>(.*?)</TAGS>"

    # Extract content for each tag
    title_match = re.search(title_pattern, input_string, re.DOTALL)
    if title_match:
        parsed_content["TITLE"] = title_match.group(1).strip()

    keypoints_match = re.search(keypoints_pattern, input_string, re.DOTALL)
    if keypoints_match:
        parsed_content["KEYPOINTS"] = keypoints_match.group(1).strip()

    summary_match = re.search(summary_pattern, input_string, re.DOTALL)
    if summary_match:
        parsed_content["SUMMARY"] = summary_match.group(1).strip()

    tags_match = re.search(tags_pattern, input_string, re.DOTALL)
    if tags_match:
        # Split the keypoints into a list
        tags = tags_match.group(1).strip().split(",")
        tags = [x.strip() for x in tags]
        # Clean up each keypoint
        parsed_content["TAGS"] = tags

    return parsed_content


def download_or_delete_from_dropbox(download=True, delete=False):
    """Download or delete files from dropbox"""
    tmp_filename = "/tmp/video.mp4"
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=config.SECRETS["DROPBOX_REFRESH_TOKEN"],
        app_key=config.SECRETS["DROPBOX_CLIENT_ID"],
        app_secret=config.SECRETS["DROPBOX_CLIENT_SECRET"],
    )
    result = dbx.files_list_folder("", recursive=True)
    for entry in result.entries:
        file_nm = entry.path_display
        tmp_filename, file_extension = os.path.splitext(entry.path_display)
        tmp_filename = "/tmp/video" + file_extension
        if any(
            x in file_nm.lower()
            for x in [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".m4a", ".mp3"]
        ):
            if download:
                with open(tmp_filename, "wb") as f:
                    metadata, res = dbx.files_download(path=file_nm)
                    f.write(res.content)
            if delete:
                dbx.files_delete(file_nm)
    return tmp_filename


def lambda_handler(event, context):
    """Lambda function handler"""
    api_key = event.get("headers", {}).get("api-key")

    # Check if the API key is present
    if api_key is None:
        return {"statusCode": 400, "body": "Missing API key"}
    elif api_key == config.SECRETS["API_KEY"]:
        notion_response = {}
        filename = download_or_delete_from_dropbox(download=True, delete=False)
        compress_and_upload(filename)
        summary = get_video_summary(filename)
        summary_content = parse_html_tags(summary)
        notion_response = create_notion_page(summary_content)
        download_or_delete_from_dropbox(download=False, delete=True)

        return {
            "statusCode": 200,
            "body": json.dumps(notion_response),
        }
    else:
        return {"statusCode": 401, "body": "Invalid API key"}
