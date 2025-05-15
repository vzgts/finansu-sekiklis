import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    amount = Column(Float)
    category = Column(String)
    transaction_type = Column(String)  # 'income' arba 'expense'
    description = Column(String)


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    category_type = Column(String)  # 'income' arba 'expense'


class FinanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Finansų sekiklis")
        self.root.geometry("1200x1200")
        self.engine = create_engine('sqlite:///finance_tracker.db')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.create_default_categories()
        self.create_widgets()
        self.update_data()

    def create_default_categories(self):
        if not self.session.query(Category).first():
            default_categories = [
                ('Maistas', 'expense'),
                ('Transportas', 'expense'),
                ('Mokesčiai', 'expense'),
                ('Pramogos', 'expense'),
                ('Būstas', 'expense'),
                ('Atlyginimas', 'income'),
                ('Verslas', 'income'),
                ('Investicijos', 'income'),
                ('Kitos pajamos', 'income')
            ]

            for name, cat_type in default_categories:
                category = Category(name=name, category_type=cat_type)
                self.session.add(category)

            self.session.commit()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Naujas įrašas", padding="10")
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(input_frame, text="Tipas:").grid(row=0, column=0, sticky=tk.W)
        self.transaction_type = tk.StringVar(value="expense")
        ttk.Radiobutton(input_frame, text="Išlaidos", variable=self.transaction_type, value="expense").grid(row=0,
                                                                                                            column=1,
                                                                                                            sticky=tk.W)
        ttk.Radiobutton(input_frame, text="Pajamos", variable=self.transaction_type, value="income").grid(row=0,
                                                                                                          column=2,
                                                                                                          sticky=tk.W)
        self.transaction_type.trace_add('write', lambda *args: self.update_category_combobox())

        ttk.Label(input_frame, text="Data:").grid(row=1, column=0, sticky=tk.W)
        self.date_entry = ttk.Entry(input_frame)
        self.date_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(input_frame, text="Suma:").grid(row=2, column=0, sticky=tk.W)
        self.amount_entry = ttk.Entry(input_frame)
        self.amount_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)

        ttk.Label(input_frame, text="Kategorija:").grid(row=3, column=0, sticky=tk.W)
        self.category_combobox = ttk.Combobox(input_frame, state="readonly")
        self.category_combobox.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        self.update_category_combobox()

        ttk.Label(input_frame, text="Aprašymas:").grid(row=4, column=0, sticky=tk.W)
        self.description_entry = ttk.Entry(input_frame, width=40)
        self.description_entry.grid(row=4, column=1, padx=5, pady=2, sticky=tk.W)

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)

        save_btn = ttk.Button(button_frame, text="Išsaugoti", command=self.save_transaction)
        save_btn.pack(side=tk.LEFT, padx=5)

        clear_btn = ttk.Button(button_frame, text="Išvalyti", command=self.clear_fields)
        clear_btn.pack(side=tk.LEFT, padx=5)

        manage_cat_btn = ttk.Button(button_frame, text="Valdyti kategorijas", command=self.manage_categories)
        manage_cat_btn.pack(side=tk.LEFT, padx=5)

        analysis_frame = ttk.LabelFrame(main_frame, text="Analizė", padding="10")
        analysis_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.figure_frame = ttk.Frame(analysis_frame)
        self.figure_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(analysis_frame)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Label(control_frame, text="Ataskaita:").pack(side=tk.LEFT)
        self.report_type = tk.StringVar(value="expenses_by_category")
        reports = [
            ("Išlaidų kategorijos", "expenses_by_category"),
            ("Pajamų kategorijos", "income_by_category"),
            ("Mėnesio išlaidos", "monthly_expenses"),
            ("Mėnesio pajamos", "monthly_income"),
            ("Balansas", "balance")
        ]

        for text, value in reports:
            ttk.Radiobutton(control_frame, text=text, variable=self.report_type,
                            value=value, command=self.update_chart).pack(side=tk.LEFT, padx=5)

        list_frame = ttk.LabelFrame(main_frame, text="Operacijos", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tree = ttk.Treeview(list_frame, columns=("date", "type", "amount", "category", "description"),
                                 show="headings")
        self.tree.heading("date", text="Data")
        self.tree.heading("type", text="Tipas")
        self.tree.heading("amount", text="Suma")
        self.tree.heading("category", text="Kategorija")
        self.tree.heading("description", text="Aprašymas")
        self.tree.column("date", width=100)
        self.tree.column("type", width=80)
        self.tree.column("amount", width=80)
        self.tree.column("category", width=120)
        self.tree.column("description", width=250)
        self.tree.pack(fill=tk.BOTH, expand=True)

        manage_frame = ttk.Frame(list_frame)
        manage_frame.pack(fill=tk.X, pady=5)

        delete_btn = ttk.Button(manage_frame, text="Ištrinti", command=self.delete_transaction)
        delete_btn.pack(side=tk.LEFT, padx=5)

        filter_frame = ttk.Frame(manage_frame)
        filter_frame.pack(side=tk.RIGHT)

        ttk.Label(filter_frame, text="Filtruoti:").pack(side=tk.LEFT)
        self.filter_month = ttk.Combobox(filter_frame, values=self.get_months_list(), width=10)
        self.filter_month.pack(side=tk.LEFT, padx=5)
        self.filter_month.bind("<<ComboboxSelected>>", self.filter_transactions)

        ttk.Label(filter_frame, text="Kategorija:").pack(side=tk.LEFT)
        self.filter_category = ttk.Combobox(filter_frame, values=self.get_all_categories(), width=15)
        self.filter_category.pack(side=tk.LEFT, padx=5)
        self.filter_category.bind("<<ComboboxSelected>>", self.filter_transactions)

        clear_filter_btn = ttk.Button(filter_frame, text="Išvalyti filtrą", command=self.clear_filter)
        clear_filter_btn.pack(side=tk.LEFT, padx=5)

    def update_category_combobox(self, *args):
        categories = self.session.query(Category).filter_by(category_type=self.transaction_type.get()).all()
        self.category_combobox['values'] = [cat.name for cat in categories]
        if categories:
            self.category_combobox.current(0)

    def save_transaction(self):
        try:
            date = datetime.strptime(self.date_entry.get(), "%Y-%m-%d").date()
            amount = float(self.amount_entry.get())
            category = self.category_combobox.get()
            description = self.description_entry.get()
            transaction_type = self.transaction_type.get()

            if not category:
                messagebox.showwarning("Klaida", "Pasirinkite kategoriją")
                return

            transaction = Transaction(
                date=date,
                amount=amount,
                category=category,
                transaction_type=transaction_type,
                description=description
            )

            self.session.add(transaction)
            self.session.commit()

            messagebox.showinfo("Sėkmingai", "Operacija išsaugota")
            self.clear_fields()
            self.update_data()
        except ValueError as e:
            messagebox.showerror("Klaida", f"Neteisingi duomenys: {str(e)}")

    def clear_fields(self):
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.amount_entry.delete(0, tk.END)
        self.description_entry.delete(0, tk.END)
        self.update_category_combobox()

    def update_data(self):
        self.load_transactions()
        self.update_chart()
        self.filter_month['values'] = self.get_months_list()
        self.filter_category['values'] = self.get_all_categories()

    def load_transactions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        transactions = self.session.query(Transaction).order_by(Transaction.date.desc()).all()

        for trans in transactions:
            trans_type = "Pajamos" if trans.transaction_type == "income" else "Išlaidos"
            amount = f"+{trans.amount:.2f}" if trans.transaction_type == "income" else f"-{trans.amount:.2f}"
            self.tree.insert("", tk.END, values=(
                trans.date.strftime("%Y-%m-%d"),
                trans_type,
                amount,
                trans.category,
                trans.description
            ), iid=trans.id)

    def update_chart(self):
        for widget in self.figure_frame.winfo_children():
            widget.destroy()

        query = self.session.query(
            Transaction.date,
            Transaction.amount,
            Transaction.category,
            Transaction.transaction_type
        )

        df = pd.read_sql(query.statement, self.session.bind)

        if df.empty:
            ttk.Label(self.figure_frame, text="Nėra duomenų diagramai rodyti").pack(expand=True)
            return

        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')

        fig = plt.Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)

        report_type = self.report_type.get()

        if report_type == "expenses_by_category":
            expenses = df[df['transaction_type'] == 'expense']
            if not expenses.empty:
                expenses_by_cat = expenses.groupby('category')['amount'].sum().sort_values()
                expenses_by_cat.plot(kind='bar', ax=ax, color='red')
                ax.set_title('Išlaidų pasiskirstymas pagal kategorijas', fontweight='bold')
                ax.set_xlabel('Suma', fontweight='bold')
                ax.tick_params(axis='x', labelrotation=360)
            else:
                ax.set_title('Nėra išlaidų duomenų')

        elif report_type == "income_by_category":
            income = df[df['transaction_type'] == 'income']
            if not income.empty:
                income_by_cat = income.groupby('category')['amount'].sum().sort_values()
                income_by_cat.plot(kind='bar', ax=ax, color='green')
                ax.set_title('Pajamų pasiskirstymas pagal kategorijas', fontweight='bold')
                ax.set_xlabel('Suma', fontweight='bold')
                ax.tick_params(axis='x', labelrotation=360)
            else:
                ax.set_title('Nėra pajamų duomenų')

        elif report_type == "monthly_expenses":
            expenses = df[df['transaction_type'] == 'expense']
            if not expenses.empty:
                monthly_expenses = expenses.groupby('month')['amount'].sum()
                monthly_expenses.plot(kind='bar', ax=ax, color='red')
                ax.set_title('Mėnesinės išlaidos', fontweight='bold')
                ax.set_ylabel('Suma', fontweight='bold')
                ax.set_xticklabels([str(period) for period in monthly_expenses.index], rotation=45)
            else:
                ax.set_title('Nėra išlaidų duomenų')

        elif report_type == "monthly_income":
            income = df[df['transaction_type'] == 'income']
            if not income.empty:
                monthly_income = income.groupby('month')['amount'].sum()
                monthly_income.plot(kind='bar', ax=ax, color='green')
                ax.set_title('Mėnesinės pajamos', fontweight='bold')
                ax.set_ylabel('Suma', fontweight='bold')
                ax.set_xticklabels([str(period) for period in monthly_income.index], rotation=45)
            else:
                ax.set_title('Nėra pajamų duomenų')

        elif report_type == "balance":
            income = df[df['transaction_type'] == 'income'].groupby('month')['amount'].sum()
            expenses = df[df['transaction_type'] == 'expense'].groupby('month')['amount'].sum()

            balance = income.subtract(expenses, fill_value=0)

            if not balance.empty:
                balance.plot(kind='bar', ax=ax, color='blue')
                ax.set_title('Mėnesinis balansas (Pajamos - Išlaidos)', fontweight='bold')
                ax.set_ylabel('Suma', fontweight='bold')
                ax.set_xticklabels([str(period) for period in balance.index], rotation=45)
            else:
                ax.set_title('Nėra duomenų balansui skaičiuoti')

        canvas = FigureCanvasTkAgg(fig, master=self.figure_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def manage_categories(self):
        cat_window = tk.Toplevel(self.root)
        cat_window.title("Kategorijų valdymas")
        cat_window.geometry("500x400")

        list_frame = ttk.Frame(cat_window, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(list_frame, columns=("name", "type"), show="headings")
        tree.heading("name", text="Pavadinimas")
        tree.heading("type", text="Tipas")
        tree.column("name", width=200)
        tree.column("type", width=100)
        tree.pack(fill=tk.BOTH, expand=True)

        categories = self.session.query(Category).order_by(Category.category_type, Category.name).all()
        for cat in categories:
            cat_type = "Pajamos" if cat.category_type == "income" else "Išlaidos"
            tree.insert("", tk.END, values=(cat.name, cat_type), iid=cat.id)

        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=5)

        add_btn = ttk.Button(button_frame, text="Pridėti", command=lambda: self.add_category(cat_window, tree))
        add_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = ttk.Button(button_frame, text="Ištrinti", command=lambda: self.delete_category(tree))
        delete_btn.pack(side=tk.LEFT, padx=5)

        close_btn = ttk.Button(button_frame, text="Uždaryti", command=cat_window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)

    def add_category(self, parent_window, tree):
        add_window = tk.Toplevel(parent_window)
        add_window.title("Pridėti kategoriją")
        add_window.geometry("300x200")

        ttk.Label(add_window, text="Pavadinimas:").pack(pady=5)
        name_entry = ttk.Entry(add_window, width=30)
        name_entry.pack(pady=5)

        ttk.Label(add_window, text="Tipas:").pack(pady=5)
        cat_type = tk.StringVar(value="expense")
        ttk.Radiobutton(add_window, text="Išlaidos", variable=cat_type, value="expense").pack()
        ttk.Radiobutton(add_window, text="Pajamos", variable=cat_type, value="income").pack()

        def save_category():
            name = name_entry.get()
            if not name:
                messagebox.showwarning("Klaida", "Įveskite kategorijos pavadinimą")
                return

            category = Category(name=name, category_type=cat_type.get())
            self.session.add(category)
            self.session.commit()

            cat_type_display = "Pajamos" if cat_type.get() == "income" else "Išlaidos"
            tree.insert("", tk.END, values=(name, cat_type_display), iid=category.id)

            self.update_category_combobox()
            self.filter_category['values'] = self.get_all_categories()

            add_window.destroy()

        save_btn = ttk.Button(add_window, text="Išsaugoti", command=save_category)
        save_btn.pack(pady=10)

    def delete_category(self, tree):
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showwarning("Klaida", "Pasirinkite kategoriją, kurią norite ištrinti")
            return

        transactions_count = self.session.query(Transaction).filter_by(
            category=tree.item(selected_item)['values'][0]).count()

        if transactions_count > 0:
            messagebox.showwarning("Klaida",
                                   f"Ši kategorija naudojama {transactions_count} operacijose. "
                                   "Pirmiausia pakeiskite šių operacijų kategorijas.")
            return

        if messagebox.askyesno("Patvirtinimas", "Ar tikrai norite ištrinti šią kategoriją?"):
            self.session.query(Category).filter_by(id=selected_item).delete()
            self.session.commit()
            tree.delete(selected_item)

            self.update_category_combobox()
            self.filter_category['values'] = self.get_all_categories()

    def delete_transaction(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Klaida", "Pasirinkite operaciją, kurią norite ištrinti")
            return

        if messagebox.askyesno("Patvirtinimas", "Ar tikrai norite ištrinti šią operaciją?"):
            self.session.query(Transaction).filter_by(id=selected_item).delete()
            self.session.commit()
            self.update_data()

    def get_months_list(self):
        dates = self.session.query(Transaction.date).distinct().all()
        months = set(datetime.strptime(str(date[0]), "%Y-%m-%d").strftime("%Y-%m") for date in dates)
        return sorted(months, reverse=True)

    def get_all_categories(self):
        categories = self.session.query(Category.name).order_by(Category.name).all()
        return [cat[0] for cat in categories]

    def filter_transactions(self, event=None):
        month = self.filter_month.get()
        category = self.filter_category.get()

        query = self.session.query(Transaction)

        if month:
            year, month_num = map(int, month.split('-'))
            query = query.filter(
                Transaction.date >= f"{year}-{month_num:02d}-01",
                Transaction.date <= f"{year}-{month_num:02d}-31"
            )

        if category:
            query = query.filter_by(category=category)

        transactions = query.order_by(Transaction.date.desc()).all()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for trans in transactions:
            trans_type = "Pajamos" if trans.transaction_type == "income" else "Išlaidos"
            amount = f"+{trans.amount:.2f}" if trans.transaction_type == "income" else f"-{trans.amount:.2f}"
            self.tree.insert("", tk.END, values=(
                trans.date.strftime("%Y-%m-%d"),
                trans_type,
                amount,
                trans.category,
                trans.description
            ), iid=trans.id)

    def clear_filter(self):
        self.filter_month.set('')
        self.filter_category.set('')
        self.load_transactions()


if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceTracker(root)
    root.mainloop()
