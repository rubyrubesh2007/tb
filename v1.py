from iqoptionapi.stable_api import IQ_Option
import numpy as np
import colorama  
from colorama import Fore, Back, init
import asyncio
import talib
import sys

init(autoreset=True)

my_user = "######"  # YOUR IQOPTION USERNAME
my_pass = "######"  # YOUR IQOPTION PASSWORD

# Global variables for trading signals
rsi_above_70 = False
rsi_below_30 = False
bollinger_signal = 0
macd_above_signal = False
stoch_above_90 = False
stoch_below_10 = False  # Initialize stoch_below_10
ma_above_price = False
money = 1  # Initial amount for Option
goal = "EURUSD"  # Initial target instrument

async def login():                                               #login def
    Iq = IQ_Option(my_user, my_pass)
    iqch1, iqch2 = Iq.connect()
    if iqch1:
        print(Fore.GREEN+"Login successful.")
    else:
        print(Fore.RED+"Login Failed.")
        sys.exit()
    return Iq

async def set_balance_type(Iq):                                  #balance type
    print(Back.MAGENTA + Fore.BLACK+"[+] ACCOUNT TYPE: ")
    print("1.REAL \n2.PRACTICE")
    acc_type = input("ENTER A NUMBER : ")
    if acc_type == '1':
        Iq.change_balance("REAL")
    elif acc_type == '2':
        Iq.change_balance("PRACTICE")
    print(Fore.GREEN+"Trading Started, Please Wait...")

async def get_realtime_candles(Iq, size, period):                #getting realtime candles data
    while True:
        Iq.start_candles_stream(goal, size, period)
        await asyncio.sleep(5)

async def set_values(Iq, my_close, size): #setting values
    cc = Iq.get_realtime_candles(goal, size)
    for k in list(cc.keys()):
        close = cc[k]['close']
        my_close.append(close)

async def countdown(time_sec):
    while time_sec:
        mins, sec = divmod(time_sec, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, sec)
        print("Time Remaining for Next Signal: " + timeformat, end='\r')
        await asyncio.sleep(1)
        time_sec -= 1

