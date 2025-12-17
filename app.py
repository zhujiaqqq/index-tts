#!/usr/bin/env python3
import threading
import re
import sys
import traceback
import importlib.util
import sysconfig
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def chunk_text(text, max_chars=50):
    sentences = [s.strip() for s in re.split(r'(?<=[。．.])\s*', text) if s.strip()]
    chunks = []
    cur = ''
    for s in sentences:
        if not cur:
            if len(s) <= max_chars:
                cur = s
            else:
                for i in range(0, len(s), max_chars):
                    chunks.append(s[i:i+max_chars])
                cur = ''
        else:
            if len(cur) + len(s) <= max_chars:
                cur = cur + s
            else:
                chunks.append(cur)
                if len(s) <= max_chars:
                    cur = s
                else:
                    for i in range(0, len(s), max_chars):
                        chunks.append(s[i:i+max_chars])
                    cur = ''
    if cur:
        chunks.append(cur)
    return chunks


class TTSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('IndexTTS Generator')
        self.geometry('760x520')
        self.resizable(True, True)
        self.create_widgets()
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def create_widgets(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        # Text file selector
        row = 0
        ttk.Label(frm, text='Text file:').grid(column=0, row=row, sticky=tk.W)
        self.txt_entry = ttk.Entry(frm)
        self.txt_entry.grid(column=1, row=row, sticky=tk.EW, padx=6)
        ttk.Button(frm, text='Browse', command=self.browse_text).grid(column=2, row=row)

        row += 1
        ttk.Label(frm, text='Speaker prompt (wav):').grid(column=0, row=row, sticky=tk.W)
        self.spk_entry = ttk.Entry(frm)
        self.spk_entry.grid(column=1, row=row, sticky=tk.EW, padx=6)
        ttk.Button(frm, text='Browse', command=self.browse_spk).grid(column=2, row=row)

        row += 1
        ttk.Label(frm, text='Output directory:').grid(column=0, row=row, sticky=tk.W)
        self.out_entry = ttk.Entry(frm)
        self.out_entry.grid(column=1, row=row, sticky=tk.EW, padx=6)
        ttk.Button(frm, text='Choose', command=self.browse_out).grid(column=2, row=row)

        row += 1
        ttk.Label(frm, text='Output prefix:').grid(column=0, row=row, sticky=tk.W)
        self.pref_entry = ttk.Entry(frm)
        self.pref_entry.insert(0, 'gen')
        self.pref_entry.grid(column=1, row=row, sticky=tk.W, padx=6)

        row += 1
        self.start_btn = ttk.Button(frm, text='Start', command=self.start)
        self.start_btn.grid(column=0, row=row, columnspan=3, pady=(8, 6))

        row += 1
        self.progress = ttk.Progressbar(frm, mode='determinate')
        self.progress.grid(column=0, row=row, columnspan=3, sticky=tk.EW, pady=(6, 6))

        row += 1
        ttk.Label(frm, text='Log:').grid(column=0, row=row, sticky=tk.W)
        row += 1
        self.logbox = tk.Text(frm, height=14, wrap=tk.WORD)
        self.logbox.grid(column=0, row=row, columnspan=3, sticky=tk.NSEW)

        # layout config
        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(row, weight=1)

        # sensible defaults
        if Path('examples/voice_03.wav').exists():
            self.spk_entry.delete(0, tk.END)
            self.spk_entry.insert(0, 'examples/voice_03.wav')
        if Path('examples/voice_01.wav').exists() and not self.spk_entry.get():
            self.spk_entry.insert(0, 'examples/voice_01.wav')

    def make_chunks(self, raw_text, min_chars=100, max_chars=200):
        """Create chunks composed of whole sentences.

        - replace newlines with spaces
        - split into sentences (keeps punctuation)
        - each chunk contains one or more full sentences
        - aim for chunk length between min_chars and max_chars
        - if a single sentence > max_chars, hard-split it into max-sized pieces
        """
        text = raw_text.replace('\n', ' ').strip()
        if not text:
            return []
        # split by common sentence-ending punctuation (Chinese and ASCII)
        sentences = [s.strip() for s in re.split(r'(?<=[。．.!?！？])\s*', text) if s.strip()]
        chunks = []
        cur = ''
        for s in sentences:
            s = s.strip()
            if not cur:
                if len(s) >= min_chars and len(s) <= max_chars:
                    chunks.append(s)
                    cur = ''
                elif len(s) > max_chars:
                    # hard split long sentence
                    for i in range(0, len(s), max_chars):
                        chunks.append(s[i:i+max_chars])
                    cur = ''
                else:
                    cur = s
            else:
                # try to append sentence to current chunk
                candidate = cur + ' ' + s
                if len(candidate) <= max_chars:
                    cur = candidate
                    if len(cur) >= min_chars:
                        chunks.append(cur.strip())
                        cur = ''
                else:
                    # can't append without exceeding max
                    if len(cur) >= min_chars:
                        chunks.append(cur.strip())
                        cur = ''
                        # process s again
                        if len(s) > max_chars:
                            for i in range(0, len(s), max_chars):
                                chunks.append(s[i:i+max_chars])
                        elif len(s) >= min_chars:
                            chunks.append(s)
                        else:
                            cur = s
                    else:
                        # cur < min and adding s would exceed max -> force flush cur
                        chunks.append(cur.strip())
                        cur = ''
                        if len(s) > max_chars:
                            for i in range(0, len(s), max_chars):
                                chunks.append(s[i:i+max_chars])
                        elif len(s) >= min_chars:
                            chunks.append(s)
                        else:
                            cur = s
        if cur:
            chunks.append(cur.strip())
        return chunks

    def browse_text(self):
        p = filedialog.askopenfilename(filetypes=[('Text files', '*.txt'), ('All files', '*.*')])
        if p:
            self.txt_entry.delete(0, tk.END)
            self.txt_entry.insert(0, p)

    def browse_spk(self):
        p = filedialog.askopenfilename(filetypes=[('WAV files', '*.wav'), ('All files', '*.*')])
        if p:
            self.spk_entry.delete(0, tk.END)
            self.spk_entry.insert(0, p)

    def browse_out(self):
        p = filedialog.askdirectory()
        if p:
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, p)

    def log(self, msg):
        def append():
            self.logbox.insert(tk.END, msg + '\n')
            self.logbox.see(tk.END)
        self.after(0, append)

    def start(self):
        txt = self.txt_entry.get().strip()
        spk = self.spk_entry.get().strip()
        outdir = self.out_entry.get().strip()
        prefix = self.pref_entry.get().strip() or 'gen'
        if not txt:
            messagebox.showwarning('Missing', 'Please choose a text file')
            return
        if not spk:
            messagebox.showwarning('Missing', 'Please choose a speaker prompt wav')
            return
        if not outdir:
            messagebox.showwarning('Missing', 'Please choose an output directory')
            return

        self.start_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.log('Starting generation...')
        thread = threading.Thread(target=self.run_generation, args=(txt, spk, outdir, prefix), daemon=True)
        thread.start()

    def run_generation(self, txt_path, spk_prompt, out_dir, prefix):
        try:
            p = Path(txt_path)
            if not p.exists():
                self.log(f'Text file not found: {txt_path}')
                return
            raw = p.read_text(encoding='utf-8')
            chunks = self.make_chunks(raw, min_chars=50, max_chars=100)
            total = len(chunks)
            if total == 0:
                self.log('No text chunks found.')
                return

            self.log(f'Chunks: {total}')
            self.after(0, lambda: self.progress.config(maximum=total))

            # ensure stdlib 'copy' module is used (avoid local copy.py shadowing)
            try:
                import copy as _copy
                mod_file = getattr(_copy, '__file__', '')
                if mod_file:
                    # if the imported copy module lives in the workspace root, replace it
                    workspace_root = Path.cwd().resolve()
                    try:
                        if Path(mod_file).resolve().parent == workspace_root:
                            stdlib_dir = sysconfig.get_paths().get('stdlib')
                            if stdlib_dir:
                                std_copy = Path(stdlib_dir) / 'copy.py'
                                if std_copy.exists():
                                    spec = importlib.util.spec_from_file_location('copy', str(std_copy))
                                    module = importlib.util.module_from_spec(spec)
                                    spec.loader.exec_module(module)
                                    sys.modules['copy'] = module
                    except Exception:
                        # non-fatal: fall back to whatever 'copy' we have
                        pass
            except Exception:
                pass

            # initialize model
            try:
                from indextts.infer_v2 import IndexTTS2
                self.log('Initializing IndexTTS2...')
                tts = IndexTTS2(cfg_path='checkpoints/config.yaml', model_dir='checkpoints', use_fp16=False, use_cuda_kernel=False, use_deepspeed=False)
            except Exception as ie:
                self.log('Failed to initialize IndexTTS2: ' + str(ie))
                self.log(traceback.format_exc())
                return

            outp = Path(out_dir)
            outp.mkdir(parents=True, exist_ok=True)

            for i, chunk in enumerate(chunks, start=1):
                out_path = outp / f'{prefix}_{i:03d}.wav'
                self.log(f'Generating {out_path} — preview: {chunk[:40] + ("..." if len(chunk)>40 else "")}')
                try:
                    tts.infer(spk_audio_prompt=spk_prompt, text=chunk, output_path=str(out_path), verbose=False)
                except Exception as e:
                    self.log('Error during infer: ' + str(e))
                    self.log(traceback.format_exc())
                self.after(0, lambda v=i: self.progress.config(value=v))

            self.log('Done.')
            messagebox.showinfo('Finished', f'Done — wrote {total} files to {outp}')

        finally:
            self.after(0, lambda: self.start_btn.config(state=tk.NORMAL))

    def on_close(self):
        self.destroy()


def main():
    app = TTSApp()
    app.mainloop()


if __name__ == '__main__':
    main()
