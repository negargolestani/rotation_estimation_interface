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
    def __init__(self, csv_path, size=1200, replace_dict=dict()):             

        self.csv_path = csv_path
        self.size = size
        self.replace_dict = replace_dict
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
        self.entry = tk.Entry(self.buttons, bd=5, width=10)
        self.entry.insert(tk.END, '10')
        self.entry.pack(side=tk.LEFT) 
        tk.Button(self.buttons, text='Rotate', width=10, command=lambda: self.rotate()).pack(side=tk.LEFT)  
        tk.Button(self.buttons, text='flip', width=10, command=lambda: self.flip()).pack(side=tk.LEFT)  
        tk.Button(self.buttons, text='Save', width=10, command=lambda: self.save()).pack(side=tk.RIGHT)  


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
        # Update image directory
        image_dir = self.data_df.loc[self.idx, 'image']
        for key, val in self.replace_dict.items(): image_dir = image_dir.replace(key, val) 

        # load image
        self.image = cv2.imread(image_dir)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)  

        # make imge square (for rotation)   
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
        self.root.title(self.idx)

        image = cv2.resize(self.image, None, fx=self.scale, fy=self.scale).astype(np.uint8)        
        self.background.image = ImageTk.PhotoImage(Image.fromarray(image))
        self.background.create_image(0, 0, image=self.background.image, anchor=tk.NW)
        self.background.pack(side=tk.BOTTOM)
        return  
    #--------------------------------------------------------------------------------------
    def rotate(self):
        rotAng_deg = self.entry.get()
        if rotAng_deg.lstrip('-+').isdigit(): 
            rotAng_deg = -int(rotAng_deg)
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
        rotAng_deg = int(self.rotAng_deg)
        self.data_df.loc[self.idx, 'estimated angle'] = np.sign(rotAng_deg)*(np.abs(rotAng_deg)%360)
        self.data_df.loc[self.idx, 'estimated flipping'] = int(self.flipping)
        self.data_df.loc[self.idx, 'time'] = (datetime.now()- self.time_start).total_seconds()
        self.data_df.to_csv( self.csv_path, index=False )

        self.idx += 1
        self.set()
####################################################################################################################################







# black ink on left  -  blue ink on right 


if __name__ == '__main__':

    csv_path = './data/data_testing.csv'
    replace_dict = {'data_processed':'Y:'}

    interface = GUI( csv_path, replace_dict=replace_dict )

