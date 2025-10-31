import network
import asyncio
import ure as re
from micropython import const

import RTC

# IP Address: 192.168.4.1
# Global Constants
_NUM_CONTAINERS = const(10)
_MIN_RES = const(60)
_TIME_INTERVAL = const(10)
number=re.compile("\d+") # type: ignore

# Global variables for the website module.
labels=["", "", "", "", "", "", "", "", "", ""]
page_requested="/home"
error_msg=""

# Debug Variables
connection_num=0

def init_wifi():
    '''
    Sets up the pico to accept connections as a soft access point with the given SSID and password.
    '''
    # Wi-Fi credentials
    _SSID = const('RPI_PICO_AP')                                    #Set access point name 
    _PASSWORD = const('12345678')                                   #Set your access point password

    # Configure Wifi as soft access point
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=_SSID, password=_PASSWORD)
    ap.active(True)                                         #activating
    while ap.active() == False:                             #Wait for connection
        pass

# Parsing Functions ----------------------------------------------------------------------
def str_to_time(time_str):
    hour, minute = time_str.split("%3A")
    minute = number.search(minute)
    if not minute:
        return 0
    minute = int(minute.group(0))
    return int(hour)*_MIN_RES+int(minute)

def schedule_add(body, schedule):
    global _NUM_CONTAINERS, _TIME_INTERVAL
    pairs = body.split("&")
    label, val = pairs[0].split("=")
    if label != "new_time":
        raise ValueError("Schedule entry did not include a time.")
    val=str_to_time(val)
    insert_pos=len(schedule)
    for x in range(0, len(schedule), 11):
        if (schedule[x] > val):
            if (val>schedule[x]-_TIME_INTERVAL):
                raise ValueError(f"Schedule entry already exists for the {time_to_str(val)}-{time_to_str(val+_TIME_INTERVAL)} range.")
            insert_pos=x
            break
        if (schedule[x] > val-_TIME_INTERVAL):
            raise ValueError(f"Schedule entry already exists for the {time_to_str(schedule[x])}-{time_to_str(schedule[x]+_TIME_INTERVAL)} range.")
    
    schedule.insert(insert_pos, val)    #Append the time.
    i=insert_pos+1
    index=0
    for pair in pairs[1:]:  #Append the doses.
        label, val = pair.split("=")
        index=int(label)+insert_pos

        match_val = number.search(val)              #Ensure value isn't empty
        if not match_val:
            continue

        while i<index:
            schedule.insert(i, 0)                      #Add zero for missing values.
            i+=1
        
        schedule.insert(i, int(match_val.group(0)))         #Add value
        i+=1
    for x in range(_NUM_CONTAINERS-(i-insert_pos-1)):
        schedule.insert(i, 0)
   
def schedule_del(page, schedule):
    global _NUM_CONTAINERS
    match_base=number.search(page)

    base=int(match_base.group(0))                        #Delete base:base+_NUM_CONTAINERS
    for _ in range(_NUM_CONTAINERS+1):
        del schedule[base]

def labels_set(body, labels):
    pairs = body.split("&")
    for pair in pairs:  #Append the doses.
        label, val = pair.split("=")
        
        if val==""or val=="'":
            continue
        if "'" in val:
            val=val[0:len(val)-1]
        
        index=int(label)
        labels[index]=val
        
def amounts_set(body, amounts):
    pairs = body.split("&")
    for pair in pairs:  #Append the doses.
        label, val = pair.split("=")
        
        match_val = number.search(val)              #Ensure value isn't empty
        if not match_val:
            continue
        
        index=int(label)
        amounts[index]=int(match_val.group(0))+amounts[index]

def amounts_clr(page, amounts):
    match_base=number.search(page)

    index=int(match_base.group(0))                  #Reset amounts[index]
    amounts[index]=0

