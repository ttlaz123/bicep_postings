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

COLORS = ['dimgray', 'limegreen', 'darkorange', 'mediumpurple', 'crimson']
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
    '''
    Determines whether at least one date is within the range
    '''
    within_dates = False 
    for date in dates:
        if(date > startdate and date < enddate):
            within_dates = True 
    return within_dates

def plot_barplot(bars_dict, xlabels, dic_labels, title='Bar Plot', savename='sample'):
    '''
    Input: plotting data, bars_dict is a dict of lists
    Ouput: barplots
    '''
    plt.figure(figsize=(16,6))
    barWidth = 0.9 / (len(bars_dict)+1)
    shift = 0
    for lab in dic_labels:
        r = np.arange(len(bars_dict[lab]))
        r = [x + barWidth * shift for x in r]
        shift += 1
        plt.bar(r, bars_dict[lab], width = barWidth, color = COLORS[shift-1],
            edgecolor = 'black', capsize=7, label=lab)
    
    plt.xticks([r + barWidth for r in range(len(bars_dict[lab]))], xlabels)
    plt.xticks(rotation=15)
    plt.ylabel('Count')
    plt.title(title)
    plt.legend()
    
    plt.savefig(savename)
    #plt.show()
    plt.close()

def get_batches(tlist):
    return tlist[:-1]

def find_batch(tlist, pcb):
    for i in range(len(tlist)):
        if (pcb < tlist[i]):
            return tlist[i-1]
    return tlist[i] 
def plot_passrate_by_screenbatch(chip_dict: dict, pcb_dict:dict, tlist:list, savename:str,
                       startdate:str = '00000000', enddate:str = '99999999'):
    batches = get_batches(tlist)
    count = {key: 0 for key in batches}
    passed = {key: 0 for key in batches}
    bypassed = {key: 0 for key in batches}
    unknown = {key: 0 for key in batches}
    for pcb in pcb_dict:
        if(not within_dates([pcb_dict[pcb]['date']], startdate, enddate)):
            continue 
        batch = find_batch(tlist, pcb)
        count[batch] += len(pcb_dict[pcb][CHIP_NAME])
        passed[batch] += pcb_dict[pcb][PASSED]
        bypassed[batch] += pcb_dict[pcb]['bypass']
        for c in pcb_dict[pcb][CHIP_NAME]:
            dates = chip_dict[c][PCB_NAME]
            unknown[batch] += int(max(dates) > pcb)
    bars_count = []
    bars_passed = []
    bars_bypassed = []
    bars_unknown = []
    bars_fail = []
    xlabels = []
    for batch in batches:
        
        bars_count.append(count[batch])
        bars_passed.append(passed[batch])
        try:
            percent =passed[batch] /count[batch]
            pstr = str(int(percent*100)) 
        except ZeroDivisionError:
            pstr = 'NaN' 
        xlabels.append(batch + ': ' + pstr + '%')
        bars_bypassed.append(bypassed[batch])
        bars_unknown.append(unknown[batch])
        bars_fail.append(bars_count[-1]-bars_passed[-1]-bars_bypassed[-1]-bars_unknown[-1])

    title_suffix =  'by Screen Batch from ' + startdate + ' to ' + enddate
    title = 'Screening Reulsts ' + title_suffix
    bars_dict = {
        'All': bars_count,
        'Passed': bars_passed,
        #'Bypassed': bars_bypassed,
        #'Unknown': bars_unknown,
        #'Fail': bars_fail
    }
    dic_labels = ['All', 'Passed']
    plot_barplot(bars_dict, xlabels, dic_labels, title, savename)


