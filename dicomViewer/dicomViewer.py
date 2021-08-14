import PySimpleGUI as sg
import math
from tkinter import *
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,NavigationToolbar2Tk)
from matplotlib import backend_bases
import pydicom as dicom
import matplotlib.pyplot as plt
import os,sys
import numpy as np

backend_bases.NavigationToolbar2.toolitems = (
        ('Home', 'Reset original view', 'home', 'home'),
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom')
      )

try:
    f = open("data.dicomViewer","r")
    f.close()
except FileNotFoundError:
    f = open("data.dicomViewer","w")
    f.write("SystemDefault")
    f.close()
    
f = open("data.dicomViewer", "r")

themes = sg.ListOfLookAndFeelValues() 
selected_theme = f.read()
current_them = sg.LOOK_AND_FEEL_TABLE[selected_theme]
sg.ChangeLookAndFeel(selected_theme)

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    toolbar=Toolbar(figure_canvas_agg, window["-CONTROLS-"].TKCanvas)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=True)
    return figure_canvas_agg

class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)

def person_data(ds,window):
    try:
        window["-NAME-"].Update(value=ds[(0x0010, 0x0010)].value)
    except:
        window["-NAME-"].Update(value=None)
    try:
        window["-ID-"].Update(value=ds[(0x0010, 0x0020)].value)
    except:
        window["-ID-"].Update(value=None)
    try:
        window["-BIRTHD-"].Update(value=ds[(0x0010, 0x0030)].value)
    except:
        window["-BIRTHD-"].Update(value=None)
    try:
        window["-SEX-"].Update(value=ds[(0x0010, 0x0040)].value)
    except:
        window["-SEX-"].Update(value=None)
    try:
        window["-WEIGHT-"].Update(value=ds[(0x0010, 0x1030)].value)
    except KeyError:
        window["-WEIGHT-"].Update(value="")
    try:
        window["-SIZE-"].Update(value=ds[(0x0010, 0x1020)].value)
    except KeyError:
        window["-SIZE-"].Update(value="")
    try:
        window["-EXAMINED-"].Update(value=ds[(0x0018, 0x0022)].value)
    except KeyError:
        window["-EXAMINED-"].Update(value="")
    try:
        window["-INSNAME-"].Update(value=ds[(0x0008, 0x0080)].value)
    except KeyError:
        window["-INSNAME-"].Update(value="")
    try:
        window["-INSADR-"].Update(value=ds[(0x008, 0x0081)].value)
    except KeyError:
        window["-INSADR-"].Update(value="")
    try:
        window["-INSDEP-"].Update(value=ds[(0x0008, 0x1045)].value)
    except KeyError:
        window["-INSDEP-"].Update(value="")
    try:
        window["-MEDICAL-"].Update(value=ds[(0x0010, 0x2000)].value)
    except KeyError:
        window["-MEDICAL-"].Update(value="")
    try:
        window["-ALLERGIES-"].Update(value=ds[(0x0010, 0x2110)].value)
    except KeyError:
        window["-ALLERGIES-"].Update(value="")
    try:
        window["-ADDHIST-"].Update(value=ds[(0x0010, 0x21b0)].value)
    except KeyError:
        window["-ADDHIST-"].Update(value="")
    try:
        window["-PATCOMMS-"].Update(value=ds[(0x0010, 0x4000)].value)
    except KeyError:
        window["-PATCOMMS-"].Update(value="")

def readFile(window,image_path,photoarray,flag):
        try:
            if flag == 0:
                val = values["-IN-"]
            else:
                val = flag
            if len(val) > 2:
                image_path = val+"/"
                photoarray.clear()
                for s in os.listdir(image_path):
                    try:
                        dicom.dcmread(image_path+s)
                        photoarray.append(s)
                    except dicom.errors.InvalidDicomError:
                        None
                slider=window["-SLIDER-"]
                slider.Update(range=(0, len(photoarray)-1),value=0)
                ds = dicom.dcmread(image_path+photoarray[0])
                ax.imshow(ds.pixel_array, cmap=plt.cm.gray,vmin=brightMin, vmax=brightMax*(-1))
                fig_agg.draw()
                person_data(ds,window)
                window["-EDIT-"].Update(disabled=False,button_color=("white","firebrick3"))
                window["-NEXT-"].Update(disabled=False,button_color=("white","royalblue4"))
                window["-PREV-"].Update(disabled=False,button_color=("white","royalblue4"))
                lockFields()
        except FileNotFoundError:
            image_path = ""
            photoarray.clear()
        return image_path,photoarray,True
    
