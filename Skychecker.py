#!/usr/bin/python3


import os,sys,subprocess,datetime,time,getpass,syslog,signal


class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Timeout.")


def Get_Output(skyreader):
   try:
       output = subprocess.check_output([skyreader, "-p", "-D"], text=True)
   except Exception as e:
       print("Error:%s"%str(e))
       output = None
   return(output)



def Gather_Responses(output):

    res_lst = []
    to_save = False
    for line in output.splitlines():
#       print("line:",line)
       if "START DBG" in line or "END DBG" in line:
           to_save = not to_save
           continue
       if to_save:
#           print("\nline to save:%s\n"%line)
           res_lst.append(line.strip())

    if res_lst:
       return(res_lst)
    else:
       return(None) 


def Parse_Responses(raw_lines):

    parsed_lst = []
    
    for line in raw_lines:

       hex_list = []

       if ":" in line and " " in line:
           parsed = line.split(":")[1]
           hex_list = [hex2b for hex2b in parsed.split(" ") if len(hex2b) >0 and "." not in hex2b]
           hex_list = " ".join(hex_list[:16])
           parsed_lst.append(hex_list)

#    for p in parsed_lst:
#       print("parsed:",p)
    return(parsed_lst)


def Skychecker():

    output = Get_Output(Path_SkyReader)
    if output:
       raw_res = Gather_Responses(output)
       if raw_res:

          parsed_res = Parse_Responses(raw_res)
          return(parsed_res)
       else:
           print("-No response from Skyreader.")
           sys.exit()
    else:
        print("-No output from Skyreader.")
        sys.exit()

def Dbg_Output():

    Sky_Responses_no_objects = []

    input("-Remove any object on the Portal and type enter.")

    while len(Sky_Responses_no_objects) < 10:

        time.sleep(1)
        print("-Reading output from Skyreader: %s/10"%len(Sky_Responses_no_objects),end="\r")
        responses= Skychecker()
        if responses:
           Sky_Responses_no_objects.append(responses)

    print()
    for n,block in enumerate(Sky_Responses_no_objects):
         print("\n-Block number:%s\n"%n)
         dummy = Count_Match(block)
         dummy = Check_Line(block,-6,"41 01 ff 77 00 00 00 00 00 00 00 00 00 00 00 00")
         for line in block:
             print(line)


def Count_Match(results):

   global Err_Cnt

   cnt_lst = [results.count(item) for item in Res_to_match]

   if DBG:
       print("cnt_lst:%s err_cnt:%s"%(cnt_lst,Err_Cnt))

   if any(cnt > Threshold for cnt in cnt_lst):
       Err_Cnt = 0
       return False
   else:
       if Err_Cnt > Max_Err:
          return True
       else:
          Err_Cnt += 1
          return False


def Check_Line(lst_to_check,index,str_to_match):

   global Err_Cnt

   try:
     if lst_to_check[index] != str_to_match:
        Err_Cnt = 0
        if DBG:
            print("-str_to_match not found at lst_to_check[%s]:%s"%(index,lst_to_check[index]))
        return False
     else:
       if DBG:
           print("-Err_cnt:%s Found str_to_match:%s at lst_to_check[%s]"%(Err_Cnt,str_to_match,index))
       if Err_Cnt > Max_Err:
          return True
       else:
          Err_Cnt += 1
          return False
   except Exception as e:
       if DBG:
           print("-Error:%s"%str(e))
       return False

def Ring_It():
   global Err_Cnt
   global Pass_Check

   Pass_Check = False
   Err_pass = 0

   subprocess.Popen(["aplay","-q","%s"%Path_sonar_wav])
#   os.system("aplay -q %s"%Path_sonar_wav)

   timestamp = str(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
   sys_msg = "==Portal has lost track of object at %s =="%timestamp

   syslog.syslog(syslog.LOG_INFO,sys_msg)

   signal.signal(signal.SIGALRM, timeout_handler)
   signal.alarm(60)
   try:
        while True:
            usr_input = getpass.getpass(prompt="Enter correct passphrase within 1 minute:")
            if usr_input == passphrase:
                os.system("killall aplay")
                Err_Cnt = 0
                Pass_Check = True
                return(Main_Loop())
            else:
                Err_pass += 1

                if Err_pass > 2:
                   sys_msg = "!!!!%s Wrong Passphrases at %s !!!!"%(Err_pass,timestamp)
                   syslog.syslog(syslog.LOG_ERR,sys_msg)

                   subprocess.Popen(["aplay","-q","%s"%Path_alarm_wav])
#                   os.system("aplay -q %s"%Path_alarm_wav)
                   return(Main_Loop(True))
                else:
                   sys_msg = "==!!Wrong Passphrase at %s !!=="%timestamp 
                   syslog.syslog(syslog.LOG_WARNING,sys_msg)
   except TimeoutError as e:
       if not Pass_Check:
           print("Error:%s"%str(e))
           timestamp = str(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
           sys_msg = "!!!!User has failed to enter correct password within a minute at %s !!!!"%(timestamp)
           syslog.syslog(syslog.LOG_ERR,sys_msg)
           subprocess.Popen(["aplay","-q",Path_alarm_wav])
    #       os.system("aplay -q %s"%Path_alarm_wav)
       return(Main_Loop(True))



def Main_Loop(skip_input=False):

    loop_cnt = 0
    if not skip_input:
        input("-Type enter to start monitoring.")

    while True:
         skyblock = Skychecker()

         if DBG:
             print("\n\n-Block Number:%s len:%s\n"%(loop_cnt,len(skyblock)))
             for n,line in enumerate(skyblock):
                 print("-%s:\t%s"%(n,line))

#         if Count_Match(skyblock):
#              return(Ring_It())

         if Check_Line(skyblock,-6,"41 01 ff 77 00 00 00 00 00 00 00 00 00 00 00 00"):
               return(Ring_It())

         loop_cnt += 1
         time.sleep(SLEEP)

####

if __name__ == "__main__":


    Err_Cnt = 0
    Max_Err = 4
    Threshold = 3
    SLEEP = 2
    Pass_Check = False

    DBG = False
    DBG_OUTPUT = False

    Res_to_match = ("52 02 0a 03 02 00 00 00 00 00 00 00 00 00 00 00","41 01 ff 77 00 00 00 00 00 00 00 00 00 00 00 00")
    passphrase = "alice"


    Path_SkyReader = "./skyrdr"
    Path_sonar_wav = "./sonar.wav"
    Path_alarm_wav = "./alarm.wav"

    print("-Path_SkyReader:",Path_SkyReader)
    

###
    if DBG_OUTPUT == True:
        Dbg_Output()
        sys.exit()
##
    Main_Loop()
##
#    output =  Skychecker()
#    for n,o in ouput:print("\nblock nbr:%s\n%s"%(n,o))
##
