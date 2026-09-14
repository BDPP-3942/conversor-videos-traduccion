from __future__ import annotations

import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from config.settings import BASE_DIR, resolve_project_path
from src.application import ApplicationError, VideoTranslationApplication
