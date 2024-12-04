import tkinter as tk

def go():
    main_frame = tk.Tk()

    frame_label = tk.LabelFrame(main_frame, text="Testing 123")
    frame_label.grid(row=0, column=0, sticky="news")

    frame_label.grid_columnconfigure(0, weight=1)
    frame_label.grid_rowconfigure(0, weight=1)

    pane_window = tk.PanedWindow(frame_label, orient="vertical")

    pane_window.grid(row=0, column=0, sticky="news")

    column_frame_1 = tk.Frame(pane_window)
    column_frame_1.grid(row=0, column=0, sticky="news")

    column_title_1 = tk.Label(column_frame_1, text="Field1")
    column_title_1.grid(row=0, column=0, sticky="ew")

    row_1 = tk.Button(column_frame_1, text="Row 0")
    row_1.grid(row=1, column=0, sticky="ew")

    row_2 = tk.Button(ccolumn_frame_1, text="Row 1")
    row_2.grid(row=1, column=0, sticky="ew")

    row_3 = tk.Button(column_frame_1, text="Row 0, Column 3")
    row_3.grid(row=1, column=0, sticky="ew")

    row_4 = tk.Button(column_frame_1, text="Row 0, Column 4")
    row_4.grid(row=1, column=0, sticky="ew")

    row_5 = tk.Button(column_frame_1, text="Row 0, Column 5")
    row_5.grid(row=1, column=0, sticky="ew")

    pane_window.add(column_frame_1)

    main_frame.mainloop()