def hover(widget, bg, hover_bg):
    widget.configure(bg=bg)
    widget.bind("<Enter>", lambda e: widget.configure(bg=hover_bg))
    widget.bind("<Leave>", lambda e: widget.configure(bg=bg))