def readSinglePhoto(window,image_path,photoarray, flag):
    try:
        if flag == 0:
            val=values["-IN2-"]
        else:
            val=flag
        if len(val)>2:
            photoarray.clear()
            image_path=val
            window["-SLIDER-"].Update(range=(0,0),value=0)
            try:
                ds = dicom.dcmread(image_path)
                ax.imshow(ds.pixel_array, cmap=plt.cm.gray,vmin=brightMin, vmax=brightMax*(-1))
                fig_agg.draw()
                person_data(ds,window)
                window["-EDIT-"].Update(disabled=False,button_color=("white","firebrick3"))
                window["-NEXT-"].Update(disabled=True,button_color=("white","royalblue4"))
                window["-PREV-"].Update(disabled=True,button_color=("white","royalblue4"))
                lockFields()
                photoarray.append(os.path.basename(image_path))
                image_path=os.path.dirname(image_path)+"/"
            except dicom.errors.InvalidDicomError:
                image_path=""
            
    except FileNotFoundError:
        image_path = ""
    return image_path,photoarray,True

def edit(editFl):
    window["-EDIT-"].Update(text="Save", button_color=("white","green"))
    window["-MEDICAL-"].Update(disabled=False)
    window["-ALLERGIES-"].Update(disabled=False)
    window["-ADDHIST-"].Update(disabled=False)
    window["-PATCOMMS-"].Update(disabled=False)
    return False

def save(ds):
    try:
        ds[(0x0010, 0x2000)].value=str(values["-MEDICAL-"])
    except KeyError:
        ds.add_new([0x0010, 0x2000], 'LO', str(values["-MEDICAL-"]))
    try:
        ds[(0x0010, 0x2110)].value=str(values["-ALLERGIES-"])
    except KeyError:
        ds.add_new([0x0010, 0x2110], 'LO', str(values["-ALLERGIES-"]))
    try:
        ds[(0x0010, 0x21b0)].value=str(values["-ADDHIST-"])
    except KeyError:
        ds.add_new([0x0010, 0x2110], 'LT', str(values["-ADDHIST-"]))
    try:
        ds[(0x0010, 0x4000)].value=str(values["-PATCOMMS-"])
    except KeyError:
        ds.add_new([0x0010, 0x4000], 'LT', str(values["-ADDHIST-"]))
    lockFields()
    ds.save_as(image_path+photoarray[int(values['-SLIDER-'])])
    return True

def lockFields():
    window["-EDIT-"].Update(text="Edit Fields", button_color=("white","firebrick3"))
    window["-MEDICAL-"].Update(disabled=True)
    window["-ALLERGIES-"].Update(disabled=True)
    window["-ADDHIST-"].Update(disabled=True)
    window["-PATCOMMS-"].Update(disabled=True)

sg.SetOptions(font="Consolas")

menu_def = [['File', ['Open File          Ctrl+O', 'Open Folder        Ctrl+D', '---', 'Preferences', ['Select theme        Ctrl+T'], 'Exit']],
            ['Help', ['Check for Updates...', '---', 'About']] ]

col = [[sg.Text('Name      '), sg.Input(key="-NAME-",disabled=True)],
        [sg.Text('ID        '), sg.Input(key="-ID-",disabled=True, size=(25,1))],
        [sg.Text('Birth Date'), sg.Input(key="-BIRTHD-",disabled=True, size=(20,1))],
        [
         sg.Text('Sex       '), sg.Input(key="-SEX-", disabled=True, size=(5,1)),
         sg.Text('  Weight'), sg.Input(key="-WEIGHT-", disabled=True, size=(5,1)),
         sg.Text('  Size'), sg.Input(key="-SIZE-", disabled=True, size=(5,1))
         ],
        [sg.Text('Options   '), sg.Input(key="-OPTIONS-", disabled=True)],       
        [sg.Text('Examined  '), sg.Input(key="-EXAMINED-", disabled=True)],
        [sg.Text('Institution Name         '), sg.Input(key="-INSNAME-", disabled=True)],
        [sg.Text('Institution Adress       '), sg.Input(key="-INSADR-", disabled=True)],
        [sg.Text('Institution Departament  '), sg.Input(key="-INSDEP-", disabled=True)],
        [sg.Button("Edit Fields",key="-EDIT-",disabled=True,button_color=("white","gray"),size=(25,1),enable_events=True)],
        [sg.Text('Medical Alerts    '), sg.Multiline(key="-MEDICAL-", disabled=True)],
        [sg.Text('Allergies         '), sg.Multiline(key="-ALLERGIES-", disabled=True)],
        [sg.Text('Additional History'), sg.Multiline(key="-ADDHIST-", disabled=True)],
        [sg.Text('Patient Comments  '), sg.Multiline(key="-PATCOMMS-", disabled=True)]
        ]
