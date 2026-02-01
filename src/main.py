import re
import os
import csv
import json
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections import Counter
from typing import Dict, List

MAX_DISPLAY = 3000
DEBOUNCE_MS = 300
LOG_PATTERN = re.compile(r'(\w+)=((?:".*?")|\S+)')

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# LOG PARSER
def parse_line(line: str) -> Dict[str, str]:
    """Parseia uma linha de log FortiGate no formato key=value."""
    parsed = {}
    for key, value in LOG_PATTERN.findall(line):
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        parsed[key] = value
    return parsed

# CLASSE PRINCIPAL
class CompleteFortiAnalyzer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('Fortinet Log Analyzer')
        self.root.geometry('1500x850')
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.all_logs: List[Dict[str, str]] = []
        self.filtered_logs: List[Dict[str, str]] = []
        self.cols: List[str] = []
        self.page = 0
        self._after_id = None
        self.sort_state = {}
        self._build_ui()

    # GUI
    def _build_ui(self):

        # Barra Superior
        top = tk.Frame(self.root, padx=10, pady=10)
        top.pack(fill=tk.X)

        tk.Button(top, text='Abrir arquivo de Log', command=self.load_file, bg='#3498db', fg='white').pack(side=tk.LEFT)
        tk.Button(top, text='Exportar CSV', command=lambda: self.export_results('csv'), bg="#077936", fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='Exportar JSON', command=lambda: self.export_results('json'), bg='#9b59b6', fg='white').pack(side=tk.LEFT)

        tk.Label(top, text='  Busca:').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self._on_search_change)
        search_entry = tk.Entry(top, textvariable=self.search_var, width=90)
        search_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(top, text='Limpar', command=self.clear_search).pack(side=tk.LEFT, padx=5)

        self.progress = ttk.Progressbar(top, orient=tk.HORIZONTAL, length=180)
        self.progress.pack(side=tk.RIGHT)

        # Área Principal
        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Painel Estatísticas 
        stats_frame = tk.Frame(main, width=220)
        stats_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        tk.Label(stats_frame, text='Estatísticas', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=5)
        self.stats_text = tk.Text(stats_frame, height=30, width=35, state=tk.DISABLED, font=('Consolas', 9))
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # Tabela
        frame = tk.Frame(main)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(frame, show='headings', selectmode='extended')
        self.tree.tag_configure('critical', background='#ffcccc')
        self.tree.tag_configure('warning', background='#fff4cc')

        vsb = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.tree.bind('<Double-1>', self.show_details)

        # Menu de Contexto 
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label='Copiar Linhas Selecionadas', command=self.copy_selection)
        self.tree.bind('<Button-3>', self._show_context_menu)

        # Navegação
        nav = tk.Frame(self.root, pady=5)
        nav.pack(fill=tk.X)
        tk.Button(nav, text='⟨ Anterior', command=self.prev_page).pack(side=tk.LEFT, padx=5)
        tk.Button(nav, text='Próxima ⟩', command=self.next_page).pack(side=tk.LEFT)
        self.page_label = tk.Label(nav, text='Página 1')
        self.page_label.pack(side=tk.LEFT, padx=10)

        # Barra de Status 
        self.status_var = tk.StringVar(value='Pronto')
        tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    # MANIPULAÇÃO DE ARQUIVOS E DADOS
    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[('Logs Fortigate', '*.log;*.txt')])
        if not path:
            return

        self.all_logs.clear()
        self.page = 0
        all_keys = set()
        size = os.path.getsize(path)
        processed = 0

        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.replace('\x00', '').strip()
                    if not line:
                        continue
                    data = parse_line(line)
                    self.all_logs.append(data)
                    all_keys.update(data.keys())
                    processed += len(line)
                    if len(self.all_logs) % 1000 == 0:
                        self.progress['value'] = (processed / size) * 100
                        self.root.update_idletasks()

            priority = ['date', 'time', 'user', 'srcip', 'dstip', 'action', 'status', 'level', 'msg']
            self.cols = [c for c in priority if c in all_keys]
            self.cols += [c for c in sorted(all_keys) if c not in self.cols]

            self.tree.delete(*self.tree.get_children())
            self.tree['columns'] = self.cols
            for col in self.cols:
                self.sort_state[col] = True
                self.tree.heading(col, text=col.upper(), command=lambda c=col: self.sort_by_column(c))
                width = 320 if col in ['msg', 'logdesc'] else 120
                self.tree.column(col, width=width, anchor='w', stretch=False)

            self.apply_filter()
            self.progress['value'] = 0
            self.status_var.set(f'{os.path.basename(path)} | {len(self.all_logs)} linhas | {size/1024/1024:.2f} MB')

        except Exception as e:
            logging.exception(e)
            messagebox.showerror('Erro', str(e))

    def export_results(self, fmt: str):
        if not self.filtered_logs:
            messagebox.showwarning('Aviso', 'Nada para exportar')
            return

        ext = '.csv' if fmt == 'csv' else '.json'
        path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(f'Arquivo {fmt.upper()}', f'*{ext}')])
        if not path:
            return

        try:
            if fmt == 'csv':
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(self.cols)
                    for log in self.filtered_logs:
                        w.writerow([log.get(c, '') for c in self.cols])
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.filtered_logs, f, indent=2)

            messagebox.showinfo('Sucesso', 'Exportação concluída')
        except Exception as e:
            logging.exception(e)
            messagebox.showerror('Erro', str(e))

    # LÓGICA DE FILTRO E BUSCA
    def _on_search_change(self, *_):
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(DEBOUNCE_MS, self.apply_filter)

    def parse_query(self, query: str) -> Dict[str, str]:
        filters = {}
        for part in query.split():
            if ':' in part:
                try:
                    k, v = part.split(':', 1)
                    filters[k.lower()] = v.lower()
                except ValueError:
                    continue
        return filters

    def apply_filter(self):
        self.filtered_logs.clear()
        q = self.search_var.get().lower()
        field_filters = self.parse_query(q)

        for log in self.all_logs:
            if field_filters:
                if not all(v in str(log.get(k, '')).lower() for k, v in field_filters.items()):
                    continue
            elif q and not any(q in str(v).lower() for v in log.values()):
                continue
            self.filtered_logs.append(log)

        self.page = 0
        self.refresh_table()
        self.update_stats()

    def clear_search(self):
        self.search_var.set('')
        self.apply_filter()

    # GERENCIAMENTO DA TABELA E VISUALIZAÇÃO
    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        start = self.page * MAX_DISPLAY
        end = start + MAX_DISPLAY

        for log in self.filtered_logs[start:end]:
            vals = [log.get(c, '') for c in self.cols]
            level = log.get('level', '').lower()
            action = log.get('action', '').lower()
            
            tag = ''
            if level in ['alert', 'critical', 'error'] or action in ['deny', 'block']:
                tag = 'critical'
            elif level in ['warning', 'notice']:
                tag = 'warning'
                
            self.tree.insert('', tk.END, values=vals, tags=(tag,))

        total_pages = max(1, (len(self.filtered_logs) - 1) // MAX_DISPLAY + 1)
        self.page_label.config(text=f'Página {self.page + 1} / {total_pages}')
        self.status_var.set(f'Exibindo {min(len(self.filtered_logs), end) - start} de {len(self.filtered_logs)} resultados')

    def sort_by_column(self, col: str):
        asc = self.sort_state.get(col, True)
        try:
            self.filtered_logs.sort(key=lambda x: float(x.get(col, 0)), reverse=not asc)
        except ValueError:
            self.filtered_logs.sort(key=lambda x: str(x.get(col, '')).lower(), reverse=not asc)

        self.sort_state[col] = not asc

        for c in self.cols:
            self.tree.heading(c, text=c.upper() + (' ▲' if (c == col and asc) else ' ▼' if (c == col) else ''))
            
        self.refresh_table()

    def update_stats(self):
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)

        if not self.filtered_logs:
            self.stats_text.config(state=tk.DISABLED)
            return

        actions = Counter(log.get('action', 'unknown') for log in self.filtered_logs)
        levels = Counter(log.get('level', 'unknown') for log in self.filtered_logs)
        srcips = Counter(log.get('srcip', 'unknown') for log in self.filtered_logs)

        self.stats_text.insert(tk.END, "TOP ACTIONS:\n" + "-"*20 + "\n")
        for k, v in actions.most_common(5):
            self.stats_text.insert(tk.END, f"{k}: {v}\n")
        self.stats_text.insert(tk.END, "\nTOP LEVELS:\n" + "-"*20 + "\n")
        for k, v in levels.most_common(5):
            self.stats_text.insert(tk.END, f"{k}: {v}\n")
        self.stats_text.insert(tk.END, "\nTOP SRC IPs:\n" + "-"*20 + "\n")
        for k, v in srcips.most_common(8):
            self.stats_text.insert(tk.END, f"{k}: {v}\n")

        self.stats_text.config(state=tk.DISABLED)

    # INTERAÇÕES E MENUS
    def show_details(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        
        win = tk.Toplevel(self.root)
        win.title('Inspeção de Log')
        win.geometry('490x560')

        txt = tk.Text(win, font=('Consolas', 10), padx=15, pady=15)
        txt.pack(fill=tk.BOTH, expand=True)

        query = self.search_var.get().lower()
        values = self.tree.item(item_id)['values']

        for k, v in zip(self.cols, values):
            line = f'{k.upper():<18}: {v}\n'
            start_idx = txt.index(tk.END)
            txt.insert(tk.END, line)
            if query and query in str(v).lower():
                txt.tag_add('highlight', f'{start_idx}', f'{txt.index(tk.END)}')

        txt.tag_configure('highlight', background='#ffffaa')
        txt.config(state=tk.DISABLED)

    def _show_context_menu(self, event):
        if self.tree.selection():
            self.context_menu.post(event.x_root, event.y_root)

    def copy_selection(self):
        selected = self.tree.selection()
        if not selected:
            return
        output = ['\t'.join(self.cols)]
        for item in selected:
            output.append('\t'.join(map(str, self.tree.item(item)['values'])))
        self.root.clipboard_clear()
        self.root.clipboard_append('\n'.join(output))
        messagebox.showinfo('Copiado', f'{len(selected)} linhas copiadas')

    # NAVEGAÇÃO
    def next_page(self):
        if (self.page + 1) * MAX_DISPLAY < len(self.filtered_logs):
            self.page += 1
            self.refresh_table()

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.refresh_table()

# BLOCO DE EXECUÇÃO
if __name__ == '__main__':
    root = tk.Tk()
    app = CompleteFortiAnalyzer(root)
    root.mainloop()