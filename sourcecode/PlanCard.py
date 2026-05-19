import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json
import os
import sys
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"

def load_or_create_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    with open(KEY_FILE, "rb") as f:
        return f.read()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

KEY = load_or_create_key()
cipher = Fernet(KEY)

class DraggablePlanCard:
    def __init__(self, canvas, x1, y1, x2, y2, color="#1f538d", text_content="Enter Your Project", rect2_coords=None, center_coords=None):
        self.canvas = canvas
        self.color = color
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        self.rect = canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, fill=color, outline="white", width=1)

        if rect2_coords:
            self.r2X1, self.r2Y1, self.r2X2, self.r2Y2 = rect2_coords
        else:
            offsetX = 130
            offsetY = 20
            self.r2X1 = 100 + offsetX
            self.r2Y1 = 80 + offsetY
            self.r2X2 = x2 + offsetX
            self.r2Y2 = y2 + offsetY

        self.rect2 = canvas.create_rectangle(self.r2X1, self.r2Y1, self.r2X2, self.r2Y2, fill="#e1e1e1", outline="white", width=1)

        self.textBox_widget = ctk.CTkTextbox(self.canvas, fg_color=color, bg_color=color, text_color="#000000", width=150, height=100, border_width=0)
        self.textBox_widget.insert("0.0", text_content)

        if center_coords:
            self.orijin_x, self.orijin_y = center_coords
        else:
            self.orijin_x = (x1 + x2) / 2
            self.orijin_y = (y1 + y2) / 2

        self.textArea = canvas.create_window(self.orijin_x, self.orijin_y, window=self.textBox_widget, anchor="center")

        self.canvas.tag_bind(self.rect, "<Button-1>", self.startMove)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.move)
        self.canvas.tag_bind(self.rect, "<Button-3>", self.deleteCard)

    def startMove(self, event):
        self.endX = event.x
        self.endY = event.y

    def move(self, event):
        dx = event.x - self.endX
        dy = event.y - self.endY

        self.canvas.move(self.rect, dx, dy)
        self.canvas.move(self.rect2, dx, dy)
        self.canvas.move(self.textArea, dx, dy)

        self.x1 += dx
        self.y1 += dy
        self.x2 += dx
        self.y2 += dy

        self.r2X1 += dx
        self.r2Y1 += dy
        self.r2X2 += dx
        self.r2Y2 += dy

        self.orijin_x += dx
        self.orijin_y += dy

        self.endX = event.x
        self.endY = event.y

    def getData(self):
        return {
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "rect2_coords": [self.r2X1, self.r2Y1, self.r2X2, self.r2Y2],
            "center_coords": [self.orijin_x, self.orijin_y],
            "color": self.color,
            "textContent": self.textBox_widget.get("1.0", "end-1c")
        }

    def deleteCard(self, event=None):
        self.canvas.delete(self.rect)
        self.canvas.delete(self.rect2)
        self.canvas.delete(self.textArea)
        self.textBox_widget.destroy()
        if self in all_cards:
            all_cards.remove(self)

app = ctk.CTk()
app.title("PlanCard")
app.geometry("1000x700")

img = Image.open(resource_path("icon.png"))
icon = ImageTk.PhotoImage(img)
app.iconphoto(True, icon)

canvasFrame = ctk.CTkFrame(app, corner_radius=25, fg_color="#492A06")
canvasFrame.pack(fill="both", expand=True, padx=20, pady=20)

canvas = ctk.CTkCanvas(canvasFrame, bg="#553712", highlightthickness=0)
canvas.pack(fill="both", expand=True, padx=10, pady=10)

all_cards = []

def createPlan():
    plan = DraggablePlanCard(canvas, 370, 350, 150, 150, color="#d4c66e")
    all_cards.append(plan)

def savePlans():
    if not all_cards:
        messagebox.showwarning("Warning", "No cards to save.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".plancard", filetypes=[("PlanCard", "*.plancard")], title="Save File")
    if not file_path:
        return

    try:
        data_to_save = [card.getData() for card in all_cards]
        json_data = json.dumps(data_to_save, ensure_ascii=False, indent=4)
        encrypted_data = cipher.encrypt(json_data.encode("utf-8"))

        with open(file_path, "wb") as f:
            f.write(encrypted_data)

        messagebox.showinfo("Success", "Encrypted file saved.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def loadPlans():
    global all_cards

    file_path = filedialog.askopenfilename(filetypes=[("PlanCard", "*.plancard")], title="Open File")
    if not file_path:
        return

    try:
        with open(file_path, "rb") as f:
            encrypted_data = f.read()

        decrypted_data = cipher.decrypt(encrypted_data)
        loaded_data = json.loads(decrypted_data.decode("utf-8"))

        for card in list(all_cards):
            card.deleteCard()

        all_cards.clear()

        for data in loaded_data:
            plan = DraggablePlanCard(
                canvas,
                data["x1"],
                data["y1"],
                data["x2"],
                data["y2"],
                color=data.get("color", "#d4c66e"),
                text_content=data["textContent"],
                rect2_coords=data.get("rect2_coords"),
                center_coords=data.get("center_coords")
            )
            all_cards.append(plan)

        messagebox.showinfo("Success", "Encrypted file loaded.")
    except Exception as e:
        messagebox.showerror("Error", f"Decryption failed:\n{e}")

btn_frame = ctk.CTkFrame(app, fg_color="transparent")
btn_frame.pack(pady=10)

ctk.CTkButton(btn_frame, text="Create PlanCard", command=createPlan).pack(side="left", padx=5)
ctk.CTkButton(btn_frame, text="Save PlanCards", command=savePlans).pack(side="left", padx=5)
ctk.CTkButton(btn_frame, text="Load PlanCards", command=loadPlans).pack(side="left", padx=5)

app.mainloop()