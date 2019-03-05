#!/usr/bin/env python3
import os, re, sys, datetime, io, subprocess, requests, glob, time
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaIoBaseDownload

debugging=False

#values for any error handling:
headers = {'Content-type': 'application/json',}

# Set Base Directory for easy changing for migration to rPi
# Get the Base Directory from file
try:
    f=open("/alexaBaseDirectory.txt", "r")
    if f.mode == 'r':
        baseDirectory=f.read().strip()
#        baseDirectory=baseDirectory.strip()
        f.close()
        if debugging:
            print("Base Directory is "+baseDirectory)
except:
    f.close()
    data = '{"text":"<!channel> Alexa Automation failed to get the working directory"}'
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    quit()

# Change directory here
os.chdir(baseDirectory)

# Get Current Number
try:
    f=open(baseDirectory+"curNum.txt", "r")
    if f.mode == 'r':
        currentNumber = f.read()
        currentNumber = int(currentNumber)
        nextNumber = currentNumber + 1
        f.close()
except:
    f.close()
    data = '{"text":"<!channel> Alexa Automation failed to open file to get current number"}'
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    quit()
if debugging:
    print("Current Number="+str(currentNumber))
    print("Next Number="+str(nextNumber))

# Download the file from Google Drive
# Setup Google Drive API
try:
    SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('drive', 'v3', http=creds.authorize(Http()))
except:
    data = '{"text":"<!channel> Alexa Automation failed to authenticate to Google Drive. Rerun script with --noauth_local_webserver to re-establish authentication."}'
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    quit()

# Call the API
# Get All the files
try:
    page_token= None
    readAhead = False
    while True:
        results = service.files().list(
            q="name contains '.m4a'", spaces='drive',
            fields='nextPageToken, files(id, name)',
            pageToken=page_token).execute()
        for file in results.get('files', []):
            fileName=file.get('name')
            if debugging:
                print("List of files returned by Google:")
                print(fileName)
            if fileName.startswith( str(nextNumber)):
                file_ID = file.get('id')
                #break
            if fileName.startswith( str(nextNumber+1)):
                readAhead = True
        page_token = results.get('nextPageToken', None)
        if page_token is None:
            break
except:
    data = '{"text":"<!channel> Alexa Automation failed to locate file number %i in Google Drive."}' % (nextNumber)
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    quit()

if not(readAhead):
    data = '{"text":"Warning: Alexa Automation sucessfully found tomorrows file, but noticed that the next one after (%i) that is missing."}' % (nextNumber+1)
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)

# Download the file
try:
    if debugging:
        print ("File ID: "+file_ID)
    request = service.files().get_media(fileId=file_ID)
    fh = io.FileIO(fileName, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        if debugging:
            print( "Download %d%%." % int(status.progress() * 100))
except:
    data = '{"text":"<!channel> Alexa Automation failed to download file number %i from Google Drive."}' % (nextNumber)
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    quit()

# Convert the File from m4a to mp3
try:
    newFileName = fileName.replace(" ", "_")
#    newFileName = newFileName.replace(".m4a", ".mp3")
    if debugging:
        print("Filename after conversion: "+newFileName)
    subprocess.run(['ffmpeg', '-i', fileName, "-filter:a", "volume=10dB", newFileName])
except:
    data = '{"text":"<!channel> Alexa Automation failed to transcode file number %i to MP3."}' % (nextNumber)
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    quit()

# Remove the .m4a version
time.sleep(3) #ensure ffmpeg is done with the file
try:
    if debugging:
        print("Removing "+baseDirectory+fileName)
    os.remove(baseDirectory+fileName)
    # Remove old files currentNumber (STR)
    for filename in glob.glob(baseDirectory+str(currentNumber)+"*"):
        if debugging:
            print("Removing "+filename)
        os.remove(filename)
except:
    data = '{"text":"Alexa Automation experienced a non-fatal error while cleaning up files. Eventually the device will run out of space if not resolved."}'
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)

# Get info about the file
try:
    # Get File Name
    fullPath=baseDirectory+newFileName
    # Get the size of the file
    fileSize=os.path.getsize(fullPath)
    fileTitle=re.search("(?<=\ \-\ )(.*?)(?=\ \-\ )",fileName)
    if debugging:
        print(newFileName, fileSize)
except:
    data = '{"text":"<!channel> Alexa Automation failed while getting info about the file to put in the XML."}'
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    quit()

# Update the RSS XML
try:
    f= open(baseDirectory+"rssfeed.xml", 'r')
    lines = f.readlines()
    f.close()
    date=datetime.datetime.today()
    if fileTitle:
        tempMatch = fileTitle.group(1)
        fileTitle = str(tempMatch)
    else:
        fileTitle = "Samson House Devotional"
    for i in range(len(lines)):
        if lines[i].startswith('    <enclosure url'):
            lines[i] = "    <enclosure url=\"https://odinforce.net/"+newFileName+"\" length=\""+str(fileSize)+"\" type=\"audio/mpeg\" />\n"
        elif lines[i].startswith('    <title>'):
            lines[i] = "    <title>"+fileTitle+"</title>\n"
        elif lines[i].startswith('    <itunes:title>'):
            lines[i] = "    <itunes:title>"+date.strftime('%m-%d-%Y')+"</itunes:title>\n"
        elif lines[i].startswith('    <pubDate>'):
            lines[i] = "    <pubDate>"+date.strftime('%a, %d %b %Y 00:00:00 -0500')+"</pubDate>\n"
    f= open(baseDirectory+"rssfeed.xml", 'w')
    f.writelines(lines)
    f.close()
except:
    f.close()
    data = '{"text":"<!channel> Alexa Automation failed while reading from the RSS XML."}'
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    quit()

# Write the new current number to file
try:
    f= open(baseDirectory+"curNum.txt", "w+")
    f.write(str(nextNumber))
    f.close()
except:
    f.close()
    data = '{"text":"<!channel> Alexa Automation failed while writing the updated XML to file."}'
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    quit()
