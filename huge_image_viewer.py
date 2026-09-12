import cv2
import numpy as np
import os
import time
import mmap
import io
from PIL import Image
import pygame
from pygame.locals import KEYDOWN, K_q
from io import BytesIO
import math
import matplotlib as plt
import pygame_widgets
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame_widgets.toggle import Toggle
import struct

#this will use pygame to populate a grid which when a square is pressed will cause an image file to be parsed to display the image in that grid area
#the most complicated part about this is that the image is stored as a flat array so we need to handle everything relating to dimension manually...

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
DRKGREY = (160, 160, 160)
GREY = (100, 100, 100)


#the grid here will be array backed grid so that in future could become non binary (ex image fail to capture should be red not green or something)
class gridtracker:
    def __init__(self, _rows, _cols, _MARGIN):
        self.MARGIN = 2
        self.rows = _rows
        self.cols = _cols
        self.grid = []
        self.eventflag = False
        self.row = 0
        self.column = 0
        self.screengridwidth = 400
        self.screengridheight = 400
        pygame.init()
        pygame.mixer.quit() #Funny little behavior, when initialized pygame starts an audio module which will grab attention of any mic or speaker which can be annoying so disable it at beginning so you can listen to podcasts while running this program
        pygame.display.set_caption('Huge image viewer')

        for row in range(self.rows):
            self.grid.append([])
            for column in range(self.cols):
                self.grid[row].append(0)  # Append a cell

        self.screen = pygame.display.set_mode([1900,1000])
        self.HEIGHT = int((self.screengridheight-(self.rows+1)*self.MARGIN)/self.rows)
        self.WIDTH = int((self.screengridwidth-(self.cols+1)*self.MARGIN)/self.cols)
        self.done = False
        self.clock = pygame.time.Clock()

    def checkforevent(self):
        events = pygame.event.get()
        pygame_widgets.update(events)
        self.sliderout.setText(self.slider.getValue())

        if self.slider.getValue() != self.prevsli or self.toggle.getValue() != self.prevtog:
            self.prevsli = self.slider.getValue()
            self.prevtog = self.toggle.getValue()
            self.eventflag = True
        pygame.display.update()

        for event in events:
            if event.type == pygame.QUIT:
                self.done = True
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.grid[self.row][self.column] = 0
                        self.column = self.column -1
                        self.grid[self.row][self.column] = 1
                    if event.key == pygame.K_RIGHT:
                        self.grid[self.row][self.column] = 0
                        self.column = self.column + 1
                        self.grid[self.row][self.column] = 1
                    if event.key == pygame.K_DOWN:
                        self.grid[self.row][self.column] = 0
                        self.row = self.row+1
                        self.grid[self.row][self.column] = 1
                    if event.key == pygame.K_UP:
                        self.grid[self.row][self.column] = 0
                        self.row = self.row - 1
                        self.grid[self.row][self.column] = 1
                    self.eventflag = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    colloc = pos[0] // (self.WIDTH + self.MARGIN)
                    rowloc = pos[1]//(self.HEIGHT + self.MARGIN)
                    if pos[0] < self.screengridwidth and pos[1] < self.screengridheight:
                        self.grid[self.row][self.column] = 0
                        self.column = colloc
                        self.row = rowloc
                        self.grid[self.row][self.column] = 1
                        self.eventflag = True
                #print("current view: " + str(self.row) + "," + str(self.column))

    def newevent(self):
        # Set the screen background
        self.screen.fill(GREY)

        for row in range(self.rows):
            for column in range(self.cols):
                color = WHITE
                if self.grid[row][column] == 1:
                    color = GREEN
                pygame.draw.rect(self.screen,
                                 color,
                                 [(self.MARGIN + self.WIDTH) * column + self.MARGIN,
                                  (self.MARGIN + self.HEIGHT) * row + self.MARGIN,
                                  self.WIDTH,
                                  self.HEIGHT])

        # Limit to 60 frames per second
        self.clock.tick(60)
        #self.drawbuttons()
        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

    def drawbuttons(self):
        self.toggle = Toggle(self.screen, 25, 455, 100, 40, startOn = True)
        self.userset_xtiles = TextBox(self.screen, 155, 450, 200, 50, fontSize=30)
        self.output = TextBox(self.screen, 155, 450, 200, 50, fontSize=30)
        self.output.disable()
        self.output.setText("raw")
        self.slider = Slider(self.screen, 5, 400, 250, 6, min=0, max=0.8, step=0.05, initial=0, handleColour=(200,0,0))
        self.sliderout = TextBox(self.screen, 260, 400, 75, 50, fontSize=30)
        self.sliderout.disable()
        self.prevsli = self.slider.getValue()
        self.prevtog = self.toggle.getValue()
        self.button = Button(self.screen, 40, 700, 100, 50, text='Quit', fontSize=30, margin=20, inactiveColour=(200, 50, 0), hoverColour=(150, 0, 0), pressedColour=(0, 200, 20), radius=20, onClick=lambda: self.quit() )

    def quit(self):
        print("quit")
        newgrid.done = True

