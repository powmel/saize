import cv2
import numpy as np
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import winsound
# SSIMによる差分検出
from skimage.metrics import structural_similarity as compare_ssim

class SpotTheDifferencePixel:
    def __init__(self, master):
        self.master = master
        master.title("ピクセル単位の間違い探し")
        # 画像データ
        self.img1 = None
        self.img2 = None
        self.rects = []             # 差分領域リスト
        self.found = []             # 見つけた差分インデックス
        self.game_mode = False
        # UI構築
        frame = Frame(master)
        frame.pack(pady=5)
        Button(frame, text="左画像を選択", command=self.load_left).pack(side=LEFT, padx=5)
        Button(frame, text="右画像を選択", command=self.load_right).pack(side=LEFT, padx=5)
        Button(frame, text="答え合わせ", command=self.answer_check).pack(side=LEFT, padx=5)
        Button(frame, text="ゲームモード開始", command=self.start_game).pack(side=LEFT, padx=5)

        self.status = Label(master, text="画像を両方読み込んでください", fg="blue")
        self.status.pack(pady=5)
        # キャンバス
        self.canvas = Canvas(master, width=800, height=400, bg="black")
        self.canvas.pack(pady=5)
        self.canvas.bind("<Button-1>", self.on_click)

    def load_left(self):
        path = filedialog.askopenfilename(filetypes=[("画像", "*.jpg *.jpeg *.png")])
        if not path: return
        self.img1 = self._read_and_resize(path)
        self.status.config(text=f"左画像: {path.split('/')[-1]}")
        self._reset()

    def load_right(self):
        path = filedialog.askopenfilename(filetypes=[("画像", "*.jpg *.jpeg *.png")])
        if not path: return
        self.img2 = self._read_and_resize(path)
        self.status.config(text=f"右画像: {path.split('/')[-1]}")
        self._reset()

    def _read_and_resize(self, path):
        pil = Image.open(path)
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        # 高さ400pxに揃える
        h, w = img.shape[:2]
        new_w = int(w * 400 / h)
        return cv2.resize(img, (new_w, 400))

    def _reset(self):
        self.rects = []
        self.found = []
        self.game_mode = False
        if self.img1 is not None and self.img2 is not None:
            self._display_combined()

    def _display_combined(self, disp=None):
        if disp is None:
            if self.img1 is None or self.img2 is None:
                return
            disp = cv2.hconcat([self.img1, self.img2])
        rgb = cv2.cvtColor(disp, cv2.COLOR_BGR2RGB)
        imgtk = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.canvas.config(width=disp.shape[1], height=disp.shape[0])
        self.canvas.delete("all")
        self.canvas.image = imgtk
        self.canvas.create_image(0, 0, anchor=NW, image=imgtk)

    def detect_differences(self):
        # SSIMを用いた差分検出
        gray1 = cv2.cvtColor(self.img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(self.img2, cv2.COLOR_BGR2GRAY)
        score, diff = compare_ssim(gray1, gray2, full=True)
        diff = (diff * 255).astype("uint8")
        # 反転して差分を強調
        _, thresh = cv2.threshold(diff, 200, 255, cv2.THRESH_BINARY_INV)
        # モルフォロジーで領域を統合
        kernel = np.ones((5,5), np.uint8)
        clean = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
        clean = cv2.morphologyEx(clean, cv2.MORPH_OPEN, kernel, iterations=1)
        # 輪郭抽出
        contours, _ = cv2.findContours(clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rects = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < 50:  # 小さい領域は除外
                continue
            x, y, w, h = cv2.boundingRect(c)
            pad = 4
            rects.append((max(x-pad,0), max(y-pad,0), w+pad*2, h+pad*2))
        self.rects = rects

    def answer_check(self):
        if self.img1 is None or self.img2 is None:
            messagebox.showwarning("警告", "左右両方の画像を読み込んでください。")
            return
        self.detect_differences()
        if not self.rects:
            messagebox.showinfo("情報", "差分が検出されませんでした。")
            return
        base = cv2.hconcat([self.img1, self.img2])
        def animate(i=0):
            disp = base.copy()
            color = (255,255,255) if i%2==0 else (0,0,255)
            offset = self.img1.shape[1]
            for x,y,w,h in self.rects:
                cv2.rectangle(disp, (x,y), (x+w,y+h), color, 2)
                cv2.rectangle(disp, (offset+x,y), (offset+x+w,y+h), color, 2)
            self._display_combined(disp)
            if i < 6:
                self.master.after(200, lambda: animate(i+1))
        animate()
        winsound.Beep(1000,200)

    def start_game(self):
        if self.img1 is None or self.img2 is None:
            messagebox.showwarning("警告", "画像を両方読み込んでください。")
            return
        self.detect_differences()
        self.found = []
        self.game_mode = True
        self.status.config(text=f"ゲーム開始: 残り {len(self.rects)} 箇所")
        self._display_combined()

    def on_click(self, event):
        if not self.game_mode:
            return
        x_click, y_click = event.x, event.y
        offset = self.img1.shape[1]
        for idx, (x,y,w,h) in enumerate(self.rects):
            if (x <= x_click < x+w and y <= y_click < y+h) or \
               (offset+x <= x_click < offset+x+w and y <= y_click < y+h):
                if idx in self.found:
                    return
                self.found.append(idx)
                self._mark_found(idx)
                rem = len(self.rects) - len(self.found)
                self.status.config(text=f"残り {rem} 箇所" if rem>0 else "おめでとう！ 全部見つけたよ！")
                winsound.Beep(800,150)
                break

    def _mark_found(self, idx):
        disp = cv2.hconcat([self.img1, self.img2])
        offset = self.img1.shape[1]
        for i in self.found:
            x,y,w,h = self.rects[i]
            cv2.rectangle(disp, (x,y), (x+w,y+h), (0,255,0), 2)
            cv2.rectangle(disp, (offset+x,y), (offset+x+w,y+h), (0,255,0), 2)
        self._display_combined(disp)

if __name__ == '__main__':
    root = Tk()
    app = SpotTheDifferencePixel(root)
    root.mainloop()
