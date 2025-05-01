import cv2
import numpy as np
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import time
import winsound
import os

class SpotTheDifferenceGame:
    def __init__(self, master):
        self.master = master
        self.master.title("サイゼリヤ風 間違い探し")

        self.img1 = None
        self.img2 = None
        self.img1_path = ""  # 左画像のパス
        self.img2_path = ""  # 右画像のパス
        self.grid_size = IntVar(value=6)
        self.found = set()
        self.diff_blocks = []
        self.game_started = False
        self.start_time = None
        self.game_time = 180  # 3分
        self.score = 0

        # キャンバスサイズを調整 (幅を倍に)
        self.canvas_width = 1200  # 600 * 2
        self.canvas_height = 400

        # スコアと時間の表示
        self.score_label = Label(master, text="スコア: 0", font=('Arial', 14))
        self.score_label.pack()
        self.time_label = Label(master, text="残り時間: 3:00", font=('Arial', 14))
        self.time_label.pack()

        # 画像選択ボタンとラベル
        self.left_image_frame = Frame(master)
        self.left_image_frame.pack(fill=X, padx=5, pady=2)
        Button(self.left_image_frame, text="左画像を選択", command=self.load_left_image).pack(side=LEFT)
        self.left_image_path_label = Label(self.left_image_frame, text="選択されていません", anchor='w')
        self.left_image_path_label.pack(side=LEFT, fill=X, expand=True, padx=5)

        self.right_image_frame = Frame(master)
        self.right_image_frame.pack(fill=X, padx=5, pady=2)
        Button(self.right_image_frame, text="右画像を選択", command=self.load_right_image).pack(side=LEFT)
        self.right_image_path_label = Label(self.right_image_frame, text="選択されていません", anchor='w')
        self.right_image_path_label.pack(side=LEFT, fill=X, expand=True, padx=5)

        Scale(master, from_=3, to=20, orient=HORIZONTAL, label="分割数（N×N）", variable=self.grid_size,
              command=lambda _: self.reset_analysis()).pack(fill=X)

        Button(master, text="比較してスタート", command=self.analyze_differences).pack(pady=5)

        self.canvas = Canvas(master, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

    def load_image(self, side):
        path = filedialog.askopenfilename(filetypes=[("画像ファイル", "*.jpg *.png *.jpeg")])
        if path:
            try:
                # 日本語パス対応
                n = np.fromfile(path, np.uint8)
                img = cv2.imdecode(n, cv2.IMREAD_COLOR)

                if img is None:
                    messagebox.showerror("エラー", f"画像を読み込めませんでした: {path}")
                    return None, ""

                # リサイズ処理
                resized_img = cv2.resize(img, (self.canvas_width // 2, self.canvas_height))
                messagebox.showinfo("情報", f"{side}画像を正常に読み込みました。")
                return resized_img, path

            except Exception as e:
                messagebox.showerror("エラー", f"画像の処理中に予期せぬエラーが発生しました: {e}")
                return None, ""
        return None, ""

    def load_left_image(self):
        img, path = self.load_image("左")
        if img is not None:
            self.img1 = img
            self.img1_path = path
            self.left_image_path_label.config(text=os.path.basename(path))
            self.reset_analysis()  # 画像が変わったら分析結果をリセット
            self.display_images()  # 左右画像表示関数を呼び出す

    def load_right_image(self):
        img, path = self.load_image("右")
        if img is not None:
            self.img2 = img
            self.img2_path = path
            self.right_image_path_label.config(text=os.path.basename(path))
            self.reset_analysis()  # 画像が変わったら分析結果をリセット
            self.display_images()  # 左右画像表示関数を呼び出す

    def reset(self):
        self.img1 = None  # 画像自体もリセット
        self.img2 = None
        self.img1_path = ""
        self.img2_path = ""
        self.left_image_path_label.config(text="選択されていません")
        self.right_image_path_label.config(text="選択されていません")
        self.reset_analysis()
        self.canvas.delete("all")  # キャンバスをクリア

    def reset_analysis(self):
        # 画像自体はリセットせず、分析結果やゲーム状態のみリセット
        self.found.clear()
        self.diff_blocks = []
        self.game_started = False
        self.score = 0
        self.score_label.config(text="スコア: 0")
        self.time_label.config(text="残り時間: 3:00")
        # 画像が読み込まれていれば表示する
        self.display_images()  # 左右画像表示関数を呼び出す

    def analyze_differences(self):
        if self.img1 is None or self.img2 is None:
            messagebox.showwarning("警告", "左右両方の画像を選択してください。")
            return

        # 画像サイズが一致するか確認 (リサイズしているので基本的には一致するはず)
        if self.img1.shape != self.img2.shape:
            messagebox.showerror("エラー", "左右の画像のサイズが異なります。同じサイズの画像を選択してください。")
            return

        self.found.clear()
        self.diff_blocks = []
        n = self.grid_size.get()
        h, w = self.img1.shape[:2]
        gh, gw = h // n, w // n

        for y in range(n):
            for x in range(n):
                y1, y2 = y * gh, (y + 1) * gh
                x1, x2 = x * gw, (x + 1) * gw

                block1 = self.img1[y1:y2, x1:x2]
                block2 = self.img2[y1:y2, x1:x2]

                diff = cv2.absdiff(block1, block2)
                gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                mean_diff = np.mean(gray)

                if mean_diff > 20:
                    self.diff_blocks.append((x, y))

        self.game_started = True
        self.start_time = time.time()
        self.update_timer()
        self.display_images()  # 左右画像表示関数を呼び出す

    def update_timer(self):
        if not self.game_started:
            return

        elapsed = int(time.time() - self.start_time)
        remaining = max(0, self.game_time - elapsed)

        if remaining == 0:
            self.game_over("時間切れです！")
            return

        minutes = remaining // 60
        seconds = remaining % 60
        self.time_label.config(text=f"残り時間: {minutes}:{seconds:02d}")
        self.master.after(1000, self.update_timer)

    def game_over(self, message):
        self.game_started = False
        messagebox.showinfo("ゲーム終了", f"{message}\nスコア: {self.score}")
        self.reset()

    def display_images(self, overlays=[]):
        if self.img1 is None or self.img2 is None:
            if self.img1 is not None:
                img_resized = cv2.resize(self.img1, (self.canvas_width // 2, self.canvas_height))
                placeholder = np.zeros((self.canvas_height, self.canvas_width // 2, 3), dtype=np.uint8)
                display = cv2.hconcat([img_resized, placeholder])
            elif self.img2 is not None:
                img_resized = cv2.resize(self.img2, (self.canvas_width // 2, self.canvas_height))
                placeholder = np.zeros((self.canvas_height, self.canvas_width // 2, 3), dtype=np.uint8)
                display = cv2.hconcat([placeholder, img_resized])
            else:
                self.canvas.delete("all")
                return
        else:
            img1_resized = cv2.resize(self.img1, (self.canvas_width // 2, self.canvas_height))
            img2_resized = cv2.resize(self.img2, (self.canvas_width // 2, self.canvas_height))
            display = cv2.hconcat([img1_resized, img2_resized])

        for (gx, gy, color, side) in overlays:
            n = self.grid_size.get()
            single_image_width = self.canvas_width // 2
            gh = self.canvas_height // n
            gw = single_image_width // n
            x_offset = 0 if side == 'left' else single_image_width
            x1, y1 = x_offset + gx * gw, gy * gh
            x2, y2 = x_offset + (gx + 1) * gw, (gy + 1) * gh
            cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)

        rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(rgb)
        img_tk = ImageTk.PhotoImage(img_pil)
        self.canvas.image = img_tk
        self.canvas.create_image(0, 0, anchor=NW, image=img_tk)

    def on_click(self, event):
        if not self.game_started:
            messagebox.showinfo("情報", "「比較してスタート」ボタンを押してください。")
            return
        if self.img1 is None or self.img2 is None:
            return

        n = self.grid_size.get()
        single_image_width = self.canvas_width // 2
        gw = single_image_width // n
        gh = self.canvas_height // n

        if event.x < single_image_width:
            side = 'left'
            gx = event.x // gw
            gy = event.y // gh
        else:
            side = 'right'
            local_x = event.x - single_image_width
            gx = local_x // gw
            gy = event.y // gh

        if not (0 <= gx < n and 0 <= gy < n):
            return

        if (gx, gy) in self.diff_blocks and (gx, gy) not in self.found:
            self.found.add((gx, gy))
            self.highlight_difference(gx, gy, side)

    def highlight_difference(self, gx, gy, side):
        if not self.game_started:
            return

        n = self.grid_size.get()
        single_image_width = self.canvas_width // 2
        gh = self.canvas_height // n
        gw = single_image_width // n
        x_offset = 0 if side == 'left' else single_image_width

        current_overlays = [(fx, fy, (0, 255, 0), s) for (fx, fy) in self.found for s in ['left', 'right']]

        def animate(count=0):
            nonlocal current_overlays
            if count >= 6:
                final_overlays = [(fx, fy, (0, 255, 0), s) for (fx, fy) in self.found for s in ['left', 'right']]
                self.display_images(overlays=final_overlays)
                return

            color = (255, 255, 255) if count % 2 == 0 else (0, 0, 255)
            temp_overlays = current_overlays + [(gx, gy, color, side)]
            self.display_images(overlays=temp_overlays)
            self.master.after(200, lambda: animate(count + 1))

        animate()

        self.score += 100
        self.score_label.config(text=f"スコア: {self.score}")
        winsound.Beep(1000, 200)

        if len(self.found) == len(self.diff_blocks):
            self.game_over("おめでとうございます！\nすべての違いを見つけました！")

if __name__ == "__main__":
    root = Tk()
    app = SpotTheDifferenceGame(root)
    root.mainloop()