def plot_failrate_by_screenbatch(chip_dict: dict, pcb_dict:dict, tlist:list, savename:str,
                       startdate:str = '00000000', enddate:str = '99999999'):
    batches = get_batches(tlist)
    count = {key: 0 for key in batches}
    passed = {key: 0 for key in batches}
    bypassed = {key: 0 for key in batches}
    unknown = {key: 0 for key in batches}
    for pcb in pcb_dict:
        if(not within_dates([pcb_dict[pcb]['date']], startdate, enddate)):
            continue 
        batch = find_batch(tlist, pcb)
        count[batch] += len(pcb_dict[pcb][CHIP_NAME])
        passed[batch] += pcb_dict[pcb][PASSED]
        bypassed[batch] += pcb_dict[pcb]['bypass']
        for c in pcb_dict[pcb][CHIP_NAME]:
            dates = chip_dict[c][PCB_NAME]
            unknown[batch] += int(max(dates) > pcb)
    bars_count = []
    bars_passed = []
    bars_bypassed = []
    bars_unknown = []
    bars_fail = []
    xlabels = []
    for batch in batches:
        xlabels.append(batch )
        bars_count.append(count[batch])
        bars_passed.append(passed[batch])
        bars_bypassed.append(bypassed[batch])
        bars_unknown.append(unknown[batch])
        bars_fail.append(bars_count[-1]-bars_passed[-1]-bars_bypassed[-1]-bars_unknown[-1])

    title_suffix =  'by Screen Batch from ' + startdate + ' to ' + enddate
    title = 'Screening Reulsts ' + title_suffix
    bars_dict = {
        'All': bars_count,
        'Passed': bars_passed,
        'Warm Fail': bars_bypassed,
        'Unknown': bars_unknown,
        'Cold Fail': bars_fail
    }
    dic_labels = ['All', 'Passed', 'Warm Fail', 'Cold Fail', 'Unknown']
    plot_barplot(bars_dict, xlabels, dic_labels, title, savename)

def plot_rescreen_by_screenbatch(chip_dict: dict, pcb_dict:dict, tlist:list, savename:str,
                       startdate:str = '00000000', enddate:str = '99999999'):
    batches = get_batches(tlist)
    max_screens = 5
    
    
    batch_data = {}
    for pcb in pcb_dict:
        if(not within_dates([pcb_dict[pcb]['date']], startdate, enddate)):
            continue 
        batch = find_batch(tlist, pcb)
        for chip in pcb_dict[pcb][CHIP_NAME]:
            rescreen_num = 1
            for pcb in chip_dict[chip][PCB_NAME]:
                if(pcb < batch):
                    rescreen_num += 1
            if(not batch in batch_data):
                batch_data[batch] = {key:0 for key in range(1, max_screens+1)}
            batch_data[batch][rescreen_num] += 1
    
    bars= {}
    xlabels = []
    keylist = list(batch_data.keys())
    keylist.sort()
    for batch in keylist:
        for nrescreen in range(1,max_screens+1):
            if(not nrescreen in bars):
                bars[nrescreen] = []
            n = batch_data[batch][nrescreen]
            bars[nrescreen].append(n)

        xlabels.append(batch)
    title_suffix =  'by batches from ' + startdate + ' to ' + enddate
    title = 'Rescreen number  ' + title_suffix
    dic_labels = [1, 2, 3, 4, 5]
    plot_barplot(bars, xlabels, dic_labels, title, savename)

def plot_passrate_by_wafer(chip_dict: dict, pcb_dict:dict, savename:str,
                       startdate:str = '00000000', enddate:str = '99999999'):
    
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
                'passed':0,
                'bypassed':0,
                'unknown':0
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

    title_suffix =  'by Wafer from ' + startdate + ' to ' + enddate
    title = 'Squid Chip Pass Rate ' + title_suffix
    bars_dict = {
        'All': bars_count,
        'Passed': bars_passed,
    }
    dic_labels = ['All', 'Passed']#, 'Bypassed', 'Fail', 'Unknown']
    plot_barplot(bars_dict, xlabels, dic_labels, title, savename)


def plot_failrate_by_wafer(chip_dict: dict, pcb_dict:dict, savename:str,
                       startdate:str = '00000000', enddate:str = '99999999'):
    
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
                'passed':0,
                'bypassed':0,
                'unknown':0
            }
        
        wafers[wafer]['count'] += 1
        # only count the chip if it passed within screening period
        passed = chip_dict[chip][PASSED] and max(dates) < enddate
        wafers[wafer]['passed'] += int(passed)
        check_bypassed = chip_dict[chip][SCREEN_FAIL][-1][SCREEN_FAIL]
        if('bypass' in str(check_bypassed).lower() and max(dates) < enddate):
            wafers[wafer]['bypassed'] += 1
        if(max(dates) > enddate):
            wafers[wafer]['unknown'] += 1
        


    
    bars_count = []
    bars_passed = []
    bars_bypassed = []
    bars_unknown = []
    bars_fail = []
    xlabels = []
    keylist = list(wafers.keys())
    keylist.sort()
    for wafer in keylist:
        if(not 'w' in wafer):
            continue
        xlabels.append(wafer )
        bars_count.append(wafers[wafer]['count'])
        bars_passed.append(wafers[wafer]['passed'])
        bars_bypassed.append(wafers[wafer]['bypassed'])
        bars_unknown.append(wafers[wafer]['unknown'])
        bars_fail.append(bars_count[-1]-bars_passed[-1]-bars_bypassed[-1]-bars_unknown[-1])

    title_suffix =  'by Wafer from ' + startdate + ' to ' + enddate
    title = 'Screening Reulsts ' + title_suffix
    bars_dict = {
        'All': bars_count,
        'Passed': bars_passed,
        'Warm Fail': bars_bypassed,
        'Unknown': bars_unknown,
        'Cold Fail': bars_fail
    }
    dic_labels = ['All', 'Passed', 'Warm Fail', 'Cold Fail', 'Unknown']
    plot_barplot(bars_dict, xlabels, dic_labels, title, savename)

