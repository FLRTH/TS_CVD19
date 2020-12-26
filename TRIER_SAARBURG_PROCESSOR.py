#!/usr/bin/env python

# coding: utf-8


############################################################################
######   COVID-19 situation in Trier-Saarburg per Verbandsgemeinde    ######
############################################################################
##### DEC-20 / by FLRTH #####
#############################


print('>> Start...')

import requests
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from bs4 import BeautifulSoup
from datetime import timedelta
from datetime import datetime as dt
from github import Github
import os

print('>> Getting data')

dataURL = 'https://5vier.de/corona-update-208649.html' # Official press statements collected in one page
inhabitantsDataURL = r'https://raw.githubusercontent.com/FLRTH/TS_CVD19/main/trier_saarburg_vg_inhabitants.csv' # Inhabitants organised in csv file
auxDataURL = r'https://raw.githubusercontent.com/FLRTH/TS_CVD19/main/COVID-19_LK_TRIER_SAARBURG_DATA.csv'

github_access = 'tscvd19_github_access.txt'
saveFolder = 'tscvd19_saveFolder.txt'

vgdf = pd.read_csv(inhabitantsDataURL) # Get inhabitants data
vg_data = pd.Series(vgdf.inhabitants.values,index=vgdf.vg).to_dict()

page = requests.get(dataURL) # Get raw data
soup = BeautifulSoup(page.content, 'html.parser') # parse html
soupArray = soup.get_text().split("\n") # split webpage line by line

getVG = True # only capture if desired
firstScan = True # make sure it is the first scan
tmpDate = '0' # tmp date
uDate = '' # stores dates temporarily
tmpIndex = 0 # handles 2 lines of data in source
tf = 30 # timeframe to plot
udates = [] # Array to store dates
tmpArray = [] # Array to store data

print('>> Processing data')

for line in soupArray:
    if line[:2] == 'Am' and firstScan: # first element is different from subsequent elements
        firstDate = line[:40].split('(')[len(line[:40].split('(')) -1 ].split(')')[0] # get date
        firstScan = False # run this element only once
    if line[:15] == 'Corona Update: ':
        uDate = line[-12:].replace('(','').replace(')','') # get date
        if uDate != tmpDate:
            tmpDate = uDate
            udates.append(uDate) # add dates
            getVG = True
    if line[:2] == 'VG' and getVG: # find data position
        tmpvg = line.replace('\xa0','')
        tmpvgArray = tmpvg.split('VG ')
        tmpvgArray = list(filter(None, tmpvgArray))
        if soupArray.index(line)==tmpIndex+1:
            getVG = False
        tmpIndex = soupArray.index(line)
        for e in tmpvgArray:
            try:
                tmpArray.append([uDate.replace('-',''), e.split(': ')[0].replace(' ','').replace(',','').replace('.',''), e.split(': ')[1].replace(' ','').replace(',','').replace('.','')]) # add data
            except:
                tmpArray.append([uDate, 'ERROR', 'ERROR']) # if data has errors, add as error    
                
for t in tmpArray: # first date retrieval is different - add the latest date
    if t[0] == '':
        t[0] = firstDate



        

df = pd.DataFrame(tmpArray, columns=["Date", "VG", "CASES"]) # build data frame
df = df[df['VG'] != 'ERROR'] # remove errors
df = df[df['Date'].str.contains("2020")] # remove date errors

dftmp = df.copy()
dftmp[['day','month','year']] = df.Date.str.split(".",expand=True,)
dftmp['imonth'] = pd.to_numeric(dftmp.month, errors='coerce')
dftmp['Date'] = pd.to_datetime(dftmp[['year', 'month', 'day']],format='%Y%m%d')
tmpmaxDate = dftmp['Date'].max()



