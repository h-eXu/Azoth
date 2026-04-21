"""Transcription frame — source selection, recording controls, progress bar."""

import os
import threading
import time
import tkinter.filedialog as filedialog

import customtkinter as ctk
from azoth.gui import theme as T


class TranscriptionFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=T.BG_DARK)
        self.app = app
        self._recording_start = 0
        self._timer_id = None
        self._current_source = None
        self._build()

    # ── Build UI ──────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Top bar ──────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            top, text="← Voltar", width=100, command=lambda: self.app.show_frame("home"),
            **T.BUTTON_SECONDARY
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            top, text="Nova Transcrição", font=T.FONT_HEADING, text_color=T.TEXT_PRIMARY
        ).grid(row=0, column=1)

        # ── Source selection ─────────────────────────────────────────
        src_frame = ctk.CTkFrame(self, **T.CARD_FRAME)
        src_frame.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        src_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            src_frame, text="Fonte do áudio:", font=T.FONT_BODY, text_color=T.TEXT_SECONDARY
        ).grid(row=0, column=0, columnspan=4, padx=16, pady=(12, 6), sticky="w")

        sources = [
            ("🎤 Microfone", "mic"),
            ("💻 Chamada/Reunião", "system"),
            ("📁 Arquivo", "file"),
            ("▶ YouTube", "youtube"),
        ]
        self._src_buttons = {}
        for i, (label, key) in enumerate(sources):
            btn = ctk.CTkButton(
                src_frame, text=label, width=140,
                command=lambda k=key: self._select_source(k),
                **T.BUTTON_SECONDARY
            )
            btn.grid(row=1, column=i, padx=8, pady=(0, 12))
            self._src_buttons[key] = btn

        # ── Controls area (device dropdown + record btn + timer) ─────
        self.ctrl_frame = ctk.CTkFrame(self, **T.CARD_FRAME)
        self.ctrl_frame.grid(row=2, column=0, padx=20, pady=8, sticky="ew")
        self.ctrl_frame.grid_columnconfigure(1, weight=1)

        # Device dropdown
        ctk.CTkLabel(
            self.ctrl_frame, text="Dispositivo:", font=T.FONT_BODY, text_color=T.TEXT_SECONDARY
        ).grid(row=0, column=0, padx=(16, 8), pady=12, sticky="w")

        self.device_var = ctk.StringVar(value="Padrão do sistema")
        self.device_dropdown = ctk.CTkOptionMenu(
            self.ctrl_frame, variable=self.device_var, values=["Padrão do sistema"],
            fg_color=T.BG_ELEVATED, button_color=T.ACCENT, button_hover_color=T.ACCENT_HOVER,
            text_color=T.TEXT_PRIMARY, font=T.FONT_BODY, width=350
        )
        self.device_dropdown.grid(row=0, column=1, padx=8, pady=12, sticky="w")

        # Record / action button
        self.action_btn = ctk.CTkButton(
            self.ctrl_frame, text="● Iniciar Gravação", width=200,
            command=self._toggle_action, **T.BUTTON_PRIMARY
        )
        self.action_btn.grid(row=1, column=0, columnspan=2, pady=(0, 8))

        # Timer label
        self.timer_label = ctk.CTkLabel(
            self.ctrl_frame, text="", font=T.FONT_BODY, text_color=T.CYAN
        )
        self.timer_label.grid(row=1, column=2, padx=16)

        # YouTube URL entry (hidden by default)
        self.url_frame = ctk.CTkFrame(self.ctrl_frame, fg_color="transparent")
        self.url_entry = ctk.CTkEntry(self.url_frame, placeholder_text="URL do YouTube...", width=400, **T.ENTRY_STYLE)
        self.url_entry.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            self.url_frame, text="Baixar", width=100, command=self._download_youtube, **T.BUTTON_PRIMARY
        ).pack(side="left")

        # ── Progress area ────────────────────────────────────────────
        prog_frame = ctk.CTkFrame(self, **T.CARD_FRAME)
        prog_frame.grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        prog_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            prog_frame, text="Aguardando...", font=T.FONT_BODY, text_color=T.TEXT_SECONDARY
        )
        self.status_label.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.progress = ctk.CTkProgressBar(
            prog_frame, fg_color=T.BG_ELEVATED, progress_color=T.ACCENT, height=8
        )
        self.progress.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
        self.progress.set(0)

        # ── Result area ──────────────────────────────────────────────
        result_frame = ctk.CTkFrame(self, **T.CARD_FRAME)
        result_frame.grid(row=4, column=0, padx=20, pady=8, sticky="nsew")
        result_frame.grid_columnconfigure(0, weight=1)
        result_frame.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            result_frame, text="Resultado:", font=T.FONT_BODY, text_color=T.TEXT_SECONDARY
        ).grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.result_text = ctk.CTkTextbox(
            result_frame, fg_color=T.BG_ELEVATED, text_color=T.TEXT_PRIMARY,
            font=T.FONT_BODY, corner_radius=8, wrap="word", state="disabled"
        )
        self.result_text.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="nsew")

        # Bottom buttons
        btn_row = ctk.CTkFrame(result_frame, fg_color="transparent")
        btn_row.grid(row=2, column=0, padx=16, pady=(0, 12))

        self.save_btn = ctk.CTkButton(
            btn_row, text="💾 Salvar", command=self._save, state="disabled", **T.BUTTON_PRIMARY
        )
        self.save_btn.pack(side="left", padx=4)

        self.analyze_btn = ctk.CTkButton(
            btn_row, text="🤖 Analisar com IA", command=self._analyze, state="disabled", **T.BUTTON_SECONDARY
        )
        self.analyze_btn.pack(side="left", padx=4)

        # Hidden initially
        self.ctrl_frame.grid_remove()

    # ── Source selection ──────────────────────────────────────────────

    def _select_source(self, source):
        self._current_source = source
        # Highlight active source button
        for key, btn in self._src_buttons.items():
            if key == source:
                btn.configure(fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER, text_color="#fff")
            else:
                btn.configure(**{k: v for k, v in T.BUTTON_SECONDARY.items() if k in ("fg_color", "hover_color", "text_color")})

        self.ctrl_frame.grid()
        self.url_frame.grid_remove()

        if source in ("mic", "system"):
            self._refresh_devices()
            self.device_dropdown.grid()
            self.action_btn.configure(text="● Iniciar Gravação", state="normal")
            self.action_btn.grid()
            self.timer_label.grid()
        elif source == "file":
            self.device_dropdown.grid_remove()
            self.timer_label.grid_remove()
            self.action_btn.configure(text="📁 Selecionar Arquivo", state="normal")
            self.action_btn.grid()
        elif source == "youtube":
            self.device_dropdown.grid_remove()
            self.action_btn.grid_remove()
            self.timer_label.grid_remove()
            self.url_frame.grid(row=1, column=0, columnspan=3, padx=16, pady=(0, 12))


    def _refresh_devices(self):
        mode = "mic" if self._current_source == "mic" else "system"
        devs = self.app.audio.list_input_devices(mode=mode)
        
        if len(devs) == 1:
            self.device_var.set(f"{devs[0][0]}: {devs[0][1]}")
            self.device_dropdown.grid_remove()
        else:
            names = ["Padrão do sistema"] + [f"{i}: {n}" for i, n in devs]
            self.device_dropdown.configure(values=names)
            self.device_var.set("Padrão do sistema")
            self.device_dropdown.grid()



    def _get_selected_device(self):
        val = self.device_var.get()
        if val == "Padrão do sistema":
            return None
        return int(val.split(":")[0])

    # ── Actions ───────────────────────────────────────────────────────

    def _toggle_action(self):
        if self._current_source in ("mic", "system"):
            if self.app.audio.is_recording:
                self._stop_recording()
            else:
                self._start_recording()
        elif self._current_source == "file":
            self._pick_file()

    def _start_recording(self):
        device = self._get_selected_device()
        self.app.audio.start_recording(device=device)
        self._recording_start = time.time()
        self.action_btn.configure(text="■ Parar Gravação", fg_color=T.ERROR, hover_color="#dc2626")
        self.status_label.configure(text="Gravando...", text_color=T.WARNING)
        self._update_timer()

    def _stop_recording(self):
        if self._timer_id:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        filepath = self.app.audio.stop_recording()
        self.action_btn.configure(text="● Iniciar Gravação", **{k: v for k, v in T.BUTTON_PRIMARY.items() if k in ("fg_color", "hover_color")})
        self.timer_label.configure(text="")
        self._run_transcription(filepath, self._current_source, cleanup=True)

    def _update_timer(self):
        if self.app.audio.is_recording:
            elapsed = int(time.time() - self._recording_start)
            m, s = divmod(elapsed, 60)
            h, m = divmod(m, 60)
            self.timer_label.configure(text=f"⏱ {h:02d}:{m:02d}:{s:02d}")
            self._timer_id = self.after(1000, self._update_timer)

    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar arquivo de áudio/vídeo",
            filetypes=[
                ("Áudio/Vídeo", "*.mp3 *.mp4 *.wav *.m4a *.ogg"),
                ("Todos", "*.*"),
            ],
        )
        if path:
            self.status_label.configure(text="Importando arquivo...", text_color=T.CYAN)
            threading.Thread(target=self._import_file_thread, args=(path,), daemon=True).start()

    def _import_file_thread(self, path):
        try:
            audio, name = self.app.audio.import_file(path)
            self.after(0, lambda: self._run_transcription(audio, "arquivo", title=name, cleanup=(audio != path)))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text=f"Erro: {e}", text_color=T.ERROR))

    def _download_youtube(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        self.status_label.configure(text="Baixando do YouTube...", text_color=T.CYAN)
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        threading.Thread(target=self._yt_thread, args=(url,), daemon=True).start()

    def _yt_thread(self, url):
        try:
            audio, title = self.app.audio.download_youtube(url)
            self.after(0, lambda: self._run_transcription(audio, "youtube", title=title, cleanup=True))
        except Exception as e:
            self.after(0, self._on_error, str(e))

    # ── Transcription ─────────────────────────────────────────────────

    def _run_transcription(self, audio_path, origin, title=None, cleanup=False):
        self._last_audio = audio_path
        self._last_origin = origin
        self._last_title = title
        self._last_cleanup = cleanup

        self.status_label.configure(text="Transcrevendo...", text_color=T.CYAN)
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.action_btn.configure(state="disabled")

        threading.Thread(
            target=self._transcribe_thread, args=(audio_path,), daemon=True
        ).start()

    def _transcribe_thread(self, audio_path):
        try:
            text, elapsed = self.app.engine.transcribe(audio_path)
            self.after(0, self._on_transcription_done, text, elapsed)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_transcription_done(self, text, elapsed):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(1.0)
        self.status_label.configure(
            text=f"✓ Transcrito em {elapsed:.1f}s ({self.app.engine.device.upper()})",
            text_color=T.SUCCESS,
        )

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.configure(state="disabled")

        self._last_text = text
        if not self._last_title:
            self._last_title = (text[:50] + "...") if len(text) > 50 else text

        self.save_btn.configure(state="normal")
        self.analyze_btn.configure(state="normal")
        self.action_btn.configure(state="normal")

        if self._last_cleanup and self._last_audio and os.path.exists(self._last_audio):
            try:
                os.remove(self._last_audio)
            except OSError:
                pass

    def _on_error(self, msg):
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(0)
        self.status_label.configure(text=f"Erro: {msg}", text_color=T.ERROR)
        self.action_btn.configure(state="normal")

    # ── Save / Analyze ────────────────────────────────────────────────

    def _save(self):
        self.app.db.save(self._last_origin, self._last_title, self._last_text)
        self.status_label.configure(text="✓ Transcrição salva!", text_color=T.SUCCESS)
        self.save_btn.configure(state="disabled")

    def _analyze(self):
        # Save first if not saved yet
        if self.save_btn.cget("state") == "normal":
            self._save()
        from azoth.gui.chat_window import ChatWindow
        ChatWindow(self, self.app, self._last_title, self._last_text)

    # ── Frame lifecycle ───────────────────────────────────────────────

    def on_show(self, **kw):
        self._reset()

    def _reset(self):
        self._current_source = None
        self.ctrl_frame.grid_remove()
        self.progress.set(0)
        self.status_label.configure(text="Aguardando...", text_color=T.TEXT_SECONDARY)
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        self.analyze_btn.configure(state="disabled")
        self.timer_label.configure(text="")
        for btn in self._src_buttons.values():
            btn.configure(**{k: v for k, v in T.BUTTON_SECONDARY.items() if k in ("fg_color", "hover_color", "text_color")})
