# Jnx - Reprodutor de Vídeo por Frames com Anotações

![imagem](https://images3.alphacoders.com/119/thumb-1920-1190662.jpg)

## Descrição do Projeto

Jnx é um reprodutor de vídeo simples, desenvolvido em **Python** usando **Streamlit**, **OpenCV** e **MoviePy**, que permite navegar pelos vídeos **frame a frame**, ao invés de usar minutos ou segundos como referência.  
O projeto inclui uma funcionalidade de **anotações de frames**, para registrar observações enquanto você revisa cada frame do vídeo.

Ele foi criado com foco em **checagem manual de vídeos de visão computacional**, permitindo que o usuário verifique visualmente se os modelos estão realizando um bom trabalho em tarefas como detecção, rastreamento ou classificação de objetos.

## Funcionalidades

- Carregar vídeos nos formatos: `.mp4`, `.avi` e `.mov`.
- Navegar pelos frames usando:
  - **Slider de frames**
  - **Botões “Frame anterior” / “Próximo frame”**
- Adicionar **observações para cada frame**.
- Visualizar todas as **anotações salvas** em uma lista.
- Compatível com Python 3.13 e Streamlit.

## Objetivo

O projeto foi criado **exclusivamente para uso pessoal**, com o objetivo de testar vídeos produzidos para visão computacional.  
A ideia é **comparar a análise automática** realizada pelos modelos com **uma checagem manual feita pelo olho humano**, garantindo maior qualidade e precisão no trabalho.

## Sobre o nome "J1nx"

O nome **Jnx** foi escolhido unicamente por gosto pessoal, inspirado na personagem **Jinx do League of Legends**.  
Não possui relação direta com funcionalidades do projeto, mas serve como uma marca pessoal para o código.

---



git clone https://github.com/seu_usuario/jnx.git
cd jnx
