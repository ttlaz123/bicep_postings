import pandas as pd 
from typing import Tuple
import numpy as np
import matplotlib.pyplot as plt

CHIP_NAME = '0'
PASSED = 'Perfect'
INPUT_FAIL = 'Open Input/other anomaly'
RS_FAIL = 'RS Anomaly'
ICCOL_FAIL = 'Ic Anomaly'
SCREEN_FAIL = 'Could not screen. Needs re-mount / re-screen'
PCB_NAME =  'PCB'
LOCATION = 'LOC'
NOTES = 'Note'
NOTES2 = 'More notes'


def read_squid_data(filename: str ) -> Tuple[dict, dict]:
    '''
    takes in path to tsv file
    returns dict of pcbs and dict of squid chips
    '''

    
    df = pd.read_table(filename)
    pcb_dict = {}
    chip_dict = {}
    prev_pcb = 0
    poscount = -1
    poscol = ['X', 'Y', 'Z']
    for index, row in df.iterrows():
        cur_pcb = row[PCB_NAME]
        if(cur_pcb is None or str(cur_pcb) == 'nan'):
            continue 

        cur_chip = row[CHIP_NAME]
        date = cur_pcb.split('_')[0]
        
        wafer = cur_chip.split('_')[0]
        if(not cur_pcb == prev_pcb):
            poscount = 0
            prev_pcb = cur_pcb
        else: 
            poscount += 1
        ncol = poscol[poscount%3]
        nrow = str(int(poscount/3))
        pos = ncol + nrow
        isRescreen = (cur_chip in chip_dict)

        if(not cur_pcb in pcb_dict):
            pcb_dict[cur_pcb] = {
                CHIP_NAME:set(), 
                'wafers':wafer,
                'date':date,
                PASSED:0,
                'fail':0,
                'unknown':0,
                'bypass':0,
                'rescreens':0
            }
            
        if(not isRescreen):
            chip_dict[cur_chip] = {
                PCB_NAME: set(),
                'wafer': wafer,
                'nscreens': 0,
                PASSED: False, 
                SCREEN_FAIL:[],
                LOCATION:[],
            }

        pcb_dict[cur_pcb][CHIP_NAME].add(cur_chip) 
        ifPassed = (row[PASSED] == 'x')
        ifBypassed = ('bypass' in str(row[SCREEN_FAIL]))
        
        pcb_dict[cur_pcb]['bypass'] += int(ifBypassed)
        pcb_dict[cur_pcb][PASSED] += int(ifPassed)
        pcb_dict[cur_pcb]['rescreens'] += int(isRescreen)

        chip_dict[cur_chip][PCB_NAME].add(cur_pcb)
        chip_dict[cur_chip]['nscreens'] += 1
        chip_dict[cur_chip][PASSED] = ifPassed
        chip_dict[cur_chip][LOCATION] = pos 
        fails = {
            INPUT_FAIL: row[INPUT_FAIL],
            RS_FAIL: row[RS_FAIL],
            ICCOL_FAIL: row[ICCOL_FAIL],
            SCREEN_FAIL: row[SCREEN_FAIL],
            NOTES: row[NOTES],
            NOTES2: row[NOTES2]
        }
        chip_dict[cur_chip][SCREEN_FAIL].append(fails)
    
    return chip_dict, pcb_dict

def within_dates(dates, startdate, enddate):
    within_dates = False 
    for date in dates:
        if(date > startdate and date < enddate):
            within_dates = True 
    return within_dates

def plot_passrate_data(chip_dict: dict, pcb_dict:dict, savename:str,
                       startdate:str = '00000000', enddate:str = '99999999'):
    plt.figure(figsize=(16,6))
    barWidth = 0.3
    wafers = {}
    for chip in chip_dict:
        pcbs = chip_dict[chip][PCB_NAME]
        dates = [p.split('_')[0] for p in pcbs]
        
        if(not within_dates(dates, startdate, enddate)):
            continue
        wafer = chip_dict[chip]['wafer']
        if(not wafer in wafers):
            wafers[wafer] = {
                'count':0,
                'passed':0
            }
        
        wafers[wafer]['count'] += 1
        # only count the chip if it passed within screening period
        passed = chip_dict[chip][PASSED] and max(dates) < enddate
        wafers[wafer]['passed'] += int(passed)
    
    bars_count = []
    bars_passed = []
    xlabels = []
    keylist = list(wafers.keys())
    keylist.sort()
    for wafer in keylist:
        if(not 'w' in wafer):
            continue
        
        percent = wafers[wafer]['passed'] / wafers[wafer]['count']
        xlabels.append(wafer + ': ' + str(int(percent*100)) + '%')
        bars_count.append(wafers[wafer]['count'])
        bars_passed.append(wafers[wafer]['passed'])

    r1 = np.arange(len(bars_count))
    r2 = [x + barWidth for x in r1]

    plt.bar(r1, bars_count, width = barWidth, color = 'blue', 
            edgecolor = 'black', capsize=7, label='All')
 
    plt.bar(r2, bars_passed, width = barWidth, color = 'cyan', 
            edgecolor = 'black',  capsize=7, label='Passed')
    
    plt.xticks([r + barWidth for r in range(len(bars_count))], xlabels)
    plt.ylabel('Count')
    plt.title('Pass Rate of Squid Chips by Wafer from ' + 
              startdate + ' to ' + enddate)
    plt.legend()
    
    plt.savefig(savename)
    plt.show()