#prototype a memory map method for reading a massive image file without opening it... This way we can load image into
#os.chdir("C:\\main\\FemtoTest\\WaferOpticalInspection\\Branch\\Python_implementation\\images\\2022-03-29 14_32_54\\renumbered_images_for_IJ")  # /autotimed
#os.chdir("C:\\main\\FemtoTest\\WaferOpticalInspection\\Branch\\Python_implementation\\images\\2022-03-29 14_32_54\\img_subsample")
os.chdir("G:\\")
cwd = os.getcwd()
os.chdir(cwd)

# imagestringraw = "full_42x15.raw"
# ydim = 12869
# xdim = 43584

#imagestringraw = "fused_python_col88_dontdelete_mod.raw"
imagestringraw = "blank.raw"
ydim = 1024 * 100
xdim = 1280 * 83

tilesx = 30 #40#
tilesy = 40 # 10#
#tileoverlap = 0.4
tilehorioverlap = 0.2
tilevertoverlap = 0.35
margin = 1

newgrid = gridtracker(int(tilesy), int(tilesx), margin)
newgrid.newevent()
newgrid.drawbuttons()


with open(imagestringraw, "rb") as f: #using the with open has some good handling benefits... Might also offer some file io reading speed improvements
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    while not newgrid.done:
        if newgrid.slider.getValue() != 0:
            tilehorioverlap = newgrid.slider.getValue()
            tilevertoverlap = newgrid.slider.getValue()

        xtiledim = int(xdim / (tilesx * (1 - tilehorioverlap) - tilehorioverlap))  # 4700 hardcoded 106280/50 = 2125 remainder 30 #
        ytiledim = int(ydim / (tilesy * (1 - tilevertoverlap) - tilevertoverlap))  # int(ydim/tilesy)#

        newgrid.checkforevent()

        if newgrid.eventflag:
            timestart = time.time()
            timestartevent = time.time()
            newgrid.eventflag = False
            newgrid.newevent()
            xindex = newgrid.column
            yindex = newgrid.row

            # seek to beginning of valid data
            findstart = xtiledim * xindex * (1 - tilehorioverlap) + xdim * (int(yindex * ytiledim * (1 - (tilevertoverlap))))  # + xdim*ytiledim*yindex # 25120 = xindex xtiledim #find s tart in top left #xindex * xtiledim
            mm.seek(int(findstart), 1)

            counter = 1
            stop = ytiledim
            data = "".encode()
            timestart = time.time()
            nextstart = xdim - xtiledim

            #instead of concatenating each row to previous we will create a list of rows and then join the list at the end!!!
            #this join alternative provides improvements that are orders ofmagnitude faster because python's native concatenate function copies the variable each iteration which is very costly for large strings
            appendeddata = []
            #while loop faster than for in range looping... nearly twice as fast idk why
            while counter < stop:
                try:
                    appendeddata.append(mm.read(int(xtiledim))) #this limits our speed not io bound
                    mm.seek(int(nextstart), 1)
                    counter = counter + 1
                except:
                    break

            data = b''.join(appendeddata)
            print("finish time: " + str(time.time() - timestart) + " image dimensions: " + str(xtiledim) + "x" + str(ytiledim))

            timestart = time.time()

            #for very large images this is slow but working with pil images is very convenient...
            newimagedata = Image.frombytes("L", (xtiledim, int(len(data) / xtiledim)),data).convert("RGBA")  # convert chunk from bytes into a PIL image with rgba so it can be easily

            if newgrid.toggle.getValue() == False:
                sizenew = (1000, 1000)
                newimagedata.thumbnail(sizenew, Image.ANTIALIAS)
                newgrid.output.setText("1000 pix wide")
            else:
                newgrid.output.setText("raw")
            print("Time spent resizing image: " + str(time.time() - timestart))

            #py_image = pygame.image.frombuffer(data, (xtiledim, int(len(data) / xtiledim)), 'P')
            #if you happen to know the image dimesnions you could
            py_image = pygame.image.frombuffer(newimagedata.tobytes(), newimagedata.size, newimagedata.mode)#newimagedata.tobytes(), newimagedata.size, newimagedata.mode
            imsurface = py_image.convert()
           # plt.pyplot.imshow(py_image)
            newgrid.screen.blit(py_image, (400, 10))
            pygame.display.update()
            mm.seek(0, 0)
            print("Total event finish time: " + str(time.time() - timestartevent))

pygame.quit()
f.close()

