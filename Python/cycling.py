'''
Created on 2012-07-06

A short script to write namelists for cycling/resubmitting WRF runs. The script reads an environment 
argument that indicates the current step, reads the parameters for the next step, writes the new WPS 
and WRF namelists with the new parameters, based on templates, and returns the new step name. 

@author: Andre R. Erler
'''

# imports
import os # directory operations
import fileinput # reading and writing config files
import shutil # file operations
import sys # writing to stdout
# my modules
from namelist import time

# setup
#if os.environ.has_key('STEP'):
#  laststep = os.environ['STEP'] # name of current (i.e. last) step
# pass current/last step name as argument
if len(sys.argv) > 1:
  laststep = sys.argv[1]
else: laststep = ''
if os.environ.has_key('STEPFILE'):
  stepfile = os.environ['STEPFILE'] # name of file with step listing
else: stepfile = 'stepfile' # default name
IniDir = os.environ['INIDIR'] # where the step file is found
nmlstwps = 'namelist.wps' # WPS namelist file
nmlstwrf = 'namelist.input' # WRF namelist file


# start execution
if __name__ == '__main__':


  # read step file
  file = fileinput.FileInput([IniDir + '/' + stepfile], mode='r')
  nextline = -1 # flag for last step not found 
  if laststep:
    # either loop over lines
    for line in file:
      if (nextline == -1) and (laststep in line):
        # scan for current/last step    
        nextline = file.filelineno() + 1
      elif nextline == file.filelineno():
        # read next line
        linesplit = line.split()
    # check against end of file
    if nextline > file.filelineno():
      nextline = 0 # flag for last step (end of file)
  else:
    # or read first line
    nextline = 1
    linesplit = file[0].split()
        
  # set up next step    
  if nextline <= 0:
    # no next step
    if nextline == 0:
      # reached end of file
      sys.stdout.write('')
      sys.exit(0)
    elif nextline == -1:
      # last/current step not found
      sys.exit(laststep+' not found in '+stepfile)
    else:
      # unknown error
      sys.exit(127)
  else:
    # extract information
    nextstep = linesplit[0] # next step name
    startdatestr = linesplit[1] # next start date
    startdate = time.splitDateWRF(startdatestr[1:-1])
    enddatestr = linesplit[2] # next end date
    enddate = time.splitDateWRF(enddatestr[1:-1])
    # create next step folder
    StepFolder = IniDir + '/' + nextstep + '/'
    if os.path.isdir(StepFolder):            
      shutil.rmtree(StepFolder) # remove directory if already there        
    os.mkdir(StepFolder) # create new step folder 
    # copy namelist templates  
    shutil.copy(IniDir+'/'+nmlstwps, StepFolder)
    shutil.copy(IniDir+'/'+nmlstwrf, StepFolder)
  
    # print next step name to stdout
    sys.stdout.write(nextstep)
    
    # determine number of domains
    file = fileinput.FileInput([StepFolder+nmlstwps], mode='r')    
    for line in file: # loop over entries/lines
      if 'max_dom' in line: # search for relevant entries
        maxdom = int(line.split()[2].strip(','))
        break; fileinput.close()    

    # WPS namelist
    # construct date strings
    startstr = ' start_date = '; endstr = ' end_date   = '
    for i in xrange(maxdom):
      startstr = startstr + startdatestr + ','
      endstr = endstr + enddatestr + ','
    startstr = startstr + '\n'; endstr = endstr + '\n'
    # write namelists
    file = fileinput.FileInput([StepFolder+nmlstwps], inplace=True)
    lstart = False; lend = False    
    for line in file: # loop over entries/lines
      # rewrite date-related entries
      if 'start_date' in line:
        if not lstart:
          # write start date and time
          sys.stdout.write(startstr)
          lstart = True # else omit line            
      elif 'end_date' in line:
        if not lend:
          # write end date and time
          sys.stdout.write(endstr)
          lend = True # else omit line
      else:
        # write original file contents
        sys.stdout.write(line)
    # close file
    fileinput.close()
    
    # WRF namelist
    datecats = ('year', 'month', 'day', 'hour')
    # construct date strings
    ldc = len(datecats); startcats = ['',]*ldc; endcats = ['',]*ldc
    for i in xrange(ldc):
      # startcat, endcat, datecat, start, end 
      startcat = ' start_'+datecats[i]+' ='; endcat = ' end_'+datecats[i]+'   ='
      for j in xrange(maxdom):
        startcat = startcat + ' ' + str(startdate[i]) + ','
        endcat = endcat + ' ' + str(enddate[i]) + ','
      startcats[i] = startcat + '\n'; endcats[i] = endcat + '\n'
    # write namelist
    file = fileinput.FileInput([StepFolder+nmlstwrf], inplace=True)
    for line in file: # loop over entries/lines
      ldate = False
      # rewrite date-related entries
      for startcat, endcat, datecat in zip(startcats, endcats, datecats):
        if datecat in line:             
          if 'start_' in line:
            # write start date and time
            sys.stdout.write(startcat)    
            ldate = True        
          elif 'end_' in line:
            # write end date and time
            sys.stdout.write(endcat)
            ldate = True
      # write original file contents
      if not ldate:
        sys.stdout.write(line)
    # close file
    fileinput.close() 