import io, time, json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib
import re
import os
import numpy as np
import ftplib
from ftplib import FTP
import timeit

'''
EPA extraction procedure
1. Download data from ftp server
2. Correct column names and export 1 file per year
3. Upscale data from hourly to monthly and by ORISPL code - export 1 file for
all years

EIA data extraction procedure
1.
'''

def main():
    try:
        os.mkdir('EPA_downloads')
    except:
        pass
    try:
        path = os.path.join('EPA_downloads', 'name_time 2015-2016.csv')
        already_downloaded = pd.read_csv(path, parse_dates=['last updated'])
    except:
        already_downloaded = pd.DataFrame(columns=['file name', 'last updated'])

    # Timestamp
    start_time = timeit.default_timer()
    name_time_list = []
    # Open ftp connection and navigate to the correct folder
    print('Opening ftp connection')
    ftp = FTP('ftp.epa.gov')
    ftp.login()
    ftp.cwd('/dmdnload/emissions/hourly/monthly')

    for year in [2015, 2016, 2017]:
        print(year)

        year_str = str(year)
        print('Change directory to', year_str)
        try:
            ftp.cwd(year_str)
        except ftplib.all_errors as e:
            print(e)
            break

        # Use ftplib to get the list of filenames
        print('Fetch filenames')
        fnames = ftp.nlst()

        # Create new directory path if it doesn't exist
        new_path = os.path.join('EPA downloads', year_str)
        try:
            os.mkdir(new_path)
        except:
            pass


        # Look for files without _HLD in the name
        name_list = []
        time_list = []
        print('Find filenames without _HLD and time last updated')
        for name in fnames:
            if '_HLD' not in name:
                try:
                    # The ftp command "MDTM" asks what time a file was last modified
                    # It returns a code and the date/time
                    # If the file name isn't already downloaded, or the time isn't the same
                    tm = pd.to_datetime(ftp.sendcmd('MDTM '+ name).split()[-1])
                    if name not in already_downloaded['file name'].values:

                        time_list.append(tm)
                        name_list.append(name)
                    elif already_downloaded.loc[already_downloaded['file name']==name, 'last updated'].values[0] != tm:
                        tm = ftp.sendcmd('MDTM '+ name)
                        time_list.append(pd.to_datetime(tm.split()[-1]))
                        name_list.append(name)
                except ftplib.all_errors as e:
                    print(e)
                    # If ftp.sendcmd didn't work, assume the connection was lost
                    ftp = FTP('ftp.epa.gov')
                    ftp.login()
                    ftp.cwd('/dmdnload/emissions/hourly/monthly')
                    ftp.cwd(year_str)
                    tm = ftp.sendcmd('MDTM '+ name)
                    time_list.append(pd.to_datetime(tm.split()[-1]))
                    name_list.append(name)


        # Store all filenames and update times
        print('Store names and update times')
        name_time_list.extend(zip(name_list, time_list))

        # Download and store data
        print('Downloading data')
        for name in name_list:
            try:
                with open(os.path.join('EPA downloads', year_str, name), 'wb') as f:
                    ftp.retrbinary('RETR %s' % name, f.write)
            except ftplib.all_errors as e:
                print(e)
                try:
                    ftp.quit()
                except ftplib.all_errors as e:
                    print(e)
                    pass
                ftp = FTP('ftp.epa.gov')
                ftp.login()
                ftp.cwd('/dmdnload/emissions/hourly/monthly')
                ftp.cwd(year_str)
                with open(os.path.join('EPA downloads', year_str, name), 'wb') as f:
                    ftp.retrbinary('RETR %s' % name, f.write)

        print('Download finished')
        print(round((timeit.default_timer() - start_time)/60.0,2), 'min so far')

        # Go back up a level on the ftp server
        ftp.cwd('..')

    # Timestamp
    elapsed = round((timeit.default_timer() - start_time)/60.0,2)
    print('Data download completed in %s mins' %(elapsed))

if __name__ == '__main__':
    main()
