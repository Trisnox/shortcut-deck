# shortcut-deck
An app that turn your mobile device into a deck that can be used for variety uses. It uses socket to connect both client and server. 

## This script is currently on proof of concept stage
It'll later rewritten using kivy for mobile devices after all major features have been met. You can use Pydroid 3 to run the client on android deivces.

# Installing and Usage
For desktop, install [python](https://www.python.org/), locate the script directory, and run `main.py`. This script include both client and server.

After navigating through the script directory, run this following command:
```
pip install -r requirements.txt
```
If you're on pydroid 3, you simply only need to install `pillow` through the pip > quick install.

After successfully installed the requirements, simply run:
```
[Windows] py main.py
[Linux]   python3 main.py
```

You can close the program by closing the command line window. It is currently buggy to close it through ctrl + c.

## Preset
You can have many preset as you want by editing the `config.yaml` using [Notepad++](https://notepad-plus-plus.org/downloads/) or any other text editor of your choice, preset template and its description also available inside the file.

# Features
- Send hotkey, can be either singular or sequence
- Send mouse click, you can also supply position
- Run external script/program using command line. Currently only desktop able to execute script/program

# to-do
- Shared script. A way for client to receive a script from server, typically python.
- OBS integration. When the server script is run inside OBS, you can integrate with OBS API with this.
- Sequence of hotkeys. Currently, you can only send single sequence of hotkey.
- Rewrite on kivy. For compability, as well executable version for linux and windows, Ios and Android included.
- Animated icon
- Wiki

# Notes
You can use another desktop as a client, though using mobile devices are much more convenient. You can't use mobile devices as a server because certain python packages cannot be used in mobile devices.