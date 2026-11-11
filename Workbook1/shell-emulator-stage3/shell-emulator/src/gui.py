import tkinter as tk
from tkinter import scrolledtext

from config import debug_params, load_vfs
from shell import Shell, get_host, get_user

FONT = ("Courier New", 11)
WINDOW_SIZE = "800x500"
START_DELAY_MS = 100


class EmulatorWindow:
    def __init__(self, args):
        self.args = args
        self.shell = None
        self.root = tk.Tk()
        self.root.title(f"Эмулятор - [{get_user()}@{get_host()}]")
        self.root.geometry(WINDOW_SIZE)
        self.output = scrolledtext.ScrolledText(
            self.root, state="disabled", bg="black", fg="#cccccc", font=FONT)
        self.output.pack(fill="both", expand=True)
        self.entry = tk.Entry(self.root, bg="black", fg="white",insertbackground="white", font=FONT)
        self.entry.pack(fill="x")

    def write(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def start(self):
        self.write(debug_params(self.args))
        vfs = load_vfs(self.args.vfs, self.write)
        if vfs is None:
            self.entry.configure(state="disabled")
            self.write("[эмулятор] запуск невозможен. Закройте окно.")
            self.root.mainloop()
            return 1
        self.shell = Shell(vfs, self.args.prompt)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()
        if self.args.script:
            self.root.after(START_DELAY_MS, self.run_script)
        self.root.mainloop()
        return 0

    def run_script(self):
        if self.shell.run_script(self.args.script, self.write):
            self.root.destroy()

    def on_enter(self, _event=None):
        line = self.entry.get()
        self.entry.delete(0, "end")
        self.write(self.shell.prompt + line)
        result = self.shell.run(line)
        if result.out:
            self.write(result.out)
        if result.should_exit:
            self.root.destroy()


def run_gui(args):
    return EmulatorWindow(args).start()
