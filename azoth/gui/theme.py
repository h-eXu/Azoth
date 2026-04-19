"""Azoth dark theme — color palette, fonts, and widget helpers."""

# ── Color Palette (GitHub-dark inspired + purple accent) ──────────

BG_DARK      = "#0d1117"
BG_CARD      = "#161b22"
BG_ELEVATED  = "#21262d"
BORDER       = "#30363d"

ACCENT       = "#7c3aed"
ACCENT_HOVER = "#6d28d9"
ACCENT_LIGHT = "#a78bfa"

CYAN         = "#22d3ee"
SUCCESS      = "#10b981"
WARNING      = "#f59e0b"
ERROR        = "#ef4444"

TEXT_PRIMARY   = "#f0f6fc"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED     = "#484f58"

# ── Fonts ─────────────────────────────────────────────────────────

FONT_FAMILY  = "Segoe UI"
FONT_TITLE   = (FONT_FAMILY, 28, "bold")
FONT_HEADING = (FONT_FAMILY, 16, "bold")
FONT_BODY    = (FONT_FAMILY, 13)
FONT_SMALL   = (FONT_FAMILY, 11)
FONT_MONO    = ("Consolas", 12)

# ── Shared widget kwargs ──────────────────────────────────────────

BUTTON_PRIMARY = dict(
    fg_color=ACCENT,
    hover_color=ACCENT_HOVER,
    text_color="#ffffff",
    font=FONT_BODY,
    corner_radius=8,
    height=42,
)

BUTTON_SECONDARY = dict(
    fg_color=BG_ELEVATED,
    hover_color=BORDER,
    text_color=TEXT_PRIMARY,
    font=FONT_BODY,
    corner_radius=8,
    height=42,
    border_width=1,
    border_color=BORDER,
)

BUTTON_DANGER = dict(
    fg_color=ERROR,
    hover_color="#dc2626",
    text_color="#ffffff",
    font=FONT_BODY,
    corner_radius=8,
    height=42,
)

CARD_FRAME = dict(
    fg_color=BG_CARD,
    corner_radius=12,
    border_width=1,
    border_color=BORDER,
)

ENTRY_STYLE = dict(
    fg_color=BG_ELEVATED,
    border_color=BORDER,
    text_color=TEXT_PRIMARY,
    font=FONT_BODY,
    corner_radius=8,
    height=40,
)


def configure_treeview_style(style):
    """Apply dark theme to ttk.Treeview using the 'clam' base theme."""
    style.theme_use("clam")
    style.configure(
        "Dark.Treeview",
        background=BG_CARD,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_CARD,
        borderwidth=0,
        rowheight=36,
        font=(FONT_FAMILY, 12),
    )
    style.configure(
        "Dark.Treeview.Heading",
        background=BG_ELEVATED,
        foreground=TEXT_PRIMARY,
        borderwidth=0,
        font=(FONT_FAMILY, 12, "bold"),
    )
    style.map(
        "Dark.Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", "#ffffff")],
    )
    style.layout("Dark.Treeview", [("Dark.Treeview.treearea", {"sticky": "nswe"})])
