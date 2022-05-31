import matplotlib.pyplot as plt
from collections.abc import MutableMapping
import cv2
import h5py
import numpy as np
import io
import sys
import os
import csv
from PIL import Image
import ujson
import pandas as pd
import datetime as dt
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo


class GUI:
    @staticmethod
    def show_end(info):
        root = tk.Tk()
        path = tk.messagebox.showinfo(title="Process finished", message=info)
        root.destroy()

    @staticmethod
    def select_file():
        root = tk.Tk()
        path = fd.askopenfilename(filetypes=[("EMD files", ".emd")], title="Choose .emd file to analyze")
        print('Opening "' + str(path) + '"')
        root.destroy()
        return path

    @staticmethod
    def save_file(type, initialfilename, windowtext, filetypeexclude = False):
        root = tk.Tk()
        types = []
        if type == "csv":
            types.append(("CSV file", ".csv"))
        if type == "jpeg" or type == "jpg":
            types.append(("JPEG file", ".jpg"))
        if type == "tif" or type == "tiff":
            types.append(("TIFF file", ".tif"))
        path = fd.asksaveasfilename(filetypes=types, initialfile = initialfilename, title=windowtext)
        if filetypeexclude:
            if "." + str(type) in path:
                ext = "." + str(type)
                path = path.replace(ext, '')
        else:
            if "." + str(type) not in path:
                path = path + "." + str(type)
        print("Saving " + str(path))
        root.destroy()
        return path

    @staticmethod
    def autoProcessAsk():
        root = tk.Tk()
        decision = tk.messagebox.askquestion('Auto Process', 'Would you like to perform auto-processing?', icon='question')
        root.destroy()
        return decision

class navigate:

    @staticmethod
    def getGroupsNames(group):
        items = []
        for item in group:
            if group.get(item, getclass=True) == h5py._hl.group.Group:
                items.append(group.get(item).name)
        print(items)

    @staticmethod
    def getGroup(group, item):
        if group.get(item, getclass=True) == h5py._hl.group.Group:
            return group.get(item)

    @staticmethod
    def getSubGroup(group, path):
        return group[path]

    @staticmethod
    def getDirectoryMap(group):
        for item in group:
            # check if group
            if group.get(item, getclass=True) == h5py._hl.group.Group:
                item = group.get(item)
                # check if emd_group_type
                # if 'emd_group_type' in item.attrs:
                print('found a group emd at: {}'.format(item.name))
                # process subgroups
                if type(item) is h5py._hl.group.Group:
                    navigate.getDirectoryMap(item)
                else:
                    print('found an emd at: {}'.format(item))
                    # print(type(item))

    @staticmethod
    def getMemberName(group, path):
        members = list(group[path].keys())
        if len(members) == 1:
            return str(members[0])
        else:
            return members

    @staticmethod
    def parseFileName(file):
        return str(file).split("/")[-1].split(".")[0]



class frameExporter:

    @staticmethod
    def checkPath(path, run=None):
        # Check whether the specified path exists or not
        isExist = os.path.exists(path)
        # Make directory if it does not exist.
        if run == "make":
            if not isExist:
                os.makedirs(path)
        # Remove directory if it does exist.
        elif run == "clear":
            if isExist:
                os.remove(path)
        # Otherwise return if dir exists.
        else:
            return isExist


    @staticmethod
    def saveAllFrames(h5pyfile, originalfilename, type="jpg", auto=False):
        if auto:
            # Make folder for frame images.
            folderpath = originalfilename + "/"
            os.makedirs(folderpath)
            path = str(folderpath) + navigate.parseFileName(originalfilename)
        else:
            path = GUI.save_file(type, navigate.parseFileName(originalfilename), "Choose folder to save images frames", filetypeexclude = True)
        print("Saveframes path: " + str(path))
        # Save files
        data = h5pyfile['Data/Image/' + navigate.getMemberName(h5pyfile, '/Data/Image/')]

        for i in range(len(data['Data'][0][0])):
            frame = np.array(data['Data'][:, :, i]).astype('uint8')
            rgbImage = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            outname = path + "_frame" + str(i) + "." + str(type)
            cv2.imwrite(outname, rgbImage)

class metadata:

    def __init__(self, h5pyfile):
        metalocation = navigate.getMemberName(h5pyfile, '/Data/Image/') # CAUTION, may break.
        self.meta = h5pyfile['/Data/Image/' + str(metalocation) + '/Metadata']
        self.nframes = self.meta.shape[1]
        self.transposed_meta = [list(i) for i in zip(*(self.meta[:]))]

    def convertASCII(self, frame):
        ascii_meta = self.transposed_meta[frame]
        metadata_text = ''.join(chr(i) for i in ascii_meta)
        ASCii = metadata_text.replace("\0", '')
        return ujson.loads(ASCii)

    @staticmethod
    def flattenAndCollect(jsondict, items):
        for _, v in jsondict.items():
            if isinstance(v, MutableMapping):
                metadata.flattenAndCollect(v, items)
            else:
                items.append(v)

    def getCSVmetadata(self, originalfilename, filter=None, auto=False):
        print("Parsing metadata.")
        if auto:
            pathname = str(originalfilename) + ".csv"
        else:
            pathname = GUI.save_file("csv", navigate.parseFileName(originalfilename), "Choose place to save metadata file")
        print("Saving metadata path: " + str(pathname))
        out = []
        cols = list(pd.json_normalize(self.convertASCII(0)).columns.values)

        for i in range(self.nframes):
            jsondict = self.convertASCII(i)
            items = []
            self.flattenAndCollect(jsondict, items)
            out.append(items)

        df = pd.DataFrame(out, columns = cols)
        if filter is None:
            print("No filter, outputting all metadata.")
            df.to_csv(pathname)
        else:
            print("Filtering metadata.")
            newdf = df[filter]
            newdf.to_csv(pathname)

    def getMetaAllFrames(self, query, printoption):
        out = []
        m = self.convertASCII(0)
        if printoption:
            for i in m:
                print(i)
                for g in m[i]:
                    print("--- " + str(g))

        for i in range(self.nframes):
            meta = self.convertASCII(i)
            if query == 'mag':
                out.append(meta['CustomProperties']['StemMagnification']['value'])
            elif query == 'sclbr':
                out.append(meta['BinaryResult']['PixelSize']['width'])  # x and y should be the same
                out.append(meta['BinaryResult']['PixelUnitX'])
            else:
                out.append('NA')
        return out
