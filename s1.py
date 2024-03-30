from iqoptionapi.stable_api import IQ_Option
from parameters import asset1,limit,stoploss,hour,minute,exptime,amount,acc_type,user,passw
from datetime import datetime as dt
import numpy as np
import colorama
from colorama import Fore, Back, init
import asyncio
import talib
import threading
import time as t
import sys
import csv


init(autoreset=True)

#USER ACCOUNT CREDENTIALS AND LOG IN 
my_user = user  #YOUR IQOPTION USERNAME
my_pass = passw #YOUR IQOTION PASSWORD

# Global variables for trading signals
size = 60
period = 14
bollinger_signal = 0
macd_above_signal = False
ma_above_price = False
my_close = []
my_high = []
my_low = []
my_volume = []

#parameters
money = amount
goal = asset1 
expirations_mode = exptime
lmt = limit
stpls = stoploss
end_time = dt.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

line = "#" * 80


Iq = IQ_Option(my_user, my_pass)
iqch1, iqch2 = Iq.connect()
if iqch1:
    print(Fore.GREEN + "Login successful.")
else:
    print(Fore.RED + "Login Failed.")
    sys.exit()


Iq.change_balance(acc_type)
print(Fore.GREEN + "Trading Started, Please Wait...")

print(Back.MAGENTA + Fore.BLACK + "[+]asset:",goal)


balance = Iq.get_balance()
print(Back.MAGENTA + Fore.BLACK + "[+] Amount Balance:", balance)
print (line)



def check_limits(balance):
    limit = float(lmt)
    stop_loss = float(stpls)
    
    if balance >= limit:
        print("Limit reached. Exiting trade.")
        sys.exit()
    elif balance <= stop_loss:
        print("Stop loss reached. Exiting trade.")
        sys.exit()


#GET OHLC DATA FROM IQOPTIONs
Iq.start_candles_stream(goal,size,period)
cc=Iq.get_realtime_candles(goal,size)

#STORE OPEN AND CLOSE VALUES
my_open = []
my_close =[]

#WHEN TO PLACE BET BEFORE EXPIRY TIME (TIME IN SECONDS)
place_at  = 0
def get_purchase_time():
    remaning_time=Iq.get_remaning(expirations_mode)   
    purchase_time=remaning_time
    return purchase_time

def get_expiration_time():
    exp=Iq.get_server_timestamp()
    time_to_buy=(exp % size)
    return int(time_to_buy)

#THREAD TO RUN TIMER SIMULTANEOUSLY
def expiration_thread():
    global place_at
    while True:
        x=get_expiration_time()
        t.sleep(1)
        if x == place_at:
            place_option(Iq, my_close, my_high, my_low, my_volume, size, period,balance)
threading.Thread(target=expiration_thread).start()

#SET VALUES TO PLACE BET(S)
def set_values( my_close, my_high, my_low, my_volume, size):
    cc = Iq.get_realtime_candles(goal, size)
    for k in list(cc.keys()):
        close = cc[k]['close']
        my_close.append(close)
        low = cc[k]['min']
        my_low.append(low)
        volume = cc[k]['volume']
        my_volume.append(volume)
        high = cc[k]['max']
        my_high.append(high)

