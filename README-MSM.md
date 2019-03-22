# Alexa
## Overview
The Alexa skill for reading the Samson House daily devotion is hosted on
a Raspbery Pi server which is physically located at Mike Moore's house
in Florida.  (See documentation for Samson House Raspberry Pi for
additional details.)

## Workflow Concept
### Step 1
Tom Mouka records the audio file for the daily devotion and saves it with a numeric sequence file name.
### Step 2
Tom Mouka uploads the recorded audio file into the Samson House Google Drive account (piratemonkscal@gmail.com - see password spreadsheet for credentials) into the _______ folder
### Step 3
An automated script runs every morning at 01:00a ET which processes the next numerically sequenced audio file and moves it into a publication folder where Alexa can retrieve it via API.
### Step 4
Alexa pulls the audio file via API on-demand as needed to play the skill

## Requirements
Daily Automation for Samson House Alexa Skill Depends on Google Drive API for Python.
(pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib) 
Requires a file on the root containing the path to the working directory. 
Requires a credentials.json file in the working folder. 
 
### Script Process
Downloads the days file from Google Drive (folder??) 
Converts it to MP3 format
Renames it to __________
Posts it in a directory (which directory??) to be hosted by a webserver 
Also creates the xml for Alexa to identify the stream. 

## Setup
1. Run the script the first time with --noauth_local_webserver to authenticate with the
appropriate Google Drive to convert the credentials.json to a
token.json. The --noauth_local_webserver argument is not required if a
valid token.json exists in the working directory. 
2. Finally place a text file containing the current 3 digit number of the Samson House .m4a
file. The script will search for this file to determine what tomorrow's
number is to download it from google drive. 
3. Create a crontab entry to call alexa.py at an appropirate time each day. The script uses the
current date when building the xml file for the rss feed, so I recommend
after midnight, but it should work either way. 
4. A second crontab entry should be created to run the verifyNext.py at an apporpriate time to
send a reminder if the next days file isn't uploaded to Google Drive.

## Troubleshooting & FAQ
- If  the Alexa script does not find the file needed for the day after tomorrow, then an Alert message is posted into the automation channel in the Samson House slack workspace.
- If the Alexa script does not find the file needed for tomorrow, then a Warning message is posted into the automation channel in the Samson House slack workspace and a notification e-mail is sent to Trey Shaver and Tom Mouka
  - Contained in that warning e-mail is a link to the Google folder to upload the next audio file
- If the next audio file is uploaded after 1a ET on the day of publication, then Alex will continue to play the previous day's audio file until the new file is processed and moved into the publication folder.  An on-demand link is available to trigger the Alexa processing script after the file is uploaded.
