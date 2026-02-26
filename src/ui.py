import os
import logging
from datetime import datetime, time
from typing import Dict

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkcalendar import DateEntry

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    plt.ioff()
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning("Matplotlib não instalado. Gráficos desabilitados.")

from log_engine import LogEngine, FilterCriteria


class UIStyle:
    BG_MAIN          = "#F0F2F7"
    BG_CARD          = "#FFFFFF"
    BG_TOOLBAR       = "#1E3148"
    BG_NAV           = "#EAF0F8"
    BG_STATUS        = "#E4ECF5"
    BG_BUTTON        = "#2B6CB0"
    BG_BUTTON_ACTIVE = "#1A56A0"
    BG_TBTN          = "#2D4A6E"
    BG_TBTN_ACTIVE   = "#3A5F85"
    BORDER_COLOR     = "#C8D5E0"
    SEPARATOR_COLOR  = "#D1DBE8"
    ACCENT           = BG_BUTTON
    SUCCESS          = "#276749"
    WARNING          = "#975A16"
    DANGER           = "#C53030"
    FG_MAIN          = "#1A2535"
    FG_ON_DARK       = "#EDF2F8"
    FG_MUTED         = "#718096"
    FG_STATUS        = "#4A5568"
    FG_BUTTON        = "#FFFFFF"
    FONT_NORMAL      = ('Segoe UI', 10)
    FONT_BOLD        = ('Segoe UI', 10, 'bold')
    FONT_SMALL       = ('Segoe UI', 9)
    FONT_MONO        = ('Consolas', 10)

    @staticmethod
    def apply_ttk_styles():
        style = ttk.Style()
        style.theme_use('clam')

        style.configure(
            "Treeview",
            background=UIStyle.BG_CARD,
            foreground=UIStyle.FG_MAIN,
            fieldbackground=UIStyle.BG_CARD,
            rowheight=26,
            bordercolor=UIStyle.BORDER_COLOR,
            font=UIStyle.FONT_NORMAL,
        )
        style.map(
            "Treeview",
            background=[("selected", UIStyle.ACCENT)],
            foreground=[("selected", UIStyle.FG_BUTTON)],
        )
        style.configure(
            "Treeview.Heading",
            background="#EDF2F8",
            foreground=UIStyle.FG_MAIN,
            font=UIStyle.FONT_BOLD,
            relief=tk.FLAT,
        )
        style.map(
            "Treeview.Heading",
            background=[("active", "#DDE7F2")],
        )
        style.configure(
            "TSpinbox",
            background=UIStyle.BG_CARD,
            foreground=UIStyle.FG_MAIN,
            fieldbackground=UIStyle.BG_CARD,
            insertcolor=UIStyle.FG_MAIN,
            arrowcolor=UIStyle.FG_MUTED,
        )

    @staticmethod
    def create_button(parent, text, command, **kwargs):
        return tk.Button(
            parent, text=text, command=command,
            bg=UIStyle.BG_BUTTON,
            fg=UIStyle.FG_BUTTON,
            font=UIStyle.FONT_NORMAL,
            relief=tk.FLAT,
            cursor='hand2',
            activebackground=UIStyle.BG_BUTTON_ACTIVE,
            activeforeground=UIStyle.FG_BUTTON,
            padx=12, pady=6,
            **kwargs
        )

    @staticmethod
    def create_toolbar_button(parent, text, command, **kwargs):
        return tk.Button(
            parent, text=text, command=command,
            bg=UIStyle.BG_TBTN,
            fg=UIStyle.FG_ON_DARK,
            font=UIStyle.FONT_NORMAL,
            relief=tk.FLAT,
            cursor='hand2',
            activebackground=UIStyle.BG_TBTN_ACTIVE,
            activeforeground=UIStyle.FG_ON_DARK,
            padx=12, pady=6,
            bd=0,
            **kwargs
        )

    @staticmethod
    def create_label(parent, text, bold=False, font=None, bg=None, fg=None, **kwargs):
        if font is None:
            font = UIStyle.FONT_BOLD if bold else UIStyle.FONT_NORMAL
        return tk.Label(
            parent, text=text,
            bg=bg if bg is not None else UIStyle.BG_MAIN,
            fg=fg if fg is not None else UIStyle.FG_MAIN,
            font=font,
            **kwargs
        )

    @staticmethod
    def create_entry(parent, textvariable, width=30, **kwargs):
        return tk.Entry(
            parent,
            textvariable=textvariable,
            font=UIStyle.FONT_NORMAL,
            bg=UIStyle.BG_CARD,
            fg=UIStyle.FG_MAIN,
            insertbackground=UIStyle.FG_MAIN,
            relief=tk.SOLID,
            bd=1,
            width=width,
            **kwargs
        )

    @staticmethod
    def create_frame(parent, **kwargs):
        return tk.Frame(parent, bg=UIStyle.BG_MAIN, **kwargs)


