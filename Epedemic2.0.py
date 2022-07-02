import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from scipy.optimize import curve_fit
from os.path import expanduser
import os

#--------------------------------------------------Regression functions------------------------------------------------#
def Expfcn(x, c1, c2, c3):
    return c1*np.exp(x*c2) + c3

def Linfcn(x,c1,c2):
    return c1*x + c2

def MovMean(X,N):
    M = []
    Xpad = list(X)
    for k in range(3):
        Xpad.insert(0,X[0])
        Xpad.append(X[-1])
    i = 3
    for x in X:
        M.append(np.mean(Xpad[i-3:i+3]))
        i += 1
    return M

def CurrEst(X,N):
    C = []
    i = 1
    for x in X:
        if i < N:
            C.append(sum(X[0:i]))
        else:
            C.append(sum(X[i-N:i]))
        i += 1
    return C

#--------------------------------------------------Download new data---------------------------------------------------#

#Folkhälsomyndigheten - Covid-19
CovidSv_site = requests.get("https://www.arcgis.com/sharing/rest/content/items/b5e7488e117749c19881cce45db13f7e/data")

#Dropbox - Data från Sveriges regioner
RegionSv_site = requests.get("https://www.dropbox.com/s/woqg0ycep9alybo/Sverige%20statistik.xlsx?dl=1")

#----------------------------------------------------Extract data------------------------------------------------------#

RegionSv = pd.read_excel(RegionSv_site.content)
RegionSv_headers = list(RegionSv.columns)
RegionSv_headers.pop(0)
RegionSv_headers.pop(-1)

CovidSv_NewCases = pd.read_excel(CovidSv_site.content, sheet_name = "Antal per dag region")

CovidSv_Deceased = pd.read_excel(CovidSv_site.content, sheet_name = "Antal avlidna per dag")

Date = CovidSv_NewCases["Statistikdatum"].values
#Second latest date (last dates data may be incomplete)
Today = str(Date[-2])

#---------------------------------------------Data processing and plots------------------------------------------------#

#Options
SaveFig = 1

#Infection active time, N
N = 21

DTime = []
X = []
TotRegion = []
Popnorm = []
Docnorm = []
Sum_Lastweek = []
ActiveEst = []
ThisLast = []

i = 1
plt.figure(5, figsize = [16, 9])
plt.figure(6, figsize = [16, 9])
plt.figure(7, figsize = [16, 9])
k = int(np.sqrt(len(RegionSv_headers)))+1

for n in RegionSv_headers:

    #Data per region
    docs = int(RegionSv[n][1])
    pops = int(RegionSv[n][2])
    New = CovidSv_NewCases[n].values
    New = New[0:-1]
    Sum = sum(New)
    Cumsum = np.cumsum(New)
    New_filter = MovMean(New, 7)

    #------------------Calculations--------------------#

    # Active cases in each region
    ActiveRegion = CurrEst(New, N)
    ActiveRegion_rel = np.array(ActiveRegion)/pops

    #Infection double time
    Speed = np.mean(New[-7:])
    DTime.append(Sum/Speed)

    #Total cases per region
    TotRegion.append(Sum)

    #Normalized to population and doctors
    Popnorm.append(Sum/pops)
    Docnorm.append(docs/ActiveRegion[-1])

    #Estimated active
    ActiveEst.append(sum(New[-N:]))

    #This week vs last week active estimates
    Diff = sum(New[-N:]) - sum(New[-(N+7):-7])
    ThisLast.append(Diff)

    plt.figure(5)
    plt.subplot(k, k, i)
    plt.plot(ActiveRegion, '*')
    plt.title(n)

    plt.figure(6)
    plt.subplot(k, k, i)
    plt.plot(New, '*')
    plt.plot(New_filter, '--')
    plt.title(n)

    plt.figure(7)
    plt.subplot(k, k, i)
    plt.plot(ActiveRegion_rel, '*')
    plt.title(n)
    axes = plt.gca()
    axes.set_xlim([0,len(ActiveRegion_rel)+1])
    axes.set_ylim([0,0.005])
    plt.grid()

    i += 1

    #--------------------------------------------------#

