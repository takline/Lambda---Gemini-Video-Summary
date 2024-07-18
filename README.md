<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="lambdagemini.png"/>
    <source media="(prefers-color-scheme: light)" srcset="lambdagemini.png"/>
    <img width="400" src="images/lambdagemini.png"/>
 <br />
</h1>


# Lambda & Google Gemini Integration

## Overview
This AWS Lambda function is designed to automatically trigger upon the upload of new files to Dropbox or S3. Upon activation, it processes the uploaded video file and generates a comprehensive summary. This summary includes key points, a deeper analysis, and categorization tags.

This was a fun excuse to try out Google's new multimodal AI model - Gemini. This integration allows the function to not just process video uploads, but to deeply understand and interpret the content.

## Workflow Summary

The AWS Lambda function orchestrates a sophisticated workflow to automate the process of video summarization. Here's a step-by-step overview:

1. **Trigger Event**: The workflow begins when a new video file is uploaded to either Dropbox or an Amazon S3 bucket. This event automatically triggers the AWS Lambda function.

2. **File Processing and Validation**: Upon activation, the function first validates the video file format and size. It ensures compatibility and prepares the file for further processing.

3. **Video Compression**: To optimize for processing speed and efficiency, the video file is compressed. This step adjusts the video to a suitable size and format without significant loss of quality, ensuring it meets the requirements of Google Cloud Storage.

4. **Upload to Google Cloud Storage**: The compressed video file is then securely uploaded to Google Cloud Storage. This step is crucial as it provides a stable and accessible location for the video, ready for analysis by the AI model.

5. **AI Analysis with Gemini Multimodal Model**: With the video in place, Google's Gemini multimodal AI model takes over. This advanced AI system analyzes the video, interpreting both visual and auditory elements. It leverages deep learning to understand context, themes, and key messages within the video.

6. **Generating the Summary**: The AI model processes the content and generates a comprehensive summary. This summary includes the most critical points, insights, and a coherent narrative that encapsulates the essence of the video.

7. **Storing Summary in Notion**: Once the summary is created, it is automatically formatted and stored in a Notion database. This integration provides an organized and easily accessible way to retrieve and review the summaries.

8. **Notification and Logging**: After the summary is successfully stored, the function sends a notification to the user (or a designated recipient) to inform them of the completion of the process. Simultaneously, detailed logs of the operation are maintained for monitoring and troubleshooting purposes.

9. **Cleanup and Maintenance**: The function also includes a cleanup routine to remove temporary files or data used during the process, ensuring efficient use of storage and resources.

10. **Security and Compliance**: Throughout the workflow, security and compliance are prioritized. Sensitive information like API keys and credentials are securely managed using AWS Secrets Manager, ensuring that the entire process is not only efficient but also secure.


## Prerequisites
- AWS account with Lambda and S3 access
- Dropbox account (if using Dropbox triggers)
- Google Cloud Storage account (for video processing and storage)
- Notion account (for storing and managing summaries)

## Configuration
Before deployment, ensure all necessary libraries and dependencies are installed, and configure the following:
- `config.py`: Contains all the configuration settings for AWS, Dropbox, Google Cloud Storage, and Notion.
- `google_auth.json`: A JSON file with your Google Cloud service account credentials.
- `SECRETS`: A dictionary obtained from AWS Secrets Manager, storing sensitive information like API keys and tokens.

## Deployment
1. Clone the repository from `git@github.com:takline/automation.git`.
2. Set up your AWS Lambda environment with the necessary permissions and environment variables.
3. Upload the code to your AWS Lambda function.

## Functionality
The Lambda function comprises several key components:
- Dropbox and S3 triggers: Initiate the function upon file upload.
- Video processing: Compresses and uploads the video to Google Cloud Storage.
- Video summary generation: Utilizes Vertex AI to generate a video summary.
- Notion integration: Creates a new page in Notion with the video summary.

## Usage
1. Upload a video file to your configured Dropbox folder or S3 bucket.
2. The Lambda function triggers automatically, processes the video, and generates a summary.
3. Check the corresponding Notion database for the new summary page.

## Logging
- Logging is handled by `lambda_logs.py`, which records function activity and errors.
- Logs are stored in S3 and can be monitored for troubleshooting and analysis.

## Security
- Use AWS Secrets Manager to securely store and access sensitive information.
- Ensure your AWS Lambda function has the minimum required permissions.

## Limitations
- Video file size is limited by Google Cloud Storage's maximum file size.