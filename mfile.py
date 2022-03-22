"""
Created on March 2022
@author: Negar Golestani
"""


import pandas as pd
import numpy as np
import cv2
import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime




####################################################################################################################################
class GUI(object):     
    def __init__(self, csv_path, size=1200):             

        self.csv_path = csv_path
        self.size = size
        self.data_df = pd.read_csv(csv_path)

        self.overlay() 
        self.next()
        self.set()
        self.root.mainloop()

        return  
    #--------------------------------------------------------------------------------------
    def overlay(self):
        self.root = tk.Tk() 
        self.root.title('Main') 

        self.background = tk.Canvas(self.root, borderwidth=0, height=self.size, width=self.size)
        self.container = self.background.create_rectangle(0, 0, self.size, self.size, width=0)

        self.buttons = tk.Frame(self.root)
        self.buttons.pack(side=tk.TOP)

        tk.Label(self.buttons, text="Rotation Angle:").pack(side=tk.LEFT) 
        self.entry = tk.Entry(self.buttons, bd=5)
        self.entry.pack(side=tk.LEFT) 
        tk.Button(self.buttons, text='Rotate', command=lambda: self.entry_rotate()).pack(side=tk.LEFT)  

        tk.Button(self.buttons, text='1 Deg (CW)', command=lambda: self.rotate(-1)).pack(side=tk.LEFT)  
        tk.Button(self.buttons, text='1 Deg (CCW)', command=lambda: self.rotate(1)).pack(side=tk.LEFT)  
        tk.Button(self.buttons, text='flip', command=lambda: self.flip()).pack(side=tk.LEFT)  
        tk.Button(self.buttons, text='Save', command=lambda: self.save()).pack(side=tk.RIGHT)  


        self.background.bind('<ButtonPress-1>', lambda event: self.background.scan_mark(event.x, event.y))
        self.background.bind('<B1-Motion>', lambda event: self.background.scan_dragto(event.x, event.y, gain=1))
        self.background.bind('<MouseWheel>', lambda event: self.zoom(event)) 

        return                                
    #--------------------------------------------------------------------------------------
    def next(self):
        if not hasattr(self, 'idx'): self.idx = 0
        while True:            
            if self.data_df.loc[self.idx].isnull().values.any(): break
            else: self.idx +=1
        if self.idx == len(self.data_df): self.root.destroy()
        return
    #--------------------------------------------------------------------------------------
    def set(self):
        self.root.title(self.idx)
        image_dir = self.data_df.loc[self.idx, 'image'].replace('data_processed', 'Y:') # <<<<<<<< UPDATE >>>>>>>>>>
        self.image = cv2.imread(image_dir)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)     
        self.cval = np.median(np.concatenate([ self.image[0,:], self.image[-1,:], self.image[:,0], self.image[:,-1] ], axis=0), axis=0)   
        H, W = self.image.shape[:2]
        top, bottom, left, right = 0, 0, 0 ,0        
        if W - H > 1:  top, bottom = [ int((W-H)/2) ]*2
        elif H - W > 1:  left, right = [ int((H-W)/2) ]*2
        self.image = cv2.copyMakeBorder(self.image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=self.cval)  
        self.scale = self.size / self.image.shape[0]
        self.refresh()

        self.rotAng_deg = 0
        self.flipping = False
        self.time_start = datetime.now()               
        return
    #--------------------------------------------------------------------------------------
    def refresh(self):  
        image = cv2.resize(self.image, None, fx=self.scale, fy=self.scale).astype(np.uint8)        
        self.background.image = ImageTk.PhotoImage(Image.fromarray(image))
        self.background.create_image(0, 0, image=self.background.image, anchor=tk.NW)
        self.background.pack(side=tk.BOTTOM)
        return  
    #--------------------------------------------------------------------------------------
    def entry_rotate(self):
        rotAng_deg = self.entry.get()
        if rotAng_deg != '': 
            self.rotate( int(rotAng_deg) )
            self.entry.delete(0, tk.END)
        return
    #--------------------------------------------------------------------------------------
    def rotate(self, rotAng_deg):
        height, width = self.image.shape[:2]    
        image_center = (width/2, height/2)     
        rotation_mat = cv2.getRotationMatrix2D(image_center, rotAng_deg, 1.)
        self.image = cv2.warpAffine(self.image, rotation_mat, (width, height), borderMode=cv2.BORDER_CONSTANT, borderValue=self.cval)

        self.rotAng_deg += rotAng_deg
        self.refresh()
        return
    #--------------------------------------------------------------------------------------
    def flip(self):
        self.image = cv2.flip(self.image, 1)

        self.refresh()
        self.flipping =  not self.flipping  
        return
    #--------------------------------------------------------------------------------------
    def zoom(self, event, delta=1.1, min_pxl=30):
        x = self.background.canvasx(event.x)
        y = self.background.canvasy(event.y)
        bbox = self.background.bbox(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass    # Is inside the image
        else: return                                                # zoom only inside image area
        
        scale = 1.0
        # scroll down
        if event.num == 5 or event.delta == -120:  
            i = min(self.size, self.size)
            if int(i * self.scale) < min_pxl: return    # image is less than min_pxl pixels
            self.scale /= delta
            scale      /= delta
        # scroll up
        elif event.num == 4 or event.delta == 120:  
            i = min(self.background.winfo_width(), self.background.winfo_height())
            if i < self.scale: return                   # 1 pixel is bigger than the visible area
            self.scale *= delta
            scale      *= delta

        self.background.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.refresh()   
                 
        return        
    #--------------------------------------------------------------------------------------
    def save(self):
        self.data_df.loc[self.idx, 'estimated angle'] = int(self.rotAng_deg)
        self.data_df.loc[self.idx, 'estimated flipping'] = int(self.flipping)
        self.data_df.loc[self.idx, 'time'] = (datetime.now()- self.time_start).total_seconds()
        self.data_df.to_csv( self.csv_path )

        self.idx += 1
        self.set()
####################################################################################################################################
if __name__ == '__main__':
    interface = GUI( './data/data_testing.csv' )
####################################################################################################################################

