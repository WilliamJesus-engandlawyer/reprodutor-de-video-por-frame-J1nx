# 🎥 Reprodutor de Vídeo por Frames com Anotações e Relatórios

Este projeto é uma aplicação em **Streamlit** que permite analisar vídeos quadro a quadro (frames), adicionar anotações em cada frame e gerar relatórios em **CSV** e **PDF**.  
É útil para revisar vídeos de forma detalhada, registrando observações específicas em determinados momentos. Criei em especifico para fazer relatórios de videos de visão computacional.

## 🚀 Deploy Cloud

A aplicação está disponível em:  
[Deploy cloud da aplicação](https://reapputor-de-video-por-frame-j1nx-g78r3edmttuqjjk62smpkb.streamlit.app/)


---

## 🚀 Funcionamento

1. **Upload do Vídeo**  
   - O usuário envia um arquivo de vídeo (`.mp4`, `.avi`, `.mov`).  
   - O vídeo é salvo temporariamente para processamento.

2. **Leitura e Contagem de Frames**  
   - O código utiliza **OpenCV (cv2)** para abrir o vídeo e identificar a quantidade total de frames.  
   - Se a contagem de frames falhar, o sistema tenta corrigir o arquivo com **FFmpeg**.  
   - Caso ainda não funcione, é feita uma leitura frame a frame.

3. **Navegação entre Frames**  
   - Seleção manual de frame por **slider**.  
   - Botões para avançar ou retroceder frames.  
   - Exibição do frame selecionado na tela.

4. **Anotações por Frame**  
   - O usuário pode escrever observações específicas para cada frame.  
   - As anotações ficam salvas na **session_state** do Streamlit.

5. **Comentário Global**  
   - Além das anotações por frame, o usuário pode inserir um comentário geral sobre o vídeo ou desempenho analisado.

6. **Visualização das Anotações**  
   - As observações são exibidas em uma tabela organizada (**Pandas DataFrame**).

7. **Exportação de Relatórios**  
   - **CSV**: planilha com frames anotados + comentário global.  
   - **PDF**: relatório com:
     - Miniaturas dos frames anotados.  
     - Observações registradas.  
     - Comentário global em página separada.  
   - O PDF é gerado com **ReportLab**.

8. **Download**  
   - Relatórios em CSV e PDF podem ser baixados diretamente pela interface.

---

## 🛠️ Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/) – Interface web interativa  
- [OpenCV](https://opencv.org/) – Leitura e manipulação de vídeos  
- [FFmpeg](https://ffmpeg.org/) – Correção de metadados de vídeos  
- [Pandas](https://pandas.pydata.org/) – Estruturação das anotações em tabelas  
- [ReportLab](https://www.reportlab.com/) – Geração de relatórios em PDF  
- [Pillow (PIL)](https://pillow.readthedocs.io/) – Processamento de imagens  

---

👉 Em resumo, este sistema combina **Streamlit + OpenCV + FFmpeg + Pandas + ReportLab** para oferecer uma ferramenta completa de **revisão de vídeo**, com foco em **anotações quadro a quadro e geração de relatórios automatizados**.

# O nome do projeto, é inpirado na personagem JINX, unicamente, porque gosto da personagem
![gostodela](https://images7.alphacoders.com/138/thumb-1920-1383989.png)

