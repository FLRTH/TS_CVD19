
# coding: utf-8

# In[ ]:


############################################################################
######   COVID-19 situation in Trier-Saarburg per Verbandsgemeinde    ######
############################################################################
##### DEC-20 / by FLRTH #####
#############################


# In[2]:


import requests
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from bs4 import BeautifulSoup
from datetime import timedelta
from datetime import datetime as dt


# In[99]:


URL = 'https://5vier.de/corona-update-208649.html' # Official press statements collected in one page
page = requests.get(URL)
soup = BeautifulSoup(page.content, 'html.parser')

inputVG = ['Konz', 'Saarburg-Kell', 'Hermeskeil', 'Schweich', 'Trier-Land', 'Ruwer'] # Parameters

inhabitantsVG = {'Konz' : 32313, 'Saarburg-Kell' : 23581, 'Hermeskeil' : 15302, 'Schweich' : 28344, 'Trier-Land' : 21947, 'Ruwer' : 18467} # Inhabitants as per wikipedia

lpvg = [] # Array of Verbandsgemeinden to be processed
udates = [] # Array to store dates
lpvg = inputVG
tmpArray = [] # Array to store data

soupArray = soup.get_text().split("\n") # split webpage line by line
getVG = True
firstScan = True
tmpDate = '0'
uDate = ''
tmpIndex = 0

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

# date format is difficult to handle - rebuild dates from scratch
df[['day','month','year']] = df.Date.str.split(".",expand=True,)
df['imonth'] = pd.to_numeric(df.month, errors='coerce')
df.drop(['Date'], axis=1, inplace=True)
df['Date'] = pd.to_datetime(df[['year', 'month', 'day']],format='%Y%m%d')
df.drop(['day', 'imonth', 'month', 'year'], axis=1, inplace=True)
df['Date'] = df['Date'].dt.date
dfvg = pd.DataFrame(columns=["Date", "VG", "CASES", "INCREMENT"]) # empty data frame

for vg in lpvg: # loop through elements
    dfk = df[df['VG'] == vg] # filter elements
    dfk = dfk.reset_index(drop=True)
    dfk.CASES = pd.to_numeric(dfk.CASES, errors='coerce')
    dfk['INCREMENT'] = dfk.CASES.diff(periods=-1)
    maxdatum = dfk['Date'].max() # get latest date
    dfk['7D_INCREMENT'] = dfk[::-1].rolling(7, on='Date')['INCREMENT'].sum() #dfk.rolling(, min_periods=1).sum()
    dfk['7D_INCIDENCE_100T'] = (dfk['7D_INCREMENT'] / inhabitantsVG[vg])*100000
    dfk['7D_INCIDENCE_100T'] = dfk['7D_INCIDENCE_100T'].fillna(0).astype(int)
    dfk = dfk.reset_index(drop=True)
    dfvg = dfvg.append(dfk)

df = dfvg

df.to_excel("Trier-Saarburg" + maxdatum.strftime("%d-%m-%Y") + ".xlsx", index=False)


# In[101]:


#dfp = df.copy()
tf = 30 #int(input('Timeframe [days]: '))

for vg in lpvg: # loop through elements
    dfp = df[df['VG'] == vg]
    maxdatum = dfp['Date'].max() # get latest date
    lastmonth = maxdatum - timedelta(days=tf) # get time frame
    dfp = dfp[(dfp['Date']>= lastmonth)] # filter time frame
    latestNumber = int(dfp[(dfp['VG'] == vg) & (dfp['Date']== maxdatum)]['INCREMENT']) # get latest increment
    latest7dIncidence100t = int(dfp[(dfp['VG'] == vg) & (dfp['Date']== maxdatum)]['7D_INCIDENCE_100T']) # get latest increment
    matplotlib.rcParams['figure.figsize'] = [20, 5]
    if latestNumber < 0:
        nSign = '-'
    else:
        nSign = '+'
    bartitle = vg + ' - ' + str(maxdatum.strftime("%d.%m.%Y")) + ' ' + nSign + str(latestNumber) + ' | 7-Tage Inzidenz: ' + str(latest7dIncidence100t) + ' / 100t' # title
    dfp = dfp.pivot("Date", "VG", "INCREMENT").plot(kind='bar', title=bartitle)
    #plt.show()
    dfp.figure.savefig(maxdatum.strftime("%d-%m-%Y") + '_' + vg + '.png', bbox_inches = "tight")

