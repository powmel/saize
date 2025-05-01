import cv2
import os
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

def split_and_save_image():
    path = filedialog.askopenfilename(filetypes=[("画像ファイル", "*.jpg *.jpeg *.png")])
    if not path:
        return

    # 画像読み込み
    img = cv2.imread(path)
    if img is None:
        messagebox.showerror("エラー", "画像を読み込めませんでした。")
        return

    h, w = img.shape[:2]
    mid = w // 2

    # 左右に分割
    left = img[:, :mid]
    right = img[:, mid:]

    # 出力ファイル名生成
    base, ext = os.path.splitext(path)
    left_path = base + "_L" + ext
    right_path = base + "_R" + ext

    # 保存
    cv2.imwrite(left_path, left)
    cv2.imwrite(right_path, right)

    messagebox.showinfo("完了", f"分割して保存しました！\n\n{left_path}\n{right_path}")

# GUI構築
root = Tk()
root.title("画像分割ツール（左右分割）")

Label(root, text="画像を選んで左右に分割・保存します", font=("Arial", 12)).pack(pady=10)
Button(root, text="画像を選択して分割", command=split_and_save_image, font=("Arial", 12)).pack(pady=20)

root.mainloop()
