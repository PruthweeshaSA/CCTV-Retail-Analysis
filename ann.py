import os
import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# ================= CONFIG =================
CANVAS_W = 960
CANVAS_H = 540

GENDER_MAP = {"M": 0, "F": 1, "U": 2}
AGE_MAP = {"K": 0, "YA": 1, "A": 2, "O": 3}
ETHNICITY_MAP = {"AS": 0, "EU": 1, "ME": 2, "AF": 3, "U": 4}
# =========================================


class MultiYOLOAnnotationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Task YOLO Person Annotation Tool (Auto-Save)")
        self.root.geometry("1380x860")

        self.image_paths = []
        self.current_index = 0

        # Stores ALL info per box
        self.boxes = []

        self.gender = "U"
        self.age = "A"
        self.ethnicity = "U"

        self.current_box = None
        self.build_ui()

    # ================= UI =================
    def build_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, pady=6)

        tk.Button(top, text="Load Video", command=self.load_video).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Prev", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Next", command=self.next_image).pack(side=tk.LEFT, padx=5)

        attr = tk.Frame(top)
        attr.pack(side=tk.LEFT, padx=30)

        self.make_group(attr, "Gender", ["M", "F", "U"], "gender")
        self.make_group(attr, "Age", ["K", "YA", "A", "O"], "age")
        self.make_group(attr, "Ethnicity", ["AS", "EU", "ME", "AF", "U"], "ethnicity")

        self.status = tk.Label(top, text="Draw box → auto-saved", fg="blue")
        self.status.pack(side=tk.LEFT, padx=20)

        self.canvas = tk.Canvas(self.root, bg="black",
                                width=CANVAS_W, height=CANVAS_H)
        self.canvas.pack(pady=10)

        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.drawing)
        self.canvas.bind("<ButtonRelease-1>", self.finish_draw)

    def make_group(self, parent, title, values, attr):
        frame = tk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=10)
        tk.Label(frame, text=title, font=("Arial", 9, "bold")).pack()

        var = tk.StringVar(value=values[-1])
        setattr(self, f"{attr}_var", var)

        for v in values:
            tk.Radiobutton(
                frame, text=v, value=v, variable=var,
                command=lambda a=attr, v=var: setattr(self, a, v.get())
            ).pack(anchor="w")

    # ================= VIDEO =================
    def load_video(self):
        video = filedialog.askopenfilename(
            filetypes=[("Video Files", "*.mp4 *.avi *.mov")]
        )
        if not video:
            return

        out_dir = filedialog.askdirectory(title="Select folder to save frames")
        if not out_dir:
            return

        cap = cv2.VideoCapture(video)
        idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imwrite(os.path.join(out_dir, f"frame_{idx:05d}.jpg"), frame)
            idx += 1

        cap.release()
        self.load_frames(out_dir)

    # ================= FRAMES =================
    def load_frames(self, folder):
        self.image_paths = sorted(
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(".jpg")
        )
        self.current_index = 0
        self.load_image()

    def load_image(self):
        self.canvas.delete("all")
        self.boxes.clear()

        img = Image.open(self.image_paths[self.current_index])
        self.ow, self.oh = img.size

        img.thumbnail((CANVAS_W, CANVAS_H))
        self.sx = self.ow / img.width
        self.sy = self.oh / img.height

        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        self.status.config(
            text=f"Auto-save enabled | {os.path.basename(self.image_paths[self.current_index])}"
        )

    # ================= DRAW =================
    def start_draw(self, e):
        self.start_x, self.start_y = e.x, e.y
        self.current_box = self.canvas.create_rectangle(
            e.x, e.y, e.x, e.y, outline="cyan", width=2
        )

    def drawing(self, e):
        self.canvas.coords(self.current_box, self.start_x, self.start_y, e.x, e.y)

    def finish_draw(self, e):
        x1, y1, x2, y2 = self.canvas.coords(self.current_box)
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        # YOLO normalized
        xc = ((x1 + x2) / 2) * self.sx / self.ow
        yc = ((y1 + y2) / 2) * self.sy / self.oh
        w = (x2 - x1) * self.sx / self.ow
        h = (y2 - y1) * self.sy / self.oh

        # Pixel
        px = int(x1 * self.sx)
        py = int(y1 * self.sy)
        pw = int((x2 - x1) * self.sx)
        ph = int((y2 - y1) * self.sy)

        box = {
            "yolo": (xc, yc, w, h),
            "pixel": (px, py, pw, ph),
            "gender": self.gender,
            "age": self.age,
            "ethnicity": self.ethnicity
        }

        self.boxes.append(box)
        self.auto_save(box)
        self.current_box = None

    # ================= AUTO SAVE =================
    def auto_save(self, box):
        img_path = self.image_paths[self.current_index]
        img_name = os.path.splitext(os.path.basename(img_path))[0]
        root_dir = os.path.dirname(img_path)

        for task in ["person", "gender", "age", "ethnicity"]:
            os.makedirs(os.path.join(root_dir, "labels", task), exist_ok=True)

        xc, yc, w, h = box["yolo"]

        self.write("person", img_name, f"0 {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
        self.write("gender", img_name, f"{GENDER_MAP[box['gender']]} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
        self.write("age", img_name, f"{AGE_MAP[box['age']]} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")
        self.write("ethnicity", img_name, f"{ETHNICITY_MAP[box['ethnicity']]} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")

        self.save_visualization(img_path)
        self.status.config(text="Bounding box auto-saved ✔")

    # ================= VISUALIZATION =================
    def save_visualization(self, img_path):
        vis_dir = os.path.join(os.path.dirname(img_path), "visualizer")
        os.makedirs(vis_dir, exist_ok=True)

        img = cv2.imread(img_path)

        for box in self.boxes:
            px, py, pw, ph = box["pixel"]
            label = f"{box['gender']} | {box['age']} | {box['ethnicity']}"

            cv2.rectangle(img, (px, py), (px + pw, py + ph), (0, 255, 255), 2)

            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img, (px, py - th - 8), (px + tw + 6, py), (0, 255, 255), -1)
            cv2.putText(img, label, (px + 3, py - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        cv2.imwrite(os.path.join(vis_dir, os.path.basename(img_path)), img)

    def write(self, task, base, line):
        path = os.path.join(
            os.path.dirname(self.image_paths[self.current_index]),
            "labels", task, base + ".txt"
        )
        with open(path, "a") as f:
            f.write(line + "\n")

    # ================= NAV =================
    def next_image(self):
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_image()

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()


# ================= RUN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = MultiYOLOAnnotationTool(root)
    root.mainloop()
