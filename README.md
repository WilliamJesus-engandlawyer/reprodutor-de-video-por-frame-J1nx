
---

# 🎞️ Anotador de Vídeo por Frames com Relatórios (Versão Desktop)

Este projeto é uma **aplicação desktop** desenvolvida com **Python**, utilizando **CustomTkinter** e **OpenCV** para permitir a **análise quadro a quadro de vídeos**, com **anotações personalizadas** e **geração automática de relatórios** em **CSV** e **PDF**.

Ideal para **análises de visão computacional**, revisão de vídeos e criação de **relatórios precisos por frame**.

---

## 🖥️ Principais Recursos

1. **Carregamento de Vídeos**

   * Suporte a arquivos `.mp4`, `.avi` e `.mov`.
   * Exibe o vídeo diretamente na interface.
   * Mostra o número total de frames e o frame atual durante a navegação.

2. **Navegação entre Frames**

   * Controle intuitivo via **slider** e botões **Anterior / Próximo**.
   * Atualização em tempo real do frame exibido.
   * Exibição clara: `Você está no frame X de Y`.

3. **Anotações por Frame**

   * Campo de texto para observações individuais por frame.
   * Salvamento automático ao alternar entre frames.
   * Botão de salvamento manual para controle extra.

4. **Comentário Global**

   * Espaço dedicado para observações gerais sobre o vídeo.

5. **Exportação de Relatórios**

   * **CSV**: planilha com frames anotados + comentário global.
   * **PDF**: relatório visual contendo:

     * Miniaturas dos frames anotados.
     * Anotações associadas.
     * Comentário global em página separada.
   * PDFs são gerados com **ReportLab**, utilizando formatação elegante.

6. **Interface Moderna**

   * Construída com **CustomTkinter**, com **modo escuro** e botões estilizados.
   * Compatível com **Windows, Linux e macOS**.

---

## 🧩 Tecnologias Utilizadas

| Tecnologia                                                      | Função                                            |
| --------------------------------------------------------------- | ------------------------------------------------- |
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Interface gráfica moderna e responsiva            |
| [OpenCV](https://opencv.org/)                                   | Leitura e manipulação de vídeos                   |
| [Pillow (PIL)](https://pillow.readthedocs.io/)                  | Exibição e processamento de frames                |
| [Pandas](https://pandas.pydata.org/)                            | Estruturação e exportação de anotações em CSV     |
| [ReportLab](https://www.reportlab.com/)                         | Geração de relatórios PDF com miniaturas e textos |

---

## ⚙️ Como Usar

### 1. Instale as dependências

```bash
pip install opencv-python pillow customtkinter pandas reportlab
```

### 2. Execute a aplicação

```bash
python app.py
```

### 3. Utilize a interface

1. Clique em **📂 Abrir vídeo** para carregar o arquivo.
2. Use **⬅️ / ➡️** ou o **slider** para navegar entre frames.
3. Escreva anotações por frame e um comentário global (opcional).
4. Exporte seu relatório em **CSV** ou **PDF** diretamente pela interface.

---

## 📄 Geração de Relatórios

Os relatórios são criados automaticamente com base nas anotações realizadas:

* **CSV**: formato estruturado para análise tabular.
* **PDF**: documento visual com miniaturas e comentários, ideal para apresentação ou documentação técnica.

---

## 🧠 Sobre a Versão Streamlit (anterior)

Uma versão anterior deste projeto foi desenvolvida em **Streamlit** e continua disponível no repositório para referência:
🔗 [Versão Web (Streamlit Cloud)](https://reapputor-de-video-por-frame-j1nx-g78r3edmttuqjjk62smpkb.streamlit.app/)

Essa versão implementa as mesmas funcionalidades em ambiente web, mas a versão **atual (Tkinter)** é **autônoma, mais leve e voltada para uso local**.

---

## 📌 Resumo

> O **Anotador de Vídeo por Frames** é uma ferramenta completa para quem precisa revisar vídeos quadro a quadro, registrar observações detalhadas e gerar relatórios profissionais de forma prática — tudo em uma interface moderna e intuitiva.

---


# O nome do projeto, é inpirado na personagem JINX, unicamente, porque gosto da personagem
![gostodela](https://images7.alphacoders.com/138/thumb-1920-1383989.png)

