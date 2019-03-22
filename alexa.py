#!/usr/bin/env python3
import os, re, sys, datetime, io, subprocess, requests, glob, time, smtplib, socket
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaIoBaseDownload
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

debugging=False

#Variables for socket to statusboardd
HOST = '127.0.0.5'
PORT = 65432
#Functions for statusboardd
def sendStatus(status):
    theStatus = status.encode()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socks:
        socks.connect((HOST, PORT))
        socks.sendall(theStatus)
        if debugging:
            print('Sent '+status)

#values for any error handling:
headers = {'Content-type': 'application/json',}
alexaWarningSent=False

#Define Email Function:
def sendMail(subject, body):
    try:
        server=smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
    except:
        print('Failed to instantiate the mail server.')
    sent_from = 'piratemonkscal@gmail.com'
    addresses = ['rhys.j.ferris@gmail.com', 'tmoucka@gmail.com']
    for address in addresses:
        try:
            msg = MIMEMultipart()
            msg['From'] = "Alexa Automator"
            msg['To'] = address
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            text = msg.as_string()
        except:
            print('Issues building the message.')
        try:
            gmail_user = 'piratemonkscal@gmail.com'
            gmail_password = 'SamsonSociety2019'
            server.login(gmail_user, gmail_password)
            server.sendmail(sent_from, address, text)
        except:
            print('Failed to send the message.')
    server.close()

# Set Base Directory for easy changing for migration to rPi
# Get the Base Directory from file
try:
    f=open("/alexaBaseDirectory.txt", "r")
    if f.mode == 'r':
        baseDirectory=f.read().strip()
        f.close()
        if debugging:
            print("Base Directory is "+baseDirectory)
except:
    f.close()
    data = '{"text":"<!channel> Alexa Automation failed to get the working directory"}'
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    sendMail('Alexa Automation Failed', 'Alexa Automation failed to get the current working directory')
    sendStatus("alexaBad()")
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
    sendMail('Alexa Automation Failed', 'Alexa Automation failed to get the current number from file')
    sendStatus("alexaBad()")
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
    sendMail('Alexa Automation Failed', 'Alexa Automation failed to authenticate to Google Drive. Rerun script with --noauth_local_webserver to re-establish authentication. Rhys probably needs to fix this one, best to make sure he got htis message.')
    sendStatus("alexaBad()")
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
                fileNameHold = fileName
                file_ID = file.get('id')
                if debugging:
                    print(fileName+" matched "+str(nextNumber))
                    print(file_ID)
                #break
            if fileName.startswith( str(nextNumber+1)):
                readAhead = True
        page_token = results.get('nextPageToken', None)
        if page_token is None:
            break
    #reset filename to correct one held from loop
    fileName = fileNameHold

except:
    data = '{"text":"<!channel> Alexa Automation failed to locate file number %i in Google Drive."}' % (nextNumber)
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    sendMail('Alexa Automation Failed', 'Alexa Automation has FAILED becuase it could not locate the next file (%i) in Google Drive. This can be remeidated in 2 steps: (1) upload the missing file to https://drive.google.com/drive/folders/1-oQx6HcsMmvEGdmnNW304JIQY9wxL1UF?usp=sharing and then (2) visit https://samson.odinforce.net/alexa.html and click the button to trigger the scritp to run.' % (nextNumber))
    sendStatus("alexaBad()")
    quit()

if not(readAhead):
    data = '{"text":"Warning: Alexa Automation sucessfully found tomorrows file, but noticed that the next one after that (%i) is missing."}' % (nextNumber+1)
#    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    sendMail('Alexa Automation Warning', 'Warning: Alexa Automation sucessfully found tomorrows file, but noticed that the next one after that (%i) is missing. Please ensure the file has been uploaded to Google Drive to avoid failure tomorrow: https://drive.google.com/drive/folders/1-oQx6HcsMmvEGdmnNW304JIQY9wxL1UF?usp=sharing' % (nextNumber+1))
    sendStatus("alexaWarning()")
    alexaWarningSent=True
    try: # Write value to file for readahead script
        f= open(baseDirectory+"readAhead.txt", "w+")
        f.write("True")
        f.close()
    except:
        f.close()
else:   # No need to run readahead script
    try:
        f= open(baseDirectory+"readAhead.txt", "w+")
        f.write("False")
        f.close()
    except:
        f.close()

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
    sendMail('Alexa Automation Failed', 'Alexa Automation failed to download file number %i from Google Drive' % (nextNumber))
    sendStatus("alexaBad()")
    quit()

# Increase the Volume
try:
    newFileName = fileName.replace(" ", "_")
#    newFileName = newFileName.replace(".m4a", ".mp3")
    if debugging:
        print("Filename after conversion: "+newFileName)
    subprocess.run(['ffmpeg', '-i', fileName, "-filter:a", "volume=10dB", newFileName])
except:
    data = '{"text":"<!channel> Alexa Automation failed to transcode file number %i"}' % (nextNumber)
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    sendMail('Alexa Automation Failed', 'Alexa Automation failed to transcode file number %i' % (nextNumber))
    sendStatus("alexaBad()")
    quit()

# Remove the old version
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
    sendMail('Alexa Automation Warning', 'Alexa Automation experienced a non-fatal error while cleaning up files. Eventually the device will run out of space if not resolved.')
    sendStatus("alexaWarning()")
    alexaWarningSent=True

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
    sendMail('Alexa Automation Failed', 'Alexa Automation failed while getting info about the file in order to build the XML')
    sendStatus("alexaBad()")
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
            lines[i] = "    <enclosure url=\"https://samson.odinforce.net/"+newFileName+"\" length=\""+str(fileSize)+"\" type=\"audio/mpeg\" />\n"
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
    sendMail('Alexa Automation Failed', 'Alexa Automation failed while reading from the RSS XML')
    sendStatus("alexaBad()")
    quit()

# Write the new current number to file
try:
    f= open(baseDirectory+"curNum.txt", "w+")
    f.write(str(nextNumber))
    f.close()
    if not(alexaWarningSent):
        sendStatus("alexaGood()")
except:
    f.close()
    data = '{"text":"<!channel> Alexa Automation failed while writing the updated XML to file."}'
    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    sendMail('Alexa Automation Failed', 'Alexa Automation failed while writing the update XML to file')
    sendStatus("alexaBad()")
    quit()
