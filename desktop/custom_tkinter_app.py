import customtkinter as ctk
import urllib.request
import json
import threading
import sys
import os

sys.path.insert(0, os.path.abspath("."))

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AsthaERPCustomTkinterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ASTHA ERP Enterprise — Astha Builders & Hardware")
        self.geometry("1100x700")

        # Sidebar Frame
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="ASTHA ERP",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.sub_logo = ctk.CTkLabel(
            self.sidebar_frame,
            text="Builders & Hardware",
            font=ctk.CTkFont(size=11),
            text_color="#3B82F6"
        )
        self.sub_logo.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Sidebar Navigation Buttons
        self.btn_dash = ctk.CTkButton(self.sidebar_frame, text="📊 Dashboard", fg_color="#3B82F6", command=self.show_dashboard)
        self.btn_dash.grid(row=2, column=0, padx=20, pady=10)

        self.btn_parties = ctk.CTkButton(self.sidebar_frame, text="👥 Parties & Ledgers", fg_color="#3B82F6", command=self.show_parties)
        self.btn_parties.grid(row=3, column=0, padx=20, pady=10)

        # Main Display Area
        self.main_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1E293B")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="ASTHA ERP Enterprise Control Panel",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.pack(pady=20, padx=20)

        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Status: Connected to Local Server (8000)",
            text_color="#22C55E"
        )
        self.status_label.pack(pady=10)

    def show_dashboard(self):
        self.title_label.configure(text="Dashboard Overview")

    def show_parties(self):
        self.title_label.configure(text="Party Directory & Outstanding Ledgers")

def launch_customtkinter():
    app = AsthaERPCustomTkinterApp()
    app.mainloop()

if __name__ == "__main__":
    launch_customtkinter()