def plot_passrate_by_rescreen(chip_dict, pcb_dict, savename,
                       startdate:str = '00000000', enddate:str = '99999999'):
    max_screen = 5

    count  = {key: 0 for key in range(1, max_screen+1)}
    passes = {key: 0 for key in range(1, max_screen+1)}
    bypass = {key: 0 for key in range(1, max_screen+1)}
    unknown = {key: 0 for key in range(1, max_screen+1)}
    for chip in chip_dict:
        pcbs = chip_dict[chip][PCB_NAME]
        dates = [p.split('_')[0] for p in pcbs]
        dates.sort()
        if(not within_dates(dates, startdate, enddate)):
            continue
        rescreen_count = 0

        for date in dates:
            rescreen_count += 1
            if(date > enddate or date < startdate):
                continue
            count[rescreen_count] += 1
            if(chip_dict[chip][PASSED] and date == max(dates)):
                passes[rescreen_count] += 1
            if(not date == max(dates)):
                unknown[rescreen_count] += 1
            check_bypassed = chip_dict[chip][SCREEN_FAIL][-1][SCREEN_FAIL]
            if('bypass' in str(check_bypassed).lower() and date == max(dates)):
                bypass[rescreen_count] += 1
                

    bars_count = []
    bars_passed = []
    bars_bypassed = []
    bars_unknown = []
    bars_fail = []
    xlabels = []
    for nscreen in range(1,max_screen+1):
        
        bars_count.append(count[nscreen])
        bars_passed.append(passes[nscreen])
        try:
            percent =passes[nscreen] /count[nscreen]
            pstr = str(int(percent*100)) 
        except ZeroDivisionError:
            pstr = 'NaN' 
        xlabels.append(str(nscreen) + ': ' + pstr+ '%')
        bars_bypassed.append(bypass[nscreen])
        bars_unknown.append(unknown[nscreen])
        bars_fail.append(bars_count[-1]-bars_passed[-1]-bars_bypassed[-1]-bars_unknown[-1])

    title_suffix =  'by Number of Times Screened from ' + startdate + ' to ' + enddate
    title = 'Screening Results ' + title_suffix
    bars_dict = {
        'All': bars_count,
        'Passed': bars_passed,
        #'Bypassed': bars_bypassed,
        #'Unknown': bars_unknown,
        #'Fail': bars_fail
    }
    dic_labels = ['All', 'Passed']#, 'Bypassed', 'Fail', 'Unknown']
    plot_barplot(bars_dict, xlabels, dic_labels, title, savename)
def plot_failrate_by_rescreen(chip_dict, pcb_dict, savename,
                       startdate:str = '00000000', enddate:str = '99999999'):
    max_screen = 5

    count  = {key: 0 for key in range(1, max_screen+1)}
    passes = {key: 0 for key in range(1, max_screen+1)}
    bypass = {key: 0 for key in range(1, max_screen+1)}
    unknown = {key: 0 for key in range(1, max_screen+1)}
    for chip in chip_dict:
        pcbs = chip_dict[chip][PCB_NAME]
        dates = [p.split('_')[0] for p in pcbs]
        dates.sort()
        if(not within_dates(dates, startdate, enddate)):
            continue
        rescreen_count = 0

        for date in dates:
            rescreen_count += 1
            if(date > enddate or date < startdate):
                continue
            count[rescreen_count] += 1
            if(chip_dict[chip][PASSED] and date == max(dates)):
                passes[rescreen_count] += 1
            if(not date == max(dates)):
                unknown[rescreen_count] += 1
            check_bypassed = chip_dict[chip][SCREEN_FAIL][-1][SCREEN_FAIL]
            if('bypass' in str(check_bypassed).lower() and date == max(dates)):
                bypass[rescreen_count] += 1
                

    bars_count = []
    bars_passed = []
    bars_bypassed = []
    bars_unknown = []
    bars_fail = []
    xlabels = []
    for nscreen in range(1,max_screen+1):
        xlabels.append(nscreen)
        bars_count.append(count[nscreen])
        bars_passed.append(passes[nscreen])
        bars_bypassed.append(bypass[nscreen])
        bars_unknown.append(unknown[nscreen])
        bars_fail.append(bars_count[-1]-bars_passed[-1]-bars_bypassed[-1]-bars_unknown[-1])

    title_suffix =  'by Number of Times Screened from ' + startdate + ' to ' + enddate
    title = 'Screening Results ' + title_suffix
    bars_dict = {
        'All': bars_count,
        'Passed': bars_passed,
        'Warm Fail': bars_bypassed,
        'Unknown': bars_unknown,
        'Cold Fail': bars_fail
    }
    dic_labels = ['All', 'Passed', 'Warm Fail', 'Cold Fail', 'Unknown']
    plot_barplot(bars_dict, xlabels, dic_labels, title, savename)


