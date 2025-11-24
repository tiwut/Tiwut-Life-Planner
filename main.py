import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import webbrowser

COLORS = {
    "bg": "#1e1e1e",
    "panel_bg": "#252526",
    "node_bg": "#333333",
    "node_border": "#00c3ff",
    "text": "#ffffff",
    "text_dim": "#aaaaaa",
    "line": "#00F300",
    "progress": "#4caf50",
    "highlight": "#be1600"
}

FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_TEXT = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 8)

class Node:
    """Data structure for a single life point"""
    def __init__(self, name, parent=None):
        self.name = name
        self.description = ""
        self.url = ""
        self.date = ""
        self.progress = 0
        self.children = []
        self.parent = parent
        self.x = 0
        self.y = 0
        self.width = 180
        self.height = 60

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "date": self.date,
            "progress": self.progress,
            "children": [child.to_dict() for child in self.children]
        }

    @classmethod
    def from_dict(cls, data, parent=None):
        node = cls(data["name"], parent)
        node.description = data.get("description", "")
        node.url = data.get("url", "")
        node.date = data.get("date", "")
        node.progress = data.get("progress", 0)
        for child_data in data.get("children", []):
            node.children.append(cls.from_dict(child_data, node))
        return node

class TimelineMindMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tiwut Life Planner")
        self.root.geometry("1200x700")
        self.root.configure(bg=COLORS["bg"])

        self.root_node = Node("My Life")
        self.selected_node = self.root_node

        self.main_paned = tk.PanedWindow(root, orient=tk.HORIZONTAL, bg=COLORS["bg"], sashwidth=4)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        self.canvas_frame = tk.Frame(self.main_paned, bg=COLORS["bg"])
        self.canvas = tk.Canvas(self.canvas_frame, bg=COLORS["bg"], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.main_paned.add(self.canvas_frame, minsize=600)

        self.editor_frame = tk.Frame(self.main_paned, bg=COLORS["panel_bg"], width=350)
        self.main_paned.add(self.editor_frame, minsize=300)

        self._setup_editor()

        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<Button-3>", self.on_right_click)
        
        self._setup_menu()

        self.redraw()

    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Timeline", command=self.save_json)
        file_menu.add_command(label="Load Timeline", command=self.load_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def _setup_editor(self):
        """Builds the right sidebar"""
        pad_opts = {'padx': 15, 'pady': 5}
        
        lbl_title = tk.Label(self.editor_frame, text="Edit Details", bg=COLORS["panel_bg"], fg=COLORS["text"], font=("Segoe UI", 14, "bold"))
        lbl_title.pack(pady=15)

        tk.Label(self.editor_frame, text="Title:", bg=COLORS["panel_bg"], fg=COLORS["text_dim"]).pack(anchor="w", **pad_opts)
        self.entry_name = tk.Entry(self.editor_frame, bg="#3c3c3c", fg="white", insertbackground="white", relief="flat")
        self.entry_name.pack(fill=tk.X, **pad_opts)
        self.entry_name.bind("<KeyRelease>", self.update_data_from_editor)

        tk.Label(self.editor_frame, text="Date / Deadline (e.g. 2025-12-31):", bg=COLORS["panel_bg"], fg=COLORS["text_dim"]).pack(anchor="w", **pad_opts)
        self.entry_date = tk.Entry(self.editor_frame, bg="#3c3c3c", fg="white", insertbackground="white", relief="flat")
        self.entry_date.pack(fill=tk.X, **pad_opts)
        self.entry_date.bind("<KeyRelease>", self.update_data_from_editor)

        tk.Label(self.editor_frame, text="Progress (%):", bg=COLORS["panel_bg"], fg=COLORS["text_dim"]).pack(anchor="w", **pad_opts)
        self.scale_progress = tk.Scale(self.editor_frame, from_=0, to=100, orient=tk.HORIZONTAL, bg=COLORS["panel_bg"], fg="white", highlightthickness=0, command=lambda x: self.update_data_from_editor())
        self.scale_progress.pack(fill=tk.X, **pad_opts)

        tk.Label(self.editor_frame, text="URL / Link:", bg=COLORS["panel_bg"], fg=COLORS["text_dim"]).pack(anchor="w", **pad_opts)
        self.entry_url = tk.Entry(self.editor_frame, bg="#3c3c3c", fg="white", insertbackground="white", relief="flat")
        self.entry_url.pack(fill=tk.X, **pad_opts)
        self.entry_url.bind("<KeyRelease>", self.update_data_from_editor)
        
        btn_open_url = tk.Button(self.editor_frame, text="Open Link 🌍", bg="#007acc", fg="white", relief="flat", command=self.open_url)
        btn_open_url.pack(pady=2, anchor="e", padx=15)

        tk.Label(self.editor_frame, text="Description / Notes:", bg=COLORS["panel_bg"], fg=COLORS["text_dim"]).pack(anchor="w", **pad_opts)
        self.txt_desc = tk.Text(self.editor_frame, height=10, bg="#3c3c3c", fg="white", insertbackground="white", relief="flat", font=FONT_TEXT)
        self.txt_desc.pack(fill=tk.BOTH, expand=True, **pad_opts)
        self.txt_desc.bind("<KeyRelease>", self.update_data_from_editor)

        btn_frame = tk.Frame(self.editor_frame, bg=COLORS["panel_bg"])
        btn_frame.pack(fill=tk.X, pady=20, padx=15)

        tk.Button(btn_frame, text="Add Child Node ➕", bg="#4caf50", fg="white", relief="flat", command=self.add_child).pack(fill=tk.X, pady=2)
        tk.Button(btn_frame, text="Delete Node 🗑️", bg="#f44336", fg="white", relief="flat", command=self.delete_node).pack(fill=tk.X, pady=2)

    
    def redraw(self):
        self.canvas.delete("all")
        start_x = 50
        start_y = self.root.winfo_height() // 2 if self.root.winfo_height() > 100 else 300
        
        self._calculate_positions(self.root_node, start_x, start_y)
        
        self._draw_lines(self.root_node)
        
        self._draw_nodes(self.root_node)

    def _calculate_positions(self, node, x, y):
        """
        Simple Tree Algorithm:
        Assigns space based on the number of leaf nodes (endpoints).
        """
        node.x = x
        node.y = y
        
        if not node.children:
            node.subtree_height = 80
            return

        total_height = 0
        for child in node.children:
            self._calculate_positions(child, x + 250, y)
            total_height += child.subtree_height
        
        node.subtree_height = total_height
        
        current_y = y - (total_height / 2)
        for child in node.children:
            child_y = current_y + (child.subtree_height / 2)
            self._calculate_positions(child, x + 250, child_y)
            current_y += child.subtree_height

    def _draw_lines(self, node):
        if not node.children:
            return
        
        for child in node.children:
            x1, y1 = node.x + node.width, node.y + (node.height/2)
            x2, y2 = child.x, child.y + (child.height/2)
            
            self.canvas.create_line(x1, y1, (x1+x2)/2, y1, (x1+x2)/2, y2, x2, y2, 
                                    fill=COLORS["line"], width=2, smooth=True)
            
            self._draw_lines(child)

    def _draw_nodes(self, node):
        bg_col = COLORS["highlight"] if node == self.selected_node else COLORS["node_bg"]
        outline_col = COLORS["node_border"] if node == self.selected_node else "#555"
        
        x, y = node.x, node.y
        w, h = node.width, node.height
        
        self.canvas.create_rectangle(x+3, y+3, x+w+3, y+h+3, fill="#111", outline="", tags="node_bg")

        self.canvas.create_rectangle(x, y, x+w, y+h, fill=bg_col, outline=outline_col, width=2, tags="node")
        
        if node.progress > 0:
            bar_width = (w - 4) * (node.progress / 100)
            self.canvas.create_rectangle(x+2, y+h-6, x+2+bar_width, y+h-2, fill=COLORS["progress"], outline="", tags="node")

        self.canvas.create_text(x+10, y+20, text=node.name, fill=COLORS["text"], font=FONT_TITLE, anchor="w", tags="node")
        
        if node.date:
            self.canvas.create_text(x+w-5, y+10, text=node.date, fill=COLORS["text_dim"], font=FONT_SMALL, anchor="e", tags="node")

        info_text = ""
        if node.url: info_text += "🔗 "
        if node.description: info_text += "📝 "
        self.canvas.create_text(x+10, y+40, text=info_text, fill="#ccc", font=FONT_SMALL, anchor="w", tags="node")
        
        for child in node.children:
            self._draw_nodes(child)


    def on_canvas_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        
        self.canvas.scan_mark(event.x, event.y)
        
        clicked_node = self._find_node_at(self.root_node, cx, cy)
        
        if clicked_node:
            self.selected_node = clicked_node
            self.load_node_to_editor()
            self.redraw()

    def on_canvas_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _find_node_at(self, node, x, y):
        if node.x <= x <= node.x + node.width and node.y <= y <= node.y + node.height:
            return node
        
        for child in node.children:
            found = self._find_node_at(child, x, y)
            if found: return found
        return None

    def on_right_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        clicked_node = self._find_node_at(self.root_node, cx, cy)
        if clicked_node:
            self.selected_node = clicked_node
            self.load_node_to_editor()
            self.redraw()
            
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="➕ Add Child Node", command=self.add_child)
            menu.add_command(label="🗑️ Delete Node", command=self.delete_node)
            menu.post(event.x_root, event.y_root)


    def load_node_to_editor(self):
        node = self.selected_node
        if not node: return

        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, node.name)

        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, node.date)

        self.entry_url.delete(0, tk.END)
        self.entry_url.insert(0, node.url)

        self.scale_progress.set(node.progress)

        self.txt_desc.delete("1.0", tk.END)
        self.txt_desc.insert("1.0", node.description)

    def update_data_from_editor(self, event=None):
        if not self.selected_node: return
        
        self.selected_node.name = self.entry_name.get()
        self.selected_node.date = self.entry_date.get()
        self.selected_node.url = self.entry_url.get()
        self.selected_node.progress = self.scale_progress.get()
        self.selected_node.description = self.txt_desc.get("1.0", tk.END).strip()
        
        self.redraw()

    def add_child(self):
        if not self.selected_node: return
        new_node = Node("New Goal", parent=self.selected_node)
        self.selected_node.children.append(new_node)
        self.redraw()

    def delete_node(self):
        if not self.selected_node: return
        if self.selected_node == self.root_node:
            messagebox.showwarning("Stop", "You cannot delete your 'Life' node!")
            return
        
        if messagebox.askyesno("Delete", "Delete this node and all sub-nodes?"):
            parent = self.selected_node.parent
            parent.children.remove(self.selected_node)
            self.selected_node = parent
            self.load_node_to_editor()
            self.redraw()

    def open_url(self):
        if self.selected_node and self.selected_node.url:
            webbrowser.open(self.selected_node.url)
        else:
            messagebox.showinfo("Info", "No URL provided.")


    def save_json(self):
        data = self.root_node.to_dict()
        file_path = filedialog.asksaveasfilename(defaultextension=".tiwut_timeline", filetypes=[("Tiwut Files", "*.tiwut_timeline")])
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                messagebox.showinfo("Saved", "Successfully saved.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

    def load_json(self):
        file_path = filedialog.askopenfilename(filetypes=[("Tiwut Files", "*.tiwut_timeline")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.root_node = Node.from_dict(data)
                self.selected_node = self.root_node
                self.load_node_to_editor()
                self.redraw()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TimelineMindMapApp(root)
    root.mainloop()