#!/usr/bin/env python3
import requests, smtplib, os
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

debugging = False

#Define Email Function:
def sendMail(subject, body):
    try:
        server=smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
    except:
        print('Failed to instantiate the mail server.')
    sent_from = 'piratemonkscal@gmail.com'
    addresses = ['rhys.j.ferris@gmail.com']
    for address in addresses:
        try:
            if debugging:
                print(subject)
                print(body)
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
    
#values for any error handling:
headers = {'Content-type': 'application/json',}

#Get Base Directory
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
#    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    sendMail('Alexa Automation Failed', 'Alexa Automation failed to get the current working directory')
    quit()

os.chdir(baseDirectory)

#See if we need to run:
try:
    f=open(baseDirectory+"readAhead.txt", "r")
    if f.mode == 'r':
        readAhead = f.read().strip()
        if debugging:
            print(readAhead)
except:
    data = '{"text":"<!channel> Alexa Automation open the readAhead value from file."}'
#    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    sendMail('Alexa Automation Failed', 'Alexa Automation open the readAhead value from file.')
finally:
    f.close()
if readAhead == 'False':
    quit()

#Begin stuff
#Get Current Number
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
#    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    sendMail('Alexa Automation Failed', 'Alexa Automation failed to get the current number from file')
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
#    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    sendMail('Alexa Automation Failed', 'Alexa Automation failed to authenticate to Google Drive. Rerun script with --noauth_local_webserver to re-establish authentication. Rhys probably needs to fix this one, best to make sure he got htis message.')
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
            if fileName.startswith( str(nextNumber+1)):
                readAhead = True
        page_token = results.get('nextPageToken', None)
        if page_token is None:
            break
    #reset filename to correct one held from loop
    fileName = fileNameHold
except:
    data = '{"text":"<!channel> Alexa Automation Read Ahead still failed to locate file number %i in Google Drive. Please remediate as soon as possible otherwise automation will fail tonight."}' % (nextNumber)
#    response = requests.post('https://hooks.slack.com/services/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', headers=headers, data=data)
    sendMail('Alexa Automation Read Ahead Warning', 'Alexa Automation Read Ahead still failed to locate file number %i in Google Drive. Please remediate as soon as possible otherwise automation will fail tonight: https://drive.google.com/drive/folders/1-oQx6HcsMmvEGdmnNW304JIQY9wxL1UF?usp=sharing' % (nextNumber))
    quit()
