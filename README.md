# houseaccount
A small python GUI tool to track personal expenses

The tools is based on a sqlite database and tracks personal spendings. For each expense, the date, a comment and a category is stored. It has some diagrams that show expenses per month and per category.
This tool replaces my excel sheet and entering data is slightly more comfortable.

# Dependencies
The program is written entirely in python3. To read in excel files it uses the xlrd module. For database access and the GUI it depends on PyQt5. So far it is only tested under Ubuntu Linux 18.04 LTS. In theory it should also run well in windows.

# Building
Needed software:
sudo apt-get install python3
sudo apt-get install python3-pip

Needed python modules
pip3 install xlrd
pip3 install PyQt5

Building a single file executable using pyinstaller:
pip3 install pyinstaller
pyinstaller --onefile main.py

This builds a single executable file in the dist folder (the folder is created automatically if it doesn't exists already)


Note that the program is only a alpha version. Many features are missing or are only poorly implemented yet.