buttonColFix=[[sg.FileBrowse(button_text="File",key="-IN2-", enable_events=True,button_color=("white","royalblue4"))]]
layout = [[sg.Menu(menu_def, tearoff=False, font=("Consolas", 11))],
          [
           sg.Text("Choose a file: "),
           sg.Input(key="-IN-", enable_events=True, disabled=True),
           sg.FolderBrowse(button_text="Folder",target="-IN-", button_color=("white","royalblue4")),
           sg.Column(buttonColFix)
           ],
          [sg.Canvas(key="-CONTROLS-")],
          [sg.Canvas(size=(640,640), key='-CANVAS-'),sg.Column(col)],
          [
           sg.Text('Photo'), sg.Slider((0, 100), orientation='h', enable_events=True, key='-SLIDER-', size=(35.8,20)),
           sg.Button("Previous",key="-PREV-",disabled=True,size=(8,1),button_color=("white","gray"),enable_events=True),
           sg.Button("Next",key="-NEXT-",disabled=True,size=(8,1),button_color=("white","gray"),enable_events=True)
           ],
          [
           sg.Text('Contrast'),sg.Slider((0, 3000), disable_number_display=True, orientation='h',default_value=0, enable_events=True, key='-SLIDER2-'),
           sg.Text('Brightness'), sg.Slider((-3000, 0), disable_number_display=True, orientation='h',default_value=-2000, enable_events=True, key='-SLIDER3-')
           ]
          ]
    
image_path = None
photoarray = []
window = sg.Window('DicomViewer', layout, finalize=True, return_keyboard_events=True)
canvas_elem = window['-CANVAS-']
canvas = canvas_elem.TKCanvas
fig = Figure()
ax = fig.add_subplot(111)
ax.xaxis.set_visible(False)
ax.yaxis.set_visible(False)
brightMin=0
brightMax=-2000
editFl=True

fig_agg = draw_figure(canvas, fig)

window['-CANVAS-'].bind('<Enter>', '+MOUSE OVER+')
window['-CANVAS-'].bind('<Leave>', '+MOUSE AWAY+')
check = ""
theme = ""

