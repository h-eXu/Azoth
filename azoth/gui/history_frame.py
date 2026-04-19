"""History frame — Treeview table with transcription records."""

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk
from azoth.gui import theme as T


class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG_DARK)
        self.app = app
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Top bar ──────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            top, text="← Voltar", width=100, command=lambda: self.app.show_frame("home"),
            **T.BUTTON_SECONDARY
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            top, text="Histórico de Transcrições", font=T.FONT_HEADING, text_color=T.TEXT_PRIMARY
        ).grid(row=0, column=1)

        # ── Treeview ─────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(self, **T.CARD_FRAME)
        tree_frame.grid(row=1, column=0, padx=20, pady=8, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style(self)
        T.configure_treeview_style(style)

        cols = ("data", "origem", "titulo", "trecho")
        self.tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", style="Dark.Treeview",
            selectmode="browse"
        )
        self.tree.heading("data", text="Data")
        self.tree.heading("origem", text="Origem")
        self.tree.heading("titulo", text="Título")
        self.tree.heading("trecho", text="Trecho")

        self.tree.column("data", width=140, minwidth=100)
        self.tree.column("origem", width=100, minwidth=80)
        self.tree.column("titulo", width=220, minwidth=120)
        self.tree.column("trecho", width=300, minwidth=150)

        scrollbar = ctk.CTkScrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(12, 0), pady=12)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 12), pady=12)

        self.tree.bind("<Double-1>", lambda e: self._view_selected())

        # ── Action buttons ───────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_frame, text="🤖 Analisar com IA", command=self._analyze_selected, **T.BUTTON_PRIMARY
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame, text="👁 Ver Transcrição", command=self._view_selected, **T.BUTTON_SECONDARY
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame, text="🗑 Deletar", command=self._delete_selected, **T.BUTTON_DANGER
        ).pack(side="left", padx=4)

        # ── Empty state label ────────────────────────────────────────
        self.empty_label = ctk.CTkLabel(
            self, text="Nenhuma transcrição encontrada.", font=T.FONT_BODY,
            text_color=T.TEXT_MUTED
        )

    # ── Data ──────────────────────────────────────────────────────────

    def _load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self._items = self.app.db.get_all()

        if not self._items:
            self.empty_label.grid(row=1, column=0, pady=40)
            return
        else:
            self.empty_label.grid_remove()

        for item in self._items:
            trecho = (item["texto"][:50] + "...") if len(item["texto"]) > 50 else item["texto"]
            self.tree.insert("", "end", values=(
                item.get("data", ""),
                item.get("origem", ""),
                item.get("titulo", ""),
                trecho,
            ))

    def _get_selected_item(self):
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        return self._items[idx]

    # ── Actions ───────────────────────────────────────────────────────

    def _view_selected(self):
        item = self._get_selected_item()
        if not item:
            return
        ViewWindow(self, item)

    def _analyze_selected(self):
        item = self._get_selected_item()
        if not item:
            return
        from azoth.gui.chat_window import ChatWindow
        ChatWindow(self, self.app, item.get("titulo", ""), item["texto"])

    def _delete_selected(self):
        item = self._get_selected_item()
        if not item:
            return
        self.app.db.delete(item.doc_id)
        self._load_data()

    # ── Lifecycle ─────────────────────────────────────────────────────

    def on_show(self, **kw):
        self._load_data()


class ViewWindow(ctk.CTkToplevel):
    """Simple read-only transcription viewer."""

    def __init__(self, parent, item):
        super().__init__(parent)
        self.title(f"Transcrição — {item.get('titulo', '')}")
        self.geometry("700x500")
        self.configure(fg_color=T.BG_DARK)

        ctk.CTkLabel(
            self, text=item.get("titulo", ""), font=T.FONT_HEADING, text_color=T.ACCENT_LIGHT
        ).pack(padx=20, pady=(16, 4))

        ctk.CTkLabel(
            self, text=f"{item.get('data', '')}  •  {item.get('origem', '')}",
            font=T.FONT_SMALL, text_color=T.TEXT_MUTED
        ).pack(padx=20, pady=(0, 8))

        txt = ctk.CTkTextbox(
            self, fg_color=T.BG_CARD, text_color=T.TEXT_PRIMARY, font=T.FONT_BODY,
            corner_radius=8, wrap="word"
        )
        txt.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        txt.insert("1.0", item["texto"])
        txt.configure(state="disabled")

        self.after(100, self.focus_force)
