import os
import PyPDF2
import pandas as pd
import chardet
from tkinter import Tk, ttk, filedialog, messagebox
from tkinter.constants import END

class PDFSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF拆分工具 v2.0")
        self.root.resizable(False, False)
        self.setup_ui()
        
    def setup_ui(self):
        """初始化用户界面"""
        # 文件选择部分
        ttk.Label(self.root, text="PDF文件:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
        self.pdf_entry = ttk.Entry(self.root, width=50)
        self.pdf_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.root, text="浏览...", command=self.select_pdf_file).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(self.root, text="输出文件夹:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.output_entry = ttk.Entry(self.root, width=50)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.root, text="浏览...", command=self.select_output_folder).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(self.root, text="名称文件(CSV):").grid(row=2, column=0, padx=10, pady=5, sticky='e')
        self.csv_entry = ttk.Entry(self.root, width=50)
        self.csv_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(self.root, text="浏览...", command=self.select_csv_file).grid(row=2, column=2, padx=5, pady=5)

        # 进度条
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

        # 开始按钮
        ttk.Button(self.root, text="开始拆分", command=self.start_split).grid(
            row=4, column=1, pady=10, ipadx=20, ipady=5)

    def select_pdf_file(self):
        """选择PDF文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        self.pdf_entry.delete(0, END)
        self.pdf_entry.insert(0, file_path)

    def select_output_folder(self):
        """选择输出文件夹"""
        folder_path = filedialog.askdirectory(title="选择输出文件夹")
        self.output_entry.delete(0, END)
        self.output_entry.insert(0, folder_path)

    def select_csv_file(self):
        """选择CSV文件"""
        file_path = filedialog.askopenfilename(
            title="选择名称文件",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        self.csv_entry.delete(0, END)
        self.csv_entry.insert(0, file_path)

    def detect_file_encoding(self, file_path):
        """自动检测文件编码"""
        with open(file_path, 'rb') as f:
            rawdata = f.read(100000)  # 读取前100KB用于检测
            return chardet.detect(rawdata)['encoding']

    def read_name_file(self, file_path):
        """读取包含名称的文件（支持CSV和Excel）"""
        if not os.path.exists(file_path):
            raise FileNotFoundError("文件不存在")
        
        # 自动检测编码（仅对CSV有效）
        if file_path.lower().endswith('.csv'):
            encoding = self.detect_file_encoding(file_path)
            encodings_to_try = [encoding, 'gb18030', 'gbk', 'utf-8', 'utf-16', 'latin1']
            
            for enc in encodings_to_try:
                try:
                    return pd.read_csv(file_path, encoding=enc)
                except UnicodeDecodeError:
                    continue
                except Exception:
                    break
        
        # 尝试Excel格式
        if file_path.lower().endswith(('.xls', '.xlsx')):
            try:
                return pd.read_excel(file_path)
            except Exception as e:
                raise ValueError(f"读取Excel文件失败: {str(e)}")
        
        raise ValueError("无法读取文件，请检查文件格式和编码")

    def split_pdf(self, pdf_path, output_folder, names):
        """执行PDF拆分操作"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError("PDF文件不存在")
        
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(reader.pages)

            if len(names) != total_pages:
                raise ValueError(
                    f"名称数量({len(names)})与PDF页数({total_pages})不匹配\n"
                    "请确保名称文件包含与PDF页数相同的名称"
                )

            self.progress['maximum'] = total_pages
            self.progress['value'] = 0

            for i, name in enumerate(names):
                # 清理文件名中的非法字符
                safe_name = "".join(
                    c for c in str(name).strip() 
                    if c.isalnum() or c in (' ', '_', '-', '(', ')', '（', '）')
                ) or f"page_{i+1}"
                
                writer = PyPDF2.PdfWriter()
                writer.add_page(reader.pages[i])

                output_path = os.path.join(output_folder, f"{safe_name}.pdf")
                with open(output_path, 'wb') as output_pdf:
                    writer.write(output_pdf)

                self.progress['value'] = i + 1
                self.root.update()

    def start_split(self):
        """开始处理拆分流程"""
        pdf_path = self.pdf_entry.get()
        output_folder = self.output_entry.get()
        csv_path = self.csv_entry.get()

        # 验证输入
        if not all([pdf_path, output_folder, csv_path]):
            messagebox.showerror("错误", "请填写所有必填字段！")
            return

        if not pdf_path.lower().endswith('.pdf'):
            messagebox.showerror("错误", "请选择有效的PDF文件（.pdf格式）")
            return

        try:
            # 读取名称文件
            df = self.read_name_file(csv_path)
            if df.empty:
                messagebox.showerror("错误", "名称文件为空或格式不正确")
                return
            
            # 获取名称列表（使用第一列）
            names = df.iloc[:, 0].astype(str).tolist()
            
            # 执行拆分
            self.split_pdf(pdf_path, output_folder, names)
            
            # 完成提示
            messagebox.showinfo(
                "完成",
                f"成功拆分 {len(names)} 页PDF到:\n{output_folder}\n\n"
                f"首尾文件名示例:\n"
                f"起始: {names[0] if len(names) > 0 else '无'}\n"
                f"结束: {names[-1] if len(names) > 1 else '无'}"
            )
            
        except Exception as e:
            messagebox.showerror("错误", f"处理失败:\n{str(e)}")
            self.progress['value'] = 0

if __name__ == "__main__":
    root = Tk()
    app = PDFSplitterApp(root)
    root.mainloop()