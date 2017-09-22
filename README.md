# INTRODUCTION

Ziroom is the largest apartment rental platform in China with tons of information about rooms in each area of different cities. When I decided to go back to work in summer, I had troubles to find a place that meet my requirements and budget. 

The main problem is that I have to click into every single page of each room to get room information. I found it every hard to filter them out and compare them, especially I only want to live with girls for safety reason. Therefore, I wrote this program to scrape information from www.ziroom.com based on location, attributes, or bookmark you save. The program will automatically summarize the key information of each room (for me I keep pricing, location, room size and type) and filter out those rooms for only girls.

This program will search for girl-only rooms in areas listed. It summarizes and lists pricing, locations, room capacity and room type of each filtered room in a html file called "result.html" for you to compare and choose.

The information to be processed is numerous, therefore multi-threading is used in the program. Make sure you have threading libraries installed on your computer. Otherwise, use the pre-built package program.



# HOW TO USE

## Command Line

### Method #1: Bookmark

1. Save all relevant room pages into "rent" folder in your bookmark html file
2. Copy your bookmark html file into "user" folder in "rent" folder
3. Goto "rent" folder, run "rent.py" and enter bookmark and press enter
4. Result will be in the "result.html" file under "user" folder



### Method #2: Locations

1. Run "rent.py" in "rent" folder
2. Enter "location"
3. Enter all location/area names that you want to search in. You can enter multiple names separated by comma, semi-colon and dash line.  It searches '次渠','次渠南','经海路' by default.
4. Result will be in the "result.html" under "user" folder



### Method #3: All

1. Run "rent.py" in "rent" folder
2. Enter all. See result in "result.html" of "user" folder



## Built Program

There is a pre-built program in the "pack" folder. It is built for windows. Users who do not know how to run command line could goto "pack" -> "rent", and find the rent.exe file. Then follow the above instructions to get specific results.