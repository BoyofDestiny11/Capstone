import asyncio
import time

# For tests only
from machine import Pin

# Our Modules
import website
import memory

# Globals shared by all modules.
data = memory.load()
        
# Code for loop
async def handle_client(reader, writer):
    '''
    :reader:            asyncio Stream reader
    :writer:            asyncion Stream writer

    Responds to the client.
    '''
    # Global variables that are shared with non-website modules
    global data
    
    # Update variables based on client request
    await website.parse_response(reader, data)
    # Generate new_page
    new_page = website.page_gen(data['schedule'], data['amounts'], data['last_dose_taken'], data['init_time'])

    # Send the HTTP response and close the connection
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(new_page)
    await writer.drain()
    await writer.wait_closed()

    memory.save(data)

async def async_loop():    
    '''
    setup: website.init_wifi and memory.load
    async loop for website and control code
    '''
    # Setup
    website.init_wifi()
    
    # Start the server and run the event loop
    server = asyncio.start_server(handle_client, "0.0.0.0", 80)
    asyncio.create_task(server)
    
    # Loop for other tasks
    global data
    while True:
        # Simulate value updates in dispenser for testing
        data["last_dose_taken"]=not data['last_dose_taken']
        memory.save(data)
        print(data)
        await asyncio.sleep(10)

# Test Functions for main-level
def loop_test():
    # Create an Event Loop
    loop = asyncio.get_event_loop()
    # Create a task to run the main function
    loop.create_task(async_loop())

    try:
        loop.run_forever()
    except Exception as e:
        print('Error occurred: ', e)
    except KeyboardInterrupt:
        print('Program Interrupted by the user')

def memory_test():
    def blink(x):
        led = Pin('LED', Pin.OUT)
        for _ in range(x):
            led.value(True)
            time.sleep(0.33)
            led.value(False)
            time.sleep(0.33)

    data = memory.load()

    while (True):
        print(data)

        data["init_time"] = data['init_time']+1
        memory.save(data)
        blink(data["init_time"])

        print("Blinking done.")
        time.sleep(5)

# Main Code
loop_test()
# memory_test()