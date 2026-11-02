import os
from pathlib import Path
from queue import Empty, Queue
from shutil import which
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def find_engine():
    command = which("ebook-convert.exe")
    if command:
        return command
    for name in ("ProgramFiles", "ProgramFiles(x86)"):
        if folder := os.environ.get(name):
            candidate = Path(folder) / "Calibre2" / "ebook-convert.exe"
            if candidate.is_file():
                return str(candidate)
    return None


def convert(engine, source, destination):
    with TemporaryDirectory(dir=destination.parent) as folder:
        output = Path(folder) / "book.pdf"
        result = subprocess.run(
            [engine, str(source), str(output)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode or not output.is_file():
            details = (result.stderr.strip() or result.stdout.strip())[-1800:]
            raise RuntimeError(details or "Calibre did not produce a PDF.")
        with output.open("rb") as pdf:
            if pdf.read(5) != b"%PDF-":
                raise RuntimeError("Calibre did not produce a valid PDF header.")
        os.replace(output, destination)


def main():
    window = tk.Tk()
    window.title("EPUB to PDF")
    window.resizable(False, False)
    panel = ttk.Frame(window, padding=24)
    panel.grid(sticky="nsew")
    ttk.Label(panel, text="EPUB to PDF", font=("Segoe UI", 20, "bold")).pack(anchor="w")
    ttk.Label(panel, text="Convert a DRM-free EPUB using Calibre on this PC.").pack(
        anchor="w", pady=(4, 18)
    )
    status = tk.StringVar(value="Choose an EPUB to get started.")
    results = Queue()

    def poll():
        try:
            error, destination = results.get_nowait()
        except Empty:
            window.after(150, poll)
            return
        button.state(["!disabled"])
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        if error:
            status.set("Conversion failed.")
            messagebox.showerror("Conversion failed", error, parent=window)
        else:
            status.set(f"Saved {destination.name}")
            if messagebox.askyesno("PDF ready", f"Open this PDF?\n\n{destination}", parent=window):
                try:
                    os.startfile(destination)
                except OSError as exc:
                    messagebox.showerror("Could not open PDF", str(exc), parent=window)

    def choose():
        engine = find_engine()
        if not engine:
            messagebox.showinfo(
                "Calibre required",
                "Install Calibre for Windows from calibre-ebook.com/download_windows, then try again.",
                parent=window,
            )
            return
        source = filedialog.askopenfilename(
            parent=window, title="Choose an EPUB", filetypes=[("EPUB books", "*.epub")]
        )
        if not source:
            return
        source = Path(source)
        target = filedialog.asksaveasfilename(
            parent=window, title="Save PDF", initialdir=source.parent,
            initialfile=source.with_suffix(".pdf").name, defaultextension=".pdf",
            filetypes=[("PDF documents", "*.pdf")],
        )
        if not target:
            return
        destination = Path(target)
        if destination.suffix.lower() != ".pdf" or source.suffix.lower() != ".epub":
            messagebox.showerror("Check file types", "Choose an EPUB and save it with a .pdf extension.", parent=window)
            return

        def work():
            try:
                convert(engine, source, destination)
            except (OSError, RuntimeError) as exc:
                results.put((str(exc), destination))
            else:
                results.put((None, destination))

        status.set(f"Converting {source.name}...")
        button.state(["disabled"])
        window.protocol("WM_DELETE_WINDOW", lambda: None)
        Thread(target=work, daemon=True).start()
        window.after(150, poll)

    button = ttk.Button(panel, text="Choose EPUB and convert", command=choose)
    button.pack(anchor="w")
    ttk.Label(panel, textvariable=status, width=52, wraplength=340).pack(anchor="w", pady=(14, 0))
    window.mainloop()


if __name__ == "__main__":
    main()
