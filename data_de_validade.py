import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sqlite3
import threading
import time

# Configuração do banco de dados
conn = sqlite3.connect('produtos.db')
cursor = conn.cursor()

# Tabelas para produtos, categorias, lotes e alarmes
cursor.execute('''
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    valor TEXT NOT NULL,
    FOREIGN KEY (produto_id) REFERENCES produtos (id)
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS lotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    validade DATE NOT NULL,
    FOREIGN KEY (produto_id) REFERENCES produtos (id)
);
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS alarmes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_categoria TEXT NOT NULL,
    valor_categoria TEXT NOT NULL,
    data_alarme DATE NOT NULL
);
''')

conn.commit()

# Funções do programa

def verificar_alarmes():
    """Verifica e notifica alarmes de vencimento."""
    data_atual = datetime.now().date()
    cursor.execute("SELECT * FROM lotes WHERE validade = ?", (data_atual,))
    lotes_hoje = cursor.fetchall()

    for lote in lotes_hoje:
        messagebox.showinfo(
            "Alerta de Vencimento",
            f"O lote '{lote[2]}' do produto com ID {lote[1]} vence hoje!"
        )

def agendar_verificacao():
    """Agenda a verificação de alarmes diariamente às 9h."""
    def tarefa_verificacao():
        while True:
            agora = datetime.now()
            proxima_execucao = datetime.combine(agora.date(), datetime.min.time()) + timedelta(hours=9)
            if agora > proxima_execucao:
                proxima_execucao += timedelta(days=1)
            intervalo = (proxima_execucao - agora).total_seconds()
            time.sleep(intervalo)
            verificar_alarmes()

    thread = threading.Thread(target=tarefa_verificacao, daemon=True)
    thread.start()

def adicionar_produto():
    """Abre uma janela para adicionar um novo produto."""
    def salvar_produto():
        nome = entry_nome.get()
        tipo = entry_tipo.get()
        quantidade = entry_quantidade.get()
        unidades = entry_unidades.get()
        sabor = entry_sabor.get()

        if not nome:
            messagebox.showerror("Erro", "O nome do produto é obrigatório.")
            return

        cursor.execute("INSERT INTO produtos (nome) VALUES (?)", (nome,))
        produto_id = cursor.lastrowid

        if tipo:
            cursor.execute("INSERT INTO categorias (produto_id, tipo, valor) VALUES (?, ?, ?)", (produto_id, "Tipo", tipo))
        if quantidade:
            cursor.execute("INSERT INTO categorias (produto_id, tipo, valor) VALUES (?, ?, ?)", (produto_id, "Quantidade", quantidade))
        if unidades:
            cursor.execute("INSERT INTO categorias (produto_id, tipo, valor) VALUES (?, ?, ?)", (produto_id, "Unidades", unidades))
        if sabor:
            cursor.execute("INSERT INTO categorias (produto_id, tipo, valor) VALUES (?, ?, ?)", (produto_id, "Sabor", sabor))

        conn.commit()
        messagebox.showinfo("Sucesso", "Produto adicionado com sucesso.")
        janela_produto.destroy()

    janela_produto = tk.Toplevel()
    janela_produto.title("Adicionar Produto")
    janela_produto.configure(bg='white')

    tk.Label(janela_produto, text="Nome do Produto:", bg='white').grid(row=0, column=0, sticky="w")
    entry_nome = tk.Entry(janela_produto)
    entry_nome.grid(row=0, column=1)

    tk.Label(janela_produto, text="Tipo de Produto:", bg='white').grid(row=1, column=0, sticky="w")
    entry_tipo = tk.Entry(janela_produto)
    entry_tipo.grid(row=1, column=1)

    tk.Label(janela_produto, text="Quantidade:", bg='white').grid(row=2, column=0, sticky="w")
    entry_quantidade = tk.Entry(janela_produto)
    entry_quantidade.grid(row=2, column=1)

    tk.Label(janela_produto, text="Número de Unidades:", bg='white').grid(row=3, column=0, sticky="w")
    entry_unidades = tk.Entry(janela_produto)
    entry_unidades.grid(row=3, column=1)

    tk.Label(janela_produto, text="Sabor:", bg='white').grid(row=4, column=0, sticky="w")
    entry_sabor = tk.Entry(janela_produto)
    entry_sabor.grid(row=4, column=1)

    tk.Button(janela_produto, text="Salvar", command=salvar_produto).grid(row=5, column=1)

def listar_produtos():
    """Lista todos os produtos na tela principal."""
    for widget in frame_lista.winfo_children():
        widget.destroy()

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    for produto in produtos:
        produto_id = produto[0]
        produto_nome = produto[1]

        frame_produto = tk.Frame(frame_lista, bg='white', pady=5)
        frame_produto.pack(fill=tk.X, padx=10)

        tk.Button(
            frame_produto,
            text="i",
            command=lambda pid=produto_id: visualizar_produto(pid)
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(frame_produto, text=produto_nome, bg='white', font=("Arial", 12)).pack(side=tk.LEFT)

def interface_principal():
    """Configura a interface principal."""
    global frame_lista

    root = tk.Tk()
    root.title("Gerenciador de Produtos Alimentícios")
    root.configure(bg='white')

    barra_superior = tk.Frame(root, bg='#333333')
    barra_superior.pack(side=tk.TOP, fill=tk.X)

    entry_busca = tk.Entry(barra_superior)
    entry_busca.pack(side=tk.LEFT, padx=5, pady=5)

    tk.Button(barra_superior, text="Pesquisar", command=lambda: buscar_produtos(entry_busca.get())).pack(side=tk.LEFT, padx=5)
    tk.Button(barra_superior, text="Pesquisa Avançada", command=abrir_pesquisa_avancada).pack(side=tk.LEFT, padx=5)
    tk.Button(barra_superior, text="Novo Produto", command=adicionar_produto).pack(side=tk.RIGHT, padx=5)

    frame_lista = tk.Frame(root, bg='white')
    frame_lista.pack(fill=tk.BOTH, expand=True)

    listar_produtos()
    agendar_verificacao()

    root.mainloop()

# Executar a aplicação
interface_principal()