def init_time_set(body):
    label, val = body.split("=")
    time=str_to_time(val)
    rtc = RTC.clocksetup(1, 3, 2)
    rtc.set_time(hour=int(time/_MIN_RES), minute=time%_MIN_RES)
    return time


async def parse_response(reader, data):
    '''
    :reader:            asynio Steam reader object

    Modifies schedule, labels, amounts, time_init, page_requested
    '''
    global labels, page_requested, error_msg
    global connection_num
    connection_num+=1
    # Read Request
    request=b''
    line=b''
    while True:
        line = await reader.read(20)
        request+=line
        if len(line) < 20: # This might glitch if the request is a multiple of 20 bytes.
            break
    request=str(request)
    # print(request)
    header, body = request.split("\\r\\n\\r\\n")
    page=header.split(" ")[1]

    # Determine action and the new page from the request
    if "/favicon.ico" in page:
        return
    elif "/delete" in page:
        schedule_del(page, data['schedule'])
        page_requested="/schedule"
        return
    elif "/clear_amount" in page:
        amounts_clr(page, data['amounts'])
        page_requested="/amounts"
        return
    elif "/submit_schedule" in page:
        try:
            schedule_add(body, data['schedule'])
        except Exception as e:
            error_msg=str(e)
        page_requested="/add"
        return
            
    elif "/submit_labels" in page:
        labels_set(body, labels)
        page_requested="/labels"
        return
    elif "/submit_amounts" in page:
        amounts_set(body, data['amounts'])
        page_requested="/amounts"
        return
    elif "/init_time" in page:
        data['init_time']=init_time_set(body)
        print(f'init_time is {data['init_time']}.')
    page_requested=page

# Page Generagation Functions ---------------------------------------------------------------
def time_to_str(time_int):
    return f'{int(time_int/_MIN_RES)}:{time_int%_MIN_RES}'

def schedule_page(schedule, labels):
    global _NUM_CONTAINERS       
    # Add table entries for each entry in list
    max=len(schedule)
    if (max == 0):
        html="""
        <html>
            <head>Schedule</head>
            <body>
                <form method="post" action="./home"><input type="submit" value="Return to home."></form>
                <form method="post" action="./add"><input type="submit" value="Add a schedule entry."></form>
            </body>
        </html>
        """
        return str(html)
    else:
        html=f"""
                <html>
                    <head>Schedule</head>
                    <body>
                        <form method="post" action="./home"><input type="submit" value="Return to home."></form>
                        <form method="post" action="./add"><input type="submit" value="Add a schedule entry."></form>
                        <table>
                            <tr>
                                <th>Time</th>
                                <th>{labels[0]}</th>
                                <th>{labels[1]}</th>
                                <th>{labels[2]}</th>
                                <th>{labels[3]}</th>
                                <th>{labels[4]}</th>
                                <th>{labels[5]}</th>
                                <th>{labels[6]}</th>
                                <th>{labels[7]}</th>
                                <th>{labels[8]}</th>
                                <th>{labels[9]}</th>
                            </tr>
                            <tr><form method="get" action="/home">
                """
        for i in range(max):
            if (i%(_NUM_CONTAINERS+1)== 0 and i!=0): # New line
                html+=f"""<td><input type="submit" formmethod="get" formaction="./delete_{i-(_NUM_CONTAINERS+1)}" value="Delete."></td></form></tr><tr><form>"""
            if (i%(_NUM_CONTAINERS+1)==0): # Time Entry
                html+=f"""<td>{time_to_str(schedule[i])}</td>"""
            else: # Dose Entry
                html+=f"""<td>{schedule[i]}</td>""" 
            
        html+= f"""
            <td><input type="submit" formmethod="get" formaction="./delete_{max-(_NUM_CONTAINERS+1)}" value="Delete."></td></form></tr>
            </table>
        </body>
        </html>
        """
    return html