def plot_rescreen_by_wafer(chip_dict, pcb_dict, savename,
                       startdate:str = '00000000', enddate:str = '99999999'):
  
    wafers = {}
    max_screens = 5

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
            wafers[wafer] = {key: 0 for key in range(1, max_screens+1)}
        wafers[wafer][rescreen_num] += 1
    
    bars= {}
    xlabels = []
    keylist = list(wafers.keys())
    keylist.sort()
    for wafer in keylist:
        if(not 'w' in wafer):
            continue
        for nrescreen in range(1,max_screens+1):
            if(not nrescreen in bars):
                bars[nrescreen] = []
            bars[nrescreen].append(wafers[wafer][nrescreen])

        xlabels.append(wafer)
    title_suffix =  'by wafer from ' + startdate + ' to ' + enddate
    title = 'Rescreen number  ' + title_suffix
    dic_labels = [1,2,3,4,5]
    plot_barplot(bars, xlabels, dic_labels, title, savename)

def timestamps():
    startstart = '20190401'
    w39 = '20191101'
    w41 = '20201001'
    nickstart = '20210520'
    w44 = '20210901'
    w45 = '20211023'
    kuostart = '20220401'
    w47 = '20220525'
    r1 = '20220701'
    r2 = '20220720'
    r3 = '20220801'
    w48 = '20220820'
    r4 = '20221101'
    endend = '20221131'

    tlist = [
        startstart,
        w39,
        w41,
        nickstart,
        w44,
        w45,
        kuostart,
        w47,
        r1,
        r2,
        r3,
        w48,
        r4,
        endend
    ]
    return tlist

def plot_data(c, p):
    tlist = timestamps()
    savedir2 = 'rescreen/'
    savedir1 = 'passrates/'
    savedir3 = 'failrates/'
    filestem1 = 'bywafer_'
    filestem2 = 'bynscreen_'
    filestem3 = 'bybatch_'

    for end in range(0, len(tlist)):
        print('Plotting for end time: ' + tlist[end])
        for start in range(end):
            print('startime: ' + str(tlist[start]))
            file_suf = tlist[start] + '_' + tlist[end]
            filename11 = savedir1 + filestem1 + file_suf + '.png'
            filename12 = savedir1 + filestem2 + file_suf + '.png'
            filename13 = savedir1 + filestem3 + file_suf + '.png'
            filename21 = savedir2 + filestem1 + file_suf + '.png'
            filename23 = savedir2 + filestem3 + file_suf + '.png'
            filename31 = savedir3 + filestem1 + file_suf + '.png'
            filename32 = savedir3 + filestem2 + file_suf + '.png'
            filename33 = savedir3 + filestem3 + file_suf + '.png'
            plot_failrate_by_wafer(c,p, filename31, startdate = tlist[start], enddate = tlist[end])
            plot_passrate_by_wafer(c,p, filename11, startdate = tlist[start], enddate = tlist[end])
            plot_rescreen_by_wafer(c,p, filename21, startdate = tlist[start], enddate = tlist[end])
            plot_failrate_by_rescreen(c,p, filename32, startdate = tlist[start], enddate = tlist[end])
            plot_passrate_by_rescreen(c,p, filename12, startdate = tlist[start], enddate = tlist[end])
            plot_passrate_by_screenbatch(c,p, tlist, filename13, startdate = tlist[start], enddate = tlist[end])
            plot_rescreen_by_screenbatch(c,p, tlist, filename23, startdate = tlist[start], enddate = tlist[end])
            plot_failrate_by_screenbatch(c,p, tlist, filename33, startdate = tlist[start], enddate = tlist[end])

def main():
    c,p = read_squid_data('../cold_screening.tsv')
    plot_data(c, p)


    

if __name__ == '__main__':
    main()