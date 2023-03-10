import sys
import math
import fnmatch
import os
import time
from PIL import Image, ImageDraw, ImageFont
from matplotlib import pyplot as plt
from tkinter import filedialog as fd
import textwrap
import json
import unicodedata
import re

with open('HYPHEN_DICT.json') as json_file:
    DICT = json.load(json_file)

DASH_LIST = ['\u2014\u2014','\u2014','\u2013', '-'] # U+2013: en-dash, U+2014: em-dash

POST_SUFFIX = ['!\u201D','?\u201D','.\u201D','.',',',';',':','!','?','\u201D'] # U+u201D: right double quotation mark

    
class HYPHENATED_WORD():
    def __init__(self, word, first_half, second_half, remaining_pixels, buf):
        self.word = word
        self.first_half = first_half
        self.second_half = second_half
        self.remaining_pixels = remaining_pixels
        self.buf = buf

class CHAPTER_TO_PGM(object):
    """ Helper class to wrap text in lines, based on given text, font
        and max allowed line width.
    """
    def __init__(self, 
                 font_file, 
                 font_size, 
                 file_name=None, 
                 text=None, 
                 side_margin=150, 
                 top_margin=250, 
                 leading=1.2, 
                 indent=None, 
                 page_number=1, 
                 hyphenation='full',
                 chapter_numbering='roman',
                 file_type = '.pgm'
                 ):
        
        self.font_file = font_file
        self.font = ImageFont.truetype(font_file, font_size)
        self.text = text
        self.side_margin = side_margin
        self.top_margin = top_margin
        self.leading = self.font.size*leading
        self.indent = indent*self.font.size
        self.text_paragraphs = None
        self.chapter_numbering = chapter_numbering
        self.page_number = page_number
        self.line_number = 0
        self.hyphenation = hyphenation
        self.file_type = file_type
        self.file_name = file_name
        self.page = Image.new("L", (1440, 1920), 240)
        self.draw_page = ImageDraw.Draw(self.page)
        self.draw = ImageDraw.Draw(Image.new(mode='RGB', size=(100, 100)))
        self.space_width = self.draw.textlength(text=' ', font=self.font)

    def CHECK_DASH(self):
        global check
        for dash in DASH_LIST: # Check this first. Do not hyphenate a dashed or already hyphenated word
            if dash in check.word: # hyphen, en-dash, or em-dash
                word_part_pixel_width = self.font.getlength(str(check.word.split(dash)[0] +  str(dash)))
                if word_part_pixel_width < check.remaining_pixels:
                    check.first_half = check.word.split(dash)[0] + dash
                    check.second_half = check.word.split(dash)[1]
                    check.buf.append(check.first_half)       
                    check.remaining_pixels = check.remaining_pixels - word_part_pixel_width
                    return True
                else: return False
    
    def CHECK_ROOT(self):
        global check
        root_list = []
        # If no dash, look for any roots, to separate the root and leave a possible suffix ending
        # Only need to look for roots up to the last 3 characters in the string b/c suffixes need to be at least 3 characters long
        for num_char in range(3,len(check.word)-2): # for word "washing" of length 7 (range 3:5), num_char=3:4 
            for start_char in range(0,len(check.word)): # for num_char=3, range(0,4), start_char=0:3
                #print(check.word[start_char:start_char+num_char])
                root_part = check.word[start_char:start_char+num_char]
                if root_part.lower() in DICT and DICT[root_part.lower()] == 'root':
                    root_list.append(root_part)
        
        if len(root_list) != 0:
            root = max(root_list, key=len)
            check.first_half = check.word.split(root)[0] + root + '-'
            check.second_half = check.word.split(root)[1]      
            word_part_pixel_width = self.font.getlength(check.first_half)
            if word_part_pixel_width < check.remaining_pixels and len(check.second_half) > 2:
                check.buf.append(check.first_half)
                check.remaining_pixels = check.remaining_pixels - word_part_pixel_width 
                return True  
            else: return False
        
    def CHECK_POST_SUFFIX(self):
        global check
        check.post_suffix_character = ""
        for character in POST_SUFFIX: # checking if the suffix exists but there are end-of-word characters
            if check.word.endswith(character):   
                check.word = check.word[0:len(check.word)-len(character)]
                check.post_suffix_character = character
    
    def CHECK_SUFFIX(self):
        global check
        for num_char in reversed(range(3,len(check.word)-2)): # Checking for suffixes
            if check.word[len(check.word)-num_char:] in DICT and DICT[check.word[len(check.word)-num_char:]] == 'suffix':      
                check.first_half = check.word[0:len(check.word)-num_char] + '-'
                check.second_half = check.word[len(check.word)-num_char:] + check.post_suffix_character
                word_part_pixel_width = self.font.getlength(check.first_half)
                if word_part_pixel_width < check.remaining_pixels:
                    check.buf.append(check.first_half)
                    check.remaining_pixels = check.remaining_pixels - word_part_pixel_width 
                    return True
    
    def CHECK_PREFIX(self):
        global check
        for num_char in reversed(range(3,len(check.word)-2)): # Checking for prefixes
            lower_case_word = check.word.lower() 
            if lower_case_word[0:num_char].lower() in DICT and DICT[lower_case_word[0:num_char]] == 'prefix':
                check.first_half = check.word[0:num_char] + '-'
                check.second_half = check.word[num_char:] + check.post_suffix_character
                word_part_pixel_width = self.font.getlength(check.first_half)
                if word_part_pixel_width < check.remaining_pixels:
                    check.buf.append(check.first_half)
                    check.remaining_pixels = check.remaining_pixels - word_part_pixel_width  
                    return True 

    def check_hyphen(self):
        global check
        word_part_pixel_width = 0
        if len(check.word) < 7: return False
        result = self.CHECK_DASH()
        if result == True: return True
        if result == False: return False
        result = self.CHECK_ROOT()
        if result == True: return True
        if result == False: return False
        self.CHECK_POST_SUFFIX()
        if   self.CHECK_SUFFIX(): return True
        elif self.CHECK_PREFIX(): return True
        else: return False        
        return False

    def DECIMAL_TO_ROMAN(self, number):
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        roman_number = ''
        i = 0
        while number > 0:
            for _ in range(number // val[i]):
                roman_number += syb[i]
                number -= val[i]
            i += 1
        return roman_number

    def new_page(self):
        self.page = Image.new("L", (1440, 1920), 240)
        self.draw_page = ImageDraw.Draw(self.page)
        self.draw = ImageDraw.Draw(Image.new(mode='RGB', size=(100, 100)))
        self.page_number += 1
        self.line_number = 0

    def save_page(self):
        # write page # footer before saving
        w = self.font.getlength(str(self.page_number)) # width of character
        self.draw_page.text((1440 - self.side_margin - w, 1920 - 0.6*self.top_margin), str(self.page_number), font_size = self.font.size, font=self.font, fill=0)
        
        # For writing the age number to the file name
        if self.page_number < 10: 
            page_number = "00" + str(self.page_number)
        elif self.page_number < 100: 
            page_number = "0" + str(self.page_number)
        else: page_number = str(self.page_number)
        
        if not os.path.exists(os.path.dirname(self.file_name) + "/pages/"):
            os.makedirs(os.path.dirname(self.file_name) + "/pages/")
        image_name = os.path.dirname(self.file_name) + "/pages/" + os.path.basename(self.file_name).split('.')[0] + "__" + page_number + self.file_type

        self.page.save(image_name)
    
    def write_chapter_title(self):
        title = os.path.basename(self.file_name).split('.')[0] # remove the extension
        chapter_number, title = os.path.basename(title).split('__') # remove the extension
        
        if chapter_number[0] == '0': 
            chapter_number = chapter_number[1:]
        title = title.replace("_", " " ) # remove the underscores and replace with spaces
        
        old_size = self.font.size
        self.line_number = 3
        
        if "--" in chapter_number:
            text = title
        else:
            if self.chapter_numbering == 'roman': 
                chapter_number = self.DECIMAL_TO_ROMAN(int(chapter_number))
                text = chapter_number + ". " + title
            if self.chapter_numbering == 'decimal':
                text = "CHAPTER " + chapter_number + "\n\n" + title
                
        self.font = ImageFont.truetype(self.font_file, self.font.size + 20)
        self.draw_page.fontmode = "1"
        self.draw_page.multiline_text((1440/2,self.top_margin + self.leading*self.line_number), text, font=self.font, fill=0, align='center', anchor='mm')
        self.line_number = 10
        self.font = ImageFont.truetype(self.font_file, old_size)

    def get_text_width(self, text):
        return self.draw.textlength(text=text, font=self.font )
    
    def get_line_pixel_width(self, text):
        return self.font.getlength(text)
    
    def write_text_line(self, xy, single_line, tracking=0, leading=None):
        x, y = xy # starting position
        lines = single_line.splitlines()
        for line in lines:
            for character in line:
                w = self.font.getlength(character) # width of character
                self.draw_page.fontmode = "1"
                self.draw_page.text((x, y), character, font_size = self.font.size, font=self.font, fill=0)
                x += w + tracking # Next printing position in pixels
            x = xy[0]
    
    def write_chapter(self):
        global check
        single_line = []
        buf = []
        buf_width = 0
        
        if self.indent == None: # Default paragraph indent in pixels (dependent on font size)
            self.indent = 2.5*self.font.size
        
        if self.text == None:
           self. file_name = fd.askopenfilename(title="Choose chapter text file", )
            
        with open(self.file_name, 'r', encoding="utf8") as file:
            self.text = file.read()
        self.text = r"{}".format(self.text)
        
        self.text_paragraphs = [' '.join([w.strip() for w in l.split(' ') if w]) for l in self.text.split('\n') if l]
        self.write_chapter_title()
        
        for paragraph in self.text_paragraphs:
            indentation = True # Indent the paragraph
            for i, word in enumerate(paragraph.split(' ')):
                word_width = self.draw.textlength(text=word, font=self.font)
                expected_width = word_width if not buf else \
                    buf_width + self.space_width + word_width
                                        
                if 2*self.top_margin + self.leading*self.line_number > 1920:
                    self.save_page()
                    self.new_page()
                    
                # word fits in line
                if indentation == True and expected_width <= 1440-2*self.side_margin - self.indent:
                    buf_width = expected_width           
                    buf.append(word)
                elif indentation == False and expected_width <= 1440-2*self.side_margin:
                    buf_width = expected_width           
                    buf.append(word)
                
                # word doesn't fit in line
                else: 
                    single_line = ' '.join(buf)
                    line_pixel_width = self.font.getlength(single_line)
                    
                    number_characters = len(buf) - 1 # Start with the number of spaces between words
                    for every_word in buf: # Add the number of characters per word
                         number_characters += len(every_word)
                         
                    if indentation == True: remaining_pixels = 1440 - 2*self.side_margin - self.indent - line_pixel_width
                    if indentation == False: remaining_pixels = 1440 - 2*self.side_margin - line_pixel_width
                    
                    tracking=remaining_pixels/(number_characters-1) # Extra spacing between each letter ( > 0 ) 
                     
                    check = HYPHENATED_WORD(word, "", "", remaining_pixels, buf) # Returns true if the word that doesn't fit can be hyphenated
                    
                    if tracking > 0.5 and self.check_hyphen():
                        # if hypen is True, change all necessary variables 
                        remaining_pixels = check.remaining_pixels
                        number_characters += len(check.first_half) + 1
                        tracking = remaining_pixels/(number_characters)
                        buf = check.buf 
                        single_line = ' '.join(buf)
                        word = check.second_half # Change the word to the latter half of the hyphenated word
                                             
                    if indentation == True: # Indent paragraphs
                        start_position = (self.side_margin + self.indent, self.top_margin + self.leading*self.line_number)
                        self.write_text_line(start_position, 
                                             single_line, 
                                             tracking)
                        
                    else:
                        start_position = (self.side_margin, self.top_margin + self.leading*self.line_number)
                        self.write_text_line(start_position, 
                                             single_line, 
                                             tracking)
                        
                    single_line = []
                    self.line_number+=1
                    buf = [word]
                    buf_width = self.draw.textlength(text=word, font=self.font)
                    indentation = False
                    
            if buf: # Text line goes part way across page
                single_line = ' '.join(buf)
                if indentation == True: 
                    start_position = (self.side_margin + self.indent, self.top_margin + self.leading*self.line_number)
                    self.write_text_line(start_position, 
                                         single_line, 
                                         tracking = 0)
                else: 
                    start_position = (self.side_margin, self.top_margin + self.leading*self.line_number)
                    self.write_text_line(start_position, 
                                         single_line, 
                                         tracking=0)

                self.line_number+=1
                buf = []
                buf_width = 0

        self.save_page()

def BOOKTEXT_TO_IMAGE(font_file,
                      font_size, 
                      side_margin=150, 
                      top_margin=250, 
                      leading=1.2, 
                      indent=None, 
                      file_type='.pgm',
                      chapter_numbering='roman',
                      hyphenation='full'
                      ):

    r"""
    Convert .txt files into rendered images of book pages.
    
    The .txt files must be in a folder of their own, with each file a chapter
    Chapter files must be two-digit numbered followed by a double underscore, followed
    by the title of the chapter with spaces replaced with underscores

        ex. Chapter 5: In the Golden Age
            05__In_the_Golden_Age.txt
            
        To prevent chapter numbering, insert '--' after the chapter number
        
        ex. 05--__In_the_Golden_Age.txt
        
    The book pages can be formatted using the following arguments
        
        font type: any TrueType font file destination. *.ttf, *.otf 
            ex. font_file=r"C:\Users\User\TrueTypeFonts\Serif_Zachery.otf"
        font size: Any integer number
            ex. font_size=36
            
        Optional arguments:
            
        line spacing: Spacing between the top of a type row relative to the top
            of the row above it. Input in terms of {em}
            ex. leading=1.2 #(1.2em from the line above)
            
        indent size: Paragraph indentations in terms of {em}
            ex. indent=2 #(indented 2em from side margin)
            
        side margins: Number of pixels for the side margins
            ex. side_margin=150
            
        top margin: Number of pixels for the top (and bottom) margin
            ex. top_margin=250
            
        chapter numbering: Decimal or roman numeral chapter numbering
            ex. chapter_numbering='decimal'
            ex. chapter_numbering='roman'
                
        hyphenation: The program can hyphenate words to make the line fit better
            within the margins. 
            Three options exist for hyphenating: 'full', 'part', 'none'
            The 'full' option does a full search for prefixes and suffixes (slowest rendering)
            The 'part' option looks for only the most common prefixes and suffixes (faster rendering)
            The 'none' option does not hyphenate at all (fastest rendering)
            The default is full hyphenation.
            ex. hyphenation='full'
    
    The function will run through all .txt files in the directory and output
    numbered pages in the file format of your choice

        ex. file_type='pgm'

    Function call example:
                
        BOOK_TO_PGM(font_file=r"C:\Users\User\TrueTypeFonts\Serif_Zachery.otf", 
                    font_size=36, 
                    side_margin=150, 
                    top_margin=250, 
                    leading=1.2, 
                    indent=2, 
                    file_type='.pgm',
                    chapter_numbering='roman'
                    hyphenation='part'
                    )
    """    
    
    path= fd.askdirectory(title="Choose your book directory")
    file = [] #2#
    page_number = 1
    global start_time
    
    start_time = time.time()
    
    for i, file in enumerate(os.listdir(path)): #2#
    
        if fnmatch.fnmatch(file, '*.txt'): #2#   
            
            with open(path + '/' + file, 'r', encoding="utf8") as chapter:
                chapter = chapter.read()
            chapter = r"{}".format(chapter)
            chapter = CHAPTER_TO_PGM(font_file = font_file, 
                                     font_size = font_size, 
                                     file_name = path + '/' + file, 
                                     file_type = file_type,
                                     text = chapter,
                                     side_margin = side_margin, 
                                     top_margin = top_margin, 
                                     leading = leading, 
                                     indent = indent, 
                                     hyphenation = hyphenation,
                                     page_number = page_number)
            
            chapter.write_chapter()
            print("Chapter " + str(i+1) + " written (page " + str(chapter.page_number) + ")\n")
            page_number = chapter.page_number + 1

#---------------------------------------------------------------------
#   MAIN
#---------------------------------------------------------------------

# Need TrueType font (.ttf or .otf)
font_file = r"C:\Users\jriffle\Documents\Demos\charmr\TrueTypeFonts\Serif_DejaVu.ttf"
font_size = 40

BOOKTEXT_TO_IMAGE(font_file, 
            font_size, 
            side_margin=150, 
            top_margin=200, 
            leading=1.4, 
            indent=2, 
            file_type='.png',
            chapter_numbering='roman', # can be 'roman' or 'decimal'
            hyphenation='none'
            )
global start_time
print(time.time() - start_time)