Pokémon TCG Match Tracker - Easy Setup Guide

Welcome! This simple guide will help you set up your Pokémon TCG Match Tracker on your computer. No technical experience needed - just follow these steps:


# Step 1: Install Python

Go to python.org

Click the yellow "Download Python" button

Run the downloaded installer file

IMPORTANT: Check the box that says "Add Python to PATH" during installation

Click "Install Now" and wait for completion



# Step 2: Download the Project

download the project files by going to the green "code" tab, then clicking "Download Zip".

Save the ZIP file to your desktop folder

Right-click the downloaded ZIP file and select "Extract All"

Remember where you extracted the folder (this is your "project folder")



# Step 3: Open the Command Window

Windows:

Press Win + R keys

Type cmd and press Enter

Mac:

Press Command + Space

Type Terminal and press Enter



# Step 4: Install Required Tools

In the command window, type each line below and press Enter after each:
bash

    pip install -r requirements.txt

    

# Step 5: Start the Tracker

In the same command window, type:
bash

    cd Desktop

bash

    cd PokemonTCGStats

bash

    python app.py



# Step 6: Open the Application

Open your web browser (Chrome, Firefox, Edge, etc.)

Type this exactly in the address bar:
    http://localhost:5000 (or an adderess prompted in the backend CMD)

Press Enter

You should now see your Pokémon TCG Match Tracker!
To Use Daily
Repeat Steps 5 and 6



# Troubleshooting Tips:

If pip install fails: 

        Try pip3 install -r requirements.txt instead

If python app.py fail Try:

        python3 app.py instead

Always keep the command window open while using the tracker

Close and reopen the command window if you make changes to the files

# Current Known Issues

Auto-save currently is not functional, please export your decks to save them

Analytic is not updated in real time, try exporting your deck and stats data, then restart your session and import that data

#How to use

Manually enter game data, the rest is self explanatory. PLEASE READ known issues to prevent data loss.