class ToolbarView:
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=UIStyle.BG_TOOLBAR, height=48)

        self.btn_load = UIStyle.create_toolbar_button(self.frame, 'Abrir Log', None)
        self.btn_load.pack(side=tk.LEFT, padx=(8, 2), pady=6)

        self._vsep()

        self.btn_charts = UIStyle.create_toolbar_button(self.frame, 'Graficos ▼', None)
        self.btn_charts.pack(side=tk.LEFT, padx=2, pady=6)
        self.charts_menu = tk.Menu(
            self.frame, tearoff=0,
            bg=UIStyle.BG_CARD, fg=UIStyle.FG_MAIN,
            activebackground=UIStyle.ACCENT,
            activeforeground=UIStyle.FG_BUTTON,
            font=UIStyle.FONT_NORMAL,
            bd=1, relief=tk.SOLID,
        )

        self._vsep()

        self.btn_csv = UIStyle.create_toolbar_button(self.frame, 'Exportar CSV', None)
        self.btn_csv.pack(side=tk.LEFT, padx=2, pady=6)

        self.btn_json = UIStyle.create_toolbar_button(self.frame, 'Exportar JSON', None)
        self.btn_json.pack(side=tk.LEFT, padx=2, pady=6)

        self.progress = ttk.Progressbar(
            self.frame, orient=tk.HORIZONTAL, length=180, mode='determinate'
        )
        self.progress.pack(side=tk.RIGHT, padx=12, pady=12)

    def _vsep(self):
        tk.Frame(
            self.frame, bg=UIStyle.BG_TBTN_ACTIVE, width=1
        ).pack(side=tk.LEFT, fill=tk.Y, pady=8, padx=4)