async def apply_trading_conditions(Iq, my_close, size, period):   #indicators condition and placing condition
    global rsi_above_70
    global rsi_below_30
    global bollinger_signal
    global macd_above_signal
    global stoch_above_90
    global stoch_below_10
    global ma_above_price

    while True:
        await set_values(Iq, my_close, size)
        if len(my_close) < period:
            await asyncio.sleep(5)
            continue

        rsi_values = talib.RSI(np.array(my_close), timeperiod=period)
        rsi_val = rsi_values[-1]

        upper, middle, lower = talib.BBANDS(np.array(my_close), timeperiod=period)
        upper_val = upper[-1]
        middle_val = middle[-1]
        lower_val = lower[-1]

        macd, macd_signal, _ = talib.MACD(np.array(my_close), fastperiod=12, slowperiod=26, signalperiod=9)
        macd_val = macd[-1]
        macd_signal = macd_signal[-1]

        slowk, slowd = talib.STOCH(np.array(my_close), np.array(my_close), np.array(my_close), fastk_period=14, slowk_period=3, slowd_period=3)
        stoch_val = slowk[-1]

        ma = talib.SMA(np.array(my_close), timeperiod=period)
        ma_val = ma[-1]

        line="#"*80
        print(line)
        print("\t\t\t\t",goal,"\t\t\t")
        print(line)

        put = []
        call = []

        print(Back.CYAN+Fore.BLACK+"RSI:")

        if rsi_val > 70 and not rsi_above_70:
            print("RSI touched above 70.",Fore.BLUE+ "RSI VAL:", rsi_val)
            rsi_above_70 = True

        if rsi_above_70 and rsi_val <70 :
            print("RSI moving below 70. Placing ",Fore.RED+"'PUT⇩'"," Option.",Fore.BLUE+ "RSI VAL:", rsi_val)
            rsi_above_70 = False
            put.append(1)

        if rsi_val < 30 and not rsi_below_30:
            print("RSI touched below 30.", Fore.BLUE+"RSI VAL:", rsi_val)
            rsi_below_30 = True

        if rsi_below_30 and rsi_val > 30 :
            print("RSI moving above 30. Placing ",Fore.GREEN+"'CALL⇑'"," Option.", Fore.BLUE+"RSI VAL:", rsi_val)
            rsi_below_30 = False
            call.append(1)

        if not rsi_above_70 and not rsi_below_30:
            print("No Trading Signal (RSI)😕.",Fore.BLUE+ "RSI VAL:", rsi_val)

        print(line)
        print(Back.CYAN+Fore.BLACK+"BOLLINGER BAND:")

        if my_close[-1] > upper[-1]:
            bollinger_signal = -1  # Bearish signal (price above upper band)
        elif my_close[-1] < lower[-1]:
            bollinger_signal = 1  # Bullish signal (price below lower band)
        else:
            bollinger_signal = 0  # No clear trading signal

        if bollinger_signal == -1:
            print("Price above upper Bollinger Band. Placing ",Fore.RED+"'PUT⇩'"," Option.", Fore.BLUE+"\nUp:", upper_val,Fore.BLUE+ "mid:", middle_val,Fore.BLUE+ "low:", lower_val)
            put.append(1)
        elif bollinger_signal == 1:
            print("Price below lower Bollinger Band. Placing ",Fore.GREEN+"'CALL⇑'"," Option.",Fore.BLUE+ "\nUp:", upper_val, Fore.BLUE+"mid:", middle_val, Fore.BLUE+"low:", lower_val)
            call.append(1)        
        else:
            print("No Clear Trading Signal (Bollinger Bands)😕.", Fore.BLUE+"\nUp:", upper_val, Fore.BLUE+"mid:", middle_val, Fore.BLUE+"low:", lower_val)
        
        print(line)
        print(Back.CYAN+Fore.BLACK+"MACD:")

        if macd_val > macd_signal and not macd_above_signal:
            print("MACD crossed above the signal line. Placing ",Fore.RED+"'PUT⇩'"," Option.",Fore.BLUE+ "macd val=", macd_val)
            macd_above_signal = True
            put.append(1)
        elif macd_val < macd_signal and macd_above_signal:
            print("MACD crossed below the signal line. Placing ",Fore.GREEN+"'CALL⇑'"," Option.", Fore.BLUE+"macd val=", macd_val)
            macd_above_signal = False
            call.append(1)

        else:
            print("No Trading Signal (MACD)😕.",Fore.BLUE+ "macd val=", macd_val)

        print(line)
        print(Back.CYAN+Fore.BLACK+"STOCHASTIC OSCILLATOR:")

        if stoch_val > 90 and not stoch_above_90:
            print("Stochastic Oscillator touched above 90.",Fore.BLUE+ "stoch val=", stoch_val)
            stoch_above_90 = True

        if stoch_above_90 and stoch_val < 90:
            print("Stochastic Oscillator moving below 90. Placing ",Fore.RED+"'PUT⇩'"," Option.",Fore.BLUE+ "stoch val=", stoch_val)
            stoch_above_90 = False
            put.append(1)

        if stoch_val < 10 and not stoch_below_10:
            print("Stochastic Oscillator touched below 10.", Fore.BLUE+"stoch val=", stoch_val)
            stoch_below_10 = True

        if stoch_below_10 and stoch_val > 10:
            print("Stochastic Oscillator touched below 10. Placing ",Fore.GREEN+"'CALL⇑'"," Option.",Fore.BLUE+ "stoch val=", stoch_val)
            stoch_below_10 = False
            call.append(1)

        if not stoch_below_10 and not stoch_above_90 :
            print("No Trading Signal (Stochastic Oscillator)😕.", Fore.BLUE+"stoch val=", stoch_val)

        print(line)
        print(Fore.BLACK+Back.CYAN+"MA:")

        if my_close[-1] > ma_val and not ma_above_price:
            print("Price crossed above the Moving Average. Placing ",Fore.RED+"'PUT⇩'"," Option.", Fore.BLUE+"\nMA val=",ma_val)
            ma_above_price = True
            put.append(1)
        elif my_close[-1] < ma_val and ma_above_price:
            print("Price crossed below the Moving Average. Placing ",Fore.GREEN+"'CALL⇑'"," Option.", Fore.BLUE+"\nMA val=", ma_val)
            ma_above_price = False
            call.append(1)

        else:
            print("No Trading Signal (Moving Average)😕.", Fore.BLUE+"MA val=", ma_val)
        
        print(line)

        call_signal = len(call)
        put_signal = len(put)

        print("total call=",call_signal ,"\ttotal put=",put_signal)

       # Calculate the average signal
        if call_signal < put_signal:
            if put_signal == 5 or put_signal == 4 :
                overall_signal = Fore.RED+"STRONG PUT⇩"
                print(Fore.BLUE+"Overall Signal:", overall_signal) 
                print(line)
                await place_option(Iq, "put")
            elif put_signal == 3 or put_signal == 2 :
                overall_signal = Fore.LIGHTRED_EX+"PUT⇩"
                print(Fore.BLUE+"Overall Signal:", overall_signal) 
                print(line)
                await place_option(Iq, "put")
            else :
                overall_signal = "NEUTRAL(PUT⇩😕)"
                print(Fore.BLUE+"Overall Signal:", overall_signal) 
                

        elif call_signal > put_signal :
            if call_signal == 5 or call_signal == 4 :
                overall_signal = Fore.GREEN+"STRONG CALL⇑"
                print(Fore.BLUE+"Overall Signal:", overall_signal) 
                print(line)
                await place_option(Iq, "call")
            elif call_signal == 3 or call_signal == 2 :
                overall_signal = Fore.LIGHTGREEN_EX+"CALL⇑"
                print(Fore.BLUE+"Overall Signal:", overall_signal) 
                print(line)
                await place_option(Iq, "call")
            else :
                overall_signal = "NEUTRAL(CALL⇑😕)"
                print(Fore.BLUE+"Overall Signal:", overall_signal) 
                
        else:
            overall_signal="NEUTRAL(NO SIGNALS😕)"
            print(Fore.BLUE+"Overall Signal:", overall_signal) 
        
        print(line)
        await countdown(60)


