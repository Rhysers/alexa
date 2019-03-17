# alexa
Daily Automation for Samson House Alexa Skill
Depends on Google Drive API for Python.(pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib)
Requires a file on the root containing the path to the working directory.
Downloads the days file from Google Drive, converts it to MP3, renames it and posts it in a directory to be hosted by a webserver
Also creates the xml for Alexa to identify the stream.

Usage:
Setup:
Requires a credentials.json file in the working folder. Run the script the first time with --noauth_local_webserver to authenticate with the appropriate Google Drive to convert the credentials.json to a token.json. The --noauth_local_webserver argument is not required if a valid token.json exists in the working directory. Finally place a text file containing the current 3 digit number of the Samson House .m4a file. The script will search for this file to determine what tomorrow's number is to download it from google drive.
Create a crontab entry to call alexa.py at an appropirate time each day. The script uses the current date when building the xml file for the rss feed, so I recommend after midnight, but it should work either way.
A second crontab entry should be created to run the verifyNext.py at an apporpriate time to send a reminder if the next days file isn't uploaded to Google Drive.
