**Windows**

install python from cmd shell type:
`python` and MS store shall popup, select python3 and click get/install.
After python is install install pip: by typing in cmd shell 
`python.exe -m pip install --upgrade pip`
after pip is installed from command shell type: 

`pip install -U python-dotenv requests configparser paramiko   confparser`
removed sys windows-curses

you can navigate to control panel > System and Security > System > Advanced system Settings.
Now in Advance System Setting click on Environment Variables.
Here we can add new user variables and new system variables. We will add user variable by clicking New under user variables.

In the new window you can add Variable name and Variable value and click ok.
Now, click Ok on Environment Variables window to save changes.

**Linux**

Start by updating the package list using the following command: `sudo apt update`.
Use the following command to install pip for Python 3: `sudo apt install python3-pip`. ...
Once the installation is complete, verify the installation by checking the pip version: `pip3 --version`.
`pip3 install -U python-dotenv requests configparser paramiko  confparser`
removed sys curses

nano ~/.bash_profile
export USER="username"
export PASSWORD="password"


**All**
cd ./config/
cp/copy parameters.ini.example parameters.ini
edit parameters.ini with users/password/IPs




windows