class FilterView:
    def __init__(self, parent):
        self.frame = tk.Frame(
            parent, bg=UIStyle.BG_CARD,
            highlightbackground=UIStyle.BORDER_COLOR,
            highlightthickness=1,
        )

        grid = tk.Frame(self.frame, bg=UIStyle.BG_CARD, padx=12, pady=10)
        grid.pack(fill=tk.X)
        grid.columnconfigure(0, weight=1)

        UIStyle.create_label(
            grid, 'Busca Geral', bold=True, bg=UIStyle.BG_CARD
        ).grid(row=0, column=0, sticky='w', pady=(0, 4))

        UIStyle.create_label(
            grid, 'Data/Hora Inicial', bold=True, bg=UIStyle.BG_CARD
        ).grid(row=0, column=2, sticky='w', padx=(12, 0), pady=(0, 4))

        UIStyle.create_label(
            grid, 'Data/Hora Final', bold=True, bg=UIStyle.BG_CARD
        ).grid(row=0, column=4, sticky='w', padx=(12, 0), pady=(0, 4))

        self.search_var = tk.StringVar()
        UIStyle.create_entry(grid, self.search_var, width=50).grid(
            row=1, column=0, sticky='ew', ipady=4
        )

        self._vsep(grid, column=1)
        self._vsep(grid, column=3)

        self.date_start, self.hour_start, self.min_start, self.sec_start = \
            self._create_datetime_controls(grid, row=1, column=2, default_time='00:00:00')

        self.date_end, self.hour_end, self.min_end, self.sec_end = \
            self._create_datetime_controls(grid, row=1, column=4, default_time='23:59:59')

        ctrl = tk.Frame(grid, bg=UIStyle.BG_CARD)
        ctrl.grid(row=0, column=5, rowspan=2, sticky='ns', padx=(16, 0))

        self.datetime_enabled = tk.BooleanVar(value=False)
        tk.Checkbutton(
            ctrl, text='Filtrar por periodo',
            variable=self.datetime_enabled,
            bg=UIStyle.BG_CARD,
            fg=UIStyle.FG_MAIN,
            activebackground=UIStyle.BG_CARD,
            selectcolor=UIStyle.BG_CARD,
            font=UIStyle.FONT_NORMAL,
        ).pack(anchor='w', pady=(0, 6))

        self.btn_clear = UIStyle.create_button(ctrl, 'Limpar Filtros', None)
        self.btn_clear.pack(fill=tk.X)

    def _vsep(self, parent, column):
        tk.Frame(
            parent, bg=UIStyle.SEPARATOR_COLOR, width=1
        ).grid(row=0, column=column, rowspan=2, sticky='ns', padx=10)

    def _create_datetime_controls(self, parent, row, column, default_time):
        container = tk.Frame(parent, bg=UIStyle.BG_CARD)
        container.grid(row=row, column=column, sticky='w', padx=(12, 0))

        date_entry = DateEntry(
            container, width=11, date_pattern='yyyy-mm-dd',
            background=UIStyle.BG_BUTTON,
            foreground=UIStyle.FG_BUTTON,
            borderwidth=1,
            font=UIStyle.FONT_NORMAL,
            headersbackground=UIStyle.BG_TOOLBAR,
            headersforeground=UIStyle.FG_ON_DARK,
            selectbackground=UIStyle.ACCENT,
            selectforeground=UIStyle.FG_BUTTON,
            normalbackground=UIStyle.BG_CARD,
            normalforeground=UIStyle.FG_MAIN,
            weekendbackground=UIStyle.BG_CARD,
            weekendforeground=UIStyle.FG_MAIN,
            othermonthbackground=UIStyle.BG_MAIN,
            othermonthforeground=UIStyle.FG_MUTED,
        )
        date_entry.pack(side=tk.LEFT, ipady=3)

        tk.Frame(container, bg=UIStyle.BG_CARD, width=8).pack(side=tk.LEFT)

        h, m, s = default_time.split(':')

        hour = ttk.Spinbox(container, from_=0, to=23, width=3,
                           format='%02.0f', font=UIStyle.FONT_NORMAL)
        hour.set(h)
        hour.pack(side=tk.LEFT, ipady=3)

        self._time_sep(container)

        minute = ttk.Spinbox(container, from_=0, to=59, width=3,
                             format='%02.0f', font=UIStyle.FONT_NORMAL)
        minute.set(m)
        minute.pack(side=tk.LEFT, ipady=3)

        self._time_sep(container)

        second = ttk.Spinbox(container, from_=0, to=59, width=3,
                             format='%02.0f', font=UIStyle.FONT_NORMAL)
        second.set(s)
        second.pack(side=tk.LEFT, ipady=3)

        return date_entry, hour, minute, second

    def _time_sep(self, container):
        tk.Label(
            container, text=':',
            bg=UIStyle.BG_CARD,
            fg=UIStyle.FG_MUTED,
            font=UIStyle.FONT_BOLD,
        ).pack(side=tk.LEFT, padx=1)


class TableView:
    def __init__(self, parent):
        self.frame = tk.LabelFrame(
            parent, text=' Logs ',
            font=UIStyle.FONT_BOLD,
            bg=UIStyle.BG_MAIN,
            fg=UIStyle.FG_MAIN,
            relief=tk.GROOVE, bd=1,
        )

        container = tk.Frame(self.frame, bg=UIStyle.BG_CARD)
        container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.tree = ttk.Treeview(container, show='headings', selectmode='extended')
        self.tree.tag_configure('critical', background="#FFF0F0", foreground="#9B2C2C")
        self.tree.tag_configure('warning',  background="#FFFBEB", foreground="#744210")
        self.tree.tag_configure('evenrow',  background=UIStyle.BG_CARD)
        self.tree.tag_configure('oddrow',   background="#F7FAFC")

        vsb = ttk.Scrollbar(container, orient='vertical',   command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)


class StatsView:
    def __init__(self, parent):
        self.frame = tk.LabelFrame(
            parent, text=' Estatisticas ',
            font=UIStyle.FONT_BOLD,
            bg=UIStyle.BG_MAIN,
            fg=UIStyle.FG_MAIN,
            relief=tk.GROOVE, bd=1,
        )

        self.text = tk.Text(
            self.frame, height=30, width=30,
            state=tk.DISABLED,
            font=UIStyle.FONT_MONO,
            bg=UIStyle.BG_CARD,
            fg=UIStyle.FG_MAIN,
            insertbackground=UIStyle.FG_MAIN,
            relief=tk.FLAT,
            padx=10, pady=10,
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)