auxRawData = pd.read_csv(auxDataURL) # Get inhabitants data
auxRawData.drop(['7D_INCIDENCE_100T', '7D_INCREMENT', 'INCREMENT'], axis=1, inplace=True)
auxRawData[['year','month','day']] = auxRawData.Date.str.split("-",expand=True,)
auxRawData['tmpDate'] = pd.to_datetime(auxRawData[['year', 'month', 'day']],format='%Y%m%d')
maxAuxDate = auxRawData['tmpDate'].max()
auxRawData['Date'] = auxRawData['day'] + '.' + auxRawData['month'] + '.' + auxRawData['year']
auxRawData = auxRawData[['Date', 'VG', 'CASES']]
auxtmpArray = auxRawData.as_matrix().tolist()

daytrys = dt.today().date().day
trys = True

# if the latest data is not available on the usual article, fetch latest data from a different source
if dt.today().date() > tmpmaxDate.date():
    print('>> Main data source outdated - switching to auxiliary data source')
    
    auxBaseURL = 'https://trier-saarburg.de/'
    
    while trys:
        if maxAuxDate.date().day == daytrys:
            trys = False
        if maxAuxDate.date().day == dt.today().date().day:
            print('>> Latest data already available in auxiliary data source')
            tmpArray = auxtmpArray
            df = pd.DataFrame(tmpArray, columns=["Date", "VG", "CASES"]) # build data frame
            df = df[df['VG'] != 'ERROR'] # remove errors
            df = df[df['Date'].str.contains("2020")] # remove date errors
        if trys:
            firstAux = False
            if maxAuxDate.date() > tmpmaxDate.date() and maxAuxDate.date().day <= daytrys:
                print('>> Retrieving heritage data')
                tmpArray = auxtmpArray
                auxURL = auxBaseURL + str(dt.today().date().year) + '/' + str(dt.today().date().month) + '/' + str(daytrys) + '/'
                daytrys = daytrys - 1
            elif dt.today().date().day == tmpmaxDate.date().day+1:
                auxURL = auxBaseURL + str(dt.today().date().year) + '/' + str(dt.today().date().month) + '/' + str(dt.today().date().day) + '/'
            else:
                auxURL = auxBaseURL + str(dt.today().date().year) + '/' + str(dt.today().date().month) + '/' + str(tmpmaxDate.date().day + 1) + '/'

            auxpage = requests.get(auxURL) # Get raw data
            auxsoup = BeautifulSoup(auxpage.content, 'html.parser') # parse html
            auxsoupArray = auxsoup.get_text().split("\n") # split webpage line by line


            tmpDate = '0' # tmp date
            auxuDate = '' # stores dates temporarily
            tmpIndex = 0 # handles 2 lines of data in source
            tf = 30 # timeframe to plot
            auxudates = [] # Array to store dates

            tmpDate = tmpmaxDate.date() + timedelta(days=1)
            latestDate = str(daytrys+1) + '.' + str(tmpDate.month) + '.' + str(tmpDate.year)
            #print(latestDate)

            print('>> Processing data')
            for line in auxsoupArray:
                if line[:2] == 'VG': # find data position
                    #print(line)

                    tmpvg = line.replace('\xa0','')
                    tmpvgArray = tmpvg.split('VG ')
                    #print(tmpvgArray)
                    tmpvgArray = list(filter(None, tmpvgArray))
                    if auxsoupArray.index(line)==tmpIndex+1:
                        getVG = False
                    tmpIndex = auxsoupArray.index(line)
                    for e in tmpvgArray:
                        #print(latestDate)
                        try:
                            tmpArray = [([auxuDate.replace('-',''), e.split(': ')[0].replace(' ','').replace(',','').replace('.',''), e.split(': ')[1].replace(' ','').replace(',','').replace('.','')])] + tmpArray # add data
                            #tmpArray.append([auxuDate.replace('-',''), e.split(': ')[0].replace(' ','').replace(',','').replace('.',''), e.split(': ')[1].replace(' ','').replace(',','').replace('.','')]) # add data
                        except:
                            tmpArray = [([auxuDate, 'ERROR', 'ERROR'])] + tmpArray # if data has errors, add as error    
            for t in tmpArray: # first date retrieval is different - add the latest date
                if t[0] == '':
                    t[0] = latestDate #firstDate

            #print(tmpArray)
            df = pd.DataFrame(tmpArray, columns=["Date", "VG", "CASES"]) # build data frame
            df = df[df['VG'] != 'ERROR'] # remove errors
            df = df[df['Date'].str.contains("2020")] # remove date errors

        
