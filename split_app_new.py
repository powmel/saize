import cv2
import numpy as np
from tkinter import *
from tkinter import filedialog
from PIL import Image, ImageTk

class ImageSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ポップな画像左右分割ツール")
        self.root.configure(bg="#E0F7FA")

        self.img = None
        self.path = None
        self.adjust = DoubleVar(value=0.0)
        self.overlay = BooleanVar(value=True)

        # --- UI ---
        btn_frame = Frame(root, bg="#E0F7FA")
        btn_frame.pack(pady=10)
        Button(btn_frame, text="📁 画像を選択", bg="#80DEEA",
               command=self.load_image, width=12).pack(side=LEFT, padx=5)
        Button(btn_frame, text="🤖 自動調整", bg="#FFCC80",
               command=self.auto_align, width=12).pack(side=LEFT, padx=5)

        status_frame = Frame(root, bg="#E0F7FA")
        status_frame.pack()
        self.status = Label(status_frame, text="画像未ロード", bg="#E0F7FA",
                            fg="#006064", font=("Arial", 10))
        self.status.pack()

        Label(root, text="🔧 分割オフセット調整（px）", bg="#E0F7FA",
              fg="#006064", font=("Arial", 10)).pack()
        Scale(root, from_=-30.0, to=30.0, resolution=0.1, orient=HORIZONTAL,
              length=400, variable=self.adjust,
              command=lambda _: self.update_preview()).pack()

        chk = Checkbutton(root, text="透過プレビュー", bg="#E0F7FA",
                          variable=self.overlay,
                          command=self.update_preview)
        chk.pack(pady=5)

        self.canvas = Canvas(root, width=600, height=400, bg="#FFFFFF", bd=2, relief=RIDGE)
        self.canvas.pack(pady=10)

        Button(root, text="💾 分割して保存", bg="#A5D6A7",
               command=self.save_images, width=20).pack(pady=5)

    def load_image(self):
        p = filedialog.askopenfilename(filetypes=[("画像", "*.jpg *.jpeg *.png")])
        if not p: return
        self.path = p
        pil = Image.open(p)
        self.img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        self.status.config(text=f"Loaded: {p.split('/')[-1]}")
        self.update_preview()

    def update_preview(self):
        if self.img is None: return
        h, w = self.img.shape[:2]
        c = w//2; adj = int(self.adjust.get())
        left = self.img[:, :c+adj]
        right = self.img[:, c-adj:]
        # サイズ揃え
        lh = left.shape[0]; lw = left.shape[1]
        rh = right.shape[0]; rw = right.shape[1]
        ht = 380
        lw2 = int(lw * ht / lh); rw2 = int(rw * ht / rh)
        left_r = cv2.resize(left, (lw2, ht))
        right_r = cv2.resize(right, (rw2, ht))

        if self.overlay.get():
            # 左画像に右画像半透明で重ねる
            overlay_img = cv2.addWeighted(left_r, 0.6, right_r, 0.6, 0)
            disp = overlay_img
        else:
            disp = cv2.hconcat([left_r, right_r])

        imgtk = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(disp, cv2.COLOR_BGR2RGB)))
        self.canvas.delete("all")
        self.canvas.image = imgtk
        self.canvas.create_image(0, 0, anchor=NW, image=imgtk)

    def save_images(self):
        if self.img is None: return
        h, w = self.img.shape[:2]
        c = w//2; adj = int(self.adjust.get())
        left = self.img[:, :c+adj]
        right = self.img[:, c-adj:]
        base, ext = self.path.rsplit('.',1)
        cv2.imwrite(f"{base}_L.{ext}", left)
        cv2.imwrite(f"{base}_R.{ext}", right)
        self.status.config(text="✅ 保存完了")

    def auto_align(self):
        """最小二乗誤差で最適オフセット探索（±30px）"""
        if self.img is None: return
        h, w = self.img.shape[:2]
        c = w//2
        best, best_err = 0, float('inf')
        # 左右を比較する幅
        for s in range(-30,31):
            L = self.img[:, :c+s]
            R = self.img[:, c-s:]
            mh = min(L.shape[0], R.shape[0])
            mw = min(L.shape[1], R.shape[1])
            L2 = cv2.resize(L, (mw, mh))
            R2 = cv2.resize(R, (mw, mh))
            err = np.mean((cv2.cvtColor(L2,cv2.COLOR_BGR2GRAY).astype(float)
                           - cv2.cvtColor(R2,cv2.COLOR_BGR2GRAY).astype(float))**2)
            if err < best_err:
                best_err, best = err, s
        self.adjust.set(best)
        self.status.config(text=f"🔧 自動調整: {best}px")
        self.update_preview()

if __name__ == "__main__":
    root = Tk()
    app = ImageSplitterApp(root)
    root.mainloop()
