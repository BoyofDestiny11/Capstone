import asyncio

# Our Modules
import website

# Globals shared by all modules.
schedule=[]
amounts=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
last_dose_taken=True
init_time=[0]


# Code for loop
async def handle_client(reader, writer):
    '''
    :reader:            asyncio Stream reader
    :writer:            asyncion Stream writer

    Responds to the client.
    '''
    # Global variables that are shared with non-website modules
    global schedule, amounts, init_time
    
    # Update variables based on client request
    await website.parse_response(reader, schedule, amounts, init_time)
    # Generate new_page
    new_page = website.page_gen(schedule, amounts, last_dose_taken, init_time)

    # Send the HTTP response and close the connection
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(new_page)
    await writer.drain()
    await writer.wait_closed()

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
    global last_dose_taken
    while True:
        # Simulate value updates in dispenser for testing
        # last_dose_taken=not last_dose_taken
        # print(last_dose_taken)
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

# Main Code
#memory.load(schedule, amounts, time_init)
loop_test()