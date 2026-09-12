from __future__ import print_function
import matplotlib.pyplot as plt
import cv2
import numpy as np
import os
import time
from PIL import Image
import mmap


##homography using image template matching (this would be very fast but relies on
class homography_calculator:
    def __init__(self, template_, threshold_):
        self.template = template_
        self.threshold = threshold_

    def calculate_displacement(self, img1_, img2_):
        found1 = self.findreference_bytemplatematch(img1_)
        found2 = self.findreference_bytemplatematch(img2_)
        if found1 and found2:
            return tuple(map(lambda i, j: i - j, found1, found2))

    def findreference_bytemplatematch(self, newimagedata):
        self.template = np.array(self.template)
        img = np.array(newimagedata)
        res = cv2.matchTemplate(img, self.template, eval('cv2.TM_CCOEFF_NORMED'))
        ret, threshimg = cv2.threshold(res, self.threshold, 1, cv2.THRESH_BINARY)

        imgeroded = cv2.dilate(threshimg, None, iterations=2)
        threshimg = imgeroded.astype(np.uint8)

        contours, hier = cv2.findContours(threshimg, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contourcount = 0

        for contour in contours:
            contourcount = contourcount + 1
            x, y, w, h = cv2.boundingRect(contour)
            # print("(" + str(x) + "," + str(y) + ")")
            cv2.rectangle(img, (x, y), (x + 200, y + 300), (255, 255, 255), 1)
        if contours:
            return (x, y)

    def calculate_displacement_homography(self, img1_, img2_):

        # img1_ = cv2.imread("image3231.tiff", 0) #img1 (right)
        # img2_ = cv2.imread("image3232.tiff", 0)

        sift = cv2.xfeatures2d.SIFT_create()

        masked1 = np.zeros((img1_.shape[0], img1_.shape[1]), np.uint8)
        masked2 = np.zeros((img2_.shape[0], img2_.shape[1]), np.uint8)

        masked1[0:1023, 0:261] = img1_[0:1023, 0:261]
        masked2[0:1023, 1279 - 261:1279] = img2_[0:1023, 1279 - 261:1279]

        kp1, des1 = sift.detectAndCompute(masked1, None)
        kp2, des2 = sift.detectAndCompute(masked2, None)

        try:

            match = cv2.BFMatcher()
            matches = match.knnMatch(des2, des1, k=2)

            good = []
            for m, n in matches:
                if m.distance < 0.3 * n.distance:
                    print(m.distance/n.distance)
                    good.append(m)  # append match indexes

            MIN_MATCHES = 1
            xdisp = []
            ydisp = []

            # img3 = cv2.drawMatches(img2_, kp2, img1_, kp1, good, None, flags=2)
            # plt.imshow(img3)
            # plt.show()

            if len(good) > MIN_MATCHES:
                for z in good:
                    # print("x translation: " + str(kp2[z.queryIdx].pt[0] - kp1[z.trainIdx].pt[0]))
                    # print("y translation: " + str(kp2[z.queryIdx].pt[1] - kp1[z.trainIdx].pt[1]))
                    if kp2[z.queryIdx].pt[1] - kp1[z.trainIdx].pt[1] > 5 and kp2[z.queryIdx].pt[1] - kp1[z.trainIdx].pt[1] < 30 and kp2[z.queryIdx].pt[0] - kp1[z.trainIdx].pt[0] > 1000 and kp2[z.queryIdx].pt[0] - kp1[z.trainIdx].pt[0] < 1050:
                        xdisp.append(kp2[z.queryIdx].pt[0] - kp1[z.trainIdx].pt[0])
                        ydisp.append(kp2[z.queryIdx].pt[1] - kp1[z.trainIdx].pt[1])
                xavg = sum(xdisp) / len(xdisp)
                yavg = sum(ydisp) / len(ydisp)
                return (xavg, yavg)
            else:
                print("not enough matches")
        except:
            print("other error")




class displace:
    def __init__(self, xdim_, ydim_, xdisp2_, ydisp2_, file):
        self.xdim = xdim_
        self.ydim = ydim_
        self.xdisp = 0
        self.ydisp = 0

        #create a raw file if it is not there yet and close
        with open(file, 'w') as f:
            pass
        #take the file we just created and memory map to it
        #self.image = np.zeros((self.ydim + 20, self.xdim + 40), np.uint8)
        with open(file,"r+") as f:  # using the with open has some good handling benefits... Might also offer some file io reading speed improvements
            self.mm = mmap.mmap(f.fileno(), self.xdim*self.ydim, access=mmap.ACCESS_WRITE)
        # self.image[:,:] = 10
        # self.image = np.array((self.ydim + 20, self.xdim+40), np.uint8)
        self.xdisp2 = xdisp2_
        self.ydisp2 = ydisp2_
        # self.image[0:root.shape[0], 0:root.shape[1]] = root
        self.counter = 1

    def fuse(self, img2, xind, rownum, xdisp_, ydisp_):
        self.xdisp = self.xdisp + xdisp_
        self.ydisp = self.ydisp + ydisp_

        rowydisp = self.ydisp
        rowxdisp = self.xdisp
        colydisp = self.ydisp2
        colxdisp = self.xdisp2

        origsize = self.mm.size()

        self.mm.resize(origsize + img2.shape[0] * img2.shape[1])

        y1, y2 = int(rowydisp + colydisp), int(rowydisp + colydisp + img2.shape[0])
        x1, x2 = int(rowxdisp + colxdisp), int(rowxdisp + colxdisp + img2.shape[1])

        findstart = x1 + self.xdim * y1
        self.mm.seek(int(findstart), 0)

        counter = 0
        nextstart = self.xdim - img2.shape[1]
        appendeddata = []
        # while loop faster than for in range looping... nearly twice as fast idk why

        timetoadd = time.time()
        collectrowdata = []
        collectrowdata = np.count_nonzero(img2, axis=1)

        print(np.count_nonzero(img2, axis = 1))


        while counter < img2.shape[0]:
            if counter > img2.shape[0]/2:
                offset = img2.shape[1] - collectrowdata[counter]
            elif counter < 5:
                offset = img2.shape[1] + collectrowdata[counter]
            else:
                offset = 0

            # if counter < 5:

            try:
                self.mm.seek(offset, 1)
                row = img2[counter, offset:img2.shape[1]]

                #appendeddata.append(self.mm.read(int(self.xtiledim)))  # this limits our speed not io bound
                self.mm.write(row)
                self.mm.seek(int(nextstart), 1)
                counter = counter + 1
            except:
                break

        print("time to add: " + str(time.time() - timetoadd))
        #self.image[y1:y2, x1:x2] = img2
        #self.image = self.image.astype(np.uint8)
        self.counter = self.counter + 1




def main():
    os.chdir("C:\\main\\FemtoTest\\WaferOpticalInspection\\Branch\\Python_implementation\\images\\2022-03-29 14_32_54\\img_subsample")  # /autotimed
    cwd = os.getcwd()
    os.chdir(cwd)

    template = cv2.imread("homographymap.tif", 0)
    img1 = cv2.imread("image3231.tiff", 0)
    img2 = cv2.imread("image3232.tiff", 0)

    img1 = cv2.imread("image3196.tiff", 0)
    img2 = cv2.imread("image3197.tiff", 0)

    os.chdir("C:\\main\\FemtoTest\\WaferOpticalInspection\\Branch\\Python_implementation\\images\\2022-03-29 14_32_54\\renumber_forpy")  # /autotimed
    cwd = os.getcwd()
    os.chdir(cwd)


    star = time.time()
    counter = 0
    ###yindex odd means we need a negative x stepping direction!!!
    xaxisstepdirection = "-"
    index_y = 104

    yrowshift = 1028 - 216
    xrowshift = -9 + 4

    # ydisplacement = 1259-640#542-446
    # xdisplacement = 30711 - 28537#28546-27464

    # newimage = displace(1280 * 89, 1024*13, xdisplacement, ydisplacement, 11, (1259-640) ,img1 #(1259 - 640)
    newimage = displace(1280 * 83, 1024 * 50, xrowshift, yrowshift, "C:\\main\\FemtoTest\\WaferOpticalInspection\\Branch\\Python_implementation\\images\\2022-03-29 14_32_54\\img_subsample\\blank.raw")  # 218
    #print("adding: " + str(83) + "," + str(6) + ".tiff")

    rownum = 0
    index_x = 60
    index_x = 83
    while index_y >= 1:
        while index_x >= 1:  # 1

            # img1 = cv2.imread(str(index_x) + "," + str(index_y) + ".tiff", 0)
            # img2 = cv2.imread(str(index_x + 1) + "," + str(index_y) + ".tiff", 0)
            # # result1 = img1
            # # result2 = img2
            #
            # image_center = tuple(np.array(img1.shape[1::-1]) / 2)
            # rot_mat = cv2.getRotationMatrix2D(image_center, 0.31, 1.0)
            # result1 = cv2.warpAffine(img1, rot_mat, img1.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
            #
            # image_center = tuple(np.array(img2.shape[1::-1]) / 2)
            # rot_mat = cv2.getRotationMatrix2D(image_center, 0.31, 1.0)
            # result2 = cv2.warpAffine(img2, rot_mat, img2.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
            #
            # star = time.time()
            # homography = homography_calculator(template, 0.85)
            # # difference = homography.calculate_displacement(img2, img1)
            # difference = homography.calculate_displacement_homography(result1, result2)
            # #print(difference)
            # print("homography time: " + str(time.time() - star))
            difference = (1015, 6)

            if difference:
                ydisplacement = int(difference[1])
                #ydisplacement = 5
                xdisplacement = int(difference[0])
                print("displacement: " + str(xdisplacement) + ", " + str(ydisplacement) )

                print("adding: " + str(index_x) + "," + str(index_y) + ".tiff")
                star2 = time.time()

                img3 = cv2.imread(str(index_x) + "," + str(index_y) + ".tiff", 0)
                #result2 = img3
                ###img3 = Image.open(str(index_x) + "," + str(index_y) + ".tiff")
                image_center = tuple(np.array(img3.shape[1::-1]) / 2)
                rot_mat = cv2.getRotationMatrix2D(image_center, 0.31, 1.0)
                result2 = cv2.warpAffine(img3, rot_mat, img3.shape[1::-1], flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
                #cv2.imwrite("C:\\main\\FemtoTest\\WaferOpticalInspection\\Branch\\Python_implementation\\images\\2022-03-29 14_32_54\\img_subsample\\temp.tiff", result2)


                newimage.fuse(result2, index_x, rownum, xdisplacement, ydisplacement)
                counter = counter + 1
                # cv2.resize(newimage.image, (0, 0), fx=0.5, fy=0.5)
                # imgplot = plt.imshow(1 - newimage.image, cmap='Greys')
                # plt.show()
                print("added " + str(counter) + " took:" + str(time.time() - star2))
                #cv2.imwrite("C:\\main\\FemtoTest\\WaferOpticalInspection\\Branch\\Python_implementation\\images\\2022-03-29 14_32_54\\img_subsample\\aaafused_python_col" + str(index_y) + ".tiff", newimage.image)

            if xaxisstepdirection == "+":
                index_x = index_x + 1
            else:
                index_x = index_x - 1
            #index_x = 70
            rownum = rownum + 1
            #print("rowstitch time: " + str(time.time() - star))

            # cv2.resize(newimage.image, (0, 0), fx=0.5, fy=0.5)
            # imgplot = plt.imshow(1 - newimage.image, cmap='Greys')
            # plt.show()
            #index_y = index_y - 1
            pass
        index_x = 83
        newimage.ydisp = 0
        newimage.xdisp = 0
        newimage.ydisp2 =  newimage.ydisp2 + yrowshift
        newimage.xdisp2 = newimage.xdisp2 + xrowshift
        index_y = index_y - 1
    # cv2.imwrite(
    #     "C:\\main\\FemtoTest\\WaferOpticalInspection\\Branch\\Python_implementation\\images\\2022-03-29 14_32_54\\img_subsample\\fused_python_DONE.tiff",
    #     newimage.image)

    print("Total runtime: " + str(time.time() - star))

if __name__ == '__main__':
    main()