#-----------------National numbers----------------#

National_New = CovidSv_NewCases["Totalt_antal_fall"].values
National_New = National_New[0:-1]
National_Cumsum = np.cumsum(National_New)
National_Sum = sum(National_New)
National_Cumsum_filter = MovMean(National_Cumsum, 7)
National_New_filter = MovMean(National_New, 7)
National_speed = np.mean(National_New[-7:])
National_DTime = National_speed/National_Sum
National_current = CurrEst(National_New, N)

National_Deceased = CovidSv_Deceased["Antal_avlidna"].values
National_Deceased = National_Deceased[0:-1]
National_Deceased_cumsum = np.cumsum(National_Deceased)

#--------------------------------------------------#

#---------------------------------------------Figure configuration-----------------------------------------------------#

#-----------------Total cases per region and double time----------------------#
plt.figure(1, figsize = [16, 9])
plt.suptitle("Totala fall per region och dubbleringstid " + Today[0:10])
plt.subplot(1,2,2)
DTime, X1 = zip(*sorted(zip(DTime, RegionSv_headers)))
for i in range(len(X1)):
    plt.bar(X1[i], DTime[i])
    plt.text(X1[i], DTime[i], int(DTime[i]), horizontalalignment='center')
plt.title("Dubbleringstid med senaste veckans infektionsfart (Högre är bättre)")
plt.subplots_adjust(bottom = 0.20)
plt.ylabel("Dagar")
plt.xticks(rotation=90)

plt.subplot(1,2,1)
TotRegion, X2 = zip(*sorted(zip(TotRegion, RegionSv_headers)))
for i in range(len(X2)):
    plt.bar(X2[i], TotRegion[i])
    plt.text(X2[i], TotRegion[i], int(TotRegion[i]), horizontalalignment='center')
plt.title("Antal bekräftade fall per region")
plt.subplots_adjust(bottom = 0.20)
plt.ylabel("Antal bekräftade fall")
plt.xticks(rotation=90)

#------------------Normalized to population and doctors----------------------#
plt.figure(2, figsize = [16, 9])
plt.suptitle("Statistik relativt antal invånare och läkare " + Today[0:10])
plt.subplot(1, 2, 1)
Popnorm, X3 = zip(*sorted(zip(Popnorm, RegionSv_headers)))
for i in range(len(X3)):
    plt.bar(X3[i], Popnorm[i] * 100)
plt.title("Totalt bekräftade fall av invånarna")
plt.subplots_adjust(bottom = 0.20)
plt.ylabel("%")
plt.xticks(rotation=90)

plt.subplot(1, 2, 2)
Docnorm, X4 = zip(*sorted(zip(Docnorm, RegionSv_headers)))
for i in range(len(X4)):
    plt.bar(X4[i], Docnorm[i])
    plt.text(X4[i], Docnorm[i], int(Docnorm[i]), horizontalalignment='center')
plt.title("Antal läkare per aktivt fall (Återhämtningstid: " + str(N) + " dagar)")
plt.subplots_adjust(bottom = 0.20)
plt.ylabel("Antal läkare")
plt.xticks(rotation=90)

#--------------------------National data plots-------------------------------#
plt.figure(3, figsize = [16, 9])
plt.suptitle("Bekräftade fall nationellt " + Today[0:10])
plt.subplot(2,2,3)
plt.plot(National_current, National_New, '*', label = "Data")
plt.plot(National_current, National_New_filter, '--', label = "Medelvärde över 7 dagar")
plt.title("Antal nya fall relativt aktiva fall")
plt.xlabel("Antal aktiva fall")
plt.ylabel("Antal nya fall")
plt.legend()
plt.grid()
plt.subplots_adjust(hspace = 0.3)

