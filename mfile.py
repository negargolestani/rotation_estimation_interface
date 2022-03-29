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
import os


####################################################################################################################################
class GUI(object):     
    def __init__(self, csv_path, replace_dict=dict()):             
        
        self.set_input(csv_path, replace_dict)
        self.set_overlay() 
        self.set_clock()

        self.start()
        self.root.mainloop()

        return                         
    #--------------------------------------------------------------------------------------
    def set_input(self, csv_path, replace_dict):
        self.csv_path = csv_path
        self.replace_dict = replace_dict        
        self.data_df = pd.read_csv(csv_path)

        self.idx = 0
        self.start_time = None 
        return
    #--------------------------------------------------------------------------------------
    def set_overlay(self, size=1000):
        self.root = tk.Tk() 

        self.size = size
        self.background = tk.Canvas(self.root, borderwidth=0, height=self.size, width=self.size)
        self.container = self.background.create_rectangle(0, 0, self.size, self.size, width=0)
    

        sub_frame = tk.Frame(self.root)
        sub_frame.place(relx=0.01, rely=0.01)
        tk.Button(sub_frame, text='BACK', width=15, height=3, command=lambda: self.set_frame(self.idx-1)).grid()

        sub_frame = tk.Frame(self.root)
        sub_frame.place(relx=.87, rely=0.01)
        tk.Button(sub_frame, text='NEXT', width=15, height=3, command=lambda: self.set_frame(self.idx+1)).grid()


        sub_frame = tk.Frame(self.root)
        sub_frame.place(relx=.5, rely=0, anchor=tk.N)

        # self.time_disp = tk.Label(sub_frame, width=20,  text="")
        self.time_disp = tk.Button(sub_frame, text='Stop', width=20, command=self.stop)
        self.time_disp.grid(row=0, column=0)
        # tk.Button(sub_frame, text='Stop', width=10, command=self.stop).grid(row=0, column=1) 


        sub_frame = tk.Frame(self.root)
        sub_frame.place(relx=.5, rely=0.055, anchor=tk.S)
       
        tk.Button(sub_frame, text='CCW Rotate', width=10, command=lambda: self.rotate(int(self.entry.get()))).grid(row=0, column=0)    
        self.entry = tk.Entry(sub_frame, bd=5, width=5, validate='all', validatecommand=((self.root.register(check_digit_entry)),'%P')) 
        self.entry.insert(tk.END, '5')
        self.entry.grid(row=0, column=1) 
        tk.Button(sub_frame, text='CW Rotate', width=10, command=lambda: self.rotate(-int(self.entry.get()))).grid(row=0, column=2)  
        tk.Button(sub_frame, text='flip', width=10, command=self.flip).grid(row=0, column=3)  
        tk.Button(sub_frame, text='Save', width=10, command=self.save).grid(row=0, column=4) 
        tk.Button(sub_frame, text='Reset', width=10, command=lambda: self.set_frame(self.idx, reload=False)).grid(row=0, column=5) 
        # tk.Button(sub_frame, text='Stop', width=10, command=self.stop).grid(row=0, column=6) 


        sub_frame = tk.Frame(self.root)
        sub_frame.place(relx=.5, rely=0.08, anchor=tk.S)
        self.tnf_frame = tk.Label(sub_frame, width=50,  text="")
        self.tnf_frame.grid()

        # Bindings
        self.background.bind('<ButtonPress-1>', lambda event: self.background.scan_mark(event.x, event.y))
        self.background.bind('<B1-Motion>', lambda event: self.background.scan_dragto(event.x, event.y, gain=1))
        self.background.bind('<MouseWheel>', lambda event: self.zoom(event)) 

        return   
    #--------------------------------------------------------------------------------------
    def set_clock(self):
        if self.start_time is not None: self.time = int((datetime.now()- self.start_time).total_seconds())
        else: self.time = 0
        self.time_disp.configure(text=f"{self.time} (Press to Stop)")
        self.root.after(100, self.set_clock)   
    #--------------------------------------------------------------------------------------
    def set_frame(self, idx, reload=True):
        self.idx = idx
        self.rotAng_deg = 0
        self.flipping = False
        
        # Load data
        image_dir = self.data_df.loc[idx, 'image']
        for key, val in replace_dict.items(): image_dir = image_dir.replace(key, val) 
        self.image = cv2.cvtColor(cv2.imread(image_dir), cv2.COLOR_BGR2RGB)  

        # make imge square (for rotation)   
        self.cval = np.median(np.concatenate([ self.image[0,:], self.image[-1,:], self.image[:,0], self.image[:,-1] ], axis=0), axis=0)   
        H, W = self.image.shape[:2]
        top, bottom, left, right = [ int(.2*np.max([H, W]))] * 4   
        if W - H > 1:  
            top += int((W-H)/2) 
            bottom += int((W-H)/2)
        elif H - W > 1:  
            left += int((H-W)/2)
            right += int((H-W)/2) 
        self.image = cv2.copyMakeBorder(self.image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=self.cval)  
        self.scale = self.size / self.image.shape[0]

        if reload:
            rotAng_deg = self.data_df.loc[idx, 'rotation']
            rotAng_deg = 0 if np.isnan(rotAng_deg) else int(rotAng_deg)
            self.rotate(rotAng_deg)

            flipping = self.data_df.loc[idx, 'flipping']
            flipping = False if np.isnan(flipping) else bool(flipping)
            if flipping: self.flip()        

            try: self.time = int(self.data_df.loc[idx, 'time'])
            except: self.time = 0

        
        title = f"{self.idx} - {os.path.basename(image_dir).split('.')[0]}"
        if not self.data_df.loc[idx].isnull().any(): title += ' (saved)'
        self.root.title(title)        
        
        self.refresh()
        self.start_time = datetime.now()
        return
    #--------------------------------------------------------------------------------------
    def start(self):   
        self.root.deiconify()   
        for win in self.root.winfo_children():
            if isinstance(win, tk.Toplevel): win.destroy()

        self.set_frame(self.idx)
    #--------------------------------------------------------------------------------------
    def stop(self):
        self.start_time = None
        self.root.withdraw()

        popup = tk.Toplevel(self.root)
        popup.title('Press to Start')
        popup.protocol("WM_DELETE_WINDOW", self.root.destroy)

        tk.Button(popup, text='Start', width=20, height=5, command=self.start).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        x,y,w,h = self.root.winfo_rootx(), self.root.winfo_rooty(), self.root.winfo_width(), self.root.winfo_height()        
        popup.geometry(f'{500}x{500}+{x+int(w/3)}+{y+int(h/5)}')
        
        popup.grab_set()                    
    #--------------------------------------------------------------------------------------
    def refresh(self):  
        image = cv2.resize(self.image, None, fx=self.scale, fy=self.scale).astype(np.uint8)        
        self.background.image = ImageTk.PhotoImage(Image.fromarray(image))
        self.background.create_image(0, 0, image=self.background.image, anchor=tk.NW)
        self.background.grid()

        if self.rotAng_deg == 0: rot_dir = ''
        elif self.rotAng_deg < 0: rot_dir = '(CW)'
        elif self.rotAng_deg > 0: rot_dir = '(CCW)'
        
        self.tnf_frame.config(text=f'Total Rotation = {abs(self.rotAng_deg)} {rot_dir} \t \t Total Flipping = {self.flipping}')
        return  
    #--------------------------------------------------------------------------------------
    def rotate(self, rotAng_deg):
        if isinstance(rotAng_deg, int):
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
        self.flipping = not self.flipping  

        self.refresh()
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
        self.data_df.loc[self.idx, 'rotation'] = np.sign(rotAng_deg)*(np.abs(rotAng_deg)%360)
        self.data_df.loc[self.idx, 'flipping'] = int(self.flipping)
        self.data_df.loc[self.idx, 'time'] = self.time
        self.data_df.to_csv( self.csv_path, index=False )

        self.set_frame(self.idx+1)
####################################################################################################################################
def check_digit_entry(P):
    if str.isdigit(P) or P == "": return True
    else: return False
####################################################################################################################################






# black ink on left  -  blue ink on right 


if __name__ == '__main__':

    csv_path = './data/data_testing.csv'
    replace_dict = {'data_processed':'Y:'}

    interface = GUI(csv_path, replace_dict=replace_dict )