def plot_passrate_by_rescreen(chip_dict, pcb_dict, savename,
                       startdate:str = '00000000', enddate:str = '99999999'):
    plt.figure(figsize=(16,6))
    barWidth = 0.3
    rescreens = {1:0, 2:0, 3:0, 4:0, 5:0}
    passes = {1:0, 2:0, 3:0, 4:0, 5:0}
    for chip in chip_dict:
        pcbs = chip_dict[chip][PCB_NAME]
        dates = [p.split('_')[0] for p in pcbs]
        dates.sort()
        if(not within_dates(dates, startdate, enddate)):
            continue
        rescreen_count = 0

        for date in dates:
            rescreen_count += 1
            if(date > startdate and date < enddate):
                rescreens[rescreen_count] += 1
                if(chip_dict[chip][PASSED] and date == max(dates)):
                        passes[rescreen_count] += 1
                
    bars_count = []
    bars_passed = []
    xlabels = []
    for n in rescreens:
        percent = passes[n] / rescreens[n]
        xlabels.append('Screen number ' + str(n) + ': ' + str(int(percent*100)) + '%')
        bars_count.append(rescreens[n])
        bars_passed.append(passes[n])
    r1 = np.arange(len(bars_count))
    r2 = [x + barWidth for x in r1]

    plt.bar(r1, bars_count, width = barWidth, color = 'blue', 
            edgecolor = 'black', capsize=7, label='All')
 
    plt.bar(r2, bars_passed, width = barWidth, color = 'cyan', 
            edgecolor = 'black',  capsize=7, label='Passed')
    
    plt.xticks([r + barWidth for r in range(len(bars_count))], xlabels)
    plt.ylabel('Count')
    plt.title('Pass Rate of Squid Chips by Screen Number from ' + 
              startdate + ' to ' + enddate)
    plt.legend()
    
    plt.savefig(savename)
    plt.show()



def plot_rescreen_data(chip_dict, pcb_dict, savename,
                       startdate:str = '00000000', enddate:str = '99999999'):
    plt.figure(figsize=(16,6))
    barWidth = 0.15
    wafers = {}
    for chip in chip_dict:
        pcbs = chip_dict[chip][PCB_NAME]
        dates = [p.split('_')[0] for p in pcbs]
        wafer = chip_dict[chip]['wafer']
        rescreen_num = 0

        for date in dates:
            if(date < enddate):
                rescreen_num += 1
        if(rescreen_num == 0 or not within_dates(dates, startdate, enddate)):
            continue
        if(not wafer in wafers):
            wafers[wafer] = {

                1:0,
                2:0,
                3:0,
                4:0,
                5:0,
            }
        
       
        wafers[wafer][rescreen_num] += 1
    
    bars= [[],[],[],[],[]]
    xlabels = []
    keylist = list(wafers.keys())
    keylist.sort()
    for wafer in keylist:
        if(not 'w' in wafer):
            continue
        for nrescreen in range(5):
            bars[nrescreen].append(wafers[wafer][nrescreen+1])

        xlabels.append(wafer)

    r1 = np.arange(len(bars[0]))
    r2 = [x + barWidth for x in r1]
    r3 = [x + barWidth for x in r2]
    r4 = [x + barWidth for x in r3]
    r5 = [x + barWidth for x in r4]

    rs =[r1, r2, r3, r4, r5]
    for i in range(5):
        plt.bar(rs[i], bars[i], width = barWidth, 
            edgecolor = 'black', capsize=7, label=i+1)
    
    plt.xticks([r + barWidth for r in range(len(bars[0]))], xlabels)
    plt.ylabel('Count')
    plt.title('Number of Screens per Squid Chips by Wafer from ' + 
              startdate + ' to ' + enddate)
    plt.legend()
    
    plt.savefig(savename)
    plt.show()

def main():
    startstart = '00000000'
    endend = '99999999'
    kuostart = '20220401'
    badstart = '20220901'
    nickstart = '20210501'
    c,p = read_squid_data('../cold_screening.tsv')
    plot_passrate_by_rescreen(c,p,'sample.png', 
                       startdate=startstart, enddate=endend)

if __name__ == '__main__':
    main()