import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from scipy.optimize import curve_fit
from os.path import expanduser
import os
import streamlit as st 

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

@st.cache(suppress_st_warning=True)
def UpdateGraphs():
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
    SaveFig = 0

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
        axes.set_ylim([0,0.030])
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
    Delay = 19
    National_Deceased = National_Deceased[0:-(1+Delay)]
    National_Deceased_cumsum = np.cumsum(National_Deceased)

    #--------------------------------------------------#

    #---------------------------------------------Figure configuration-----------------------------------------------------#

    #-----------------Total cases per region and double time----------------------#
    fig1 = plt.figure(1, figsize = [16, 9])
    plt.suptitle("Total reported cases per region + time to double cases " + Today[0:10])
    plt.subplot(1,2,2)
    DTime, X1 = zip(*sorted(zip(DTime, RegionSv_headers)))
    for i in range(len(X1)):
        plt.bar(X1[i], DTime[i])
        plt.text(X1[i], DTime[i], int(DTime[i]), horizontalalignment='center')
    plt.title("Time to double cases with last weeks speed (Higher is better)")
    plt.subplots_adjust(bottom = 0.20)
    plt.ylabel("Days")
    plt.xticks(rotation=90)

    plt.subplot(1,2,1)
    TotRegion, X2 = zip(*sorted(zip(TotRegion, RegionSv_headers)))
    for i in range(len(X2)):
        plt.bar(X2[i], TotRegion[i])
        plt.text(X2[i], TotRegion[i], int(TotRegion[i]), horizontalalignment='center', rotation = 90)
    plt.title("Confirmed cases per region")
    plt.subplots_adjust(bottom = 0.20)
    plt.ylabel("Confirmed cases")
    plt.xticks(rotation=90)

    #------------------Normalized to population and doctors----------------------#
    fig2 = plt.figure(2, figsize = [16, 9])
    plt.suptitle("Statistics normalized to inhabitants and number of doctors " + Today[0:10])
    plt.subplot(1, 2, 1)
    Popnorm, X3 = zip(*sorted(zip(Popnorm, RegionSv_headers)))
    for i in range(len(X3)):
        plt.bar(X3[i], Popnorm[i] * 100)
    plt.title("Total confirmed cases, normalized to inhabitants")
    plt.subplots_adjust(bottom = 0.20)
    plt.ylabel("%")
    plt.xticks(rotation=90)

    plt.subplot(1, 2, 2)
    Docnorm, X4 = zip(*sorted(zip(Docnorm, RegionSv_headers)))
    for i in range(len(X4)):
        plt.bar(X4[i], Docnorm[i])
        plt.text(X4[i], Docnorm[i], int(Docnorm[i]), horizontalalignment='center')
    plt.title("Number of doctors per active case (Assumed recovery time: " + str(N) + " days)")
    plt.subplots_adjust(bottom = 0.20)
    plt.ylabel("Doctors per confirmed case")
    plt.xticks(rotation=90)

    #--------------------------National data plots-------------------------------#
    fig3 = plt.figure(3, figsize = [16, 9])
    plt.suptitle("Confirmed cases nationally " + Today[0:10])
    plt.subplot(2,2,3)
    plt.plot(National_current, National_New, '*', label = "Data")
    plt.plot(National_current, National_New_filter, '--', label = "7 day average")
    plt.title("New cases relative active cases")
    plt.xlabel("Active cases")
    plt.ylabel("New cases")
    plt.legend()
    plt.grid()
    plt.subplots_adjust(hspace = 0.3)

    plt.subplot(2,2,1)
    plt.plot(National_New, '*', label = "Data")
    plt.plot(National_New_filter, '--', label = "7 day average")
    plt.title("New cases per day")
    plt.xlabel("Days")
    plt.ylabel("New cases")
    plt.legend()
    plt.grid()

    plt.subplot(2,2,2)
    plt.plot(National_Cumsum, '*')
    plt.title("Total number of confirmed cases")
    plt.xlabel("Days")
    plt.ylabel("Number of cases")
    plt.grid()

    plt.subplot(2,2,4)
    plt.plot(National_current, '*')
    plt.title("Active cases (Assumed recovery time: " + str(N) + " days)")
    plt.xlabel("Days")
    plt.ylabel("Active confirmed cases")
    plt.grid()

    #Estimated active per region
    fig4 = plt.figure(4, figsize = [16, 9])
    plt.subplot(1,2,1)
    ActiveEst, X5 = zip(*sorted(zip(ActiveEst, RegionSv_headers)))
    for i in range(len(X5)):
        plt.bar(X5[i], ActiveEst[i])
        plt.text(X5[i], ActiveEst[i], int(ActiveEst[i]), horizontalalignment='center', rotation = 90)
    plt.title("Active cases per region (Assumed recovery time: " + str(N) + " days)")
    plt.subplots_adjust(bottom = 0.20)
    plt.ylabel("Number of active cases")
    plt.xticks(rotation=90)

    plt.subplot(1,2,2)
    ThisLast, X6 = zip(*sorted(zip(ThisLast, RegionSv_headers)))
    for i in range(len(X6)):
        plt.bar(X6[i], ThisLast[i])
        plt.text(X6[i], ThisLast[i], int(ThisLast[i]), horizontalalignment='center')
    plt.title("1 week change in active cases  (Assumed recovery time: " + str(N) + " days)")
    plt.subplots_adjust(bottom = 0.20)
    plt.ylabel("Change in active cases")
    plt.xticks(rotation=90)
    plt.grid()

    fig5 = plt.figure(5)
    plt.suptitle("Active cases per day and region (Assumed recovery time: " + str(N) + " days) " + Today[0:10])
    plt.subplots_adjust(hspace = 0.5)

    fig6 = plt.figure(6)
    plt.suptitle("New cases per day (Data and 7-day average) " + Today[0:10])
    plt.subplots_adjust(hspace = 0.5)

    fig7 = plt.figure(7)
    plt.suptitle("Confirmed cases relative to population in each region " + Today[0:10])
    plt.subplots_adjust(hspace = 0.5)
    plt.subplots_adjust(wspace = 0.4)

    fig8 = plt.figure(8, figsize = [16, 9])
    plt.suptitle("Deceased Nationally (Last " + str(Delay) + " days omitted due to retroactive changes) (Data retrieved: " + Today[0:10] + ")")
    plt.subplot(1,2,1)
    plt.plot(National_Deceased,'*')
    plt.title("Nationally deceased per day")
    plt.xlabel("Days")
    plt.ylabel("Number of deceased")
    plt.grid()

    plt.subplot(1,2,2)
    plt.plot(National_Deceased_cumsum,'*')
    plt.title("Nationally cumulative deceased per day")
    plt.xlabel("Days")
    plt.ylabel("Number of deceased")
    plt.grid()
    st.pyplot(fig1)
    st.pyplot(fig2)
    st.pyplot(fig3)
    st.pyplot(fig4)
    st.pyplot(fig5)
    st.pyplot(fig6)
    st.pyplot(fig7)
    st.pyplot(fig8)

st.title('Epedemic webb app')
UpdateGraphs()







