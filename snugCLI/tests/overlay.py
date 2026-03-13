import tkinter as tk

""" Create Window """
app = tk.Tk()

""" Edit Window """
app.geometry("200x300")
app.overrideredirect(True)
label = tk.Label(app, text="Test Window")
label.pack(pady=20)
app.wm_attributes("-alpha",0.3)



""" Activate Command """
app.mainloop()