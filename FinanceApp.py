import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import datetime
import csv
import os
import traceback
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('finance_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 枚举和数据结构 ====================
class TransactionType(Enum):
    INCOME = "收入"
    EXPENSE = "支出"

@dataclass
class Transaction:
    id: int
    type: TransactionType
    category: str
    amount: float
    date: str
    description: str
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'category': self.category,
            'amount': self.amount,
            'date': self.date,
            'description': self.description
        }

# ==================== 核心业务类 ====================
class FinanceManager:
    def __init__(self):
        self.transactions: List[Transaction] = []
        self.next_id = 1
        self.categories = {
            '收入': ['工资', '奖金', '投资回报', '其他收入'],
            '支出': ['餐饮', '交通', '购物', '娱乐', '住房', '医疗']
        }
        self._load_data()
    
    def _load_data(self):
        """加载数据 - 添加详细日志"""
        try:
            if os.path.exists('transactions.json'):
                logger.info("开始加载数据文件")
                with open('transactions.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"读取到 {len(data)} 条交易记录")
                    
                    for item in data:
                        try:
                            transaction = Transaction(
                                id=item['id'],
                                type=TransactionType(item['type']),
                                category=item['category'],
                                amount=item['amount'],
                                date=item['date'],
                                description=item['description']
                            )
                            self.transactions.append(transaction)
                        except KeyError as e:
                            logger.error(f"数据字段缺失: {e}, 数据: {item}")
                        except ValueError as e:
                            logger.error(f"数据类型错误: {e}, 数据: {item}")
                    
                    if self.transactions:
                        self.next_id = max(t.id for t in self.transactions) + 1
                        logger.info(f"下一个ID设置为: {self.next_id}")
            else:
                logger.info("数据文件不存在，将创建新文件")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            messagebox.showwarning("数据错误", "数据文件格式错误，将创建新文件")
        except Exception as e:
            logger.error(f"加载数据失败: {e}\n{traceback.format_exc()}")
    
    def save_data(self):
        """保存数据"""
        try:
            logger.debug(f"开始保存 {len(self.transactions)} 条记录")
            with open('transactions.json', 'w', encoding='utf-8') as f:
                json.dump([t.to_dict() for t in self.transactions], f, 
                         ensure_ascii=False, indent=2)
            logger.info("数据保存成功")
        except Exception as e:
            logger.error(f"保存数据失败: {e}\n{traceback.format_exc()}")
            raise
    
    def add_transaction(self, type_: TransactionType, category: str, 
                       amount: float, description: str = "") -> Transaction:
        """添加交易记录 - 添加详细验证"""
        logger.debug(f"添加交易: type={type_}, category={category}, amount={amount}")
        
        # 验证输入
        if not category or category.strip() == "":
            logger.error("类别为空")
            raise ValueError("请选择交易类别")
        
        if amount <= 0:
            logger.error(f"金额无效: {amount}")
            raise ValueError("金额必须大于0")
        
        if amount > 1000000:
            logger.error(f"金额过大: {amount}")
            raise ValueError("金额不能超过1000000")
        
        try:
            transaction = Transaction(
                id=self.next_id,
                type=type_,
                category=category.strip(),
                amount=round(float(amount), 2),
                date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                description=description.strip()
            )
            
            self.transactions.append(transaction)
            self.next_id += 1
            self.save_data()
            
            logger.info(f"交易添加成功: ID={transaction.id}")
            return transaction
            
        except Exception as e:
            logger.error(f"创建交易对象失败: {e}\n{traceback.format_exc()}")
            raise
    
    def get_transactions(self, filter_type: Optional[TransactionType] = None) -> List[Transaction]:
        if filter_type:
            return [t for t in self.transactions if t.type == filter_type]
        return self.transactions
    
    def get_summary(self) -> Dict:
        total_income = sum(t.amount for t in self.transactions if t.type == TransactionType.INCOME)
        total_expense = sum(t.amount for t in self.transactions if t.type == TransactionType.EXPENSE)
        balance = total_income - total_expense
        
        income_by_category = {}
        expense_by_category = {}
        
        for t in self.transactions:
            if t.type == TransactionType.INCOME:
                income_by_category[t.category] = income_by_category.get(t.category, 0) + t.amount
            else:
                expense_by_category[t.category] = expense_by_category.get(t.category, 0) + t.amount
        
        return {
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance,
            'income_by_category': income_by_category,
            'expense_by_category': expense_by_category
        }
    
    def export_to_csv(self, filename: str):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', '类型', '类别', '金额', '日期', '描述'])
                for t in self.transactions:
                    writer.writerow([
                        t.id, t.type.value, t.category, 
                        t.amount, t.date, t.description
                    ])
            logger.info(f"数据已导出到: {filename}")
            return True
        except Exception as e:
            logger.error(f"导出失败: {e}\n{traceback.format_exc()}")
            return False

# ==================== GUI应用类 ====================
class FinanceApp:
    def __init__(self):
        logger.info("启动财务管理系统")
        self.finance_manager = FinanceManager()
        self.setup_ui()
    
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("个人财务管理系统 - 修复版")
        self.root.geometry("900x700")
        
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 左侧：添加交易区域
        left_frame = ttk.LabelFrame(main_frame, text="添加交易", padding="10")
        left_frame.grid(row=0, column=0, padx=(0, 10), sticky=tk.N)
        
        # 交易类型
        ttk.Label(left_frame, text="交易类型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="收入")
        type_combo = ttk.Combobox(left_frame, textvariable=self.type_var, 
                                values=["收入", "支出"], state="readonly", width=20)
        type_combo.grid(row=0, column=1, pady=5)
        type_combo.bind('<<ComboboxSelected>>', self.on_type_change)
        
        # 交易类别 - 添加验证
        ttk.Label(left_frame, text="交易类别*:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(left_frame, textvariable=self.category_var, 
                                          width=20, state="readonly")
        self.category_combo.grid(row=1, column=1, pady=5)
        self.update_categories()
        
        # 金额 - 添加验证
        ttk.Label(left_frame, text="金额*:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.amount_var = tk.StringVar(value="0.00")
        amount_entry = ttk.Entry(left_frame, textvariable=self.amount_var, width=23)
        amount_entry.grid(row=2, column=1, pady=5)
        
        # 描述
        ttk.Label(left_frame, text="描述:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.desc_text = tk.Text(left_frame, height=3, width=20)
        self.desc_text.grid(row=3, column=1, pady=5)
        
        # 按钮
        ttk.Button(left_frame, text="添加交易", command=self.add_transaction).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(left_frame, text="导出CSV", command=self.export_csv).grid(row=5, column=0, columnspan=2, pady=5)
        
        # 右侧：交易列表和摘要
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 交易列表
        list_frame = ttk.LabelFrame(right_frame, text="交易记录", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ('ID', '类型', '类别', '金额', '日期', '描述')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == '金额':
                self.tree.column(col, width=80, anchor='e')
            else:
                self.tree.column(col, width=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 过滤器
        filter_frame = ttk.Frame(list_frame)
        filter_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky=tk.W)
        
        ttk.Label(filter_frame, text="筛选:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                  values=["全部", "收入", "支出"], state="readonly", width=15)
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self.refresh_list)
        
        # 摘要信息
        summary_frame = ttk.LabelFrame(right_frame, text="财务摘要", padding="10")
        summary_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.summary_labels = {}
        labels_info = [
            ("总收入:", "total_income", "¥0.00"),
            ("总支出:", "total_expense", "¥0.00"),
            ("余额:", "balance", "¥0.00")
        ]
        
        for i, (text, key, default) in enumerate(labels_info):
            ttk.Label(summary_frame, text=text).grid(row=i, column=0, sticky=tk.W)
            self.summary_labels[key] = ttk.Label(summary_frame, text=default, 
                                                font=('Arial', 10, 'bold'))
            self.summary_labels[key].grid(row=i, column=1, sticky=tk.W, padx=(10, 0))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=(0, 5))
        
        # 初始化数据
        self.refresh_list()
        self.update_summary()
        
        # 绑定事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_type_change(self, event=None):
        """交易类型改变时更新类别"""
        self.update_categories()
    
    def update_categories(self):
        """更新类别下拉框"""
        selected_type = self.type_var.get()
        categories = self.finance_manager.categories.get(selected_type, [])
        self.category_combo['values'] = categories
        if categories:
            self.category_combo.set(categories[0])
        else:
            self.category_combo.set("")
    
    def add_transaction(self):
        """添加交易记录 - 关键修复部分"""
        try:
            logger.debug("开始添加交易")
            
            # 获取输入值
            type_str = self.type_var.get()
            category = self.category_var.get()
            amount_str = self.amount_var.get()
            description = self.desc_text.get("1.0", tk.END).strip()
            
            logger.debug(f"输入值: type={type_str}, category={category}, amount={amount_str}")
            
            # 验证输入
            error_messages = []
            
            if not category or category.strip() == "":
                error_messages.append("请选择交易类别")
                logger.warning("类别未选择")
            
            try:
                amount = float(amount_str)
                logger.debug(f"金额解析成功: {amount}")
            except ValueError:
                error_messages.append("金额必须是数字")
                logger.error(f"金额解析失败: {amount_str}")
            
            if error_messages:
                messagebox.showerror("输入错误", "\n".join(error_messages))
                return
            
            # 转换类型
            transaction_type = TransactionType.INCOME if type_str == "收入" else TransactionType.EXPENSE
            
            # 添加交易
            transaction = self.finance_manager.add_transaction(
                transaction_type, category, amount, description
            )
            
            # 清空输入
            self.amount_var.set("0.00")
            self.desc_text.delete("1.0", tk.END)
            self.status_var.set(f"交易添加成功 (ID: {transaction.id})")
            
            # 刷新显示
            self.refresh_list()
            self.update_summary()
            
            logger.info(f"交易添加完成: ID={transaction.id}")
            
        except ValueError as e:
            logger.error(f"验证错误: {e}")
            messagebox.showerror("输入错误", str(e))
        except Exception as e:
            logger.error(f"添加失败: {e}\n{traceback.format_exc()}")
            messagebox.showerror("系统错误", f"添加失败: {str(e)}")
    
    def refresh_list(self, event=None):
        """刷新交易列表"""
        try:
            # 清空现有项
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 获取过滤条件
            filter_type = self.filter_var.get()
            transactions = self.finance_manager.get_transactions()
            
            # 应用过滤
            if filter_type == "收入":
                transactions = [t for t in transactions if t.type == TransactionType.INCOME]
            elif filter_type == "支出":
                transactions = [t for t in transactions if t.type == TransactionType.EXPENSE]
            
            # 添加项到Treeview
            for transaction in reversed(transactions):  # 最新的在前面
                self.tree.insert('', 0, values=(
                    transaction.id,
                    transaction.type.value,
                    transaction.category,
                    f"¥{transaction.amount:.2f}",
                    transaction.date,
                    transaction.description[:20] + "..." if len(transaction.description) > 20 
                    else transaction.description
                ))
            
            logger.debug(f"列表刷新完成，显示 {len(transactions)} 条记录")
            self.status_var.set(f"显示 {len(transactions)} 条记录")
            
        except Exception as e:
            logger.error(f"刷新列表失败: {e}\n{traceback.format_exc()}")
            self.status_var.set("刷新失败")
    
    def update_summary(self):
        """更新摘要信息"""
        try:
            summary = self.finance_manager.get_summary()
            
            # 更新标签
            self.summary_labels['total_income'].config(
                text=f"¥{summary['total_income']:.2f}",
                foreground='green'
            )
            self.summary_labels['total_expense'].config(
                text=f"¥{summary['total_expense']:.2f}",
                foreground='red'
            )
            
            balance_color = 'green' if summary['balance'] >= 0 else 'red'
            self.summary_labels['balance'].config(
                text=f"¥{summary['balance']:.2f}",
                foreground=balance_color
            )
            
            logger.debug(f"摘要更新: 收入={summary['total_income']}, 支出={summary['total_expense']}")
            
        except Exception as e:
            logger.error(f"更新摘要失败: {e}\n{traceback.format_exc()}")
    
    def export_csv(self):
        """导出CSV文件"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
                title="导出数据"
            )
            
            if filename:
                if self.finance_manager.export_to_csv(filename):
                    messagebox.showinfo("成功", f"数据已导出到:\n{filename}")
                    self.status_var.set(f"数据已导出到: {os.path.basename(filename)}")
                else:
                    messagebox.showerror("错误", "导出失败，请查看日志")
                    self.status_var.set("导出失败")
        
        except Exception as e:
            logger.error(f"导出CSV失败: {e}\n{traceback.format_exc()}")
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def on_closing(self):
        """关闭窗口时的清理工作"""
        logger.info("应用程序关闭")
        self.root.destroy()
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()

# ==================== 主程序 ====================
def main():
    """主函数"""
    try:
        print("=" * 50)
        print("个人财务管理系统启动")
        print(f"当前时间: {datetime.datetime.now()}")
        print("日志文件: finance_debug.log")
        print("=" * 50)
        
        # 启动GUI应用
        app = FinanceApp()
        app.run()
        
    except Exception as e:
        logger.error(f"程序启动失败: {e}\n{traceback.format_exc()}")
        messagebox.showerror("启动错误", f"程序启动失败:\n{str(e)}")

# ==================== 程序入口 ====================
if __name__ == "__main__":
    main()