while True: 
    event, values = window.read()
    if event is None:
        break
    elif event in ('Exit', 'e:69'):
        window.close()

    elif event in ('Open File          Ctrl+O', 'o:79'):
        file = sg.popup_get_file('', no_window=True)
        image_path, photoarray, editFl= readSinglePhoto(window,file,photoarray,file)

    elif event in ('Open Folder        Ctrl+D', 'd:68'):
        file = sg.popup_get_folder('', no_window=True)
        image_path, photoarray, editFl= readFile(window,image_path,photoarray,file)

    elif event in ('Select theme        Ctrl+T', 't:84'):
        colorLayout = [
        [sg.T('User Setting:')],
        [sg.Text('Select Theme:'), 
        sg.Combo(values=themes, default_value=selected_theme, size=(15, 1), enable_events=True, key='select_theme')],
        [sg.T("To fully enjoy the theme you need to restart the program.")], 
        [sg.B('Ok'), sg.B("Restart")]]
        colorWindow = sg.Window('Select theme', layout=colorLayout)
        while True:
            e, v = colorWindow.read()
            if e is None:
                break
            
            elif e == "Ok":
                colorWindow.close()

            elif e == "Restart":
                os.execl(sys.executable, sys.executable, * sys.argv)

            elif e == 'select_theme':

                try:
                    selected_theme = v['select_theme']
                    current_them = sg.LOOK_AND_FEEL_TABLE[selected_theme]
                    window_bkg = current_them.get('BACKGROUND')
                    colorWindow.TKroot.config(background=window_bkg)
                except Exception as e:
                    print(e)
                
                f = open("data.dicomViewer", "w")
                f.write(selected_theme)
                f.close()      

    elif event == ('Check for Updates...'):
        sg.popup('There are currently no updates available.', title="DicomViewer")

    elif event == ('About'):
        sg.popup('About', title="DicomViewer")

    elif event == "-CANVAS-+MOUSE OVER+":
        check = "-CANVAS-+MOUSE OVER+"
    elif event == "-CANVAS-+MOUSE AWAY+":
        check = "-CANVAS-+MOUSE AWAY+"
        
    elif event == "-IN-":
        image_path, photoarray, editFl= readFile(window,image_path,photoarray,0)
        
    elif event == "-IN2-":
        image_path, photoarray, editFl= readSinglePhoto(window,image_path,photoarray,0)
        
    elif event == "-SLIDER-":
        ax.cla()
        if(image_path!="" and image_path!=None):   
            ds = dicom.dcmread(image_path+photoarray[int(values['-SLIDER-'])]) 
            ax.imshow(ds.pixel_array, cmap=plt.cm.gray,vmin=brightMin, vmax=brightMax*(-1))
            fig_agg.draw()
            person_data(ds,window)
            editFl=True
            lockFields()
            
    elif event == "-NEXT-": 
        ax.cla()
        if(image_path!="" and image_path!=None and len(photoarray)>1):
            nextNr = int(values['-SLIDER-'])+1
            if nextNr < len(photoarray):
                ds = dicom.dcmread(image_path+photoarray[nextNr])
                window["-SLIDER-"].Update(value=nextNr)
            ax.imshow(ds.pixel_array, cmap=plt.cm.gray,vmin=brightMin, vmax=brightMax*(-1))
            fig_agg.draw()
            person_data(ds,window)
            editFl=True
            lockFields()
            
    elif event == "-PREV-":
        ax.cla()
        if(image_path!="" and image_path!=None and len(photoarray)>1):
            nextNr = int(values['-SLIDER-'])-1
            if nextNr >= 0:
                ds = dicom.dcmread(image_path+photoarray[nextNr])
                window["-SLIDER-"].Update(value=nextNr)
            else:
                ds = dicom.dcmread(image_path+photoarray[0])
            ax.imshow(ds.pixel_array, cmap=plt.cm.gray,vmin=brightMin, vmax=brightMax*(-1))
            fig_agg.draw()
            person_data(ds,window)
            editFl=True
            lockFields()
            
    elif event == "-SLIDER2-":
        ax.cla()
        brightMin=int(values["-SLIDER2-"])  
        if(image_path!="" and image_path!=None):
            ds = dicom.dcmread(image_path+photoarray[int(values['-SLIDER-'])]) 
            slider2=window["-SLIDER2-"]
            slider2.Update(range=(0,brightMax*(-1)-1))
            slider3=window["-SLIDER3-"]
            slider3.Update(range=(-3000, brightMin*(-1)-1))
            ax.imshow(ds.pixel_array, cmap=plt.cm.gray,vmin=brightMin, vmax=brightMax*(-1))
            fig_agg.draw()
            
    elif event == "-SLIDER3-":
        ax.cla()
        brightMax=int(values["-SLIDER3-"])
        if(image_path!="" and image_path!=None):
            ds = dicom.dcmread(image_path+photoarray[int(values['-SLIDER-'])])
            slider2=window["-SLIDER2-"] 
            slider2.Update(range=(0,brightMax*(-1)-1))
            slider3=window["-SLIDER3-"]
            slider3.Update(range=(-3000,brightMin*(-1)-1))
            ax.imshow(ds.pixel_array, cmap=plt.cm.gray,vmin=brightMin, vmax=brightMax*(-1))
            fig_agg.draw()
            
    elif event == "-EDIT-": 
        if editFl:
            editFl=edit(editFl)
        else:
            ds=dicom.dcmread(image_path+photoarray[int(values['-SLIDER-'])])
            editFl=save(ds)

    elif event == "MouseWheel:Up" and check == "-CANVAS-+MOUSE OVER+":
        ax.cla()
        if(image_path!="" and image_path!=None and len(photoarray)>1):
            nextNr = int(values['-SLIDER-'])+1
            if nextNr < len(photoarray):
                ds = dicom.dcmread(image_path+photoarray[nextNr])
                window["-SLIDER-"].Update(value=nextNr)
            ax.imshow(ds.pixel_array, cmap=plt.cm.gray,vmin=brightMin, vmax=brightMax*(-1))
            fig_agg.draw()
            person_data(ds,window)
            editFl=True
            lockFields()

    
    elif event == "MouseWheel:Down" and check == "-CANVAS-+MOUSE OVER+":
        ax.cla()
        if(image_path!="" and image_path!=None and len(photoarray)>1):
            nextNr = int(values['-SLIDER-'])-1
            if nextNr >= 0:
                ds = dicom.dcmread(image_path+photoarray[nextNr])
                window["-SLIDER-"].Update(value=nextNr)
            else:
                ds = dicom.dcmread(image_path+photoarray[0])
            ax.imshow(ds.pixel_array, cmap=plt.cm.gray,vmin=brightMin, vmax=brightMax*(-1))
            fig_agg.draw()
            person_data(ds,window)
            editFl=True
            lockFields()
            
window.close()
