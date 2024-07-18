#!/bin/bash

# Configure defaults
PREFIX=$1
SAMPLE=$2
FORMAT=$3

# Download object
aws s3 cp s3://$BUCKET_NAME/$PREFIX-original/$SAMPLE/$SAMPLE.$FORMAT .

# Test FFprobe
ffprobe $SAMPLE.$FORMAT -v quiet -show_format -show_streams -of json

# Test FFmpeg
ffmpeg -loglevel warning -y -i $SAMPLE.$FORMAT -vn -codec:a libmp3lame -b:a 128k $SAMPLE.mp3
ffprobe $SAMPLE.mp3 -v quiet -show_format -show_streams -of json

ffmpeg -loglevel warning -y -i $SAMPLE.$FORMAT -vn -strict -2 -codec:a libfdk_aac -b:a 96k $SAMPLE.m4a
ffprobe $SAMPLE.m4a -v quiet -show_format -show_streams -of json

ffmpeg -loglevel warning -y -i $SAMPLE.$FORMAT -vn -codec:a libvorbis $SAMPLE.ogg
ffprobe $SAMPLE.ogg -v quiet -show_format -show_streams -of json

ls -la

# Remove any generated audio file
rm $SAMPLE*
