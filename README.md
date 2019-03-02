# alexa
Daily Automation for Samson House Alexa Skill
Depends on Google Drive API for Python.(pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib)
Requires a file on the root containing the path to the working directory.
Downloads the days file from Google Drive, converts it to MP3, renames it and posts it in a directory to be hosted by a webserver
Also creates the xml for Alexa to identify the stream.
