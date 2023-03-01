import cmodule.charmr_module as cm
import os
import sys
import signal
import time
import math
import subprocess
import numpy as np
import datetime
import threading
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import utils as utils
from model.brightnesstemperaturemenu import BrightnessTemperatureMenu
import model.basemenu
from model.startup import Startup
from model.mainmenu import MainMenu
from model.mainsettingsmenu import MainSettingsMenu
from model.slideshow import Slideshow


'''
This class is responsible for recieving user input. It monitors what appplication the user is currently on (main menu, slideshow, etc.), and sends
the input to the appropriate application. It also sends commands to the display to display the appropriate application based on user input.
'''

class Controller:

    def __init__(self): 
        
        self.current_application = 'startup'
        
        self.startup = Startup()
                
        # responsible for monitoring the brightness/temperature of the demo
        #self.bght_temp_menu = BrightnessTemperatureMenu() 

        # responsible for monitoring applications that can be launched from the main menu (currently, slideshows, sketch app, and main menu settings)
        self.main_menu = MainMenu() # Builds menu, saves as temporary image

        self.main_settings_menu = MainSettingsMenu()

        self.slideshow = None

        # to be implemented
        self.wfm_transition_dict = {'dictionary of waveform transitions'} # should be loaded from a json file?
        
        # to be implemented - easier way to send user input to the appropriate input processing method
        # ideally - self.components[self.current_application](user_input) -> to process user input - no need for a big if/else
        # statement to figure out which method to send input to
        self.components={'main': self.send_menu_input,
                         'mainsettings': self.send_msettings_input, 
                         # 'slideshow': self.send_slideshow_input,
                         # #'pause': self.send_pause_input,
                         # 'pausesettings': self.send_psettings_input
                         }

        self.touch_dict={
            'brightness_button': [[0,1716], [215,cm.hsize]],
            'temperature_button': [[215,1716], [420,cm.hsize]],
            'sketch_button': [[.6910*cm.wsize,.8854*cm.hsize], [.8507*cm.wsize,cm.hsize]],
            'settings_button': [[.8507*cm.wsize,.8854*cm.hsize], [cm.wsize,cm.hsize]],
            'exit_button': [[.7743*cm.wsize,.1781*cm.hsize], [.8590*cm.wsize,.2417*cm.hsize]],
            'back_button': [[.6736*cm.wsize,.1771*cm.hsize], [.7708*cm.wsize,.2396*cm.hsize]],
            'slider': [[460,1730], [990,1850]]
            }

    '''
    Waits for user input. When input is recieved, sends input to correct processing function based on what the current application is.
    ''' 
    def run(self):
        
        self.run_main_menu()

    '''
    Sets the current application to be the main menu and sends a command to display to load the appropriate screen.
    '''
    def run_main_menu(self):
        if self.current_application == 'startup':
            self.startup.clear()
        
        self.current_application = 'main'
        self.main_menu.display()
        
        while True:
            
            user_input = utils.get_input()
            processed_input = self.main_menu.process_input(user_input)
                        
            if processed_input == 'settings_button':
                self.run_settings()


    '''
    Sets the current application to the appropriate settings. If the user is currently in the 'main' application, changes the current application to main settings 
    ('msettings') and displays the appropriate screen by sending a command to the display class. If the user is currently in the 'pause' application, changes the 
    current application to the pause settings ('psettings') and displays the appropriate screen.
    '''
    def run_settings(self):
        if self.current_application == 'main':
            self.current_application = 'mainsettings'
            self.main_settings_menu.display()
            
            while True:  
                user_input = utils.get_input()            
                processed_input = self.main_settings_menu.process_input(user_input)
                                
                if processed_input == 'settings_button':
                    self.run_main_menu()
                
        elif self.current_application == 'pause':
            self.current_application = 'pausesettings'
            #self.display.display_pausesettings()

    '''
    Displays the temp/brightness slider and sends the user input to the BrightnessTemperatureSlider class to change the brightness/temperature on the device.
    '''
    def run_slider(self, user_input):
        # figure out how to display check - in Jake's code it is tied up with buttons method
        #self.model.update_slider(user_input)
        self.bght_temp_menu.brightness_temperature_slider(user_input)
    
    '''
    Displays the 'brightness' label above the brightness/temperature slider and updates the BrightnessTemperatureMenu's current application so that any touches on the
    slider will modify device brightness
    '''
    # def load_brightness(self):
    #     self.bght_temp_menu.select_type("bght")
    #     self.display.load_area(self.display.directory + 'label_brightness.pgm', (616,1718))   

    '''
    Displays the 'temperature' label above the brightness/temperature slider and updates the BrightnessTemperatureMenu's current application so that any touches on the
    slider will modify device temperature
    '''
    # def load_temperature(self):
    #     self.bght_temp_menu.select_type("temp")
    #     self.display.load_area(self.display.directory + 'label_temperature.pgm', (616,1718))

    '''
    Sets the current application to be 'main' and sends a command to display to display the starup screen.
    '''
    # def load_startup(self):
    #     self.current_application = 'main'
    #     self.display.display_startup_screen()

    '''
    Sends user input to the main menu. Currently, users can select either a slideshow or the sketch app to be run. The main menu will return the application that
    is selected, and the controller will either run and display the slideshow or run and display the sketch app.
    '''
    def send_menu_input(self, user_input):
        application = self.main_menu.process_input(user_input)

        # if application != None: 
        #     if type(application) == Slideshow:
        #         self.current_application = 'slideshow'
                
        #         self.slideshow = application

        #         self.slideshow_run()


    def send_msettings_input(self, user_input):
        pass

    def send_slideshow_input(self, user_input):
        pass

    # def send_pause_input(self, user_input):
    #     self.slideshow.process_pause_input(user_input)

    def send_psettings_input(self, user_input):
        self.slideshow.process_settings_input(user_input)

        # USE THIS TO TAKE CARE OF DISPLAYING PAUSE SCREEN CHECKMARKED OPTIONS, ETC
        # self.display.update_pause_screen()

    '''
    Sets the current application to be 'pause' and sends a command to display to display the pause screen.
    '''
    def run_pause(self): pass
        # self.current_application = 'pause'
        # self.display.display_pause()                                                                                                                                                                                                                                                                       

    def run_sketch(self, app): pass
        # self.main_menu.launch_sketch_app()
        # self.display.display_sketch_app()

    '''
    Autoruns the slideshow. If no user input is recieved before the slide timeout, sends a command to the display to change the slide. Otherwise, processes the slideshow
    input. If a 'QUIT' command is recieved from the slideshow input processing method, will terminate the slideshow autorun (essentially pausing the slideshow on the 
    current slide)
    '''
    def run_slideshow(self):
        while self.slideshow.cur_slide <  self.slideshow.length:
            user_input = utils.get_input(t=self.slideshow.slide_timer())

            # no input before slide times out, automatically transition to next slide
            if user_input == None:
                self.slideshow.change_slide(self.slideshow, "next")
            else:
                output = self.process_slideshow_input(self.slideshow, user_input)

                # come up with something better. Right now, if user pauses process input will return QUIT signifying that autoplay of slideshow should end
                if output == 'QUIT':
                    return

    '''
    Processes any user input recieved while a slideshow is running.
    Tap touch (user_input is a list of touch coordinates)
        - pause slideshow and load the appropriate pause screen
    Swipe touch (user_input is a string)
        - either changes slide or loads pause/main screen based on swipe direction
    Button input (user_input is a string)
        - either changes slide or loads pause screen based on swipe direction
    '''
    def process_slideshow_input(self, slideshow, user_input):
        if type(user_input) == list: 
            #direction = 'remain'
            self.load_pause()

            return 'QUIT'
            # CLEAR("strd")# Tap touch returns list value

        elif type(user_input) == str: # Swipe touch returns string value
            if user_input == "swipe left":  
                direction = "next"
            if user_input == "swipe right":
                direction = "back"
            if user_input == "swipe down":
                self.load_main()
                return 'QUIT'
            if user_input == "swipe up" or "enter":
                self.load_pause()
                return 'QUIT'
            if user_input == "up":
                direction = "next"
            if user_input == "down":
                direction = "back"          

        self.display.change_slide(slideshow, direction) # LOADS AND DISPLAYS SLIDE
        
if __name__ == '__main__':

    c = Controller()

    c.run()