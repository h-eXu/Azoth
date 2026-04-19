"""✦ AZOTH — Som em Texto
Entry point: launches the CustomTkinter GUI application.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from azoth.gui.app import AzothApp


def main():
    app = AzothApp()
    app.mainloop()


if __name__ == "__main__":
    main()