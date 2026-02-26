import tkinter as tk
from ui import FortiAnalyzerApp


def main():
    root = tk.Tk()
    _app = FortiAnalyzerApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
