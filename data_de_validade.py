import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import ttk
from datetime import datetime, time
import threading
import time as time_mod
import winsound
import json
import os

produtos = []
categorias_personalizadas = []
produtos_para_destacar = []
indice_mapeamento = []

ultimo_botao_focado = None

def restaurar_foco_botao():
    if ultimo_botao_focado is not None:
        try:
            ultimo_botao_focado.focus_set()
        except:
            pass

def atualizar_lista_visual():
    lista_produtos.delete(0, tk.END)
    indice_mapeamento.clear()

    hoje = datetime.now().date()

    def prioridade(produto):
        datas = produto.get("vencimentos", [])
        prioridade_valor = 5
        for data_str in datas:
            try:
                data_venc = datetime.strptime(data_str, "%d/%m/%Y").date()
                dias = (data_venc - hoje).days
                if dias == 0:
                    return 0
                elif dias == 1:
                    return 1
                elif 1 < dias <= 7:
                    prioridade_valor = min(prioridade_valor, 2)
                elif 7 < dias <= 30:
                    prioridade_valor = min(prioridade_valor, 3)
            except:
                continue
        return prioridade_valor

    produtos_ordenados = sorted(enumerate(produtos), key=lambda p: (prioridade(p[1]), p[1].get("nome", "").lower()))

    for idx_real, produto in produtos_ordenados:
        indice_mapeamento.append(idx_real)
        texto = f"{produto.get('nome', '')} | Código: {produto.get('código de barras', '')}"
        cor_fundo = None
        cor_texto = "black"

        if "vencimentos" in produto and produto["vencimentos"]:
            datas_ordenadas = sorted(produto["vencimentos"], key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
            texto += f" | Vencimentos: {', '.join(datas_ordenadas)}"
            for data_str in datas_ordenadas:
                try:
                    data_venc = datetime.strptime(data_str, "%d/%m/%Y").date()
                    dias = (data_venc - hoje).days
                    if dias == 0:
                        cor_fundo = "#333333"
                        cor_texto = "white"
                        break
                    elif dias == 1:
                        cor_fundo = "#FF6666"
                        break
                    elif 1 < dias <= 7:
                        cor_fundo = "#FFA500"
                        break
                    elif 7 < dias <= 30:
                        cor_fundo = "#FFFF99"
                        break
                except:
                    continue

        idx = lista_produtos.size()
        lista_produtos.insert(tk.END, texto)
        if cor_fundo:
            lista_produtos.itemconfig(idx, {'bg': cor_fundo, 'fg': cor_texto})

def popup_categorias_personalizadas(produto):
    popup = tk.Toplevel(janela)
    popup.title("Selecionar Categorias")
    popup.configure(bg="#cccccc")
    popup.geometry("400x220")
    popup.grab_set()
    popup.resizable(False, False)

    tk.Label(popup, text="Escolha uma categoria ou aperte finalizar para concluir:", bg="#cccccc", font=("Arial", 11)).pack(pady=(10, 5))

    categoria_var = tk.StringVar()
    combo = ttk.Combobox(popup, textvariable=categoria_var, values=categorias_personalizadas, state="readonly")
    combo.pack(padx=20, fill="x")

    tk.Label(popup, text="Digite o valor e aperte confima:", bg="#cccccc", font=("Arial", 11)).pack(pady=(10, 5))

    entrada = tk.Entry(popup, font=("Arial", 11))
    entrada.pack(padx=20, fill="x")

    def confirmar():
        cat = categoria_var.get()
        val = entrada.get()
        if cat and val:
            produto[cat] = val
            entrada.delete(0, tk.END)
            categoria_var.set("")

    def finalizar():
        popup.destroy()
        restaurar_foco_botao()

    frame_botoes = tk.Frame(popup, bg="#cccccc")
    frame_botoes.pack(pady=20)

    btn_confirmar = tk.Button(frame_botoes, text="Confirmar", command=confirmar,
                              bg="white", fg="black", font=("Arial", 10, "bold"), width=12)
    btn_confirmar.pack(side="left", padx=10)

    btn_finalizar = tk.Button(frame_botoes, text="Finalizar", command=finalizar,
                              bg="white", fg="black", font=("Arial", 10, "bold"), width=12)
    btn_finalizar.pack(side="left", padx=10)

    entrada.focus()
    entrada.bind("<Return>", lambda e: confirmar())

    popup.wait_window()

def adicionar_categoria():
    nova_categoria = popup_input("Nova Categoria", "Digite o nome da nova categoria:")
    if nova_categoria:
        if nova_categoria not in categorias_personalizadas:
            categorias_personalizadas.append(nova_categoria)
            salvar_dados()
            popup_aviso("Sucesso", f"Categoria '{nova_categoria}' adicionada!")
        else:
            popup_aviso("Aviso", "Essa categoria já existe.")

def remover_categoria():
    if not categorias_personalizadas:
        popup_aviso("Nenhuma categoria", "Não há categorias para remover.")
        return

    categorias_str = "\n".join(f"{i+1}. {cat}" for i, cat in enumerate(categorias_personalizadas))
    escolha = popup_input("Remover Categoria", f"Digite o número da categoria para remover:\n\n{categorias_str}")
    if escolha and escolha.isdigit():
        escolha = int(escolha)

    if escolha and 1 <= escolha <= len(categorias_personalizadas):
        categoria_removida = categorias_personalizadas.pop(escolha - 1)
        salvar_dados()
        for produto in produtos:
            if categoria_removida in produto:
                del produto[categoria_removida]
        atualizar_lista_visual()
        popup_aviso("Categoria Removida", f"A categoria '{categoria_removida}' foi removida.")
    else:
        popup_aviso("Aviso", "Número inválido ou cancelado.")

def adicionar_produto():
    nome = popup_input("Novo Produto", "Digite o nome do produto:")
    if not nome:
        return

    codigo = popup_input("Código de Barras", "Digite o código de barras do produto:")
    if not codigo:
        popup_aviso("Aviso", "O código de barras é obrigatório.")
        return

    novo_produto = {
        "nome": nome,
        "código de barras": codigo
    }

    if categorias_personalizadas:
        popup_categorias_personalizadas(novo_produto)

    produtos.append(novo_produto)
    salvar_dados()
    atualizar_lista_visual()

def remover_produto():
    selecionado = lista_produtos.curselection()
    if selecionado:
        indice_visual = selecionado[0]
        indice = indice_mapeamento[indice_visual]
        produto = produtos[indice]
        produto_removido = produtos.pop(indice)
        salvar_dados()
        atualizar_lista_visual()
        popup_aviso("Removido", f"Produto '{produto_removido['nome']}' removido com sucesso.")
    else:
        popup_aviso("Aviso", "Selecione um produto para remover.")


def alterar_produto():
    selecionado = lista_produtos.curselection()
    if not selecionado:
        popup_aviso("Aviso", "Selecione um produto para alterar.")
        return

    indice_visual = selecionado[0]
    indice = indice_mapeamento[indice_visual]
    produto = produtos[indice]

    novo_nome = popup_input("Alterar Nome", f"Nome atual: {produto.get('nome', '')}\nDigite o novo nome ou deixe em branco para manter:")
    if novo_nome:
        produto["nome"] = novo_nome

    novo_codigo = popup_input("Alterar Código de Barras", f"Código atual: {produto.get('código de barras', '')}\nDigite o novo código ou deixe em branco para manter:")
    if novo_codigo:
        produto["código de barras"] = novo_codigo

    categorias_do_produto = [cat for cat in categorias_personalizadas if cat in produto]
    if categorias_do_produto:
        popup = tk.Toplevel(janela)
        popup.title("Remover Categoria")
        popup.configure(bg="#DDDDDD")
        popup.geometry("370x180")
        popup.grab_set()
        popup.resizable(False, False)

        tk.Label(popup, text="Selecione a categoria que deseja remover:",
                 bg="#DDDDDD", fg="black", font=("Arial", 12), wraplength=340).pack(pady=(15, 5))

        cat_var = tk.StringVar()
        combo_cat = ttk.Combobox(popup, textvariable=cat_var, values=categorias_do_produto, state="readonly",
                                 font=("Arial", 11))
        combo_cat.pack(pady=5, padx=20, fill="x")

        def confirmar_remocao():
            cat_remover = cat_var.get()
            if cat_remover:
                del produto[cat_remover]
                popup.destroy()
                popup_aviso("Removida", f"A categoria '{cat_remover}' foi removida do produto.")
            else:
                popup.destroy()

        btn_confirmar = tk.Button(popup, text="Remover Categoria", command=confirmar_remocao,
                                  bg="white", fg="black", font=("Arial", 10, "bold"), relief="ridge", bd=2)
        btn_confirmar.pack(pady=15)

        popup.wait_window()

    if categorias_personalizadas:
        popup = tk.Toplevel(janela)
        popup.title("Adicionar Categoria")
        popup.configure(bg="#DDDDDD")
        popup.geometry("370x180")
        popup.grab_set()
        popup.resizable(False, False)

        tk.Label(popup, text="Deseja adicionar uma nova categoria a este produto?",
                 bg="#DDDDDD", fg="black", font=("Arial", 12), wraplength=340).pack(pady=(15, 5))

        opcao_var = tk.StringVar()
        combo_opcao = ttk.Combobox(popup, textvariable=opcao_var, values=["Sim", "Não"], state="readonly",
                                   font=("Arial", 11))
        combo_opcao.pack(pady=5, padx=20, fill="x")

        def confirmar_opcao():
            escolha = opcao_var.get()
            popup.destroy()
            if escolha == "Sim":
                popup_categorias_personalizadas(produto)

        btn_confirmar = tk.Button(popup, text="Confirmar", command=confirmar_opcao,
                                  bg="white", fg="black", font=("Arial", 10, "bold"), relief="ridge", bd=2)
        btn_confirmar.pack(pady=15)

        popup.wait_window()

    atualizar_lista_visual()
    popup_aviso("Sucesso", "Produto atualizado com sucesso.")

def adicionar_datas_ao_produto():
    selecionado = lista_produtos.curselection()
    if not selecionado:
        popup_aviso("Aviso", "Selecione um produto primeiro.")
        return

    indice_visual = selecionado[0]
    indice = indice_mapeamento[indice_visual]
    produto = produtos[indice]

    if "vencimentos" not in produto:
        produto["vencimentos"] = []

    if len(produto["vencimentos"]) >= 5:
        popup_aviso("Limite atingido", "Você já adicionou 5 datas de vencimento.")
        return

    popup = tk.Toplevel(janela)
    popup.title("Adicionar Data de Vencimento")
    popup.configure(bg="#DDDDDD")
    popup.geometry("300x220")
    popup.grab_set()
    popup.resizable(False, False)

    tk.Label(popup, text="Selecione ou digite a data de vencimento:",
             bg="#DDDDDD", font=("Arial", 11)).pack(pady=10)

    frame_inputs = tk.Frame(popup, bg="#DDDDDD")
    frame_inputs.pack(pady=5)

    dia_var = tk.StringVar()
    mes_var = tk.StringVar()
    ano_var = tk.StringVar(value=str(datetime.now().year))

    dias = [str(i).zfill(2) for i in range(1, 32)]
    meses = [str(i).zfill(2) for i in range(1, 13)]
    anos = [str(i) for i in range(2025, 2101)]

    combo_dia = ttk.Combobox(frame_inputs, textvariable=dia_var, values=dias, width=5, font=("Arial", 11))
    combo_mes = ttk.Combobox(frame_inputs, textvariable=mes_var, values=meses, width=5, font=("Arial", 11))
    combo_ano = ttk.Combobox(frame_inputs, textvariable=ano_var, values=anos, width=7, font=("Arial", 11))

    combo_dia.grid(row=0, column=0, padx=5)
    combo_mes.grid(row=0, column=1, padx=5)
    combo_ano.grid(row=0, column=2, padx=5)

    def check_length(var, length, next_widget):
        if len(var.get()) >= length:
            next_widget.focus()

    combo_dia.bind("<KeyRelease>", lambda e: check_length(dia_var, 2, combo_mes))
    combo_mes.bind("<KeyRelease>", lambda e: check_length(mes_var, 2, combo_ano))

    def confirmar():
        dia = dia_var.get()
        mes = mes_var.get()
        ano = ano_var.get()
        data_str = f"{dia}/{mes}/{ano}"
        try:
            data_validada = datetime.strptime(data_str, "%d/%m/%Y").strftime("%d/%m/%Y")
            produto["vencimentos"].append(data_validada)
            limpar_datas_vencidas()
            salvar_dados()
            atualizar_lista_visual()
            popup.destroy()
        except ValueError:
            popup_aviso("Erro", "Data inválida. Verifique se o dia, mês e ano são válidos.")

    btn_confirmar = tk.Button(popup, text="Confirmar", command=confirmar,
                              bg="white", fg="black", font=("Arial", 10, "bold"))
    btn_confirmar.pack(pady=15)

    popup.bind("<Return>", lambda event: confirmar())
    combo_dia.focus()

    popup.wait_window()
    janela.after(10, restaurar_foco_botao)

def remover_datas_do_produto():
    selecionado = lista_produtos.curselection()
    if not selecionado:
        popup_aviso("Aviso", "Selecione um produto primeiro.")
        return

    indice_visual = selecionado[0]
    indice = indice_mapeamento[indice_visual]
    produto = produtos[indice]

    if "vencimentos" not in produto or not produto["vencimentos"]:
        popup_aviso("Nada a remover", "Este produto não possui datas de vencimento.")
        return

    lista_datas = "\n".join(f"{i+1}. {d}" for i, d in enumerate(produto["vencimentos"]))
    escolha = popup_input("Remover Data", f"Escolha o número da data para remover:\n\n{lista_datas}")

    if escolha:
        try:
            escolha_int = int(escolha)
        except ValueError:
            popup_aviso("Aviso", "Número inválido.")
            return
    else:
        return

    if 1 <= escolha_int <= len(produto["vencimentos"]):
        data_removida = produto["vencimentos"].pop(escolha_int - 1)
        atualizar_lista_visual()
        popup_aviso("Removida", f"A data {data_removida} foi removida.")
    else:
        popup_aviso("Aviso", "Número inválido ou operação cancelada.")

def solicitar_datas_vencimento():
    datas = []
    for i in range(5):
        data_input = popup_input("Data de Vencimento", f"Digite a {i+1}ª data de vencimento (dd/mm/aaaa) ou deixe em branco para parar:")
        if not data_input:
            break
        try:
            data_validada = datetime.strptime(data_input, "%d/%m/%Y").strftime("%d/%m/%Y")
            datas.append(data_validada)
        except ValueError:
            popup_aviso("Erro", "Formato de data inválido. Use dd/mm/aaaa.")
            continue
    return datas

def mostrar_produto(produto):
    texto = f"{produto.get('nome', '')} | Código: {produto.get('código de barras', '')}"

    if "vencimentos" in produto and produto["vencimentos"]:
        datas_ordenadas = sorted(produto["vencimentos"], key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        texto += f" | Vencimentos: {', '.join(datas_ordenadas)}"

    for cat in categorias_personalizadas:
        if cat in produto:
            texto += f" | {cat}: {produto[cat]}"

    lista_produtos.insert(tk.END, texto)

def aplicar_filtro(termo):
    lista_produtos.delete(0, tk.END)
    termo = termo.strip().lower()
    campo = filtro_var.get().lower()

    for produto in produtos:
        if campo == "nome":
            if termo in produto.get("nome", "").lower():
                mostrar_produto(produto)
        elif campo == "código de barras":
            for chave, valor in produto.items():
                if chave.lower() == "código de barras" and termo in str(valor).lower():
                    mostrar_produto(produto)
        elif campo == "categoria":
            for cat_nome, valor in produto.items():
                if cat_nome.lower() != "nome" and cat_nome.lower() != "vencimentos":
                    if termo in str(valor).lower():
                        mostrar_produto(produto)

def verificar_vencimentos():
    agora = datetime.now()
    hoje = agora.date()
    hora_atual = agora.time()

    if hora_atual < time(9, 0):
        return

    produtos_para_destacar.clear()
    novos_avisos = {
        "1 mês": [],
        "7 dias": [],
        "1 dia": [],
        "hoje": []
    }

    for produto in produtos:
        datas = produto.get("vencimentos", [])
        novas_datas = []

        for data_str in datas:
            try:
                data_venc = datetime.strptime(data_str, "%d/%m/%Y").date()
                dias_restantes = (data_venc - hoje).days

                if dias_restantes == 30:
                    novos_avisos["1 mês"].append(f"{produto['nome']} ({data_str})")
                elif dias_restantes == 7:
                    novos_avisos["7 dias"].append(f"{produto['nome']} ({data_str})")
                elif dias_restantes == 1:
                    novos_avisos["1 dia"].append(f"{produto['nome']} ({data_str})")
                elif dias_restantes == 0:
                    novos_avisos["hoje"].append(f"{produto['nome']} ({data_str})")
                    produtos_para_destacar.append(produto)

                if dias_restantes >= 0:
                    novas_datas.append(data_str)
            except ValueError:
                continue

        produto["vencimentos"] = novas_datas

    atualizar_lista_visual()

    mensagem = ""
    for categoria, lista in novos_avisos.items():
        if lista:
            mensagem += f"⚠ Produtos que vencem em {categoria}:\n" + "\n".join(lista) + "\n\n"

    if mensagem:
        messagebox.showwarning("Resumo de Vencimentos do Dia", mensagem.strip())

def limpar_datas_vencidas():
    hoje = datetime.now().date()
    for produto in produtos:
        if "vencimentos" in produto:
            produto["vencimentos"] = [
                data_str for data_str in produto["vencimentos"]
                if datetime.strptime(data_str, "%d/%m/%Y").date() >= hoje
            ]

def agendar_verificacao_diaria():
    def tarefa():
        while True:
            agora = datetime.now()
            if agora.hour == 9 and agora.minute == 0:
                winsound.Beep(1000, 1000)
                verificar_vencimentos()
                time_mod.sleep(61)
            time_mod.sleep(30)
    thread = threading.Thread(target=tarefa, daemon=True)
    thread.start()

janela = tk.Tk()
janela.title("Controle de Vencimento")

COR_FUNDO = "#2b2b2b"
janela.configure(bg=COR_FUNDO)

largura = int(1280 * 2 / 3)
altura = int(720 * 2 / 3)
janela.geometry(f"{largura}x{altura}")


COR_BOTAO_BG = "white"
COR_BOTAO_FG = "black"

def popup_input(titulo, mensagem):
    popup = tk.Toplevel(janela)
    popup.title(titulo)
    popup.configure(bg="#DDDDDD")
    popup.geometry("480x200")
    popup.grab_set()
    popup.resizable(False, False)

    tk.Label(popup, text=mensagem, bg="#DDDDDD", fg="black", font=("Arial", 12), wraplength=460).pack(pady=(20, 10))

    entrada = tk.Entry(popup, font=("Arial", 12))
    entrada.pack(padx=20, fill="x")

    popup.wait_visibility()
    popup.lift()

    popup.after(100, lambda: entrada.focus_force())

    valor = {"resposta": None}

    def confirmar():
        valor["resposta"] = entrada.get()
        popup.destroy()

    botao = tk.Button(popup, text="Confirmar", command=confirmar,
                      bg="white", fg="black", font=("Arial", 10, "bold"),
                      relief="ridge", bd=2)
    botao.pack(pady=20)

    popup.bind("<Return>", lambda event: confirmar())

    popup.wait_window()
    janela.after(10, restaurar_foco_botao)
    return valor["resposta"]

def popup_aviso(titulo, mensagem):
    aviso = tk.Toplevel(janela)
    aviso.title(titulo)
    aviso.configure(bg="#DDDDDD")
    aviso.geometry("333x133")
    aviso.grab_set()
    aviso.resizable(False, False)

    tk.Label(aviso, text=mensagem, bg="#DDDDDD", fg="black", font=("Arial", 11), wraplength=300).pack(pady=20, padx=15)

    botao = tk.Button(aviso, text="OK", command=aviso.destroy,
                      bg="white", fg="black", font=("Arial", 10, "bold"),
                      relief="ridge", bd=2)
    botao.pack(pady=5)
    botao.focus()

    aviso.bind("<Return>", lambda event: aviso.destroy())

    aviso.wait_window()
    janela.after(10, restaurar_foco_botao)

def chamar_funcao_mantendo_foco(func, botao):
    global ultimo_botao_focado
    ultimo_botao_focado = botao
    func()

frame_topo = tk.Frame(janela, bg=COR_FUNDO)
frame_topo.pack(fill="x", pady=(0, 10))

frame_botoes = tk.Frame(frame_topo, bg=COR_FUNDO)
frame_botoes.pack(fill="x", pady=(10, 5), padx=20)

botoes = [
    ("Adicionar Produto", adicionar_produto),
    ("Remover Produto", remover_produto),
    ("Alterar Produto", alterar_produto),
    ("Nova Categoria", adicionar_categoria),
    ("Remover Categoria", remover_categoria),
    ("Adicionar Data", adicionar_datas_ao_produto),
    ("Remover Datas", remover_datas_do_produto)
]

botoes_widgets = []

for i, (texto, comando) in enumerate(botoes):
    btn = tk.Button(frame_botoes, text=texto,
                    bg=COR_BOTAO_BG, fg=COR_BOTAO_FG, relief="raised", font=("Arial", 10, "bold"))
    btn.pack(side="left", padx=5, pady=5, ipadx=5, ipady=2)

    btn.config(command=lambda c=comando, b=btn: chamar_funcao_mantendo_foco(c, b))

    btn.bind("<Return>", lambda e, c=comando, b=btn: chamar_funcao_mantendo_foco(c, b))

    def foco_proximo(event, idx=i):
        botoes_widgets[(idx + 1) % len(botoes_widgets)].focus_set()

    def foco_anterior(event, idx=i):
        botoes_widgets[(idx - 1) % len(botoes_widgets)].focus_set()

    btn.bind("<Right>", foco_proximo)
    btn.bind("<Left>", foco_anterior)

    botoes_widgets.append(btn)

botoes_widgets[0].focus_set()

frame_pesquisa = tk.Frame(frame_topo, bg=COR_FUNDO)
frame_pesquisa.pack(fill="x", padx=20, pady=(0, 10))

tk.Label(frame_pesquisa, text="Buscar por:", bg=COR_FUNDO, fg="white").pack(side="left", padx=(0, 5))

opcoes_filtro = ["Nome", "Categoria", "Código de Barras"]
filtro_var = tk.StringVar(value="Nome")
combo_filtro = ttk.Combobox(frame_pesquisa, textvariable=filtro_var, values=opcoes_filtro,
                            state="readonly", width=20)
combo_filtro.pack(side="left", padx=5)

entrada_busca = tk.Entry(frame_pesquisa)
entrada_busca.pack(side="left", fill="x", expand=True, padx=5)
entrada_busca.bind("<Return>", lambda event: aplicar_filtro(entrada_busca.get()))

botao_buscar = tk.Button(frame_pesquisa, text="Buscar", command=lambda: aplicar_filtro(entrada_busca.get()),
                         bg=COR_BOTAO_BG, fg=COR_BOTAO_FG, relief="raised")
botao_buscar.pack(side="left", padx=5)

lista_produtos = tk.Listbox(janela, bg="white", fg="black", font=("Arial", 12), bd=0, highlightthickness=0)
lista_produtos.pack(fill="both", expand=True)

def salvar_dados():
    dados = {
        "produtos": produtos,
        "categorias": categorias_personalizadas
    }
    with open("dados_vencimento.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def carregar_dados():
    global produtos, categorias_personalizadas
    if os.path.exists("dados_vencimento.json"):
        with open("dados_vencimento.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
            produtos = dados.get("produtos", [])
            categorias_personalizadas = dados.get("categorias", [])

carregar_dados()
limpar_datas_vencidas()
salvar_dados()
atualizar_lista_visual()

def salvar_antes_de_sair():
    salvar_dados()
    janela.destroy()

janela.protocol("WM_DELETE_WINDOW", salvar_antes_de_sair)

import sys

def verificar_e_sair():
    verificar_vencimentos()
    janela.after(30000, lambda: sys.exit())

import sys
if len(sys.argv) > 1 and sys.argv[1] == "--alerta":
    verificar_e_sair()
else:
    janela.mainloop()

janela.mainloop()