async def place_option(Iq, option_type):                           #place option
    expirations_mode = 1  # Option Expiration Time in Minutes (You can adjust this as needed)

    check, id = Iq.buy(money, goal, option_type, expirations_mode)
    if check:
        print(Fore.GREEN+f"'{option_type}' Option Placed Successfully.")
    else:
        print(Fore.RED + f"'{option_type}' Option Failed.")

async def main():                                                  #main def
    Iq = await login()
    await set_balance_type(Iq)

    global goal
    global money

    print(Back.MAGENTA + Fore.BLACK+"[+] Assets:" )
    print(Fore.RED+"AUDCAD,AUDJPY,AUDUSD,EURGBP,EURUSD,EURJPY,GBPJPY,GBPUSD,USDCAD,USDJPY")
    print(Fore.RED + "add -OTC at end of Assets on market holidays type Asset in capital letters")
    goal = input(Fore.BLUE+"Enter the ASSET:")
    money = float(input(Fore.BLUE+"Enter the AMOUNT($):"))

    balance=Iq.get_balance()
    print(Back.MAGENTA+Fore.BLACK+"[+] Amount Balance :",balance)

    size = 60
    period = 14

    my_close = []

    # Create tasks for each strategy
    tasks = [
        get_realtime_candles(Iq, size, period),
        apply_trading_conditions(Iq, my_close, size, period)
    ]

    # Start all tasks
    await asyncio.gather(*tasks)

if __name__ == "__main__":                                         #main def loop
    asyncio.run(main())

