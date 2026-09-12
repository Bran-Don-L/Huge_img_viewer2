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
import matplotlib.pyplot as plt
import pygame_widgets
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame_widgets.toggle import Toggle
import struct

#this will use pygame to populate a grid which when a square is pressed will cause an image file to be parsed to display the image in that grid area
#the most complicated part about this is that the image is stored as a flat array so we need to handle everything relating to dimension manually...



#prototype a memory map method for reading a massive image file without opening it... This way we can load image into
#os.chdir("C:\\main\\FemtoTest\\WaferOpticalInspection\\Branch\\Python_implementation\\images\\2022-03-29 14_32_54\\renumbered_images_for_IJ")  # /autotimed
#os.chdir("C:\\main\\FemtoTest\\WaferOpticalInspection\\Branch\\Python_implementation\\postprocessing\\Image_stitcher")
os.chdir("G:\\")
cwd = os.getcwd()
os.chdir(cwd)

# imagestringraw = "full_42x15.raw"
# ydim = 12869
# xdim = 43584

#imagestringraw = "fused_python_col88_dontdelete_mod.raw"
imagestringraw = "blank.raw"
ydim = 1024 * 100#100
xdim = 1280 * 83#83

tilesx = 10#50 #40#
tilesy = 20#70 # 10#
#tileoverlap = 0.4
tilehorioverlap = 0
tilevertoverlap = 0
margin = 1

thumb_nail = Image.new('RGBA', (tilesx*400, tilesy*193))


with open(imagestringraw, "rb") as f: #using the with open has some good handling benefits... Might also offer some file io reading speed improvements which is a major bottleneck of this method
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

    xtiledim = int(xdim / (tilesx * (1 - tilehorioverlap) - tilehorioverlap))  # 4700 hardcoded 106280/50 = 2125 remainder 30 #
    ytiledim = int(ydim / (tilesy * (1 - tilevertoverlap) - tilevertoverlap))  # int(ydim/tilesy)#

    timestart = time.time()
    timestartevent = time.time()

    xindex = 1
    yindex = 1

    for yindex in range(tilesy):
        for xindex in range(tilesx):

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

            sizenew = (400, 400)
            newimagedata.thumbnail(sizenew, Image.BILINEAR)

            h,w = newimagedata.size

            print("width: ", w)
            print("height: ", h)

            print("Time spent resizing image: " + str(time.time() - timestart))

            #py_image = pygame.image.frombuffer(data, (xtiledim, int(len(data) / xtiledim)), 'P')
            #if you happen to know the image dimesnions you could
            #py_image = pygame.image.frombuffer(newimagedata.tobytes(), newimagedata.size, newimagedata.mode)#newimagedata.tobytes(), newimagedata.size, newimagedata.mode
            #imsurface = py_image.convert()

            thumb_nail.paste(newimagedata, (xindex*400,yindex*193))
            #plt.imshow(newimagedata)
            #plt.show()
            mm.seek(0, 0)
            print("Total event finish time: " + str(time.time() - timestartevent))
    plt.imshow(thumb_nail)
    plt.show()
f.close()