def page_gen(schedule, amounts, last_dose_taken, init_time):
    global page_requested, labels, error_msg
    if "/schedule" in page_requested:
        html=schedule_page(schedule, labels)
    elif "/add" in page_requested:
        html= f"""
        <html>
        <head>Add Entry to Schedule</head>
        <body>
            <form method="post" action="./schedule"><input type="submit" value="Return to schedule view."></form>
            <form method="post" action="./schedule">
            <table>
                <tr>
                    <th>Time</th>
                    <th>{labels[0]}</th>
                    <th>{labels[1]}</th>
                    <th>{labels[2]}</th>
                    <th>{labels[3]}</th>
                    <th>{labels[4]}</th>
                    <th>{labels[5]}</th>
                    <th>{labels[6]}</th>
                    <th>{labels[7]}</th>
                    <th>{labels[8]}</th>
                    <th>{labels[9]}</th>
                </tr>
                <tr>
                    <td><input type="time" name="new_time" id="time" placeholder="Enter dispense time."></td>
                    <td><input type="number" min=0 name="0" id="0" placeholder="Enter dose amount."></td>
                    <td><input type="number" min=0 name="1" id="1" placeholder="Enter dose amount."></td>
                    <td><input type="number" min=0 name="2" id="2" placeholder="Enter dose amount."></td>
                    <td><input type="number" min=0 name="3" id="3" placeholder="Enter dose amount."></td>
                    <td><input type="number" min=0 name="4" id="4" placeholder="Enter dose amount."></td>
                    <td><input type="number" min=0 name="5" id="5" placeholder="Enter dose amount."></td>
                    <td><input type="number" min=0 name="6" id="6" placeholder="Enter dose amount."></td>
                    <td><input type="number" min=0 name="7" id="7" placeholder="Enter dose amount."></td>
                    <td><input type="number" min=0 name="8" id="8" placeholder="Enter dose amount."></td>
                    <td><input type="number" min=0 name="9" id="9" placeholder="Enter dose amount."></td>
                </tr>
                <tr>
                    <td><input type="submit" formaction="./submit_schedule" value="Add new dispense time."></td>
                </tr>
                <tr><td>{error_msg}</td></tr>
            </table>
            </form>
        </body>
        </html>
        """
    elif "/labels" in page_requested:
        html= f"""
        <html>
        <head>Label Containers</head>
        <body>
            <form method="post" action="./home"><input type="submit" value="Return to home."></form>
            <form>
                <table>
                        <th>Container 1</th>
                        <th>Container 2</th>
                        <th>Container 3</th>
                        <th>Container 4</th>
                        <th>Container 5</th>
                        <th>Container 6</th>
                        <th>Container 7</th>
                        <th>Container 8</th>
                        <th>Container 9</th>
                        <th>Container 10</th>
                    </tr>
                    <tr>
                        <td><input type="text" id="0" name="0" placeholder="{labels[0]}"></td>
                        <td><input type="text" id="1" name="1" placeholder="{labels[1]}"></td>
                        <td><input type="text" id="2" name="2" placeholder="{labels[2]}"></td>
                        <td><input type="text" id="3" name="3" placeholder="{labels[3]}"></td>
                        <td><input type="text" id="4" name="4" placeholder="{labels[4]}"></td>
                        <td><input type="text" id="5" name="5" placeholder="{labels[5]}"></td>
                        <td><input type="text" id="6" name="6" placeholder="{labels[6]}"></td>
                        <td><input type="text" id="7" name="7" placeholder="{labels[7]}"></td>
                        <td><input type="text" id="8" name="8" placeholder="{labels[8]}"></td>
                        <td><input type="text" id="9" name="9" placeholder="{labels[9]}"></td>
                    </tr>
                    <tr><input type="submit" formmethod="post" formaction="./submit_labels" value="Set Labels."></tr>
                </table>
            </form>
        </body>
        </html>
        """
    elif "/amounts" in page_requested:
        html= f"""
        <html>
        <head>Pill Amounts</head>
        <body>
            <form method="post" action="./home"><input type="submit" value="Return to home."></form>
            <form method="post" action="./home">
                <table>
                    <tr>
                        <th>{labels[0]}</th>
                        <th>{labels[1]}</th>
                        <th>{labels[2]}</th>
                        <th>{labels[3]}</th>
                        <th>{labels[4]}</th>
                        <th>{labels[5]}</th>
                        <th>{labels[6]}</th>
                        <th>{labels[7]}</th>
                        <th>{labels[8]}</th>
                        <th>{labels[9]}</th>
                    </tr>
                    <tr>
                        <td>{amounts[0]}</td>
                        <td>{amounts[1]}</td>
                        <td>{amounts[2]}</td>
                        <td>{amounts[3]}</td>
                        <td>{amounts[4]}</td>
                        <td>{amounts[5]}</td>
                        <td>{amounts[6]}</td>
                        <td>{amounts[7]}</td>
                        <td>{amounts[8]}</td>
                        <td>{amounts[9]}</td>
                    </tr>
                    <tr>
                        <td><input type="" id="0" name="0"></td>
                        <td><input type="number" min=0 id="1" name="1"></td>
                        <td><input type="number" min=0 id="2" name="2"></td>
                        <td><input type="number" min=0 id="3" name="3"></td>
                        <td><input type="number" min=0 id="4" name="4"></td>
                        <td><input type="number" min=0 id="5" name="5"></td>
                        <td><input type="number" min=0 id="6" name="6"></td>
                        <td><input type="number" min=0 id="7" name="7"></td>
                        <td><input type="number" min=0 id="8" name="8"></td>
                        <td><input type="number" min=0 id="9" name="9"></td>
                        <td><input type="submit" formaction="./submit_amounts" value="Add to pill total."></td>
                    </tr>
                    <tr>
                        <td><input type="submit" formaction="./clear_amount0" value="Reset Amount."></td>
                        <td><input type="submit" formaction="./clear_amount1" value="Reset Amount."></td>
                        <td><input type="submit" formaction="./clear_amount2" value="Reset Amount."></td>
                        <td><input type="submit" formaction="./clear_amount3" value="Reset Amount."></td>
                        <td><input type="submit" formaction="./clear_amount4" value="Reset Amount."></td>
                        <td><input type="submit" formaction="./clear_amount5" value="Reset Amount."></td>
                        <td><input type="submit" formaction="./clear_amount6" value="Reset Amount."></td>
                        <td><input type="submit" formaction="./clear_amount7" value="Reset Amount."></td>
                        <td><input type="submit" formaction="./clear_amount8" value="Reset Amount."></td>
                        <td><input type="submit" formaction="./clear_amount9" value="Reset Amount."></td>
                    </tr>
                </table>
            </form>
        </body>
        </html>
        """
    else:
        dose_alarm=" not"
        if (last_dose_taken):
            dose_alarm=""
        html= f"""
        <html>
        <head>Home</head>
        <body>
            <form method="get" action="./home">
            <table>
                <tr>
                    <td><input type="submit" formmethod="get" formaction="./labels" value="Label Containers"></td>
                </tr>
                <tr>
                    <td><input type="submit" formmethod="get" formaction="./amounts" value="Update Pill Amounts"></td>
                </tr>
                <tr>
                    <td><input type="submit" formmethod="get" formaction="./schedule" value="View Schedule"></td>
                </tr>
                <tr>
                    <td>Initial Time</td>
                    <td>Reset Time</td>
                </tr>
                <tr>
                    <td>{time_to_str(init_time)}</td>
                    <td><input type="time" name="init_time" id="time" placeholder=""></td>
                    <td><input type="submit" formmethod="post" formaction="./init_time" value="Reset initial time."></td>
                </tr>
                <tr>
                    <td>The last dose was{dose_alarm} taken.</td>
                </tr>
            </table>
            </form>
        </body>
        </html>
        """

    error_msg=""
    return str(html)
