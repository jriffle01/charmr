import threading
import sys 
sys.path.append('cmodule')

import charmr_module as cm

'''
Responsible for monitoring the state of the slideshow
'''
class Slideshow():

    def __init__(self, cm_slideshow):

        # the current slide of the slideshow
        self.cur_slide = 0
        
        # this is the slideshow info from the charmr_module file, stored for easy access
        self.cm_slideshow = cm_slideshow

        # the length of the slideshow (number of slides)
        self.length = len(self.cm_slideshow.file)

        # to be implemented - pause management
        #self.pause_menu = PauseMenu()


    # def setup(self, arg):
    #     #def CHANGE_SLIDESHOW(arg):
    #     # s_Check = self.directory + 'check_bar.pgm'; s_Uncheck = self.directory + 'uncheck_bar.pgm'    
    #     # CHECK(menu.sshw, int(arg)-1, None, s_Check, s_Uncheck)
    #     self.slideshow_progression()

    '''
    Calculates the necessary slide timeout based on the waveform of the current slide
    
    RETURNS
    The slide timeout value (int)
    '''
    def slide_timer(self):   
        if str(self.cm_slideshow.wfm[self.cur_slide]) == '2': time_Added = 1024
        if str(self.cm_slideshow.wfm[self.cur_slide]) == '3': time_Added = 377
        if str(self.cm_slideshow.wfm[self.cur_slide]) == '4': time_Added = 518
        if str(self.cm_slideshow.wfm[self.cur_slide]) == '5': time_Added = 1518
        if str(self.cm_slideshow.wfm[self.cur_slide]) == '6': time_Added = 377
        if str(self.cm_slideshow.wfm[self.cur_slide]) == '7': time_Added = 729

        return int(self.cm_slideshow.time[self.cur_slide])+time_Added
            
            
