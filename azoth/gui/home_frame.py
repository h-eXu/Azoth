"""Home frame — main menu with 3 action buttons."""

import customtkinter as ctk
from azoth.gui import theme as T


class HomeFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG_DARK)
        self.app = app
        self._build()

    def _build(self):
        # ── Spacer top ───────────────────────────────────────────────
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Title ────────────────────────────────────────────────────
        title = ctk.CTkLabel(
            self, text="✦  AZOTH", font=T.FONT_TITLE, text_color=T.ACCENT_LIGHT
        )
        title.grid(row=1, column=0, pady=(0, 4))

        subtitle = ctk.CTkLabel(
            self, text="Som em Texto", font=T.FONT_HEADING, text_color=T.TEXT_SECONDARY
        )
        subtitle.grid(row=2, column=0, pady=(0, 40))

        # ── Buttons container ────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0)

        buttons = [
            ("📝  Nova Transcrição", T.BUTTON_PRIMARY, lambda: self.app.show_frame("transcription")),
            ("📊  Análise de Transcrições", T.BUTTON_SECONDARY, lambda: self.app.show_frame("history")),
            ("🚪  Sair", T.BUTTON_SECONDARY, self.app.quit),
        ]

        for i, (text, style, cmd) in enumerate(buttons):
            btn = ctk.CTkButton(btn_frame, text=text, command=cmd, width=320, **style)
            btn.grid(row=i, column=0, pady=6)

        # ── Status bar ───────────────────────────────────────────────
        self.status_label = ctk.CTkLabel(
            self, text="", font=T.FONT_SMALL, text_color=T.TEXT_MUTED
        )
        self.status_label.grid(row=5, column=0, pady=(0, 16), sticky="s")

    def set_status(self, msg):
        self.status_label.configure(text=msg)

    def on_show(self, **kw):
        pass