#print(df)


#print('Reformat dates')

# date format is difficult to handle - rebuild dates from scratch
df[['day','month','year']] = df.Date.str.split(".",expand=True,)
df['imonth'] = pd.to_numeric(df.month, errors='coerce')
df.drop(['Date'], axis=1, inplace=True)
df['Date'] = pd.to_datetime(df[['year', 'month', 'day']],format='%Y%m%d')
df.drop(['day', 'imonth', 'month', 'year'], axis=1, inplace=True)
df['Date'] = df['Date'].dt.date
dfvg = pd.DataFrame(columns=["Date", "VG", "CASES", "INCREMENT"]) # empty data frame

#print('Build data set')

for vg in list(vg_data.keys()): # loop through elements
    dfk = df[df['VG'] == vg] # filter elements
    dfk = dfk.reset_index(drop=True)
    dfk.CASES = pd.to_numeric(dfk.CASES, errors='coerce')
    dfk['INCREMENT'] = dfk.CASES.diff(periods=-1) # calculate increment
    maxdatum = dfk['Date'].max() # get latest date
    dfk['7D_INCREMENT'] = dfk[::-1].rolling(7, on='Date')['INCREMENT'].sum() #dfk.rolling(, min_periods=1).sum()
    dfk['7D_INCIDENCE_100T'] = (dfk['7D_INCREMENT'] / vg_data[vg])*100000 # calculate 7 day incidence
    dfk['7D_INCIDENCE_100T'] = dfk['7D_INCIDENCE_100T'].fillna(0).astype(int) 
    dfk = dfk.reset_index(drop=True)
    dfvg = dfvg.append(dfk)

df = dfvg

df.CASES = pd.to_numeric(df.CASES, errors='coerce')

#print('Save csv')

saveto = open(saveFolder, "r").readline().split(';')[0]
df.to_excel(saveto + "Trier-Saarburg_" + maxdatum.strftime("%d-%m-%Y") + ".xlsx", index=False)
df.to_csv("COVID-19_LK_TRIER_SAARBURG_DATA.csv", index=False)

#print('Build overview')
# build overview table
dft = df.copy()
dft = dft[['VG','Date', 'INCREMENT','CASES','7D_INCIDENCE_100T','7D_INCREMENT']]
dft = dft[(dft['Date'] == maxdatum)]
vgs = np.array(dft['VG'])
dft.drop(['VG'], axis=1, inplace=True)
fig, ax = plt.subplots(1,1)
ax.axis('tight')
ax.axis('off')
ax.table(cellText=dft.values,colLabels=dft.columns,rowLabels=vgs,loc="center")

#plt.show()
ax.figure.savefig('LANDKREIS.pdf', bbox_inches = "tight") #maxdatum.strftime("%d-%m-%Y") + '_LANDKREIS.png')

