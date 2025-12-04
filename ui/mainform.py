import tkinter as tk
from tkinter import Menu
from ui.sampleScreen import create_ui
# -------------------------
# Function to open screen 1
# -------------------------
def open_screen1():
    root = tk.Tk()
    create_ui(root)
    label.pack(pady=40)


# -------------------------
# Function to open screen 2
# -------------------------
def open_screen2():
    screen2 = tk.Toplevel(root)
    screen2.title("Screen 2")
    screen2.geometry("400x300")

    label = tk.Label(screen2, text="This is Screen 2", font=("Arial", 16))
    label.pack(pady=40)


# -------------------------
# Main Window
# -------------------------
root = tk.Tk()
root.title("GRC_360")
root.geometry("700x600")

label = tk.Label(root, text="GRC 360", font=("Arial", 20))
label.pack(pady=50)

# -------------------------
# Menu Bar
# -------------------------
menubar = Menu(root)

# Create a Menu
screen_menu = Menu(menubar, tearoff=0)
screen_menu.add_command(label="MySQL & PostgreSQL", command=open_screen1)
screen_menu.add_command(label="Open Screen 2", command=open_screen2)
screen_menu.add_separator()
screen_menu.add_command(label="Exit", command=root.quit)

# Add Menu to Window
menubar.add_cascade(label="Sirisha",menu=screen_menu)
menubar.add_cascade(label= "Meghana")
menubar.add_cascade(label="Swetha")

# Display Menu
root.config(menu=menubar)

root.mainloop()
