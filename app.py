import tkinter as tk
from tkinter import messagebox
import customtkinter
import logging
import os
import time
import datetime
import vlc
import sqlite3
import configparser
import atexit

class App:
    def __init__(self, master):
        self.master = master

        root.title("Quran Player")
        root.geometry("310x160")
        # add padding to the window
        root.config(pady=7)

        logging.basicConfig(level=logging.NOTSET)

        # Themes
        customtkinter.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
        customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

        # config
        self.config_file = 'config.ini'
        self.create_config()
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

        # Define the options for the dropdown
        self.options = []
        for i in range(30):
            formatted_num = "{:02d}".format(i + 1)
            self.options.append('Juz ' + str(formatted_num))

        # Define Items
        self.option_menu = customtkinter.CTkOptionMenu(root, values=self.options, command=self.option_changed)
        self.option_menu.set(self.get_config_selection()) # set initial value
        self.elapsed_label = customtkinter.CTkLabel(root, text="00:00:00", width=20)
        self.play_button = customtkinter.CTkButton(root, text="Play", fg_color='#16a34a', hover_color='#166534', command=self.toggle_play_button, width=50)
        self.stop_button = customtkinter.CTkButton(root, text="Stop", fg_color='#dc2626', hover_color='#991b1b', command=self.stop, width=40)
        self.repeat_label = customtkinter.CTkLabel(root, text="Repeat:")
        self.repeat_entry = customtkinter.CTkEntry(root, width=40)
        self.repeat_entry.insert(1, "15")
        self.data_button = customtkinter.CTkButton(root, text="Data", command=self.display_data, width=40)
        self.shutdown_var = tk.BooleanVar(root, self.get_config_shutdown())
        self.checkbox = customtkinter.CTkCheckBox(root, text="Shutdown after finish", variable=self.shutdown_var)
        self.status_label = customtkinter.CTkLabel(root, text="", width=280)

        # Position
        self.option_menu.grid(sticky="W", row=0, column=0, columnspan=2, padx=18, pady=5)
        self.elapsed_label.grid(sticky="W", row=0, column=2, columnspan=2, pady=5)
        self.play_button.grid(sticky="W", row=1, column=0, padx=20, pady=5, ipadx=10)
        self.stop_button.grid(sticky="W", row=1, column=1, ipadx=10)
        self.repeat_label.grid(sticky="W", row=1, column=2, padx=5)
        self.repeat_entry.grid(sticky="W", row=1, column=3, padx=18)
        self.data_button.grid(sticky="W", row=2, column=0, padx=20, pady=5, ipadx=10)
        self.checkbox.grid(sticky="W", row=2, column=1, columnspan=4, pady=5)
        self.status_label.grid(sticky="W", row=3, column=0, columnspan=4, padx=20)

        # Initialize variables
        self.file_path = ""
        self.file_name = ""
        self.repeat = 1
        self.stop_trigger = False
        self.run_time = False
        self.pause = False
        self.played = False # indicate when first play initiate

        # Initiate Run
        #self.option_set()

        # Initialize Time Elapse
        self.start_time = time.time()
        self.elapsed_time = 0

        # Initialize Button States
        self.stop_button.configure(state="disabled")

        # update config
        atexit.register(self.update_config)

    def create_config(self):
        if not os.path.exists(self.config_file):
            # create the config file if it doesn't exist
            with open(self.config_file, 'w') as f:
                f.write('[config]\n')
                f.write('Selection = "Juz 01"\n')
                f.write('Shutdown = 0\n')

    def get_config_selection(self):
        selection_value = self.config.get('config', 'Selection')
        if selection_value in self.options:
            return selection_value
        else:
            return self.options[0]

    def get_config_shutdown(self):
        shutdown_value = self.config.getint('config', 'Shutdown')
        return shutdown_value;

    def update_config(self):
        # update the value of Selection and Shutdown
        self.config.set('config', 'Selection', self.option_menu.get())
        self.config.set('config', 'Shutdown', str(int(self.shutdown_var.get())))
        #messagebox.showinfo('test', self.shutdown_var.get())

        # write the updated config back to the file
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    # Define a function to toggle the button state
    def toggle_play_button(self):
        if self.play_button.cget('text') == 'Play':
            self.play_button.configure(text='Pause', fg_color='#ca8a04', hover_color='#854d0e')

            if(self.played == False):
                logging.info("Start playing")
                self.played = True
                self.play()
            else:
                # unpause
                self.pause = False

        else:
            self.play_button.configure(text='Play')
            self.pause = True # Pause

    def play(self):

        #self.play_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.option_menu.configure(state="disabled")

        self.option_set()
        # Create a new instance of VLC player
        instance = vlc.Instance()

        # Create a new media player object
        player = instance.media_player_new()

        # Load the media file
        media = instance.media_new(self.file_path)
        player.set_media(media)

        try:
            repeat_times = int(self.repeat_entry.get())
        except ValueError:
            repeat_times = 1

        # elapsed
        self.run_time = True
        self.start_time = time.time()
        self.update_elapsed_time()

        for i in range(repeat_times):

            # start playing the media file
            player.play()
            logging.info('repeat ' + str(i + 1))
            self.status_label.configure(text='Playing ' + self.file_name + ' (' + str(i + 1) + ')')
            # loop until the media file stops playing
            while True:
                if self.pause == True and player.get_state() != vlc.State.Paused:
                    player.pause()
                    logging.info('pause')

                if self.pause == False and player.get_state() == vlc.State.Paused:
                    player.play()
                    logging.info('continue')

                if self.stop_trigger == True:
                    player.stop()
                    self.stop_trigger = False
                    self.stop_button.configure(state="disabled")
                    return
                if player.get_state() == vlc.State.Ended:
                    logging.info("Media file has ended")
                    player.stop()
                    break
                root.update()
                time.sleep(0.05) # sleep to prevent cpu high usage

        self.play_button.configure(state="normal")
        self.option_menu.configure(state="normal")

        # update stop states
        self.stop_states()

        # shutdown if checked
        if self.shutdown_var.get():
            self.shutdown()
            root.destroy()
            logging.info('shutdown ya')
        else:
            logging.info('shutdown no')

    def stop(self):
        self.stop_trigger = True
        logging.info('mp3 stopped')
        self.stop_states()

    def stop_states(self):
        self.run_time = False
        self.played = False
        self.pause = False
        self.elapsed_time = 0
        self.play_button.configure(state="normal", text='Play', fg_color='#16a34a', hover_color='#166534')
        self.option_menu.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text='Stop playing')
        self.insert_data(self.option_menu.get(), self.elapsed_label.cget("text"))
        self.elapsed_label.configure(text='00:00:00')

    def update_elapsed_time(self):
        if self.run_time == True:
            # Calculate the elapsed time since the program started
            #elapsed_time = time.time() - self.start_time
            if self.pause == False:
                self.elapsed_time += 0.1

            # Format the elapsed time as hh:mm:ss
            time_str = time.strftime("%H:%M:%S", time.gmtime(self.elapsed_time))

            # Update the elapsed time label
            self.elapsed_label.configure(text=time_str)

            # Call this method again after 100 ms
            root.after(100, self.update_elapsed_time)

    def insert_data(self, *args):
        conn = self.connectdb()
        cursor = conn.cursor()
        now = datetime.datetime.now()
        formatted_dt = now.strftime("%Y-%m-%d %H:%M:%S")  # format the datetime object as a string
        sql = "INSERT INTO mytable (datetime, title, info) VALUES (?, ?, ?)"
        data = (formatted_dt, args[0], args[1])
        cursor.execute(sql, data)
        logging.info('Data saved')
        conn.commit()
        conn.close()

    def connectdb(self):
        # connect to the SQLite database
        conn = sqlite3.connect('data.db')
        logging.info('Database connected')
        conn.execute('''CREATE TABLE IF NOT EXISTS mytable
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         datetime TEXT NOT NULL,
                         title TEXT NOT NULL,
                         info TEXT NOT NULL);''')

        return conn

    def shutdown(self):
        os.system("shutdown /s /t 1")

    def option_set(self):
        self.file_name = 'Shaikh Saad Al-Ghamdi - ' + self.option_menu.get() + '.mp3'

        desktop_dir = os.path.join(os.path.expanduser("~/Desktop"), "Saad Al-Ghamidi")
        current_dir = os.path.join(os.getcwd(), "Saad Al-Ghamidi")

        # use folder in current directory if exist, otherwise use folder in desktop
        if os.path.exists(current_dir):
            logging.info('Folder in current directory exist')
            self.file_path = os.path.join(os.getcwd(), "Saad Al-Ghamidi", self.file_name)
        elif os.path.exists(desktop_dir):
            self.file_path = os.path.join(os.path.expanduser("~/Desktop"), "Saad Al-Ghamidi", self.file_name)
        else:
            messagebox.showinfo("Error", "Folder Quran tidak wujud!")

    def option_changed(self, value):
        logging.info(value + ' selected')

    def center_window(window):
        # get the screen width and height
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # calculate the x and y coordinates to center the window
        x = int((screen_width - window.winfo_reqwidth()) / 2)
        y = int((screen_height - window.winfo_reqheight()) / 2)

        # set the window position
        window.geometry("+{}+{}".format(x, y))

    # create a function to open the child window
    def display_datas(self):
        # create the child window
        child_window = customtkinter.CTk()

        # set the properties of the child window
        child_window.geometry("360x200")
        child_window.title("Child Window")
        child_window.resizable(False, True)
        App.center_window(child_window)

        canvas = customtkinter.CTkCanvas(child_window, width=340)
        canvas.pack(side="left", fill="both", expand=True)

        # bind the mousewheel event to the on_mousewheel function
        canvas.bind_all("<MouseWheel>", lambda event: self.on_mousewheel(canvas, event))

        frame = customtkinter.CTkFrame(canvas)
        frame.pack(side="left", fill="both", expand=True)

        conn = self.connectdb()

        # execute a SELECT statement to get the table data
        cursor = conn.execute('SELECT datetime, title, info FROM mytable ORDER BY id DESC')

        # create a header row
        header = ["Datetime", "Title", "Info"]
        for i, col_name in enumerate(header):
            #label = tk.Label(frame, text=col_name, relief=tk.RIDGE, width=15)
            label = customtkinter.CTkLabel(frame, text=col_name, width=100, padx=5)
            label.grid(row=0, column=i)

        # create a row for each record in the table
        for i, row in enumerate(cursor):
            for j, cell in enumerate(row):
                #label = tk.Label(frame, text=cell, relief=tk.RIDGE, width=15)
                label = customtkinter.CTkLabel(frame, text=cell, padx=5)
                label.grid(row=i + 1, column=j)

        # commit the changes and close the database connection
        conn.commit()
        conn.close()

        # add a scrollbar to the canvas
        scrollbar = tk.Scrollbar(child_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.config(yscrollcommand=scrollbar.set)

        # update the canvas when the frame is resized
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # add the frame to the canvas
        canvas.create_window((0, 0), window=frame, anchor="nw")

        # run the child window
        child_window.mainloop()

    # define a function to create the popout window
    def display_data(self):
        dd = tk.Tk()
        #dd = customtkinter.CTk()
        dd.geometry("360x200")
        # disable window resizing
        dd.resizable(False, True)
        App.center_window(dd)

        canvas = tk.Canvas(dd, width=340)
        canvas.pack(side="left", fill="both", expand=True)

        # bind the mousewheel event to the on_mousewheel function
        canvas.bind_all("<MouseWheel>", lambda event: self.on_mousewheel(canvas, event))

        frame = tk.Frame(canvas)
        frame.pack(side="left", fill="both", expand=True)

        conn = self.connectdb()

        # execute a SELECT statement to get the table data
        cursor = conn.execute('SELECT datetime, title, info FROM mytable ORDER BY id DESC')

        # create a header row
        header = ["Datetime", "Title", "Info"]
        for i, col_name in enumerate(header):
            label = tk.Label(frame, text=col_name, relief=tk.RIDGE, width=15)
            label.grid(row=0, column=i)

        # create a row for each record in the table
        for i, row in enumerate(cursor):
            for j, cell in enumerate(row):
                label = tk.Label(frame, text=cell, relief=tk.RIDGE, width=15)
                label.grid(row=i + 1, column=j)

        # commit the changes and close the database connection
        conn.commit()
        conn.close()

        # add a scrollbar to the canvas
        scrollbar = tk.Scrollbar(dd, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.config(yscrollcommand=scrollbar.set)


        # update the canvas when the frame is resized
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # add the frame to the canvas
        canvas.create_window((0, 0), window=frame, anchor="nw")

    def on_mousewheel(self, canvas, event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")



if __name__ == '__main__':
    root = customtkinter.CTk()
    App.center_window(root)
    Gui = App(root)
    root.resizable(False, False)
    root.mainloop()