class NavigationView:
    def __init__(self, parent):
        self.frame = tk.Frame(
            parent, bg=UIStyle.BG_NAV,
            highlightbackground=UIStyle.BORDER_COLOR,
            highlightthickness=1,
        )

        self.btn_prev = UIStyle.create_button(self.frame, '◀ Anterior', None)
        self.btn_prev.pack(side=tk.LEFT, padx=(8, 2), pady=5)

        self.btn_next = UIStyle.create_button(self.frame, 'Proxima ▶', None)
        self.btn_next.pack(side=tk.LEFT, padx=2, pady=5)

        self.label = tk.Label(
            self.frame,
            text='Pagina 1 / 1',
            bg=UIStyle.BG_NAV,
            fg=UIStyle.FG_STATUS,
            font=UIStyle.FONT_BOLD,
        )
        self.label.pack(side=tk.LEFT, padx=14)


class StatusView:
    def __init__(self, parent):
        self.var = tk.StringVar(value='Pronto')
        self.label = tk.Label(
            parent,
            textvariable=self.var,
            bd=0, anchor=tk.W,
            bg=UIStyle.BG_STATUS,
            fg=UIStyle.FG_STATUS,
            font=UIStyle.FONT_SMALL,
            padx=10, pady=4,
        )


class FortiAnalyzerApp:
    PAGE_SIZE   = 3000
    DEBOUNCE_MS = 300
    APPNAME     = "Fortinet Log Analyzer"
    APPVERSION  = "V2"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(self.APPNAME + " " + self.APPVERSION)
        self.root.geometry('1600x900')
        self.root.configure(bg=UIStyle.BG_MAIN)

        UIStyle.apply_ttk_styles()

        self.engine = LogEngine()
        self.current_page = 0
        self.sort_state: Dict[str, bool] = {}
        self._debounce_id = None
        self._chart_windows = []

        self._build_ui()
        self._connect_events()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_ui(self):
        self.toolbar = ToolbarView(self.root)
        self.toolbar.frame.pack(fill=tk.X)

        self.filters = FilterView(self.root)
        self.filters.frame.pack(fill=tk.X, padx=10, pady=(8, 0))

        main = UIStyle.create_frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 0))

        self.stats = StatsView(main)
        self.stats.frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))

        self.table = TableView(main)
        self.table.frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.navigation = NavigationView(self.root)
        self.navigation.frame.pack(fill=tk.X, padx=10, pady=(4, 4))

        self.status = StatusView(self.root)
        self.status.label.pack(side=tk.BOTTOM, fill=tk.X)

        self.context_menu = tk.Menu(
            self.root, tearoff=0,
            bg=UIStyle.BG_CARD, fg=UIStyle.FG_MAIN,
            activebackground=UIStyle.ACCENT,
            activeforeground=UIStyle.FG_BUTTON,
            font=UIStyle.FONT_NORMAL,
        )
        self.context_menu.add_command(
            label='Copiar Linhas Selecionadas',
            command=self._copy_selection,
        )

    def _connect_events(self):
        self.toolbar.btn_load.config(command=self._load_file)
        self.toolbar.btn_csv.config(command=lambda: self._export('csv'))
        self.toolbar.btn_json.config(command=lambda: self._export('json'))

        self.toolbar.btn_charts.config(command=self._show_charts_menu)
        self.toolbar.charts_menu.add_command(
            label='Volume de Logs', command=self._show_volume_chart
        )
        self.toolbar.charts_menu.add_command(
            label='Heatmap de Logs (30min)', command=self._show_heatmap_chart
        )
        self.toolbar.charts_menu.add_separator()
        self.toolbar.charts_menu.add_command(
            label='Top 5 IPs de Origem',
            command=lambda: self._show_top_chart('srcip', 'Top 5 IPs de Origem', 5)
        )
        self.toolbar.charts_menu.add_command(
            label='Top 5 IPs de Destino',
            command=lambda: self._show_top_chart('dstip', 'Top 5 IPs de Destino', 5)
        )
        self.toolbar.charts_menu.add_command(
            label='Top 5 Acoes',
            command=lambda: self._show_top_chart('action', 'Top 5 Acoes', 5)
        )
        self.toolbar.charts_menu.add_command(
            label='Distribuicao de Niveis',
            command=self._plot_level_distribution
        )
        self.toolbar.charts_menu.add_command(
            label='Erros/Critical ao Longo do Tempo',
            command=self._plot_error_trend
        )

        self.filters.search_var.trace_add('write', self._on_search_change)
        self.filters.btn_clear.config(command=self._clear_filters)

        self.filters.date_start.bind('<<DateEntrySelected>>', self._on_datetime_change)
        self.filters.date_end.bind('<<DateEntrySelected>>',   self._on_datetime_change)

        for spinbox in [
            self.filters.hour_start, self.filters.min_start, self.filters.sec_start,
            self.filters.hour_end,   self.filters.min_end,   self.filters.sec_end,
        ]:
            for event in ('<KeyRelease>', '<<Increment>>', '<<Decrement>>'):
                spinbox.bind(event, self._on_datetime_change)

        self.filters.datetime_enabled.trace_add('write', lambda *_: self._apply_filters())

        self.table.tree.bind('<Double-1>', self._show_details)
        self.table.tree.bind('<Button-3>', self._show_context_menu)

        self.navigation.btn_prev.config(command=self._prev_page)
        self.navigation.btn_next.config(command=self._next_page)

    def _load_file(self):
        path = filedialog.askopenfilename(filetypes=[('Logs', '*.log;*.txt')])
        if not path:
            return

        try:
            total, size = self.engine.load_file(path)

            self.table.tree.delete(*self.table.tree.get_children())
            self.table.tree['columns'] = self.engine.columns

            for col in self.engine.columns:
                self.sort_state[col] = True
                self.table.tree.heading(
                    col, text=col.upper(),
                    command=lambda c=col: self._sort_by_column(c)
                )
                width = 320 if col in ['msg', 'logdesc'] else 120
                self.table.tree.column(col, width=width, anchor='w', stretch=False)

            self._apply_filters()
            self.status.var.set(
                f'{os.path.basename(path)}  |  {total:,} linhas  |  '
                f'{size / 1024 / 1024:.2f} MB'
            )

        except Exception as e:
            logging.exception(e)
            messagebox.showerror('Erro', str(e))

    def _export(self, fmt: str):
        if not self.engine.filtered_logs:
            messagebox.showwarning('Aviso', 'Nada para exportar.')
            return

        ext = f'.{fmt}'
        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f'Arquivo {fmt.upper()}', f'*{ext}')]
        )
        if not path:
            return

        try:
            if fmt == 'csv':
                self.engine.export_csv(path)
            else:
                self.engine.export_json(path)
            messagebox.showinfo('Exportacao concluida', f'Arquivo salvo em:\n{path}')
        except Exception as e:
            logging.exception(e)
            messagebox.showerror('Erro', str(e))

    def _on_search_change(self, *_):
        if self._debounce_id:
            self.root.after_cancel(self._debounce_id)
        self._debounce_id = self.root.after(self.DEBOUNCE_MS, self._apply_filters)

    def _on_datetime_change(self, *_):
        if self.filters.datetime_enabled.get():
            self._on_search_change()

    def _apply_filters(self):
        field_filters, free_text = self.engine.parse_query(
            self.filters.search_var.get().strip()
        )

        date_start = None
        date_end   = None

        if self.filters.datetime_enabled.get():
            try:
                date_start = datetime.combine(
                    self.filters.date_start.get_date(),
                    time(int(self.filters.hour_start.get()),
                         int(self.filters.min_start.get()),
                         int(self.filters.sec_start.get()))
                )
                date_end = datetime.combine(
                    self.filters.date_end.get_date(),
                    time(int(self.filters.hour_end.get()),
                         int(self.filters.min_end.get()),
                         int(self.filters.sec_end.get()))
                )
            except Exception as e:
                logging.error(f'Erro ao processar data/hora: {e}')

        criteria = FilterCriteria(
            field_filters=field_filters,
            free_text=free_text,
            date_start=date_start,
            date_end=date_end,
        )

        self.engine.apply_filter(criteria)
        self.current_page = 0
        self._refresh_table()
        self._update_stats()

    def _clear_filters(self):
        self.filters.search_var.set('')
        self.filters.datetime_enabled.set(False)
        self.filters.hour_start.set('00')
        self.filters.min_start.set('00')
        self.filters.sec_start.set('00')
        self.filters.hour_end.set('23')
        self.filters.min_end.set('59')
        self.filters.sec_end.set('59')
        self._apply_filters()

    def _sort_by_column(self, column: str):
        asc = self.sort_state.get(column, True)
        self.engine.sort_logs(column, asc)
        self.sort_state[column] = not asc

        for col in self.engine.columns:
            indicator = ' ▲' if (col == column and asc) else (' ▼' if col == column else '')
            self.table.tree.heading(col, text=col.upper() + indicator)

        self._refresh_table()

    def _refresh_table(self):
        self.table.tree.delete(*self.table.tree.get_children())
        page_logs = self.engine.get_page(self.current_page, self.PAGE_SIZE)

        for index, log in enumerate(page_logs):
            vals   = [log.get(c, '') for c in self.engine.columns]
            level  = log.get('level',  '').lower()
            action = log.get('action', '').lower()

            base_tag = 'evenrow' if index % 2 == 0 else 'oddrow'

            if level in ('alert', 'critical', 'error') or action in ('deny', 'block'):
                tag = ('critical', base_tag)
            elif level in ('warning', 'notice'):
                tag = ('warning', base_tag)
            else:
                tag = base_tag

            self.table.tree.insert('', tk.END, values=vals, tags=tag)

        total       = len(self.engine.filtered_logs)
        total_pages = max(1, (total - 1) // self.PAGE_SIZE + 1)
        self.navigation.label.config(
            text=f'Pagina {self.current_page + 1} / {total_pages}'
        )

        shown = len(page_logs)
        self.status.var.set(f'Exibindo {shown:,} de {total:,} registros')

    def _update_stats(self):
        self.stats.text.config(state=tk.NORMAL)
        self.stats.text.delete('1.0', tk.END)

        if not self.engine.filtered_logs:
            self.stats.text.insert(tk.END, 'Nenhum log encontrado.')
            self.stats.text.config(state=tk.DISABLED)
            return

        stats = self.engine.get_statistics()

        self.stats.text.tag_configure(
            'header',
            font=(UIStyle.FONT_MONO[0], UIStyle.FONT_MONO[1], 'bold'),
            foreground=UIStyle.ACCENT,
        )
        self.stats.text.tag_configure(
            'divider',
            foreground=UIStyle.FG_MUTED,
        )

        def write_section(title, counter, n):
            self.stats.text.insert(tk.END, f' {title}\n', 'header')
            self.stats.text.insert(tk.END, ' ' + '─' * 24 + '\n', 'divider')
            for k, v in counter.most_common(n):
                self.stats.text.insert(tk.END, f'  {k}: {v:,}\n')
            self.stats.text.insert(tk.END, '\n')

        write_section('TOP ACTIONS', stats['actions'], 5)
        write_section('TOP LEVELS',  stats['levels'],  5)
        write_section('TOP SRC IPs', stats['srcips'],  8)
        write_section('TOP DST IPs', stats['dstips'],  8)

        self.stats.text.config(state=tk.DISABLED)

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_table()

    def _next_page(self):
        max_page = max(0, (len(self.engine.filtered_logs) - 1) // self.PAGE_SIZE)
        if self.current_page < max_page:
            self.current_page += 1
            self._refresh_table()

    def _show_charts_menu(self):
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showwarning(
                "Matplotlib nao disponivel",
                "Instale matplotlib para usar graficos:\npip install matplotlib",
            )
            return

        if not self.engine.filtered_logs:
            messagebox.showwarning("Aviso", "Nenhum log para gerar grafico.")
            return

        self.toolbar.charts_menu.post(
            self.toolbar.btn_charts.winfo_rootx(),
            self.toolbar.btn_charts.winfo_rooty() + self.toolbar.btn_charts.winfo_height(),
        )

    def _make_chart_window(self, title: str, geometry: str) -> tk.Toplevel:
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(geometry)
        win.configure(bg=UIStyle.BG_MAIN)
        self._chart_windows.append(win)
        return win

    def _chart_btn_frame(self, win: tk.Toplevel) -> tk.Frame:
        frame = tk.Frame(win, bg=UIStyle.BG_STATUS, pady=4)
        frame.pack(fill=tk.X, side=tk.BOTTOM)
        return frame

    def _add_export_button(self, btn_frame: tk.Frame, fig) -> None:
        def export_image():
            filepath = filedialog.asksaveasfilename(
                defaultextension='.png',
                filetypes=[('PNG', '*.png'), ('JPEG', '*.jpg'), ('PDF', '*.pdf')]
            )
            if filepath:
                fig.savefig(filepath, dpi=300, bbox_inches='tight')
                messagebox.showinfo('Sucesso', f'Imagem salva em:\n{filepath}')

        UIStyle.create_button(btn_frame, 'Exportar Imagem', export_image).pack(
            side=tk.LEFT, padx=8, pady=4
        )

    def _on_chart_close(self, win: tk.Toplevel, fig) -> None:
        plt.close(fig)
        if win in self._chart_windows:
            self._chart_windows.remove(win)
        win.destroy()

    def _embed_canvas(self, fig, win: tk.Toplevel, btn_frame: tk.Frame) -> None:
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._add_export_button(btn_frame, fig)
        win.protocol("WM_DELETE_WINDOW", lambda: self._on_chart_close(win, fig))

    def _show_volume_chart(self):
        timeline_data = self.engine.get_timeline_data()
        if not timeline_data:
            messagebox.showinfo('Info', 'Dados insuficientes para volume.')
            return

        win       = self._make_chart_window('Volume de Logs', '1000x650')
        btn_frame = self._chart_btn_frame(win)

        fig, ax = plt.subplots(figsize=(11, 6))
        hours  = list(timeline_data.keys())
        counts = list(timeline_data.values())

        ax.plot(range(len(hours)), counts, marker='o', linewidth=2,
                markersize=5, color='#2B6CB0', markerfacecolor='#63B3ED')
        ax.fill_between(range(len(hours)), counts, alpha=0.15, color='#2B6CB0')
        ax.set_xlabel('Data/Hora', fontsize=11, fontweight='bold')
        ax.set_ylabel('Quantidade de Logs', fontsize=11, fontweight='bold')
        ax.set_title('Volume de Logs ao Longo do Tempo', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')

        step = max(1, len(hours) // 10)
        ax.set_xticks(range(0, len(hours), step))
        ax.set_xticklabels([hours[i] for i in range(0, len(hours), step)],
                           rotation=45, ha='right', fontsize=9)
        plt.tight_layout()

        self._embed_canvas(fig, win, btn_frame)

    def _show_top_chart(self, field: str, title: str, limit: int = 5):
        top_data = self.engine.get_top_data(field, limit=limit)
        if not top_data:
            messagebox.showinfo('Info', f'Nenhum dado disponivel para {field}.')
            return

        win       = self._make_chart_window(title, '900x650')
        btn_frame = self._chart_btn_frame(win)

        fig, ax = plt.subplots(figsize=(10, 6))
        labels = [item[0] for item in top_data]
        values = [item[1] for item in top_data]

        palette = ['#2B6CB0', '#3182CE', '#4299E1', '#63B3ED', '#90CDF4']
        bars = ax.barh(range(len(labels)), values,
                       color=palette[:len(labels)], edgecolor='none')
        ax.invert_yaxis()
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_xlabel('Quantidade', fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=13, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')

        for i, (bar, value) in enumerate(zip(bars, values)):
            ax.text(value + max(values) * 0.01, i, f'{value:,}',
                    va='center', fontsize=10, fontweight='bold')
        plt.tight_layout()

        self._embed_canvas(fig, win, btn_frame)

    def _plot_error_trend(self):
        data = self.engine.get_error_time_series()
        if not data:
            messagebox.showinfo("Info", "Sem erros/criticos no periodo.")
            return

        win       = self._make_chart_window('Erros / Critical ao Longo do Tempo', '1000x600')
        btn_frame = self._chart_btn_frame(win)

        times  = list(data.keys())
        values = list(data.values())

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(range(len(times)), values, marker='o', linewidth=2,
                markersize=5, color='#C53030', markerfacecolor='#FC8181')
        ax.fill_between(range(len(times)), values, alpha=0.15, color='#C53030')
        ax.set_title('Erros / Critical ao Longo do Tempo', fontsize=13, fontweight='bold')
        ax.set_xlabel('Data/Hora', fontsize=11, fontweight='bold')
        ax.set_ylabel('Quantidade', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')

        step = max(1, len(times) // 10)
        ax.set_xticks(range(0, len(times), step))
        ax.set_xticklabels([times[i] for i in range(0, len(times), step)],
                           rotation=45, ha='right', fontsize=9)
        plt.tight_layout()

        self._embed_canvas(fig, win, btn_frame)

    def _plot_level_distribution(self):
        data = self.engine.get_level_counts()
        if not data:
            messagebox.showinfo("Info", "Sem dados para exibir.")
            return

        filtered = [(k, v) for k, v in data.items() if k and v > 0]
        if not filtered:
            messagebox.showinfo("Info", "Sem niveis validos.")
            return

        labels = [k for k, v in filtered]
        values = [v for k, v in filtered]

        win       = self._make_chart_window('Distribuicao de Niveis', '700x600')
        btn_frame = self._chart_btn_frame(win)

        palette = ['#2B6CB0', '#C53030', '#975A16', '#276749', '#6B46C1', '#B83280']
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.set_title('Distribuicao de Niveis', fontsize=13, fontweight='bold')

        if len(labels) <= 6:
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=palette[:len(labels)])
        else:
            ax.barh(labels, values, color=palette[:min(len(labels), 6)], edgecolor='none')
            ax.set_xlabel('Quantidade', fontsize=11, fontweight='bold')
            ax.grid(True, axis='x', alpha=0.3, linestyle='--')

        plt.tight_layout()

        self._embed_canvas(fig, win, btn_frame)

    def _show_heatmap_chart(self):
        interval_data = self.engine.get_30min_distribution()
        if not interval_data:
            messagebox.showinfo('Info', 'Dados insuficientes para heatmap.')
            return

        win       = self._make_chart_window('Heatmap de Logs (30min)', '1200x650')
        btn_frame = self._chart_btn_frame(win)

        fig, ax = plt.subplots(figsize=(14, 6))
        intervals = list(interval_data.keys())
        counts    = list(interval_data.values())

        max_count = max(counts) if counts else 1
        colors    = plt.cm.Blues([0.2 + 0.8 * (c / max_count) for c in counts])

        bars = ax.bar(range(len(intervals)), counts,
                      color=colors, edgecolor='none')

        for bar, count in zip(bars, counts):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, count, f'{count:,}',
                        ha='center', va='bottom', fontsize=7, fontweight='bold')

        ax.set_xlabel('Data/Hora', fontsize=11, fontweight='bold')
        ax.set_ylabel('Quantidade de Logs', fontsize=11, fontweight='bold')
        ax.set_title('Distribuicao de Logs (intervalos de 30min)', fontsize=13, fontweight='bold')
        ax.set_xticks(range(len(intervals)))
        ax.set_xticklabels(intervals, rotation=90, ha='right', fontsize=7)
        ax.grid(True, axis='y', alpha=0.3, linestyle='--')

        if counts:
            avg = sum(counts) / len(counts)
            ax.axhline(y=avg, color='#C53030', linestyle='--', linewidth=1.5,
                       label=f'Media: {avg:.0f}', alpha=0.8)
            ax.legend(fontsize=10)

        plt.tight_layout()

        self._embed_canvas(fig, win, btn_frame)

    def _show_details(self, event):
        item_id = self.table.tree.identify_row(event.y)
        if not item_id:
            return

        win = tk.Toplevel(self.root)
        win.title('Inspecao de Log')
        win.geometry('560x680')
        win.configure(bg=UIStyle.BG_MAIN)

        header = tk.Frame(win, bg=UIStyle.BG_TOOLBAR, pady=10)
        header.pack(fill=tk.X)
        tk.Label(
            header, text='DETALHES DO REGISTRO',
            font=UIStyle.FONT_BOLD,
            bg=UIStyle.BG_TOOLBAR,
            fg=UIStyle.FG_ON_DARK,
        ).pack()

        txt = tk.Text(
            win,
            font=UIStyle.FONT_MONO,
            padx=12, pady=12,
            bg=UIStyle.BG_CARD,
            fg=UIStyle.FG_MAIN,
            insertbackground=UIStyle.FG_MAIN,
            relief=tk.FLAT,
        )
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        query  = self.filters.search_var.get().lower()
        values = self.table.tree.item(item_id)['values']

        txt.tag_configure('key',
                          foreground=UIStyle.ACCENT,
                          font=(UIStyle.FONT_MONO[0], UIStyle.FONT_MONO[1], 'bold'))
        txt.tag_configure('hl',  background='#FEF08A')
        txt.tag_configure('val', foreground=UIStyle.FG_MAIN)

        for k, v in zip(self.engine.columns, values):
            txt.insert(tk.END, f'{k.upper():<18}: ', 'key')
            val_tag = 'hl' if (query and query in str(v).lower()) else 'val'
            txt.insert(tk.END, f'{v}\n', val_tag)

        txt.config(state=tk.DISABLED)

    def _show_context_menu(self, event):
        if self.table.tree.selection():
            self.context_menu.post(event.x_root, event.y_root)

    def _copy_selection(self):
        selected = self.table.tree.selection()
        if not selected:
            return

        rows = ['\t'.join(self.engine.columns)]
        for item in selected:
            rows.append('\t'.join(map(str, self.table.tree.item(item)['values'])))

        self.root.clipboard_clear()
        self.root.clipboard_append('\n'.join(rows))
        messagebox.showinfo('Copiado', f'{len(selected)} linha(s) copiada(s).')

    def _on_closing(self):
        for win in self._chart_windows[:]:
            try:
                win.destroy()
            except Exception:
                pass

        if MATPLOTLIB_AVAILABLE:
            plt.close('all')

        if self._debounce_id:
            self.root.after_cancel(self._debounce_id)

        self.root.quit()
        self.root.destroy()