print('---------------------------------------------------------------------')
#print('Create charts')
for vg in list(vg_data.keys()): # loop through elements
    dfk = df[df['VG'] == vg] # filter only on elements
    dfk = dfk.reset_index(drop=True)
    dfk.CASES = pd.to_numeric(dfk.CASES, errors='coerce')
    dfk['INCREMENT'] = dfk.CASES.diff(periods=-1) # get real increment
    #dfo = dfk.copy()
    maxdatum = dfk['Date'].max() # get latest date
    lastmonth = maxdatum - timedelta(days=tf) # get time frame
    lastseven = maxdatum - timedelta(days=6)
    totalLastSeven = dfk[(dfk['Date']>= lastseven)]['INCREMENT'].sum() # get 7 day total infections
    incdn = int((totalLastSeven / vg_data[vg])*100000) # calculate 7 day incidence rate
    dfk = dfk[(dfk['Date']>= lastmonth)] # filter on time frame
    dfk = dfk.sort_values(by='Date') # sort dates
    dfk = dfk.reset_index(drop=True)
    latestNumber = int(dfk[(dfk['VG'] == vg) & (dfk['Date']== maxdatum)]['INCREMENT']) # get latest increment
    matplotlib.rcParams['figure.figsize'] = [20, 5]
    if latestNumber < 0:
        nSign = '-'
    else:
        nSign = '+'
    if len(str(latestNumber)) == 1:
        ltstNbr = ' ' + str(latestNumber)
    else:
        ltstNbr = str(latestNumber)
    bartitle = vg + ' - ' + str(maxdatum.strftime("%d.%m.%Y")) + ' ' + nSign + ltstNbr + ' | 7-Tage Inzidenz: ' + str(incdn) + ' / 100t' # title
    if len(bartitle.split(' - ')[0])>10:
        tbs = ':\t'
    else:
        tbs = ':\t\t'
    if len(bartitle.split(' - ')[1].split(': ')[1]) == 9:
        ldspc = ' '
    else:
        ldspc = ''
    print('>> ' + bartitle.split(' - ')[0] + tbs + bartitle.split(' - ')[1].split(': ')[0] + ': ' + ldspc + bartitle.split(' - ')[1].split(': ')[1])
    dfk = dfk.pivot("Date", "VG", "INCREMENT").plot(kind='bar', title=bartitle) #.set_xticklabels([])

    #plt.show()
    dfk.figure.savefig(vg + '.pdf', bbox_inches = "tight") #maxdatum.strftime("%d-%m-%Y") + '_' + vg + '.png', bbox_inches = "tight")
    

# collect upload elements
uploadContent = list(vg_data.keys())
uploadContent.append('LANDKREIS')
uploadContent.append('COVID-19_LK_TRIER_SAARBURG_DATA.csv')
    
# reformat / could be done differently by scanning root folder for elements in uploadContent
i = 0
for x in uploadContent:
    if not x.endswith('.csv'):
        x = x + '.pdf'
        uploadContent[i] = x
        i = i+1

print('---------------------------------------------------------------------')

print('>> Latest on github:\t' + str(maxAuxDate.date().day) + '.' + str(maxAuxDate.date().month) + '.' + str(maxAuxDate.date().year))

upld = input('>> Upload to github? y/n ')

if upld == 'y':
    print('>> Uploading...')
    token = open(github_access, "r").readline().split(';')[0]
    g = Github(token) # log-in
    repo = g.get_user().get_repo('TS_CVD19')

    # based on example to be found on stackoverflow by Bhuvanesh: https://stackoverflow.com/questions/63427607/python-upload-files-directly-to-github-using-pygithub
    all_files = []
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            file = file_content
            all_files.append(str(file).replace('ContentFile(path="','').replace('")',''))

    for c in uploadContent:
        if c.endswith('.csv'):
            with open(c, 'r') as file:
                content = file.read()
        else:  
            with open(c, 'rb') as file:
                content = file.read()

        # Upload to github
        git_file = c
        if git_file in all_files:
            contents = repo.get_contents(git_file)
            repo.update_file(contents.path, "updated " + maxdatum.strftime("%d-%m-%Y"), content, contents.sha, branch="main")
            print('>> ' + git_file + ' updated')
        else:
            repo.create_file(git_file, "created " + maxdatum.strftime("%d-%m-%Y"), content, branch="main")
            print('>> ' + git_file + ' created')
    print('>> Completed.')

for c in uploadContent:
    os.remove(c)