plt.subplot(2,2,1)
plt.plot(National_New, '*', label = "Data")
plt.plot(National_New_filter, '--', label = "Medelvärde över 7 dagar")
plt.title("Antal nya fall per dag")
plt.xlabel("Dagar")
plt.ylabel("Antal nya fall")
plt.legend()
plt.grid()

plt.subplot(2,2,2)
plt.plot(National_Cumsum, '*')
plt.title("Totalt antal bekräftade fall")
plt.xlabel("Dagar")
plt.ylabel("Antal fall")
plt.grid()

plt.subplot(2,2,4)
plt.plot(National_current, '*')
plt.title("Aktiva fall (Ansatt återhämtningstid: " + str(N) + " dagar)")
plt.xlabel("Dagar")
plt.ylabel("Antal aktiva bekräftade fall")
plt.grid()

#Estimated active per region
plt.figure(4, figsize = [16, 9])
plt.subplot(1,2,1)
ActiveEst, X5 = zip(*sorted(zip(ActiveEst, RegionSv_headers)))
for i in range(len(X5)):
    plt.bar(X5[i], ActiveEst[i])
    plt.text(X5[i], ActiveEst[i], int(ActiveEst[i]), horizontalalignment='center')
plt.title("Aktiva fall per region (Återhämtningstid: " + str(N) + " dagar)")
plt.subplots_adjust(bottom = 0.20)
plt.ylabel("Antal aktiva fall")
plt.xticks(rotation=90)

plt.subplot(1,2,2)
ThisLast, X6 = zip(*sorted(zip(ThisLast, RegionSv_headers)))
for i in range(len(X6)):
    plt.bar(X6[i], ThisLast[i])
    plt.text(X6[i], ThisLast[i], int(ThisLast[i]), horizontalalignment='center')
plt.title("Förändring i aktivap fall sedan förra veckan  (Återhämtningstid: " + str(N) + " dagar)")
plt.subplots_adjust(bottom = 0.20)
plt.ylabel("Förändring i aktiva fall")
plt.xticks(rotation=90)
plt.grid()

plt.figure(5)
plt.suptitle("Aktiva fall per region och dag (Ansatt återhämtningstid: " + str(N) + " dagar) " + Today[0:10])
plt.subplots_adjust(hspace = 0.5)

plt.figure(6)
plt.suptitle("Antal nya fall per dag (Data och 7 dagars medelvärde) " + Today[0:10])
plt.subplots_adjust(hspace = 0.5)

plt.figure(7)
plt.suptitle("Procent bekräftade fall av befolkningen " + Today[0:10])
plt.subplots_adjust(hspace = 0.5)
plt.subplots_adjust(wspace = 0.4)

plt.figure(8, figsize = [16, 9])
plt.subplot(1,2,1)
plt.plot(National_Deceased,'*')
plt.title("Nationellt antal avlidna per dag")
plt.xlabel("Dagar")
plt.ylabel("Antal avlidna")
plt.grid()

plt.subplot(1,2,2)
plt.plot(National_Deceased_cumsum,'*')
plt.title("Nationellt cumulativt antal avlidna per dag")
plt.xlabel("Dagar")
plt.ylabel("Antal avlidna")
plt.grid()

if SaveFig == 1:
    for s in range(1,9):
        plt.figure(s)

        #home = expanduser("~")
        #loc = r"\Documents\Epedemic2"
        output = "\Output " + Today[0:10]
        filename = r"\Fig" + str(s) + " " + Today[0:10] + r".png"
        loc = r"C:\Users\Onjii\OneDrive\Dokument\Jobb\ABB\Covid19 stats"
        #path = home + loc + output
        path = loc + output
        #path = loc + filename
        savepath = path + filename
        if not os.path.exists(path): os.mkdir(path)
        plt.savefig(savepath)
    os.startfile(path)


