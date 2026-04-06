import tkinter as tk
import csv
import re
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# Assuming these are in your local directory
from db_manager import DBManager
from config import (APP_TITLE, THEME, WINDOW_SIZE, FONT_BOLD, 
                    FONT_NORMAL, CATEGORIES, CATEGORY_COLORS)

class ContactApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.style = ttk.Style(theme=THEME)
        self.db = DBManager()
        self.selected_id = None

        self.setup_ui()
        self.load_contacts()

    def setup_ui(self):
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=BOTH, expand=YES)

        # --- HEADER ---
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=X, pady=(0, 20))

        ttk.Label(header_frame, text="ProContact Manager ✨",
                  font=("Segoe UI", 28, "bold"),
                  bootstyle=PRIMARY).pack(side=LEFT)

        self.theme_btn = ttk.Checkbutton(
            header_frame,
            text="Dark Mode",
            bootstyle="round-toggle",
            command=self.toggle_theme
        )
        self.theme_btn.pack(side=RIGHT, pady=10)
        self.theme_btn.state(['selected'])

        # --- STATS ---
        self.stats_frame = ttk.Frame(self.main_frame)
        self.stats_frame.pack(fill=X, pady=(0, 20))
        self.update_stats_ui()

        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=BOTH, expand=YES)

        # --- LEFT SIDEBAR (ENTRY FORM) ---
        self.sidebar = ttk.LabelFrame(self.content_frame, text=" Contact Details ")
        self.sidebar.pack(side=LEFT, fill=Y, padx=(0, 15))

        self.sidebar_inner = ttk.Frame(self.sidebar, padding=15)
        self.sidebar_inner.pack(fill=BOTH, expand=YES)

        self.entries = {}
        fields = [("Name:", "name"), ("Phone:", "phone"),
                  ("Email:", "email"), ("Birthday:", "birthday")]

        for label_text, attr in fields:
            ttk.Label(self.sidebar_inner, text=label_text,
                      font=FONT_NORMAL).pack(anchor=W, pady=(8, 2))
            entry = ttk.Entry(self.sidebar_inner, width=30)
            entry.pack(fill=X, pady=2)
            self.entries[attr] = entry

        ttk.Label(self.sidebar_inner, text="Category:",
                  font=FONT_NORMAL).pack(anchor=W, pady=(8, 2))
        self.cat_var = tk.StringVar(value="Other")
        self.cat_combo = ttk.Combobox(
            self.sidebar_inner,
            textvariable=self.cat_var,
            values=CATEGORIES,
            state="readonly"
        )
        self.cat_combo.pack(fill=X, pady=2)
        self.entries['category'] = self.cat_combo

        ttk.Label(self.sidebar_inner, text="Address:",
                  font=FONT_NORMAL).pack(anchor=W, pady=(8, 2))
        self.address_entry = ttk.Entry(self.sidebar_inner, width=30)
        self.address_entry.pack(fill=X, pady=2)
        self.entries['address'] = self.address_entry

        # Buttons
        self.btn_frame = ttk.Frame(self.sidebar_inner)
        self.btn_frame.pack(fill=X, pady=(25, 0))

        self.btn_add = ttk.Button(self.btn_frame, text="➕ Add", width=12,
                                  bootstyle=SUCCESS, command=self.add_contact)
        self.btn_add.grid(row=0, column=0, padx=5, pady=5)

        self.btn_update = ttk.Button(self.btn_frame, text="💾 Update", width=12,
                                    bootstyle=WARNING, command=self.update_contact)
        self.btn_update.grid(row=0, column=1, padx=5, pady=5)

        self.btn_delete = ttk.Button(self.btn_frame, text="🗑️ Delete", width=12,
                                    bootstyle=DANGER, command=self.delete_contact)
        self.btn_delete.grid(row=1, column=0, padx=5, pady=5)

        self.btn_clear = ttk.Button(self.btn_frame, text="🧹 Clear", width=12,
                                   bootstyle=SECONDARY, command=self.clear_fields)
        self.btn_clear.grid(row=1, column=1, padx=5, pady=5)

        # --- RIGHT PANEL (SEARCH & TABLE) ---
        self.right_frame = ttk.Frame(self.content_frame)
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=YES)

        self.search_frame = ttk.Frame(self.right_frame)
        self.search_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(self.search_frame, text="Search:",
                  font=FONT_NORMAL).pack(side=LEFT, padx=(0, 10))
        self.search_entry = ttk.Entry(self.search_frame, bootstyle=PRIMARY)
        self.search_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_contacts())

        self.btn_refresh = ttk.Button(self.search_frame, text="🔄 Refresh",
                                     bootstyle="info-outline",
                                     command=self.load_contacts)
        self.btn_refresh.pack(side=RIGHT, padx=5)

        self.btn_export = ttk.Button(self.search_frame, text="📥 Export CSV",
                                    bootstyle="success-outline",
                                    command=self.export_csv)
        self.btn_export.pack(side=RIGHT, padx=5)

        # Table
        tree_columns = ("ID", "Name", "Phone", "Email",
                        "Category", "Birthday", "Address")
        self.tree = ttk.Treeview(self.right_frame,
                                 columns=tree_columns,
                                 show="headings",
                                 bootstyle=INFO)

        column_widths = {"ID": 50, "Name": 150, "Phone": 120,
                         "Email": 180, "Category": 100,
                         "Birthday": 100, "Address": 200}

        for col in tree_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=W,
                             width=column_widths.get(col, 150))

        self.tree.pack(fill=BOTH, expand=YES)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.scrollbar = ttk.Scrollbar(self.tree,
                                      orient=VERTICAL,
                                      command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=RIGHT, fill=Y)

    def update_stats_ui(self):
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        contacts = self.db.get_all_contacts()
        total = len(contacts)

        # Total Card
        card = ttk.Frame(self.stats_frame, bootstyle=SECONDARY, padding=10)
        card.pack(side=LEFT, padx=5, fill=X, expand=YES)
        ttk.Label(card, text="Total Contacts", font=FONT_NORMAL).pack()
        ttk.Label(card, text=str(total), font=("Segoe UI", 18, "bold")).pack()

        # Category Breakdown
        counts = {cat: 0 for cat in CATEGORIES}
        for c in contacts:
            cat = c.get('category', 'Other')
            if cat in counts:
                counts[cat] += 1

        for cat, count in counts.items():
            if count > 0:
                color = CATEGORY_COLORS.get(cat, "secondary")
                card = ttk.Frame(self.stats_frame, bootstyle=color, padding=10)
                card.pack(side=LEFT, padx=5, fill=X, expand=YES)
                ttk.Label(card, text=cat, font=FONT_NORMAL,
                          bootstyle=f"{color}-inverse").pack()
                ttk.Label(card, text=str(count), font=("Segoe UI", 18, "bold"),
                          bootstyle=f"{color}-inverse").pack()

    def toggle_theme(self):
        theme = "superhero" if self.theme_btn.instate(['selected']) else "flatly"
        self.style.theme_use(theme)

    def get_input_data(self):
        return {attr: entry.get().strip() for attr, entry in self.entries.items()}

    def validate_input(self, data):
        if not data['name'] or not data['phone']:
            messagebox.showwarning("Incomplete Data", "Name and Phone Number are required!")
            return False

        if not re.match(r'^[6-9]\d{9}$', data['phone']):
            messagebox.showerror("Invalid Phone", "Enter valid 10-digit Indian phone number!")
            return False

        if data['email'] and not re.match(r'^[\w\.-]+@gmail\.com$', data['email']):
            messagebox.showerror("Invalid Email", "Enter valid Gmail address!")
            return False

        return True

    def clear_fields(self):
        for entry in self.entries.values():
            if isinstance(entry, ttk.Entry):
                entry.delete(0, END)
            elif isinstance(entry, ttk.Combobox):
                self.cat_var.set("Other")
        self.selected_id = None
        self.tree.selection_remove(self.tree.selection())

    def load_contacts(self):
        self.tree.delete(*self.tree.get_children())
        contacts = self.db.get_all_contacts()
        for c in contacts:
            self.tree.insert("", END, values=(
                c['id'], c['name'], c['phone'], c['email'],
                c['category'], c['birthday'], c['address']))
        self.update_stats_ui()

    def search_contacts(self):
        query = self.search_entry.get().strip()
        if not query:
            self.load_contacts()
            return

        self.tree.delete(*self.tree.get_children())
        contacts = self.db.search_contacts(query)
        for c in contacts:
            self.tree.insert("", END, values=(
                c['id'], c['name'], c['phone'], c['email'],
                c['category'], c['birthday'], c['address']))

    def add_contact(self):
        data = self.get_input_data()
        if self.validate_input(data):
            if self.db.add_contact(data['name'], data['phone'],
                                   data['email'], data['address'],
                                   data['category'], data['birthday']):
                messagebox.showinfo("Success", "Contact added successfully!")
                self.clear_fields()
                self.load_contacts()

    def on_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            self.selected_id = values[0]

            # Map tree values back to entry fields
            # Values index: 0:ID, 1:Name, 2:Phone, 3:Email, 4:Category, 5:Birthday, 6:Address
            mapping = {
                "name": values[1],
                "phone": values[2],
                "email": values[3],
                "category": values[4],
                "birthday": values[5],
                "address": values[6]
            }

            for attr, val in mapping.items():
                if attr == 'category':
                    self.cat_var.set(val)
                else:
                    self.entries[attr].delete(0, END)
                    self.entries[attr].insert(0, val)

    def update_contact(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Select a contact from the list first!")
            return

        data = self.get_input_data()
        if self.validate_input(data):
            if self.db.update_contact(self.selected_id, data['name'], data['phone'],
                                      data['email'], data['address'],
                                      data['category'], data['birthday']):
                messagebox.showinfo("Success", "Contact updated successfully!")
                self.clear_fields()
                self.load_contacts()

    def delete_contact(self):
        selection = self.tree.selection()

        if not selection:
            messagebox.showwarning("No Selection", "Please select a contact from the table first!")
            return

        # Get data from selected row
        item = self.tree.item(selection[0])
        values = item['values']
        contact_id = values[0]
        contact_name = values[1]

        # Use standard messagebox for guaranteed boolean return
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{contact_name}'?")
        
        if confirm:
            if self.db.delete_contact(contact_id):
                messagebox.showinfo("Deleted", "Contact has been removed.")
                self.clear_fields()
                self.load_contacts()
            else:
                messagebox.showerror("Error", "Failed to delete the contact from the database.")

    def export_csv(self):
        contacts = self.db.get_all_contacts()
        if not contacts:
            messagebox.showwarning("No Data", "No contacts available to export.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".csv", 
                                             filetypes=[("CSV files", "*.csv")])
        if path:
            try:
                with open(path, "w", newline='', encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=contacts[0].keys())
                    writer.writeheader()
                    writer.writerows(contacts)
                messagebox.showinfo("Exported", f"Successfully saved to {path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to save file: {e}")


if __name__ == "__main__":
    root = ttk.Window(themename=THEME)
    app = ContactApp(root)
    root.mainloop()