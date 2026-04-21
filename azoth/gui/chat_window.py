"""Chat window — template-based auto-analysis + streaming chat with AI."""

import threading
import customtkinter as ctk
from azoth.core.analysis import TEMPLATES
from azoth.gui import theme as T


class ChatWindow(ctk.CTkToplevel):
    """Toplevel window: runs auto-analysis with selectable template, then enables interactive chat."""

    def __init__(self, parent, app, title, transcription):
        super().__init__(parent)
        self.app = app
        self.transcription = transcription
        self.agent = None

        self.title(f"✦ Azoth — Análise: {title}")
        self.geometry("850x680")
        self.minsize(700, 500)
        self.configure(fg_color=T.BG_DARK)

        self._build()
        self.after(100, self.focus_force)
        self.after(200, self._run_auto_analysis)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Header ───────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=T.BG_CARD, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            header, text="🤖 Análise com IA", font=T.FONT_HEADING,
            text_color=T.ACCENT_LIGHT
        ).pack(padx=20, pady=(12, 6), anchor="w")

        # ── Template selector ────────────────────────────────────────
        selector_frame = ctk.CTkFrame(header, fg_color="transparent")
        selector_frame.pack(padx=20, pady=(0, 10), anchor="w", fill="x")

        ctk.CTkLabel(
            selector_frame, text="Template:", font=T.FONT_BODY,
            text_color=T.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 8))

        # Build label list preserving order, store key lookup
        self._template_labels = [v["label"] for v in TEMPLATES.values()]
        self._label_to_key = {v["label"]: k for k, v in TEMPLATES.items()}

        self.template_var = ctk.StringVar(value=self._template_labels[0])
        self.template_dropdown = ctk.CTkOptionMenu(
            selector_frame,
            variable=self.template_var,
            values=self._template_labels,
            fg_color=T.BG_ELEVATED,
            button_color=T.ACCENT,
            button_hover_color=T.ACCENT_HOVER,
            text_color=T.TEXT_PRIMARY,
            font=T.FONT_BODY,
            width=220,
            state="disabled",
        )
        self.template_dropdown.pack(side="left")

        self.rerun_btn = ctk.CTkButton(
            selector_frame, text="↺ Reanalisar", width=120,
            command=self._rerun_analysis, state="disabled",
            **T.BUTTON_SECONDARY
        )
        self.rerun_btn.pack(side="left", padx=(8, 0))

        # ── Chat display ─────────────────────────────────────────────
        self.chat_display = ctk.CTkTextbox(
            self, fg_color=T.BG_CARD, text_color=T.TEXT_PRIMARY, font=T.FONT_BODY,
            corner_radius=8, wrap="word", state="disabled"
        )
        self.chat_display.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")

        self.chat_display._textbox.tag_configure("system", foreground=T.CYAN)
        self.chat_display._textbox.tag_configure("user_tag", foreground=T.ACCENT_LIGHT)
        self.chat_display._textbox.tag_configure("bot_tag", foreground=T.SUCCESS)
        self.chat_display._textbox.tag_configure("error_tag", foreground=T.ERROR)

        # ── Input area ───────────────────────────────────────────────
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Digite sua pergunta...", **T.ENTRY_STYLE
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.input_entry.configure(state="disabled")
        self.input_entry.bind("<Return>", lambda e: self._send_message())

        self.send_btn = ctk.CTkButton(
            input_frame, text="Enviar", width=100, command=self._send_message,
            state="disabled", **T.BUTTON_PRIMARY
        )
        self.send_btn.grid(row=0, column=1)

    # ── Helpers ───────────────────────────────────────────────────────

    def _append_text(self, text, tag=None):
        self.chat_display.configure(state="normal")
        if tag:
            self.chat_display._textbox.insert("end", text, tag)
        else:
            self.chat_display._textbox.insert("end", text)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _set_input_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        self.input_entry.configure(state=state)
        self.send_btn.configure(state=state)
        if enabled:
            self.input_entry.focus()

    def _get_selected_template_key(self):
        label = self.template_var.get()
        return self._label_to_key.get(label, "geral")

    # ── Auto-analysis ─────────────────────────────────────────────────

    def _run_auto_analysis(self):
        label = self.template_var.get()
        self._append_text(f"Executando análise: {label}...\n\n", "system")
        threading.Thread(target=self._analysis_thread, daemon=True).start()

    def _analysis_thread(self):
        try:
            key = self._get_selected_template_key()
            agent, response = self.app.analysis.auto_analyze_stream(
                self.transcription, template=key
            )
            self.agent = agent
            for msg in response:
                if msg.content:
                    self.after(0, self._append_text, msg.content)
            self.after(0, self._on_analysis_done)
        except Exception as e:
            self.after(0, self._append_text, f"\nErro na análise: {e}\n", "error_tag")
            self.after(0, lambda: self._set_input_enabled(True))

    def _on_analysis_done(self):
        self._append_text("\n\n─── Chat disponível. Digite sua pergunta. ───\n\n", "system")
        self._set_input_enabled(True)
        self.template_dropdown.configure(state="normal")
        self.rerun_btn.configure(state="normal")

    # ── Re-analysis ───────────────────────────────────────────────────

    def _rerun_analysis(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.agent = None
        self._set_input_enabled(False)
        self.template_dropdown.configure(state="disabled")
        self.rerun_btn.configure(state="disabled")
        self._run_auto_analysis()

    # ── Chat ──────────────────────────────────────────────────────────

    def _send_message(self):
        msg = self.input_entry.get().strip()
        if not msg or not self.agent:
            return

        self.input_entry.delete(0, "end")
        self._set_input_enabled(False)

        self._append_text(f"\n🧑 Você: ", "user_tag")
        self._append_text(f"{msg}\n\n")
        self._append_text("🤖 Azoth: ", "bot_tag")

        threading.Thread(target=self._chat_thread, args=(msg,), daemon=True).start()

    def _chat_thread(self, message):
        try:
            response = self.app.analysis.chat_stream(self.agent, message)
            for msg in response:
                if msg.content:
                    self.after(0, self._append_text, msg.content)
            self.after(0, self._on_chat_done)
        except Exception as e:
            self.after(0, self._append_text, f"\nErro: {e}\n", "error_tag")
            self.after(0, lambda: self._set_input_enabled(True))

    def _on_chat_done(self):
        self._append_text("\n")
        self._set_input_enabled(True)