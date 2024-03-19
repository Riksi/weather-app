import subprocess
import pandas as pd

usaf =  749502 #747187
wban =  99999 #3104
yy = 1944 #2016

sd = yy * 10000 + 101
ed = yy * 10000 + 1231
data_inpt = f'data-{usaf}-{wban}-{yy}.csv'
print('Saving data to', data_inpt)

#stid = '%06i-%05i'%(usaf, wban)
stid = '%s-%05i'%(str(usaf).zfill(6), wban)
command = './data_from_station_yyyymmddhhmm.py -n {stid} -i {stid} -f YYYY MM DD HR MN TEMP DEWP SPD DIR -s {sd} -e {ed} | grep -v -e "*" -e "^\\s*$" >  {data_inpt}'
command = command.format(stid=stid, sd=sd, ed=ed, data_inpt=data_inpt)
## Run this command to get the data and wait for it to finish
subprocess.run(command, shell=True)

print(data_inpt, len(pd.read_csv(data_inpt)))