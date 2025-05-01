import cv2
import numpy as np
import os
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class ImageSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("調整付き画像分割アプリ（精密バージョン）")

        self.original_img = None
        self.image_path = None
        self.adjust = DoubleVar(value=4.0)

        Button(root, text="画像を選択", command=self.load_image).pack(pady=5)

        Label(root, text="分割位置の微調整（0.1単位）", font=("Arial", 10)).pack()
        Scale(root, from_=0.0, to=-10.0, resolution=0.1, orient=HORIZONTAL,
              length=400, variable=self.adjust, command=lambda _: self.update_preview()).pack()

        self.canvas = Canvas(root, width=700, height=350, bg="white")
        self.canvas.pack(pady=10)

        Button(root, text="分割して保存", command=self.save_images).pack(pady=5)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("画像ファイル", "*.jpg *.jpeg *.png")])
        if not path:
            return

        try:
            pil_img = Image.open(path)
            self.original_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            self.image_path = path
            self.update_preview()
        except Exception as e:
            messagebox.showerror("エラー", f"画像の読み込みに失敗しました。\n{e}")

    def update_preview(self):
        if self.original_img is None:
            return

        h, w = self.original_img.shape[:2]
        center = w // 2
        adj = float(self.adjust.get())

        left = self.original_img[:, :int(center + adj)]
        right = self.original_img[:, int(center - adj):]

        left_resized = cv2.resize(left, (int(left.shape[1] * 350 / h), 350))
        right_resized = cv2.resize(right, (int(right.shape[1] * 350 / h), 350))
        preview = cv2.hconcat([left_resized, right_resized])

        rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(rgb))

        self.canvas.delete("all")
        self.canvas.image = img_tk
        self.canvas.create_image(0, 0, anchor=NW, image=img_tk)

    def save_images(self):
        if self.original_img is None:
            messagebox.showwarning("警告", "画像を読み込んでください。")
            return

        h, w = self.original_img.shape[:2]
        center = w // 2
        adj = float(self.adjust.get())

        left = self.original_img[:, :int(center + adj)]
        right = self.original_img[:, int(center - adj):]

        base_path = self.image_path.rsplit('.', 1)[0]
        ext = "." + self.image_path.rsplit('.', 1)[1]
        left_path = base_path + "_L" + ext
        right_path = base_path + "_R" + ext

        cv2.imwrite(left_path, left)
        cv2.imwrite(right_path, right)
        messagebox.showinfo("完了", f"保存しました！\n\n{left_path}\n{right_path}")

if __name__ == "__main__":
    root = Tk()
    app = ImageSplitterApp(root)
    root.mainloop()