with open('asset1.csv', mode='a', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Trade Time', 'bollinger bands','MACD','MA','overall signal', 'Result'])



#BET PLACEMENT CONDITIONS AND BET PLACEMENT
def place_option(Iq, my_close, my_high, my_low, my_volume, size, period,balance):  
    
    global bollinger_signal
    global macd_above_signal
    global ma_above_price
    
    last_Trade = "None"
    check_limits(balance)
    
    set_values(my_close, my_high, my_low, my_volume, size)

    while True:

        current_time = dt.now()

        if current_time >= end_time:
            # Your trading bot logic goes here
            print(f"Trading bot shutdowned at  {current_time}")
            sys.exit()


        set_values(my_close, my_high, my_low, my_volume, size)
        if len(my_close) < period:
            t.sleep(5)
            continue

        trade_time = t.strftime('%Y-%m-%d %H:%M:%S')
        print(Back.MAGENTA + Fore.BLACK +"Date & Time :",trade_time)
        

        upper, middle, lower = talib.BBANDS(np.array(my_close), timeperiod=period)
        upper_val = upper[-1]
        middle_val = middle[-1]
        lower_val = lower[-1]

        macd, macd_signal, _ = talib.MACD(np.array(my_close), fastperiod=12, slowperiod=26, signalperiod=9)
        macd_val = macd[-1]
        macd_signal = macd_signal[-1]

        ma = talib.SMA(np.array(my_close), timeperiod=period)
        ma_val = ma[-1]

        
        print(line)
        print("\t\t\t\t", goal, "\t\t\t")
        print(line)

        # Bollinger Bands
        put = []
        call = []

        print(Back.CYAN+Fore.BLACK+"BOLLINGER BAND:")
        if my_close[-1] > upper[-1]:
            bollinger_signal = -1
        elif my_close[-1] < lower[-1]:
            bollinger_signal = 1
        else:
            bollinger_signal = 0

        if bollinger_signal == -1:
            print("Price above upper Bollinger Band. Placing ", Fore.RED + "'PUT⇩'", " Option.")
            bb = "put"
            put.append(1)
        elif bollinger_signal == 1:
            print("Price below lower Bollinger Band. Placing ", Fore.GREEN + "'CALL⇑'", " Option.")
            bb = "call"
            call.append(1)
        else:
            print("No Clear Trading Signal (Bollinger Bands)😕.")
            bb = "neutral"
        # MACD
        print(Back.CYAN + Fore.BLACK + "MACD:")

        if macd_val > macd_signal and not macd_above_signal:
            print("MACD crossed above the signal line. Placing ", Fore.RED + "'PUT⇩'", " Option.")
            macd_above_signal = True
            macd = "put"
            put.append(1)
        elif macd_val < macd_signal and macd_above_signal:
            print("MACD crossed below the signal line. Placing ", Fore.GREEN + "'CALL⇑'", " Option.")
            macd_above_signal = False
            macd = "call"
            call.append(1)
        else:
            print("No Trading Signal (MACD)😕.")
            macd="neutral"

        # Moving Average
        print(Back.CYAN + Fore.BLACK + "MA:")

        if my_close[-1] > ma_val and not ma_above_price:
            print("Price crossed above the Moving Average. Placing ", Fore.RED + "'PUT⇩'", " Option.")
            ma_above_price = True
            ma = "put"
            put.append(1)
        elif my_close[-1] < ma_val and ma_above_price:
            print("Price crossed below the Moving Average. Placing ", Fore.GREEN + "'CALL⇑'", " Option.")
            ma_above_price = False
            ma = "call"
            call.append(1)
        else:
            print("No Trading Signal (Moving Average)😕.")
            ma = "neutral"

        print(line)

        call_signal = len(call)
        put_signal = len(put)

        print("total call=", call_signal, "\ttotal put=", put_signal)

        
        
            # Add more indicators as needed
        
        
        # Calculate the average signal
        if call_signal < put_signal:
            if put_signal == 3:
                overall_signal = Fore.RED + "STRONG PUT⇩"
                print(Fore.BLUE + "Overall Signal:", overall_signal)
                check,id=Iq.buy(money,goal,"put",expirations_mode)
                if check:
                    print(Fore.GREEN + "PUT Option Placed Successfully.")
                    result = Iq.check_win_v3(id)
                    if result < 0 :
                        last_Trade ="loss"
                        
                    elif result == 0:
                        last_Trade ="draw"
                        
                    else:
                        last_Trade="profit"
                        

                else:
                    print(Fore.RED + "PUT option Failed.")

                trade_data = f"{trade_time},{bb},{macd},{ma},{overall_signal}, {last_Trade}"
                with open('asset1.csv', mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([trade_time, bb, macd, ma,overall_signal, last_Trade])

                print(line)
                
            elif put_signal == 2:
                overall_signal = Fore.LIGHTRED_EX + "PUT⇩"
                print(Fore.BLUE + "Overall Signal:", overall_signal)
                check,id=Iq.buy(money,goal,"put",expirations_mode)
                if check:
                    print(Fore.GREEN + "PUT Option Placed Successfully.")
                    result = Iq.check_win_v3(id)
                    if result < 0 :
                        last_Trade ="loss"
                        
                    elif result == 0:
                        last_Trade ="draw"
                        
                    else:
                        last_Trade="profit"
                        


                else:
                    print(Fore.RED + "PUT option Failed.")

                trade_data = f"{trade_time},{bb},{macd},{ma},{overall_signal}, {last_Trade}"
                with open('asset1.csv', mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([trade_time, bb, macd, ma,overall_signal, last_Trade])

                print(line)
                
            else:
                overall_signal = "NEUTRAL(PUT⇩😕)"
                print(Fore.BLUE + "Overall Signal:", overall_signal)

        elif call_signal > put_signal:
            if call_signal == 3:
                overall_signal = Fore.GREEN + "STRONG CALL⇑"
                print(Fore.BLUE + "Overall Signal:", overall_signal)
                check,id=Iq.buy(money,goal,"call",expirations_mode)
                if check:
                    print(Fore.GREEN + "CALL Option Placed Successfully.")
                    result = Iq.check_win_v3(id)
                    if result < 0 :
                        last_Trade ="loss"
                        
                    elif result == 0:
                        last_Trade ="draw"
                        
                    else:
                        last_Trade="profit"
                        


                else:
                    print(Fore.RED + "CALL option Failed.")

                trade_data = f"{trade_time},{bb},{macd},{ma},{overall_signal}, {last_Trade}"
                with open('asset1.csv', mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([trade_time, bb, macd, ma,overall_signal, last_Trade])

                print(line)
                
            elif call_signal == 2:
                overall_signal = Fore.LIGHTGREEN_EX + "CALL⇑"
                print(Fore.BLUE + "Overall Signal:", overall_signal)
                check,id=Iq.buy(money,goal,"call",expirations_mode)
                if check:
                    print(Fore.GREEN + "CALL Option Placed Successfully.")
                    result = Iq.check_win_v3(id)
                    if result < 0 :
                        last_Trade ="loss"
                        
                    elif result == 0:
                        last_Trade ="draw"
                        
                    else:
                        last_Trade="profit"

                
                        


                else:
                    print(Fore.RED + "CALL option Failed.")

                trade_data = f"{trade_time},{bb},{macd},{ma},{overall_signal}, {last_Trade}"
                with open('asset1.csv', mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([trade_time, bb, macd, ma,overall_signal, last_Trade])
                
                print(line)
                
            else:
                overall_signal = "NEUTRAL(CALL⇑😕)"
                print(Fore.BLUE + "Overall Signal:", overall_signal)

        else:
            overall_signal = "NEUTRAL(NO SIGNALS😕)"
            print(Fore.BLUE + "Overall Signal:", overall_signal)

        print(Back.MAGENTA + Fore.BLACK + f"Last Trade Result: {last_Trade}")

        
        

        last_Trade = "None"

        print(line)

        t.sleep(60)

            
#--END
